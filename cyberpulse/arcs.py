"""Operative loyalty arcs + district grid simulation (additive, save-compatible).

Arcs reward sustained trust with each operative across three tiers. Several
stages carry live mechanical bonuses (checked by the engine at the point of
use); the rest are fiction and dossier flavor. Districts give the living
grid a street-level simulation layer: each district reports load, patrol
weight, and market mood derived deterministically from (seed, tick, alert).
"""

import hashlib
from typing import Any, Dict, List

from cyberpulse.models import Quest

ARC_DEFS: Dict[str, Dict[str, Any]] = {
    "mira": {
        "title": "Syndicate Ledger",
        "stages": (
            {"trust": 2, "label": "Reliable Asset",
             "text": "Mira starts routing priority contracts to you first.",
             "bonus": "+1 turn rush window on Syndicate contracts."},
            {"trust": 4, "label": "Fixer's Confidant",
             "text": "Mira admits the dead courier was her runner. She owes you the truth.",
             "bonus": "Declining Syndicate contracts costs no trust."},
            {"trust": 6, "label": "Syndicate Ghost",
             "text": "Mira scrubs your name pre-emptively whenever alert spikes.",
             "bonus": "Alert decay +1/turn while a Syndicate contract is active."},
        ),
    },
    "kilo": {
        "title": "Ghost Circuit",
        "stages": (
            {"trust": 2, "label": "Bench Regular",
             "text": "Kilo leaves a spare cooling cell on your rig after every job.",
             "bonus": "Overdrive costs 1 CPU."},
            {"trust": 4, "label": "Circuit Family",
             "text": "Kilo teaches you the ghost-boot trick the dead courier used.",
             "bonus": "Daemon yields +10% per tick."},
            {"trust": 6, "label": "Street Legend",
             "text": "The Ghost Circuit paints your handle on the night-market wall.",
             "bonus": "Street standing gains +1 per victory."},
        ),
    },
    "archivist": {
        "title": "Dead Letters",
        "stages": (
            {"trust": 2, "label": "Catalogued",
             "text": "The Archivist files you under 'still breathing' and opens a side channel.",
             "bonus": "One extra contract offer slot."},
            {"trust": 4, "label": "Trusted Reader",
             "text": "The Archivist shows you the redacted page: NEXUS was a census before it was a weapon.",
             "bonus": "Wipe-logs scrubs 5% extra trace."},
            {"trust": 6, "label": "Living Archive",
             "text": "The Archive starts writing your run into the permanent record.",
             "bonus": "Epilogue gains a dedicated archive stanza."},
        ),
    },
    "zero": {
        "title": "Mirror Runner",
        "stages": (
            {"trust": 2, "label": "Worthy Opponent",
             "text": "Zero stops probing your link and starts leaving tips instead.",
             "bonus": "Counter-trace costs 1 CPU."},
            {"trust": 4, "label": "Parallel Ghost",
             "text": "Zero admits they cracked Black ICE once and it grew back. You are the second try.",
             "bonus": "Black ICE nodes show an extra forecast line."},
            {"trust": 6, "label": "Zero's Equal",
             "text": "Zero offers the alliance early: no Act III theatrics, just two ghosts.",
             "bonus": "Act III choice epilogue extended."},
        ),
    },
}

# Two new side-quest blueprints reusing existing quest objectives (no engine changes).
ARC_QUEST_BLUEPRINTS: List[Dict[str, Any]] = [
    {
        "quest_id": "q_arc_cold_wallet",
        "title": "Cold Wallet",
        "description": "Steal 2 data files from any breached hosts for Kilo's ghost-boot fund.",
        "objective": "steal_file",
        "target": "",
        "required": 2,
        "reward_creds": 160,
        "giver": "kilo",
        "story_act": 2,
        "story_chapter": 2,
        "accepted": False,
        "required_trust": 2,
    },
    {
        "quest_id": "q_arc_dead_letter",
        "title": "Dead Letter Drop",
        "description": "Deploy 1 keylogger daemon for the Archivist's dead-letter network.",
        "objective": "deploy_daemon",
        "target": "keylogger",
        "required": 1,
        "reward_creds": 140,
        "giver": "archivist",
        "story_act": 2,
        "story_chapter": 2,
        "accepted": False,
        "required_trust": 2,
    },
]

DISTRICTS = (
    {"key": "neon_row", "name": "Neon Row", "flavor": "night markets, chrome vendors"},
    {"key": "ledger_heights", "name": "Ledger Heights", "flavor": "Syndicate banks, audit towers"},
    {"key": "rust_yards", "name": "Rust Yards", "flavor": "chop shops, ghost-circuit benches"},
    {"key": "dead_archive", "name": "Dead Archive", "flavor": "data brokers, dead drops"},
    {"key": "black_ice_ward", "name": "Black ICE Ward", "flavor": "NetWatch precinct, hunter pens"},
)


def arc_stage(contact_id: str, trust: int) -> int:
    """Return how many arc stages (0-3) a trust value unlocks."""
    try:
        trust_value = int(trust)
    except (TypeError, ValueError):
        return 0
    if isinstance(trust, bool):
        return 0
    stages = ARC_DEFS.get(contact_id, {}).get("stages", ())
    reached = 0
    for stage in stages:
        if trust_value >= int(stage.get("trust", 99)):
            reached += 1
    return reached


