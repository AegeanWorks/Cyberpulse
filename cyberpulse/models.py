"""Domain models for CyberPulse cyberspace nodes, decks, contracts, and career profiles."""

import math
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from cyberpulse.factions import normalize_standing


class NodeType:
    GATEWAY = "GATEWAY"
    FIREWALL = "FIREWALL"
    DATA_VAULT = "DATA_VAULT"
    ICE_DEFENSE = "ICE_DEFENSE"
    CENTRAL_CORE = "CENTRAL_CORE"


class NodeStatus:
    LOCKED = "LOCKED"
    DISCOVERED = "DISCOVERED"
    BREACHED = "BREACHED"


class RewardType:
    STANDARD = "STANDARD"
    CRITICAL_JACKPOT = "CRITICAL_JACKPOT"
    CHIP_DROP = "CHIP_DROP"


class OperatingStance:
    BALANCED = "balanced"
    STEALTH = "stealth"
    OVERCLOCK = "overclock"
    ANALYSIS = "analysis"


# ---------------------------------------------------------------------------
# Visual sprite metadata (presentation-only, never persisted in saves).
# Zero-dependency: glyph + CSS/canvas shape + palette key. Keeps the Python
# terminal map, the web canvas, and the legend in sync from one source.
# ---------------------------------------------------------------------------
NODE_VISUALS: Dict[str, Dict[str, str]] = {
    NodeType.GATEWAY: {
        "glyph": "◇", "shape": "diamond", "label": "GATEWAY",
        "hue": "cyan", "css_class": "sprite-gateway",
        "blurb": "Entry router",
    },
    NodeType.FIREWALL: {
        "glyph": "⬡", "shape": "hexagon", "label": "FIREWALL",
        "hue": "amber", "css_class": "sprite-firewall",
        "blurb": "Filtered chokepoint",
    },
    NodeType.DATA_VAULT: {
        "glyph": "▣", "shape": "vault", "label": "VAULT",
        "hue": "gold", "css_class": "sprite-vault",
        "blurb": "Loot store",
    },
    NodeType.ICE_DEFENSE: {
        "glyph": "▲", "shape": "triangle", "label": "BLACK ICE",
        "hue": "red", "css_class": "sprite-ice",
        "blurb": "Active countermeasure",
    },
    NodeType.CENTRAL_CORE: {
        "glyph": "⬢", "shape": "core", "label": "SUPERCORE",
        "hue": "magenta", "css_class": "sprite-core",
        "blurb": "Final objective",
    },
}

STATUS_VISUALS: Dict[str, Dict[str, str]] = {
    NodeStatus.LOCKED: {"glyph": "·", "css_class": "status-locked", "label": "SEALED"},
    NodeStatus.DISCOVERED: {"glyph": "◌", "css_class": "status-discovered", "label": "EXPOSED"},
    NodeStatus.BREACHED: {"glyph": "●", "css_class": "status-breached", "label": "BREACHED"},
}

STANCE_VISUALS: Dict[str, Dict[str, str]] = {
    OperatingStance.BALANCED: {"glyph": "◎", "label": "BALANCED"},
    OperatingStance.STEALTH: {"glyph": "◍", "label": "STEALTH"},
    OperatingStance.OVERCLOCK: {"glyph": "⚡", "label": "OVERCLOCK"},
    OperatingStance.ANALYSIS: {"glyph": "⌖", "label": "ANALYSIS"},
}


def node_visual(node_type: str, status: str = "") -> Dict[str, str]:
    """Return presentation metadata for a node type + status pair."""
    base = dict(NODE_VISUALS.get(node_type, NODE_VISUALS[NodeType.GATEWAY]))
    overlay = STATUS_VISUALS.get(status, {})
    if overlay:
        base = {**base, "status_glyph": overlay["glyph"],
                "status_label": overlay["label"],
                "status_class": overlay["css_class"]}
    return base


