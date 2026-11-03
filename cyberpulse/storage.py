"""Crash-resilient savegame and career profile storage engine for CyberPulse."""

import hashlib
import json
import math
import os
import random
import shutil
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from cyberpulse.daily import modifier_by_id
from cyberpulse.difficulty import normalize_difficulty
from cyberpulse.factions import (
    allegiance_contract_bonus,
    allegiance_shop_discount,
    normalize_allegiance,
    normalize_standing,
)
from cyberpulse.engine import GameEngine
from cyberpulse.models import CareerProfile, CyberDeck, GameState, Node
from cyberpulse.puzzles import puzzle_from_dict

AUTO_SLOT = "auto"
SLOT_KEYS = ("1", "2", "3", AUTO_SLOT)
SLOT_NAME_LIMIT = 32


def encode_rng_state(state: Any) -> Dict[str, Any]:
    """Convert a random.Random state tuple into a JSON-safe payload."""
    version, internal, gauss_next = state
    return {
        "version": int(version),
        "internal": [int(value) for value in internal],
        "gauss_next": gauss_next,
    }


def decode_rng_state(payload: Dict[str, Any]) -> Any:
    """Restore a random.Random state tuple from a persisted payload."""
    return (
        int(payload["version"]),
        tuple(int(value) for value in payload["internal"]),
        payload.get("gauss_next"),
    )


