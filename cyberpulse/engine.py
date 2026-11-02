"""Deterministic cyberspace game engine with risk-reward loss aversion and near-miss feedback."""

import random
import time
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple

from cyberpulse.achievements import achievement_names, evaluate_achievements
from cyberpulse.daily import is_next_day, modifier_by_id
from cyberpulse.difficulty import contract_multiplier, normalize_difficulty, trace_multiplier
from cyberpulse.factions import (
    allegiance_contract_bonus,
    allegiance_shop_discount,
    contract_bonus,
    normalize_allegiance,
    normalize_standing,
    rank_up_reward,
    street_discount,
    update_standing,
)
from cyberpulse.rivals import generate_rival, rival_move_delay
from cyberpulse.scoring import score_run
from cyberpulse.deckos import kill_process as deckos_kill
from cyberpulse.deckos import list_processes as deckos_procs
from cyberpulse.deckos import recent_history as deckos_history
from cyberpulse.deckos import sysinfo as deckos_sysinfo
from cyberpulse.arcs import ARC_DEFS as ARCS_DEFS
from cyberpulse.arcs import arc_epilogue_lines as arcs_epilogue_lines
from cyberpulse.arcs import arc_stage as arcs_stage
from cyberpulse.arcs import district_for_node as arcs_district_for_node
from cyberpulse.arcs import stage_info as arcs_stage_info
from cyberpulse.arcs import arc_status as arcs_status
from cyberpulse.arcs import district_grid as arcs_districts
from cyberpulse.arcs import ensure_arc_quests
from cyberpulse.arcs import live_bonuses as arcs_live_bonuses
from cyberpulse.tutorial import tutorial_steps
from cyberpulse.models import (
    BountyContract,
    CareerProfile,
    ContactProfile,
    CyberDeck,
    EmployeeProfile,
    ExploitPayload,
    FirewallPolicy,
    FirewallRule,
    GameState,
    HostAntivirus,
    HostFirewall,
    MalwareDaemon,
    NetWatchHunter,
    Node,
    NodeStatus,
    NodeType,
    OperatingStance,
    PortService,
    Quest,
    SecurityAwarenessLevel,
    SocialVectorType,
    VirtualFile,
    VirusCraftRecipe,
    apply_career_profile,
)
from cyberpulse.network import generate_network
from cyberpulse.puzzles import BufferPuzzle, FrequencyPuzzle, HashCrackPuzzle
from cyberpulse.rewards import roll_breach_reward
from cyberpulse.world import (
    AmbientEvent,
    adjust_alert,
    advance_clock,
    alert_tier,
    ambient_event_for,
    apply_resecure,
    apply_social_shift,
    calculate_distance,
    clock_label,
    deploy_hunter,
    drift_market,
    market_multiplier,
    neutralize_hunter,
    patrol_pressure,
    plan_resecures,
    record_news,
    shift_name,
    shift_profile,
    social_shift_modifier,
    step_hunter,
    tier_rank,
    world_rng,
    world_summary as build_world_summary,
)
from cyberpulse.story import (
    CHOICE_EPILOGUES,
    CHOICE_LABELS,
    COMBO_EPILOGUES,
    CONTACT_EPILOGUES,
    FAVOR_DESCRIPTIONS,
    MAIN_QUEST_IDS,
    OUTCOME_EPILOGUES,
    STORY_INTRO,
    STORY_LOG_SEED,
    act_title,
    dialogue_for,
    initial_contacts,
    trust_dialogue_for,
    initial_quests,
)

KNOWN_CVES: Dict[str, ExploitPayload] = {
    "cve-2024-38812": ExploitPayload(
        cve_id="CVE-2024-38812",
        name="Heap Overflow Zero-Day",
        target_service="http",
        required_ram_mb=32,
        cpu_cost=2,
        stealth_rating=4,
        damage_trace=8,
        description="Remote code execution heap corruption in network packet parser.",
    ),
    "cve-2023-22515": ExploitPayload(
        cve_id="CVE-2023-22515",
        name="Broken Auth Privilege Escalation",
        target_service="http",
        required_ram_mb=16,
        cpu_cost=2,
        stealth_rating=5,
        damage_trace=5,
        description="Zero-day unauthorized administrator account creation flaw.",
    ),
    "cve-2024-21413": ExploitPayload(
        cve_id="CVE-2024-21413",
        name="Outlook Moniker Link Bypass",
        target_service="smtp",
        required_ram_mb=16,
        cpu_cost=1,
        stealth_rating=3,
        damage_trace=10,
        description="Remote credential theft and code execution via moniker parsing.",
    ),
    "cve-2024-6387": ExploitPayload(
        cve_id="CVE-2024-6387",
        name="RegreSSHion Race Condition",
        target_service="ssh",
        required_ram_mb=48,
        cpu_cost=2,
        stealth_rating=4,
        damage_trace=12,
        description="Signal handler race condition leading to unauthenticated root RCE.",
    ),
    "cve-2023-38606": ExploitPayload(
        cve_id="CVE-2023-38606",
        name="Blind SQL Injection",
        target_service="mysql",
        required_ram_mb=32,
        cpu_cost=2,
        stealth_rating=4,
        damage_trace=8,
        description="Blind SQL injection bypassing WAF filters to extract root hashes.",
    ),
    "cve-2011-2523": ExploitPayload(
        cve_id="CVE-2011-2523",
        name="vsftpd Backdoor Payload",
        target_service="ftp",
        required_ram_mb=16,
        cpu_cost=1,
        stealth_rating=2,
        damage_trace=14,
        description="Legacy backdoor payload triggering root shell on port 6200.",
    ),
    "cve-2022-0778": ExploitPayload(
        cve_id="CVE-2022-0778",
        name="OpenSSL BN_mod_sqrt Parsing Loop",
        target_service="https",
        required_ram_mb=32,
        cpu_cost=2,
        stealth_rating=4,
        damage_trace=10,
        description="Infinite loop parsing invalid elliptic curve parameters triggering TLS root shell.",
    ),
    "cve-2025-9901": ExploitPayload(
        cve_id="CVE-2025-9901",
        name="Project Omega Quantum Zero-Day",
        target_service="any",
        required_ram_mb=64,
        cpu_cost=3,
        stealth_rating=5,
        damage_trace=5,
        description="Universal quantum zero-day payload overriding neural subroutines and central cores.",
    ),
    "cve-2020-0796": ExploitPayload(
        cve_id="CVE-2020-0796",
        name="SMGhost SMBv3 RCE",
        target_service="smb",
        required_ram_mb=32,
        cpu_cost=2,
        stealth_rating=3,
        damage_trace=11,
        description="SMBv3 compression parsing flaw granting remote code execution on file shares.",
    ),
    "cve-2023-39417": ExploitPayload(
        cve_id="CVE-2023-39417",
        name="Postgres SQL Gateway Escape",
        target_service="postgres",
        required_ram_mb=32,
        cpu_cost=2,
        stealth_rating=4,
        damage_trace=8,
        description="Extension script privilege escape yielding superuser SQL execution.",
    ),
}

CRAFTING_RECIPES: Dict[str, VirusCraftRecipe] = {
    "keylogger_daemon": VirusCraftRecipe(
        name="keylogger_daemon",
        vector="stealth",
        payload="keylogger",
        cost_creds=100,
        cpu_cost=2,
        description="Persistent background listener chip. Harvests credentials and passive credits from breached hosts.",
    ),
    "worm_replicator": VirusCraftRecipe(
        name="worm_replicator",
        vector="worm",
        payload="logic_overload",
        cost_creds=150,
        cpu_cost=3,
        description="Self-propagating payload. Breaches target node and forces disclosure of all adjacent subnet nodes.",
    ),
    "data_siphon": VirusCraftRecipe(
        name="data_siphon",
        vector="trojan",
        payload="credit_siphon",
        cost_creds=120,
        cpu_cost=2,
        description="Automated exfiltration script. Immediately drains 150 unbanked credits from target host.",
    ),
    "trace_cleaner": VirusCraftRecipe(
        name="trace_cleaner",
        vector="stealth",
        payload="trace_wipe",
        cost_creds=80,
        cpu_cost=2,
        description="Anti-forensic daemon. Scrub active trace by 35% on execution.",
    ),
}


CONTRACT_RISK: Dict[str, Dict[str, float]] = {
    "standard": {"reward": 1.0, "max_trace": 80, "rush": 0.20, "duration_delta": 0, "offer_ttl": 10},
    "priority": {"reward": 1.2, "max_trace": 70, "rush": 0.22, "duration_delta": -3, "offer_ttl": 8},
    "black": {"reward": 1.5, "max_trace": 60, "rush": 0.25, "duration_delta": -5, "offer_ttl": 6},
}

CONTRACT_BOARD_SIZE = 3
OFFER_DROP_FEE = 30

CONTRACT_BASE_REWARD: Dict[str, int] = {"breach": 120, "extract": 200, "wipe": 220, "recon": 80}