ENTITY_VISUALS: Dict[str, Dict[str, str]] = {
    "mira": {"glyph": "◆", "css_class": "avatar-fixer", "label": "FIXER"},
    "kilo": {"glyph": "⬢", "css_class": "avatar-techie", "label": "TECHIE"},
    "archivist": {"glyph": "▤", "css_class": "avatar-broker", "label": "BROKER"},
    "zero": {"glyph": "⬣", "css_class": "avatar-zero", "label": "ZERO"},
    "Vex": {"glyph": "✕", "css_class": "avatar-rival-vex", "label": "RIVAL"},
    "Marrow": {"glyph": "◍", "css_class": "avatar-rival-marrow", "label": "RIVAL"},
    "Static": {"glyph": "⚡", "css_class": "avatar-rival-static", "label": "RIVAL"},
    "hunter": {"glyph": "◉", "css_class": "avatar-hunter", "label": "HUNTER"},
    "hunter_confused": {"glyph": "◎", "css_class": "avatar-hunter-confused", "label": "HUNTER"},
    "hunter_dead": {"glyph": "○", "css_class": "avatar-hunter-dead", "label": "HUNTER"},
}

SHOP_VISUALS: Dict[str, Dict[str, str]] = {
    "overclock_cpu": {"glyph": "⚡", "css_class": "item-hardware", "label": "CPU"},
    "expand_ram": {"glyph": "▤", "css_class": "item-hardware", "label": "RAM"},
    "ice_dampener": {"glyph": "❄", "css_class": "item-hardware", "label": "ICE"},
    "logic_bomb": {"glyph": "✸", "css_class": "item-exploit", "label": "BOMB"},
    "ghost_protocol": {"glyph": "👻", "css_class": "item-exploit", "label": "GHOST"},
    "dead_mans_switch": {"glyph": "⛨", "css_class": "item-consumable", "label": "SAFE"},
}

PUZZLE_VISUALS: Dict[str, Dict[str, str]] = {
    "frequency": {"glyph": "∿", "css_class": "puzzle-freq", "label": "RESONANCE"},
    "buffer": {"glyph": "▦", "css_class": "puzzle-buffer", "label": "OVERFLOW"},
    "hash": {"glyph": "⌘", "css_class": "puzzle-hash", "label": "CIPHER"},
}

WORLD_VISUALS: Dict[str, Dict[str, str]] = {
    "GREEN": {"glyph": "●", "css_class": "posture-green", "label": "GREEN"},
    "AMBER": {"glyph": "●", "css_class": "posture-amber", "label": "AMBER"},
    "RED": {"glyph": "●", "css_class": "posture-red", "label": "RED"},
    "BLACK": {"glyph": "●", "css_class": "posture-black", "label": "BLACK"},
}


def entity_visual(key: str) -> Dict[str, str]:
    """Return presentation metadata for contacts, rivals, hunters, shop, puzzles."""
    for table in (ENTITY_VISUALS, SHOP_VISUALS, PUZZLE_VISUALS, WORLD_VISUALS):
        if key in table:
            return dict(table[key])
    return {"glyph": "·", "css_class": "avatar-unknown", "label": str(key).upper()[:12]}


@dataclass
class PortService:
    """An exposed TCP/UDP network service on a target host."""
    port: int
    service: str  # "ssh", "ftp", "http", "mysql", "smtp"
    version: str
    vulnerable: bool = True
    exploit_tool: str = "ssh_overflow"
    breached: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PortService":
        return cls(**data)


@dataclass
class VirtualFile:
    """A file stored on a target host's virtual filesystem."""
    path: str
    size_kb: int
    content: str
    is_target_data: bool = False
    value_creds: int = 150
    downloaded: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VirtualFile":
        return cls(**data)


@dataclass
class BountyContract:
    """A syndicate-issued objective with bonus rewards upon fulfillment (Zeigarnik Effect)."""
    contract_id: str
    title: str
    target_node_type: str
    target_ip: Optional[str] = None
    target_file: Optional[str] = None
    wipe_logs_required: bool = False
    max_trace_limit: int = 75
    reward_creds: int = 150
    completed: bool = False
    giver: str = ""
    risk_tier: str = "standard"
    objective: str = ""  # "", "breach", "extract", "wipe"; empty infers legacy behavior
    expires_turn: int = 0  # 0 = no deadline for legacy contracts
    rush_turn: int = 0     # complete at or before this turn for the rush bonus
    bonus_creds: int = 0   # rush bonus
    failed: bool = False
    description: str = ""
    offer_expires_turn: int = 0  # shelf life while the job sits on the board
    deadline_turns: int = 0      # window length applied when the job is accepted

    @property
    def objective_kind(self) -> str:
        """Return the explicit objective, or infer it from legacy contract fields."""
        if self.objective:
            return self.objective
        if self.wipe_logs_required:
            return "wipe"
        if self.target_file or self.target_ip:
            return "extract"
        return "breach"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BountyContract":
        return cls(**data)


