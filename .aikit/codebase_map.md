# Codebase Map & Symbol Catalog 🗺️

> **AUTO-GENERATED & VERIFIED BY `scripts/update_knowledge_base.py`**
> This document provides an automated, up-to-date registry of all modules, classes, and exported functions across this repository.

---

## 📊 Codebase Metrics
- **Total Python Modules**: `48`
- **Total Classes**: `84`
- **Total Top-Level Functions**: `122`
- **Total Class Methods**: `822`
- **Total Source Lines**: `18707`

---

## 📦 Modules & Exported Symbols

### [`cyberpulse/__init__.py`](cyberpulse/__init__.py)
> *CyberPulse: Retro-cyberpunk terminal hacking simulation game.*

**Size**: `3` lines (`91` bytes)

---

### [`cyberpulse/achievements.py`](cyberpulse/achievements.py)
> *Career milestone catalog and settlement-time evaluation.*

**Size**: `129` lines (`5157` bytes)

**Classes:**
- `class Achievement` - *A permanent career milestone shown in the dossier.*

**Functions:**
- `def achievement_name(achievement_id)` - *Return a display name, falling back to the raw identifier.*
- `def achievement_status(profile)` - *Return the catalog annotated with this profile's unlocked state.*
- `def achievement_names(achievement_ids)` - *Map stored identifiers to display names in catalog order.*
- `def evaluate_achievements(engine, profile)` - *Return newly earned milestone identifiers for a settled run.*

---

### [`cyberpulse/arcs.py`](cyberpulse/arcs.py)
> *Operative loyalty arcs + district grid simulation (additive, save-compatible).*

**Size**: `254` lines (`10672` bytes)

**Functions:**
- `def arc_stage(contact_id, trust)` - *Return how many arc stages (0-3) a trust value unlocks.*
- `def stage_info(contact_id, stage)` - *Return the label/text/bonus of an arc stage (stage 1-3).*
- `def arc_status(contacts)` - *Summarize every operative's arc for CLI/Web/dossier consumers.*
- `def _district_seed(seed, tick, key)` - *Deterministic district roll (hashlib, not hash(): stable across processes).*
- `def district_for_node(seed, node_id)` - *Tick-independent street mapping: every host lives in one district.*
- `def district_grid(seed, tick, alert)` - *Deterministic per-tick district simulation: load, patrol, market mood.*
- `def arc_epilogue_lines(contacts)` - *Epilogue stanzas for operatives whose loyalty arc reached stage 3.*
- `def live_bonuses(engine)` - *Which arc mechanical bonuses are currently active for this run.*
- `def ensure_arc_quests(engine)` - *Backfill arc side-quests into old runs; returns number added.*

---

### [`cyberpulse/cli.py`](cyberpulse/cli.py)
> *Interactive and scriptable retro-cyberpunk terminal CLI for CyberPulse with behavioral mechanics.*

**Size**: `1623` lines (`76161` bytes)

**Functions:**
- `def print_deckos(engine)`
- `def print_arcs(engine)`
- `def print_districts(engine)`
- `def setup_terminal_encoding()` - *Ensure stdout and stderr handle utf-8 safely across all Windows code pages.*
- `def safe_print(msg)` - *Print message to stdout with graceful fallback for legacy terminal code pages.*
- `def get_default_data_dir()`
- `def render_trace_bar(trace_percent, width)`
- `def topology_token(engine, node_id)` - *Compact fixed-width token for the ASCII topology map.*
- `def render_topology_map(engine)` - *Fixed-layout ASCII topology mirroring the web matrix slots.*
- `def print_hud(engine)`
- `def print_contract(engine)`
- `def print_hunters(engine)`
- `def print_shop(shop, deck, price_multiplier, street_discount)`
- `def print_tutorial(engine, profile)` - *Render the first-run field manual with live checklist state.*
- `def print_hall(profile, difficulty)` - *Render the Hall of Fame, optionally filtered by difficulty.*
- `def print_career(profile)`
- `def print_workshop(engine)`
- `def print_daemons(engine)`
- `def print_cves(engine)`
- `def print_story(engine)`
- `def print_world(engine)`
- `def print_news(engine, limit)`
- `def print_run_summary(engine)`
- `def print_quests(engine)`
- `def print_contacts(engine)`
- `def print_save_slots(saves)` - *Render a compact list of restorable save slots.*
- `def choose_load_slot(save_mgr)` - *Prompt for a save slot to continue; returns None when the player cancels.*
- `def show_main_menu(engine, save_mgr)` - *Render the interactive main menu and return 'start', 'load', 'daily', or 'quit'.*
- `def execute_hack_puzzle(engine, target_id, auto_solve)`
- `def run_command(cmd_line, engine, save_mgr, auto_solve)` - *Execute a single command string. Returns False to quit.*
- `def handle_run_completion(engine, save_mgr)` - *Persist career stats and clean up savegame when run concludes (victory or game-over).*
- `def main(argv)`

---

### [`cyberpulse/daily.py`](cyberpulse/daily.py)
> *Deterministic daily-run keys, seeds and rule modifiers.*

**Size**: `75` lines (`2366` bytes)

**Classes:**
- `class DailyModifier` - *A rule twist applied only to a daily run.*

**Functions:**
- `def daily_modifier(day)` - *Return the deterministic modifier for a date.*
- `def modifier_by_id(modifier_id)` - *Return a modifier by id, or None for normal runs.*
- `def daily_key(day)` - *Return the ISO date key for a daily run.*
- `def daily_seed(day)` - *Return a stable numeric seed derived from the local date.*
- `def daily_run(day)` - *Return the (key, seed) pair for a daily run.*
- `def is_next_day(previous_key, current_key)` - *Return True when current_key is exactly one calendar day after previous_key.*

---

### [`cyberpulse/deckos.py`](cyberpulse/deckos.py)
> *In-game DeckOS computer simulation: processes, sysinfo, uptime, command history.*

**Size**: `144` lines (`6192` bytes)

**Functions:**
- `def _rogue_present(seed, turn, alert)` - *A rogue miner squats on the deck when the grid is hot (deterministic).*
- `def list_processes(engine)` - *Build the DeckOS process table from live engine state.*
- `def sysinfo(engine)` - *Snapshot of the deck as a computer: specs, load, uptime, threat.*
- `def kill_process(engine, pid)` - *Terminate a killable DeckOS process. Rogue miners free CPU; daemons are recalled.*
- `def record_history(engine, cmd_line)` - *Append a command to the run-scoped history (bounded, backfilled).*
- `def recent_history(engine, limit)`

---

### [`cyberpulse/difficulty.py`](cyberpulse/difficulty.py)
> *Difficulty normalization and run modifiers.*

**Size**: `24` lines (`860` bytes)

**Functions:**
- `def normalize_difficulty(value)` - *Return a supported difficulty key, defaulting invalid input to normal.*
- `def trace_multiplier(difficulty)` - *Return the trace gain multiplier for a difficulty.*
- `def contract_multiplier(difficulty)` - *Return the contract payout multiplier for a difficulty.*

---

### [`cyberpulse/engine.py`](cyberpulse/engine.py)
> *Deterministic cyberspace game engine with risk-reward loss aversion and near-miss feedback.*

**Size**: `4482` lines (`214339` bytes)