def stage_info(contact_id: str, stage: int) -> Dict[str, Any]:
    """Return the label/text/bonus of an arc stage (stage 1-3)."""
    try:
        if isinstance(stage, bool):
            return {"label": "", "text": "", "bonus": ""}
        wanted = int(stage)
    except (TypeError, ValueError):
        return {"label": "", "text": "", "bonus": ""}
    stages = ARC_DEFS.get(contact_id, {}).get("stages", ())
    if 1 <= wanted <= len(stages):
        info = stages[wanted - 1]
        return {"label": info.get("label", ""), "text": info.get("text", ""),
                "bonus": info.get("bonus", "")}
    return {"label": "", "text": "", "bonus": ""}


def arc_status(contacts: List[Any]) -> List[Dict[str, Any]]:
    """Summarize every operative's arc for CLI/Web/dossier consumers."""
    out: List[Dict[str, Any]] = []
    for contact in contacts or []:
        cid = getattr(contact, "contact_id", "?")
        trust = int(getattr(contact, "trust", 0))
        spec = ARC_DEFS.get(cid)
        if not spec:
            continue
        stage = arc_stage(cid, trust)
        nxt = spec["stages"][stage]["trust"] if stage < len(spec["stages"]) else None
        if stage:
            bonus = spec["stages"][stage - 1].get("bonus", "")
        elif spec["stages"]:
            bonus = f"Next @ trust {spec['stages'][0]['trust']}: {spec['stages'][0].get('bonus', '')}"
        else:
            bonus = ""
        out.append({
            "contact_id": cid,
            "name": getattr(contact, "name", cid),
            "arc": spec["title"],
            "trust": trust,
            "stage": stage,
            "next_trust": nxt,
            "stage_label": spec["stages"][stage - 1]["label"] if stage else "Unproven",
            "stage_text": spec["stages"][stage - 1]["text"] if stage else "Earn trust to open this arc.",
            "bonus": bonus,
        })
    return out


def _district_seed(seed: int, tick: int, key: str) -> int:
    """Deterministic district roll (hashlib, not hash(): stable across processes)."""
    digest = hashlib.sha256(f"cyberpulse-district:{int(seed)}:{int(tick)}:{key}".encode()).hexdigest()
    return int(digest[:8], 16)


def district_for_node(seed: int, node_id: str) -> Dict[str, Any]:
    """Tick-independent street mapping: every host lives in one district.

    Uses the same stable hash as the district grid (never `hash()`), so the
    address of a host is identical across processes, saves, and replays.
    """
    district = DISTRICTS[_district_seed(seed, 0, str(node_id)) % len(DISTRICTS)]
    return dict(district)


def district_grid(seed: int, tick: int, alert: int) -> List[Dict[str, Any]]:
    """Deterministic per-tick district simulation: load, patrol, market mood."""
    rows: List[Dict[str, Any]] = []
    for idx, district in enumerate(DISTRICTS):
        h = _district_seed(seed, tick, district["key"]) % 100
        load = min(100, max(5, (h + int(alert) // 2 + idx * 7) % 100))
        patrol = "heavy" if int(alert) >= 55 and (h + idx) % 3 == 0 else ("light" if int(alert) < 30 else "standard")
        mood = "surging" if load > 75 else ("quiet" if load < 30 else "steady")
        rows.append({
            "key": district["key"],
            "name": district["name"],
            "flavor": district["flavor"],
            "load": load,
            "patrol": patrol,
            "market_mood": mood,
        })
    return rows


ARC_EPILOGUES: Dict[str, str] = {
    "mira": "Mira closes your file herself. In the Syndicate ledger, you are a blank page that gets things done.",
    "kilo": "Kilo paints your handle on the night-market wall, big enough to read from orbit.",
    "archivist": "The Archivist binds your run into the permanent stacks, spine out.",
    "zero": "Zero files you under 'equal'. Nobody else has that folder.",
}


def arc_epilogue_lines(contacts: List[Any]) -> List[str]:
    """Epilogue stanzas for operatives whose loyalty arc reached stage 3."""
    lines: List[str] = []
    for contact in contacts or []:
        cid = getattr(contact, "contact_id", "?")
        if arc_stage(cid, int(getattr(contact, "trust", 0))) >= 3:
            line = ARC_EPILOGUES.get(cid)
            if line:
                lines.append(line)
    return lines


def live_bonuses(engine: Any) -> Dict[str, bool]:
    """Which arc mechanical bonuses are currently active for this run."""
    def trust(cid: str) -> int:
        for contact in getattr(engine.state, "contacts", []) or []:
            if getattr(contact, "contact_id", "") == cid:
                return int(getattr(contact, "trust", 0))
        return 0

    contract = getattr(engine.state, "active_contract", None)
    giver = getattr(contract, "giver", "") if contract else ""
    return {
        "mira_decay": arc_stage("mira", trust("mira")) >= 3 and giver == "mira",
        "kilo_yield": arc_stage("kilo", trust("kilo")) >= 2,
        "kilo_overdrive": arc_stage("kilo", trust("kilo")) >= 1,
        "archivist_wipe": arc_stage("archivist", trust("archivist")) >= 2,
        "zero_counter": arc_stage("zero", trust("zero")) >= 1,
    }


def ensure_arc_quests(engine: Any) -> int:
    """Backfill arc side-quests into old runs; returns number added."""
    try:
        existing = {q.quest_id for q in getattr(engine.state, "quests", [])}
    except (AttributeError, TypeError):
        return 0
    added = 0
    for blueprint in ARC_QUEST_BLUEPRINTS:
        if blueprint["quest_id"] not in existing:
            try:
                engine.state.quests.append(Quest(**blueprint))
            except (TypeError, AttributeError):
                continue
            added += 1
    return added