class GameEngine:
    """Manages gameplay rules, push-your-luck risk, and victory/defeat conditions."""

    MAX_LAY_LOW_TURNS = 3
    LAY_LOW_TRACE_COOLING = 2
    LOCKDOWN_TURNS = 2
    FAILURE_TRACE_STACK = 4
    MAX_FAILURE_TRACE = 30
    MAX_RUN_HISTORY = 20
    # Black ICE surge when pulling the jack: a hot connection is a final gamble.
    EXTRACTION_SURGE_BANDS = ((85, 15), (70, 10), (50, 5))

    def __init__(
        self,
        seed: int = 1337,
        career_profile: Optional[CareerProfile] = None,
        difficulty: str = "normal",
        daily_modifier: str = "",
        allegiance: str = "none",
    ):
        self.seed = int(seed)
        self.difficulty = normalize_difficulty(difficulty)
        self.allegiance = normalize_allegiance(allegiance)
        self.allegiance_contract_bonus = allegiance_contract_bonus(self.allegiance)
        self.allegiance_shop_discount = allegiance_shop_discount(self.allegiance)
        self.faction_standing = normalize_standing(
            career_profile.faction_standing if career_profile else {}
        )
        self.contract_standing_bonus = contract_bonus(self.faction_standing)
        self.street_standing_discount = street_discount(self.faction_standing)
        modifier = modifier_by_id(daily_modifier)
        self.daily_modifier = modifier.modifier_id if modifier else ""
        # Identity of this specific run; save slots use it to purge every checkpoint on settlement.
        self.run_id = uuid.uuid4().hex
        self.daily_key = ""
        self.last_unlocked_achievements: List[str] = []
        self.last_rank_ups: List[Dict[str, Any]] = []
        self.last_run_score: Optional[int] = None
        self.last_score_breakdown: Optional[Dict[str, int]] = None
        self.last_hall_rank: Optional[int] = None
        self.rng = random.Random(self.seed)
        self.nodes: Dict[str, Node] = generate_network(self.seed)
        self.deck: CyberDeck = CyberDeck()
        if career_profile:
            apply_career_profile(self.deck, career_profile)

        # Generate a procedural Syndicate Bounty Contract (Zeigarnik Effect)
        contract = BountyContract(
            contract_id=f"cnt_{self.seed % 1000:03d}",
            title="Syndicate Infiltration Order: Data Extraction",
            target_node_type=NodeType.DATA_VAULT,
            target_ip="10.0.4.15",
            target_file="/data/corporate_slush_fund.csv",
            wipe_logs_required=True,
            max_trace_limit=70,
            reward_creds=200,
            giver="mira",
            risk_tier="priority",
            objective="wipe",
            expires_turn=24,
            rush_turn=13,
            bonus_creds=75,
            description=(
                "Steal the corporate slush-fund ledger from the Financial Ledger Vault "
                "and sanitize its access logs before the Syndicate window closes."
            ),
        )

        self.state: GameState = GameState(
            seed=self.seed,
            current_node_id="node_gateway",
            trace_percent=0,
            turns_elapsed=0,
            active_contract=contract,
        )
        self.state.story_log = list(STORY_LOG_SEED)
        self.state.quests = initial_quests()
        self.state.contacts = initial_contacts()
        self.state.rival = generate_rival(self.seed)
        ensure_arc_quests(self)
        if self.difficulty == "easy":
            self.deck.max_cpu += 2
            self.deck.cpu_cycles = self.deck.max_cpu
        elif self.difficulty == "hard":
            self.state.world.alert_level = min(100, self.state.world.alert_level + 15)
        if modifier:
            if modifier.start_alert:
                self.state.world.alert_level = min(
                    100, self.state.world.alert_level + modifier.start_alert
                )
            if modifier.start_cpu:
                self.deck.cpu_cycles = max(1, self.deck.cpu_cycles + modifier.start_cpu)
        self._sync_story_quests()
        self.pending_puzzles: Dict[str, Any] = {}
        self.run_settled: bool = False
        self._last_alert_tier: Optional[str] = alert_tier(self.state.world.alert_level)
        self._refresh_contract_offers()

    def get_current_node(self) -> Node:
        return self.nodes[self.state.current_node_id]

    def _mark_probed(self, node_id: str) -> None:
        """Record that the runner has mapped a host's services (survives save/load)."""
        if node_id not in self.state.probed_nodes:
            self.state.probed_nodes.append(node_id)

    def _find_quest(self, quest_id: Optional[str]) -> Optional[Quest]:
        if not quest_id:
            return None
        for quest in self.state.quests:
            if quest.quest_id == quest_id:
                return quest
        return None

    def _find_contact(self, contact_id: Optional[str]) -> Optional[ContactProfile]:
        if not contact_id:
            return None
        lookup = str(contact_id).strip().lower()
        for contact in self.state.contacts:
            if contact.contact_id == lookup or contact.handle.lower() == lookup or contact.name.lower() == lookup:
                return contact
        return None

    def _log_story(self, message: str) -> None:
        self.state.story_log.append(message)
        if len(self.state.story_log) > 60:
            del self.state.story_log[:-60]

    def _sync_story_quests(self) -> None:
        """Auto-accept unlocked main-story quests so the campaign cannot stall."""
        newly_accepted: List[Quest] = []
        for quest in self.state.quests:
            if (
                quest.quest_id in MAIN_QUEST_IDS
                and not quest.accepted
                and not quest.completed
                and quest.story_act <= self.state.story_act
            ):
                quest.accepted = True
                self._log_story(f"NEW MAIN QUEST: {quest.title} — {quest.description}")
                newly_accepted.append(quest)
        for quest in newly_accepted:
            self._reconcile_quest_progress(quest)

    def _contact_trust(self, contact_id: str) -> int:
        """Trust level for an operative (0 when the contact is missing)."""
        contact = self._find_contact(contact_id)
        return int(getattr(contact, "trust", 0)) if contact else 0

    def _adjust_trust(self, contact: Any, delta: int) -> Optional[str]:
        """Shift an operative's trust, announcing loyalty-arc stage crossings.

        Returns the arc-unlock line when the change opens a new arc stage,
        else None. Decreases never announce.
        """
        if contact is None or not delta:
            return None
        before = arcs_stage(contact.contact_id, int(contact.trust))
        contact.trust = max(-1, int(contact.trust) + int(delta))
        after = arcs_stage(contact.contact_id, int(contact.trust))
        if after <= before:
            return None
        info = arcs_stage_info(contact.contact_id, after)
        line = (
            f"🌟 ARC ADVANCE — {contact.name}: {info['label']} "
            f"(stage {after}/3). {info['bonus']}"
        )
        self._log_story(line)
        self.state.message_log.append(line)
        return line

    def _quest_progress_from_state(self, quest: Quest) -> int:
        """Progress the world already holds for a one-shot objective."""
        if quest.objective == "breach_type":
            return sum(
                1
                for node in self.nodes.values()
                if node.status == NodeStatus.BREACHED and node.node_type == quest.target
            )
        if quest.objective == "steal_file":
            return 1 if quest.target in self.state.looted_payloads else 0
        if quest.objective == "wipe_logs":
            node = self.find_node(quest.target)
            return 1 if node and node.logs_cleared else 0
        if quest.objective == "deploy_daemon":
            return sum(1 for daemon in self.deck.active_daemons if daemon.daemon_type == quest.target)
        if quest.objective == "craft_recipe":
            return sum(1 for chip in self.deck.exploits if chip == quest.target)
        return 0

    def _reconcile_quest_progress(self, quest: Quest) -> List[str]:
        """Credit one-shot events that happened before the quest was accepted."""
        if not quest.accepted or quest.completed:
            return []
        earned = min(max(1, quest.required), self._quest_progress_from_state(quest))
        if earned <= quest.progress:
            return []
        quest.progress = earned
        if quest.progress >= max(1, quest.required):
            return self._complete_quest(quest)
        return []

    def _complete_quest(self, quest: Quest) -> List[str]:
        """Mark a quest complete once, grant its reward, and advance the main story."""
        if quest.completed:
            return []
        quest.completed = True
        if quest.reward_creds:
            self.state.unbanked_creds += quest.reward_creds
        if quest.reward_item and quest.reward_item not in self.deck.exploits:
            self.deck.exploits.append(quest.reward_item)

        reward_bits = []
        if quest.reward_creds:
            reward_bits.append(f"+{quest.reward_creds} Creds")
        if quest.reward_item:
            reward_bits.append(f"[{quest.reward_item}]")
        reward_text = ", ".join(reward_bits) if reward_bits else "story intel"
        line = f"📜 QUEST COMPLETE: {quest.title}! Reward: {reward_text}."
        self._log_story(line)
        messages = [line]

        if quest.quest_id in MAIN_QUEST_IDS:
            advanced = self._advance_story(
                quest.story_act + 1,
                1,
                f"{quest.title} resolved.",
            )
            if advanced:
                messages.append(f"📖 {advanced}")
        return messages

    def _advance_story(self, act: int, chapter: int, reason: str) -> str:
        if act < self.state.story_act:
            return ""
        if act == self.state.story_act and chapter <= self.state.story_chapter:
            return ""
        self.state.story_act = act
        self.state.story_chapter = chapter
        title, subtitle = act_title(act)
        message = f"{title} — {subtitle}: {reason}"
        self._log_story(message)
        self._sync_story_quests()
        return message

    def _progress_quests(self, objective: str, target: str = "", amount: int = 1) -> List[str]:
        messages: List[str] = []
        for quest in self.state.quests:
            if not quest.accepted or quest.completed or quest.objective != objective:
                continue
            if quest.target and quest.target != target:
                continue

            quest.progress = min(max(1, quest.required), quest.progress + amount)
            if quest.progress < max(1, quest.required):
                continue
            messages.extend(self._complete_quest(quest))
        return messages

    def is_quest_locked(self, quest: Quest) -> bool:
        if quest.quest_id in MAIN_QUEST_IDS and quest.story_act > self.state.story_act:
            return True
        giver = self._find_contact(quest.giver)
        if giver and giver.unlock_act > self.state.story_act:
            return True
        return bool(giver and quest.required_trust > giver.trust)

    def _story_gate_reason(self, node: Node) -> Optional[str]:
        """A story lock the network topology alone does not enforce."""
        if node.node_type == NodeType.CENTRAL_CORE and self.state.story_act < 4:
            return "The Nexus supercore is sealed until Act IV. Advance the campaign first."
        return None

    def accept_quest(self, quest_id: str) -> Tuple[bool, str]:
        """Accept a contact's side quest or expose an unlocked story objective."""
        if self.state.is_game_over:
            return False, "Cannot accept a quest: system lockout in effect."
        if self.state.is_jacked_out:
            return False, "Cannot accept a quest: terminal session jacked out."
        if self.state.is_victory:
            return False, "Cannot accept a quest: mission already complete."

        quest = self._find_quest(quest_id)
        if not quest:
            return False, f"Unknown quest '{quest_id}'."
        if quest.completed:
            return False, f"Quest '{quest.title}' is already complete."
        if quest.accepted:
            return False, f"Quest '{quest.title}' is already active."
        if self.is_quest_locked(quest):
            giver = self._find_contact(quest.giver)
            if giver and quest.required_trust > giver.trust:
                return False, (
                    f"Quest '{quest.title}' requires {giver.name} trust {quest.required_trust} "
                    f"(current {giver.trust}). Work with them first."
                )
            return False, f"Quest '{quest.title}' is not available until the story advances."

        giver = self._find_contact(quest.giver)

        quest.accepted = True
        arc_line = self._adjust_trust(giver, 1) if giver else None
        message = f"📜 QUEST ACCEPTED: {quest.title} — {quest.description}"
        if arc_line:
            message += f"\n{arc_line}"
        self._log_story(message)
        self.state.message_log.append(message)

        completion_lines = self._reconcile_quest_progress(quest)
        if completion_lines:
            message += "\n" + "\n".join(completion_lines)
        return True, message

    def _apply_contact_favor(self, contact: ContactProfile) -> Tuple[bool, str]:
        if contact.contact_id == "mira":
            if self.state.trace_percent <= 0:
                return False, "Mira cannot hide a trace that is already at 0%."
            before = self.state.trace_percent
            self.state.trace_percent = max(0, before - 20)
            return True, f"Mira burns a Syndicate favor: trace reduced by {before - self.state.trace_percent}%."
        if contact.contact_id == "kilo":
            if self.deck.cpu_cycles >= self.deck.max_cpu:
                return False, "Kilo says your deck is already running cool."
            self.deck.cpu_cycles = self.deck.max_cpu
            return True, f"Kilo vents the deck: CPU restored to {self.deck.max_cpu}/{self.deck.max_cpu}."
        if contact.contact_id == "archivist":
            locked = sorted(
                (node for node in self.nodes.values() if node.status == NodeStatus.LOCKED),
                key=lambda node: (node.security_level, node.node_id),
            )
            if not locked:
                return False, "The Archive has no locked nodes left to expose."
            node = locked[0]
            node.status = NodeStatus.DISCOVERED
            return True, f"The Archivist exposes '{node.name}' ({node.ip_address}) on your grid."
        if contact.contact_id == "zero":
            if "ghost_protocol" in self.deck.exploits:
                self.state.unbanked_creds += 100
                return True, "Agent Zero cannot spare a chip, but wires 100 unbanked Creds instead."
            self.deck.exploits.append("ghost_protocol")
            return True, "Agent Zero lends you a ghost_protocol exploit chip."

        self.state.unbanked_creds += 50
        return True, f"{contact.name} helps you out with 50 unbanked Creds."

    def interact_contact(
        self,
        contact_id: str,
        mode: str = "talk",
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """Talk to an operative, accept their job, or spend their one-time favor."""
        if self.state.is_game_over:
            return False, "Cannot open a channel: system lockout in effect.", {}
        if self.state.is_jacked_out:
            return False, "Cannot open a channel: terminal session jacked out.", {}
        if self.state.is_victory:
            return False, "Cannot open a channel: mission already complete.", {}

        contact = self._find_contact(contact_id)
        if not contact:
            return False, f"Unknown operative '{contact_id}'.", {}
        if contact.unlock_act > self.state.story_act:
            return False, f"{contact.name} is not on the grid yet.", {}

        mode_key = str(mode or "talk").lower().strip()
        report = {
            "contact_id": contact.contact_id,
            "name": contact.name,
            "handle": contact.handle,
            "role": contact.role,
            "faction": contact.faction,
            "trust": contact.trust,
            "trust_tier": contact.trust_tier,
            "favor_used": contact.favor_used,
            "bonus_favor_used": contact.bonus_favor_used,
            "favor_available": (
                not contact.favor_used
                or (contact.trust >= 6 and not contact.bonus_favor_used)
            ),
            "choice": self.state.story_choice,
            "pact_available": (
                contact.contact_id == "zero"
                and self.state.story_act >= 3
                and not self.state.story_choice
            ),
            "mode": mode_key,
        }

        if mode_key in ("talk", "chat", ""):
            line = dialogue_for(contact.contact_id, self.state.story_act, self.state.story_choice)
            tier_line = trust_dialogue_for(contact.contact_id, contact.trust_tier)
            if tier_line:
                line = f"{line}\n{tier_line}"
            stage = arcs_stage(contact.contact_id, int(contact.trust))
            if stage:
                info = arcs_stage_info(contact.contact_id, stage)
                title = ARCS_DEFS.get(contact.contact_id, {}).get("title", "arc")
                line = f"{line}\n[{contact.name} — {title} arc, stage {stage}/3: {info['label']}]"
            self.state.message_log.append(line)
            report["dialogue"] = line
            return True, line, report

        if mode_key in ("ally", "defy"):
            if contact.contact_id != "zero":
                return False, f"{contact.name} has no alliance to offer.", report
            if self.state.story_act < 3:
                return False, "Agent Zero will not discuss an alliance until the Black ICE job.", report
            if self.state.story_choice:
                return False, f"You already chose: {CHOICE_LABELS.get(self.state.story_choice, self.state.story_choice)}.", report

            if mode_key == "ally":
                self.state.story_choice = "zero_ally"
                arc_line = self._adjust_trust(contact, 3)
                if "ghost_protocol" in self.deck.exploits:
                    self.state.unbanked_creds += 150
                    reward = "Zero wires 150 unbanked Creds."
                else:
                    self.deck.exploits.append("ghost_protocol")
                    reward = "Zero shares a ghost_protocol exploit chip."
                message = f"🤝 ALLIANCE FORGED: {CHOICE_LABELS['zero_ally']}. {reward}"
                if arc_line:
                    message += f"\n{arc_line}"
            else:
                self.state.story_choice = "zero_defy"
                self._adjust_trust(contact, -1)
                mira = self._find_contact("mira")
                mira_line = self._adjust_trust(mira, 2) if mira else None
                self.state.unbanked_creds += 150
                message = f"⚔️ DEFIANCE DECLARED: {CHOICE_LABELS['zero_defy']}. Mira wires 150 unbanked Creds."
                if mira_line:
                    message += f"\n{mira_line}"

            self._log_story(message)
            self.state.message_log.append(message)
            report["choice"] = self.state.story_choice
            report["trust"] = contact.trust
            report["pact_available"] = False
            return True, message, report

        if mode_key in ("job", "quest", "work"):
            for quest_id in (contact.quest_id, contact.secondary_quest_id):
                quest = self._find_quest(quest_id)
                if quest and not quest.accepted and not quest.completed:
                    ok, message = self.accept_quest(quest.quest_id)
                    if ok:
                        report["trust"] = contact.trust
                        report["quest_id"] = quest.quest_id
                    return ok, message, report
            return False, f"{contact.name} has no new work for you right now.", report

        if mode_key in ("favor", "help"):
            can_use = (
                not contact.favor_used
                or (contact.trust >= 6 and not contact.bonus_favor_used)
            )
            if not can_use:
                return False, f"{contact.name} has already spent their favor this run.", report
            ok, message = self._apply_contact_favor(contact)
            if not ok:
                return False, message, report
            if contact.favor_used:
                contact.bonus_favor_used = True
            else:
                contact.favor_used = True
            arc_line = self._adjust_trust(contact, 1)
            if arc_line:
                message += f"\n{arc_line}"
            self._log_story(f"FAVOR: {contact.name} — {message}")
            self.state.message_log.append(message)
            report["favor_used"] = contact.favor_used
            report["bonus_favor_used"] = contact.bonus_favor_used
            report["favor_available"] = contact.trust >= 6 and not contact.bonus_favor_used
            report["trust"] = contact.trust
            report["trust_tier"] = contact.trust_tier
            return True, message, report

        return False, f"Unknown interaction '{mode}'. Use talk, job, or favor.", report

    def ensure_story_state(self) -> None:
        """Backfill story content when loading a save created before story support."""
        if not self.state.story_log:
            self.state.story_log = list(STORY_LOG_SEED)
        if not self.state.quests:
            self.state.quests = initial_quests()
        if not self.state.contacts:
            self.state.contacts = initial_contacts()
        ensure_arc_quests(self)
        # A swapped-in save may carry a different alert level than the fresh engine,
        # so resync the corporate posture baseline silently on the next grid pulse.
        self._last_alert_tier = None
        if self.state.rival is None:
            self.state.rival = generate_rival(self.seed)
        self._sync_story_quests()
        if not self.state.contract_offers:
            self._refresh_contract_offers()

    def story_summary(self) -> Dict[str, Any]:
        title, subtitle = act_title(self.state.story_act)
        return {
            "act": self.state.story_act,
            "chapter": self.state.story_chapter,
            "act_title": title,
            "chapter_title": subtitle,
            "intro": STORY_INTRO,
            "choice": self.state.story_choice,
            "choice_label": CHOICE_LABELS.get(self.state.story_choice, ""),
            "log": self.state.story_log[-20:],
        }

    def world_summary(self) -> Dict[str, Any]:
        """Return the living-grid snapshot with the newest headlines and hunter telemetry."""
        summary = build_world_summary(self.state.world)
        summary["news"] = self.news_feed(10)
        dist = -1
        nearest_name = ""
        active = [h for h in self.state.world.hunters if h.status in ("hunting", "confused", "intercepted")]
        if active:
            dist = calculate_distance(self.nodes, active[0].current_node_id, self.state.current_node_id)
            nearest_name = active[0].name
        summary["nearest_hunter_distance"] = dist
        summary["nearest_hunter_name"] = nearest_name
        summary["districts"] = arcs_districts(self.seed, int(self.state.turns_elapsed),
                                              int(self.state.world.alert_level))
        return summary

    def deckos_summary(self) -> Dict[str, Any]:
        """In-game computer snapshot: sysinfo + process table (Web/CLI DeckOS panel)."""
        info = deckos_sysinfo(self)
        info["processes"] = deckos_procs(self)
        return info

    def arcs_summary(self) -> Dict[str, Any]:
        """Operative loyalty-arc tracker for CLI/Web/dossier consumers."""
        return {"arcs": arcs_status(self.state.contacts), "live": arcs_live_bonuses(self)}

    def district_summary(self) -> Dict[str, Any]:
        """Street-level district simulation rows for the living-grid ticker."""
        rows = arcs_districts(self.seed, int(self.state.turns_elapsed),
                              int(self.state.world.alert_level))
        hosts_by_key: Dict[str, List[str]] = {}
        for node_id in self.nodes:
            key = arcs_district_for_node(self.seed, node_id)["key"]
            hosts_by_key.setdefault(key, []).append(node_id)
        for row in rows:
            row["hosts"] = sorted(hosts_by_key.get(row["key"], []))
        return {"districts": rows}

    def host_district(self, node_id: str) -> Dict[str, Any]:
        """Street-layer address of a host: its district plus live patrol/load/mood."""
        mapping = arcs_district_for_node(self.seed, node_id)
        live = {row["key"]: row for row in arcs_districts(
            self.seed, int(self.state.turns_elapsed), int(self.state.world.alert_level))}
        row = live.get(mapping["key"], {})
        return {"district": mapping["name"], "district_key": mapping["key"],
                "flavor": mapping.get("flavor", ""),
                "patrol": row.get("patrol", "standard"),
                "load": row.get("load", 0),
                "market_mood": row.get("market_mood", "steady")}

    def offer_district(self, target_ip: str = "", target_node_type: str = "") -> Dict[str, str]:
        """Street address of a contract target for board display."""
        node = self.find_node(target_ip) if target_ip else None
        if node is None:
            return {"district": "WILDCAT GRID", "district_patrol": "standard"}
        hood = self.host_district(node.node_id)
        return {"district": hood["district"], "district_patrol": hood["patrol"]}

    def node_districts(self) -> Dict[str, Dict[str, str]]:
        """Compact per-host district tags for Web/CLI consumers."""
        grid = {row["key"]: row for row in arcs_districts(
            self.seed, int(self.state.turns_elapsed), int(self.state.world.alert_level))}
        out: Dict[str, Dict[str, str]] = {}
        for node_id in self.nodes:
            mapping = arcs_district_for_node(self.seed, node_id)
            out[node_id] = {"district": mapping["name"],
                            "district_patrol": grid.get(mapping["key"], {}).get("patrol", "standard")}
        return out

    def news_feed(self, limit: int = 12) -> List[Dict[str, Any]]:
        """Return the newest living-grid headlines, oldest first."""
        capped = max(1, int(limit))
        return [item.to_dict() for item in self.state.world.news[-capped:]]

    def run_summary(self) -> Dict[str, Any]:
        """Return the terminal (or in-progress) run's legacy for CLI and Web display."""
        if self.state.is_victory:
            outcome = "victory"
            outcome_title = "MISSION ACCOMPLISHED"
        elif self.state.is_game_over:
            outcome = "lockout"
            outcome_title = "CONNECTION TERMINATED"
        elif self.state.is_jacked_out:
            outcome = "jackout"
            outcome_title = "SAFE EXTRACTION"
        else:
            outcome = "active"
            outcome_title = "RUN IN PROGRESS"

        completed = [quest for quest in self.state.quests if quest.completed]
        main_quests = [quest for quest in self.state.quests if quest.quest_id in MAIN_QUEST_IDS]
        main_complete = bool(main_quests) and all(quest.completed for quest in main_quests)

        epilogue = [OUTCOME_EPILOGUES.get(outcome, OUTCOME_EPILOGUES["active"])]
        if self.state.story_choice:
            choice_line = CHOICE_EPILOGUES.get(self.state.story_choice)
            if choice_line:
                epilogue.append(choice_line)
            # Zero's arc (trust 6+): equals get a longer goodbye.
            if arcs_stage("zero", self._contact_trust("zero")) >= 3:
                epilogue.append("Zero keeps a chair open for you now. Equals don't knock.")
        if main_complete and outcome == "victory":
            epilogue.append("Every act of the NEXUS file is closed. The next story starts without you.")
        for contact in self.state.contacts:
            if contact.favor_used or contact.trust >= 3:
                line = CONTACT_EPILOGUES.get(contact.contact_id)
                if line:
                    epilogue.append(line)
        epilogue.extend(arcs_epilogue_lines(self.state.contacts))
        for threshold in sorted(COMBO_EPILOGUES, reverse=True):
            if self.state.best_combo >= threshold:
                epilogue.append(COMBO_EPILOGUES[threshold])
                break

        title, subtitle = act_title(self.state.story_act)
        return {
            "outcome": outcome,
            "outcome_title": outcome_title,
            "epilogue": epilogue,
            "best_combo": self.state.best_combo,
            "turns_elapsed": self.state.turns_elapsed,
            "nodes_breached": sum(
                1 for node in self.nodes.values() if node.status == NodeStatus.BREACHED
            ),
            "districts_compromised": sorted(
                {self.host_district(node_id)["district"] for node_id, node in self.nodes.items()
                 if node.status == NodeStatus.BREACHED}
            ),
            "districts_compromised_count": len(
                {self.host_district(node_id)["district_key"] for node_id, node in self.nodes.items()
                 if node.status == NodeStatus.BREACHED}
            ),
            "unbanked_credits_lost": 0 if outcome != "lockout" else self.state.lost_creds,
            "trace_percent": self.state.trace_percent,
            "quests_completed": [quest.title for quest in completed],
            "quests_completed_count": len(completed),
            "quests_total": len(self.state.quests),
            "main_story_complete": main_complete,
            "contacts": [
                {
                    "contact_id": contact.contact_id,
                    "name": contact.name,
                    "trust": contact.trust,
                    "trust_tier": contact.trust_tier,
                    "favor_used": contact.favor_used,
                    "bonus_favor_used": contact.bonus_favor_used,
                }
                for contact in self.state.contacts
                if contact.unlock_act <= self.state.story_act
            ],
            "story_act": self.state.story_act,
            "story_title": f"{title} // {subtitle}",
            "achievements_unlocked": achievement_names(self.last_unlocked_achievements),
            "daily_key": getattr(self, "daily_key", ""),
            "rival": self.rival_summary(),
            "difficulty": self.difficulty,
            "allegiance": self.allegiance,
            "factions": dict(self.faction_standing),
            "daily_modifier": self.daily_modifier_summary(),
            "rank_ups": self.last_rank_ups,
            "score": self.last_run_score,
            "score_breakdown": self.last_score_breakdown,
            "hall_rank": self.last_hall_rank,
        }

    def list_quests(self) -> List[Dict[str, Any]]:
        quests = []
        for quest in self.state.quests:
            data = quest.to_dict()
            data["locked"] = self.is_quest_locked(quest)
            if data["locked"]:
                giver = self._find_contact(quest.giver)
                if giver and quest.required_trust > giver.trust:
                    data["lock_reason"] = f"Requires {giver.name} trust {quest.required_trust}"
                else:
                    data["lock_reason"] = "Advance the story"
            quests.append(data)
        return quests

    def list_contacts(self) -> List[Dict[str, Any]]:
        contacts = []
        for contact in self.state.contacts:
            data = contact.to_dict()
            data["locked"] = contact.unlock_act > self.state.story_act
            data["dialogue"] = dialogue_for(contact.contact_id, self.state.story_act, self.state.story_choice)
            data["trust_tier"] = contact.trust_tier
            data["trust_dialogue"] = trust_dialogue_for(contact.contact_id, contact.trust_tier)
            data["favor_available"] = (
                not contact.favor_used
                or (contact.trust >= 6 and not contact.bonus_favor_used)
            )
            data["favor_description"] = FAVOR_DESCRIPTIONS.get(contact.contact_id, "")
            arc_spec = ARCS_DEFS.get(contact.contact_id, {})
            arc_stage_no = arcs_stage(contact.contact_id, contact.trust)
            data["arc_title"] = arc_spec.get("title", "")
            data["arc_stage"] = arc_stage_no
            stages = arc_spec.get("stages", ())
            data["arc_label"] = stages[arc_stage_no - 1]["label"] if arc_stage_no else "Unproven"
            data["pact_available"] = (
                contact.contact_id == "zero"
                and self.state.story_act >= 3
                and not self.state.story_choice
            )
            contacts.append(data)
        return contacts

    def get_or_create_puzzle(self, node_id: str) -> Tuple[bool, str, Optional[Any], Optional[Node]]:
        """Return the pending hacking puzzle for a node, creating it only once.

        Keeping the puzzle instance on the engine prevents every CLI/API re-entry from
        granting a fresh set of attempts for the same node.
        """
        ok, reason = self.can_hack_node(node_id)
        if not ok:
            return False, reason, None, None

        node = self.nodes[node_id]
        puzzle = self.pending_puzzles.get(node_id)
        if puzzle is None:
            node_salt = sum((index + 1) * ord(char) for index, char in enumerate(node_id))
            seed = self.seed + (self.state.turns_elapsed * 31) + node_salt
            p_type = node.puzzle_type or "frequency"
            if p_type == "buffer":
                puzzle = BufferPuzzle.generate(seed)
            elif p_type == "hash":
                puzzle = HashCrackPuzzle.generate(seed)
            else:
                puzzle = FrequencyPuzzle.generate(seed)
            self.pending_puzzles[node_id] = puzzle

        return True, "Puzzle active.", puzzle, node

    def clear_pending_puzzle(self, node_id: str) -> None:
        """Discard a solved or exhausted puzzle so the node cannot replay its attempts."""
        self.pending_puzzles.pop(node_id, None)

    def _lockdown_reason(self, node: Node) -> Optional[str]:
        """Return a denial when a host's ICE is still rotating after a burned intrusion."""
        remaining = int(node.lockdown_until_turn) - self.state.turns_elapsed
        if remaining <= 0:
            return None
        turns = "turn" if remaining == 1 else "turns"
        return (
            f"🔒 HOST LOCKDOWN: {node.hostname} ({node.ip_address}) is rotating its ICE for "
            f"{remaining} more {turns}. Use lay_low/wait, probe another host, or return at turn "
            f"{node.lockdown_until_turn}."
        )

    def register_puzzle_failure(self, node_id: str, reason: str) -> Tuple[bool, str]:
        """Apply the cost of a burned intrusion script: trace, combo loss, and a host lockdown.

        A failed puzzle is a detected intrusion, not a free retry. Each stacked failure on the
        same host adds trace, raises its EDR alert, and seals the host for a short recalibration
        window so the player must spend turns (or pick another target) before trying again.
        """
        node = self.nodes.get(node_id)
        if node is None:
            return False, f"Invalid node '{node_id}'."

        node.failed_attempts += 1
        penalty = min(
            self.MAX_FAILURE_TRACE,
            node.trace_rate + self.FAILURE_TRACE_STACK * (node.failed_attempts - 1),
        )
        effective_penalty = self.mitigated_trace(penalty)
        self.add_trace(penalty)
        node.lockdown_until_turn = self.state.turns_elapsed + self.LOCKDOWN_TURNS
        if node.antivirus and node.antivirus.enabled and not node.antivirus.evaded:
            node.antivirus.alert_level = min(100, node.antivirus.alert_level + 10)
        self.break_combo(reason)
        self.clear_pending_puzzle(node_id)

        msg = (
            f"🔒 HOST LOCKDOWN: {node.hostname} burned your intrusion script "
            f"(attempt {node.failed_attempts}, trace +{effective_penalty}% -> {self.state.trace_percent}%). "
            f"Its ICE is recalibrating until turn {node.lockdown_until_turn}."
        )
        self.state.message_log.append(msg)
        return True, msg

    def resolve_puzzle_near_miss(self, puzzle: Any) -> str:
        """Record a near miss and convert the first one per puzzle into a bonus attempt.

        Near misses are the strongest re-engagement cue in the reward loop; making the first
        one per puzzle mechanically real (an extra tuning attempt or one buffer retry) turns
        the cue into a small, capped win instead of pure flavor. Later near misses still
        count for telemetry but grant nothing, so a puzzle cannot be stalled forever.
        """
        if not getattr(puzzle, "near_miss", False):
            return ""
        self.state.near_miss_count += 1
        claim = getattr(puzzle, "claim_near_miss_bonus", None)
        if not callable(claim) or not claim():
            return ""
        msg = (
            "⚡ NEAR-MISS SURGE: the near-lock echo stabilizes the intrusion script — "
            "one bonus attempt granted."
        )
        self.state.message_log.append(msg)
        return msg

    def mitigated_trace(self, raw_amount: int) -> int:
        """Return the trace actually added after passive ICE dampener, stance, and proxy mitigation."""
        raw = max(0, int(raw_amount))
        if raw == 0:
            return 0
        reduction = 0.0
        if self.deck.ice_dampener_level > 0:
            reduction += min(0.60, 0.20 * self.deck.ice_dampener_level)

        stance = getattr(self.deck, "operating_stance", OperatingStance.BALANCED)
        if stance == OperatingStance.STEALTH:
            reduction += 0.35
        elif stance == OperatingStance.OVERCLOCK:
            raw = int(raw * 1.25)

        active_proxies = [
            node_id
            for node_id in getattr(self.deck, "proxy_chain", [])
            if node_id in self.nodes and self.nodes[node_id].status == NodeStatus.BREACHED
        ]
        if active_proxies:
            reduction += min(0.45, 0.15 * len(active_proxies))

        if reduction > 0:
            reduction = min(0.85, reduction)
            amount = max(1, int(raw * (1.0 - reduction)))
        else:
            amount = raw
        modifier = modifier_by_id(self.daily_modifier)
        daily_factor = modifier.trace_multiplier if modifier else 1.0
        return max(1, int(round(amount * trace_multiplier(self.difficulty) * daily_factor)))

    def extraction_surge(self) -> int:
        """Black ICE surge applied while pulling the jack, before the link is cut."""
        trace = self.state.trace_percent
        for threshold, surge in self.EXTRACTION_SURGE_BANDS:
            if trace >= threshold:
                return surge
        return 0

    def extraction_risk(self) -> Dict[str, Any]:
        """Preview the extraction surge and whether it would burn an active run."""
        surge = self.mitigated_trace(self.extraction_surge())
        projected = min(100, self.state.trace_percent + surge)
        return {
            "surge": surge,
            "projected_trace": projected,
            "lethal": projected >= 100,
        }

    def combo_rate_preview(self) -> Dict[str, Any]:
        """Return the current and next-breach combo bonus rates (informational only)."""
        current = min(0.50, 0.10 * max(0, self.state.combo_streak))
        nxt = min(0.50, 0.10 * (max(0, self.state.combo_streak) + 1))
        return {
            "streak": self.state.combo_streak,
            "current_rate": round(current, 2),
            "next_rate": round(nxt, 2),
            "unbanked_at_risk": self.state.unbanked_creds,
        }

    def action_forecast(self, action: Any, target: Any = "") -> Dict[str, Any]:
        """Preview CPU/trace/turn costs for one action without mutating any state.

        Read-only balance transparency: every number is derived from the same
        cost formulas the mutating action uses (via mitigated_trace), so the
        preview can never drift from reality. Unknown or illegal actions
        return ok False with a reason.
        """
        act = str(action or "").strip().lower()
        if self.state.is_game_over:
            return {"ok": False, "action": act, "reason": "System lockout in effect."}
        if self.state.is_jacked_out:
            return {"ok": False, "action": act, "reason": "Terminal session jacked out."}
        if self.state.is_victory:
            return {"ok": False, "action": act, "reason": "Mission already complete."}

        if act == "scan":
            return {
                "ok": True, "action": act, "cpu_delta": 1,
                "trace_gain": self.mitigated_trace(5), "turns": 1,
                "notes": "Reveals adjacent nodes; +1 CPU (capped at max).",
            }
        if act == "probe":
            node = self.find_node(str(target or ""))
            if node is None:
                return {"ok": False, "action": act, "reason": "No such host."}
            notes = "Lists open ports; +1 CPU (capped at max)."
            if (node.node_type == NodeType.ICE_DEFENSE
                    and arcs_stage("zero", self._contact_trust("zero")) >= 2):
                notes += " Zero's read: Black ICE counter-rotation inside."
            return {
                "ok": True, "action": act, "target": node.node_id,
                "cpu_delta": 1, "trace_gain": self.mitigated_trace(4), "turns": 1,
                "notes": notes,
            }
        if act == "overdrive":
            cost = 1 if arcs_stage("kilo", self._contact_trust("kilo")) >= 1 else 2
            if self.deck.cpu_cycles < cost:
                return {"ok": False, "action": act, "reason": f"Need {cost} CPU."}
            if self.state.trace_percent >= 92:
                return {"ok": False, "action": act, "reason": "Trace too high."}
            notes = "+1 combo, +10 Creds unbanked."
            if cost == 1:
                notes += " Kilo arc discount applied."
            return {
                "ok": True, "action": act, "cpu_delta": -cost,
                "trace_gain": self.mitigated_trace(8), "turns": 0,
                "notes": notes,
            }
        if act in ("spoof", "spoof_ip"):
            if self.deck.cpu_cycles < 3:
                return {"ok": False, "action": act, "reason": "Need 3 CPU."}
            if self.state.trace_percent <= 0:
                return {"ok": False, "action": act, "reason": "Trace already 0%."}
            return {
                "ok": True, "action": act, "cpu_delta": -3, "trace_gain": 0,
                "trace_reduction": min(25, self.state.trace_percent),
                "projected_trace": max(0, self.state.trace_percent - 25),
                "turns": 0, "notes": "Drops trace up to 25%; scrambles hunters 2 turns.",
            }
        if act in ("lay_low", "wait"):
            try:
                turns = max(1, min(3, int(str(target or "1").strip() or "1")))
            except (TypeError, ValueError):
                turns = 1
            room = max(0, self.deck.max_cpu - self.deck.cpu_cycles)
            return {
                "ok": True, "action": act, "cpu_delta": min(turns, room),
                "trace_gain": 0, "turns": turns,
                "notes": "Grid keeps moving (patrol, hunters, ambient).",
            }
        if act == "quickhack":
            node = self.find_node(str(target or ""))
            if node is None:
                return {"ok": False, "action": act, "reason": "No such host."}
            if node.status == NodeStatus.BREACHED:
                return {"ok": False, "action": act, "reason": "Already breached."}
            gate = self._story_gate_reason(node)
            if gate:
                return {"ok": False, "action": act, "reason": gate}
            lockdown = self._lockdown_reason(node)
            if lockdown:
                return {"ok": False, "action": act, "reason": lockdown}
            curr = self.get_current_node()
            if node.node_id not in curr.connected_ids and node.node_id != curr.node_id:
                return {"ok": False, "action": act, "reason": "Not adjacent."}
            if node.security_level > 2:
                return {
                    "ok": False, "action": act, "target": node.node_id,
                    "trace_gain": self.mitigated_trace(6), "turns": 0,
                    "reason": "Tier 3+ ICE resists quickhack.",
                }
            cpu_cost = 2 + node.security_level
            if self.deck.cpu_cycles < cpu_cost:
                return {"ok": False, "action": act, "reason": f"Need {cpu_cost} CPU."}
            heat = 0
            heat_note = ""
            if self.host_district(node.node_id)["patrol"] == "heavy":
                heat = self.mitigated_trace(1)
                heat_note = " District heat: +1% trace under heavy patrol."
            return {
                "ok": True, "action": act, "target": node.node_id,
                "cpu_delta": -cpu_cost,
                "trace_gain": self.mitigated_trace(10 + node.security_level * 4) + heat,
                "turns": 1, "notes": "Skips the mini-game; pays full breach trace." + heat_note,
            }
        if act == "jackout":
            risk = self.extraction_risk()
            return {
                "ok": True, "action": act, "cpu_delta": 0,
                "trace_gain": risk["surge"], "turns": 0,
                "projected_trace": risk["projected_trace"],
                "lethal": risk["lethal"], "notes": "Banks all unbanked loot.",
            }
        if act in ("counter_rival", "counter"):
            rival = self.state.rival
            if rival is None or rival.status != "active":
                return {"ok": False, "action": act, "reason": "No active rival."}
            cost = 1 if arcs_stage("zero", self._contact_trust("zero")) >= 1 else 2
            if self.deck.cpu_cycles < cost:
                return {"ok": False, "action": act, "reason": f"Need {cost} CPU."}
            notes = "Delays the rival board grab by 5 turns."
            if cost == 1:
                notes += " Zero arc discount applied."
            return {
                "ok": True, "action": act, "cpu_delta": -cost,
                "trace_gain": 0, "turns": 0, "notes": notes,
            }
        if act in ("wipe_logs", "wipe"):
            node = self.find_node(str(target or ""))
            if node is None:
                return {"ok": False, "action": act, "reason": "No such host."}
            if node.status != NodeStatus.BREACHED:
                return {"ok": False, "action": act, "reason": "Host is not breached."}
            scrub = 25 if arcs_stage("archivist", self._contact_trust("archivist")) >= 2 else 20
            notes = "Sanitizes access logs; the grid advances one turn."
            if scrub > 20:
                notes += " Archivist deep scrub applied."
            return {
                "ok": True, "action": act, "target": node.node_id,
                "cpu_delta": 0, "trace_gain": 0,
                "trace_reduction": min(scrub, self.state.trace_percent),
                "projected_trace": max(0, self.state.trace_percent - scrub),
                "turns": 1, "notes": notes,
            }
        if act in ("move", "hop", "transfer"):
            node = self.find_node(str(target or ""))
            if node is None:
                return {"ok": False, "action": act, "reason": "No such host."}
            allowed, reason = self.can_move_to(node.node_id)
            if not allowed:
                return {"ok": False, "action": act, "reason": reason}
            notes = "Transfers the terminal; +1 CPU (capped at max)."
            from_hood = self.host_district(self.state.current_node_id)
            to_hood = self.host_district(node.node_id)
            if from_hood["district_key"] != to_hood["district_key"]:
                notes += f" Enters {to_hood['district']} grid ({to_hood['flavor']})."
            return {
                "ok": True, "action": act, "target": node.node_id,
                "cpu_delta": 1, "trace_gain": self.mitigated_trace(2),
                "turns": 1, "notes": notes,
            }
        if act in ("social", "social_engineer", "phish"):
            node = self.find_node(str(target or ""))
            if node is None:
                return {"ok": False, "action": act, "reason": "No such host."}
            if node.status == NodeStatus.BREACHED:
                return {"ok": False, "action": act, "reason": "Host is already compromised."}
            curr = self.get_current_node()
            if node.node_id not in curr.connected_ids and node.node_id != curr.node_id:
                return {"ok": False, "action": act, "reason": "Target is out of subnet range."}
            if self.deck.cpu_cycles < 1:
                return {"ok": False, "action": act, "reason": "Need 1 CPU."}
            vector_key = SocialVectorType.SPEAR_PHISH
            emp = node.employees[0] if node.employees else None
            if emp is None:
                emp = EmployeeProfile(name="Staff Associate", role="Operations",
                                      email=f"staff@{node.hostname}",
                                      awareness_level=SecurityAwarenessLevel.STANDARD)
            chance, shift = self._social_success_chance(node, vector_key, emp)
            return {
                "ok": True, "action": act, "target": node.node_id,
                "cpu_delta": -1, "trace_gain": self.mitigated_trace(6),
                "turns": 1,
                "notes": f"Spear-phish vs {emp.name} ({emp.awareness_level}): ~{chance:.0%} success on {shift} shift, {self.host_district(node.node_id)['district']} grid.",
            }
        if act in ("bypass", "bypass_firewall", "fw"):
            node = self.find_node(str(target or ""))
            if node is None:
                return {"ok": False, "action": act, "reason": "No such host."}
            curr = self.get_current_node()
            if node.node_id not in curr.connected_ids and node.node_id != curr.node_id:
                return {"ok": False, "action": act, "reason": "Target is out of subnet range."}
            if not node.firewall or not node.firewall.enabled:
                return {"ok": False, "action": act, "reason": "Host has no active firewall."}
            blocked = [r for r in (node.firewall.rules or []) if r.action == "BLOCK" and not r.bypassed]
            if not blocked:
                return {"ok": False, "action": act, "reason": "No blocked ports to bypass."}
            if self.deck.cpu_cycles < 1:
                return {"ok": False, "action": act, "reason": "Need 1 CPU."}
            return {
                "ok": True, "action": act, "target": node.node_id,
                "cpu_delta": -1, "trace_gain": self.mitigated_trace(5),
                "turns": 1,
                "notes": f"Knock opens a blocked port ({len(blocked)} blocked); fragment 7% / tunnel 2 CPU 9% hit harder.",
            }
        if act in ("evade", "evade_av", "av"):
            node = self.find_node(str(target or ""))
            if node is None:
                return {"ok": False, "action": act, "reason": "No such host."}
            curr = self.get_current_node()
            if node.node_id not in curr.connected_ids and node.node_id != curr.node_id:
                return {"ok": False, "action": act, "reason": "Target is out of subnet range."}
            if not node.antivirus or not node.antivirus.enabled:
                return {"ok": False, "action": act, "reason": "Host has no active Antivirus to evade."}
            if node.antivirus.evaded:
                return {"ok": False, "action": act, "reason": "Antivirus is already evaded."}
            if self.deck.cpu_cycles < 2:
                return {"ok": False, "action": act, "reason": "Need 2 CPU."}
            return {
                "ok": True, "action": act, "target": node.node_id,
                "cpu_delta": -2, "trace_gain": self.mitigated_trace(6),
                "turns": 1,
                "notes": "Rootkit blinds EDR and drops its alert 35%; spoof costs 1 CPU but +8% trace.",
            }
        if act in ("deploy", "daemon", "keylogger"):
            node = self.find_node(str(target or ""))
            if node is None:
                return {"ok": False, "action": act, "reason": "No such host."}
            if node.status != NodeStatus.BREACHED:
                return {"ok": False, "action": act, "reason": "Host is not breached."}
            if any(d.target_node_id == node.node_id and d.daemon_type == "keylogger"
                   for d in self.deck.active_daemons):
                return {"ok": False, "action": act, "reason": "Keylogger already running on this host."}
            if self.deck.cpu_cycles < 2:
                return {"ok": False, "action": act, "reason": "Need 2 CPU."}
            daemon_yield = 15 + node.security_level * 5
            boosted = arcs_stage("kilo", self._contact_trust("kilo")) >= 2
            if boosted:
                daemon_yield += max(1, daemon_yield // 10)
            notes = (f"+{daemon_yield} unbanked Creds/turn passive siphon, +3% trace/tick exposure, "
                     "+2 alert on install.")
            if boosted:
                notes += " Kilo arc yield applied."
            return {
                "ok": True, "action": act, "target": node.node_id,
                "cpu_delta": -2, "trace_gain": 0, "turns": 0, "notes": notes,
            }
        if act in ("reveal", "intel_reveal"):
            node = self.find_node(str(target or ""))
            if node is None:
                return {"ok": False, "action": act, "reason": "Intel reveal needs a known host."}
            if node.status == NodeStatus.BREACHED:
                return {"ok": False, "action": act, "reason": "Host is already breached."}
            if self.deck.threat_intel_count < 1:
                return {"ok": False, "action": act, "reason": "Need 1 intel fragment."}
            return {
                "ok": True, "action": act, "target": node.node_id,
                "cpu_delta": 0, "trace_gain": 0, "turns": 0, "intel_delta": -1,
                "notes": "Remote deep scan: services, vulns, blocked ports, EDR. No trace, no clock.",
            }
        if act in ("forge", "intel_forge"):
            if "zero_day_forge" in self.deck.exploits:
                return {"ok": False, "action": act, "reason": "A zero_day_forge chip is already loaded."}
            if self.deck.threat_intel_count < 2:
                return {"ok": False, "action": act, "reason": "Need 2 intel fragments."}
            return {
                "ok": True, "action": act,
                "cpu_delta": 0, "trace_gain": 0, "turns": 0, "intel_delta": -2,
                "notes": "Mints zero_day_forge: breach any adjacent host outright.",
            }
        if act in ("proxy", "tunnel", "proxy_hop"):
            node = self.find_node(str(target or ""))
            if node is None:
                return {"ok": False, "action": act, "reason": "No such host."}
            if node.status != NodeStatus.BREACHED:
                return {"ok": False, "action": act, "reason": "Host is not breached."}
            if node.node_id == self.state.current_node_id:
                return {"ok": False, "action": act, "reason": "Cannot proxy through the active terminal host."}
            if node.node_id in self.deck.proxy_chain:
                return {"ok": False, "action": act, "reason": "Host is already in the proxy chain."}
            if len(self.deck.proxy_chain) >= 3:
                return {"ok": False, "action": act, "reason": "Proxy chain limit reached (max 3 hops)."}
            if self.deck.cpu_cycles < 1:
                return {"ok": False, "action": act, "reason": "Need 1 CPU."}
            dampen = min(45, (len(self.deck.proxy_chain) + 1) * 15)
            return {
                "ok": True, "action": act, "target": node.node_id,
                "cpu_delta": -1, "trace_gain": 0, "turns": 0,
                "notes": f"Splice tunnel ({len(self.deck.proxy_chain) + 1}/3 hops): -{dampen}% trace generation.",
            }
        if act in ("sever", "sever_proxy", "burn_proxy"):
            if not self.deck.proxy_chain:
                return {"ok": False, "action": act, "reason": "No active proxy hops to sever."}
            return {
                "ok": True, "action": act,
                "cpu_delta": 0, "trace_gain": 0,
                "trace_reduction": min(15, self.state.trace_percent),
                "projected_trace": max(0, self.state.trace_percent - 15),
                "turns": 0, "notes": "Burn a tunnel hop to dump 15% trace immediately.",
            }
        if act in ("counter_hunter", "hunter", "countermeasure"):
            active_hunters = [h for h in self.state.world.hunters
                              if h.status in ("hunting", "confused", "intercepted")]
            if not active_hunters:
                return {"ok": False, "action": act, "reason": "No active NetWatch hunters."}
            hunter = active_hunters[0]
            options = []
            ready = False
            if "logic_bomb" in self.deck.exploits:
                options.append("logic_bomb READY (neutralize)")
                ready = True
            else:
                options.append("logic_bomb MISSING chip")
            if "ghost_protocol" in self.deck.exploits:
                options.append("ghost_protocol READY (-30% trace, banish)")
                ready = True
            else:
                options.append("ghost_protocol MISSING chip")
            if self.deck.cpu_cycles >= 3:
                options.append("cpu_burst READY (3 CPU, confuse 3 turns)")
                ready = True
            else:
                options.append("cpu_burst NEEDS 3 CPU")
            if not ready:
                return {"ok": False, "action": act,
                        "reason": f"{hunter.name} is active but no countermeasure is available."}
            return {
                "ok": True, "action": act, "target": hunter.current_node_id,
                "cpu_delta": 0, "trace_gain": 0, "turns": 0,
                "notes": f"{hunter.name} ({hunter.status}) is the target. " + "; ".join(options) + ".",
            }
        return {"ok": False, "action": act, "reason": f"Unknown action '{act}'."}

    @staticmethod
    def hop_latency_ms(node: Any) -> int:
        """Deterministic per-hop latency: base + security tiers + stable jitter."""
        base = 8 + max(1, int(getattr(node, "security_level", 1))) * 3
        jitter = abs(hash(getattr(node, "node_id", "?"))) % 7
        return base + jitter

    def trace_route(self, target: Any = "") -> Dict[str, Any]:
        """Trace the hop path from the current host to a target (read-only)."""
        node = self.find_node(str(target or ""))
        if node is None:
            return {"ok": False, "reason": f"No such host '{target}'."}
        start = self.state.current_node_id
        if node.node_id == start:
            hop = {"node_id": node.node_id, "hostname": node.hostname,
                   "ip_address": node.ip_address, "latency_ms": self.hop_latency_ms(node)}
            return {"ok": True, "target": node.node_id, "hops": [hop],
                    "total_latency_ms": hop["latency_ms"], "hop_count": 1}
        prev: Dict[str, Optional[str]] = {start: None}
        queue = [start]
        while queue:
            current = queue.pop(0)
            cur_node = self.nodes.get(current)
            if cur_node is None:
                continue
            for nxt in cur_node.connected_ids:
                if nxt not in prev and nxt in self.nodes:
                    prev[nxt] = current
                    queue.append(nxt)
        if node.node_id not in prev:
            return {"ok": False, "reason": "Target unreachable from current subnet."}
        path = []
        cursor: Optional[str] = node.node_id
        while cursor is not None:
            path.append(cursor)
            cursor = prev[cursor]
        path.reverse()
        hops = []
        total = 0
        for nid in path:
            hop_node = self.nodes[nid]
            latency = self.hop_latency_ms(hop_node)
            total += latency
            hops.append({"node_id": nid, "hostname": hop_node.hostname,
                         "ip_address": hop_node.ip_address,
                         "node_type": hop_node.node_type,
                         "security_level": hop_node.security_level,
                         "latency_ms": latency})
        return {"ok": True, "target": node.node_id, "hops": hops,
                "total_latency_ms": total, "hop_count": len(hops)}

    def host_fingerprint(self, target: Any = "") -> Dict[str, Any]:
        """Summarize a host's identity: OS, uptime, patch train, ports, staff shifts."""
        node = self.find_node(str(target or ""))
        if node is None:
            return {"ok": False, "reason": f"No such host '{target}'."}
        try:
            current_shift = shift_name(self.state.world.minute)
        except (AttributeError, TypeError, ValueError):  # hygiene: clock glitch never blocks recon
            current_shift = "Unknown"
        shift_key = str(current_shift or "").strip().lower()
        on_shift = 0
        by_shift: Dict[str, int] = {"day": 0, "night": 0, "swing": 0}
        for emp in node.employees:
            ws = str(getattr(emp, "work_shift", "day") or "day").lower()
            by_shift[ws] = by_shift.get(ws, 0) + 1
            day_hours = "morning" in shift_key or "afternoon" in shift_key
            night_hours = "evening" in shift_key or "late" in shift_key
            if ws == "swing" or (ws == "day" and day_hours) or (ws == "night" and night_hours):
                on_shift += 1
        return {
            "ok": True, "node_id": node.node_id, "hostname": node.hostname,
            "ip_address": node.ip_address, "node_type": node.node_type,
            "security_level": node.security_level, "status": node.status,
            "os_name": getattr(node, "os_name", "Unknown OS"),
            "uptime_hours": getattr(node, "uptime_hours", 0),
            "uptime_days": round(getattr(node, "uptime_hours", 0) / 24, 1),
            "patch_level": getattr(node, "patch_level", "patch-unknown"),
            "open_ports": len(node.ports or []),
            "current_shift": current_shift,
            "employees_on_shift": on_shift,
            "employees_total": len(node.employees or []),
            "shifts": by_shift,
        }

    def add_trace(self, raw_amount: int) -> None:
        """Increase system trace, mitigated by ICE dampeners. 100% triggers lockout & loss of loot."""
        amount = self.mitigated_trace(raw_amount)

        before = self.state.trace_percent
        self.state.trace_percent = min(100, self.state.trace_percent + amount)

        # Living-grid headlines for trace escalation
        if before < 50 <= self.state.trace_percent:
            record_news(
                self.state.world,
                self.state.turns_elapsed,
                "NetWatch",
                "Intrusion signature crossed the 50% NetWatch trace threshold.",
            )
        if before < 80 <= self.state.trace_percent:
            record_news(
                self.state.world,
                self.state.turns_elapsed,
                "NetWatch",
                "Black ICE lock-in at 80% trace; connection integrity degrading.",
                tone="alert",
            )

        # High-arousal danger feedback; near misses are counted only by the puzzle layer.
        if 80 <= self.state.trace_percent < 100:
            self.state.message_log.append(
                f"⚠️ CRITICAL TRACE WARNING: {self.state.trace_percent}%! Black ICE locks tightening!"
            )

        if self.state.trace_percent >= 100:
            already_over = self.state.is_game_over
            self.state.is_game_over = True
            self.state.combo_streak = 0
            lost_loot = self.state.unbanked_creds
            covered = 0
            if not already_over and self.deck.extraction_insurance and lost_loot > 0:
                covered = lost_loot // 2
                if covered:
                    lost_loot -= covered
                    self.deck.cryptocreds += covered
                    self.deck.extraction_insurance = False
                    self.state.message_log.append(
                        f"🛡️ Dead Man's Switch banked {covered} unbanked Creds before the ICE burned the link."
                    )
            self.state.unbanked_creds = 0
            if not already_over:
                self.state.lost_creds = lost_loot
            self.state.looted_payloads.clear()
            record_news(
                self.state.world,
                self.state.turns_elapsed,
                "NetWatch",
                "A netrunner's deck burned out mid-intrusion in the Sprawl.",
                tone="negative",
            )
            self.state.message_log.append(
                f"🚨 SECURITY TRACE LOCKOUT DETECTED! Connection severed. Lost {lost_loot} unbanked Creds!"
            )

    def regenerate_cpu(self, amount: int = 1) -> int:
        """Cool down cyberdeck processing units and recover CPU cycles."""
        old = self.deck.cpu_cycles
        self.deck.cpu_cycles = min(self.deck.max_cpu, self.deck.cpu_cycles + amount)
        return self.deck.cpu_cycles - old

    def advance_turn(self) -> List[str]:
        """Advance the run clock one turn: daemons harvest, then the living grid reacts."""
        self.state.turns_elapsed += 1
        messages = self.tick_daemons()
        messages.extend(self.tick_world())
        if getattr(self.deck, "operating_stance", OperatingStance.BALANCED) == OperatingStance.OVERCLOCK:
            if self.state.turns_elapsed % 2 == 0:
                self.regenerate_cpu(1)
        return messages

    def refresh_faction_bonuses(self) -> None:
        """Recompute cached faction multipliers from the current standing snapshot."""
        self.contract_standing_bonus = contract_bonus(self.faction_standing)
        self.street_standing_discount = street_discount(self.faction_standing)

    def shop_price_multiplier(self) -> float:
        """Return the live market index after the Street standing discount."""
        market = self.world_summary()["market_multiplier"]
        discount = self.street_standing_discount + self.allegiance_shop_discount
        return market * max(0.5, 1.0 - discount)

    def daily_modifier_summary(self) -> Optional[Dict[str, Any]]:
        """Return the active daily modifier for HUD and archive display."""
        modifier = modifier_by_id(self.daily_modifier)
        if modifier is None:
            return None
        return {
            "modifier_id": modifier.modifier_id,
            "name": modifier.name,
            "description": modifier.description,
            "start_alert": modifier.start_alert,
            "start_cpu": modifier.start_cpu,
            "trace_multiplier": modifier.trace_multiplier,
            "contract_multiplier": modifier.contract_multiplier,
        }

    def tutorial_progress(self) -> List[Dict[str, Any]]:
        """Return the first-run field manual with live completion flags."""
        return tutorial_steps(self)

    def rival_summary(self) -> Optional[Dict[str, Any]]:
        """Return the active rival's public status for HUD and dossier display."""
        rival = self.state.rival
        if rival is None:
            return None
        return {
            "name": rival.name,
            "handle": rival.handle,
            "skill": rival.skill,
            "tagline": rival.tagline,
            "status": rival.status,
            "next_move_turn": rival.next_move_turn,
            "turns_until": max(0, rival.next_move_turn - self.state.turns_elapsed),
            "contracts_stolen": rival.contracts_stolen,
        }

    def counter_rival(self) -> Tuple[bool, str]:
        """Burn CPU to trace the rival and postpone their next contract grab."""
        rival = self.state.rival
        if rival is None or rival.status != "active":
            return False, "No active rival netrunner to counter."
        # Zero's arc (trust 2+): she feeds you the rival's schedule, halving the cost.
        cost = 1 if arcs_stage("zero", self._contact_trust("zero")) >= 1 else 2
        if self.deck.cpu_cycles < cost:
            return False, f"Counter-trace needs {cost} CPU cycle(s)."
        self.deck.cpu_cycles -= cost
        rival.next_move_turn += 5
        message = (
            f"🛰️ [RIVAL] Counter-traced {rival.name}; their next board move is delayed "
            f"by 5 turns (ETA {max(0, rival.next_move_turn - self.state.turns_elapsed)}T)."
        )
        if cost == 1:
            message += " [ZERO ARC: discounted trace]"
        self.state.message_log.append(message)
        return True, message

    def _tick_rival(self) -> List[str]:
        """Let the rival compete for a posted contract, or probe when the board is empty."""
        rival = self.state.rival
        if rival is None or rival.status != "active":
            return []
        now = self.state.turns_elapsed
        if now < rival.next_move_turn:
            return []

        self._refresh_contract_offers()
        rng = world_rng(self.seed, now, f"rival:{rival.handle}")
        if self.state.contract_offers:
            offer = self.state.contract_offers.pop(rng.randrange(len(self.state.contract_offers)))
            rival.contracts_stolen += 1
            delay = rival_move_delay(rival.skill, self.state.story_act, rng.randint(0, 2))
            rival.next_move_turn = now + delay
            message = (
                f"🕶️ [RIVAL] {rival.name} ({rival.handle}) snatched '{offer.title}' "
                f"from the job board; next move in ~{delay} turns."
            )
            record_news(
                self.state.world,
                now,
                "Syndicate",
                f"Rival runner {rival.name} claimed a Syndicate contract before the board could fill.",
                tone="alert",
            )
            self.state.message_log.append(message)
            return [message]

        pressure = 2 + rival.skill
        self.add_trace(pressure)
        delay = rival_move_delay(rival.skill, self.state.story_act, rng.randint(0, 2))
        rival.next_move_turn = now + delay
        message = (
            f"🕶️ [RIVAL] {rival.name} pinged your link looking for work "
            f"(+{pressure}% trace, next move in ~{delay} turns)."
        )
        self.state.message_log.append(message)
        return [message]

    def lay_low(self, turns: int = 1) -> Tuple[bool, str]:
        """Ghost the connection for a few turns: recover CPU while the grid keeps moving."""
        if self.state.is_game_over:
            return False, "Cannot lay low: system lockout in effect."
        if self.state.is_jacked_out:
            return False, "Cannot lay low: terminal session jacked out."
        if self.state.is_victory:
            return False, "Cannot lay low: mission already complete."
        try:
            count = int(turns)
        except (TypeError, ValueError):
            return False, "Lay low accepts a whole number of turns (1-3)."
        if count < 1 or count > self.MAX_LAY_LOW_TURNS:
            return False, f"Lay low accepts 1-{self.MAX_LAY_LOW_TURNS} turns."

        world = self.state.world
        cpu_before = self.deck.cpu_cycles
        trace_before = self.state.trace_percent
        alert_before = world.alert_level
        turns_before = self.state.turns_elapsed
        messages: List[str] = []
        for _ in range(count):
            self.regenerate_cpu(1)
            # A silent connection lets NetWatch lose the scent: trace cools while ghosted.
            if self.state.trace_percent > 0:
                self.state.trace_percent = max(0, self.state.trace_percent - self.LAY_LOW_TRACE_COOLING)
            messages.extend(self.advance_turn())
            if self.state.is_game_over or self.state.is_jacked_out or self.state.is_victory:
                break

        elapsed = self.state.turns_elapsed - turns_before
        cooling_note = (
            f"ghost cooling -{self.LAY_LOW_TRACE_COOLING}%/turn, " if trace_before > 0 else ""
        )
        summary = (
            f"🛰️ [LAY LOW] Ghosted the connection for {elapsed} turn(s) until {clock_label(world)}: "
            f"CPU {self.deck.cpu_cycles - cpu_before:+d}, {cooling_note}"
            f"trace {trace_before}% -> {self.state.trace_percent}%, "
            f"alert {alert_before}% -> {world.alert_level}%."
        )
        if self.state.is_game_over:
            summary += " The grid burned your deck while you idled."
        elif self.state.is_victory:
            summary += " The run reached a terminal state during downtime."
        detail = " ".join(message for message in messages if message)
        full_message = f"{summary} {detail}".strip()
        self.state.message_log.append(summary)
        return True, full_message

    def tick_world(self) -> List[str]:
        """Advance the in-game clock, alert, market, ambient events, and grid response."""
        if self.state.is_game_over or self.state.is_jacked_out or self.state.is_victory:
            return []
        world = self.state.world
        if self._last_alert_tier is None:
            # Silent baseline sync so loaded saves do not report a phantom escalation.
            self._last_alert_tier = alert_tier(world.alert_level)
        advance_clock(world)
        profile = shift_profile(world.minute)
        drift_market(world, world_rng(self.seed, self.state.turns_elapsed, "drift"), bias=profile.market_bias)
        world.turns_since_event += 1
        messages: List[str] = []
        self._decay_alert(profile.alert_decay_bonus)
        messages.extend(self._check_contract_clock())
        rival_messages = self._tick_rival()
        if rival_messages:
            messages.extend(rival_messages)
            if self.state.is_game_over:
                return messages

        event = ambient_event_for(
            self.seed, self.state.turns_elapsed, world.alert_level, world.turns_since_event
        )
        if event:
            messages.extend(self._apply_ambient_event(event))
            if self.state.is_game_over:
                return messages

        pressure = patrol_pressure(world)
        if pressure:
            self.add_trace(pressure)
            msg = (
                f"🚨 [NETWATCH PATROL] Grid alert {world.alert_level}% sustains an active ICE sweep "
                f"(+{pressure}% trace)."
            )
            messages.append(msg)
            self.state.message_log.append(msg)
            if self.state.is_game_over:
                return messages

        # Street simulation bites back: under BLACK alert, two or more
        # heavy-patrol districts run coordinated sweeps (+1 trace).
        if world.alert_level >= 75:
            heavy = [d for d in arcs_districts(self.seed, int(self.state.turns_elapsed),
                                               int(world.alert_level))
                     if d["patrol"] == "heavy"]
            if len(heavy) >= 2:
                self.add_trace(1)
                names = ", ".join(d["name"] for d in heavy[:2])
                sweep_msg = (
                    f"🚨 [DISTRICT SWEEP] {names} run a coordinated NetWatch sweep "
                    "(+1% trace)."
                )
                messages.append(sweep_msg)
                self.state.message_log.append(sweep_msg)
                record_news(
                    world,
                    self.state.turns_elapsed,
                    "NetWatch",
                    f"Coordinated sweeps hit {names}; runners report burned proxies.",
                    tone="alert",
                )
                if self.state.is_game_over:
                    return messages

        for node_id in plan_resecures(
            self.seed,
            self.state.turns_elapsed,
            world.alert_level,
            self.nodes,
            self.state.current_node_id,
            chance_delta=profile.resecure_chance_delta,
        ):
            node = self.nodes[node_id]
            message = apply_resecure(node)
            message += f" ({self.host_district(node_id)['district']} grid back under corporate control.)"
            if node_id in self.deck.proxy_chain:
                self.deck.proxy_chain.remove(node_id)
                message += " Proxy tunnel collapsed."
            recalled = self._recall_daemons(node_id)
            if recalled:
                message += f" {recalled} background daemon(s) quarantined."
            world.resecured_count += 1
            record_news(
                world,
                self.state.turns_elapsed,
                "NetWatch",
                f"Sysadmins re-secured {node.hostname} ({self.host_district(node_id)['district']} grid); intruder access revoked.",
                tone="alert",
            )
            messages.append(message)
            self.state.message_log.append(message)

        deployed_hunter = deploy_hunter(world, self.nodes, self.state.turns_elapsed)
        if deployed_hunter:
            spawn_node = self.nodes.get(deployed_hunter.current_node_id)
            spawn_name = spawn_node.name if spawn_node else deployed_hunter.current_node_id
            spawn_hood = self.host_district(deployed_hunter.current_node_id)
            hunter_msg = (
                f"🚨 [NETWATCH HUNTER] Critical grid alert {world.alert_level}% triggered deployment of "
                f"{deployed_hunter.name} at {spawn_name} — {spawn_hood['district']} grid, "
                f"patrols {spawn_hood['patrol']}."
            )
            messages.append(hunter_msg)
            self.state.message_log.append(hunter_msg)

        hunter_rng = world_rng(self.seed, self.state.turns_elapsed, "hunter_move")
        for hunter in world.hunters:
            if hunter.status not in ("hunting", "confused", "intercepted"):
                continue
            step_res = step_hunter(hunter, self.nodes, self.state.current_node_id, hunter_rng)
            action = step_res.get("action")
            curr_node = self.get_current_node()
            target_node = self.nodes.get(hunter.current_node_id)
            target_name = target_node.name if target_node else hunter.current_node_id

            if action == "intercepted" or hunter.current_node_id == self.state.current_node_id:
                hunter.status = "intercepted"
                self.add_trace(15)
                self.break_combo(f"{hunter.name} clashed with your connection")
                cpu_drained = min(2, self.deck.cpu_cycles)
                self.deck.cpu_cycles = max(0, self.deck.cpu_cycles - 2)
                inter_msg = (
                    f"💥 [NETWATCH CLASH] {hunter.name} intercepted your connection at {curr_node.name}! "
                    f"CPU drained (-{cpu_drained}) and ICE trace spiked (+15% -> {self.state.trace_percent}%)! "
                    f"({self.host_district(curr_node.node_id)['district']} grid lockdown.)"
                )
                record_news(
                    world,
                    self.state.turns_elapsed,
                    "NetWatch",
                    f"{hunter.name} engaged netrunner at {curr_node.name}!",
                    tone="alert",
                )
                messages.append(inter_msg)
                self.state.message_log.append(inter_msg)
                if self.state.is_game_over:
                    return messages
            elif action == "moved":
                recalled = self._recall_daemons(hunter.current_node_id)
                if recalled:
                    purge_msg = f"🧹 [NETWATCH SWEEP] {hunter.name} swept {target_name} and purged {recalled} daemon(s)!"
                    messages.append(purge_msg)
                    self.state.message_log.append(purge_msg)

                dist = calculate_distance(self.nodes, hunter.current_node_id, self.state.current_node_id)
                if dist == 1:
                    prox_hood = self.host_district(hunter.current_node_id)
                    prox_msg = (
                        f"⚠️ [HUNTER PROXIMITY] {hunter.name} detected 1 hop away at {target_name} "
                        f"({prox_hood['district']} grid)!"
                    )
                    messages.append(prox_msg)
                    self.state.message_log.append(prox_msg)

        tier_msg = self._announce_alert_tier()
        if tier_msg:
            messages.append(tier_msg)
        return messages

    def _intrusion_footprint(self) -> int:
        """Count currently-breached hosts the corporation still has to clean up."""
        return sum(
            1
            for node in self.nodes.values()
            if node.status == NodeStatus.BREACHED and node.node_type != NodeType.GATEWAY
        )

    def _announce_alert_tier(self) -> Optional[str]:
        """Report a corporate posture change to the wire and the run log."""
        before_tier = self._last_alert_tier or alert_tier(self.state.world.alert_level)
        after_tier = alert_tier(self.state.world.alert_level)
        self._last_alert_tier = after_tier
        if before_tier == after_tier:
            return None

        escalating = tier_rank(after_tier) > tier_rank(before_tier)
        if escalating:
            headlines = {
                "AMBER": ("OmniCorp PR", "OmniCorp raises grid posture to AMBER: intrusion reports under review."),
                "RED": ("NetWatch", "NetWatch escalates the grid to RED: active counter-intrusion protocols."),
                "BLACK": ("NetWatch", "NetWatch declares BLACK alert: total corporate mobilization against the intruder."),
            }
            source, headline = headlines.get(after_tier, ("GridWire", f"Grid posture shifts to {after_tier}."))
            tone = "alert" if after_tier in ("RED", "BLACK") else "neutral"
            message = (
                f"🚨 [GRID POSTURE] Corporate response escalated {before_tier} -> {after_tier} "
                f"(alert {self.state.world.alert_level}%)."
            )
        else:
            headlines = {
                "AMBER": ("GridWire", "Corporate posture relaxes to AMBER after a quieter shift on the grid."),
                "GREEN": ("GridWire", "OmniCorp stands down to GREEN: the Sprawl breathes again."),
            }
            source, headline = headlines.get(after_tier, ("GridWire", f"Grid posture cools to {after_tier}."))
            tone = "positive"
            message = (
                f"😌 [GRID POSTURE] Corporate response cooled {before_tier} -> {after_tier} "
                f"(alert {self.state.world.alert_level}%)."
            )

        record_news(self.state.world, self.state.turns_elapsed, source, headline, tone=tone)
        self.state.message_log.append(message)
        return message

    def _decay_alert(self, shift_bonus: int = 0) -> int:
        """Cool the grid while trace is low; a hot trace keeps corporate response elevated.

        A wide intrusion footprint (breached hosts the corporation still sees as
        compromised) keeps sysadmins mobilized, slowing the decay by up to 3 per turn.
        """
        trace = self.state.trace_percent
        if trace >= 70:
            base = 1
        elif trace >= 40:
            base = -1
        else:
            base = -2
        footprint_penalty = min(3, self._intrusion_footprint() // 2)
        mira_bonus = 0
        # Mira's arc (trust 6+): her ledger crew scrubs your name while you run
        # a Syndicate (mira-giver) contract, cooling the grid one extra point.
        contract = self.state.active_contract
        if (contract is not None and getattr(contract, "giver", "") == "mira"
                and arcs_stage("mira", self._contact_trust("mira")) >= 3):
            mira_bonus = 1
        return adjust_alert(self.state.world, base - int(shift_bonus) + footprint_penalty - mira_bonus)

    def _ambient_district(self, event_key: str) -> str:
        """Street grounding for ambient grid events: fixed beats keep their home
        district, while brownouts and ICE patrols strike the heaviest-load grid."""
        fixed = {
            "street_chatter": "neon_row",
            "freelance_wire": "dead_archive",
            "corporate_pr": "ledger_heights",
            "crackdown": "black_ice_ward",
        }
        rows = arcs_districts(self.seed, int(self.state.turns_elapsed),
                              int(self.state.world.alert_level))
        by_key = {row["key"]: row for row in rows}
        if event_key in fixed:
            return by_key.get(fixed[event_key], {}).get("name", "")
        if event_key in ("grid_brownout", "ice_patrol") and rows:
            return max(rows, key=lambda row: row["load"])["name"]
        return ""

    def _apply_ambient_event(self, event: AmbientEvent) -> List[str]:
        """Apply a rolled ambient grid event to the deck, loot, alert, or topology."""
        world = self.state.world
        world.turns_since_event = 0
        effects: List[str] = []
        if event.credits:
            self.state.unbanked_creds += event.credits
            effects.append(f"+{event.credits} CR")
        if event.cpu and not (self.state.is_game_over or self.state.is_jacked_out or self.state.is_victory):
            self.deck.cpu_cycles = max(0, min(self.deck.max_cpu, self.deck.cpu_cycles + event.cpu))
            effects.append(f"CPU {event.cpu:+d}")
        if event.alert:
            adjust_alert(world, event.alert)
            effects.append(f"alert {event.alert:+d}%")
        if event.reveal:
            revealed = self._reveal_frontier_node()
            if revealed:
                hood = self.host_district(revealed.node_id)
                effects.append(
                    f"revealed {revealed.hostname} ({revealed.ip_address}) [{hood['district']}]"
                )
        if event.trace:
            self.add_trace(event.trace)
            effects.append(f"+{event.trace}% trace")

        district = self._ambient_district(event.key)
        tag = f" [{district}]" if district else ""
        record_news(world, self.state.turns_elapsed, event.source, event.headline + tag, tone=event.tone)
        suffix = f" ({', '.join(effects)})" if effects else ""
        message = f"🌐 [GRID EVENT] {event.headline}{tag}{suffix}"
        self.state.message_log.append(message)
        return [message]

    def _reveal_frontier_node(self) -> Optional["Node"]:
        """Reveal one locked node adjacent to the current host, else any locked node."""
        current = self.get_current_node()
        locked = [self.nodes[nid] for nid in current.connected_ids if self.nodes.get(nid) and self.nodes[nid].status == NodeStatus.LOCKED]
        if not locked:
            locked = [node for node in sorted(self.nodes.values(), key=lambda n: n.node_id) if node.status == NodeStatus.LOCKED]
        if not locked:
            return None
        target = sorted(locked, key=lambda n: n.node_id)[0]
        target.status = NodeStatus.DISCOVERED
        return target

    def _recall_daemons(self, node_id: str) -> int:
        """Remove player daemons from a host after the grid re-secures it."""
        remaining = [d for d in self.deck.active_daemons if d.target_node_id != node_id]
        recalled = len(self.deck.active_daemons) - len(remaining)
        self.deck.active_daemons = remaining
        return recalled

    def scramble_hunter_radar(self, turns: int = 2) -> int:
        """Confuse active hunters' tracking algorithms for a number of turns."""
        count = 0
        for h in self.state.world.hunters:
            if h.status in ("hunting", "confused"):
                h.confused_turns = max(h.confused_turns, turns)
                h.status = "confused"
                count += 1
        return count

    def counter_hunter(self, method: str = "logic_bomb") -> Tuple[bool, str]:
        """Deploy tactical countermeasures against an active NetWatch Hunter."""
        if self.state.is_game_over:
            return False, "Cannot counter hunter: system lockout in effect."
        if self.state.is_jacked_out:
            return False, "Cannot counter hunter: terminal session jacked out."
        if self.state.is_victory:
            return False, "Cannot counter hunter: mission already complete."

        active_hunters = [h for h in self.state.world.hunters if h.status in ("hunting", "confused", "intercepted")]
        if not active_hunters:
            return False, "No active NetWatch hunters detected in sector."

        hunter = active_hunters[0]
        method = (method or "logic_bomb").lower().strip()

        if method == "logic_bomb":
            if "logic_bomb" not in self.deck.exploits:
                return False, "No logic_bomb exploit chip loaded in cyberdeck."
            self.deck.exploits.remove("logic_bomb")
            neutralize_hunter(hunter, reason="logic_bomb")
            record_news(
                self.state.world,
                self.state.turns_elapsed,
                "GridWire",
                f"NetWatch hunter {hunter.name} destroyed by intruder logic bomb payload.",
                tone="positive",
            )
            msg = f"💣 [COUNTERMEASURE] Detonated logic_bomb! {hunter.name} neutralized and offline!"
            self.state.message_log.append(msg)
            return True, msg

        if method == "ghost_protocol":
            if "ghost_protocol" not in self.deck.exploits:
                return False, "No ghost_protocol exploit chip loaded in cyberdeck."
            self.deck.exploits.remove("ghost_protocol")
            hunter.confused_turns = 4
            hunter.status = "confused"
            for nid, node in self.nodes.items():
                if node.node_type == NodeType.CENTRAL_CORE:
                    hunter.current_node_id = nid
                    break
            reduced = min(self.state.trace_percent, 30)
            self.state.trace_percent = max(0, self.state.trace_percent - 30)
            msg = f"👻 [COUNTERMEASURE] Deployed ghost_protocol! Masked signature, dropped trace by {reduced}%, and banished {hunter.name}!"
            self.state.message_log.append(msg)
            return True, msg

        if method in ("cpu_burst", "scramble"):
            if self.deck.cpu_cycles < 3:
                return False, "Insufficient CPU cycles (need 3 CPU for electronic scramble)."
            self.deck.cpu_cycles -= 3
            hunter.confused_turns = 3
            hunter.status = "confused"
            msg = f"⚡ [COUNTERMEASURE] Burned 3 CPU for electronic jamming! {hunter.name} sensors scrambled for 3 turns."
            self.state.message_log.append(msg)
            return True, msg

        return False, f"Unknown countermeasure method '{method}'. Valid: logic_bomb, ghost_protocol, cpu_burst"

    def spoof_ip(self) -> Tuple[bool, str]:
        """Reduce active trace level by burning CPU cycles."""
        if self.state.is_game_over:
            return False, "Cannot spoof: system lockout in effect."
        if self.state.is_jacked_out:
            return False, "Cannot spoof: terminal session jacked out."
        if self.deck.cpu_cycles < 3:
            return False, "Insufficient CPU cycles (need 3 CPU)."
        if self.state.trace_percent <= 0:
            return False, "Cannot spoof: active trace is already at 0%."
        self.deck.cpu_cycles -= 3
        before = self.state.trace_percent
        self.state.trace_percent = max(0, before - 25)
        reduced = before - self.state.trace_percent
        self.scramble_hunter_radar(turns=2)
        msg = f"🛡️ IP Proxy bounced. Trace reduced by {reduced}% (current: {self.state.trace_percent}%)."
        self.state.message_log.append(msg)
        return True, msg

    def break_combo(self, reason: str) -> bool:
        """Shatter the active combo streak after a detected intrusion failure.

        Loss aversion keeps the streak meaningful: any detected failure (burned-out
        puzzle, flagged social lure, hunter clash, AV quarantine) resets the combo
        while the career-relevant best combo is preserved.
        """
        if self.state.combo_streak <= 0:
            return False
        lost = self.state.combo_streak
        self.state.combo_streak = 0
        msg = f"💔 COMBO BROKEN: neural sync x{lost} lost — {reason}."
        self.state.message_log.append(msg)
        return True

    def overdrive(self) -> Tuple[bool, str]:
        """Burn CPU and trace to stack a combo before the next breach."""
        if self.state.is_game_over:
            return False, "Cannot overdrive: system lockout in effect."
        if self.state.is_jacked_out:
            return False, "Cannot overdrive: terminal session jacked out."
        if self.state.is_victory:
            return False, "Cannot overdrive: mission already complete."
        # Kilo's arc (trust 2+): a spare cooling cell halves the CPU burn.
        cost = 1 if arcs_stage("kilo", self._contact_trust("kilo")) >= 1 else 2
        if self.deck.cpu_cycles < cost:
            return False, f"Insufficient CPU cycles (need {cost} CPU for overdrive)."
        if self.state.trace_percent >= 92:
            return False, "Cannot overdrive: trace is too high to risk another surge."

        self.deck.cpu_cycles -= cost
        self.state.combo_streak += 1
        self.state.best_combo = max(self.state.best_combo, self.state.combo_streak)
        self.state.unbanked_creds += 10
        self.add_trace(8)
        msg = (
            f"⚡ NEURAL OVERDRIVE! Combo x{self.state.combo_streak} primed "
            f"(+10 Creds, Trace +8% -> {self.state.trace_percent}%)."
        )
        if cost == 1:
            msg += " [KILO ARC: discounted burn]"
        self.state.message_log.append(msg)
        return True, msg

    def scan_surroundings(self) -> Tuple[bool, str, List[Node]]:
        """Scan adjacent nodes to reveal their security level and status."""
        if self.state.is_game_over:
            return False, "Cannot scan: system lockout in effect.", []
        if self.state.is_jacked_out:
            return False, "Cannot scan: terminal session jacked out.", []
        if self.state.is_victory:
            return False, "Cannot scan: mission already complete.", []
        current = self.get_current_node()
        revealed: List[Node] = []
        for adj_id in current.connected_ids:
            node = self.nodes.get(adj_id)
            if node:
                if node.status == NodeStatus.LOCKED:
                    node.status = NodeStatus.DISCOVERED
                revealed.append(node)

        self.state.scanned = True
        self.add_trace(5)
        self.regenerate_cpu(1)
        self.advance_turn()
        msg = f"Scanned {len(revealed)} adjacent network nodes. Recovered 1 CPU cycle."
        if self.state.is_game_over:
            msg += " The grid burned your deck during the sweep."
        return True, msg, revealed

    def can_move_to(self, target_id: str) -> Tuple[bool, str]:
        """Verify whether the player can transition to target node."""
        if self.state.is_game_over:
            return False, "Cannot move: system lockout in effect."
        if self.state.is_jacked_out:
            return False, "Cannot move: terminal session jacked out."
        if self.state.is_victory:
            return False, "Cannot move: mission already complete."
        if target_id not in self.nodes:
            return False, f"Unknown node: {target_id}"

        current = self.get_current_node()
        if target_id not in current.connected_ids:
            return False, f"Node '{target_id}' is not directly connected to '{current.node_id}'."

        target = self.nodes[target_id]
        if target.status != NodeStatus.BREACHED:
            return False, f"Node '{target.name}' is unbreached ({target.status}). Breach security first."

        return True, "Path clear."

    def move_to(self, target_id: str) -> Tuple[bool, str]:
        """Move player's intrusion session to an adjacent breached node."""
        allowed, reason = self.can_move_to(target_id)
        if not allowed:
            return False, reason

        origin = self.get_current_node()
        self.state.current_node_id = target_id
        self.regenerate_cpu(1)
        self.add_trace(2)
        self.advance_turn()
        node = self.get_current_node()
        msg = f"⚡ Transferred terminal session to '{node.name}'. Recovered 1 CPU cycle."
        from_hood = self.host_district(origin.node_id)
        to_hood = self.host_district(node.node_id)
        if from_hood["district_key"] != to_hood["district_key"]:
            msg += f" 🌆 Crossing into {to_hood['district']} grid ({to_hood['flavor']})."
        if self.state.is_game_over:
            msg += " The grid burned your deck on arrival."
        self.state.message_log.append(msg)
        return True, msg

    def can_hack_node(self, target_id: str) -> Tuple[bool, str]:
        """Verify whether player cyberdeck meets hardware requirements to attack node."""
        if self.state.is_game_over:
            return False, "Cannot hack: system lockout in effect."
        if self.state.is_jacked_out:
            return False, "Cannot hack: terminal session jacked out."
        if self.state.is_victory:
            return False, "Cannot hack: mission already complete."
        if target_id not in self.nodes:
            return False, f"Unknown node '{target_id}'."

        node = self.nodes[target_id]
        if node.status == NodeStatus.BREACHED:
            return False, f"Node '{node.name}' is already breached."
        gate = self._story_gate_reason(node)
        if gate:
            return False, gate

        lockdown = self._lockdown_reason(node)
        if lockdown:
            return False, lockdown

        curr = self.get_current_node()
        if target_id not in curr.connected_ids and target_id != curr.node_id:
            return False, f"Node '{node.name}' is not in direct subnet range of '{curr.name}'."

        required_ram = node.security_level * 16
        if self.deck.ram_mb < required_ram:
            return False, f"INSUFFICIENT RAM: Infiltration requires {required_ram}MB buffer memory (deck has {self.deck.ram_mb}MB). Upgrade RAM in the Black Market shop."

        return True, "Requirements met."

    def _contract_rng(self) -> random.Random:
        """Dedicated contract stream so contract generation never shifts reward rolls."""
        self.state.contract_seq += 1
        return world_rng(self.seed, self.state.turns_elapsed, f"contract:{self.state.contract_seq}")

    def _contract_giver(self, objective: str, risk: str) -> str:
        """Pick the operative whose trust and voice fit the job."""
        if risk == "black":
            zero = self._find_contact("zero")
            if zero and zero.unlock_act <= self.state.story_act:
                return "zero"
        if objective in ("extract", "wipe"):
            archivist = self._find_contact("archivist")
            if archivist and archivist.unlock_act <= self.state.story_act:
                return "archivist"
        return "mira"

    def _contract_candidates(self, objective: str) -> List[Node]:
        """Return hosts that can still satisfy a fresh job for this objective."""
        core_allowed = self.state.story_act >= 4
        nodes = [
            node
            for node in self.nodes.values()
            if node.node_type != NodeType.GATEWAY
            and (node.node_type != NodeType.CENTRAL_CORE or core_allowed)
        ]
        if objective == "breach":
            return [node for node in nodes if node.status != NodeStatus.BREACHED]
        if objective == "extract":
            return [
                node
                for node in nodes
                if any(
                    vfile.is_target_data
                    and vfile.value_creds > 0
                    and vfile.path not in self.state.looted_payloads
                    for vfile in node.filesystem
                )
            ]
        if objective == "wipe":
            return [node for node in nodes if not node.logs_cleared]
        if objective == "recon":
            return [
                node
                for node in nodes
                if node.status in (NodeStatus.DISCOVERED, NodeStatus.BREACHED)
            ]
        return []

    def _choose_contract_risk(self, rng: random.Random) -> str:
        roll = rng.random()
        if self.state.world.alert_level >= 55 or self.state.story_act >= 3:
            if roll < 0.18:
                return "black"
            if roll < 0.55:
                return "priority"
            return "standard"
        return "priority" if roll < 0.35 else "standard"

    def _contract_deadline(self, objective: str, node: Node, risk: str, trust: int, rng: random.Random) -> Tuple[int, int]:
        duration = 18 + (4 if objective in ("extract", "wipe") else (-4 if objective == "recon" else 0))
        duration += node.security_level * 2
        duration += int(CONTRACT_RISK[risk]["duration_delta"])
        duration += min(3, max(0, trust) // 2)
        duration += rng.randint(-2, 2)
        duration = max(8, duration)
        return duration, max(4, duration // 2)

    def _activate_contract(self, contract: BountyContract) -> BountyContract:
        """Start an accepted job's clock and clear its board shelf life."""
        if contract.deadline_turns:
            contract.expires_turn = self.state.turns_elapsed + contract.deadline_turns
            contract.rush_turn = self.state.turns_elapsed + max(4, contract.deadline_turns // 2)
            # Mira's arc (trust 2+): her desk holds the rush window one turn longer.
            if (getattr(contract, "giver", "") == "mira"
                    and arcs_stage("mira", self._contact_trust("mira")) >= 1):
                contract.rush_turn += 1
        contract.offer_expires_turn = 0
        contract.failed = False
        return contract

    def _offer_signature(self, contract: BountyContract) -> Tuple[str, str, str]:
        return (contract.objective_kind, contract.target_ip or "", contract.target_file or "")

    def reroll_contract_offers(self, cost: int = 50) -> Tuple[bool, str]:
        """Spend credits to replace the posted board with fresh offers."""
        if self.state.is_game_over:
            return False, "Cannot reroll: system lockout in effect."
        if self.state.is_jacked_out:
            return False, "Cannot reroll: terminal session jacked out."
        if self.state.is_victory:
            return False, "Cannot reroll: mission already complete."
        if self.deck.cryptocreds < cost:
            return False, f"Reroll needs {cost} CryptoCreds (have {self.deck.cryptocreds})."

        previous = list(self.state.contract_offers)
        self.state.contract_offers = []
        added = self._refresh_contract_offers()
        if not added:
            self.state.contract_offers = previous
            return False, "No fresh contract candidates are available on this grid."
        self.deck.cryptocreds -= cost
        message = f"Rerolled the Syndicate board for {cost} CR; {len(added)} fresh offer(s) posted."
        self.state.message_log.append(message)
        return True, message

    def _contract_board_size(self) -> int:
        """Offer slots: the Archive's arc (trust 2+) opens one extra slot."""
        bonus = 1 if arcs_stage("archivist", self._contact_trust("archivist")) >= 1 else 0
        return CONTRACT_BOARD_SIZE + bonus

    def _refresh_contract_offers(
        self, exclude_signatures: Optional[Set[Tuple[str, str, str]]] = None
    ) -> List[BountyContract]:
        """Expire stale board entries and fill the board with distinct concrete jobs."""
        now = self.state.turns_elapsed
        self.state.contract_offers = [
            offer
            for offer in self.state.contract_offers
            if not offer.offer_expires_turn or offer.offer_expires_turn > now
        ]
        signatures = {self._offer_signature(offer) for offer in self.state.contract_offers}
        if exclude_signatures:
            signatures.update(exclude_signatures)
        active = self.state.active_contract
        if active and not active.completed and not active.failed:
            signatures.add(self._offer_signature(active))

        added: List[BountyContract] = []
        attempts = 0
        board_size = self._contract_board_size()
        while len(self.state.contract_offers) < board_size and attempts < 24 + board_size:
            attempts += 1
            offer = self._build_contract()
            if offer is None:
                break
            signature = self._offer_signature(offer)
            if signature in signatures:
                continue
            self.state.contract_offers.append(offer)
            signatures.add(signature)
            added.append(offer)
        return added

    def _build_contract(self) -> Optional[BountyContract]:
        """Generate a concrete, deadline-bound job from the live grid state."""
        rng = self._contract_rng()
        feasible = [objective for objective in ("breach", "extract", "wipe") if self._contract_candidates(objective)]
        if not feasible and self._contract_candidates("recon"):
            feasible = ["recon"]
        if not feasible:
            return None

        objective = rng.choices(
            feasible,
            weights=[3 if name == "breach" else 4 for name in feasible],
            k=1,
        )[0]
        candidates = sorted(self._contract_candidates(objective), key=lambda node: node.node_id)
        node = rng.choice(candidates)
        risk = self._choose_contract_risk(rng)
        giver = self._contract_giver(objective, risk)
        contact = self._find_contact(giver)
        trust = contact.trust if contact else 0
        deadline_turns, _rush_offset = self._contract_deadline(objective, node, risk, trust, rng)
        offer_expires_turn = self.state.turns_elapsed + int(CONTRACT_RISK[risk]["offer_ttl"])

        base_reward = CONTRACT_BASE_REWARD[objective] + node.security_level * 20
        reward = int(round(base_reward * CONTRACT_RISK[risk]["reward"]))
        bonus = int(round(reward * CONTRACT_RISK[risk]["rush"]))
        max_trace = int(CONTRACT_RISK[risk]["max_trace"])

        target_file = None
        wipe_required = False
        if objective == "extract":
            files = sorted(
                (
                    vfile
                    for vfile in node.filesystem
                    if vfile.is_target_data
                    and vfile.value_creds > 0
                    and vfile.path not in self.state.looted_payloads
                ),
                key=lambda vfile: vfile.path,
            )
            target_file = rng.choice(files).path
        elif objective == "wipe":
            wipe_required = True
            unlooted = sorted(
                (
                    vfile
                    for vfile in node.filesystem
                    if vfile.is_target_data
                    and vfile.value_creds > 0
                    and vfile.path not in self.state.looted_payloads
                ),
                key=lambda vfile: vfile.path,
            )
            if unlooted and rng.random() < 0.5:
                target_file = rng.choice(unlooted).path

        if objective == "breach":
            title = f"Syndicate Breach Order: {node.hostname}"
            description = f"Infiltrate {node.hostname} ({node.ip_address}) and plant the Syndicate rootkit."
        elif objective == "extract":
            title = f"Data Extraction: {str(target_file).split('/')[-1]}"
            description = f"Infiltrate {node.hostname} ({node.ip_address}) and extract {target_file}."
        elif objective == "recon":
            title = f"Recon Sweep: {node.hostname}"
            description = (
                f"Probe {node.hostname} ({node.ip_address}) and confirm its listening services for the Syndicate."
            )
        else:
            title = f"Sanitize Contract: {node.hostname}"
            if target_file:
                description = (
                    f"Steal {target_file} from {node.hostname} ({node.ip_address}) and wipe its "
                    "access logs before the Syndicate window closes."
                )
            else:
                description = (
                    f"Infiltrate {node.hostname} ({node.ip_address}) and wipe its access logs "
                    "before the Syndicate window closes."
                )

        contract = BountyContract(
            contract_id=f"cnt_{self.state.turns_elapsed:03d}_{self.state.contract_seq:04d}",
            title=title,
            target_node_type=node.node_type,
            target_ip=node.ip_address,
            target_file=target_file,
            wipe_logs_required=wipe_required,
            max_trace_limit=max_trace,
            reward_creds=reward,
            giver=giver,
            risk_tier=risk,
            objective=objective,
            expires_turn=0,
            rush_turn=0,
            bonus_creds=bonus,
            deadline_turns=deadline_turns,
            offer_expires_turn=offer_expires_turn,
            description=description,
        )
        return contract

    def dispatch_next_contract(self) -> Optional[BountyContract]:
        """Dispatch and immediately accept a concrete job (legacy/test helper)."""
        new_contract = self._build_contract()
        if new_contract:
            self._activate_contract(new_contract)
        self.state.active_contract = new_contract
        if new_contract:
            self._log_story(
                f"NEW SYNDICATE CONTRACT: {new_contract.title} "
                f"({new_contract.risk_tier.upper()} risk, deadline turn {new_contract.expires_turn})."
            )
        return new_contract

    def accept_contract(self, contract_id: str) -> Tuple[bool, str]:
        """Accept a posted offer and start its deadline clock."""
        if self.state.is_game_over:
            return False, "Cannot accept a contract: system lockout in effect."
        if self.state.is_jacked_out:
            return False, "Cannot accept a contract: terminal session jacked out."
        if self.state.is_victory:
            return False, "Cannot accept a contract: mission already complete."
        active = self.state.active_contract
        if active and not active.completed and not active.failed:
            return False, (
                f"You already have an active contract ({active.title}). Complete it or run "
                "`decline_contract` before accepting another."
            )
        if self.state.turns_elapsed < self.state.contract_decline_until_turn:
            return False, "The broker needs one grid turn to repost terms after a decline."
        offer = next(
            (candidate for candidate in self.state.contract_offers if candidate.contract_id == contract_id),
            None,
        )
        if offer is None:
            self._refresh_contract_offers()
            return False, f"No posted contract offer with id '{contract_id}'."
        if offer.offer_expires_turn and offer.offer_expires_turn <= self.state.turns_elapsed:
            self._refresh_contract_offers()
            return False, f"Offer '{offer.title}' expired before it was accepted."
        self.state.contract_offers.remove(offer)
        self.state.active_contract = self._activate_contract(offer)
        self.state.contract_decline_until_turn = 0
        self.state.contract_notice = ""
        message = (
            f"JOB ACCEPTED: {offer.title} — deadline turn {offer.expires_turn} "
            f"(rush by turn {offer.rush_turn})."
        )
        self._refresh_contract_offers()
        self.state.message_log.append(message)
        return True, message

    def drop_offer(self, contract_id: str) -> Tuple[bool, str]:
        """Remove one posted offer: pay the broker fee, or take a one-turn cooldown if broke."""
        if self.state.is_game_over or self.state.is_jacked_out or self.state.is_victory:
            return False, "Cannot drop an offer: the run has already ended."
        offer = next(
            (candidate for candidate in self.state.contract_offers if candidate.contract_id == contract_id),
            None,
        )
        if offer is None:
            self._refresh_contract_offers()
            return False, f"No posted contract offer with id '{contract_id}'."
        if self.deck.cryptocreds >= OFFER_DROP_FEE:
            self.deck.cryptocreds -= OFFER_DROP_FEE
            broker_note = f"Broker fee -{OFFER_DROP_FEE} CR."
        else:
            if self.state.turns_elapsed < self.state.contract_decline_until_turn:
                return False, "The broker is still reposting terms; wait one grid turn."
            self.state.contract_decline_until_turn = self.state.turns_elapsed + 1
            broker_note = "Broker waives the fee; terms repost next turn."
        self.state.contract_offers.remove(offer)
        self._refresh_contract_offers({self._offer_signature(offer)})
        self.state.contract_notice = ""
        message = (
            f"OFFER DROPPED: {offer.title}. {broker_note} The board is refreshed."
        )
        self.state.message_log.append(message)
        return True, message

    def decline_contract(self) -> Tuple[bool, str]:
        """Walk away from the active job: lose giver trust, keep the board stocked."""
        if self.state.is_game_over or self.state.is_jacked_out or self.state.is_victory:
            return False, "Cannot decline a contract: the run has already ended."
        contract = self.state.active_contract
        if contract is None or contract.completed or contract.failed:
            return False, "There is no active contract to decline."
        contract.failed = True
        contact = self._find_contact(contract.giver)
        if contact:
            # Mira's arc (trust 4+): the Fixer's Confidant covers walk-aways.
            if (contact.contact_id == "mira"
                    and arcs_stage("mira", int(contact.trust)) >= 2):
                message_cover = (
                    f"CONTRACT DECLINED: {contract.title}. "
                    "Mira covers the walk-away: no trust lost; the board is refreshed."
                )
                self.state.active_contract = None
                self.state.contract_decline_until_turn = self.state.turns_elapsed + 1
                self._refresh_contract_offers()
                self.state.contract_notice = ""
                self.state.message_log.append(message_cover)
                return True, message_cover
            self._adjust_trust(contact, -1)
        self.state.active_contract = None
        self.state.contract_decline_until_turn = self.state.turns_elapsed + 1
        self._refresh_contract_offers()
        self.state.contract_notice = ""
        message = (
            f"CONTRACT DECLINED: {contract.title}. "
            f"{contact.name if contact else 'The Syndicate'} trust -1; the board is refreshed."
        )
        self.state.message_log.append(message)
        return True, message

    def _contract_targets_node(self, contract: BountyContract, node: Node) -> bool:
        if contract.target_ip and contract.target_ip != node.ip_address:
            return False
        return node.node_type == contract.target_node_type

    def _contract_completes_on_breach(self, contract: BountyContract, node: Node) -> bool:
        """Return True when a node breach satisfies a contract without extra objectives."""
        if contract.completed or contract.failed:
            return False
        if contract.objective_kind != "breach" or not self._contract_targets_node(contract, node):
            return False
        return self.state.trace_percent <= contract.max_trace_limit

    def _contract_download_matches(self, contract: BountyContract, node: Node, vfile: VirtualFile) -> bool:
        """Return True when this download advances the active contract."""
        if contract.completed:
            return False
        if contract.target_ip and contract.target_ip != node.ip_address:
            return False
        kind = contract.objective_kind
        if kind == "extract":
            if contract.target_file:
                return contract.target_file == vfile.path
            return bool(contract.target_ip) and contract.target_ip == node.ip_address
        if kind == "wipe":
            return bool(contract.target_file) and contract.target_file == vfile.path
        # Legacy generic sector bounties may be cleared by extracting from a matching host.
        return (
            not contract.target_file
            and not contract.target_ip
            and node.node_type == contract.target_node_type
        )

    def _contract_recon_matches(self, contract: BountyContract, node: Node) -> bool:
        return contract.objective_kind == "recon" and self._contract_targets_node(contract, node)

    def _contract_wipe_ready(self, contract: BountyContract, node: Node) -> bool:
        if contract.completed or contract.objective_kind != "wipe":
            return False
        if contract.target_ip and contract.target_ip != node.ip_address:
            return False
        return not contract.target_file or contract.target_file in self.state.looted_payloads

    def _contract_payout(self, contract: BountyContract) -> Tuple[int, int, int]:
        """Return (total, trust_bonus, rush_bonus) for a completed job."""
        contact = self._find_contact(contract.giver)
        trust = max(0, contact.trust) if contact else 0
        trust_bonus = int(round(contract.reward_creds * min(0.25, 0.05 * trust)))
        rush_bonus = (
            contract.bonus_creds
            if contract.rush_turn and self.state.turns_elapsed <= contract.rush_turn
            else 0
        )
        modifier = modifier_by_id(self.daily_modifier)
        daily_factor = modifier.contract_multiplier if modifier else 1.0
        total = int(round(
            (contract.reward_creds + trust_bonus + rush_bonus)
            * contract_multiplier(self.difficulty)
            * daily_factor
            * (1.0 + self.contract_standing_bonus + self.allegiance_contract_bonus)
        ))
        return total, trust_bonus, rush_bonus

    def _finalize_contract(self, contract: BountyContract, node: Node) -> str:
        """Pay a completed job once, reward its giver's trust, and dispatch the next job."""
        if contract.completed or contract.failed:
            return ""
        total, trust_bonus, rush_bonus = self._contract_payout(contract)
        contract.completed = True
        self.state.contract_notice = ""
        self.state.unbanked_creds += total
        contact = self._find_contact(contract.giver)
        arc_line = self._adjust_trust(contact, 1) if contact else None

        payout_bits = [f"+{total} Creds"]
        if trust_bonus:
            payout_bits.append(f"trust bonus +{trust_bonus}")
        if rush_bonus:
            payout_bits.append(f"RUSH BONUS +{rush_bonus}")
        message = f"🏆 SYNDICATE CONTRACT COMPLETED on {node.hostname}! {', '.join(payout_bits)}."
        if arc_line:
            message += f"\n{arc_line}"
        record_news(
            self.state.world,
            self.state.turns_elapsed,
            "Syndicate",
            f"Syndicate bounty cleared on {node.hostname}; payment released.",
            tone="positive",
        )
        self.state.active_contract = None
        self._refresh_contract_offers()
        if self.state.contract_offers:
            message += " Job board refreshed; choose the next contract."
        else:
            message += " No fresh offers remain; wait for the grid to re-secure a host."
        self.state.message_log.append(message)
        return message

    def _fail_contract(self, contract: BountyContract) -> List[str]:
        """Expire a job, cost its giver trust, raise heat, and post the next contract."""
        contract.failed = True
        contact = self._find_contact(contract.giver)
        if contact:
            self._adjust_trust(contact, -1)
        adjust_alert(self.state.world, 3)
        message = (
            f"⏳ CONTRACT EXPIRED: {contract.title} missed its turn {contract.expires_turn} "
            f"deadline. {contact.name if contact else 'The Syndicate'} loses trust (-1) and the "
            "grid alert rises (+3%)."
        )
        record_news(
            self.state.world,
            self.state.turns_elapsed,
            "Syndicate",
            "A contracted runner missed a deadline; the Syndicate is displeased.",
            tone="negative",
        )
        self.state.active_contract = None
        message += " New offers pending on the next grid tick."
        self.state.contract_notice = message
        self.state.message_log.append(message)
        return [message]

    def _check_contract_clock(self) -> List[str]:
        """Warn near a deadline, expire a missed job, and rotate the offer board."""
        messages: List[str] = []
        self._refresh_contract_offers()
        contract = self.state.active_contract
        if contract and not contract.completed and not contract.failed and contract.expires_turn:
            remaining = contract.expires_turn - self.state.turns_elapsed
            if remaining <= 0:
                return self._fail_contract(contract)
            if remaining in (5, 2):
                rush = ""
                if contract.rush_turn and self.state.turns_elapsed <= contract.rush_turn:
                    rush = f" Rush bonus still live until turn {contract.rush_turn}."
                warning = (
                    f"⏳ CONTRACT CLOCK: {remaining} turn(s) left on {contract.title} "
                    f"(deadline turn {contract.expires_turn}).{rush}"
                )
                self.state.contract_notice = warning
                self.state.message_log.append(warning)
                messages.append(warning)

        if self.state.active_contract is None and self.state.contract_offers:
            previous_notice = self.state.contract_notice
            if "CONTRACT EXPIRED" in previous_notice and "job offer(s)" not in previous_notice:
                message = (
                    f"{previous_notice} {len(self.state.contract_offers)} job offer(s) are now "
                    "on the board; accept one with accept_job <id>."
                )
                self.state.contract_notice = message
                self.state.message_log.append(message)
                messages.append(message)
        return messages

    def complete_breach(self, node_id: str) -> Tuple[bool, str]:
        """Mark node as breached, evaluate variable-ratio rewards, and check contracts."""
        if self.state.is_game_over:
            return False, "Cannot breach: system lockout in effect."
        if self.state.is_jacked_out:
            return False, "Cannot breach: terminal session jacked out."
        if self.state.is_victory:
            return False, "Cannot breach: mission already complete."
        if node_id not in self.nodes:
            return False, f"Invalid node '{node_id}'."

        node = self.nodes[node_id]
        if node.status == NodeStatus.BREACHED:
            return False, f"Node '{node.name}' is already breached."
        gate = self._story_gate_reason(node)
        if gate:
            return False, gate

        node.status = NodeStatus.BREACHED
        node.breached_turn = self.state.turns_elapsed
        self.clear_pending_puzzle(node_id)

        # Variable-ratio reward roll (Skinner reinforcement schedule). A host the grid
        # re-secured has no fresh data, so re-breaching it pays nothing and cannot farm.
        fresh_data = not node.reward_claimed
        combo_bonus = 0
        if fresh_data:
            creds_awarded, reward_desc, exploit_drop = roll_breach_reward(node, self.rng)
            self.state.combo_streak += 1
            self.state.best_combo = max(self.state.best_combo, self.state.combo_streak)
            combo_rate = min(0.50, 0.10 * self.state.combo_streak)
            combo_bonus = int(creds_awarded * combo_rate)
            self.state.unbanked_creds += creds_awarded + combo_bonus
            node.reward_claimed = True
            if exploit_drop and exploit_drop not in self.deck.exploits:
                self.deck.exploits.append(exploit_drop)
        else:
            reward_desc = "No fresh data: the host was re-secured and its vaults wiped."

        msg = f"💥 Infiltration successful! '{node.name}' breached. {reward_desc}"
        stance = getattr(self.deck, "operating_stance", OperatingStance.BALANCED)
        if fresh_data and stance == OperatingStance.OVERCLOCK:
            overclock_bonus = max(1, int(creds_awarded * 0.25))
            self.state.unbanked_creds += overclock_bonus
            msg += f" ⚡ OVERCLOCK HARVEST: +{overclock_bonus} bonus Creds!"
        elif fresh_data and stance == OperatingStance.ANALYSIS:
            gained = 1 + (1 if self.rng.random() < 0.35 else 0)
            self.deck.threat_intel_count += gained
            msg += (
                f" 🔍 THREAT INTEL: {gained} fragment(s) recovered "
                f"(Total: {self.deck.threat_intel_count})."
            )

        if combo_bonus:
            msg += f" 🔥 COMBO x{self.state.combo_streak}: +{combo_bonus} bonus Creds!"

        if node.data_payload and node.data_payload not in self.state.looted_payloads:
            self.state.looted_payloads.append(node.data_payload)
            msg += f" Acquired: [{node.data_payload}]."

        # Loud intrusions raise the living grid's alert level and make the news feed
        adjust_alert(self.state.world, 3 + node.security_level * 2)
        hood = self.host_district(node.node_id)
        if hood["patrol"] == "heavy":
            self.add_trace(1)
            msg += f"\n🌆 DISTRICT HEAT: {hood['district']} patrols are crawling (+1% trace)."
        record_news(
            self.state.world,
            self.state.turns_elapsed,
            "NetWatch",
            f"Breach detected on {node.hostname} ({node.ip_address}); corporate response mobilizing.",
            tone="alert",
        )

        # Syndicate Contract Check (Zeigarnik Effect)
        contract = self.state.active_contract
        if contract and self._contract_completes_on_breach(contract, node):
            msg += "\n" + self._finalize_contract(contract, node)
        elif (
            contract
            and not contract.completed
            and contract.objective_kind == "breach"
            and self._contract_targets_node(contract, node)
            and self.state.trace_percent > contract.max_trace_limit
        ):
            msg += (
                f"\n⚠️ CONTRACT TRACE LIMIT EXCEEDED: {self.state.trace_percent}% > "
                f"{contract.max_trace_limit}%. The breach is real but the bounty is not "
                "confirmed; cool trace and re-breach after the grid re-secures the host."
            )

        # Story quest progress: only a first, data-bearing breach counts; a re-secured
        # host must not be farmable for quest credit.
        if fresh_data:
            for line in self._progress_quests("breach_type", node.node_type):
                msg += f"\n{line}"

        # Unlock adjacent nodes to DISCOVERED
        for adj_id in node.connected_ids:
            adj = self.nodes.get(adj_id)
            if adj and adj.status == NodeStatus.LOCKED:
                adj.status = NodeStatus.DISCOVERED

        if node.node_type == NodeType.CENTRAL_CORE:
            self.state.is_victory = True
            msg += " 🏆 CORE INFILTRATED! MISSION ACCOMPLISHED!"
            record_news(
                self.state.world,
                self.state.turns_elapsed,
                "OmniCorp PR",
                "NEXUS supercore offline: OmniCorp declares a city-wide systems emergency.",
                tone="negative",
            )

        self.state.message_log.append(msg)
        return True, msg

    def use_exploit(self, exploit_name: str, target_id: Optional[str] = None) -> Tuple[bool, str]:
        """Deploy an executable exploit chip loaded in cyberdeck firmware."""
        if self.state.is_game_over:
            return False, "Cannot use exploit: system lockout in effect."
        if self.state.is_jacked_out:
            return False, "Cannot use exploit: terminal session jacked out."
        if self.state.is_victory:
            return False, "Cannot use exploit: mission already complete."

        name = str(exploit_name or "").lower().strip()
        if not name:
            return False, "No exploit name specified."
        if name not in self.deck.exploits:
            return False, f"Exploit '{name}' is not loaded in cyberdeck firmware."

        if name == "ghost_protocol":
            reduced = min(self.state.trace_percent, 40)
            self.state.trace_percent = max(0, self.state.trace_percent - 40)
            self.scramble_hunter_radar(turns=4)
            self.deck.exploits.remove(name)
            msg = f"👻 GHOST PROTOCOL DEPLOYED! Neural signature masked. Trace dropped by {reduced}% (current: {self.state.trace_percent}%)."
            self.state.message_log.append(msg)
            return True, msg

        if name == "logic_bomb":
            if target_id and target_id.lower() in ("hunter", "aegis", "netwatch"):
                return self.counter_hunter(method="logic_bomb")
            if not target_id:
                return False, "Usage: exploit logic_bomb <node_id | hunter>"
            if target_id not in self.nodes:
                return False, f"Unknown node '{target_id}'."
            target = self.nodes[target_id]
            if target.status == NodeStatus.BREACHED:
                return False, f"Node '{target.name}' is already breached."
            curr = self.get_current_node()
            if target_id not in curr.connected_ids and target_id != curr.node_id:
                return False, f"Target '{target.name}' is not in direct subnet range of '{curr.name}'."

            breached, breach_msg = self.complete_breach(target_id)
            if not breached:
                return False, breach_msg
            self.deck.exploits.remove(name)
            msg = f"💣 LOGIC BOMB DETONATED! Destroyed ICE defenses on '{target.name}'. {breach_msg}"
            return True, msg

        if name == "port_scan":
            target = self.find_node(target_id or self.state.current_node_id)
            if not target:
                return False, f"Target '{target_id}' not found."
            curr = self.get_current_node()
            if target.node_id not in curr.connected_ids and target.node_id != curr.node_id:
                return False, f"Target '{target.hostname}' is not in direct subnet range."
            if target.status == NodeStatus.BREACHED:
                return False, f"Node '{target.name}' is already breached."
            if target.status == NodeStatus.LOCKED:
                target.status = NodeStatus.DISCOVERED
            self._mark_probed(target.node_id)
            self.deck.exploits.remove(name)
            services = ", ".join(f"{p.port}/{p.service}" for p in target.ports) or "none"
            msg = (
                f"PORT SCAN CHIP BURNED: mapped {target.hostname} ({target.ip_address}) with no trace. "
                f"Services [{services}]."
            )
            self.state.message_log.append(msg)
            return True, msg

        if name == "buffer_overflow":
            if not target_id:
                return False, "Usage: exploit buffer_overflow <node_id>"
            node = self.find_node(target_id)
            if not node:
                return False, f"Target '{target_id}' not found."
            if node.status == NodeStatus.BREACHED:
                return False, f"Node '{node.name}' is already breached."
            gate = self._story_gate_reason(node)
            if gate:
                return False, gate
            curr = self.get_current_node()
            if node.node_id not in curr.connected_ids and node.node_id != curr.node_id:
                return False, f"Target '{node.hostname}' is not in direct subnet range."
            self.add_trace(12)
            if self.state.is_game_over:
                fail_msg = "BUFFER OVERFLOW DETONATED: the grid severed the link before the payload landed."
                self.state.message_log.append(fail_msg)
                return False, fail_msg
            breached, breach_msg = self.complete_breach(node.node_id)
            if not breached:
                return False, breach_msg
            self.deck.exploits.remove(name)
            msg = (
                f"BUFFER OVERFLOW CHIP BURNED: {node.hostname} fell to a register smash "
                f"(+12% trace). {breach_msg}"
            )
            self.state.message_log.append(msg)
            return True, msg

        if name == "spoof_ip":
            if self.state.trace_percent <= 0:
                return False, "Trace is already at 0%; hold the spoof_ip chip."
            reduced = min(self.state.trace_percent, 30)
            self.state.trace_percent = max(0, self.state.trace_percent - 30)
            self.deck.exploits.remove(name)
            msg = (
                f"SPOOF_IP CHIP BURNED: bounced the connection and shed {reduced}% trace "
                f"(current: {self.state.trace_percent}%)."
            )
            self.state.message_log.append(msg)
            return True, msg

        if name == "zero_day_forge":
            if not target_id:
                return False, "Usage: exploit zero_day_forge <node_id>"
            if target_id.lower() in ("hunter", "aegis", "netwatch"):
                return False, "Zero-day forge cannot be spent on a hunter."
            if target_id not in self.nodes:
                return False, f"Unknown node '{target_id}'."
            target = self.nodes[target_id]
            if target.status == NodeStatus.BREACHED:
                return False, f"Node '{target.name}' is already breached."
            curr = self.get_current_node()
            if target_id not in curr.connected_ids and target_id != curr.node_id:
                return False, f"Target '{target.name}' is not in direct subnet range of '{curr.name}'."
            gate = self._story_gate_reason(target)
            if gate:
                return False, gate
            breach_cost = min(15, target.security_level * 3)
            self.add_trace(breach_cost)
            if self.state.is_game_over:
                fail_msg = "💀 FORGED ZERO-DAY BURNED: the grid severed the link before it landed."
                self.state.message_log.append(fail_msg)
                return False, fail_msg
            breached, breach_msg = self.complete_breach(target_id)
            if not breached:
                return False, breach_msg
            self.deck.exploits.remove(name)
            msg = (
                f"🧠 FORGED ZERO-DAY DEPLOYED: {target.name} fell without a mini-game "
                f"(+{breach_cost}% trace). {breach_msg}"
            )
            self.state.message_log.append(msg)
            return True, msg

        if name == "brute_miner":
            curr = self.get_current_node()
            if curr.status != NodeStatus.BREACHED:
                return False, "Brute miner can only be executed on a securely breached node."
            mined = 150
            self.deck.exploits.remove(name)
            self.add_trace(15)
            if self.state.is_game_over:
                fail_msg = "💀 BRUTE MINER DETONATED: Black ICE burned the deck before the mined payload could settle."
                self.state.message_log.append(fail_msg)
                return False, fail_msg
            self.state.unbanked_creds += mined
            msg = f"⛏️ BRUTE MINER EXECUTED! Mined +{mined} unbanked CryptoCreds (Trace +15% -> {self.state.trace_percent}%)."
            self.state.message_log.append(msg)
            return True, msg

        if name == "trace_cleaner":
            reduced = min(self.state.trace_percent, 35)
            self.state.trace_percent = max(0, self.state.trace_percent - 35)
            self.deck.exploits.remove(name)
            msg = f"🧹 TRACE CLEANER EXECUTED! Scrubbed active forensic footprint by {reduced}% (current: {self.state.trace_percent}%)."
            self.state.message_log.append(msg)
            return True, msg

        if name == "data_siphon":
            target = target_id or self.state.current_node_id
            node = self.find_node(target)
            if not node:
                return False, f"Target '{target}' not found."
            if node.status != NodeStatus.BREACHED:
                return False, f"Data siphon requires host {node.hostname} to be securely breached."
            siphoned = 150
            self.deck.exploits.remove(name)
            self.add_trace(10)
            if self.state.is_game_over:
                fail_msg = f"💀 DATA SIPHON DETONATED: Black ICE burned the deck before the siphon from {node.hostname} could settle."
                self.state.message_log.append(fail_msg)
                return False, fail_msg
            self.state.unbanked_creds += siphoned
            msg = f"⚡ DATA SIPHON EXECUTED! Drained +{siphoned} unbanked Creds from {node.hostname} (Trace +10% -> {self.state.trace_percent}%)."
            self.state.message_log.append(msg)
            return True, msg

        if name == "worm_replicator":
            if not target_id:
                return False, "Usage: exploit worm_replicator <target_ip | node_id>"
            node = self.find_node(target_id)
            if not node:
                return False, f"Target '{target_id}' not found."
            if node.status == NodeStatus.BREACHED:
                return False, f"Node '{node.name}' is already breached."
            curr = self.get_current_node()
            if node.node_id not in curr.connected_ids and node.node_id != curr.node_id:
                return False, f"Target '{node.hostname}' is not in direct subnet range."
            breached, breach_msg = self.complete_breach(node.node_id)
            if not breached:
                return False, breach_msg
            self.deck.exploits.remove(name)
            for adj_id in node.connected_ids:
                adj = self.nodes.get(adj_id)
                if adj and adj.status == NodeStatus.LOCKED:
                    adj.status = NodeStatus.DISCOVERED
            msg = f"🐛 WORM REPLICATOR PROPAGATED! Infiltrated {node.hostname} and forced network disclosure of connected subnets!\n{breach_msg}"
            self.state.message_log.append(msg)
            return True, msg

        if name == "keylogger_daemon":
            target = target_id or self.state.current_node_id
            ok, d_msg = self.deploy_daemon(target, "keylogger")
            if ok:
                self.deck.exploits.remove(name)
            return ok, d_msg

        return False, f"Exploit '{name}' has no active payload handler."

    def jackout(self) -> Tuple[bool, str]:
        """Push-Your-Luck extraction: safely bank all unbanked credits and looted payloads."""
        if self.state.is_game_over:
            return False, "Cannot jack out: terminal already locked out."
        if self.state.is_jacked_out:
            return False, "Already jacked out."
        if self.state.is_victory:
            return False, "Mission already complete; extraction is automatic."

        curr = self.get_current_node()
        if curr.status != NodeStatus.BREACHED:
            return False, "Can only jack out from a securely breached node."

        banked = self.state.unbanked_creds
        payload_count = len(self.state.looted_payloads)
        raw_surge = self.extraction_surge()
        surge = self.mitigated_trace(raw_surge)
        trace_before = self.state.trace_percent
        if raw_surge:
            # The ICE closes on the connection as it drops. A hot extraction can still kill.
            self.add_trace(raw_surge)
            if self.state.is_game_over:
                record_news(
                    self.state.world,
                    self.state.turns_elapsed,
                    "NetWatch",
                    "Black ICE caught a netrunner at the extraction point; the deck burned.",
                    tone="negative",
                )
                fail_msg = (
                    f"💀 EXTRACTION FAILED: Black ICE surged +{surge}% as you pulled the jack "
                    f"(trace {trace_before}% -> 100%). The link burned and {banked} unbanked "
                    "Creds were lost."
                )
                self.state.message_log.append(fail_msg)
                return False, fail_msg

        self.deck.cryptocreds += banked
        self.state.unbanked_creds = 0
        self.state.is_jacked_out = True
        adjust_alert(self.state.world, -3)
        record_news(
            self.state.world,
            self.state.turns_elapsed,
            "StreetFeed",
            f"An operator vanished from the grid with {banked} CR and {payload_count} payload(s).",
            tone="positive",
        )

        msg = f"🚪 SAFE EXTRACTION! Banked {banked} CryptoCreds and secured {payload_count} data payloads."
        if surge:
            msg += (
                f" Black ICE surged +{surge}% at the extraction point "
                f"(trace {trace_before}% -> {self.state.trace_percent}%), but the link held."
            )
        for line in self._progress_quests("finish_run", "jackout"):
            msg += f"\n{line}"
        self.state.message_log.append(msg)
        return True, msg

    def settle_career(self, profile: CareerProfile) -> bool:
        """Apply a finished run's outcome to the persistent profile exactly once.

        Victory and manual jackout bank all unbanked loot; a lockout records a failed run.
        ``lifetime_creds`` grows only by the net gain over the profile's prior bank.
        """
        if self.run_settled:
            return False
        if not (self.state.is_victory or self.state.is_game_over or self.state.is_jacked_out):
            return False

        if self.state.is_victory or self.state.is_jacked_out:
            self.deck.cryptocreds += self.state.unbanked_creds
            self.state.unbanked_creds = 0
            profile.successful_runs += 1
            profile.current_streak += 1
            profile.best_streak = max(profile.best_streak, profile.current_streak)
        else:
            profile.failed_runs += 1
            profile.current_streak = 0

        profile.best_combo = max(profile.best_combo, self.state.best_combo)
        gained = max(0, self.deck.cryptocreds - profile.banked_creds)
        profile.banked_creds = self.deck.cryptocreds
        profile.lifetime_creds += gained

        daily_key = getattr(self, "daily_key", "")
        if daily_key:
            best = profile.daily_best if isinstance(profile.daily_best, dict) else {}
            best[daily_key] = max(int(best.get(daily_key, 0) or 0), gained)
            profile.daily_best = dict(sorted(best.items())[-30:])

            last_key = profile.last_daily_key if isinstance(profile.last_daily_key, str) else ""
            previous_streak = int(profile.daily_streak or 0)
            if daily_key == last_key:
                streak = max(1, previous_streak)
            elif is_next_day(last_key, daily_key):
                streak = max(1, previous_streak) + 1
            else:
                streak = 1
            profile.daily_streak = streak
            profile.best_daily_streak = max(int(profile.best_daily_streak or 0), streak)
            profile.last_daily_key = daily_key

        if self.state.is_victory:
            outcome = "victory"
        elif self.state.is_jacked_out:
            outcome = "jackout"
        else:
            outcome = "lockout"
        contract = self.state.active_contract
        old_standing = normalize_standing(profile.faction_standing)
        standing = normalize_standing(profile.faction_standing)
        if contract and contract.completed:
            standing = update_standing(
                standing, "syndicate", 3 if self.allegiance == "syndicate" else 2
            )
        if outcome in ("victory", "jackout"):
            street_gain = 2 if self.allegiance == "street" else 1
            # Kilo's arc (trust 6+): a painted handle earns one more standing.
            if outcome == "victory" and arcs_stage("kilo", self._contact_trust("kilo")) >= 3:
                street_gain += 1
            standing = update_standing(standing, "street", street_gain)
        profile.faction_standing = standing
        self.faction_standing = standing
        rank_ups: List[Dict[str, Any]] = []
        reward_total = 0
        for faction in ("syndicate", "street"):
            rank_name, reward = rank_up_reward(faction, old_standing, standing)
            if rank_name:
                rank_ups.append({"faction": faction, "rank": rank_name, "reward": reward})
                reward_total += reward
        if reward_total:
            self.deck.cryptocreds += reward_total
            profile.banked_creds = self.deck.cryptocreds
            profile.lifetime_creds += reward_total
        self.last_rank_ups = rank_ups

        new_achievements = evaluate_achievements(self, profile)
        profile.achievements = list(dict.fromkeys([
            *(profile.achievements if isinstance(profile.achievements, list) else []),
            *new_achievements,
        ]))
        self.last_unlocked_achievements = new_achievements

        summary = self.run_summary()
        score_info = score_run(
            gained=gained,
            best_combo=self.state.best_combo,
            quests_done=summary["quests_completed_count"],
            nodes_breached=summary["nodes_breached"],
            outcome=outcome,
            contract_completed=bool(contract and contract.completed),
            main_story_complete=bool(summary["main_story_complete"]),
        )
        record = {
            "outcome": outcome,
            "run_id": self.run_id,
            "seed": self.seed,
            "turns": self.state.turns_elapsed,
            "creds": self.deck.cryptocreds,
            "gained": gained,
            "best_combo": self.state.best_combo,
            "story_act": self.state.story_act,
            "quests_done": summary["quests_completed_count"],
            "contract_completed": bool(contract and contract.completed),
            "achievements": list(new_achievements),
            "daily_key": daily_key,
            "daily_modifier": self.daily_modifier,
            "difficulty": self.difficulty,
            "allegiance": self.allegiance,
            "factions": dict(standing),
            "rank_ups": list(rank_ups),
            "score": score_info["score"],
            "score_breakdown": score_info["breakdown"],
            "finished_at": time.time(),
        }
        history = profile.run_history if isinstance(profile.run_history, list) else []
        history.append(record)
        profile.run_history = history[-self.MAX_RUN_HISTORY:]

        hall_entry = {
            key: record[key]
            for key in (
                "run_id", "score", "outcome", "seed", "turns", "creds",
                "best_combo", "story_act", "daily_key", "daily_modifier", "difficulty", "finished_at",
            )
        }
        hall = profile.hall_of_fame if isinstance(profile.hall_of_fame, list) else []
        ranked = sorted(
            (entry for entry in [*hall, hall_entry] if isinstance(entry, dict)),
            key=lambda entry: int(entry.get("score", 0)) if isinstance(entry.get("score", 0), int) else 0,
            reverse=True,
        )
        unique: List[Dict[str, Any]] = []
        seen_runs = set()
        for entry in ranked:
            entry_run = entry.get("run_id")
            if entry_run and entry_run in seen_runs:
                continue
            if entry_run:
                seen_runs.add(entry_run)
            unique.append(entry)
            if len(unique) >= 10:
                break
        profile.hall_of_fame = unique
        self.last_run_score = score_info["score"]
        self.last_score_breakdown = score_info["breakdown"]
        self.last_hall_rank = next(
            (index + 1 for index, entry in enumerate(unique) if entry.get("run_id") == self.run_id),
            None,
        )
        self.run_settled = True
        return True

    def find_node(self, query: Optional[str]) -> Optional[Node]:
        """Lookup node by node_id, ip_address, or hostname."""
        if not query:
            return None
        q = str(query).strip().lower()
        if str(query) in self.nodes:
            return self.nodes[str(query)]
        for node in self.nodes.values():
            if node.node_id.lower() == q or node.ip_address.lower() == q or node.hostname.lower() == q:
                return node
        return None

    def probe_host(self, target_query: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Perform network port scan (nmap-style) against a target IP, hostname, or node_id."""
        if self.state.is_game_over:
            return False, "Cannot probe: system lockout in effect.", None
        if self.state.is_jacked_out:
            return False, "Cannot probe: terminal session jacked out.", None
        if self.state.is_victory:
            return False, "Cannot probe: mission already complete.", None

        node = self.find_node(target_query)
        if not node:
            return False, f"Host '{target_query}' not reachable or does not exist.", None

        curr = self.get_current_node()
        if node.status == NodeStatus.LOCKED and node.node_id not in curr.connected_ids and node.node_id != curr.node_id:
            return False, f"Host {node.ip_address} ({node.hostname}) is unreachable from current subnet.", None

        if node.status == NodeStatus.LOCKED:
            node.status = NodeStatus.DISCOVERED

        contract_before = self.state.active_contract
        self._mark_probed(node.node_id)
        self.add_trace(4)
        self.regenerate_cpu(1)
        self.advance_turn()

        port_data = []
        for p in node.ports:
            port_data.append({
                "port": p.port,
                "service": p.service,
                "version": p.version,
                "vulnerable": p.vulnerable,
                "breached": p.breached,
                "exploit_tool": p.exploit_tool,
            })

        report = {
            "node_id": node.node_id,
            "ip_address": node.ip_address,
            "hostname": node.hostname,
            "status": node.status.value if hasattr(node.status, "value") else str(node.status),
            "security_level": node.security_level,
            "ports": port_data,
        }
        hood = self.host_district(node.node_id)
        report.update({
            "district": hood["district"],
            "district_patrol": hood["patrol"],
            "district_load": hood["load"],
            "district_market_mood": hood["market_mood"],
        })

        port_lines = []
        for p in node.ports:
            status_str = "BREACHED" if p.breached else ("VULNERABLE" if p.vulnerable else "SECURE")
            port_lines.append(f"  {p.port:<5}/tcp  OPEN  {p.service:<10}  {p.version:<25}  [{status_str}]")

        summary = (
            f"Nmap scan report for {node.hostname} ({node.ip_address})\n"
            f"Host is UP (latency 12ms). Security Tier: {node.security_level} (RAM required: {node.security_level * 16}MB)\n"
            f"District: {hood['district']} (patrol {hood['patrol']}, market {hood['market_mood']})\n"
            f"PORT     STATE SERVICE     VERSION                     STATUS\n"
            + "\n".join(port_lines)
        )
        if self.state.is_game_over:
            summary += "\n[!] The grid burned your deck while the scan was returning."
        elif contract_before and self._contract_recon_matches(contract_before, node):
            if contract_before.failed:
                summary += (
                    "\n⏳ CONTRACT WINDOW CLOSED: the probe returned after the deadline tick; "
                    "the old bounty was not paid."
                )
            elif not contract_before.completed:
                if self.state.trace_percent <= contract_before.max_trace_limit:
                    summary += "\n" + self._finalize_contract(contract_before, node)
                else:
                    summary += (
                        f"\n⚠️ CONTRACT TRACE LIMIT EXCEEDED: {self.state.trace_percent}% > "
                        f"{contract_before.max_trace_limit}%. Cool trace and probe again to confirm "
                        "the recon bounty."
                    )
        self.state.message_log.append(f"Probed {node.ip_address} ({node.hostname}). Found {len(node.ports)} open port(s).")
        return True, summary, report

    def exploit_service(self, target_query: str, port_num: int, cve_id: Optional[str] = None) -> Tuple[bool, str]:
        """Launch an exploit payload (generic zero-day or targeted CVE) against an open service port on target host."""
        if self.state.is_game_over:
            return False, "Cannot exploit: system lockout in effect."
        if self.state.is_jacked_out:
            return False, "Cannot exploit: terminal session jacked out."
        if self.state.is_victory:
            return False, "Cannot exploit: mission already complete."

        node = self.find_node(target_query)
        if not node:
            return False, f"Target '{target_query}' not found."

        if node.status == NodeStatus.BREACHED:
            return False, f"Host {node.hostname} ({node.ip_address}) is already breached (root shell active)."
        gate = self._story_gate_reason(node)
        if gate:
            return False, gate

        lockdown = self._lockdown_reason(node)
        if lockdown:
            return False, lockdown

        curr = self.get_current_node()
        if node.node_id not in curr.connected_ids and node.node_id != curr.node_id:
            return False, f"Host {node.hostname} ({node.ip_address}) is not in direct subnet routing range."

        target_port = next((p for p in node.ports if p.port == port_num), None)
        if not target_port:
            self.add_trace(8)
            return False, f"Port {port_num}/tcp is closed or filtered on {node.ip_address}."

        # 1. Network Firewall Ingress Filter Check
        if node.firewall and node.firewall.is_port_blocked(port_num):
            self.add_trace(10)
            return False, f"🛡️ FIREWALL BLOCKED: Port {port_num}/tcp on {node.hostname} is actively blocked by {node.firewall.firewall_type}. Bypass the firewall (bypass {node.ip_address} {port_num}) or use social engineering."

        # 2. Match Exploit Payload / CVE
        selected_cve: Optional[ExploitPayload] = None
        if cve_id:
            cve_key = cve_id.lower().strip()
            selected_cve = KNOWN_CVES.get(cve_key)
            if not selected_cve:
                avail = ", ".join(k.upper() for k in KNOWN_CVES.keys())
                return False, f"Unknown exploit payload '{cve_id}'. Available CVEs: {avail}"

            if selected_cve.target_service != "any" and selected_cve.target_service != target_port.service:
                return False, f"Exploit mismatch: {selected_cve.cve_id} targets '{selected_cve.target_service}', but port {port_num} runs '{target_port.service}'."

            required_ram = selected_cve.required_ram_mb
            cpu_needed = selected_cve.cpu_cost
            trace_add = selected_cve.damage_trace
            exploit_label = f"{selected_cve.cve_id} ({selected_cve.name})"
        else:
            required_ram = node.security_level * 16
            cpu_needed = 2
            trace_add = node.trace_rate
            exploit_label = f"Zero-Day Buffer Exploit on {target_port.service}"

        if getattr(self.deck, "operating_stance", OperatingStance.BALANCED) == OperatingStance.ANALYSIS:
            required_ram = max(16, required_ram - 32)

        if self.deck.ram_mb < required_ram:
            return False, f"INSUFFICIENT RAM: Infiltration requires {required_ram}MB buffer memory (deck has {self.deck.ram_mb}MB)."

        if self.deck.cpu_cycles < cpu_needed:
            return False, f"INSUFFICIENT CPU: Launching exploit requires at least {cpu_needed} CPU cycles (deck has {self.deck.cpu_cycles})."

        if not target_port.vulnerable:
            self.add_trace(12)
            return False, f"Exploit failed: Service '{target_port.service}' on port {port_num} has no known vulnerabilities. IDS alert triggered!"

        # 3. Host Antivirus Heuristics Check
        av_notice = ""
        if node.antivirus and node.antivirus.enabled and not node.antivirus.evaded:
            stealth = selected_cve.stealth_rating if selected_cve else 3
            av_mult = 0.5 if getattr(self.deck, "operating_stance", OperatingStance.BALANCED) == OperatingStance.STEALTH else 1.0
            if stealth < 3:
                node.antivirus.alert_level = min(100, node.antivirus.alert_level + int(25 * av_mult))
                self.add_trace(8)
                av_notice = f"\n⚠️ [ANTIVIRUS WARNING] {node.antivirus.name} detected noisy exploit signature! Alert level spiked to {node.antivirus.alert_level}%."
            else:
                node.antivirus.alert_level = min(100, node.antivirus.alert_level + max(1, int(5 * av_mult)))

        self.deck.cpu_cycles -= cpu_needed
        target_port.breached = True
        self.add_trace(trace_add)
        self.advance_turn()
        breached, breach_msg = self.complete_breach(node.node_id)
        if not breached:
            msg = f"💥 EXPLOIT LANDED but root access was interrupted on {node.hostname}:\n{breach_msg}{av_notice}"
            return False, msg
        msg = f"💥 EXPLOIT SUCCESSFUL! Injected {exploit_label} via port {port_num} ({target_port.service}). Root access acquired on {node.hostname} ({node.ip_address})!\n{breach_msg}{av_notice}"
        return True, msg

    def list_files(self, target_query: Optional[str] = None) -> Tuple[bool, str, List[VirtualFile]]:
        """List files (ls) on target host's virtual filesystem (requires host to be breached)."""
        if self.state.is_game_over:
            return False, "Cannot list files: system lockout in effect.", []
        if self.state.is_jacked_out:
            return False, "Cannot list files: terminal session jacked out.", []

        if target_query:
            node = self.find_node(target_query)
        else:
            node = self.get_current_node()

        if not node:
            return False, f"Host '{target_query}' not found.", []

        if node.status != NodeStatus.BREACHED:
            return False, f"Access Denied: Host {node.hostname} ({node.ip_address}) is not breached. Exploit open ports first.", []

        files = node.filesystem
        lines = [f"Directory listing for {node.hostname} ({node.ip_address}):", "PERM        SIZE     VALUE    TARGET  PATH"]
        for f in files:
            target_mark = "★ YES" if f.is_target_data else "  no "
            val_str = f"{f.value_creds}cr" if f.value_creds > 0 else "---"
            lines.append(f"-rw-r--r--  {f.size_kb:>4}KB  {val_str:>7}  {target_mark:>6}  {f.path}")

        return True, "\n".join(lines), files

    def read_file(self, target_query: str, file_path: str) -> Tuple[bool, str, Optional[str]]:
        """Read file contents (cat) on breached host."""
        if self.state.is_game_over:
            return False, "Cannot read file: system lockout in effect.", None
        if self.state.is_jacked_out:
            return False, "Cannot read file: terminal session jacked out.", None

        node = self.find_node(target_query)
        if not node:
            return False, f"Host '{target_query}' not found.", None

        if node.status != NodeStatus.BREACHED:
            return False, f"Access Denied: Host {node.hostname} is not breached.", None

        fp = str(file_path or "").strip()
        if not fp:
            return False, "File path cannot be empty.", None

        vfile = next((f for f in node.filesystem if f.path == fp or f.path.endswith("/" + fp) or f.path.split("/")[-1] == fp), None)
        if not vfile:
            return False, f"File '{file_path}' not found on {node.hostname}.", None

        return True, f"=== [cat {vfile.path}] ===\n{vfile.content}\n=== [EOF] ===", vfile.content

    def download_file(self, target_query: str, file_path: str) -> Tuple[bool, str, Optional[VirtualFile]]:
        """Download / steal data file from breached host (yields unbanked credits and fulfills bounties)."""
        if self.state.is_game_over:
            return False, "Cannot download: system lockout in effect.", None
        if self.state.is_jacked_out:
            return False, "Cannot download: terminal session jacked out.", None
        if self.state.is_victory:
            return False, "Cannot download: mission already complete.", None

        node = self.find_node(target_query)
        if not node:
            return False, f"Host '{target_query}' not found.", None

        if node.status != NodeStatus.BREACHED:
            return False, f"Access Denied: Host {node.hostname} is not breached.", None

        fp = str(file_path or "").strip()
        if not fp:
            return False, "File path cannot be empty.", None

        vfile = next((f for f in node.filesystem if f.path == fp or f.path.endswith("/" + fp) or f.path.split("/")[-1] == fp), None)
        if not vfile:
            return False, f"File '{file_path}' not found on {node.hostname}.", None

        # Stolen data fences at the live black-market index: a hot grid pays more.
        fence_rate = market_multiplier(self.state.world)
        contract_before = self.state.active_contract

        self.add_trace(8)
        self.advance_turn()
        if self.state.is_game_over:
            fail_msg = (
                f"💀 EXFILTRATION ABORTED: the grid burned your deck while pulling '{vfile.path}'. "
                "No payout was secured."
            )
            self.state.message_log.append(fail_msg)
            return False, fail_msg, None
        if self.state.is_jacked_out or self.state.is_victory:
            return False, "Exfiltration aborted: the run has already ended.", None

        already_looted = vfile.path in self.state.looted_payloads
        if not already_looted:
            self.state.looted_payloads.append(vfile.path)
            if vfile.value_creds > 0:
                payout = max(1, int(round(vfile.value_creds * fence_rate)))
            else:
                payout = 0
            self.state.unbanked_creds += payout

        # Archive copy into player's local deck filesystem under /loot/<filename>
        loot_name = vfile.path.split("/")[-1]
        loot_path = f"/loot/{loot_name}"
        if not any(f.path == loot_path for f in self.deck.local_filesystem):
            self.deck.local_filesystem.append(
                VirtualFile(path=loot_path, size_kb=vfile.size_kb, content=vfile.content, value_creds=vfile.value_creds)
            )

        msg = f"📥 EXFILTRATION COMPLETE: Stole '{vfile.path}' ({vfile.size_kb}KB) from {node.hostname}."
        if vfile.value_creds > 0 and not already_looted:
            msg += (
                f" Fenced on the black market at x{fence_rate} index: +{payout} unbanked Creds!"
                f" Archived to local rig ({loot_path})."
            )

        contract = contract_before
        if contract and contract.failed and self._contract_download_matches(contract, node, vfile):
            msg += (
                "\n⏳ CONTRACT WINDOW CLOSED: the transfer finished after the deadline tick; "
                "the old bounty was not paid."
            )
        elif contract and not contract.completed and not contract.failed:
            target_matches = self._contract_download_matches(contract, node, vfile)
            if target_matches:
                kind = contract.objective_kind
                if kind == "wipe":
                    if contract.target_file in self.state.looted_payloads and node.logs_cleared:
                        if self.state.trace_percent <= contract.max_trace_limit:
                            msg += "\n" + self._finalize_contract(contract, node)
                        else:
                            msg += (
                                f"\n⚠️ CONTRACT TRACE LIMIT EXCEEDED: {self.state.trace_percent}% > "
                                f"{contract.max_trace_limit}%. Cool trace and re-download the target "
                                "to confirm the bounty."
                            )
                    elif contract.target_file in self.state.looted_payloads:
                        msg += (
                            "\n⚠️ BOUNTY OBJECTIVE: Target data stolen, but contract requires "
                            f"logs to be wiped! Run: wipe_logs {node.ip_address}"
                        )
                elif self.state.trace_percent > contract.max_trace_limit:
                    msg += (
                        f"\n⚠️ CONTRACT TRACE LIMIT EXCEEDED: {self.state.trace_percent}% > "
                        f"{contract.max_trace_limit}%. Cool trace and re-download the target "
                        "to confirm the bounty."
                    )
                else:
                    msg += "\n" + self._finalize_contract(contract, node)

        for line in self._progress_quests("steal_file", vfile.path):
            msg += f"\n{line}"

        self.state.message_log.append(msg)
        return True, msg, vfile

    def wipe_logs(self, target_query: str) -> Tuple[bool, str]:
        """Clear access logs (wipe_logs) on target host to reduce active trace by 20% and fulfill clean escape clauses."""
        if self.state.is_game_over:
            return False, "Cannot wipe logs: system lockout in effect."
        if self.state.is_jacked_out:
            return False, "Cannot wipe logs: terminal session jacked out."
        if self.state.is_victory:
            return False, "Cannot wipe logs: mission already complete."

        node = self.find_node(target_query)
        if not node:
            return False, f"Host '{target_query}' not found."

        if node.status != NodeStatus.BREACHED:
            return False, f"Access Denied: Host {node.hostname} is not breached."

        contract_before = self.state.active_contract
        if node.logs_cleared:
            contract = contract_before
            if contract and self._contract_wipe_ready(contract, node):
                if contract.failed:
                    return False, "Logs are already sanitized; the old contract window has closed."
                if self.state.trace_percent <= contract.max_trace_limit:
                    signoff = self._finalize_contract(contract, node)
                    return True, f"🧹 LOGS ALREADY SANITIZED on {node.hostname}. {signoff}"
                return False, (
                    f"Logs on {node.hostname} are already sanitized, but contract sign-off needs "
                    f"trace <= {contract.max_trace_limit}% (current {self.state.trace_percent}%)."
                )
            return False, f"Logs on {node.hostname} are already sanitized."

        node.logs_cleared = True
        # The Archivist's arc (trust 4+): she teaches a deeper scrub, 25% instead of 20%.
        scrub = 25 if arcs_stage("archivist", self._contact_trust("archivist")) >= 2 else 20
        trace_drop = min(self.state.trace_percent, scrub)
        self.state.trace_percent = max(0, self.state.trace_percent - scrub)
        self.scramble_hunter_radar(turns=2)
        self.advance_turn()
        if self.state.is_game_over:
            fail_msg = (
                f"💀 LOG WIPE ABORTED: the grid burned your deck on {node.hostname} before the "
                "sanitization completed. No contract credit was awarded."
            )
            self.state.message_log.append(fail_msg)
            return False, fail_msg
        if self.state.is_jacked_out or self.state.is_victory:
            return False, "Log wipe aborted: the run has already ended."

        msg = f"🧹 LOGS SANITIZED: Erased intruder access timestamps on {node.hostname} ({node.ip_address}). Trace dropped by {trace_drop}% (current: {self.state.trace_percent}%)."

        contract = contract_before
        wipe_ready = bool(contract and self._contract_wipe_ready(contract, node))
        if contract and contract.failed and wipe_ready:
            msg += (
                "\n⏳ CONTRACT WINDOW CLOSED: the logs were sanitized after the deadline tick; "
                "the old bounty was not paid."
            )
        elif wipe_ready:
            if self.state.trace_percent <= contract.max_trace_limit:
                msg += "\n" + self._finalize_contract(contract, node)
            else:
                msg += (
                    f"\n⚠️ CONTRACT TRACE LIMIT EXCEEDED: {self.state.trace_percent}% > "
                    f"{contract.max_trace_limit}%. Logs are sanitized; cool trace and run "
                    f"wipe_logs {node.ip_address} again to sign off."
                )

        for line in self._progress_quests("wipe_logs", node.ip_address):
            msg += f"\n{line}"

        self.state.message_log.append(msg)
        return True, msg

    def tick_daemons(self) -> List[str]:
        """Process active background malware daemons (e.g. keyloggers) and host antivirus sweeps."""
        if self.state.is_game_over or self.state.is_jacked_out or self.state.is_victory:
            return []

        messages = []
        for daemon in list(self.deck.active_daemons):
            if self.state.is_game_over or self.state.is_jacked_out or self.state.is_victory:
                break
            daemon.turns_active += 1
            node = self.nodes.get(daemon.target_node_id)
            if not node or node.status != NodeStatus.BREACHED:
                continue

            # Check Antivirus heuristic sweep
            if node.antivirus and node.antivirus.enabled and not node.antivirus.evaded:
                node.antivirus.alert_level = min(100, node.antivirus.alert_level + (node.antivirus.heuristic_sensitivity * 4))
                if node.antivirus.alert_level >= 50:
                    quarantine_roll = self.rng.random()
                    if quarantine_roll <= (node.antivirus.alert_level / 100.0):
                        if daemon in self.deck.active_daemons:
                            self.deck.active_daemons.remove(daemon)
                        self.add_trace(15)
                        self.break_combo(f"{node.antivirus.name} quarantined your {daemon.daemon_type}")
                        node.antivirus.quarantine_log.append(f"Quarantined {daemon.daemon_type} on turn {self.state.turns_elapsed}")
                        q_msg = f"🛡️ [ANTIVIRUS QUARANTINE] {node.antivirus.name} on {node.hostname} detected and terminated background {daemon.daemon_type}! Alert Level: {node.antivirus.alert_level}%. Active Trace +15%!"
                        messages.append(q_msg)
                        self.state.message_log.append(q_msg)
                        if self.state.is_game_over:
                            break
                        continue

            # Kilo's arc (trust 4+): ghost-boot tuning lifts daemon yields 10%.
            daemon_yield = daemon.yield_per_turn
            if arcs_stage("kilo", self._contact_trust("kilo")) >= 2:
                daemon_yield += max(1, daemon_yield // 10)
            self.state.unbanked_creds += daemon_yield
            self.add_trace(daemon.detection_risk)
            msg = f"📡 [{daemon.daemon_type.upper()}] Harvested +{daemon_yield} unbanked Creds from {node.hostname} (Trace +{daemon.detection_risk}%)."
            messages.append(msg)
            self.state.message_log.append(msg)
            if self.state.is_game_over:
                break
        return messages

    def deploy_daemon(self, target_query: str, daemon_type: str = "keylogger") -> Tuple[bool, str]:
        """Deploy an in-game background malware listener daemon onto a breached host."""
        if self.state.is_game_over:
            return False, "Cannot deploy daemon: system lockout in effect."
        if self.state.is_jacked_out:
            return False, "Cannot deploy daemon: terminal session jacked out."
        if self.state.is_victory:
            return False, "Cannot deploy daemon: mission already complete."

        node = self.find_node(target_query)
        if not node:
            return False, f"Target '{target_query}' not found."

        if node.status != NodeStatus.BREACHED:
            return False, f"Cannot deploy daemon: Host {node.hostname} ({node.ip_address}) is not breached."

        if any(d.target_node_id == node.node_id and d.daemon_type == daemon_type for d in self.deck.active_daemons):
            return False, f"Daemon '{daemon_type}' is already running on {node.hostname}."

        if self.deck.cpu_cycles < 2:
            return False, "Insufficient CPU cycles (need 2 CPU to initialize daemon listener)."

        self.deck.cpu_cycles -= 2
        existing_ids = [
            int(d.daemon_id.rsplit("_", 1)[-1])
            for d in self.deck.active_daemons
            if d.daemon_id.startswith("dmn_") and d.daemon_id.rsplit("_", 1)[-1].isdigit()
        ]
        daemon_id = f"dmn_{max(existing_ids, default=0) + 1:03d}"
        # Deeper hosts carry richer traffic: siphoning the core pays more than a border router.
        daemon_yield = 15 + node.security_level * 5
        daemon = MalwareDaemon(
            daemon_id=daemon_id,
            daemon_type=daemon_type,
            target_node_id=node.node_id,
            target_ip=node.ip_address,
            yield_per_turn=daemon_yield,
            detection_risk=3,
        )
        self.deck.active_daemons.append(daemon)
        adjust_alert(self.state.world, 2)
        msg = f"👾 DAEMON INITIALIZED: [{daemon_type.upper()}] active on {node.hostname} ({node.ip_address}). Passively harvesting +{daemon_yield} unbanked Creds/turn."
        for line in self._progress_quests("deploy_daemon", daemon_type):
            msg += f"\n{line}"
        self.state.message_log.append(msg)
        return True, msg

    def list_local_files(self) -> Tuple[bool, str, List[VirtualFile]]:
        """List files (ls) stored on player's local cyberdeck rig (localhost)."""
        if self.state.is_game_over:
            return False, "Cannot list files: system lockout in effect.", []
        if self.state.is_jacked_out:
            return False, "Cannot list files: terminal session jacked out.", []

        lines = [
            f"Local Rig Filesystem ({self.deck.local_hostname} [{self.deck.local_ip}]):",
            "PERM        SIZE     VALUE    PATH"
        ]
        for f in self.deck.local_filesystem:
            val_str = f"{f.value_creds}cr" if f.value_creds > 0 else "---"
            lines.append(f"-rw-r--r--  {f.size_kb:>4}KB  {val_str:>7}  {f.path}")
        return True, "\n".join(lines), self.deck.local_filesystem

    def read_local_file(self, file_path: str) -> Tuple[bool, str, Optional[str]]:
        """Read content (cat) of a file on player's local cyberdeck rig."""
        if self.state.is_game_over:
            return False, "Cannot read file: system lockout in effect.", None
        if self.state.is_jacked_out:
            return False, "Cannot read file: terminal session jacked out.", None

        fp = str(file_path or "").strip()
        if not fp:
            return False, "File path cannot be empty.", None

        vfile = next((f for f in self.deck.local_filesystem if f.path == fp or f.path.endswith("/" + fp) or f.path.split("/")[-1] == fp), None)
        if not vfile:
            return False, f"File '{file_path}' not found on local deck.", None
        return True, f"=== [cat {vfile.path}] ===\n{vfile.content}\n=== [EOF] ===", vfile.content

    def _social_success_chance(self, node: Any, vector_key: str, emp: Any) -> Tuple[float, str]:
        """Deterministic lure odds shared by execution and forecast (no roll)."""
        awareness = emp.awareness_level
        if vector_key == SocialVectorType.SPEAR_PHISH:
            base_chance = max(0.40, 0.90 - (node.security_level * 0.12))
        elif vector_key == SocialVectorType.PRETEXT:
            base_chance = 0.90 if awareness == SecurityAwarenessLevel.NAIVE else (0.75 if awareness == SecurityAwarenessLevel.STANDARD else 0.40)
        elif vector_key == SocialVectorType.BAIT:
            base_chance = 0.85 if awareness == SecurityAwarenessLevel.NAIVE else (0.70 if awareness == SecurityAwarenessLevel.STANDARD else 0.45)
        else:  # VISHING
            base_chance = 0.90 if awareness == SecurityAwarenessLevel.NAIVE else (0.70 if awareness == SecurityAwarenessLevel.STANDARD else 0.50)

        # The living clock matters: staff availability and alertness follow the shift.
        current_shift = shift_name(self.state.world.minute)
        base_chance = apply_social_shift(base_chance, self.state.world.minute)
        return base_chance, current_shift

    def social_engineer(self, target_query: str, vector: str = "spear_phish", employee_name: Optional[str] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """Launch an interactive social engineering attack (pretext, bait, spear_phish, vishing) against target employees."""
        vector_key = str(vector or "").lower().strip()
        valid_vectors = [SocialVectorType.PRETEXT, SocialVectorType.BAIT, SocialVectorType.SPEAR_PHISH, SocialVectorType.VISHING]
        if vector_key not in valid_vectors:
            return False, f"Invalid vector '{vector}'. Valid options: pretext, bait, spear_phish, vishing.", {}

        if self.state.is_game_over:
            return False, "Cannot engage: system lockout in effect.", {}
        if self.state.is_jacked_out:
            return False, "Cannot engage: terminal session jacked out.", {}
        if self.state.is_victory:
            return False, "Cannot engage: mission already complete.", {}

        node = self.find_node(target_query)
        if not node:
            return False, f"Target '{target_query}' not found.", {}

        if node.status == NodeStatus.BREACHED:
            return False, f"Host {node.hostname} ({node.ip_address}) is already compromised.", {}

        curr = self.get_current_node()
        if node.node_id not in curr.connected_ids and node.node_id != curr.node_id:
            return False, f"Target {node.hostname} is out of subnet range.", {}

        if self.deck.cpu_cycles < 1:
            return False, "Insufficient CPU cycles (need 1 CPU).", {}

        # Pick target employee
        emp = None
        if employee_name and node.employees:
            emp = next((e for e in node.employees if e.name.lower() == employee_name.lower()), None)
        if not emp and node.employees:
            emp = node.employees[0]
        if not emp:
            emp = EmployeeProfile(name="Staff Associate", role="Operations", email=f"staff@{node.hostname}", awareness_level=SecurityAwarenessLevel.STANDARD)

        self.deck.cpu_cycles -= 1
        self.add_trace(6)
        self.advance_turn()
        if self.state.is_game_over:
            fail_msg = (
                f"💀 SOCIAL ENGINEERING ABORTED: the grid burned your deck while the lure was "
                f"in flight to {node.hostname}."
            )
            self.state.message_log.append(fail_msg)
            return False, fail_msg, {}
        if self.state.is_jacked_out or self.state.is_victory:
            return False, "Social engineering aborted: the run has already ended.", {}

        # Calculate success probability based on vector vs employee security awareness
        base_chance, current_shift = self._social_success_chance(node, vector_key, emp)
        shift_modifier = social_shift_modifier(self.state.world.minute)

        roll = self.rng.random()
        success = roll <= base_chance

        report = {
            "target_ip": node.ip_address,
            "target_hostname": node.hostname,
            "vector": vector_key,
            "employee": emp.name,
            "role": emp.role,
            "awareness": emp.awareness_level,
            "success": success,
            "roll": round(roll, 2),
            "chance": round(base_chance, 2),
            "shift": current_shift,
            "shift_modifier": shift_modifier,
        }

        shift_note = f"   * Shift timing ({current_shift}): social vectors {shift_modifier:+.0%}.\n"

        if success:
            emp.compromised = True
            if node.status == NodeStatus.LOCKED:
                node.status = NodeStatus.DISCOVERED

            lowered = False
            if node.security_level > 1:
                node.security_level -= 1
                lowered = True

            # If host firewall has blocked rules, auto-bypass a blocked rule!
            fw_bypass_notice = ""
            if node.firewall and node.firewall.enabled:
                blocked_rule = next((r for r in node.firewall.rules if r.action == "BLOCK" and not r.bypassed), None)
                if blocked_rule:
                    blocked_rule.bypassed = True
                    blocked_rule.bypass_method = f"social_{vector_key}"
                    fw_bypass_notice = f"   * Leaked security override: Firewall port {blocked_rule.port}/tcp rule bypassed!\n"

            cred_file = f"/loot/{node.hostname}_credentials.token"
            token_content = (
                f"HARVESTED SOCIAL CREDENTIALS\n"
                f"Target: {emp.name} ({emp.role})\n"
                f"Host: {node.hostname} ({node.ip_address})\n"
                f"Vector: {vector_key.upper()}\n"
                f"Credential: {emp.leaked_credential or f'TOKEN-{self.rng.randint(1000, 9999)}-SEC'}\n"
            )
            if not any(f.path == cred_file for f in self.deck.local_filesystem):
                self.deck.local_filesystem.append(
                    VirtualFile(path=cred_file, size_kb=1, content=token_content, value_creds=40)
                )

            tag = "🎣 PHISHING SUCCESS" if vector_key == SocialVectorType.SPEAR_PHISH else f"🎭 SOCIAL ENGINEERING SUCCESS [{vector_key.upper()}]"
            msg = f"{tag}: Employee at {node.hostname} clicked credential lure!\n" if vector_key == SocialVectorType.SPEAR_PHISH else f"{tag}: Compromised {emp.name} ({emp.role}) at {node.hostname}!\n"
            msg += shift_note
            if lowered:
                msg += f"   * Security tier downgraded to Level {node.security_level} (Buffer RAM required reduced to {node.security_level * 16}MB)!\n"
            if fw_bypass_notice:
                msg += fw_bypass_notice
            msg += f"   * Harvested auth token saved to local rig at {cred_file}."
            for line in self._progress_quests("social_vector", vector_key):
                msg += f"\n{line}"
            self.state.message_log.append(f"Social engineering [{vector_key}] success on {node.hostname} ({self.host_district(node.node_id)['district']} grid).")
            return True, msg, report
        else:
            self.add_trace(8)
            self.break_combo("social lure flagged by target staff")
            if node.antivirus:
                node.antivirus.alert_level = min(100, node.antivirus.alert_level + 20)
            tag = "🎣 PHISHING FAILED" if vector_key == SocialVectorType.SPEAR_PHISH else f"🎭 SOCIAL ENGINEERING FAILED [{vector_key.upper()}]"
            msg = f"{tag}: {emp.name} on {node.hostname} flagged lure. IDS alert triggered (Trace +8%)! [{self.host_district(node.node_id)['district']} grid]\n{shift_note}"
            self.state.message_log.append(msg)
            return False, msg, report

    def phish_target(self, target_query: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Dispatch a simulated social engineering spear-phishing campaign to target host employees (backward compatible)."""
        return self.social_engineer(target_query, vector=SocialVectorType.SPEAR_PHISH)

    def get_firewall_status(self, target_query: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Inspect the network firewall rules defending a target host."""
        node = self.find_node(target_query)
        if not node:
            return False, f"Target '{target_query}' not found.", None
        if not node.firewall:
            return True, f"Host {node.hostname} ({node.ip_address}) has no active network firewall.", None

        rules_desc = []
        for r in node.firewall.rules:
            status = "BYPASSED" if r.bypassed else ("BLOCKED" if r.action == "BLOCK" else "ALLOWED")
            rules_desc.append(f"  * Port {r.port}/tcp: [{status}] (Method: {r.bypass_method or 'None'})")

        msg = f"🛡️ [FIREWALL REPORT] {node.hostname} ({node.ip_address})\n"
        msg += f"Type: {node.firewall.firewall_type} | Policy: {node.firewall.policy} | Tampered: {node.firewall.tampered}\n"
        msg += "\n".join(rules_desc) if rules_desc else "  * No active port filtering rules."
        return True, msg, node.firewall.to_dict()

    def bypass_firewall(self, target_query: str, port: int, method: str = "knock") -> Tuple[bool, str]:
        """Execute a firewall bypass against a blocked port via port-knocking, packet fragmentation, or proxy-tunneling."""
        if self.state.is_game_over:
            return False, "Cannot bypass firewall: system lockout in effect."
        if self.state.is_jacked_out:
            return False, "Cannot bypass firewall: terminal session jacked out."
        if self.state.is_victory:
            return False, "Cannot bypass firewall: mission already complete."

        node = self.find_node(target_query)
        if not node:
            return False, f"Target '{target_query}' not found."

        curr = self.get_current_node()
        if node.node_id not in curr.connected_ids and node.node_id != curr.node_id:
            return False, f"Target {node.hostname} ({node.ip_address}) is not in direct subnet range."

        if not node.firewall or not node.firewall.enabled:
            return False, f"Host {node.hostname} has no active firewall."

        method_key = str(method or "").lower().strip()
        costs = {
            "knock": {"cpu": 1, "trace": 5, "name": "Port Knocking Sequence"},
            "fragment": {"cpu": 1, "trace": 7, "name": "MTU Packet Fragmentation"},
            "tunnel": {"cpu": 2, "trace": 9, "name": "Encapsulated Proxy Tunneling"},
        }
        if method_key not in costs:
            return False, f"Unknown bypass method '{method}'. Valid methods: knock, fragment, tunnel."

        spec = costs[method_key]
        if self.deck.cpu_cycles < spec["cpu"]:
            return False, f"INSUFFICIENT CPU: {spec['name']} requires {spec['cpu']} CPU cycles."

        rule = next((r for r in node.firewall.rules if r.port == port and r.action == "BLOCK"), None)
        if not rule:
            return False, f"Port {port}/tcp is not currently blocked by {node.hostname}'s firewall."

        if rule.bypassed:
            return False, f"Port {port}/tcp is already bypassed on {node.hostname}."

        self.deck.cpu_cycles -= spec["cpu"]
        self.add_trace(spec["trace"])
        self.advance_turn()
        if self.state.is_game_over:
            fail_msg = (
                f"💀 FIREWALL BYPASS ABORTED: the grid burned your deck while injecting "
                f"{spec['name']} into {node.hostname}."
            )
            self.state.message_log.append(fail_msg)
            return False, fail_msg
        if self.state.is_jacked_out or self.state.is_victory:
            return False, "Firewall bypass aborted: the run has already ended."

        rule.bypassed = True
        rule.bypass_method = method_key
        msg = f"🔓 FIREWALL BYPASSED: Injected {spec['name']} into {node.hostname} ({node.ip_address}).\n"
        msg += f"   * Port {port}/tcp rule deactivated! Direct service exploitation is now enabled (Trace +{spec['trace']}%)."
        self.state.message_log.append(f"Bypassed firewall port {port} on {node.hostname}.")
        return True, msg

    def get_antivirus_status(self, target_query: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Inspect the active Antivirus / EDR status on a target host."""
        node = self.find_node(target_query)
        if not node:
            return False, f"Target '{target_query}' not found.", None
        if not node.antivirus:
            return True, f"Host {node.hostname} ({node.ip_address}) has no active Antivirus software.", None

        status_str = "HOOKED / EVADED" if node.antivirus.evaded else ("ACTIVE / HUNTING" if node.antivirus.enabled else "DISABLED")
        msg = f"🛡️ [ANTIVIRUS REPORT] {node.hostname} ({node.ip_address})\n"
        msg += f"Engine: {node.antivirus.name} ({node.antivirus.version})\n"
        msg += f"Status: [{status_str}]\n"
        msg += f"Alert Level: {node.antivirus.alert_level}% (Sensitivity: {node.antivirus.heuristic_sensitivity}/5)\n"
        msg += f"Quarantined Daemons: {len(node.antivirus.quarantine_log)}"
        return True, msg, node.antivirus.to_dict()

    def evade_antivirus(self, target_query: str, method: str = "rootkit") -> Tuple[bool, str]:
        """Inject a stealth evasion hook or memory-patch into a target host's Antivirus suite."""
        if self.state.is_game_over:
            return False, "Cannot evade AV: system lockout in effect."
        if self.state.is_jacked_out:
            return False, "Cannot evade AV: terminal session jacked out."
        if self.state.is_victory:
            return False, "Cannot evade AV: mission already complete."

        node = self.find_node(target_query)
        if not node:
            return False, f"Target '{target_query}' not found."

        curr = self.get_current_node()
        if node.node_id not in curr.connected_ids and node.node_id != curr.node_id:
            return False, f"Target {node.hostname} ({node.ip_address}) is not in direct subnet range."

        if not node.antivirus or not node.antivirus.enabled:
            return False, f"Host {node.hostname} has no active Antivirus to evade."

        if node.antivirus.evaded:
            return False, f"Antivirus on {node.hostname} ({node.antivirus.name}) is already evaded and blinded."

        method_key = str(method or "").lower().strip()
        costs = {
            "rootkit": {"cpu": 2, "trace": 6, "name": "Kernel Rootkit Hook"},
            "spoof": {"cpu": 1, "trace": 8, "name": "Signature Morphing Shifter"},
        }
        if method_key not in costs:
            return False, f"Unknown evasion method '{method}'. Valid methods: rootkit, spoof."

        spec = costs[method_key]
        if self.deck.cpu_cycles < spec["cpu"]:
            return False, f"INSUFFICIENT CPU: {spec['name']} requires {spec['cpu']} CPU cycles."

        self.deck.cpu_cycles -= spec["cpu"]
        self.add_trace(spec["trace"])
        self.advance_turn()
        if self.state.is_game_over:
            fail_msg = (
                f"💀 EDR EVASION ABORTED: the grid burned your deck while deploying "
                f"{spec['name']} against {node.hostname}."
            )
            self.state.message_log.append(fail_msg)
            return False, fail_msg
        if self.state.is_jacked_out or self.state.is_victory:
            return False, "EDR evasion aborted: the run has already ended."

        node.antivirus.evaded = True
        node.antivirus.alert_level = max(0, node.antivirus.alert_level - 35)
        msg = f"👁️‍🗨️ ANTIVIRUS EVADED: Deployed {spec['name']} against {node.antivirus.name} on {node.hostname}.\n"
        msg += f"   * EDR scanner blinded! Memory sweeps suppressed for active daemons (Alert reduced to {node.antivirus.alert_level}%)."
        self.state.message_log.append(f"Blinded AV on {node.hostname}.")
        return True, msg

    def list_cves(self) -> List[Dict[str, Any]]:
        """Return the catalog of weaponized CVE exploit payloads."""
        return [cve.to_dict() for cve in KNOWN_CVES.values()]

    def craft_virus(self, recipe_name: str) -> Tuple[bool, str]:
        """Assemble a custom virus chip in the netrunner workshop."""
        if self.state.is_game_over:
            return False, "Cannot craft virus: system lockout in effect."
        if self.state.is_jacked_out:
            return False, "Cannot craft virus: terminal session jacked out."
        if self.state.is_victory:
            return False, "Cannot craft virus: mission already complete."

        recipe_key = str(recipe_name or "").lower().strip()
        recipe = CRAFTING_RECIPES.get(recipe_key)
        if not recipe:
            available = ", ".join(CRAFTING_RECIPES.keys())
            return False, f"Unknown recipe '{recipe_name}'. Available recipes: {available}"

        total_funds = self.deck.cryptocreds + self.state.unbanked_creds
        if total_funds < recipe.cost_creds:
            return False, f"Insufficient funds: Synthesis requires {recipe.cost_creds} Creds (available: {total_funds} Creds)."

        rem = recipe.cost_creds
        if self.state.unbanked_creds >= rem:
            self.state.unbanked_creds -= rem
        else:
            rem -= self.state.unbanked_creds
            self.state.unbanked_creds = 0
            self.deck.cryptocreds -= rem

        self.deck.exploits.append(recipe.name)
        msg = f"🧬 WORKSHOP SYNTHESIS COMPLETE: Crafted virus chip '{recipe.name}' (Vector: {recipe.vector}, Payload: {recipe.payload}). Loaded into deck exploits."
        for line in self._progress_quests("craft_recipe", recipe_key):
            msg += f"\n{line}"
        self.state.message_log.append(msg)
        return True, msg

    def list_crafting_recipes(self) -> List[Dict[str, Any]]:
        """List available malware crafting recipes in the workshop."""
        return [r.to_dict() for r in CRAFTING_RECIPES.values()]

    def spend_threat_intel(self, mode: str, target_query: Optional[str] = None) -> Tuple[bool, str]:
        """Burn ANALYSIS-stance threat intel for a tactical edge.

        - reveal (1 intel): remote deep-scan a host without adjacency and without trace.
        - forge (2 intel): mint a single-use zero_day_forge chip that breaches a host outright.
        """
        if self.state.is_game_over:
            return False, "Cannot spend intel: system lockout in effect."
        if self.state.is_jacked_out:
            return False, "Cannot spend intel: terminal session jacked out."
        if self.state.is_victory:
            return False, "Cannot spend intel: mission already complete."

        action = str(mode or "reveal").lower().strip()
        if action not in ("reveal", "forge"):
            return False, f"Unknown intel action '{mode}'. Use 'reveal' or 'forge'."

        cost = 1 if action == "reveal" else 2
        if action == "forge" and "zero_day_forge" in self.deck.exploits:
            return False, "A zero_day_forge chip is already loaded. Burn it before forging another."
        if self.deck.threat_intel_count < cost:
            return False, (
                f"INSUFFICIENT THREAT INTEL: {action} needs {cost} fragment(s), "
                f"deck holds {self.deck.threat_intel_count}. Breach hosts in ANALYSIS stance to harvest intel."
            )

        if action == "forge":
            self.deck.threat_intel_count -= cost
            self.deck.exploits.append("zero_day_forge")
            msg = (
                f"🧠 INTEL FORGED: assembled a single-use zero_day_forge chip from {cost} threat fragments. "
                "Run it on any adjacent host to breach it outright."
            )
            self.state.message_log.append(msg)
            return True, msg

        node = self.find_node(target_query or "")
        if not node:
            return False, f"Intel reveal needs a known host; '{target_query}' was not found."
        if node.status == NodeStatus.BREACHED:
            return False, f"{node.hostname} is already breached; hold the fragment for another target."

        # Threat intel is a side-effect-free remote deep scan: it must not add
        # trace, spend CPU, or advance the world clock.
        if node.status == NodeStatus.LOCKED:
            node.status = NodeStatus.DISCOVERED
        self._mark_probed(node.node_id)
        self.deck.threat_intel_count -= cost

        open_ports = [f"{p.port}/{p.service}" for p in node.ports]
        vuln_ports = [f"{p.port}/{p.service}" for p in node.ports if p.vulnerable]
        blocked = []
        if node.firewall and node.firewall.enabled:
            blocked = [str(p) for p in node.ports if node.firewall.is_port_blocked(p.port)]
        edr = node.antivirus.name if node.antivirus and node.antivirus.enabled else "none"
        msg = (
            f"🛰️ INTEL REVEAL ({cost} fragment): {node.hostname} ({node.ip_address}) — "
            f"services [{', '.join(open_ports) or 'none'}] | "
            f"vulnerable [{', '.join(vuln_ports) or 'none'}] | "
            f"blocked ports [{', '.join(blocked) or 'none'}] | EDR [{edr}] // "
            f"{self.host_district(node.node_id)['district']} grid"
        )
        self.state.message_log.append(msg)
        return True, msg

    def set_stance(self, stance_query: str) -> Tuple[bool, str]:
        """Switch cyberdeck operating bus stance: balanced, stealth, overclock, analysis."""
        if self.state.is_game_over:
            return False, "Cannot shift stance: system lockout in effect."
        if self.state.is_jacked_out:
            return False, "Cannot shift stance: terminal session jacked out."
        if self.state.is_victory:
            return False, "Cannot shift stance: mission already complete."

        stance = (stance_query or "").strip().lower()
        valid = (OperatingStance.BALANCED, OperatingStance.STEALTH, OperatingStance.OVERCLOCK, OperatingStance.ANALYSIS)
        if stance not in valid:
            return False, f"Unknown operating stance '{stance_query}'. Available: {', '.join(valid)}."

        if self.deck.operating_stance == stance:
            return True, f"Cyberdeck operating bus is already in {stance.upper()} stance."

        self.deck.operating_stance = stance
        effects = {
            OperatingStance.BALANCED: "Standard neural throughput calibrated.",
            OperatingStance.STEALTH: "Phantom routing engaged: -35% trace generation, -50% EDR alert buildup.",
            OperatingStance.OVERCLOCK: "Blitz bus engaged: +25% breach bounty, accelerated CPU regen (+25% trace generation).",
            OperatingStance.ANALYSIS: "Oracle diagnostics engaged: -32MB RAM threshold, 1-2 threat intel per fresh breach.",
        }
        msg = f"⚡ Stance shifted to [{stance.upper()}]. {effects[stance]}"
        self.state.message_log.append(msg)
        return True, msg

    def add_proxy_hop(self, node_query: str) -> Tuple[bool, str]:
        """Route neural telemetry through a compromised host to dampen trace buildup."""
        if self.state.is_game_over:
            return False, "Cannot route proxy: system lockout in effect."
        if self.state.is_jacked_out:
            return False, "Cannot route proxy: terminal session jacked out."
        if self.state.is_victory:
            return False, "Cannot route proxy: mission already complete."

        node = self.find_node(node_query)
        if not node:
            return False, f"Target host '{node_query}' not found."
        if node.status != NodeStatus.BREACHED:
            return False, f"Cannot proxy through {node.hostname} ({node.ip_address}): host is not breached."
        if node.node_id == self.state.current_node_id:
            return False, f"Cannot proxy through active terminal host {node.hostname}."
        if node.node_id in self.deck.proxy_chain:
            return False, f"Host {node.hostname} is already in the proxy chain."
        if len(self.deck.proxy_chain) >= 3:
            return False, "Proxy chain limit reached (max 3 hops). Sever a proxy hop first."
        if self.deck.cpu_cycles < 1:
            return False, "Cannot route proxy: at least 1 CPU cycle is required to splice the tunnel."

        self.deck.cpu_cycles -= 1
        self.deck.proxy_chain.append(node.node_id)
        dampen_pct = min(45, len(self.deck.proxy_chain) * 15)
        msg = (
            f"🔗 Proxy tunnel established via {node.hostname} ({node.ip_address}) (-1 CPU). "
            f"Signal dampening: -{dampen_pct}% trace generation "
            f"({len(self.deck.proxy_chain)}/3 hops active)."
        )
        self.state.message_log.append(msg)
        return True, msg

    def sever_proxy(self, node_query: Optional[str] = None) -> Tuple[bool, str]:
        """Burn a proxy tunnel connection to dump 15% trace immediately."""
        if self.state.is_game_over:
            return False, "Cannot sever proxy: system lockout in effect."
        if self.state.is_jacked_out:
            return False, "Cannot sever proxy: terminal session jacked out."
        if self.state.is_victory:
            return False, "Cannot sever proxy: mission already complete."
        if not self.deck.proxy_chain:
            return False, "No active proxy hops in tunnel."

        target_id: Optional[str] = None
        if node_query:
            node = self.find_node(node_query)
            if not node or node.node_id not in self.deck.proxy_chain:
                return False, f"Host '{node_query}' is not in active proxy chain."
            target_id = node.node_id
        else:
            target_id = self.deck.proxy_chain[-1]

        self.deck.proxy_chain.remove(target_id)
        node = self.nodes.get(target_id)
        host_label = f"{node.hostname} ({node.ip_address})" if node else target_id

        trace_dump = min(self.state.trace_percent, 15)
        self.state.trace_percent = max(0, self.state.trace_percent - trace_dump)
        msg = f"💥 Proxy tunnel severed at {host_label}! Scrambled telemetry dropped -{trace_dump}% trace ({len(self.deck.proxy_chain)} hops remaining)."
        self.state.message_log.append(msg)
        return True, msg

    def quickhack(self, target_query: str) -> Tuple[bool, str]:
        """Instant-breach an adjacent low-security host at a steep CPU and trace cost.

        Quickhacking skips the mini-game but cannot defeat hardened ICE. It exists so a
        confident runner can trade resources for tempo, not to bypass the puzzle loop.
        """
        if self.state.is_game_over:
            return False, "Cannot quickhack: system lockout in effect."
        if self.state.is_jacked_out:
            return False, "Cannot quickhack: terminal session jacked out."
        if self.state.is_victory:
            return False, "Cannot quickhack: mission already complete."

        node = self.find_node(target_query)
        if not node:
            return False, f"Target '{target_query}' not found."
        if node.status == NodeStatus.BREACHED:
            return False, f"Host {node.hostname} ({node.ip_address}) is already breached."

        gate = self._story_gate_reason(node)
        if gate:
            return False, gate
        lockdown = self._lockdown_reason(node)
        if lockdown:
            return False, lockdown

        curr = self.get_current_node()
        if node.node_id not in curr.connected_ids and node.node_id != curr.node_id:
            return False, f"Host {node.hostname} ({node.ip_address}) is not adjacent in routing range."

        if node.security_level > 2:
            self.add_trace(6)
            return False, (
                f"🧠 QUICKHACK REJECTED: {node.hostname} runs security tier {node.security_level} ICE. "
                "Rapid injection only pierces tiers 1-2; use probe + exploit for hardened hosts."
            )

        cpu_cost = 2 + node.security_level
        if self.deck.cpu_cycles < cpu_cost:
            return False, (
                f"Insufficient CPU for quickhack: needs {cpu_cost} cycles "
                f"(deck has {self.deck.cpu_cycles})."
            )

        self.clear_pending_puzzle(node.node_id)
        self.deck.cpu_cycles -= cpu_cost
        self.add_trace(10 + node.security_level * 4)
        self.advance_turn()
        breached, breach_msg = self.complete_breach(node.node_id)
        if not breached:
            return False, f"⚡ QUICKHACK SPENT but the breach collapsed:\n{breach_msg}"
        return True, (
            f"⚡ QUICKHACK LANDED on {node.hostname} ({node.ip_address}) for {cpu_cost} CPU. "
            f"Rapid injection skipped the ICE dialogue.\n{breach_msg}"
        )