**Classes:**
- `class GameEngine` - *Manages gameplay rules, push-your-luck risk, and victory/defeat conditions.*
  - Method `.__init__(seed, career_profile, difficulty, daily_modifier, allegiance)`
  - Method `.get_current_node()`
  - Method `._mark_probed(node_id)` - *Record that the runner has mapped a host's services (survives save/load).*
  - Method `._find_quest(quest_id)`
  - Method `._find_contact(contact_id)`
  - Method `._log_story(message)`
  - Method `._sync_story_quests()` - *Auto-accept unlocked main-story quests so the campaign cannot stall.*
  - Method `._contact_trust(contact_id)` - *Trust level for an operative (0 when the contact is missing).*
  - Method `._adjust_trust(contact, delta)` - *Shift an operative's trust, announcing loyalty-arc stage crossings.*
  - Method `._quest_progress_from_state(quest)` - *Progress the world already holds for a one-shot objective.*
  - Method `._reconcile_quest_progress(quest)` - *Credit one-shot events that happened before the quest was accepted.*
  - Method `._complete_quest(quest)` - *Mark a quest complete once, grant its reward, and advance the main story.*
  - Method `._advance_story(act, chapter, reason)`
  - Method `._progress_quests(objective, target, amount)`
  - Method `.is_quest_locked(quest)`
  - Method `._story_gate_reason(node)` - *A story lock the network topology alone does not enforce.*
  - Method `.accept_quest(quest_id)` - *Accept a contact's side quest or expose an unlocked story objective.*
  - Method `._apply_contact_favor(contact)`
  - Method `.interact_contact(contact_id, mode)` - *Talk to an operative, accept their job, or spend their one-time favor.*
  - Method `.ensure_story_state()` - *Backfill story content when loading a save created before story support.*
  - Method `.story_summary()`
  - Method `.world_summary()` - *Return the living-grid snapshot with the newest headlines and hunter telemetry.*
  - Method `.deckos_summary()` - *In-game computer snapshot: sysinfo + process table (Web/CLI DeckOS panel).*
  - Method `.arcs_summary()` - *Operative loyalty-arc tracker for CLI/Web/dossier consumers.*
  - Method `.district_summary()` - *Street-level district simulation rows for the living-grid ticker.*
  - Method `.host_district(node_id)` - *Street-layer address of a host: its district plus live patrol/load/mood.*
  - Method `.offer_district(target_ip, target_node_type)` - *Street address of a contract target for board display.*
  - Method `.node_districts()` - *Compact per-host district tags for Web/CLI consumers.*
  - Method `.news_feed(limit)` - *Return the newest living-grid headlines, oldest first.*
  - Method `.run_summary()` - *Return the terminal (or in-progress) run's legacy for CLI and Web display.*
  - Method `.list_quests()`
  - Method `.list_contacts()`
  - Method `.get_or_create_puzzle(node_id)` - *Return the pending hacking puzzle for a node, creating it only once.*
  - Method `.clear_pending_puzzle(node_id)` - *Discard a solved or exhausted puzzle so the node cannot replay its attempts.*
  - Method `._lockdown_reason(node)` - *Return a denial when a host's ICE is still rotating after a burned intrusion.*
  - Method `.register_puzzle_failure(node_id, reason)` - *Apply the cost of a burned intrusion script: trace, combo loss, and a host lockdown.*
  - Method `.resolve_puzzle_near_miss(puzzle)` - *Record a near miss and convert the first one per puzzle into a bonus attempt.*
  - Method `.mitigated_trace(raw_amount)` - *Return the trace actually added after passive ICE dampener, stance, and proxy mitigation.*
  - Method `.extraction_surge()` - *Black ICE surge applied while pulling the jack, before the link is cut.*
  - Method `.extraction_risk()` - *Preview the extraction surge and whether it would burn an active run.*
  - Method `.combo_rate_preview()` - *Return the current and next-breach combo bonus rates (informational only).*
  - Method `.action_forecast(action, target)` - *Preview CPU/trace/turn costs for one action without mutating any state.*
  - Method `.hop_latency_ms(node)` - *Deterministic per-hop latency: base + security tiers + stable jitter.*
  - Method `.trace_route(target)` - *Trace the hop path from the current host to a target (read-only).*
  - Method `.host_fingerprint(target)` - *Summarize a host's identity: OS, uptime, patch train, ports, staff shifts.*
  - Method `.add_trace(raw_amount)` - *Increase system trace, mitigated by ICE dampeners. 100% triggers lockout & loss of loot.*
  - Method `.regenerate_cpu(amount)` - *Cool down cyberdeck processing units and recover CPU cycles.*
  - Method `.advance_turn()` - *Advance the run clock one turn: daemons harvest, then the living grid reacts.*
  - Method `.refresh_faction_bonuses()` - *Recompute cached faction multipliers from the current standing snapshot.*
  - Method `.shop_price_multiplier()` - *Return the live market index after the Street standing discount.*
  - Method `.daily_modifier_summary()` - *Return the active daily modifier for HUD and archive display.*
  - Method `.tutorial_progress()` - *Return the first-run field manual with live completion flags.*
  - Method `.rival_summary()` - *Return the active rival's public status for HUD and dossier display.*
  - Method `.counter_rival()` - *Burn CPU to trace the rival and postpone their next contract grab.*
  - Method `._tick_rival()` - *Let the rival compete for a posted contract, or probe when the board is empty.*
  - Method `.lay_low(turns)` - *Ghost the connection for a few turns: recover CPU while the grid keeps moving.*
  - Method `.tick_world()` - *Advance the in-game clock, alert, market, ambient events, and grid response.*
  - Method `._intrusion_footprint()` - *Count currently-breached hosts the corporation still has to clean up.*
  - Method `._announce_alert_tier()` - *Report a corporate posture change to the wire and the run log.*
  - Method `._decay_alert(shift_bonus)` - *Cool the grid while trace is low; a hot trace keeps corporate response elevated.*
  - Method `._ambient_district(event_key)` - *Street grounding for ambient grid events: fixed beats keep their home*
  - Method `._apply_ambient_event(event)` - *Apply a rolled ambient grid event to the deck, loot, alert, or topology.*
  - Method `._reveal_frontier_node()` - *Reveal one locked node adjacent to the current host, else any locked node.*
  - Method `._recall_daemons(node_id)` - *Remove player daemons from a host after the grid re-secures it.*
  - Method `.scramble_hunter_radar(turns)` - *Confuse active hunters' tracking algorithms for a number of turns.*
  - Method `.counter_hunter(method)` - *Deploy tactical countermeasures against an active NetWatch Hunter.*
  - Method `.spoof_ip()` - *Reduce active trace level by burning CPU cycles.*
  - Method `.break_combo(reason)` - *Shatter the active combo streak after a detected intrusion failure.*
  - Method `.overdrive()` - *Burn CPU and trace to stack a combo before the next breach.*
  - Method `.scan_surroundings()` - *Scan adjacent nodes to reveal their security level and status.*
  - Method `.can_move_to(target_id)` - *Verify whether the player can transition to target node.*
  - Method `.move_to(target_id)` - *Move player's intrusion session to an adjacent breached node.*
  - Method `.can_hack_node(target_id)` - *Verify whether player cyberdeck meets hardware requirements to attack node.*
  - Method `._contract_rng()` - *Dedicated contract stream so contract generation never shifts reward rolls.*
  - Method `._contract_giver(objective, risk)` - *Pick the operative whose trust and voice fit the job.*
  - Method `._contract_candidates(objective)` - *Return hosts that can still satisfy a fresh job for this objective.*
  - Method `._choose_contract_risk(rng)`
  - Method `._contract_deadline(objective, node, risk, trust, rng)`
  - Method `._activate_contract(contract)` - *Start an accepted job's clock and clear its board shelf life.*
  - Method `._offer_signature(contract)`
  - Method `.reroll_contract_offers(cost)` - *Spend credits to replace the posted board with fresh offers.*
  - Method `._contract_board_size()` - *Offer slots: the Archive's arc (trust 2+) opens one extra slot.*
  - Method `._refresh_contract_offers(exclude_signatures)` - *Expire stale board entries and fill the board with distinct concrete jobs.*
  - Method `._build_contract()` - *Generate a concrete, deadline-bound job from the live grid state.*
  - Method `.dispatch_next_contract()` - *Dispatch and immediately accept a concrete job (legacy/test helper).*
  - Method `.accept_contract(contract_id)` - *Accept a posted offer and start its deadline clock.*
  - Method `.drop_offer(contract_id)` - *Remove one posted offer: pay the broker fee, or take a one-turn cooldown if broke.*
  - Method `.decline_contract()` - *Walk away from the active job: lose giver trust, keep the board stocked.*
  - Method `._contract_targets_node(contract, node)`
  - Method `._contract_completes_on_breach(contract, node)` - *Return True when a node breach satisfies a contract without extra objectives.*
  - Method `._contract_download_matches(contract, node, vfile)` - *Return True when this download advances the active contract.*
  - Method `._contract_recon_matches(contract, node)`
  - Method `._contract_wipe_ready(contract, node)`
  - Method `._contract_payout(contract)` - *Return (total, trust_bonus, rush_bonus) for a completed job.*
  - Method `._finalize_contract(contract, node)` - *Pay a completed job once, reward its giver's trust, and dispatch the next job.*
  - Method `._fail_contract(contract)` - *Expire a job, cost its giver trust, raise heat, and post the next contract.*
  - Method `._check_contract_clock()` - *Warn near a deadline, expire a missed job, and rotate the offer board.*
  - Method `.complete_breach(node_id)` - *Mark node as breached, evaluate variable-ratio rewards, and check contracts.*
  - Method `.use_exploit(exploit_name, target_id)` - *Deploy an executable exploit chip loaded in cyberdeck firmware.*
  - Method `.jackout()` - *Push-Your-Luck extraction: safely bank all unbanked credits and looted payloads.*
  - Method `.settle_career(profile)` - *Apply a finished run's outcome to the persistent profile exactly once.*
  - Method `.find_node(query)` - *Lookup node by node_id, ip_address, or hostname.*
  - Method `.probe_host(target_query)` - *Perform network port scan (nmap-style) against a target IP, hostname, or node_id.*
  - Method `.exploit_service(target_query, port_num, cve_id)` - *Launch an exploit payload (generic zero-day or targeted CVE) against an open service port on target host.*
  - Method `.list_files(target_query)` - *List files (ls) on target host's virtual filesystem (requires host to be breached).*
  - Method `.read_file(target_query, file_path)` - *Read file contents (cat) on breached host.*
  - Method `.download_file(target_query, file_path)` - *Download / steal data file from breached host (yields unbanked credits and fulfills bounties).*
  - Method `.wipe_logs(target_query)` - *Clear access logs (wipe_logs) on target host to reduce active trace by 20% and fulfill clean escape clauses.*
  - Method `.tick_daemons()` - *Process active background malware daemons (e.g. keyloggers) and host antivirus sweeps.*
  - Method `.deploy_daemon(target_query, daemon_type)` - *Deploy an in-game background malware listener daemon onto a breached host.*
  - Method `.list_local_files()` - *List files (ls) stored on player's local cyberdeck rig (localhost).*
  - Method `.read_local_file(file_path)` - *Read content (cat) of a file on player's local cyberdeck rig.*
  - Method `._social_success_chance(node, vector_key, emp)` - *Deterministic lure odds shared by execution and forecast (no roll).*
  - Method `.social_engineer(target_query, vector, employee_name)` - *Launch an interactive social engineering attack (pretext, bait, spear_phish, vishing) against target employees.*
  - Method `.phish_target(target_query)` - *Dispatch a simulated social engineering spear-phishing campaign to target host employees (backward compatible).*
  - Method `.get_firewall_status(target_query)` - *Inspect the network firewall rules defending a target host.*
  - Method `.bypass_firewall(target_query, port, method)` - *Execute a firewall bypass against a blocked port via port-knocking, packet fragmentation, or proxy-tunneling.*
  - Method `.get_antivirus_status(target_query)` - *Inspect the active Antivirus / EDR status on a target host.*
  - Method `.evade_antivirus(target_query, method)` - *Inject a stealth evasion hook or memory-patch into a target host's Antivirus suite.*
  - Method `.list_cves()` - *Return the catalog of weaponized CVE exploit payloads.*
  - Method `.craft_virus(recipe_name)` - *Assemble a custom virus chip in the netrunner workshop.*
  - Method `.list_crafting_recipes()` - *List available malware crafting recipes in the workshop.*
  - Method `.spend_threat_intel(mode, target_query)` - *Burn ANALYSIS-stance threat intel for a tactical edge.*
  - Method `.set_stance(stance_query)` - *Switch cyberdeck operating bus stance: balanced, stealth, overclock, analysis.*
  - Method `.add_proxy_hop(node_query)` - *Route neural telemetry through a compromised host to dampen trace buildup.*
  - Method `.sever_proxy(node_query)` - *Burn a proxy tunnel connection to dump 15% trace immediately.*
  - Method `.quickhack(target_query)` - *Instant-breach an adjacent low-security host at a steep CPU and trace cost.*

---

### [`cyberpulse/factions.py`](cyberpulse/factions.py)
> *Faction standing normalization and bounded reputation bonuses.*

**Size**: `102` lines (`3524` bytes)