@dataclass
class CareerProfile:
    """Persistent meta-progression profile tracking permanent stats and upgrades."""
    alias: str = "ZeroCool"
    banked_creds: int = 100
    lifetime_creds: int = 100
    successful_runs: int = 0
    failed_runs: int = 0
    current_streak: int = 0
    best_streak: int = 0
    best_combo: int = 0
    purchased_upgrades: List[str] = field(default_factory=list)
    run_history: List[Dict[str, Any]] = field(default_factory=list)
    achievements: List[str] = field(default_factory=list)
    daily_best: Dict[str, int] = field(default_factory=dict)
    daily_streak: int = 0
    best_daily_streak: int = 0
    last_daily_key: str = ""
    hall_of_fame: List[Dict[str, Any]] = field(default_factory=list)
    faction_standing: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CareerProfile":
        data_clean = dict(data)
        alias = " ".join(str(data_clean.get("alias", "ZeroCool") or "").split())[:24]
        data_clean["alias"] = alias or "ZeroCool"
        history = data_clean.get("run_history")
        if not isinstance(history, list):
            history = []
        data_clean["run_history"] = [entry for entry in history if isinstance(entry, dict)][-20:]
        achievements = data_clean.get("achievements")
        if not isinstance(achievements, list):
            achievements = []
        data_clean["achievements"] = list(dict.fromkeys(
            str(achievement) for achievement in achievements if isinstance(achievement, str)
        ))
        daily_best = data_clean.get("daily_best")
        if not isinstance(daily_best, dict):
            daily_best = {}
        cleaned_daily = {
            str(day): max(0, int(value))
            for day, value in daily_best.items()
            if (
                isinstance(day, str)
                and isinstance(value, (int, float))
                and not isinstance(value, bool)
                and math.isfinite(float(value))
            )
        }
        data_clean["daily_best"] = dict(sorted(cleaned_daily.items())[-30:])
        for field_name in ("daily_streak", "best_daily_streak"):
            value = data_clean.get(field_name, 0)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                value = 0
            data_clean[field_name] = value
        data_clean["best_daily_streak"] = max(
            data_clean["best_daily_streak"], data_clean["daily_streak"]
        )
        last_key = data_clean.get("last_daily_key", "")
        data_clean["last_daily_key"] = last_key if isinstance(last_key, str) else ""
        hall = data_clean.get("hall_of_fame")
        if not isinstance(hall, list):
            hall = []
        cleaned_hall: List[Dict[str, Any]] = []
        ranked_hall = sorted(
            (entry for entry in hall if isinstance(entry, dict)),
            key=lambda entry: int(entry.get("score", 0)) if isinstance(entry.get("score", 0), int) else 0,
            reverse=True,
        )
        seen_runs = set()
        for entry in ranked_hall:
            run_id = entry.get("run_id")
            if run_id and run_id in seen_runs:
                continue
            if run_id:
                seen_runs.add(run_id)
            cleaned_hall.append(dict(entry))
            if len(cleaned_hall) >= 10:
                break
        data_clean["hall_of_fame"] = cleaned_hall
        data_clean["faction_standing"] = normalize_standing(
            data_clean.get("faction_standing")
        )
        return cls(**data_clean)


@dataclass
class RivalNetrunner:
    """A named competitor who works the same Syndicate board during a run."""
    name: str
    handle: str
    skill: int
    tagline: str = ""
    next_move_turn: int = 6
    contracts_stolen: int = 0
    status: str = "active"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RivalNetrunner":
        clean = dict(data)
        clean.setdefault("name", "Unknown")
        clean.setdefault("handle", "unknown")
        for field_name, default in (("skill", 1), ("next_move_turn", 6), ("contracts_stolen", 0)):
            try:
                clean[field_name] = int(clean.get(field_name, default))
            except (TypeError, ValueError):
                clean[field_name] = default
        clean["skill"] = max(1, min(3, clean["skill"]))
        clean["next_move_turn"] = max(1, clean["next_move_turn"])
        clean["contracts_stolen"] = max(0, clean["contracts_stolen"])
        return cls(**clean)


class FirewallPolicy:
    ALLOW_ALL = "ALLOW_ALL"
    FILTER_PORTS = "FILTER_PORTS"
    STRICT_DROP = "STRICT_DROP"


