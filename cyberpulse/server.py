"""Zero-dependency HTTP REST backend and static file server for CyberPulse Web Cyberdeck."""

import json
import math
import mimetypes
import os
import sys
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

# Ensure project root is in sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from cyberpulse.achievements import achievement_status
from cyberpulse.daily import daily_modifier, daily_run
from cyberpulse.deckos import record_history as _record_history
from cyberpulse.difficulty import normalize_difficulty
from cyberpulse.engine import GameEngine
from cyberpulse.factions import rank_for
from cyberpulse.models import CareerProfile, NodeStatus, NodeType
from cyberpulse.puzzles import BufferPuzzle, FrequencyPuzzle, HashCrackPuzzle
from cyberpulse.shop import BlackMarketShop
from cyberpulse.storage import SaveManager


STATIC_DIR = Path(__file__).resolve().parent / "static"
MAX_BODY_BYTES = 1024 * 1024


def coerce_seed(value: Any) -> int:
    """Convert API/CLI seed input to an integer, rejecting non-finite or non-numeric values."""
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("seed must be a finite number") from exc
    if not math.isfinite(number):
        raise ValueError("seed must be finite")
    return int(number)


class CyberdeckSession:
    """Encapsulates the stateful game session driving the Web Cyberdeck interface."""

    def __init__(
        self,
        data_dir: Optional[Path] = None,
        seed: int = 1337,
        daily_key: str = "",
        difficulty: str = "normal",
        daily_modifier: str = "",
        allegiance: str = "none",
    ):
        self.data_dir = data_dir or (Path.cwd() / ".cyberpulse")
        self.save_mgr = SaveManager(self.data_dir)
        self.shop = BlackMarketShop()
        self.career = self.save_mgr.load_career()
        self.engine = GameEngine(
            seed=seed,
            career_profile=self.career,
            difficulty=difficulty,
            daily_modifier=daily_modifier,
            allegiance=allegiance,
        )
        self.engine.daily_key = str(daily_key or "")
        self.active_puzzle: Optional[Any] = None
        self.active_puzzle_node_id: Optional[str] = None
        self.save_mgr.mark_autosave_baseline(self.engine)
        self.lock = threading.RLock()

    def settle_run_if_finished(self) -> Optional[Any]:
        """Persist a victory/lockout exactly once as soon as the run reaches a terminal state."""
        engine = self.engine
        if engine.run_settled:
            return None
        if not (engine.state.is_victory or engine.state.is_game_over or engine.state.is_jacked_out):
            return None

        profile = self.save_mgr.load_career()
        engine.settle_career(profile)
        if not self.save_mgr.save_career(profile):
            engine.run_settled = False
        else:
            self.save_mgr.delete_run(engine.run_id)
        return profile

    def get_full_state(self) -> Dict[str, Any]:
        """Aggregate complete runtime state for frontend rendering."""
        self.settle_run_if_finished()
        self.save_mgr.autosave(self.engine)
        curr = self.engine.get_current_node()
        career = self.save_mgr.load_career()
        world = self.engine.world_summary()
        nodes = {nid: n.to_dict() for nid, n in self.engine.nodes.items()}
        for nid, tag in self.engine.node_districts().items():
            if nid in nodes:
                nodes[nid].update(tag)
        state_data = self.engine.state.to_dict()
        for offer in state_data.get("contract_offers", []) or []:
            tag = self.engine.offer_district(offer.get("target_ip", ""))
            offer["district"] = tag["district"]
            offer["district_patrol"] = tag["district_patrol"]
        active = state_data.get("active_contract")
        if isinstance(active, dict):
            tag = self.engine.offer_district(active.get("target_ip", ""))
            active["district"] = tag["district"]
            active["district_patrol"] = tag["district_patrol"]
        return {
            "seed": self.engine.seed,
            "daily_key": getattr(self.engine, "daily_key", ""),
            "daily_modifier": self.engine.daily_modifier_summary(),
            "difficulty": self.engine.difficulty,
            "allegiance": self.engine.allegiance,
            "state": state_data,
            "deck": self.engine.deck.to_dict(),
            "extraction_risk": self.engine.extraction_risk(),
            "current_node": curr.to_dict(),
            "nodes": nodes,
            "career": career.to_dict(),
            "story": self.engine.story_summary(),
            "world": world,
            "run_summary": self.engine.run_summary(),
            "rival": self.engine.rival_summary(),
            "tutorial": self.engine.tutorial_progress(),
            "quests": self.engine.list_quests(),
            "contacts": self.engine.list_contacts(),
            "deckos": self.engine.deckos_summary(),
            "arcs": self.engine.arcs_summary(),
            "districts": self.engine.district_summary()["districts"],
            "shop_items": self.shop.list_available(
                self.engine.deck, price_multiplier=self.engine.shop_price_multiplier()
            ),
            "workshop_recipes": self.engine.list_crafting_recipes(),
            "known_cves": self.engine.list_cves(),
            "has_save": self.save_mgr.has_save(),
            "saves": self.save_mgr.list_saves(),
            "local_rig": {
                "ip": self.engine.deck.local_ip,
                "hostname": self.engine.deck.local_hostname,
                "model": self.engine.deck.model_name,
                "files": [f.to_dict() for f in self.engine.deck.local_filesystem],
                "daemons": [d.to_dict() for d in self.engine.deck.active_daemons],
            },
        }

    def reset_game(
        self,
        seed: Optional[int] = None,
        daily: bool = False,
        difficulty: str = "normal",
        allegiance: str = "none",
    ) -> Dict[str, Any]:
        new_daily_key = ""
        modifier_id = ""
        if daily:
            new_daily_key, new_seed = daily_run()
            modifier_id = daily_modifier().modifier_id
        else:
            new_seed = coerce_seed(seed) if seed is not None else (self.engine.seed + 1)
        self.career = self.save_mgr.load_career()
        self.engine = GameEngine(
            seed=new_seed,
            career_profile=self.career,
            difficulty=normalize_difficulty(difficulty),
            daily_modifier=modifier_id,
            allegiance=allegiance,
        )
        self.engine.daily_key = new_daily_key
        self.active_puzzle = None
        self.active_puzzle_node_id = None
        self.save_mgr.mark_autosave_baseline(self.engine)
        return self.get_full_state()

    def save_run(self, slot: Any = 1, name: Optional[str] = None) -> Tuple[bool, str]:
        """Persist the live run to a manual slot with the terminal's atomic manager."""
        key = self.save_mgr.normalize_slot(slot)
        if key == "auto":
            return False, "AUTOSAVE is automatic; choose manual slot 1, 2, or 3."
        engine = self.engine
        if engine.state.is_victory or engine.state.is_game_over or engine.state.is_jacked_out:
            return False, "This run is already over; there is nothing left to save."
        path = self.save_mgr.save(engine, key, name=name)
        if path is None:
            return False, "Save failed: the save file could not be replaced after 5 attempts."
        self.save_mgr.claim_slot(key)
        label = self.save_mgr.slot_label(key)
        if self.save_mgr.clean_name(name):
            label = f"{label} // {self.save_mgr.clean_name(name)}"
        return True, f"Infiltration progress saved to {label}. LOAD will restore this exact state."

    def rename_save(self, slot: Any = 1, name: Any = "") -> Tuple[bool, str]:
        """Rename an existing manual checkpoint without changing the run."""
        key = self.save_mgr.normalize_slot(slot)
        label = self.save_mgr.slot_label(key)
        if key == "auto":
            return False, "AUTOSAVE cannot be renamed."
        if not self.save_mgr.rename_slot(key, name):
            return False, f"No checkpoint in {label}."
        clean = self.save_mgr.clean_name(name)
        suffix = f" to '{clean}'" if clean else " (label cleared)"
        return True, f"Renamed {label}{suffix}."

    def reset_career(self) -> Optional[Dict[str, Any]]:
        """Back up and delete the career plus all saves, then start a fresh run."""
        had_career = (
            self.save_mgr.career_file.exists()
            or self.save_mgr.career_file.with_suffix(".bak").exists()
        )
        backup = self.save_mgr.backup_career()
        if had_career and backup is None:
            return None
        self.save_mgr.delete_career()
        self.save_mgr.delete_all_saves()
        self.career = CareerProfile()
        self.engine = GameEngine(
            seed=self.engine.seed + 1,
            career_profile=self.career,
            difficulty=self.engine.difficulty,
        )
        self.active_puzzle = None
        self.active_puzzle_node_id = None
        self.save_mgr.mark_autosave_baseline(self.engine)
        return self.get_full_state()

    def rename_alias(self, name: Any = "") -> Tuple[bool, str]:
        """Persist a new career alias after trimming and capping it."""
        clean = " ".join(str(name or "").split())[:24]
        if not clean:
            return False, "Alias cannot be empty."
        profile = self.save_mgr.load_career()
        profile.alias = clean
        if not self.save_mgr.save_career(profile):
            return False, "Alias could not be saved."
        self.career = profile
        return True, f"Alias set to {clean}."

    def delete_save(self, slot: Any = 1) -> Tuple[bool, str]:
        """Delete a checkpoint from the archive without touching the live run."""
        key = self.save_mgr.normalize_slot(slot)
        label = self.save_mgr.slot_label(key)
        if not self.save_mgr.has_save(key):
            return False, f"No checkpoint in {label}."
        self.save_mgr.delete_save(key)
        return True, f"Deleted {label} checkpoint."

    def load_run(self, slot: Any = 1) -> Tuple[bool, str]:
        """Replace the live engine with a saved run from the requested slot."""
        key = self.save_mgr.normalize_slot(slot)
        label = self.save_mgr.slot_label(key)
        loaded = self.save_mgr.load(key)
        if loaded is None:
            return False, f"No saved run found in {label}. Save a run before trying to continue."
        self.engine = loaded
        self.active_puzzle = None
        self.active_puzzle_node_id = None
        return True, f"Loaded saved infiltration session from {label}."