**Functions:**
- `def normalize_allegiance(value)` - *Return a supported run allegiance, defaulting unknown values to none.*
- `def allegiance_contract_bonus(allegiance)` - *Return the Syndicate patron contract bonus.*
- `def allegiance_shop_discount(allegiance)` - *Return the Street patron Black Market discount.*
- `def normalize_standing(data)` - *Return a clean two-faction standing map with non-negative capped integers.*
- `def update_standing(standing, faction, delta)` - *Add reputation to one faction and return a normalized copy.*
- `def rank_for(faction, standing)` - *Return (rank index, rank name, promotion reward) for a faction standing.*
- `def rank_up_reward(faction, old_standing, new_standing)` - *Return (rank name, reward) when a settlement crosses a rank threshold.*
- `def contract_bonus(standing)` - *Return the Syndicate contract-pay bonus (1% per point, capped at 20%).*
- `def street_discount(standing)` - *Return the Street Black Market discount (1% per point, capped at 15%).*

---

### [`cyberpulse/models.py`](cyberpulse/models.py)
> *Domain models for CyberPulse cyberspace nodes, decks, contracts, and career profiles.*

**Size**: `843` lines (`32083` bytes)

**Classes:**
- `class NodeType`
- `class NodeStatus`
- `class RewardType`
- `class OperatingStance`
- `class PortService` - *An exposed TCP/UDP network service on a target host.*
  - Method `.to_dict()`
  - Method `.from_dict(data)`
- `class VirtualFile` - *A file stored on a target host's virtual filesystem.*
  - Method `.to_dict()`
  - Method `.from_dict(data)`
- `class BountyContract` - *A syndicate-issued objective with bonus rewards upon fulfillment (Zeigarnik Effect).*
  - Property `.objective_kind` - *Return the explicit objective, or infer it from legacy contract fields.*
  - Method `.to_dict()`
  - Method `.from_dict(data)`
- `class CareerProfile` - *Persistent meta-progression profile tracking permanent stats and upgrades.*
  - Method `.to_dict()`
  - Method `.from_dict(data)`
- `class RivalNetrunner` - *A named competitor who works the same Syndicate board during a run.*
  - Method `.to_dict()`
  - Method `.from_dict(data)`
- `class FirewallPolicy`
- `class FirewallRule` - *A packet filtering or port access rule enforced by a host firewall.*
  - Method `.to_dict()`
  - Method `.from_dict(data)`
- `class HostFirewall` - *A network firewall defending a host's open ports against unauthorized ingress.*
  - Method `.is_port_blocked(port)`
  - Method `.to_dict()`
  - Method `.from_dict(data)`
- `class HostAntivirus` - *An active endpoint detection and response (EDR) / antivirus service on a target host.*
  - Method `.to_dict()`
  - Method `.from_dict(data)`
- `class ExploitPayload` - *A weaponized vulnerability exploit / CVE targeting specific network services.*
  - Method `.to_dict()`
  - Method `.from_dict(data)`
- `class SocialVectorType`
- `class SecurityAwarenessLevel`
- `class EmployeeProfile` - *Target organization employee persona susceptible to social engineering attacks.*
  - Method `.to_dict()`
  - Method `.from_dict(data)`
- `class Node` - *A target host or infrastructure subsystem on the network grid.*
  - Method `.to_dict()`
  - Method `.from_dict(data)`
- `class MalwareDaemon` - *An active background script deployed on a compromised host (e.g. keylogger, siphon).*
  - Method `.to_dict()`
  - Method `.from_dict(data)`
- `class VirusCraftRecipe` - *A crafting recipe to synthesize custom virus/malware chips in the netrunner workshop.*
  - Method `.to_dict()`
  - Method `.from_dict(data)`
- `class CyberDeck` - *The player's hardware deck used to execute hacking exploits.*
  - Method `.to_dict()`
  - Method `.from_dict(data)`
- `class Quest` - *A tracked story or side objective with a reward.*
  - Property `.ready`
  - Method `.to_dict()`
  - Method `.from_dict(data)`
- `class ContactProfile` - *A persistent in-game operative the player can talk to, work for, and call favors on.*
  - Property `.trust_tier`
  - Method `.to_dict()`
  - Method `.from_dict(data)`
- `class NewsItem` - *A single living-grid headline generated by world events.*
  - Method `.to_dict()`
  - Method `.from_dict(data)`
- `class NetWatchHunter` - *An autonomous NetWatch counter-infiltration agent tracking the player across subnets.*
  - Method `.to_dict()`
  - Method `.from_dict(data)`
- `class WorldState` - *Living-grid simulation: in-game clock, corporate alert, market drift, news, and hunters.*
  - Method `.to_dict()`
  - Method `.from_dict(data)`
- `class GameState` - *The full runtime state of a CyberPulse infiltration run.*
  - Method `.to_dict()`
  - Method `.from_dict(data)`

**Functions:**
- `def node_visual(node_type, status)` - *Return presentation metadata for a node type + status pair.*
- `def entity_visual(key)` - *Return presentation metadata for contacts, rivals, hunters, shop, puzzles.*
- `def apply_career_profile(deck, profile)` - *Apply persistent upgrades and synchronize banked funds into an active cyberdeck.*

---

### [`cyberpulse/network.py`](cyberpulse/network.py)
> *Procedural cyberspace network generator with deterministic topology.*

**Size**: `478` lines (`22352` bytes)

**Functions:**
- `def host_fingerprint_fields(rng, node_type, security)` - *Derive deterministic host identity: OS, uptime, and patch train.*
- `def generate_network(seed)` - *Generate a deterministic cyberspace infiltration network grid from seed.*
- `def _generate_side_hosts(rng, nodes)` - *Attach 2-3 seeded side hosts to the fixed campaign spine.*

---

### [`cyberpulse/puzzles.py`](cyberpulse/puzzles.py)
> *Interactive and deterministic cyberpunk hacking mini-game puzzles with near-miss feedback.*

**Size**: `198` lines (`7998` bytes)

**Classes:**
- `class FrequencyPuzzle` - *Tuning resonance frequency puzzle with near-miss feedback mechanics.*
  - Method `.__init__(target_freq, tolerance)`
  - Method `.claim_near_miss_bonus()` - *Convert the first near miss into one extra tuning attempt.*
  - Method `.to_dict()`
  - Method `.from_dict(data)`
  - Method `.generate(seed)`
  - Method `.tune(guess)` - *Test a frequency guess with near-miss detection.*
- `class BufferPuzzle` - *Memory buffer sequence matching puzzle with partial alignment detection.*
  - Method `.__init__(matrix, target_seq)`
  - Method `.claim_near_miss_bonus()` - *Convert the first near miss into one free retry before the host locks down.*
  - Method `.to_dict()`
  - Method `.from_dict(data)`
  - Method `.generate(seed)`
  - Method `.verify_sequence(player_seq)` - *Verify whether player's sequence matches with near-miss feedback.*
- `class HashCrackPuzzle` - *Cryptographic password / hash cracking cipher puzzle with single-letter near miss.*
  - Method `.__init__(target_word, word_list)`
  - Method `.claim_near_miss_bonus()` - *Convert the first character-level near miss into one extra keyword attempt.*
  - Method `.to_dict()`
  - Method `.from_dict(data)`
  - Method `.generate(seed)`
  - Method `.guess(candidate)` - *Evaluate a guess and return matching character count with near-miss detection.*

**Functions:**
- `def puzzle_from_dict(data)` - *Restore a persisted puzzle payload, or None when the type is unknown.*

---

### [`cyberpulse/rewards.py`](cyberpulse/rewards.py)
> *Variable-ratio reward engine and dopamine loot schedules for CyberPulse.*

**Size**: `39` lines (`1312` bytes)

**Functions:**
- `def roll_breach_reward(node, rng)` - *Calculate variable-ratio reward payout and drops (Skinner box reinforcement schedule).*

---

### [`cyberpulse/rivals.py`](cyberpulse/rivals.py)
> *Deterministic rival-netrunner generation.*

**Size**: `61` lines (`1763` bytes)

**Functions:**
- `def generate_rival(seed)` - *Create the run's rival from a deterministic seed stream.*
- `def rival_move_delay(skill, story_act, jitter)` - *Deterministic rival board delay: skill base, act pressure, RNG jitter.*

---

### [`cyberpulse/scoring.py`](cyberpulse/scoring.py)
> *Transparent run scoring for legacy and Hall of Fame rankings.*

**Size**: `26` lines (`861` bytes)

**Functions:**
- `def score_run(*, gained, best_combo, quests_done, nodes_breached, outcome, contract_completed, main_story_complete)` - *Return a score and its itemized breakdown for one settled run.*

---

### [`cyberpulse/server.py`](cyberpulse/server.py)
> *Zero-dependency HTTP REST backend and static file server for CyberPulse Web Cyberdeck.*

**Size**: `1045` lines (`46858` bytes)

**Classes:**
- `class CyberdeckSession` - *Encapsulates the stateful game session driving the Web Cyberdeck interface.*
  - Method `.__init__(data_dir, seed, daily_key, difficulty, daily_modifier, allegiance)`
  - Method `.settle_run_if_finished()` - *Persist a victory/lockout exactly once as soon as the run reaches a terminal state.*
  - Method `.get_full_state()` - *Aggregate complete runtime state for frontend rendering.*
  - Method `.reset_game(seed, daily, difficulty, allegiance)`
  - Method `.save_run(slot, name)` - *Persist the live run to a manual slot with the terminal's atomic manager.*
  - Method `.rename_save(slot, name)` - *Rename an existing manual checkpoint without changing the run.*
  - Method `.reset_career()` - *Back up and delete the career plus all saves, then start a fresh run.*
  - Method `.rename_alias(name)` - *Persist a new career alias after trimming and capping it.*
  - Method `.delete_save(slot)` - *Delete a checkpoint from the archive without touching the live run.*
  - Method `.load_run(slot)` - *Replace the live engine with a saved run from the requested slot.*
- `class CyberdeckHTTPHandler` - *HTTP request handler providing REST API endpoints and static cyberdeck assets.*
  - Method `.log_message(format, *args)` - *Route cyberdeck request logs without cluttering console.*
  - Method `.send_json_response(data, status)`
  - Method `.do_OPTIONS()`
  - Method `.do_GET()`
  - Method `._do_get()`
  - Method `.serve_static(path)`
  - Method `.do_POST()`
  - Method `._do_post(path, payload)`

**Functions:**
- `def coerce_seed(value)` - *Convert API/CLI seed input to an integer, rejecting non-finite or non-numeric values.*
- `def create_server(host, port, data_dir, seed, daily_key, difficulty, daily_modifier, allegiance)` - *Instantiate and configure the ThreadingHTTPServer for CyberPulse Web Cyberdeck.*
- `def run_web(host, port, data_dir, seed, open_browser, daily_key, difficulty, daily_modifier, allegiance)` - *Launch the Web Cyberdeck server and optionally launch default system web browser.*