@dataclass
class FirewallRule:
    """A packet filtering or port access rule enforced by a host firewall."""
    rule_id: str
    port: int
    action: str = "BLOCK"  # "BLOCK", "ALLOW"
    bypassed: bool = False
    bypass_method: Optional[str] = None  # "knock", "fragment", "tunnel"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FirewallRule":
        return cls(**data)


@dataclass
class HostFirewall:
    """A network firewall defending a host's open ports against unauthorized ingress."""
    enabled: bool = True
    policy: str = FirewallPolicy.FILTER_PORTS
    firewall_type: str = "Stateful-Packet-Filter"
    rules: List[FirewallRule] = field(default_factory=list)
    tampered: bool = False

    def is_port_blocked(self, port: int) -> bool:
        if not self.enabled or self.tampered:
            return False
        for rule in self.rules:
            if rule.port == port and rule.action == "BLOCK" and not rule.bypassed:
                return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        res = asdict(self)
        res["rules"] = [r.to_dict() if hasattr(r, "to_dict") else r for r in self.rules]
        return res

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HostFirewall":
        clean = dict(data)
        if "rules" in clean and isinstance(clean["rules"], list):
            clean["rules"] = [
                FirewallRule.from_dict(r) if isinstance(r, dict) else r for r in clean["rules"]
            ]
        return cls(**clean)


@dataclass
class HostAntivirus:
    """An active endpoint detection and response (EDR) / antivirus service on a target host."""
    name: str = "SentinelCore EDR"
    version: str = "v4.2"
    enabled: bool = True
    alert_level: int = 0          # 0% to 100%
    heuristic_sensitivity: int = 3 # 1 (low) to 5 (high)
    evaded: bool = False           # True if player has hooked/blinded the AV
    quarantine_log: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HostAntivirus":
        return cls(**data)


@dataclass
class ExploitPayload:
    """A weaponized vulnerability exploit / CVE targeting specific network services."""
    cve_id: str                    # e.g. "CVE-2024-38812"
    name: str                      # e.g. "SSH Buffer Overflow"
    target_service: str            # "ssh", "ftp", "http", "mysql", "smtp", "any"
    required_ram_mb: int = 16
    cpu_cost: int = 2
    stealth_rating: int = 3        # 1 (noisy, triggers AV) to 5 (stealthy zero-day)
    damage_trace: int = 10         # Trace generated on launch
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExploitPayload":
        return cls(**data)


class SocialVectorType:
    PRETEXT = "pretext"         # Impersonating Internal IT support requesting urgent cred reset
    BAIT = "bait"               # Dropping infected simulated USB / trojan PDF document
    SPEAR_PHISH = "spear_phish" # Executive CEO fraud urgent wire / credential lure
    VISHING = "vishing"         # Voice-phishing helpdesk operator for MFA token


class SecurityAwarenessLevel:
    NAIVE = "NAIVE"             # 85% success on all vectors
    STANDARD = "STANDARD"       # 55% success, requires pretext/bait
    PARANOID = "PARANOID"       # 25% success, requires spear_phish/vishing


@dataclass
class EmployeeProfile:
    """Target organization employee persona susceptible to social engineering attacks."""
    name: str
    role: str                   # "Helpdesk Operator", "DevOps Engineer", "CFO", "Marketing Intern"
    email: str
    awareness_level: str = SecurityAwarenessLevel.STANDARD
    compromised: bool = False
    leaked_credential: Optional[str] = None
    work_shift: str = "day"  # "day" (06-18), "night" (18-06), or "swing"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EmployeeProfile":
        return cls(**data)