class CyberdeckHTTPHandler(BaseHTTPRequestHandler):
    """HTTP request handler providing REST API endpoints and static cyberdeck assets."""

    server_session: CyberdeckSession
    timeout = 15

    def log_message(self, format: str, *args: Any) -> None:
        """Route cyberdeck request logs without cluttering console."""
        sys.stdout.flush()

    def send_json_response(self, data: Any, status: int = HTTPStatus.OK) -> None:
        payload = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Allow", "GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self) -> None:
        path = self.path.split("?")[0]
        if not path.startswith("/api/"):
            self.serve_static(path)
            return
        with self.server_session.lock:
            self._do_get()

    def _do_get(self) -> None:
        path = self.path.split("?")[0]

        if path == "/api/state":
            self.send_json_response(self.server_session.get_full_state())
            return

        if path == "/api/shop":
            multiplier = self.server_session.engine.shop_price_multiplier()
            items = self.server_session.shop.list_available(self.server_session.engine.deck, price_multiplier=multiplier)
            self.send_json_response({
                "items": items,
                "creds": self.server_session.engine.deck.cryptocreds,
                "market_multiplier": multiplier,
                "street_discount": self.server_session.engine.street_standing_discount,
            })
            return

        if path == "/api/world":
            world = self.server_session.engine.world_summary()
            self.send_json_response({"world": world, "news": world.get("news", [])})
            return

        if path == "/api/career":
            self.server_session.settle_run_if_finished()
            profile = self.server_session.save_mgr.load_career()
            payload = profile.to_dict()
            payload["achievement_catalog"] = achievement_status(profile)
            payload["faction_ranks"] = {
                faction: rank_for(faction, standing)[1]
                for faction, standing in (profile.faction_standing or {}).items()
                if faction in ("syndicate", "street")
            }
            self.send_json_response(payload)
            return

        if path == "/api/workshop":
            recipes = self.server_session.engine.list_crafting_recipes()
            self.send_json_response({"recipes": recipes})
            return

        if path == "/api/cves":
            self.send_json_response({"cves": self.server_session.engine.list_cves()})
            return

        if path == "/api/firewall":
            target = self.server_session.engine.state.current_node_id
            if "?" in self.path:
                for pair in self.path.split("?")[1].split("&"):
                    if "=" in pair:
                        k, v = pair.split("=", 1)
                        if k in ("target", "ip", "node_id"):
                            target = v
            ok, msg, fw_dict = self.server_session.engine.get_firewall_status(target)
            self.send_json_response({"ok": ok, "message": msg, "firewall": fw_dict}, HTTPStatus.OK if ok else HTTPStatus.BAD_REQUEST)
            return

        if path == "/api/antivirus":
            target = self.server_session.engine.state.current_node_id
            if "?" in self.path:
                for pair in self.path.split("?")[1].split("&"):
                    if "=" in pair:
                        k, v = pair.split("=", 1)
                        if k in ("target", "ip", "node_id"):
                            target = v
            ok, msg, av_dict = self.server_session.engine.get_antivirus_status(target)
            self.send_json_response({"ok": ok, "message": msg, "antivirus": av_dict}, HTTPStatus.OK if ok else HTTPStatus.BAD_REQUEST)
            return

        if path == "/api/local_files":
            self.send_json_response({
                "ip": self.server_session.engine.deck.local_ip,
                "hostname": self.server_session.engine.deck.local_hostname,
                "files": [f.to_dict() for f in self.server_session.engine.deck.local_filesystem],
                "daemons": [d.to_dict() for d in self.server_session.engine.deck.active_daemons],
            })
            return

        if path == "/api/deckos":
            self.send_json_response(self.server_session.engine.deckos_summary())
            return

        if path == "/api/arcs":
            self.send_json_response(self.server_session.engine.arcs_summary())
            return

        if path == "/api/districts":
            self.send_json_response(self.server_session.engine.district_summary())
            return

        if path == "/api/puzzle":
            # Extract query params
            node_id = None
            if "?" in self.path:
                for pair in self.path.split("?")[1].split("&"):
                    if "=" in pair:
                        k, v = pair.split("=", 1)
                        if k == "node_id":
                            node_id = v

            if not node_id or node_id not in self.server_session.engine.nodes:
                self.send_json_response({"ok": False, "error": f"Invalid node '{node_id}'"}, HTTPStatus.BAD_REQUEST)
                return

            can_hack, reason, puzzle, node = self.server_session.engine.get_or_create_puzzle(node_id)
            if not can_hack or puzzle is None or node is None:
                self.send_json_response({"ok": False, "error": reason})
                return

            self.server_session.active_puzzle = puzzle
            self.server_session.active_puzzle_node_id = node_id
            p_type = node.puzzle_type or "frequency"
            puzzle_payload: Dict[str, Any] = {
                "ok": True,
                "node_id": node_id,
                "node_name": node.name,
                "security_level": node.security_level,
                "puzzle_type": p_type,
            }

            if isinstance(puzzle, FrequencyPuzzle):
                puzzle_payload.update({
                    "tolerance": puzzle.tolerance,
                    "attempts_left": puzzle.attempts_left,
                    "min_freq": getattr(puzzle, "min_freq", 20.0),
                    "max_freq": getattr(puzzle, "max_freq", 99.0),
                })
            elif isinstance(puzzle, BufferPuzzle):
                puzzle_payload.update({
                    "matrix": puzzle.matrix,
                    "target_seq": puzzle.target_seq,
                })
            elif isinstance(puzzle, HashCrackPuzzle):
                puzzle_payload.update({
                    "word_list": puzzle.word_list,
                    "word_length": len(puzzle.target_word),
                    "attempts_left": puzzle.attempts_left,
                })

            self.send_json_response(puzzle_payload)
            return

        if path == "/api/forecast":
            action = "scan"
            target = ""
            if "?" in self.path:
                from urllib.parse import parse_qsl, unquote
                for k, v in parse_qsl(self.path.split("?", 1)[1], keep_blank_values=True):
                    if k == "action":
                        action = unquote(v)
                    elif k in ("target", "ip", "node_id"):
                        target = unquote(v)
            self.send_json_response(self.server_session.engine.action_forecast(action, target))
            return

        if path == "/api/route":
            target = self.server_session.engine.state.current_node_id
            if "?" in self.path:
                from urllib.parse import parse_qsl, unquote
                for k, v in parse_qsl(self.path.split("?", 1)[1], keep_blank_values=True):
                    if k in ("target", "ip", "node_id"):
                        target = unquote(v)
            self.send_json_response(self.server_session.engine.trace_route(target))
            return

        # Serve static assets
        self.serve_static(path)

    def serve_static(self, path: str) -> None:
        static_root = STATIC_DIR.resolve()
        if path in ("", "/"):
            req_file = static_root / "index.html"
        else:
            rel = path.lstrip("/")
            req_file = (static_root / rel).resolve()

        if not req_file.is_relative_to(static_root) or not req_file.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, f"Asset '{path}' not found")
            return

        mime_type, _ = mimetypes.guess_type(str(req_file))
        mime_type = mime_type or "application/octet-stream"

        try:
            with open(req_file, "rb") as f:
                content = f.read()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", f"{mime_type}; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except OSError:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, "Failed to read file")

    def do_POST(self) -> None:
        try:
            content_len = int(self.headers.get("Content-Length", 0))
        except (TypeError, ValueError):
            self.send_json_response({"ok": False, "error": "Invalid Content-Length"}, HTTPStatus.BAD_REQUEST)
            return
        if content_len < 0 or content_len > MAX_BODY_BYTES:
            self.send_json_response({"ok": False, "error": "Request body too large"}, HTTPStatus.REQUEST_ENTITY_TOO_LARGE)
            return

        try:
            body = self.rfile.read(content_len).decode("utf-8") if content_len > 0 else "{}"
            payload = json.loads(body)
        except (UnicodeDecodeError, json.JSONDecodeError):
            self.send_json_response({"ok": False, "error": "Malformed JSON payload"}, HTTPStatus.BAD_REQUEST)
            return
        if not isinstance(payload, dict):
            self.send_json_response({"ok": False, "error": "JSON payload must be an object"}, HTTPStatus.BAD_REQUEST)
            return

        path = self.path.split("?")[0]
        with self.server_session.lock:
            self._do_post(path, payload)

    def _do_post(self, path: str, payload: Dict[str, Any]) -> None:
        if path == "/api/action":
            action = payload.get("action")
            engine = self.server_session.engine
            save_mgr = self.server_session.save_mgr
            shop = self.server_session.shop

            if engine.state.is_victory and action not in ("reset", "load"):
                self.send_json_response(
                    {"ok": False, "error": "Mission already complete. Start a new run.", "state": self.server_session.get_full_state()},
                    HTTPStatus.BAD_REQUEST,
                )
                return

            if action in ("save", "load", "reset", "reset_career", "rename_save", "rename",
                            "delete_save", "delete", "rename_alias", "alias"):
                pass  # meta actions stay out of the DeckOS shell history
            elif action:
                # Mirror Web play into the run-scoped DeckOS history so `history`
                # reads the same in the terminal and the cyberdeck.
                label = str(action)
                for key in ("target", "ip", "node_id", "pid", "mode", "stance",
                            "vector", "method", "daemon_type", "slot", "name"):
                    value = payload.get(key)
                    if value not in (None, ""):
                        label += f" {value}"
                        break
                _record_history(engine, label[:160])

            if action == "save":
                try:
                    ok, msg = self.server_session.save_run(
                        payload.get("slot", 1), name=payload.get("name")
                    )
                except ValueError as exc:
                    self.send_json_response({"ok": False, "error": str(exc)}, HTTPStatus.BAD_REQUEST)
                    return
                self.send_json_response({"ok": ok, "message": msg, "state": self.server_session.get_full_state()})
                return

            if action in ("rename_save", "rename"):
                try:
                    ok, msg = self.server_session.rename_save(
                        payload.get("slot", 1), payload.get("name", "")
                    )
                except ValueError as exc:
                    self.send_json_response({"ok": False, "error": str(exc)}, HTTPStatus.BAD_REQUEST)
                    return
                self.send_json_response({"ok": ok, "message": msg, "state": self.server_session.get_full_state()})
                return

            if action in ("delete_save", "delete"):
                try:
                    ok, msg = self.server_session.delete_save(payload.get("slot", 1))
                except ValueError as exc:
                    self.send_json_response({"ok": False, "error": str(exc)}, HTTPStatus.BAD_REQUEST)
                    return
                self.send_json_response({"ok": ok, "message": msg, "state": self.server_session.get_full_state()})
                return

            if action == "reset_career":
                if str(payload.get("confirm", "")) != "RESET":
                    self.send_json_response(
                        {"ok": False, "error": "Career reset requires confirm RESET."},
                        HTTPStatus.BAD_REQUEST,
                    )
                    return
                state = self.server_session.reset_career()
                if state is None:
                    self.send_json_response(
                        {"ok": False, "error": "Career backup failed; reset aborted."},
                        HTTPStatus.INTERNAL_SERVER_ERROR,
                    )
                    return
                self.send_json_response({"ok": True, "message": "Career reset.", "state": state})
                return

            if action in ("rename_alias", "alias"):
                ok, msg = self.server_session.rename_alias(payload.get("name", ""))
                self.send_json_response({"ok": ok, "message": msg, "state": self.server_session.get_full_state()})
                return

            if action == "load":
                try:
                    ok, msg = self.server_session.load_run(payload.get("slot", 1))
                except ValueError as exc:
                    self.send_json_response({"ok": False, "error": str(exc)}, HTTPStatus.BAD_REQUEST)
                    return
                self.send_json_response({"ok": ok, "message": msg, "state": self.server_session.get_full_state()})
                return

            if action == "scan":
                ok, msg, _ = engine.scan_surroundings()
                self.send_json_response({"ok": ok, "message": msg, "state": self.server_session.get_full_state()})
                return

            if action == "move":
                target = payload.get("target")
                ok, msg = engine.move_to(target)
                self.send_json_response({"ok": ok, "message": msg, "state": self.server_session.get_full_state()})
                return

            if action == "spoof":
                ok, msg = engine.spoof_ip()
                self.send_json_response({"ok": ok, "message": msg, "state": self.server_session.get_full_state()})
                return

            if action == "overdrive":
                ok, msg = engine.overdrive()
                self.send_json_response({"ok": ok, "message": msg, "state": self.server_session.get_full_state()})
                return

            if action == "stance":
                stance = payload.get("stance", "")
                ok, msg = engine.set_stance(stance)
                self.send_json_response({"ok": ok, "message": msg, "state": self.server_session.get_full_state()})
                return

            if action in ("proxy", "add_proxy"):
                target = payload.get("target") or ""
                ok, msg = engine.add_proxy_hop(target)
                self.send_json_response({"ok": ok, "message": msg, "state": self.server_session.get_full_state()})
                return

            if action in ("sever_proxy", "unproxy"):
                target = payload.get("target")
                ok, msg = engine.sever_proxy(target)
                self.send_json_response({"ok": ok, "message": msg, "state": self.server_session.get_full_state()})
                return

            if action == "quickhack":
                target = payload.get("target") or ""
                ok, msg = engine.quickhack(target)
                self.send_json_response({"ok": ok, "message": msg, "state": self.server_session.get_full_state()})
                return

            if action == "intel":
                mode = payload.get("mode", "reveal")
                target = payload.get("target") or ""
                ok, msg = engine.spend_threat_intel(mode, target)
                self.send_json_response({"ok": ok, "message": msg, "state": self.server_session.get_full_state()})
                return

            if action in ("lay_low", "wait"):
                ok, msg = engine.lay_low(payload.get("turns", 1))
                self.send_json_response({"ok": ok, "message": msg, "state": self.server_session.get_full_state()})
                return

            if action in ("contact", "talk", "interact"):
                contact_id = payload.get("contact_id") or payload.get("target") or ""
                mode = payload.get("mode", "talk")
                ok, msg, report = engine.interact_contact(contact_id, mode)
                self.send_json_response({
                    "ok": ok,
                    "message": msg,
                    "report": report,
                    "state": self.server_session.get_full_state(),
                })
                return

            if action == "accept_quest":
                quest_id = payload.get("quest_id") or payload.get("target") or ""
                ok, msg = engine.accept_quest(quest_id)
                self.send_json_response({"ok": ok, "message": msg, "state": self.server_session.get_full_state()})
                return

            if action == "accept_contract":
                contract_id = payload.get("contract_id") or payload.get("target") or ""
                ok, msg = engine.accept_contract(contract_id)
                self.send_json_response({"ok": ok, "message": msg, "state": self.server_session.get_full_state()})
                return

            if action == "drop_offer":
                contract_id = payload.get("contract_id") or payload.get("target") or ""
                ok, msg = engine.drop_offer(contract_id)
                self.send_json_response({"ok": ok, "message": msg, "state": self.server_session.get_full_state()})
                return

            if action == "decline_contract":
                ok, msg = engine.decline_contract()
                self.send_json_response({"ok": ok, "message": msg, "state": self.server_session.get_full_state()})
                return

            if action == "jackout":
                ok, msg = engine.jackout()
                self.send_json_response({"ok": ok, "message": msg, "state": self.server_session.get_full_state()})
                return

            if action == "exploit":
                name = payload.get("name")
                target = payload.get("target")
                ok, msg = engine.use_exploit(name, target)
                self.send_json_response({"ok": ok, "message": msg, "state": self.server_session.get_full_state()})
                return

            if action in ("counter", "counter_hunter"):
                method = payload.get("method", "logic_bomb")
                ok, msg = engine.counter_hunter(method=method)
                self.send_json_response({"ok": ok, "message": msg, "state": self.server_session.get_full_state()})
                return

            if action in ("counter_rival", "trace_rival"):
                ok, msg = engine.counter_rival()
                self.send_json_response({"ok": ok, "message": msg, "state": self.server_session.get_full_state()})
                return

            if action in ("reroll_contracts", "reroll"):
                ok, msg = engine.reroll_contract_offers()
                self.send_json_response({"ok": ok, "message": msg, "state": self.server_session.get_full_state()})
                return

            if action == "shop_buy":
                item_id = payload.get("item_id")
                item = shop.catalog.get(item_id)
                multiplier = engine.shop_price_multiplier()
                ok, msg = shop.purchase(engine.deck, item_id, price_multiplier=multiplier)
                if ok and (item is None or item.category != "consumable"):
                    profile = save_mgr.load_career()
                    profile.purchased_upgrades.append(item_id)
                    profile.banked_creds = engine.deck.cryptocreds
                    save_mgr.save_career(profile)
                self.send_json_response({"ok": ok, "message": msg, "state": self.server_session.get_full_state()})
                return

            if action == "probe":
                target = payload.get("target") or engine.state.current_node_id
                ok, msg, report = engine.probe_host(target)
                self.send_json_response({"ok": ok, "message": msg, "report": report, "state": self.server_session.get_full_state()})
                return

            if action == "exploit_service":
                target = payload.get("target") or engine.state.current_node_id
                try:
                    port = int(payload.get("port", 0))
                except (TypeError, ValueError):
                    self.send_json_response({"ok": False, "error": "Port must be an integer"}, HTTPStatus.BAD_REQUEST)
                    return
                cve_id = payload.get("cve_id")
                ok, msg = engine.exploit_service(target, port, cve_id=cve_id)
                self.send_json_response({"ok": ok, "message": msg, "state": self.server_session.get_full_state()})
                return

            if action in ("bypass_firewall", "bypass"):
                target = payload.get("target") or engine.state.current_node_id
                try:
                    port = int(payload.get("port", 0))
                except (TypeError, ValueError):
                    self.send_json_response({"ok": False, "error": "Port must be an integer"}, HTTPStatus.BAD_REQUEST)
                    return
                method = payload.get("method", "knock")
                ok, msg = engine.bypass_firewall(target, port, method)
                self.send_json_response({"ok": ok, "message": msg, "state": self.server_session.get_full_state()})
                return

            if action in ("evade_av", "evade"):
                target = payload.get("target") or engine.state.current_node_id
                method = payload.get("method", "rootkit")
                ok, msg = engine.evade_antivirus(target, method)
                self.send_json_response({"ok": ok, "message": msg, "state": self.server_session.get_full_state()})
                return

            if action in ("social", "social_engineer"):
                target = payload.get("target") or engine.state.current_node_id
                vector = payload.get("vector", "spear_phish")
                employee = payload.get("employee")
                ok, msg, report = engine.social_engineer(target, vector, employee)
                self.send_json_response({"ok": ok, "message": msg, "report": report, "state": self.server_session.get_full_state()})
                return

            if action == "list_files":
                target = payload.get("target")
                ok, msg, files = engine.list_files(target)
                self.send_json_response({
                    "ok": ok,
                    "message": msg,
                    "files": [f.to_dict() if hasattr(f, "to_dict") else f for f in files],
                    "state": self.server_session.get_full_state(),
                })
                return

            if action == "read_file":
                target = payload.get("target") or engine.state.current_node_id
                file_path = payload.get("path", "")
                ok, msg, content = engine.read_file(target, file_path)
                self.send_json_response({"ok": ok, "message": msg, "content": content, "state": self.server_session.get_full_state()})
                return

            if action in ("download_file", "steal"):
                target = payload.get("target") or engine.state.current_node_id
                file_path = payload.get("path", "")
                ok, msg, vfile = engine.download_file(target, file_path)
                self.send_json_response({
                    "ok": ok,
                    "message": msg,
                    "file": vfile.to_dict() if vfile and hasattr(vfile, "to_dict") else None,
                    "state": self.server_session.get_full_state(),
                })
                return

            if action == "wipe_logs":
                target = payload.get("target") or engine.state.current_node_id
                ok, msg = engine.wipe_logs(target)
                self.send_json_response({"ok": ok, "message": msg, "state": self.server_session.get_full_state()})
                return

            if action == "phish":
                target = payload.get("target") or engine.state.current_node_id
                ok, msg, report = engine.phish_target(target)
                self.send_json_response({"ok": ok, "message": msg, "report": report, "state": self.server_session.get_full_state()})
                return

            if action == "craft":
                recipe = payload.get("recipe") or payload.get("recipe_id") or ""
                ok, msg = engine.craft_virus(recipe)
                if ok:
                    profile = save_mgr.load_career()
                    profile.banked_creds = engine.deck.cryptocreds
                    save_mgr.save_career(profile)
                self.send_json_response({"ok": ok, "message": msg, "state": self.server_session.get_full_state()})
                return

            if action == "deploy_daemon":
                target = payload.get("target") or engine.state.current_node_id
                daemon_type = payload.get("daemon_type", "keylogger")
                ok, msg = engine.deploy_daemon(target, daemon_type)
                self.send_json_response({"ok": ok, "message": msg, "state": self.server_session.get_full_state()})
                return

            if action == "kill_process":
                try:
                    pid = int(payload.get("pid", payload.get("target", 0)))
                except (TypeError, ValueError):
                    self.send_json_response({"ok": False, "error": "PID must be a number"}, HTTPStatus.BAD_REQUEST)
                    return
                from cyberpulse.deckos import kill_process as _kill
                ok, msg = _kill(engine, pid)
                self.send_json_response({"ok": ok, "message": msg, "state": self.server_session.get_full_state()})
                return

            if action == "reset":
                seed = payload.get("seed")
                if seed is not None:
                    try:
                        seed = coerce_seed(seed)
                    except (TypeError, ValueError):
                        self.send_json_response({"ok": False, "error": "Seed must be a finite number"}, HTTPStatus.BAD_REQUEST)
                        return
                daily = bool(payload.get("daily"))
                difficulty = payload.get("difficulty", "normal")
                allegiance = payload.get("allegiance", "none")
                state = self.server_session.reset_game(
                    seed, daily=daily, difficulty=difficulty, allegiance=allegiance
                )
                message = (
                    f"Daily run {state['daily_key']} started."
                    if daily else "Neural link reset."
                )
                self.send_json_response({"ok": True, "message": message, "state": state})
                return

            self.send_json_response({"ok": False, "error": f"Unknown action '{action}'"}, HTTPStatus.BAD_REQUEST)
            return

        if path == "/api/puzzle/solve":
            p = self.server_session.active_puzzle
            node_id = self.server_session.active_puzzle_node_id

            if not p or not node_id:
                self.send_json_response({"ok": False, "error": "No active hacking puzzle"}, HTTPStatus.BAD_REQUEST)
                return

            engine = self.server_session.engine
            if engine.state.is_game_over or engine.state.is_jacked_out or engine.state.is_victory:
                self.send_json_response({"ok": False, "error": "Session is no longer active"}, HTTPStatus.BAD_REQUEST)
                return
            node = engine.nodes.get(node_id)
            if node is None or engine.pending_puzzles.get(node_id) is not p:
                self.server_session.active_puzzle = None
                self.server_session.active_puzzle_node_id = None
                self.send_json_response({"ok": False, "error": "Puzzle is no longer active"}, HTTPStatus.BAD_REQUEST)
                return

            guess = payload.get("guess")
            solved = False
            near_miss = False
            near_miss_bonus = False
            message = ""
            exhausted = False

            if isinstance(p, FrequencyPuzzle):
                try:
                    val = float(guess)
                except (ValueError, TypeError):
                    self.send_json_response({"ok": False, "error": "Invalid frequency numeric value"}, HTTPStatus.BAD_REQUEST)
                    return
                solved, message = p.tune(val)
                near_miss = p.near_miss
                bonus_message = engine.resolve_puzzle_near_miss(p)
                if bonus_message:
                    near_miss_bonus = True
                    message = f"{message}\n{bonus_message}"
                exhausted = not solved and p.attempts_left <= 0
                if exhausted:
                    _, lockdown_message = engine.register_puzzle_failure(
                        node_id, f"intrusion script burned out on {node.hostname}"
                    )
                    message = f"{message}\n{lockdown_message}"

            elif isinstance(p, BufferPuzzle):
                if not isinstance(guess, list):
                    self.send_json_response({"ok": False, "error": "Guess must be a sequence list"}, HTTPStatus.BAD_REQUEST)
                    return
                solved, message = p.verify_sequence(guess)
                near_miss = p.near_miss
                bonus_message = engine.resolve_puzzle_near_miss(p)
                if bonus_message:
                    near_miss_bonus = True
                    message = f"{message}\n{bonus_message}"
                if not solved and not bonus_message:
                    _, lockdown_message = engine.register_puzzle_failure(
                        node_id, f"buffer injection corrupted on {node.hostname}"
                    )
                    message = f"{message}\n{lockdown_message}"
                    exhausted = True

            elif isinstance(p, HashCrackPuzzle):
                solved, message = p.guess(str(guess))
                near_miss = p.near_miss
                bonus_message = engine.resolve_puzzle_near_miss(p)
                if bonus_message:
                    near_miss_bonus = True
                    message = f"{message}\n{bonus_message}"
                exhausted = not solved and p.attempts_left <= 0
                if exhausted:
                    _, lockdown_message = engine.register_puzzle_failure(
                        node_id, f"hash crack locked out on {node.hostname}"
                    )
                    message = f"{message}\n{lockdown_message}"

            if solved:
                engine.clear_pending_puzzle(node_id)
                engine.complete_breach(node_id)
                self.server_session.active_puzzle = None
                self.server_session.active_puzzle_node_id = None
            elif exhausted:
                engine.clear_pending_puzzle(node_id)
                self.server_session.active_puzzle = None
                self.server_session.active_puzzle_node_id = None

            attempts_left = getattr(p, "attempts_left", 0)
            self.send_json_response({
                "ok": True,
                "solved": solved,
                "near_miss": near_miss,
                "near_miss_bonus": near_miss_bonus,
                "message": message,
                "attempts_left": attempts_left,
                "state": self.server_session.get_full_state(),
            })
            return

        self.send_json_response({"ok": False, "error": f"Unknown endpoint '{path}'"}, HTTPStatus.NOT_FOUND)