---

### [`cyberpulse/shop.py`](cyberpulse/shop.py)
> *Black market cyberdeck upgrades and exploit vendor for CyberPulse.*

**Size**: `167` lines (`6301` bytes)

**Classes:**
- `class ShopItem`
- `class BlackMarketShop` - *Manages purchasing of cyberdeck hardware upgrades and exploit chips.*
  - Method `.__init__(catalog)`
  - Method `.price_for(item, price_multiplier)` - *Effective cost after living-grid market drift, never below 1 Cred.*
  - Method `.list_available(deck, price_multiplier)` - *List all shop items and current upgrade status at the current market price.*
  - Method `.purchase(deck, item_id, price_multiplier)` - *Attempt to buy an item at the current market price and apply its stat bonuses.*

---

### [`cyberpulse/storage.py`](cyberpulse/storage.py)
> *Crash-resilient savegame and career profile storage engine for CyberPulse.*

**Size**: `418` lines (`18255` bytes)

**Classes:**
- `class SaveManager` - *Manages atomic saving and loading of game states and career profiles.*
  - Method `.__init__(data_dir)`
  - Method `.normalize_slot(slot)` - *Return a canonical slot key: '1', '2', '3' or 'auto'.*
  - Method `.slot_path(slot)` - *Map a slot key to its atomic save file, keeping slot 1 backward compatible.*
  - Method `.slot_label(slot)` - *Return a human-readable label for a slot.*
  - Method `._slot_exists(key)`
  - Method `._is_readable_json(path)` - *Return True when a file parses as JSON, so a corrupt primary never replaces a good backup.*
  - Method `._write_atomic(target_path, data)` - *Write JSON payload to target_path atomically; returns None when the replace never lands.*
  - Method `._read_json_with_backup(target_path, quarantine)` - *Read JSON from target_path, falling back to shadow .bak if corrupted or missing.*
  - Method `._read_slot_payload(key, quarantine)`
  - Method `.has_save(slot)` - *Return True when any slot (or the requested slot) has a save or shadow backup.*
  - Method `.clean_name(name)` - *Normalize a slot label to one line and cap it for the archive UI.*
  - Method `.save(engine, slot, name)` - *Atomically persist engine state to a manual slot or the autosave slot.*
  - Method `.claim_slot(slot)` - *Record that this interface owns a slot and may purge it when the run settles.*
  - Method `.rename_slot(slot, name)` - *Rename an existing manual checkpoint without changing its run progress or timestamp.*
  - Method `.load(slot)` - *Load and restore engine state from a slot with backup recovery.*
  - Method `._signature(engine)` - *Hash the parts of a run that autosave should notice without rewriting unchanged state.*
  - Method `.mark_autosave_baseline(engine)` - *Remember the current state so a new or freshly loaded run is not written before it changes.*
  - Method `.autosave(engine)` - *Write the autosave slot once per state change; terminal runs are never saved.*
  - Method `.list_saves()` - *Return metadata for every restorable slot, newest first.*
  - Method `.delete_save(slot)` - *Remove a slot's savegame and its shadow backup.*
  - Method `.delete_run(run_id)` - *Purge this interface's owned checkpoints of a settled run, leaving other runs untouched.*
  - Method `.backup_career()` - *Copy the current career payload to career.backup.json before a reset.*
  - Method `.delete_career()` - *Remove the active career profile and its shadow backup.*
  - Method `.delete_all_saves()` - *Remove every manual slot and the autosave checkpoint.*
  - Method `.save_career(profile)` - *Atomically persist career meta-progression profile.*
  - Method `.load_career()` - *Load persistent career profile with backup recovery or return fresh profile.*

**Functions:**
- `def encode_rng_state(state)` - *Convert a random.Random state tuple into a JSON-safe payload.*
- `def decode_rng_state(payload)` - *Restore a random.Random state tuple from a persisted payload.*

---

### [`cyberpulse/story.py`](cyberpulse/story.py)
> *Story acts, quest blueprints, and operative dialogue for CyberPulse.*

**Size**: `310` lines (`12460` bytes)

**Functions:**
- `def initial_quests()` - *Return the persistent quest board for a new run.*
- `def initial_contacts()` - *Return the operatives available to a new run.*
- `def act_title(act)`
- `def dialogue_for(contact_id, act, choice)`
- `def trust_dialogue_for(contact_id, tier)`

---

### [`cyberpulse/tutorial.py`](cyberpulse/tutorial.py)
> *State-driven first-run field manual.*

**Size**: `38` lines (`1399` bytes)

**Functions:**
- `def tutorial_steps(engine)` - *Return the five core-loop steps annotated with live completion state.*

---

### [`cyberpulse/world.py`](cyberpulse/world.py)
> *Living-grid world simulation: in-game clock, corporate alert, news, and grid response.*

**Size**: `558` lines (`18934` bytes)

**Classes:**
- `class ShiftProfile` - *Tactical posture of the grid during one in-game shift.*
- `class AmbientEvent` - *A deterministic grid event that can nudge credits, CPU, trace, alert, or topology.*

**Functions:**
- `def alert_tier(alert_level)` - *Return the named corporate response posture for a grid alert level.*
- `def tier_rank(tier)` - *Return the ordering index of a named alert tier (GREEN=0 .. BLACK=3).*
- `def world_rng(seed, tick, stream)` - *Return a deterministic per-tick RNG stream independent of the engine reward RNG.*
- `def clamp(value, low, high)`
- `def clock_minute_text(minute)` - *Render an in-game minute of day as HH:MM.*
- `def shift_name(minute)` - *Return the named shift covering an in-game minute of day.*
- `def shift_profile(minute)` - *Return the tactical profile of the shift covering an in-game minute of day.*
- `def shift_effect_text(profile)` - *Render a compact human-readable summary of a shift's mechanical modifiers.*
- `def social_shift_modifier(minute)` - *Return how much the current shift helps or hinders social engineering.*
- `def apply_social_shift(chance, minute)` - *Blend a base social-engineering chance with the shift modifier, clamped to 5-95%.*
- `def clock_label(world)` - *Return a compact clock label such as ``Day 2 13:45 (Afternoon)``.*
- `def record_news(world, tick, source, headline, tone)` - *Append a headline to the living-grid feed, keeping the newest entries.*
- `def format_news_item(item)`
- `def advance_clock(world, turns)` - *Advance the in-game clock, rolling over to the next day at midnight.*
- `def adjust_alert(world, delta)` - *Raise or lower the grid-wide corporate alert level within 0-100.*
- `def adjust_market(world, delta)` - *Nudge the black-market price multiplier within its bounds.*
- `def drift_market(world, rng, bias)` - *Random-walk the black market, pulled toward a shift-biased target while the grid is hot.*
- `def market_multiplier(world)` - *Current black-market price multiplier applied to shop costs.*
- `def patrol_pressure(world)` - *Trace added per turn by NetWatch patrol sweeps at higher alert levels.*
- `def ambient_event_for(seed, tick, alert_level, turns_since_event)` - *Roll one deterministic ambient event for a world tick, or None for a quiet turn.*
- `def plan_resecures(seed, tick, alert_level, nodes, current_node_id, chance_delta)` - *Choose hosts the grid re-secures this tick: hot grid, cooled-down, looted targets.*
- `def apply_resecure(node)` - *Undo a breach in place and restore the host's defensive posture.*
- `def find_shortest_path(nodes, start_id, goal_id)` - *Find the shortest unweighted path of node IDs from start_id to goal_id using BFS.*
- `def calculate_distance(nodes, start_id, goal_id)` - *Return the hop distance between start_id and goal_id, or -1 if unreachable.*
- `def deploy_hunter(world, nodes, tick)` - *Deploy an active NetWatch Hunter if the shift-adjusted alert threshold is met and none is active.*
- `def step_hunter(hunter, nodes, player_node_id, rng)` - *Advance the hunter by 1 hop along the network graph towards the player or random neighbor if confused.*
- `def neutralize_hunter(hunter, reason)` - *Neutralize an active NetWatch hunter.*
- `def world_summary(world)` - *Serialize the living-grid snapshot for CLI and Web consumers.*

---

### [`start.py`](start.py)
> *Zero-friction launcher for CyberPulse terminal and Web Cyberdeck.*

**Size**: `28` lines (`744` bytes)

**Functions:**
- `def start(argv)` - *Launch the Web Cyberdeck by default, or forward custom CLI arguments.*

---

### [`tests/__init__.py`](tests/__init__.py)
> *Test suite for CyberPulse.*

**Size**: `1` lines (`33` bytes)

---

### [`tests/test_achievements.py`](tests/test_achievements.py)
> *Unit tests for career milestone evaluation and catalog integrity.*

**Size**: `113` lines (`4216` bytes)

**Classes:**
- `class TestAchievements`
  - Method `.setUp()`
  - Method `.test_catalog_ids_are_unique_and_described()`
  - Method `.test_catalog_status_marks_unlocked_entries()`
  - Method `.test_combo_milestones_unlock_at_their_thresholds()`
  - Method `.test_victory_conditions_unlock_ghost_and_speed()`
  - Method `.test_contract_vault_and_economy_conditions()`
  - Method `.test_hot_extraction_and_veteran_conditions()`
  - Method `.test_hard_clear_requires_a_hard_victory()`
  - Method `.test_daily_streak_milestones()`
  - Method `.test_faction_insider_at_ten_standing()`
  - Method `.test_unlocks_are_not_returned_twice()`

---

### [`tests/test_arc_mechanics.py`](tests/test_arc_mechanics.py)
> *Live arc bonuses + district sweep mechanics (Cyberpulse 0.5.0).*

**Size**: `461` lines (`21307` bytes)