@dataclass
class Node:
    """A target host or infrastructure subsystem on the network grid."""
    node_id: str
    name: str
    node_type: str
    security_level: int
    status: str = NodeStatus.LOCKED
    connected_ids: List[str] = field(default_factory=list)
    trace_rate: int = 10
    credits_reward: int = 0
    data_payload: Optional[str] = None
    puzzle_type: Optional[str] = None  # "frequency", "buffer", "hash"
    ip_address: str = "127.0.0.1"
    hostname: str = "localhost"
    ports: List[PortService] = field(default_factory=list)
    filesystem: List[VirtualFile] = field(default_factory=list)
    logs_cleared: bool = False
    firewall: Optional[HostFirewall] = None
    antivirus: Optional[HostAntivirus] = None
    employees: List[EmployeeProfile] = field(default_factory=list)
    breached_turn: int = -1      # turn the host was breached; -1 = never
    reward_claimed: bool = False  # fresh data already looted, so re-breaches pay nothing
    failed_attempts: int = 0      # burned intrusion scripts on this host
    lockdown_until_turn: int = -1  # host ICE refuses new puzzle/service intrusions until this turn
    os_name: str = "Unknown OS"   # host fingerprint: operating system
    uptime_hours: int = 0         # host fingerprint: time since last reboot
    patch_level: str = "patch-unknown"  # host fingerprint: last patch train

    def to_dict(self) -> Dict[str, Any]:
        res = asdict(self)
        res["ports"] = [p.to_dict() if hasattr(p, "to_dict") else p for p in self.ports]
        res["filesystem"] = [f.to_dict() if hasattr(f, "to_dict") else f for f in self.filesystem]
        if self.firewall:
            res["firewall"] = self.firewall.to_dict() if hasattr(self.firewall, "to_dict") else self.firewall
        if self.antivirus:
            res["antivirus"] = self.antivirus.to_dict() if hasattr(self.antivirus, "to_dict") else self.antivirus
        res["employees"] = [e.to_dict() if hasattr(e, "to_dict") else e for e in self.employees]
        return res

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Node":
        data_clean = dict(data)
        if "ports" in data_clean and isinstance(data_clean["ports"], list):
            data_clean["ports"] = [
                PortService.from_dict(p) if isinstance(p, dict) else p for p in data_clean["ports"]
            ]
        if "filesystem" in data_clean and isinstance(data_clean["filesystem"], list):
            data_clean["filesystem"] = [
                VirtualFile.from_dict(f) if isinstance(f, dict) else f for f in data_clean["filesystem"]
            ]
        if "firewall" in data_clean and isinstance(data_clean["firewall"], dict):
            data_clean["firewall"] = HostFirewall.from_dict(data_clean["firewall"])
        if "antivirus" in data_clean and isinstance(data_clean["antivirus"], dict):
            data_clean["antivirus"] = HostAntivirus.from_dict(data_clean["antivirus"])
        if "employees" in data_clean and isinstance(data_clean["employees"], list):
            data_clean["employees"] = [
                EmployeeProfile.from_dict(e) if isinstance(e, dict) else e for e in data_clean["employees"]
            ]
        return cls(**data_clean)


@dataclass
class MalwareDaemon:
    """An active background script deployed on a compromised host (e.g. keylogger, siphon)."""
    daemon_id: str
    daemon_type: str  # "keylogger", "siphon", "worm"
    target_node_id: str
    target_ip: str
    yield_per_turn: int = 25
    detection_risk: int = 4
    turns_active: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MalwareDaemon":
        return cls(**data)


@dataclass
class VirusCraftRecipe:
    """A crafting recipe to synthesize custom virus/malware chips in the netrunner workshop."""
    name: str
    vector: str   # "stealth", "brute", "worm"
    payload: str  # "keylogger", "credit_siphon", "trace_wipe", "logic_overload"
    cost_creds: int = 100
    cpu_cost: int = 2
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VirusCraftRecipe":
        return cls(**data)