class SaveManager:
    """Manages atomic saving and loading of game states and career profiles."""

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.save_file = self.data_dir / "savegame.json"
        self.autosave_file = self.data_dir / "autosave.json"
        self.career_file = self.data_dir / "career.json"
        self._owned_slots: Set[str] = set()
        self._last_autosave_signature: Optional[str] = None

    @staticmethod
    def normalize_slot(slot: Any = 1) -> str:
        """Return a canonical slot key: '1', '2', '3' or 'auto'."""
        if slot is None:
            return "1"
        if isinstance(slot, bool):
            raise ValueError("slot must be 1, 2, 3 or 'auto'")
        if isinstance(slot, int):
            key = str(slot)
        elif isinstance(slot, str):
            key = slot.strip().lower()
        else:
            raise ValueError("slot must be 1, 2, 3 or 'auto'")
        if key in ("auto", "autosave"):
            return AUTO_SLOT
        if key in ("1", "2", "3"):
            return key
        raise ValueError("slot must be 1, 2, 3 or 'auto'")

    def slot_path(self, slot: Any = 1) -> Path:
        """Map a slot key to its atomic save file, keeping slot 1 backward compatible."""
        key = self.normalize_slot(slot)
        if key == "1":
            return self.save_file
        if key == AUTO_SLOT:
            return self.autosave_file
        return self.data_dir / f"savegame_slot{key}.json"

    @classmethod
    def slot_label(cls, slot: Any = 1) -> str:
        """Return a human-readable label for a slot."""
        key = cls.normalize_slot(slot)
        return "AUTOSAVE" if key == AUTO_SLOT else f"SLOT {key}"

    def _slot_exists(self, key: str) -> bool:
        path = self.slot_path(key)
        return path.exists() or path.with_suffix(".bak").exists()

    def _is_readable_json(self, path: Path) -> bool:
        """Return True when a file parses as JSON, so a corrupt primary never replaces a good backup."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                json.load(f)
            return True
        except (json.JSONDecodeError, OSError):
            return False

    def _write_atomic(self, target_path: Path, data: Any) -> Optional[Path]:
        """Write JSON payload to target_path atomically; returns None when the replace never lands."""
        backup_path = target_path.with_suffix(".bak")

        payload = json.dumps(data, indent=2)
        temp_path: Optional[Path] = None
        try:
            fd, temp_name = tempfile.mkstemp(dir=self.data_dir, prefix=f".tmp_{target_path.name}_")
            temp_path = Path(temp_name)
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(payload)
                f.flush()
                os.fsync(f.fileno())

            if target_path.exists() and self._is_readable_json(target_path):
                shutil.copy2(target_path, backup_path)

            for _ in range(5):
                try:
                    os.replace(temp_path, target_path)
                    return target_path
                except OSError:
                    time.sleep(0.02)
            return None
        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)

    def _read_json_with_backup(self, target_path: Path, quarantine: bool = True) -> Optional[Any]:
        """Read JSON from target_path, falling back to shadow .bak if corrupted or missing."""
        backup_path = target_path.with_suffix(".bak")

        if target_path.exists():
            try:
                with open(target_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                if quarantine:
                    # Quarantine corrupted file
                    corrupt_path = self.data_dir / f"{target_path.name}.corrupt_{int(time.time())}"
                    try:
                        shutil.move(target_path, corrupt_path)
                    except OSError:  # hygiene: allow quarantine best-effort; backup recovery follows
                        pass

        # Attempt recovery from shadow backup
        if backup_path.exists():
            try:
                with open(backup_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):  # hygiene: allow unusable backup is reported as None
                pass

        return None

    def _read_slot_payload(self, key: str, quarantine: bool = False) -> Optional[Any]:
        return self._read_json_with_backup(self.slot_path(key), quarantine=quarantine)

    def has_save(self, slot: Any = None) -> bool:
        """Return True when any slot (or the requested slot) has a save or shadow backup."""
        if slot is None:
            return any(self._slot_exists(key) for key in SLOT_KEYS)
        return self._slot_exists(self.normalize_slot(slot))

    @staticmethod
    def clean_name(name: Any = "") -> str:
        """Normalize a slot label to one line and cap it for the archive UI."""
        return " ".join(str(name or "").split())[:SLOT_NAME_LIMIT]

    def save(self, engine: GameEngine, slot: Any = 1, name: Optional[str] = None) -> Optional[Path]:
        """Atomically persist engine state to a manual slot or the autosave slot."""
        key = self.normalize_slot(slot)
        target = self.slot_path(key)
        if name is None and key != AUTO_SLOT:
            existing = self._read_slot_payload(key)
            existing_meta = existing.get("meta") if isinstance(existing, dict) else None
            name = existing_meta.get("name", "") if isinstance(existing_meta, dict) else ""
        data = {
            "seed": engine.seed,
            "run_id": getattr(engine, "run_id", uuid.uuid4().hex),
            "daily_key": getattr(engine, "daily_key", ""),
            "daily_modifier": getattr(engine, "daily_modifier", ""),
            "difficulty": getattr(engine, "difficulty", "normal"),
            "allegiance": getattr(engine, "allegiance", "none"),
            "faction_standing": normalize_standing(getattr(engine, "faction_standing", {})),
            "deck": engine.deck.to_dict(),
            "state": engine.state.to_dict(),
            "nodes": {nid: n.to_dict() for nid, n in engine.nodes.items()},
            "rng_state": encode_rng_state(engine.rng.getstate()),
            "puzzles": {
                nid: puzzle.to_dict()
                for nid, puzzle in engine.pending_puzzles.items()
                if hasattr(puzzle, "to_dict")
            },
            "meta": {
                "slot": key,
                "kind": "auto" if key == AUTO_SLOT else "manual",
                "name": self.clean_name(name),
                "saved_at": time.time(),
            },
        }
        return self._write_atomic(target, data)

    def claim_slot(self, slot: Any = 1) -> None:
        """Record that this interface owns a slot and may purge it when the run settles."""
        self._owned_slots.add(self.normalize_slot(slot))

    def rename_slot(self, slot: Any = 1, name: Any = "") -> bool:
        """Rename an existing manual checkpoint without changing its run progress or timestamp."""
        key = self.normalize_slot(slot)
        if key == AUTO_SLOT:
            return False
        path = self.slot_path(key)
        data = self._read_json_with_backup(path)
        if not isinstance(data, dict):
            return False
        meta = data.get("meta") if isinstance(data.get("meta"), dict) else {}
        if "saved_at" not in meta:
            candidates = [candidate for candidate in (path, path.with_suffix(".bak")) if candidate.exists()]
            if candidates:
                meta["saved_at"] = max(candidate.stat().st_mtime for candidate in candidates)
        meta["name"] = self.clean_name(name)
        data["meta"] = meta
        return self._write_atomic(path, data) is not None

    def load(self, slot: Any = 1) -> Optional[GameEngine]:
        """Load and restore engine state from a slot with backup recovery."""
        key = self.normalize_slot(slot)
        data = self._read_json_with_backup(self.slot_path(key))
        if not data or not isinstance(data, dict):
            return None

        try:
            engine = GameEngine(seed=data["seed"], career_profile=self.load_career())
            engine.run_id = str(data.get("run_id") or getattr(engine, "run_id", uuid.uuid4().hex))
            engine.daily_key = str(data.get("daily_key") or "")
            modifier = modifier_by_id(data.get("daily_modifier", ""))
            engine.daily_modifier = modifier.modifier_id if modifier else ""
            engine.difficulty = normalize_difficulty(data.get("difficulty", "normal"))
            engine.allegiance = normalize_allegiance(data.get("allegiance", "none"))
            engine.allegiance_contract_bonus = allegiance_contract_bonus(engine.allegiance)
            engine.allegiance_shop_discount = allegiance_shop_discount(engine.allegiance)
            snapshot = data.get("faction_standing")
            if isinstance(snapshot, dict):
                engine.faction_standing = normalize_standing(snapshot)
                engine.refresh_faction_bonuses()
            engine.deck = CyberDeck.from_dict(data["deck"])
            engine.state = GameState.from_dict(data["state"])
            engine.nodes = {nid: Node.from_dict(ndata) for nid, ndata in data["nodes"].items()}
            engine.ensure_story_state()
            rng_state = data.get("rng_state")
            if isinstance(rng_state, dict):
                try:
                    engine.rng.setstate(decode_rng_state(rng_state))
                except (KeyError, TypeError, ValueError):
                    engine.rng = random.Random(engine.seed + engine.state.turns_elapsed)
            else:
                engine.rng = random.Random(engine.seed + engine.state.turns_elapsed)

            puzzles = data.get("puzzles")
            if isinstance(puzzles, dict):
                for nid, payload in puzzles.items():
                    if not isinstance(payload, dict):
                        continue
                    puzzle = puzzle_from_dict(payload)
                    if puzzle is not None:
                        engine.pending_puzzles[nid] = puzzle
            self._owned_slots.add(key)
            self._last_autosave_signature = self._signature(engine)
            return engine
        except (AttributeError, KeyError, TypeError, ValueError):
            return None

    def _signature(self, engine: GameEngine) -> str:
        """Hash the parts of a run that autosave should notice without rewriting unchanged state."""
        payload = {
            "run_id": getattr(engine, "run_id", ""),
            "difficulty": getattr(engine, "difficulty", "normal"),
            "allegiance": getattr(engine, "allegiance", "none"),
            "faction_standing": getattr(engine, "faction_standing", {}),
            "daily_key": getattr(engine, "daily_key", ""),
            "daily_modifier": getattr(engine, "daily_modifier", ""),
            "state": engine.state.to_dict(),
            "deck": engine.deck.to_dict(),
            "nodes": {
                nid: [
                    str(getattr(node.status, "value", node.status)),
                    bool(node.reward_claimed),
                    int(getattr(node, "lockdown_until_turn", 0) or 0),
                ]
                for nid, node in engine.nodes.items()
            },
            "puzzles": {
                nid: puzzle.to_dict() if hasattr(puzzle, "to_dict") else str(puzzle)
                for nid, puzzle in engine.pending_puzzles.items()
            },
        }
        serialized = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha1(serialized.encode("utf-8")).hexdigest()

    def mark_autosave_baseline(self, engine: GameEngine) -> None:
        """Remember the current state so a new or freshly loaded run is not written before it changes."""
        self._last_autosave_signature = self._signature(engine)

    def autosave(self, engine: GameEngine) -> Optional[Path]:
        """Write the autosave slot once per state change; terminal runs are never saved."""
        if engine.state.is_victory or engine.state.is_game_over or engine.state.is_jacked_out:
            return None
        signature = self._signature(engine)
        if signature == self._last_autosave_signature:
            return None
        path = self.save(engine, AUTO_SLOT)
        if path is not None:
            self.claim_slot(AUTO_SLOT)
            self._last_autosave_signature = signature
        return path

    def list_saves(self) -> List[Dict[str, Any]]:
        """Return metadata for every restorable slot, newest first."""
        saves: List[Dict[str, Any]] = []
        for key in SLOT_KEYS:
            if not self._slot_exists(key):
                continue
            data = self._read_slot_payload(key)
            if not isinstance(data, dict):
                continue
            meta = data.get("meta") if isinstance(data.get("meta"), dict) else {}
            state = data.get("state") if isinstance(data.get("state"), dict) else {}
            deck = data.get("deck") if isinstance(data.get("deck"), dict) else {}
            saved_at = meta.get("saved_at")
            if (
                not isinstance(saved_at, (int, float))
                or isinstance(saved_at, bool)
                or not math.isfinite(float(saved_at))
                or float(saved_at) <= 0
            ):
                path = self.slot_path(key)
                candidates = [p for p in (path, path.with_suffix(".bak")) if p.exists()]
                saved_at = max(p.stat().st_mtime for p in candidates) if candidates else 0.0
            saves.append({
                "slot": key,
                "label": self.slot_label(key),
                "name": self.clean_name(meta.get("name", "")),
                "kind": "auto" if key == AUTO_SLOT else "manual",
                "saved_at": float(saved_at),
                "saved_at_display": time.strftime("%Y-%m-%d %H:%M", time.localtime(float(saved_at))),
                "turns": int(state.get("turns_elapsed", 0) or 0),
                "creds": int(deck.get("cryptocreds", 0) or 0),
                "trace": int(state.get("trace_percent", 0) or 0),
                "act": int(state.get("story_act", 1) or 1),
                "seed": int(data.get("seed", 0) or 0),
                "terminal": bool(
                    state.get("is_victory") or state.get("is_game_over") or state.get("is_jacked_out")
                ),
            })
        order = {key: index for index, key in enumerate(SLOT_KEYS)}
        saves.sort(key=lambda entry: (-entry["saved_at"], order.get(entry["slot"], 99)))
        return saves

    def delete_save(self, slot: Any = 1) -> None:
        """Remove a slot's savegame and its shadow backup."""
        key = self.normalize_slot(slot)
        path = self.slot_path(key)
        path.unlink(missing_ok=True)
        path.with_suffix(".bak").unlink(missing_ok=True)
        self._owned_slots.discard(key)
        if key == AUTO_SLOT:
            self._last_autosave_signature = None

    def delete_run(self, run_id: str) -> None:
        """Purge this interface's owned checkpoints of a settled run, leaving other runs untouched."""
        for key in SLOT_KEYS:
            if key not in self._owned_slots:
                continue
            data = self._read_slot_payload(key)
            if not isinstance(data, dict):
                self.delete_save(key)
                continue
            file_run = data.get("run_id")
            if file_run in (None, "", run_id):
                self.delete_save(key)
        self._owned_slots.clear()
        self._last_autosave_signature = None

    def backup_career(self) -> Optional[Path]:
        """Copy the current career payload to career.backup.json before a reset."""
        data = self._read_json_with_backup(self.career_file)
        if not isinstance(data, dict):
            return None
        backup_path = self.data_dir / "career.backup.json"
        return self._write_atomic(backup_path, data)

    def delete_career(self) -> None:
        """Remove the active career profile and its shadow backup."""
        self.career_file.unlink(missing_ok=True)
        self.career_file.with_suffix(".bak").unlink(missing_ok=True)

    def delete_all_saves(self) -> None:
        """Remove every manual slot and the autosave checkpoint."""
        for key in SLOT_KEYS:
            self.delete_save(key)

    def save_career(self, profile: CareerProfile) -> Optional[Path]:
        """Atomically persist career meta-progression profile."""
        return self._write_atomic(self.career_file, profile.to_dict())

    def load_career(self) -> CareerProfile:
        """Load persistent career profile with backup recovery or return fresh profile."""
        data = self._read_json_with_backup(self.career_file)
        if not data or not isinstance(data, dict):
            return CareerProfile()

        try:
            return CareerProfile.from_dict(data)
        except (AttributeError, KeyError, TypeError, ValueError):
            return CareerProfile()