**Classes:**
- `class ArcMechanicsTest`
  - Method `.setUp()`
  - Method `.test_zero_arc_discounts_counter_rival()`
  - Method `.test_zero_arc_counter_needs_only_one_cpu()`
  - Method `.test_kilo_arc_boosts_daemon_yield()`
  - Method `.test_archivist_arc_deepens_wipe()`
  - Method `.test_mira_arc_cools_grid_on_syndicate_contract()`
  - Method `.test_mira_arc_needs_syndicate_contract()`
  - Method `.test_district_sweep_adds_trace_under_black_alert()`
  - Method `.test_district_grid_matches_hashlib_reference()`
  - Method `.test_live_bonuses_reflect_trust_and_contract()`
  - Method `.test_arc_epilogues_fire_only_at_stage_three()`
  - Method `.test_run_summary_carries_arc_epilogues()`
  - Method `.test_adjust_trust_announces_stage_crossings()`
  - Method `.test_adjust_trust_silent_without_crossing()`
  - Method `.test_adjust_trust_floors_at_minus_one()`
  - Method `.test_accept_quest_carries_arc_unlock()`
  - Method `.test_archivist_arc_opens_extra_offer_slot()`
  - Method `.test_arc_status_carries_bonus_text()`
  - Method `.test_talk_names_the_loyalty_arc()`
  - Method `.test_kilo_arc_discounts_overdrive()`
  - Method `.test_overdrive_forecast_reflects_kilo_arc()`
  - Method `.test_contact_channels_carry_arc_stage()`
  - Method `.test_mira_arc_extends_rush_window()`
  - Method `.test_mira_arc_covers_declines()`
  - Method `.test_kilo_arc_adds_street_standing_on_victory()`
  - Method `.test_zero_arc_forecasts_black_ice()`
  - Method `.test_zero_arc_extends_choice_epilogue()`
  - Method `.test_district_for_node_is_stable()`
  - Method `.test_district_summary_partitions_all_hosts()`
  - Method `.test_breach_in_heavy_district_adds_heat()`
  - Method `.test_breach_outside_heavy_districts_adds_no_heat()`
  - Method `.test_probe_report_carries_district()`
  - Method `.test_hunter_deployment_names_its_district()`
  - Method `.test_hunter_clash_names_the_grid()`
  - Method `.test_deckos_probe_names_hunter_district()`
  - Method `.test_offer_district_maps_targets_to_streets()`
  - Method `.test_resecure_names_the_district_grid()`
  - Method `.test_intel_reveal_names_the_district()`
  - Method `.test_run_summary_tracks_district_coverage()`
  - Method `.test_ambient_events_name_their_district()`
  - Method `.test_reveal_effect_names_the_district()`
  - Method `.test_move_across_districts_announces_the_crossing()`

**Functions:**
- `def _quiet(engine)` - *Neutralize ambient/rival randomness for deterministic tick assertions.*

---

### [`tests/test_cli.py`](tests/test_cli.py)
> *Integration tests for CyberPulse CLI.*

**Size**: `670` lines (`28037` bytes)

**Classes:**
- `class TestCLI`
  - Method `.setUp()`
  - Method `.run_cli(*args)`
  - Method `.test_cli_help()`
  - Method `.test_main_menu_quit()`
  - Method `.test_main_menu_starts_run_then_quits()`
  - Method `.test_contract_briefing_and_job_clock()`
  - Method `.test_contract_expiry_is_surfaced_in_cli()`
  - Method `.test_decline_contract_command_opens_the_board()`
  - Method `.test_story_quests_contacts_and_overdrive_commands()`
  - Method `.test_world_news_commands_and_hud_grid_line()`
  - Method `.test_lay_low_command_and_shift_doctrine()`
  - Method `.test_lay_low_rejects_bad_turn_count()`
  - Method `.test_shop_command_reports_market_index()`
  - Method `.test_agent_zero_alliance_after_act_three()`
  - Method `.test_jackout_records_best_combo_in_career()`
  - Method `.test_contact_job_and_favor_commands()`
  - Method `.test_batch_infiltration_playthrough()`
  - Method `.test_batch_named_slot_round_trip()`
  - Method `.test_saves_command_lists_manual_slots()`
  - Method `.test_named_slot_round_trip_and_rename()`
  - Method `.test_delete_slot_command_requires_an_explicit_slot()`
  - Method `.test_batch_commands_autosave_state_changes()`
  - Method `.test_invalid_save_slot_reports_usage()`
  - Method `.test_jackout_purges_owned_slots_and_autosave()`
  - Method `.test_replay_starts_a_run_from_an_archived_seed()`
  - Method `.test_replay_rejects_an_out_of_range_index()`
  - Method `.test_rival_commands_inspect_and_counter()`
  - Method `.test_career_dossier_shows_faction_standing()`
  - Method `.test_reset_career_aborts_if_the_backup_write_fails()`
  - Method `.test_reset_career_requires_confirmation_and_backs_up()`
  - Method `.test_alias_command_persists_and_shows_in_the_dossier()`
  - Method `.test_hall_command_filters_by_difficulty()`
  - Method `.test_tutorial_command_lists_the_first_run_steps()`
  - Method `.test_reroll_command_spends_credits_and_refills_the_board()`
  - Method `.test_allegiance_flag_reaches_the_hud()`
  - Method `.test_difficulty_flag_reaches_the_hud()`
  - Method `.test_daily_flag_uses_the_date_seed()`
  - Method `.test_daily_career_dossier_shows_the_streak()`
  - Method `.test_dead_mans_switch_does_not_become_a_career_upgrade()`
  - Method `.test_career_dossier_lists_recent_runs()`
  - Method `.test_jackout_command()`
  - Method `.test_shop_and_buy_command()`
  - Method `.test_career_progression_across_sessions()`
  - Method `.test_exploit_command()`
  - Method `.test_ram_insufficient_message_in_cli()`
  - Method `.test_simulation_cli_workflow()`
  - Method `.test_cli_virtual_rig_and_phishing_commands()`
  - Method `.test_cli_cyber_warfare_commands()`
  - Method `.test_handle_run_completion_in_batch_mode()`
  - Method `.test_lifetime_creds_not_double_counted()`
  - Method `.test_bypass_rejects_non_numeric_port()`
  - Method `.test_minigame_eof_stops_batch_without_traceback()`
  - Method `.test_cli_reuses_pending_puzzle_attempts()`
  - Method `.test_failed_puzzle_breaks_combo()`
  - Method `.test_cli_hunter_and_counter_commands()`
  - Method `.test_unknown_command_reports_and_tactical_commands_run()`
  - Method `.test_start_launcher_function()`

---

### [`tests/test_daily.py`](tests/test_daily.py)
> *Unit tests for deterministic daily-run keys and seeds.*

**Size**: `55` lines (`1811` bytes)

**Classes:**
- `class TestDailyRun`
  - Method `.test_key_and_seed_are_stable_for_a_date()`
  - Method `.test_different_days_produce_different_seeds()`
  - Method `.test_daily_modifier_is_stable_and_from_the_table()`
  - Method `.test_daily_modifier_changes_across_the_roster()`
  - Method `.test_next_day_detection_handles_gaps_and_bad_keys()`

---

### [`tests/test_deckos_arcs.py`](tests/test_deckos_arcs.py)
> *DeckOS computer simulation + operative arcs + district sim (Cyberpulse 0.5.0).*

**Size**: `108` lines (`4091` bytes)

**Classes:**
- `class DeckOSTest`
  - Method `.setUp()`
  - Method `.test_process_table_has_base_system_procs()`
  - Method `.test_sysinfo_reports_uptime_and_specs()`
  - Method `.test_kill_unknown_pid_fails()`
  - Method `.test_kill_protected_proc_fails()`
  - Method `.test_history_roundtrip()`
  - Method `.test_engine_summaries_present()`
- `class ArcsTest`
  - Method `.setUp()`
  - Method `.test_arc_stages_start_at_zero()`
  - Method `.test_arc_stage_thresholds()`
  - Method `.test_arc_quests_backfilled_for_new_runs()`
  - Method `.test_arc_quests_backfilled_for_old_saves()`
  - Method `.test_district_grid_deterministic()`
- `class CLIParityTest`
  - Method `.test_deckos_arcs_districts_forecast_commands()`

---

### [`tests/test_difficulty.py`](tests/test_difficulty.py)
> *Unit tests for difficulty normalization and modifiers.*

**Size**: `25` lines (`1039` bytes)

**Classes:**
- `class TestDifficulty`
  - Method `.test_normalization_defaults_unknown_values()`
  - Method `.test_trace_multipliers_order_by_difficulty()`
  - Method `.test_contract_multipliers_favor_easy_and_tax_hard()`

---

### [`tests/test_engine.py`](tests/test_engine.py)
> *Unit tests for CyberPulse game engine.*

**Size**: `2187` lines (`92412` bytes)