@dataclass
class CyberDeck:
    """The player's hardware deck used to execute hacking exploits."""
    model_name: str = "Onyx-Vortex 400"
    cpu_cycles: int = 10
    max_cpu: int = 10
    ram_mb: int = 64
    max_ram: int = 64
    cryptocreds: int = 100
    exploits: List[str] = field(default_factory=lambda: ["port_scan", "buffer_overflow", "spoof_ip"])
    ice_dampener_level: int = 0
    overclock_level: int = 0
    ram_boost_level: int = 0
    local_ip: str = "10.99.0.2"
    local_hostname: str = "rig.netrunner.local"
    local_filesystem: List[VirtualFile] = field(default_factory=lambda: [
        VirtualFile(path="/home/deck/notes.txt", size_kb=2, content="NETRUNNER LOG:\n- Target Alpha router: 192.168.1.10\n- Target Finance Vault: 10.0.4.15\n- Target Supercore: 172.16.80.1"),
        VirtualFile(path="/bin/netrunner.sh", size_kb=4, content="#!/bin/sh\n# Cyberdeck intrusion helper matrix\necho 'Rig online. Neural link active.'"),
        VirtualFile(path="/loot/README.md", size_kb=1, content="# Loot Directory\nExfiltrated target data files are saved here automatically."),
    ])
    active_daemons: List[MalwareDaemon] = field(default_factory=list)
    known_cves: List[str] = field(default_factory=lambda: [
        "CVE-2024-38812",
        "CVE-2023-22515",
        "CVE-2024-21413",
        "CVE-2024-6387",
        "CVE-2023-38606",
        "CVE-2011-2523",
        "CVE-2022-0778",
        "CVE-2025-9901",
    ])
    operating_stance: str = OperatingStance.BALANCED
    proxy_chain: List[str] = field(default_factory=list)
    threat_intel_count: int = 0
    extraction_insurance: bool = False

    def to_dict(self) -> Dict[str, Any]:
        res = asdict(self)
        res["local_filesystem"] = [f.to_dict() if hasattr(f, "to_dict") else f for f in self.local_filesystem]
        res["active_daemons"] = [d.to_dict() if hasattr(d, "to_dict") else d for d in self.active_daemons]
        return res

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CyberDeck":
        clean = dict(data)
        if "local_filesystem" in clean and isinstance(clean["local_filesystem"], list):
            clean["local_filesystem"] = [
                VirtualFile.from_dict(f) if isinstance(f, dict) else f for f in clean["local_filesystem"]
            ]
        if "active_daemons" in clean and isinstance(clean["active_daemons"], list):
            clean["active_daemons"] = [
                MalwareDaemon.from_dict(d) if isinstance(d, dict) else d for d in clean["active_daemons"]
            ]
        if "known_cves" not in clean:
            clean["known_cves"] = ["CVE-2024-38812", "CVE-2023-22515", "CVE-2024-21413", "CVE-2025-9901"]
        if "operating_stance" not in clean:
            clean["operating_stance"] = OperatingStance.BALANCED
        if "proxy_chain" not in clean:
            clean["proxy_chain"] = []
        if "threat_intel_count" not in clean:
            clean["threat_intel_count"] = 0
        return cls(**clean)


def apply_career_profile(deck: CyberDeck, profile: CareerProfile) -> None:
    """Apply persistent upgrades and synchronize banked funds into an active cyberdeck."""
    deck.cryptocreds = profile.banked_creds
    for up in profile.purchased_upgrades:
        if up == "overclock_cpu":
            deck.overclock_level += 1
            deck.max_cpu += 2
            deck.cpu_cycles = max(deck.cpu_cycles, deck.max_cpu)
        elif up == "expand_ram":
            deck.ram_boost_level += 1
            deck.max_ram += 32
            deck.ram_mb = max(deck.ram_mb, deck.max_ram)
        elif up == "ice_dampener":
            deck.ice_dampener_level += 1
        elif up not in deck.exploits:
            deck.exploits.append(up)


@dataclass
class Quest:
    """A tracked story or side objective with a reward."""
    quest_id: str
    title: str
    description: str
    objective: str  # breach_type, breach_count, steal_file, wipe_logs, social_vector, deploy_daemon, craft_recipe, finish_run
    target: str = ""
    required: int = 1
    progress: int = 0
    reward_creds: int = 0
    reward_item: str = ""
    giver: str = ""
    story_act: int = 1
    story_chapter: int = 1
    accepted: bool = False
    completed: bool = False
    required_trust: int = 0

    @property
    def ready(self) -> bool:
        return self.progress >= max(1, self.required)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Quest":
        return cls(**data)


@dataclass
class ContactProfile:
    """A persistent in-game operative the player can talk to, work for, and call favors on."""
    contact_id: str
    name: str
    handle: str
    role: str
    faction: str
    tagline: str = ""
    unlock_act: int = 1
    trust: int = 0
    favor_used: bool = False
    bonus_favor_used: bool = False
    quest_id: str = ""
    secondary_quest_id: str = ""

    @property
    def trust_tier(self) -> str:
        if self.trust >= 6:
            return "Inner Circle"
        if self.trust >= 3:
            return "Trusted"
        return "Neutral"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContactProfile":
        return cls(**data)


@dataclass
class NewsItem:
    """A single living-grid headline generated by world events."""
    tick: int
    day: int
    minute: int
    source: str
    headline: str
    tone: str = "neutral"  # "neutral", "positive", "negative", "alert"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NewsItem":
        return cls(**data)