def create_server(
    host: str = "127.0.0.1",
    port: int = 8420,
    data_dir: Optional[Path] = None,
    seed: int = 1337,
    daily_key: str = "",
    difficulty: str = "normal",
    daily_modifier: str = "",
    allegiance: str = "none",
) -> ThreadingHTTPServer:
    """Instantiate and configure the ThreadingHTTPServer for CyberPulse Web Cyberdeck."""
    session = CyberdeckSession(
        data_dir=data_dir,
        seed=seed,
        daily_key=daily_key,
        difficulty=difficulty,
        daily_modifier=daily_modifier,
        allegiance=allegiance,
    )

    class CustomHandler(CyberdeckHTTPHandler):
        server_session = session

    server = ThreadingHTTPServer((host, port), CustomHandler)
    server.allow_reuse_address = True
    return server


def run_web(
    host: str = "127.0.0.1",
    port: int = 8420,
    data_dir: Optional[Path] = None,
    seed: int = 1337,
    open_browser: bool = True,
    daily_key: str = "",
    difficulty: str = "normal",
    daily_modifier: str = "",
    allegiance: str = "none",
) -> None:
    """Launch the Web Cyberdeck server and optionally launch default system web browser."""
    import webbrowser

    server = create_server(
        host=host, port=port, data_dir=data_dir, seed=seed,
        daily_key=daily_key, difficulty=difficulty, daily_modifier=daily_modifier,
        allegiance=allegiance,
    )
    url = f"http://{host}:{port}"
    print(f"\n+==========================================================================+")
    print(f"|            >> CYBERPULSE // WEB CYBERDECK ONLINE <<                     |")
    print(f"+==========================================================================+")
    print(f"[*] Visual Interface:  {url}")
    print(f"[*] World Seed:        {seed}")
    print(f"[*] Standard Library:  Pure Python 3 (Zero External Packages)")
    print(f"[*] Terminate:         Press Ctrl+C to sever neural connection")
    print(f"+==========================================================================+\n")

    if open_browser:
        webbrowser.open_new_tab(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Severing cyberdeck web connection.")
    finally:
        server.server_close()


if __name__ == "__main__":
    run_web(open_browser=True)