**Classes:**
- `class TestEngine`
  - Method `.setUp()`
  - Method `.test_initial_state()`
  - Method `.test_scan_reveals_connected()`
  - Method `.test_cannot_move_to_unbreached_node()`
  - Method `.test_breach_and_move()`
  - Method `.test_trace_lockout_burns_unbanked_loot()`
  - Method `.test_jackout_safely_banks_loot()`
  - Method `.test_jackout_previews_black_ice_surge_bands()`
  - Method `.test_ice_dampener_can_make_hot_extraction_survivable()`
  - Method `.test_jackout_applies_survivable_surge_and_banks()`
  - Method `.test_jackout_above_85_percent_can_burn_the_run()`
  - Method `.test_download_after_grid_lockout_does_not_pay()`
  - Method `.test_bypass_after_grid_lockout_leaves_rule_blocked()`
  - Method `.test_social_after_grid_lockout_leaves_security_intact()`
  - Method `.test_brute_miner_burn_consumes_chip_without_crediting()`
  - Method `.test_ice_dampener_reduces_trace_gain()`
  - Method `.test_bounty_contract_fulfillment()`
  - Method `.test_generated_contracts_are_concrete_and_deterministic()`
  - Method `.test_contract_deadline_warns_then_expires()`
  - Method `.test_initial_offer_board_contains_three_distinct_jobs()`
  - Method `.test_accept_contract_starts_deadline_and_refills_board()`
  - Method `.test_decline_contract_costs_trust_without_alert()`
  - Method `.test_drop_offer_costs_broker_fee_and_refills()`
  - Method `.test_player_contract_actions_clear_stale_tick_notice()`
  - Method `.test_offer_shelf_life_rotates_the_board()`
  - Method `.test_recon_fallback_jobs_fill_an_exhausted_grid()`
  - Method `.test_contract_payout_includes_trust_and_rush()`
  - Method `.test_breach_contract_requires_its_named_target()`
  - Method `.test_extract_contract_requires_named_file_and_stealth()`
  - Method `.test_contract_expiry_is_not_missed_by_download_tick()`
  - Method `.test_wipe_contract_can_sign_off_after_cooling()`
  - Method `.test_cpu_regeneration()`
  - Method `.test_ram_capacity_check()`
  - Method `.test_use_exploit_ghost_protocol()`
  - Method `.test_use_exploit_logic_bomb()`
  - Method `.test_use_exploit_brute_miner()`
  - Method `.test_find_node_by_ip_and_hostname()`
  - Method `.test_probe_host()`
  - Method `.test_exploit_service()`
  - Method `.test_virtual_filesystem_simulation()`
  - Method `.test_loot_payout_follows_the_market()`
  - Method `.test_loot_payout_discounts_at_cold_market()`
  - Method `.test_loot_fencing_never_pays_zero_for_valuable_data()`
  - Method `.test_wipe_logs_trace_reduction()`
  - Method `.test_local_deck_filesystem_and_loot_archiving()`
  - Method `.test_phishing_dispatch()`
  - Method `.test_craft_virus_workshop()`
  - Method `.test_deploy_and_tick_keylogger_daemon()`
  - Method `.test_daemon_ids_stay_unique_after_a_removal()`
  - Method `.test_daemon_yield_scales_with_host_security()`
  - Method `.test_firewall_inspection_and_bypass()`
  - Method `.test_antivirus_status_and_evasion()`
  - Method `.test_cve_catalog_and_exploit_execution()`
  - Method `.test_new_cve_rows_cover_live_side_services()`
  - Method `.test_social_engineering_vectors()`
  - Method `.test_social_chance_follows_the_shift()`
  - Method `.test_game_over_and_jacked_out_guards()`
  - Method `.test_defensive_input_sanitization()`
  - Method `.test_exploit_service_turn_advancement()`
  - Method `.test_complete_breach_is_idempotent()`
  - Method `.test_worm_replicator_rejects_breached_target_without_consuming_chip()`
  - Method `.test_spoof_reports_actual_reduction()`
  - Method `.test_spoof_rejects_zero_trace_without_burning_cpu()`
  - Method `.test_tick_daemons_stops_after_lockout()`
  - Method `.test_bypass_and_evade_require_direct_subnet()`
  - Method `.test_social_engineering_requires_direct_subnet()`
  - Method `.test_wipe_logs_is_idempotent()`
  - Method `.test_probe_advances_daemon_tick()`
  - Method `.test_pending_puzzle_keeps_attempts_between_calls()`
  - Method `.test_failed_puzzle_seals_host_and_escalates_failure_cost()`
  - Method `.test_critical_trace_warning_is_not_counted_as_a_near_miss()`
  - Method `.test_near_miss_grants_bonus_attempt_only_once_per_puzzle()`
  - Method `.test_failure_message_reports_dampened_trace_cost()`
  - Method `.test_stacked_puzzle_failures_add_escalating_trace()`
  - Method `.test_resecure_clears_host_lockdown()`
  - Method `.test_settle_career_appends_a_run_history_record()`
  - Method `.test_settle_career_history_is_capped_and_records_lockout()`
  - Method `.test_settle_career_records_daily_best_and_history_tag()`
  - Method `.test_settle_career_keeps_the_best_daily_gain()`
  - Method `.test_settle_career_scores_and_ranks_the_run()`
  - Method `.test_settle_career_hall_dedupes_and_caps_at_ten()`
  - Method `.test_daily_streak_increments_on_consecutive_days()`
  - Method `.test_daily_streak_same_day_repeat_does_not_increment()`
  - Method `.test_daily_streak_resets_after_a_gap()`
  - Method `.test_settle_career_banks_victory_loot_once()`
  - Method `.test_exploit_lockout_does_not_claim_root_access()`
  - Method `.test_faction_standing_applies_bonuses_and_grows_on_settlement()`
  - Method `.test_contract_board_reroll_charges_and_refills()`
  - Method `.test_contract_board_reroll_requires_funds_and_an_active_run()`
  - Method `.test_faction_allegiance_changes_economics_and_standing_growth()`
  - Method `.test_settle_career_awards_faction_rank_promotions_once()`
  - Method `.test_daily_modifiers_apply_starting_conditions_and_multipliers()`
  - Method `.test_difficulty_changes_trace_and_starting_state()`
  - Method `.test_difficulty_multiplies_contract_payout()`
  - Method `.test_float_seed_is_coerced()`
  - Method `.test_dead_mans_switch_banks_half_the_unbanked_loot_on_lockout()`
  - Method `.test_rival_steals_a_posted_contract_on_schedule()`
  - Method `.test_counter_rival_delays_the_next_move_and_costs_cpu()`
  - Method `.test_counter_rival_requires_cpu()`
  - Method `.test_lockout_summary_reports_lost_unbanked_credits()`
  - Method `.test_run_summary_reflects_legacy()`
  - Method `.test_settle_career_records_best_combo_on_failure()`
  - Method `.test_run_summary_victory_marks_main_story_complete()`
  - Method `.test_mutating_actions_reject_after_victory()`
  - Method `.test_story_state_and_contacts_initialize()`
  - Method `.test_overdrive_stacks_combo_and_trace()`
  - Method `.test_break_combo_resets_streak_keeps_best()`
  - Method `.test_social_failure_breaks_combo()`
  - Method `.test_av_quarantine_breaks_combo()`
  - Method `.test_gateway_quest_advances_story_and_unlocks_contact()`
  - Method `.test_main_story_quest_chain_reaches_finale()`
  - Method `.test_trust_gates_kilo_secondary_quest()`
  - Method `.test_inner_circle_unlocks_tier_dialogue_and_second_favor()`
  - Method `.test_contact_job_and_favor()`
  - Method `.test_locked_contact_rejects_interaction()`
  - Method `.test_agent_zero_pact_requires_act_three()`
  - Method `.test_agent_zero_alliance_branch()`
  - Method `.test_agent_zero_defiance_branch()`
  - Method `.test_locked_story_quest_cannot_be_accepted_early()`
  - Method `.test_archivist_favor_reveals_locked_node()`
  - Method `.test_ensure_story_state_backfills_old_save()`
  - Method `.test_out_of_order_ice_breach_still_completes_black_ice_quest()`
  - Method `.test_out_of_order_file_theft_counts_when_money_quest_unlocks()`
  - Method `.test_out_of_order_log_wipe_completes_side_quest_when_accepted()`
  - Method `.test_accept_quest_rejects_terminal_states()`
  - Method `.test_core_is_sealed_until_act_four()`
  - Method `.test_download_contract_respects_trace_limit()`
- `class TestDeckStanceProxyAndQuickhack` - *Tactical depth added by operating stances, proxy tunnels, and quickhacks.*
  - Method `.setUp()`
  - Method `.test_stance_changes_trace_math_and_rejects_unknown()`
  - Method `.test_overclock_stance_accelerates_cpu_regen()`
  - Method `.test_proxy_hop_requires_breach_and_costs_cpu()`
  - Method `.test_proxy_chain_dampens_trace_and_sever_dumps_trace()`
  - Method `.test_a_resecured_or_stale_proxy_stops_dampening()`
  - Method `.test_quickhack_breaches_low_tier_adjacent_host_at_a_cost()`
  - Method `.test_quickhack_rejects_hardened_and_distant_hosts()`
  - Method `.test_quickhack_needs_cpu()`
  - Method `.test_analysis_stance_harvests_intel_on_fresh_breach()`
  - Method `.test_intel_reveal_maps_a_distant_host_without_trace()`
  - Method `.test_intel_reveal_rejects_breached_host_without_spending()`
  - Method `.test_intel_forge_loads_zero_day_chip()`
  - Method `.test_intel_reveal_rejects_unknown_mode_and_empty_pool()`
  - Method `.test_zero_day_forge_breaches_adjacent_host_once()`
  - Method `.test_zero_day_forge_rejects_distant_target()`
  - Method `.test_port_scan_chip_maps_adjacent_host_without_trace_or_turn()`
  - Method `.test_buffer_overflow_chip_breaches_at_a_trace_cost()`
  - Method `.test_spoof_ip_chip_sheds_trace_and_refuses_when_clean()`
  - Method `.test_probe_and_intel_reveal_record_probed_nodes()`
  - Method `.test_port_scan_chip_records_probed_node()`
  - Method `.test_port_scan_chip_refuses_breached_host_without_consuming_it()`
- `class TestSideSubnetIntegration`
  - Method `.setUp()`
  - Method `.test_side_host_is_revealed_hacked_and_contract_ready()`

---

### [`tests/test_factions.py`](tests/test_factions.py)
> *Unit tests for faction standing normalization and bonuses.*

**Size**: `59` lines (`2246` bytes)

**Classes:**
- `class TestFactions`
  - Method `.test_normalize_standing_drops_unknown_and_invalid_values()`
  - Method `.test_bonuses_are_capped()`
  - Method `.test_ranks_follow_standing_thresholds()`
  - Method `.test_allegiance_normalization_and_bonuses()`
  - Method `.test_update_standing_clamps_growth()`

---

### [`tests/test_forecast.py`](tests/test_forecast.py)
> *Failing-first tests for read-only action forecasts (no balance numbers change).*

**Size**: `266` lines (`11644` bytes)

**Classes:**
- `class TestActionForecast`
  - Method `.test_scan_forecast_matches_engine_costs_and_is_pure()`
  - Method `.test_overdrive_forecast_and_block_at_high_trace()`
  - Method `.test_spoof_forecast_reduces_trace()`
  - Method `.test_quickhack_forecast_per_security_tier()`
  - Method `.test_quickhack_forecast_includes_district_heat()`
  - Method `.test_counter_forecast_reflects_zero_arc_discount()`
  - Method `.test_wipe_forecast_reflects_archivist_arc()`
  - Method `.test_unknown_action_is_rejected()`
  - Method `.test_move_forecast_names_district_crossing()`
  - Method `.test_deploy_forecast_shows_passive_yield()`
  - Method `.test_intel_forecasts_gate_on_fragments()`
  - Method `.test_proxy_forecast_shows_dampening()`
  - Method `.test_hunter_forecast_lists_ready_countermeasures()`
  - Method `.test_social_forecast_shows_lure_odds()`
  - Method `.test_bypass_forecast_lists_blocked_ports()`
  - Method `.test_evade_forecast_blocks_without_active_av()`
  - Method `.test_combo_rate_preview_caps_at_fifty_percent()`
  - Method `.test_jackout_forecast_matches_extraction_risk()`
  - Method `.test_cli_blocked_forecast_has_no_double_period()`
  - Method `.test_cli_forecast_command_reports_costs()`