@dataclass
class NetWatchHunter:
    """An autonomous NetWatch counter-infiltration agent tracking the player across subnets."""
    hunter_id: str = "hunter_alpha"
    name: str = "NetWatch Hunter Aegis-9"
    current_node_id: str = "node_central_core"
    status: str = "hunting"  # "hunting", "intercepted", "confused", "neutralized"
    turns_active: int = 0
    target_node_id: str = ""
    confused_turns: int = 0  # turns pathfinding is scrambled

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NetWatchHunter":
        return cls(**data)


@dataclass
class WorldState:
    """Living-grid simulation: in-game clock, corporate alert, market drift, news, and hunters."""
    minute: int = 8 * 60         # in-game minute of the current day (0-1439)
    day: int = 1
    alert_level: int = 10        # grid-wide corporate alert (0-100)
    market_index: float = 1.0    # black-market price multiplier
    turns_since_event: int = 99  # turns since the last ambient grid event
    resecured_count: int = 0     # hosts the grid has re-secured this run
    news: List[NewsItem] = field(default_factory=list)
    hunters: List[NetWatchHunter] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        res = asdict(self)
        res["news"] = [n.to_dict() if hasattr(n, "to_dict") else n for n in self.news]
        res["hunters"] = [h.to_dict() if hasattr(h, "to_dict") else h for h in self.hunters]
        return res

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorldState":
        clean = dict(data)
        if "news" in clean and isinstance(clean["news"], list):
            clean["news"] = [NewsItem.from_dict(n) if isinstance(n, dict) else n for n in clean["news"]]
        if "hunters" in clean and isinstance(clean["hunters"], list):
            clean["hunters"] = [NetWatchHunter.from_dict(h) if isinstance(h, dict) else h for h in clean["hunters"]]
        return cls(**clean)


@dataclass
class GameState:
    """The full runtime state of a CyberPulse infiltration run."""
    seed: int
    current_node_id: str
    trace_percent: int = 0
    turns_elapsed: int = 0
    is_game_over: bool = False
    is_victory: bool = False
    is_jacked_out: bool = False
    unbanked_creds: int = 0
    lost_creds: int = 0
    looted_payloads: List[str] = field(default_factory=list)
    active_contract: Optional[BountyContract] = None
    contract_offers: List[BountyContract] = field(default_factory=list)
    contract_decline_until_turn: int = 0
    contract_seq: int = 0
    near_miss_count: int = 0
    contract_notice: str = ""
    message_log: List[str] = field(default_factory=list)
    combo_streak: int = 0
    best_combo: int = 0
    story_act: int = 1
    story_chapter: int = 1
    story_choice: str = ""
    story_log: List[str] = field(default_factory=list)
    quests: List[Quest] = field(default_factory=list)
    contacts: List[ContactProfile] = field(default_factory=list)
    world: WorldState = field(default_factory=WorldState)
    probed_nodes: List[str] = field(default_factory=list)
    scanned: bool = False
    rival: Optional[RivalNetrunner] = None

    def to_dict(self) -> Dict[str, Any]:
        res = asdict(self)
        if self.active_contract:
            res["active_contract"] = self.active_contract.to_dict()
        return res

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GameState":
        contract_data = data.get("active_contract")
        contract = BountyContract.from_dict(contract_data) if isinstance(contract_data, dict) else None
        data_clean = dict(data)
        data_clean["active_contract"] = contract
        offers = data_clean.get("contract_offers")
        if isinstance(offers, list):
            data_clean["contract_offers"] = [
                BountyContract.from_dict(offer) if isinstance(offer, dict) else offer
                for offer in offers
            ]
        if "contract_seq" not in data_clean and (offers or contract):
            data_clean["contract_seq"] = 10000
        if "probed_nodes" not in data_clean:
            data_clean["probed_nodes"] = []
        if "lost_creds" not in data_clean:
            data_clean["lost_creds"] = 0
        quests = data_clean.get("quests")
        if isinstance(quests, list):
            data_clean["quests"] = [Quest.from_dict(q) if isinstance(q, dict) else q for q in quests]
        contacts = data_clean.get("contacts")
        if isinstance(contacts, list):
            data_clean["contacts"] = [
                ContactProfile.from_dict(c) if isinstance(c, dict) else c for c in contacts
            ]
        world = data_clean.get("world")
        if isinstance(world, dict):
            data_clean["world"] = WorldState.from_dict(world)
        rival = data_clean.get("rival")
        if isinstance(rival, dict):
            data_clean["rival"] = RivalNetrunner.from_dict(rival)
        return cls(**data_clean)