---

### [`tests/test_grid.py`](tests/test_grid.py)
> *Integration tests for living-grid simulation wired into the game engine.*

**Size**: `309` lines (`12790` bytes)

**Classes:**
- `class TestGridIntegration`
  - Method `.setUp()`
  - Method `.test_advance_turn_moves_clock_daemons_and_market()`
  - Method `.test_lay_low_advances_time_and_recovers_cpu()`
  - Method `.test_lay_low_cools_trace_while_ghosted()`
  - Method `.test_lay_low_trace_cooling_stops_at_zero()`
  - Method `.test_lay_low_rejects_invalid_input_and_terminal_runs()`
  - Method `.test_tick_world_shift_changes_alert_decay()`
  - Method `.test_breach_raises_alert_and_publishes_news()`
  - Method `.test_trace_thresholds_publish_news()`
  - Method `.test_patrol_pressure_adds_trace_at_high_alert()`
  - Method `.test_ambient_grid_events_fire_and_publish()`
  - Method `.test_grid_resecures_host_and_recalls_daemons()`
  - Method `.test_rebreach_after_resecure_pays_nothing()`
  - Method `.test_breached_footprint_slows_alert_decay()`
  - Method `.test_alert_tier_escalation_publishes_news()`
  - Method `.test_world_summary_and_news_feed_shapes()`
  - Method `.test_hunter_deployment_on_alert_threshold()`
  - Method `.test_hunter_advances_and_intercepts_player()`
  - Method `.test_hunter_intercept_breaks_combo()`
  - Method `.test_hunter_scrambled_by_spoof_and_wipe()`
  - Method `.test_counter_hunter_with_logic_bomb()`
  - Method `.test_counter_hunter_with_ghost_protocol()`

---

### [`tests/test_init.py`](tests/test_init.py)
> *Smoke test for cyberpulse package.*

**Size**: `13` lines (`277` bytes)

**Classes:**
- `class TestCyberpulseInit`
  - Method `.test_version_defined()`

---

### [`tests/test_models.py`](tests/test_models.py)
> *Unit tests for CyberPulse domain models.*

**Size**: `303` lines (`12486` bytes)

**Classes:**
- `class TestModels`
  - Method `.test_node_roundtrip()`
  - Method `.test_port_and_file_roundtrip()`
  - Method `.test_deck_roundtrip()`
  - Method `.test_recipe_roundtrip()`
  - Method `.test_game_state_roundtrip()`
  - Method `.test_game_state_backfills_missing_lost_creds()`
  - Method `.test_bounty_contract_objective_inference_and_deadline_roundtrip()`
  - Method `.test_career_profile_roundtrip()`
  - Method `.test_career_alias_is_trimmed_and_defaulted()`
  - Method `.test_old_career_payload_defaults_to_empty_run_history()`
  - Method `.test_career_daily_best_drops_malformed_values()`
  - Method `.test_career_history_drops_malformed_entries_and_keeps_recent()`
  - Method `.test_apply_career_profile()`
  - Method `.test_firewall_and_antivirus_models()`
  - Method `.test_exploit_payload_and_employee_models()`
  - Method `.test_node_with_cyber_warfare_components()`
  - Method `.test_known_cves_deck_and_catalog()`

---

### [`tests/test_network.py`](tests/test_network.py)
> *Unit tests for procedural network generation.*

**Size**: `156` lines (`6474` bytes)

**Classes:**
- `class TestNetwork`
  - Method `.test_network_topology()`
  - Method `.test_deterministic_generation()`
  - Method `.test_network_simulation_topology()`
- `class TestProceduralSideHosts`
  - Method `._side_hosts(nodes)`
  - Method `._fingerprint(nodes)`
  - Method `.test_same_seed_builds_the_same_side_subnet()`
  - Method `.test_different_seeds_change_the_side_subnet()`
  - Method `.test_side_hosts_are_wired_into_the_spine()`
  - Method `.test_campaign_spine_stays_fixed()`
- `class TestSideHostTable`
  - Method `.test_every_template_row_is_schema_valid()`
  - Method `.test_template_ports_hostnames_and_files_are_unique()`
  - Method `.test_every_template_service_has_a_dedicated_or_universal_cve()`
  - Method `.test_new_rows_appear_in_seeded_grids()`

---

### [`tests/test_puzzles.py`](tests/test_puzzles.py)
> *Unit tests for CyberPulse hacking mini-game puzzles.*

**Size**: `88` lines (`3152` bytes)

**Classes:**
- `class TestPuzzles`
  - Method `.test_frequency_puzzle_tuning()`
  - Method `.test_frequency_exhaustion()`
  - Method `.test_buffer_puzzle_verification()`
  - Method `.test_frequency_near_miss_grants_one_bonus_attempt()`
  - Method `.test_buffer_near_miss_grants_one_retry()`
  - Method `.test_hash_near_miss_grants_one_bonus_attempt()`
  - Method `.test_hash_crack_puzzle()`

---

### [`tests/test_rewards.py`](tests/test_rewards.py)
> *Unit tests for variable-ratio rewards and dopamine loot schedules.*

**Size**: `55` lines (`1827` bytes)

**Classes:**
- `class TestRewards`
  - Method `.setUp()`
  - Method `.test_zero_reward_node()`
  - Method `.test_exploit_chip_drop_threshold()`
  - Method `.test_jackpot_multiplier()`

---

### [`tests/test_rivals.py`](tests/test_rivals.py)
> *Unit tests for deterministic rival generation.*

**Size**: `93` lines (`3303` bytes)

**Classes:**
- `class TestRivalGeneration`
  - Method `.test_rival_is_deterministic_for_a_seed()`
  - Method `.test_rival_fields_are_within_design_bounds()`
- `class TestRivalActEscalation`
  - Method `.test_pressure_table_covers_all_acts()`
  - Method `.test_delay_shrinks_as_acts_progress()`
  - Method `.test_delay_respects_floor()`
  - Method `.test_unknown_act_falls_back_to_baseline()`
  - Method `.test_tick_uses_act_pressure()`
  - Method `.test_counter_rival_still_delays_five()`
- `class TestRivalRosterContent`
  - Method `.test_roster_has_four_rows_with_unique_handles()`
  - Method `.test_new_row_is_reachable_by_seed()`

---

### [`tests/test_scoring.py`](tests/test_scoring.py)
> *Unit tests for the transparent run score formula.*

**Size**: `64` lines (`1814` bytes)

**Classes:**
- `class TestScoring`
  - Method `.test_score_breakdown_uses_documented_weights()`
  - Method `.test_lockout_has_no_outcome_bonus()`
  - Method `.test_negative_inputs_are_clamped()`

---

### [`tests/test_server.py`](tests/test_server.py)
> *Unit and integration tests for CyberPulse HTTP REST server.*

**Size**: `1165` lines (`51172` bytes)

**Classes:**
- `class TestCyberdeckServer`
  - Method `.setUpClass()`
  - Method `.tearDownClass()`
  - Method `._get(path)`
  - Method `._post(path, payload)`
  - Method `.test_get_state()`
  - Method `.test_rival_state_and_counter_action()`
  - Method `.test_buying_a_consumable_does_not_persist_a_career_upgrade()`
  - Method `.test_get_shop()`
  - Method `.test_get_world_state_and_grid_fields()`
  - Method `.test_market_markup_reaches_shop_endpoint()`
  - Method `.test_reset_career_requires_confirmation()`
  - Method `.test_rename_alias_action()`
  - Method `.test_get_career()`
  - Method `.test_action_scan_and_spoof()`
  - Method `.test_puzzle_endpoint_and_solve()`
  - Method `.test_static_not_found()`
  - Method `.test_static_path_traversal_blocked()`
  - Method `.test_static_assets_served()`
  - Method `.test_server_simulation_actions()`
  - Method `.test_get_workshop_and_local_files()`
  - Method `.test_tactical_stance_proxy_and_quickhack_actions()`
  - Method `.test_intel_action_reveals_and_forges()`
  - Method `.test_server_phish_craft_and_daemon()`
  - Method `.test_get_cves_firewall_antivirus()`
  - Method `.test_firewall_bypass_evade_and_social()`
  - Method `.test_malformed_port_is_rejected_with_json_error()`
  - Method `.test_craft_accepts_recipe_name_from_web_client()`
  - Method `.test_json_responses_do_not_enable_wildcard_cors()`
  - Method `.test_reset_accepts_float_seed()`
  - Method `.test_reset_rejects_invalid_seed()`
  - Method `.test_puzzle_retry_keeps_remaining_attempts()`
  - Method `.test_buffer_near_miss_grants_one_web_retry_then_locks_host()`
  - Method `.test_victory_settles_career_once()`
  - Method `.test_game_over_settles_failed_run_once()`
  - Method `.test_craft_persists_banked_spend()`
  - Method `.test_forecast_endpoint_matches_engine_costs()`
  - Method `.test_route_endpoint_reports_hops()`
  - Method `.test_web_settlement_does_not_delete_unowned_save()`
  - Method `.test_state_includes_story_quests_and_contacts()`
  - Method `.test_overdrive_action()`
  - Method `.test_contact_talk_job_and_favor_actions()`
  - Method `.test_agent_zero_alliance_action()`
  - Method `.test_accept_quest_action_respects_trust_gate()`
  - Method `.test_contract_board_decline_and_accept_action()`
  - Method `.test_drop_offer_action_spends_broker_fee()`
  - Method `.test_accept_quest_after_jackout_is_rejected()`
  - Method `.test_static_assets_do_not_wait_for_session_lock()`
  - Method `.test_get_world_and_state_contains_hunters()`
  - Method `.test_counter_hunter_api_action()`
  - Method `.test_lay_low_api_action()`
- `class TestCyberdeckSaveLoadSession`
  - Method `.setUp()`
  - Method `.test_save_then_load_restores_exact_progress()`
  - Method `.test_load_without_a_save_reports_a_missing_run()`
  - Method `.test_terminal_run_is_not_saved()`
  - Method `.test_finishing_a_run_deletes_an_earlier_save()`
  - Method `.test_save_run_accepts_a_named_slot()`
  - Method `.test_autosave_starts_after_baseline_and_tracks_changes()`
  - Method `.test_reset_can_start_a_daily_run()`
  - Method `.test_manual_save_refuses_the_auto_slot()`
  - Method `.test_autosave_can_be_loaded_from_its_slot()`
  - Method `.test_named_slot_can_be_renamed_without_reloading_it()`
  - Method `.test_delete_save_leaves_the_live_run_untouched()`
  - Method `.test_invalid_slot_is_rejected()`
  - Method `.test_settlement_deletes_every_checkpoint_of_the_run()`
- `class TestCyberdeckSaveLoadAPI`
  - Method `.setUpClass()`
  - Method `.tearDownClass()`
  - Method `._post(payload)`
  - Method `._state()`
  - Method `.test_save_and_continue_round_trip()`
- `class TestCyberdeckSaveSlotsAPI`
  - Method `.setUpClass()`
  - Method `.tearDownClass()`
  - Method `._post(payload)`
  - Method `.test_reset_career_aborts_when_backup_fails()`
  - Method `.test_reroll_contracts_action()`
  - Method `.test_reset_accepts_faction_allegiance()`
  - Method `.test_invalid_or_named_difficulty_reset()`
  - Method `.test_daily_reset_over_http()`
  - Method `.test_name_rename_and_delete_over_http()`
  - Method `.test_named_slot_round_trip_and_autosave_payload()`
  - Method `.test_web_actions_mirror_into_deckos_history()`
  - Method `.test_state_nodes_carry_district_tags()`

---

### [`tests/test_shop.py`](tests/test_shop.py)
> *Unit tests for Black Market Shop in CyberPulse.*

**Size**: `103` lines (`4177` bytes)

**Classes:**
- `class TestShop`
  - Method `.setUp()`
  - Method `.test_list_items()`
  - Method `.test_purchase_cpu_overclock()`
  - Method `.test_purchase_ice_dampener()`
  - Method `.test_purchase_insufficient_funds()`
  - Method `.test_purchase_max_level()`
  - Method `.test_dead_mans_switch_is_a_one_use_consumable()`
  - Method `.test_market_markup_raises_prices()`
  - Method `.test_market_discount_lowers_prices()`
  - Method `.test_invalid_market_multiplier_falls_back_to_base_price()`
  - Method `.test_explicit_empty_catalog_is_honored()`
  - Method `.test_none_catalog_falls_back_to_default()`

---

### [`tests/test_sim_life.py`](tests/test_sim_life.py)
> *Failing-first tests for lifelike simulation: routes, fingerprints, work shifts.*

**Size**: `76` lines (`3242` bytes)

**Classes:**
- `class TestSimLife`
  - Method `.test_nodes_carry_host_fingerprint()`
  - Method `.test_fingerprint_defaults_backfill_legacy_nodes()`
  - Method `.test_employees_have_work_shifts()`
  - Method `.test_legacy_employee_defaults_to_day_shift()`
  - Method `.test_traceroute_reports_hops_and_latency()`
  - Method `.test_traceroute_is_deterministic()`
  - Method `.test_traceroute_rejects_unknown_host()`
  - Method `.test_host_fingerprint_summarizes_target()`

---

### [`tests/test_storage.py`](tests/test_storage.py)
> *Unit tests for CyberPulse savegame and career profile persistence.*

**Size**: `635` lines (`24667` bytes)

**Classes:**
- `class TestStorage`
  - Method `.setUp()`
  - Method `.test_save_and_load()`
  - Method `.test_load_nonexistent()`
  - Method `.test_save_preserves_story_quests_and_contacts()`
  - Method `.test_save_preserves_tactical_deck_state()`
  - Method `.test_save_preserves_rival_state_and_backfills_old_saves()`
  - Method `.test_save_restores_the_run_start_faction_snapshot()`
  - Method `.test_save_preserves_extraction_insurance()`
  - Method `.test_load_backfills_story_for_old_save()`
  - Method `.test_career_save_and_load()`
  - Method `.test_corrupt_primary_does_not_overwrite_a_good_backup()`
  - Method `.test_list_saves_falls_back_when_timestamp_is_not_finite()`
  - Method `.test_career_run_history_round_trips()`
  - Method `.test_backup_and_delete_career_preserve_a_recovery_copy()`
  - Method `.test_delete_all_saves_removes_every_slot()`
  - Method `.test_career_faction_standing_round_trips()`
  - Method `.test_career_hall_of_fame_round_trips()`
  - Method `.test_career_default_fallback()`
  - Method `.test_old_career_payload_uses_best_combo_default()`
  - Method `.test_load_corrupted_save_with_backup_recovery()`
  - Method `.test_load_corrupted_career_with_backup_recovery()`
  - Method `.test_delete_save()`
  - Method `.test_rng_state_is_preserved_across_save_and_load()`
  - Method `.test_old_save_without_rng_state_keeps_legacy_reseed()`
  - Method `.test_save_preserves_pending_puzzle_attempts()`
  - Method `.test_save_preserves_contract_offer_board()`
  - Method `.test_old_offer_save_without_contract_sequence_gets_safe_migration()`
  - Method `.test_old_active_contract_save_without_sequence_gets_safe_migration()`
  - Method `.test_contract_sequence_persists_and_prevents_id_collisions()`
  - Method `.test_failed_replace_reports_no_save()`
  - Method `.test_slots_are_isolated_and_listed_with_progress()`
  - Method `.test_autosave_writes_once_per_state_change()`
  - Method `.test_autosave_refuses_a_finished_run()`
  - Method `.test_delete_run_removes_every_checkpoint_of_that_run_only()`
  - Method `.test_legacy_save_without_run_id_is_still_slot_one()`
  - Method `.test_save_stores_and_lists_a_slot_name()`
  - Method `.test_save_without_a_name_preserves_the_existing_name()`
  - Method `.test_rename_slot_preserves_checkpoint_and_timestamp()`
  - Method `.test_rename_legacy_save_keeps_its_display_timestamp()`
  - Method `.test_slot_name_is_trimmed_and_capped()`
  - Method `.test_rename_missing_or_auto_slot_is_refused()`
  - Method `.test_delete_save_only_removes_the_requested_slot()`
  - Method `.test_invalid_slot_is_rejected()`

---

### [`tests/test_tutorial.py`](tests/test_tutorial.py)
> *Unit tests for the first-run tutorial checklist.*

**Size**: `49` lines (`1464` bytes)

**Classes:**
- `class TestTutorial`
  - Method `.setUp()`
  - Method `._done_map()`
  - Method `.test_fresh_run_has_no_completed_steps()`
  - Method `.test_steps_track_persisted_progress()`
  - Method `.test_scan_command_sets_the_scan_flag()`

---

### [`tests/test_version.py`](tests/test_version.py)
> *Release metadata tests.*

**Size**: `36` lines (`1071` bytes)

**Classes:**
- `class TestVersion`
  - Method `.test_version_is_semver()`
  - Method `.test_pyproject_version_matches_the_package()`
  - Method `.test_cli_version_flag_reports_the_package_version()`

---

### [`tests/test_visuals.py`](tests/test_visuals.py)
> *Unit tests for presentation sprite registries and the CLI topology map.*

**Size**: `73` lines (`2627` bytes)

**Classes:**
- `class TestVisualRegistries`
  - Method `.test_every_node_type_has_sprite()`
  - Method `.test_node_status_overlay_keeps_base_shape()`
  - Method `.test_entity_shop_puzzle_world_tables_nonempty()`
  - Method `.test_entity_visual_falls_back_without_throwing()`
- `class TestTopologyMap`
  - Method `.test_fixed_slots_and_current_marker()`
  - Method `.test_unknown_node_renders_placeholder()`

---

### [`tests/test_world.py`](tests/test_world.py)
> *Unit tests for the living-grid world simulation module.*

**Size**: `499` lines (`21082` bytes)

**Classes:**
- `class TestWorldClock`
  - Method `.test_clock_text_and_shifts()`
  - Method `.test_advance_clock_rolls_days()`
  - Method `.test_clock_label_and_summary()`
- `class TestShiftProfiles`
  - Method `.test_shift_profile_boundaries()`
  - Method `.test_shift_modifiers_create_distinct_tradeoffs()`
  - Method `.test_shift_effect_text_is_human_readable()`
  - Method `.test_shift_profiles_carry_social_deltas()`
  - Method `.test_shift_effect_text_documents_social_surface()`
  - Method `.test_apply_social_shift_clamps_and_modifies()`
  - Method `.test_world_summary_documents_the_shift()`
  - Method `.test_alert_tier_boundaries()`
  - Method `.test_world_summary_includes_alert_tier()`
  - Method `.test_alert_tiers_are_ordered_and_unique()`
- `class TestWorldAlertAndMarket`
  - Method `.test_alert_clamps()`
  - Method `.test_market_bounds_and_multiplier()`
  - Method `.test_market_drift_is_bounded_and_deterministic()`
  - Method `.test_market_drift_shift_bias_moves_the_target()`
  - Method `.test_patrol_pressure_thresholds()`
- `class TestNewsFeed`
  - Method `.test_record_news_formats_and_trims()`
- `class TestAmbientEvents`
  - Method `.test_quiet_turn_when_cooling_down()`
  - Method `.test_low_alert_never_picks_negative_events()`
  - Method `.test_high_alert_can_pick_negative_events()`
  - Method `.test_event_roll_is_deterministic()`
- `class TestGridResponse`
  - Method `.test_no_resecure_below_alert_threshold()`
  - Method `.test_recent_breach_and_current_node_are_exempt()`
  - Method `.test_core_is_never_resecured()`
  - Method `.test_high_alert_eventually_resecures_and_is_deterministic()`
  - Method `.test_resecure_chance_delta_changes_response_rate()`
  - Method `.test_apply_resecure_restores_defenses()`
- `class TestWorldPersistence`
  - Method `.test_world_state_roundtrip()`
  - Method `.test_legacy_save_without_world_gets_defaults()`
  - Method `.test_game_state_roundtrip_keeps_world()`
- `class TestNetWatchHunterSimulation`
  - Method `.setUp()`
  - Method `.test_hunter_model_roundtrip()`
  - Method `.test_world_state_with_hunters_roundtrip()`
  - Method `.test_find_shortest_path_and_distance()`
  - Method `.test_deploy_hunter_threshold()`
  - Method `.test_deploy_hunter_threshold_follows_the_shift()`
  - Method `.test_step_hunter_moves_and_intercepts()`
  - Method `.test_intercepted_status_clears_when_hunter_leaves_player_host()`
  - Method `.test_step_hunter_confused()`
  - Method `.test_neutralize_hunter()`

**Functions:**
- `def make_node(node_id, node_type, security_level, status, breached_turn)`

---
