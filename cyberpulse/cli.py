"""Interactive and scriptable retro-cyberpunk terminal CLI for CyberPulse with behavioral mechanics."""

import argparse
import sys
import time
from pathlib import Path

# Ensure project root is in sys.path when executed directly as a script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from typing import List, Optional

from cyberpulse import __version__
from cyberpulse.achievements import ACHIEVEMENTS, achievement_names
from cyberpulse.daily import daily_modifier, daily_run
from cyberpulse.engine import GameEngine
from cyberpulse.factions import rank_for
from cyberpulse.models import CareerProfile, CyberDeck, NodeStatus, NodeType, node_visual
from cyberpulse.puzzles import BufferPuzzle, FrequencyPuzzle, HashCrackPuzzle
from cyberpulse.shop import BlackMarketShop
from cyberpulse.storage import SaveManager
from cyberpulse.world import calculate_distance, clock_minute_text


def setup_terminal_encoding() -> None:
    """Ensure stdout and stderr handle utf-8 safely across all Windows code pages."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, OSError):  # hygiene: allow detached stream; plain prints still work
                pass


def safe_print(msg: str) -> None:
    """Print message to stdout with graceful fallback for legacy terminal code pages."""
    try:
        print(msg)
    except UnicodeEncodeError:
        try:
            print(msg.encode("ascii", errors="replace").decode("ascii"))
        except (OSError, ValueError):  # hygiene: allow fallback stream unusable, nowhere to report
            pass


setup_terminal_encoding()


def get_default_data_dir() -> Path:
    return Path.cwd() / ".cyberpulse"


def render_trace_bar(trace_percent: int, width: int = 20) -> str:
    filled = int((max(0, min(100, trace_percent)) / 100) * width)
    bar = "#" * filled + "-" * (width - filled)
    if trace_percent >= 80:
        tier = "CRITICAL"
    elif trace_percent >= 50:
        tier = "HOT"
    elif trace_percent >= 25:
        tier = "WARM"
    else:
        tier = "COLD"
    return f"[{bar}] {trace_percent}% {tier}"


def topology_token(engine: GameEngine, node_id: str) -> str:
    """Compact fixed-width token for the ASCII topology map."""
    node = engine.nodes.get(node_id)
    if node is None:
        return "[   ]"
    sprite = node_visual(node.node_type, node.status)
    mark = "@" if node_id == engine.state.current_node_id else " "
    if node.status == NodeStatus.BREACHED:
        st = "B"
    elif node.status == NodeStatus.DISCOVERED:
        st = "D"
    else:
        st = "L"
    return f"[{mark}{sprite.get('glyph', '*')}{st}]"


def render_topology_map(engine: GameEngine) -> List[str]:
    """Fixed-layout ASCII topology mirroring the web matrix slots."""
    gw = topology_token(engine, "node_gateway")
    pa = topology_token(engine, "node_proxy_a")
    pb = topology_token(engine, "node_proxy_b")
    v1 = topology_token(engine, "node_vault_1")
    v2 = topology_token(engine, "node_vault_2")
    ice = topology_token(engine, "node_ice_perimeter")
    core = topology_token(engine, "node_central_core")
    sides = [topology_token(engine, f"node_side_{i:02d}") for i in (1, 2, 3) if f"node_side_{i:02d}" in engine.nodes]
    pad = " ".join(sides) if sides else "-- vacant --"
    return [
        "Topology Map (fixed slots, web parity):",
        f"   {v1}      {v2}",
        f"     {pa}  {ice}  {core}",
        f"  {gw}--+--+--+--<",
        f"     {pb}  SIDE:{pad}",
    ]


def print_hud(engine: GameEngine) -> None:
    curr = engine.get_current_node()
    trace_bar = render_trace_bar(engine.state.trace_percent)

    unbanked_str = f" [PUSH-YOUR-LUCK: +{engine.state.unbanked_creds} UNBANKED!]" if engine.state.unbanked_creds > 0 else ""
    contract = engine.state.active_contract
    if contract:
        target_info = f" -> Target: {contract.target_ip or contract.target_node_type}"
        if contract.target_file:
            target_info += f" ({contract.target_file})"
        status_tag = "[COMPLETED]" if contract.completed else "[ACTIVE]"
        contract_str = f"{contract.title}{target_info} (+{contract.reward_creds} Creds) {status_tag}"
    else:
        contract_str = f"None | Offers: {len(engine.state.contract_offers)} (run contracts)"

    print("\n+==========================================================================+")
    print(f"|          >> CYBERPULSE // NEURAL INTRUSION HARNESS v{__version__} <<             |")
    print("+==========================================================================+")
    print(f"[*] Location:   {curr.name} | {curr.hostname} ({curr.ip_address}) [{curr.node_id}]")
    print(f"[*] Local Rig:  {engine.deck.local_hostname} ({engine.deck.local_ip}) [{engine.deck.model_name}]")
    print(f"[*] Trace:      {trace_bar} | Turns: {engine.state.turns_elapsed} | Difficulty: {engine.difficulty.upper()}")
    print(f"[*] Allegiance: {engine.allegiance.upper()}")
    risk = engine.extraction_risk()
    if risk["surge"]:
        lethal = " ⚠ LETHAL EXTRACTION" if risk["lethal"] else ""
        print(f"[*] Jackout ICE: +{risk['surge']}% surge (projected trace {risk['projected_trace']}%){lethal}")
    print(f"[*] Deck:       CPU: {engine.deck.cpu_cycles}/{engine.deck.max_cpu} | RAM: {engine.deck.ram_mb}MB | Creds: {engine.deck.cryptocreds}{unbanked_str}")
    print(f"[*] Stance:     {engine.deck.operating_stance.upper()} | Proxies: {len(engine.deck.proxy_chain)}/3 | Threat Intel: {engine.deck.threat_intel_count}")
    insurance = " | Dead Man's Switch: ARMED" if engine.deck.extraction_insurance else ""
    print(f"[*] Upgrades:   ICE Dampener: Lvl {engine.deck.ice_dampener_level} | Overclock: Lvl {engine.deck.overclock_level}{insurance}")
    daily_mod = engine.daily_modifier_summary()
    if daily_mod:
        print(f"[*] Daily Mod:  {daily_mod['name']} // {daily_mod['description']}")
    exploits_str = ', '.join(engine.deck.exploits) if engine.deck.exploits else "None"
    print(f"[*] Exploits:   {exploits_str}")
    if engine.deck.active_daemons:
        print(f"[*] Daemons:    {len(engine.deck.active_daemons)} background listener(s) active")
    print(f"[*] Contract:   {contract_str}")
    rival = engine.rival_summary()
    if rival:
        print(
            f"[*] Rival:      {rival['name']} ({rival['handle']}) | "
            f"stolen {rival['contracts_stolen']} | next move in {rival['turns_until']}T"
        )
    if contract and not contract.completed and not contract.failed and contract.expires_turn:
        remaining = contract.expires_turn - engine.state.turns_elapsed
        clock = "EXPIRED" if remaining <= 0 else f"{remaining} turn(s) left"
        rush = ""
        if contract.bonus_creds and contract.rush_turn:
            rush = f" | RUSH +{contract.bonus_creds} by turn {contract.rush_turn}"
        print(f"[*] Job Clock:  {clock} | {contract.risk_tier.upper()} risk{rush}")
    if engine.state.contract_notice:
        print(f"[!] Job Alert:  {engine.state.contract_notice}")
    if engine.state.near_miss_count > 0:
        print(f"[*] Adrenaline: [NEAR-MISS ENCOUNTERS: {engine.state.near_miss_count}]")
    story = engine.story_summary()
    active_quests = sum(1 for q in engine.state.quests if q.accepted and not q.completed)
    print(f"[*] Story:      {story['act_title']} // {story['chapter_title']} | Combo: x{engine.state.combo_streak} | Quests: {active_quests} active")
    combo_fc = engine.combo_rate_preview()
    print(f"[*] Combo Rate: next breach +{int(combo_fc['next_rate'] * 100)}% | unbanked at risk: {combo_fc['unbanked_at_risk']} CR")
    world = engine.state.world
    world_info = engine.world_summary()
    hunter_tag = ""
    active_hunters = [h for h in world.hunters if h.status in ("hunting", "confused", "intercepted")]
    if active_hunters:
        h = active_hunters[0]
        dist = world_info.get("nearest_hunter_distance", -1)
        dist_str = f"{dist} hop{'s' if dist != 1 else ''}" if dist >= 0 else "unreachable"
        if dist == 0:
            hunter_tag = f" | 🚨 HUNTER INTERCEPT: {h.name}!"
        elif dist == 1:
            hunter_tag = f" | ⚠️ HUNTER CLOSE: {h.name} (1 hop)!"
        else:
            hunter_tag = f" | 📡 Hunter: {h.name} ({dist_str})"
    print(f"[*] Grid:       {world_info['clock']} | Alert: {world.alert_level}% [{world_info['alert_tier']}] | Market: x{world_info['market_multiplier']}{hunter_tag}")
    print(f"[*] Shift:      {world_info['shift']} // {world_info['shift_tagline']}")
    print(f"[*] Doctrine:   {world_info['shift_effect']}")
    print("--------------------------------------------------------------------------")
    print("Discovered Subnet Nodes:")
    for cid in curr.connected_ids:
        adj = engine.nodes.get(cid)
        if adj:
            icon = "[BREACHED]" if adj.status == NodeStatus.BREACHED else ("[DISCOVERED]" if adj.status == NodeStatus.DISCOVERED else "[LOCKED]")
            sprite = node_visual(adj.node_type, adj.status)
            print(f"   * {sprite.get('glyph', '*')} {adj.ip_address:<15} | {adj.hostname:<24} | {sprite.get('label', adj.node_type):<9} | {icon} (Sec: {adj.security_level})")
    for line in render_topology_map(engine):
        print(line)
    print("Legend: ◇ GATEWAY | ⬡ FIREWALL | ▣ VAULT | ▲ BLACK ICE | ⬢ SUPERCORE | ● BREACHED ◌ EXPOSED · SEALED | @ YOU")
    print("+==========================================================================+")


def print_contract(engine: GameEngine) -> None:
    contract = engine.state.active_contract
    print("\n+==========================================================================+")
    print("|                 >> SYNDICATE JOB BOARD // CONTRACTS <<                  |")
    print("+==========================================================================+")
    if contract:
        contact = engine._find_contact(contract.giver)
        giver = f"{contact.name} ({contact.handle})" if contact else "The Syndicate"
        remaining = contract.expires_turn - engine.state.turns_elapsed if contract.expires_turn else None
        print(f"[*] ACTIVE:    {contract.title} [{contract.risk_tier.upper()} RISK]")
        print(f"[*] Broker:    {giver}")
        print(f"[*] Objective: {contract.description or contract.objective_kind.upper()}")
        print(f"[*] Target:    {contract.target_ip or contract.target_node_type}")
        if contract.target_file:
            print(f"[*] Payload:   {contract.target_file}")
        print(f"[*] Stealth:   trace must stay <= {contract.max_trace_limit}% at confirmation")
        print(f"[*] Payout:    +{contract.reward_creds} base Creds" + (f" +{contract.bonus_creds} rush bonus" if contract.bonus_creds else ""))
        if remaining is None:
            print("[*] Deadline:  none (legacy contract)")
        else:
            state = "EXPIRED" if remaining <= 0 else f"{remaining} turn(s) left"
            print(f"[*] Deadline:  {state} (turn {contract.expires_turn})")
            if contract.rush_turn:
                print(f"[*] Rush:      complete by turn {contract.rush_turn} for the bonus")
        print("[*] Decline:   decline_contract (costs giver trust)")
        print("--------------------------------------------------------------------------")
    else:
        print("[*] ACTIVE:    none — choose an offer below with accept_job <id>")
    if engine.state.contract_notice:
        print(f"[!] Alert:     {engine.state.contract_notice}")
    print("\n>>> POSTED OFFERS")
    offers = engine.state.contract_offers
    if not offers:
        print("[*] No fresh Syndicate work on this grid. Advance the clock or wait for re-secure.")
    for index, offer in enumerate(offers, start=1):
        contact = engine._find_contact(offer.giver)
        giver = contact.name if contact else "Syndicate"
        offer_left = offer.offer_expires_turn - engine.state.turns_elapsed if offer.offer_expires_turn else None
        offer_clock = f"offer expires in {offer_left} turn(s)" if offer_left is not None else "no offer expiry"
        print(f"[{index}] {offer.title} [{offer.risk_tier.upper()} RISK] — {giver}")
        print(f"    {offer.description}")
        print(f"    Target: {offer.target_ip or offer.target_node_type} | Window: {offer.deadline_turns} turns | {offer_clock}")
        print(f"    Pay: +{offer.reward_creds} base (+{offer.bonus_creds} rush) | ACCEPT: accept_job {offer.contract_id}")
    print("+==========================================================================+")


def print_hunters(engine: GameEngine) -> None:
    world = engine.state.world
    active = [h for h in world.hunters if h.status in ("hunting", "confused", "intercepted")]
    print("\n+==========================================================================+")
    print("|              >> NETWATCH COUNTER-INFILTRATION RADAR <<                   |")
    print("+==========================================================================+")
    if not active:
        radar_summary = engine.world_summary()
        print("[*] Radar Status: CLEAR. No active NetWatch hunter signatures in sector.")
        print(f"[*] Grid Corporate Alert: {world.alert_level}% [{radar_summary['alert_tier']}] (Hunters deploy at >={radar_summary['shift_modifiers']['hunter_threshold']}%)")
    else:
        for h in active:
            loc_node = engine.nodes.get(h.current_node_id)
            loc_name = f"{loc_node.hostname} ({loc_node.ip_address})" if loc_node else h.current_node_id
            dist = calculate_distance(engine.nodes, h.current_node_id, engine.state.current_node_id)
            dist_str = f"{dist} hop(s)" if dist >= 0 else "unreachable"
            confusion = f"CONFUSED ({h.confused_turns} turns left)" if h.confused_turns > 0 else "LOCK-ON"
            print(f"[*] Hunter Unit:     {h.name} [{h.status.upper()}]")
            print(f"[*] Sector Location: {loc_name}")
            print(f"[*] Proximity:       {dist_str} to your active rig")
            print(f"[*] Scent Tracking:  {confusion}")
            print(f"[*] Active Turns:    {h.turns_active}")
        print("--------------------------------------------------------------------------")
        print("Tactical Countermeasures:")
        print("   * counter hunter logic_bomb     - detonate logic bomb payload to neutralize")
        print("   * counter hunter ghost_protocol - mask signature & banish hunter back to core")
        print("   * counter hunter cpu_burst      - burn 3 CPU cycles to scramble hunter radar")
        print("   * spoof / wipe_logs             - drops trace and adds 2 turns of confusion")
    print("+==========================================================================+")


def print_shop(
    shop: BlackMarketShop,
    deck: CyberDeck,
    price_multiplier: float = 1.0,
    street_discount: float = 0.0,
) -> None:
    items = shop.list_available(deck, price_multiplier=price_multiplier)
    print("\n+==========================================================================+")
    print("|                   >> BLACK MARKET CYBER-VENDOR <<                        |")
    print("+==========================================================================+")
    print(f"[*] Available Funds: {deck.cryptocreds} CryptoCreds | Market index: x{price_multiplier:.3f}")
    if street_discount:
        print(f"[*] Street Standing: -{street_discount * 100:.0f}% black-market discount applied.")
    if price_multiplier > 1.0:
        print("[!] The grid is hot: black-market prices are marked up tonight.")
    elif price_multiplier < 1.0:
        print("[*] A quiet grid: black-market prices are discounted tonight.")
    print()
    for it in items:
        status = f"Lvl {it['current_level']}/{it['max_level']}" if it['max_level'] > 1 else ("OWNED" if it['current_level'] > 0 else "AVAILABLE")
        buy_tag = "[AFFORDABLE]" if it['can_buy'] else "[LOCKED]"
        cost_str = f"{it['cost']}" if it['cost'] == it['base_cost'] else f"{it['cost']} (base {it['base_cost']})"
        print(f"   * {it['item_id']:<18} | Cost: {cost_str:<16} Creds | {status:<12} | {buy_tag}")
        print(f"     Description: {it['description']}")
    print("--------------------------------------------------------------------------")
    print("Buy with: buy <item_id> (e.g. `buy overclock_cpu` or `buy ice_dampener`)")
    print("+==========================================================================+")


def print_tutorial(engine: GameEngine, profile: CareerProfile) -> None:
    """Render the first-run field manual with live checklist state."""
    if profile.successful_runs or profile.failed_runs:
        print("\nField manual archived: your career already has settled runs.")
        return
    steps = engine.tutorial_progress()
    print("\n+-------------------------------- FIRST RUN CHECKLIST ------------------------+")
    for step in steps:
        mark = "x" if step["done"] else " "
        print(f"  [{mark}] {step['title']:<16} {step['hint']}")
    if all(step["done"] for step in steps):
        print("  All five steps complete. The rest of the grid is yours.")
    print("+----------------------------------------------------------------------------+")


def print_hall(profile: CareerProfile, difficulty: str = "all") -> None:
    """Render the Hall of Fame, optionally filtered by difficulty."""
    hall = profile.hall_of_fame if isinstance(profile.hall_of_fame, list) else []
    if difficulty != "all":
        hall = [
            entry for entry in hall
            if str(entry.get("difficulty", "normal")).lower() == difficulty
        ]
    label = difficulty.upper()
    print(f"HALL OF FAME [{label}]:")
    if not hall:
        print("   (no ranked runs for this filter yet)")
    for index, entry in enumerate(hall[:5], start=1):
        outcome = str(entry.get("outcome", "unknown")).upper()
        entry_difficulty = str(entry.get("difficulty", "normal")).upper()
        print(
            f"   #{index} {int(entry.get('score', 0)):>6,}  {entry_difficulty:<6} "
            f"{outcome:<8} SEED {entry.get('seed', '?')}  TURN {entry.get('turns', 0)}"
        )


def print_career(profile: CareerProfile) -> None:
    print("\n+==========================================================================+")
    print(f"|               >> HACKER CAREER DOSSIER: {profile.alias} <<                  |")
    print("+==========================================================================+")
    print(f"[*] Banked Funds:     {profile.banked_creds} CryptoCreds")
    print(f"[*] Lifetime Stolen:  {profile.lifetime_creds} CryptoCreds")
    print(f"[*] Heists Cleared:   {profile.successful_runs} successful | {profile.failed_runs} severed")
    print(f"[*] Infiltration Run: Streak: {profile.current_streak} (Best: {profile.best_streak})")
    print(f"[*] Best Neural Combo: x{profile.best_combo}")
    upgrades = ', '.join(profile.purchased_upgrades) if profile.purchased_upgrades else "None"
    print(f"[*] Hardware Rig:     {upgrades}")
    unlocked_names = achievement_names(profile.achievements or [])
    print(f"[*] Milestones:       {len(unlocked_names)}/{len(ACHIEVEMENTS)}")
    if unlocked_names:
        print(f"     {', '.join(unlocked_names)}")
    standing = profile.faction_standing if isinstance(profile.faction_standing, dict) else {}
    syndicate = int(standing.get("syndicate", 0) or 0)
    street = int(standing.get("street", 0) or 0)
    syndicate_rank = rank_for("syndicate", syndicate)[1]
    street_rank = rank_for("street", street)[1]
    print(
        f"[*] Factions:         Syndicate {syndicate} [{syndicate_rank}] "
        f"(+{min(20, syndicate)}% contract pay) | Street {street} [{street_rank}] "
        f"(-{min(15, street)}% shop)"
    )
    print(f"[*] Daily Streak:     {profile.daily_streak} (Best: {profile.best_daily_streak})")
    daily = profile.daily_best if isinstance(profile.daily_best, dict) else {}
    if daily:
        recent = sorted(daily.items(), reverse=True)[:3]
        print("[*] Daily Bests:     " + " | ".join(f"{day} +{creds} CR" for day, creds in recent))
    else:
        print("[*] Daily Bests:      none yet (try --daily or menu 7)")
    print("--------------------------------------------------------------------------")
    print_hall(profile)
    print("--------------------------------------------------------------------------")
    print("RECENT RUNS:")
    history = profile.run_history[-5:] if isinstance(profile.run_history, list) else []
    if not history:
        print("   (no settled runs yet; finish a run to record a legacy)")
    for index, record in enumerate(reversed(history), start=1):
        outcome = str(record.get("outcome", "unknown")).upper()
        finished = record.get("finished_at")
        stamp = "--"
        if isinstance(finished, (int, float)):
            try:
                stamp = time.strftime("%Y-%m-%d %H:%M", time.localtime(float(finished)))
            except (ValueError, OSError, OverflowError):  # hygiene: allow malformed timestamp shows as --
                pass
        print(
            f"   * [{index}] {outcome:<8} {str(record.get('difficulty', 'normal')).upper():<6} "
            f"SEED {record.get('seed', '?')}  TURN {record.get('turns', 0)}  "
            f"{record.get('creds', 0)} CR  COMBO x{record.get('best_combo', 0)}  {stamp}"
        )
    print("+==========================================================================+")


def print_workshop(engine: GameEngine) -> None:
    recipes = engine.list_crafting_recipes()
    total_funds = engine.deck.cryptocreds + engine.state.unbanked_creds
    print("\n+==========================================================================+")
    print("|               >> NETRUNNER MALWARE SYNTHESIS BAY <<                      |")
    print("+==========================================================================+")
    print(f"[*] Available Funds: {total_funds} CryptoCreds (Banked: {engine.deck.cryptocreds}, Unbanked: {engine.state.unbanked_creds})\n")
    for r in recipes:
        can_afford = total_funds >= r["cost_creds"]
        afford_tag = "[AFFORDABLE]" if can_afford else "[INSUFFICIENT FUNDS]"
        print(f"   * {r['name']:<18} | Cost: {r['cost_creds']:<3}cr | Vector: {r['vector']:<7} | {afford_tag}")
        print(f"     Payload: {r['payload']} | {r['description']}")
    print("--------------------------------------------------------------------------")
    print("Synthesize with: craft <recipe_name> (e.g. `craft worm_replicator` or `craft keylogger_daemon`)")
    print("+==========================================================================+")


def print_daemons(engine: GameEngine) -> None:
    print("\n+==========================================================================+")
    print("|              >> ACTIVE BACKGROUND MALWARE DAEMONS <<                     |")
    print("+==========================================================================+")
    if not engine.deck.active_daemons:
        print("   No background daemons currently deployed.")
    else:
        for d in engine.deck.active_daemons:
            node = engine.nodes.get(d.target_node_id)
            hname = node.hostname if node else d.target_ip
            print(f"   * {d.daemon_id} [{d.daemon_type.upper()}] on {hname} ({d.target_ip})")
            print(f"     Yield: +{d.yield_per_turn} unbanked creds/turn | Detection Trace: +{d.detection_risk}%/turn | Turns Active: {d.turns_active}")
    print("+==========================================================================+")


def print_cves(engine: GameEngine) -> None:
    print("\n+==========================================================================+")
    print("|             >> WEAPONIZED CVE VULNERABILITY EXPLOIT CATALOG <<          |")
    print("+==========================================================================+")
    cves = engine.list_cves()
    for c in cves:
        print(f"   * {c['cve_id']:<15} | {c['name']:<28} | Target: {c['target_service'].upper():<5}")
        print(f"     RAM: {c['required_ram_mb']}MB | CPU: {c['cpu_cost']} | Stealth: {c['stealth_rating']}/5 | Trace: +{c['damage_trace']}%")
        print(f"     {c['description']}")
    print("--------------------------------------------------------------------------")
    print("Deploy with: exploit <ip> <port> [cve_id] (e.g. `exploit 192.168.1.10 21 cve-2011-2523`)")
    print("+==========================================================================+")


def print_story(engine: GameEngine) -> None:
    story = engine.story_summary()
    print("\n+==========================================================================+")
    print(f"|                 >> STORY // {story['act_title']}: {story['chapter_title']} <<")
    print("+==========================================================================+")
    print(f"[*] {story['intro']}")
    print("--------------------------------------------------------------------------")
    for line in story["log"][-6:]:
        print(f"   > {line}")
    print("+==========================================================================+")


def print_world(engine: GameEngine) -> None:
    summary = engine.world_summary()
    print("\n+==========================================================================+")
    print("|                    >> LIVING GRID // CITY PULSE <<                       |")
    print("+==========================================================================+")
    print(f"[*] Clock:      {summary['clock']}")
    print(f"[*] Shift:      {summary['shift']} // {summary['shift_tagline']}")
    print(f"[*] Doctrine:   {summary['shift_effect']}")
    print(f"[*] Grid Alert: {summary['alert_level']}% [{summary['alert_tier']}] | Market: x{summary['market_multiplier']} black-market index")
    print(f"[*] Response:   Re-secured hosts: {summary['resecured_count']}")
    print("--------------------------------------------------------------------------")
    print("Latest headlines:")
    for item in summary["news"][-8:]:
        print(f"   > [{item['source']}] {item['headline']}")
    print("--------------------------------------------------------------------------")
    print("News wire: news | Flip through the whole feed with: news 20")
    print("+==========================================================================+")


def print_news(engine: GameEngine, limit: int = 12) -> None:
    items = engine.news_feed(limit)
    print("\n+==========================================================================+")
    print("|                       >> GRID NEWS WIRE <<                               |")
    print("+==========================================================================+")
    if not items:
        print("   > (the wire is quiet; breach a host to make headlines)")
    for item in items:
        stamp = f"Day {item['day']} {clock_minute_text(item['minute'])}"
        print(f"   > [{stamp}] {item['source']}: {item['headline']}")
    print("+==========================================================================+")


def print_run_summary(engine: GameEngine) -> None:
    summary = engine.run_summary()
    print("\n+==========================================================================+")
    print(f"|                 >> RUN LEGACY // {summary['outcome_title']} <<")
    print("+==========================================================================+")
    print(f"[*] Story:       {summary['story_title']}")
    print(f"[*] Best Combo:  x{summary['best_combo']} | Quests: {summary['quests_completed_count']}/{summary['quests_total']}")
    if summary.get("achievements_unlocked"):
        print(f"[*] Milestones:  {', '.join(summary['achievements_unlocked'])}")
    if summary.get("daily_key"):
        print(f"[*] Daily:       {summary['daily_key']}")
    if summary.get("allegiance") and summary["allegiance"] != "none":
        print(f"[*] Allegiance:  {summary['allegiance'].upper()}")
    for promotion in summary.get("rank_ups", []):
        print(
            f"[*] Promotion:   {promotion['faction'].upper()} -> {promotion['rank']} "
            f"(+{promotion['reward']} CR)"
        )
    if summary.get("score") is not None:
        rank = f" | HALL #{summary['hall_rank']}" if summary.get("hall_rank") else ""
        print(f"[*] Score:       {summary['score']:,}{rank}")
    real_contacts = [c for c in summary["contacts"] if c["trust"] > 0 or c["favor_used"]]
    if real_contacts:
        print("[*] Operatives:  " + ", ".join(
            f"{c['name']} (trust {c['trust']}{', favor spent' if c['favor_used'] else ''})"
            for c in real_contacts
        ))
    print("--------------------------------------------------------------------------")
    for line in summary["epilogue"]:
        print(f"   > {line}")
    print("+==========================================================================+")


def print_quests(engine: GameEngine) -> None:
    print("\n+==========================================================================+")
    print("|                     >> MISSION BOARD // QUESTS <<                        |")
    print("+==========================================================================+")
    for quest in engine.state.quests:
        if quest.completed:
            status = "[COMPLETE]"
        elif engine.is_quest_locked(quest):
            status = "[LOCKED]"
        elif quest.accepted:
            status = f"[{quest.progress}/{max(1, quest.required)}]"
        else:
            status = "[AVAILABLE]"
        giver = engine._find_contact(quest.giver)
        giver_name = giver.name if giver else quest.giver
        print(f"   * {quest.quest_id:<16} {status:<12} {quest.title} (+{quest.reward_creds} CR)")
        print(f"     {quest.description} // Contact: {giver_name}")
        if engine.is_quest_locked(quest) and giver and quest.required_trust > giver.trust:
            print(f"     Requires trust {quest.required_trust} with {giver.name} (current {giver.trust}).")
    print("--------------------------------------------------------------------------")
    print("Accept with: accept <quest_id>. Talk to contacts with: contact <handle> job")
    print("+==========================================================================+")


def print_contacts(engine: GameEngine) -> None:
    print("\n+==========================================================================+")
    print("|                    >> OPERATIVE CHANNELS // CONTACTS <<                  |")
    print("+==========================================================================+")
    for contact in engine.list_contacts():
        if contact["locked"]:
            print(f"   * {contact['handle']:<16} [SIGNAL LOCKED] {contact['name']}")
            continue
        if not contact["favor_used"]:
            favor = "READY"
        elif contact["trust"] >= 6 and not contact["bonus_favor_used"]:
            favor = "INNER CIRCLE FAVOR READY"
        elif contact["bonus_favor_used"]:
            favor = "BOTH SPENT"
        else:
            favor = "SPENT"
        print(f"   * {contact['handle']:<16} {contact['name']:<16} Trust: {contact['trust']} [{contact['trust_tier']}] | Favor: {favor}")
        print(f"     {contact['role']} // {contact['faction']} // {contact['tagline']}")
        print(f"     \"{contact['dialogue']}\"")
        if contact.get("trust_dialogue"):
            print(f"     \"{contact['trust_dialogue']}\"")
    print("--------------------------------------------------------------------------")
    print("Talk: contact <handle> talk | Job: contact <handle> job | Favor: contact <handle> favor")
    print("+==========================================================================+")


def print_save_slots(saves: List[dict]) -> None:
    """Render a compact list of restorable save slots."""
    if not saves:
        print("No saved runs found.")
        return
    print("\n+-------------------------------- SAVED RUNS --------------------------------+")
    for entry in saves:
        label = entry["label"]
        if entry.get("name"):
            label = f"{label} // {entry['name']}"
        print(
            f"  [{entry['slot']}] {label:<28} TURN {entry['turns']:<3} "
            f"{entry['creds']} CR  TRACE {entry['trace']}%  ACT {entry['act']}  "
            f"{entry['saved_at_display']}"
        )
    print("+----------------------------------------------------------------------------+")


def choose_load_slot(save_mgr: SaveManager) -> Optional[str]:
    """Prompt for a save slot to continue; returns None when the player cancels."""
    saves = save_mgr.list_saves()
    if not saves:
        print("No saved runs found.")
        return None
    print_save_slots(saves)
    try:
        raw = input("load-slot [auto/1-3] (blank cancels)> ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return None
    if not raw or raw in ("q", "quit", "cancel"):
        return None
    try:
        return save_mgr.normalize_slot(raw)
    except ValueError:
        print("Invalid slot. Choose auto, 1, 2, or 3.")
        return None


def show_main_menu(engine: GameEngine, save_mgr: SaveManager) -> str:
    """Render the interactive main menu and return 'start', 'load', 'daily', or 'quit'."""
    print("\n+==========================================================================+")
    print("|              >> CYBERPULSE // NEURAL INTRUSION HARNESS <<                |")
    print("|                              MAIN MENU                                   |")
    print("+==========================================================================+")
    print("|  [1] JACK IN (new run)       [2] CONTINUE (load save)                    |")
    print("|  [3] STORY BRIEFING          [4] OPERATIVES                              |")
    print("|  [5] CAREER DOSSIER          [6] HOW TO PLAY                             |")
    print("|  [7] DAILY RUN               [Q] QUIT                                    |")
    print("+==========================================================================+")

    while True:
        try:
            choice = input("main-menu> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Neural link closed.")
            return "quit"

        if choice in ("1", "start", "new", "jackin", "jack in"):
            return "start"
        if choice in ("2", "continue", "load"):
            return "load"
        if choice in ("3", "story", "brief"):
            print_story(engine)
            print_quests(engine)
            continue
        if choice in ("4", "contacts", "crew"):
            print_contacts(engine)
            continue
        if choice in ("5", "career"):
            print_career(save_mgr.load_career())
            continue
        if choice in ("6", "help", "how"):
            print("Commands: status, contract, bounty, accept_job, drop_offer, decline_contract, story, quests, contacts, contact, accept, world, news, scan, probe, exploit,")
            print("          bypass, evade, social, ls, cat, steal, wipe_logs, keylogger, craft,")
            print("          move, overdrive, stance, proxy, quickhack, intel, spoof, cash_out, shop, buy, contract, reroll, rival, counter_rival, tutorial, career, hall, alias, reset_career,")
            print("          save [1-3] [name], load [1-3|auto], saves, rename, delete, replay, quit")
            print("Daily challenge: run `python -m cyberpulse.cli --daily` or choose 7.")
            continue
        if choice in ("7", "daily", "daily run"):
            return "daily"
        if choice in ("q", "quit", "exit"):
            print("👋 Neural link closed.")
            return "quit"
        print("Unknown choice. Enter 1-6 or Q.")


def execute_hack_puzzle(engine: GameEngine, target_id: str, auto_solve: bool = False) -> bool:
    can_hack, reason, puzzle, node = engine.get_or_create_puzzle(target_id)
    if not can_hack or node is None or puzzle is None:
        print(f"⚠️ {reason}")
        return False

    print(f"\n⚡ INITIATING CYBER-ATTACK ON: {node.name} (Sec Level: {node.security_level})")

    # If auto_solve is True (used in batch/tests)
    if auto_solve:
        engine.clear_pending_puzzle(target_id)
        _, msg = engine.complete_breach(target_id)
        print(msg)
        return True

    # Puzzle execution based on node puzzle_type
    p_type = node.puzzle_type or "frequency"
    if p_type == "frequency" and isinstance(puzzle, FrequencyPuzzle):
        print(f"📡 TUNING PROTOCOL: Target frequency between 20.0 and 99.0 GHz (tolerance ±{puzzle.tolerance} GHz).")
        while puzzle.attempts_left > 0:
            val_str = input(f"Enter target GHz [{puzzle.attempts_left} tries left]: ").strip()
            try:
                guess = float(val_str)
            except ValueError:
                print("Invalid frequency value.")
                continue
            ok, msg = puzzle.tune(guess)
            print(msg)
            bonus_msg = engine.resolve_puzzle_near_miss(puzzle)
            if bonus_msg:
                print(bonus_msg)
            if ok:
                engine.clear_pending_puzzle(target_id)
                engine.complete_breach(target_id)
                return True
        _, lockdown_msg = engine.register_puzzle_failure(
            target_id, f"intrusion script burned out on {node.hostname}"
        )
        print(lockdown_msg)
        return False

    elif p_type == "buffer" and isinstance(puzzle, BufferPuzzle):
        print("💾 BUFFER OVERFLOW PROTOCOL: Inject target hex sequence:")
        print(f"   Target: {puzzle.target_seq}")
        while True:
            seq_str = input("Enter hex codes separated by space: ").strip().upper()
            player_seq = seq_str.split()
            ok, msg = puzzle.verify_sequence(player_seq)
            print(msg)
            bonus_msg = engine.resolve_puzzle_near_miss(puzzle)
            if bonus_msg:
                print(bonus_msg)
            if ok:
                engine.clear_pending_puzzle(target_id)
                engine.complete_breach(target_id)
                return True
            if bonus_msg:
                continue
            _, lockdown_msg = engine.register_puzzle_failure(
                target_id, f"buffer injection corrupted on {node.hostname}"
            )
            print(lockdown_msg)
            return False

    elif p_type == "hash" and isinstance(puzzle, HashCrackPuzzle):
        print(f"🔑 HASH CRACK PROTOCOL: Potential keys: {', '.join(puzzle.word_list)}")
        while puzzle.attempts_left > 0:
            guess = input(f"Guess keyword [{puzzle.attempts_left} tries left]: ").strip()
            ok, msg = puzzle.guess(guess)
            print(msg)
            bonus_msg = engine.resolve_puzzle_near_miss(puzzle)
            if bonus_msg:
                print(bonus_msg)
            if ok:
                engine.clear_pending_puzzle(target_id)
                engine.complete_breach(target_id)
                return True
        _, lockdown_msg = engine.register_puzzle_failure(
            target_id, f"hash crack locked out on {node.hostname}"
        )
        print(lockdown_msg)
        return False

    engine.clear_pending_puzzle(target_id)
    engine.complete_breach(target_id)
    return True


def run_command(cmd_line: str, engine: GameEngine, save_mgr: SaveManager, auto_solve: bool = False) -> bool:
    """Execute a single command string. Returns False to quit."""
    parts = cmd_line.strip().split()
    if not parts:
        return True
    action = parts[0].lower()
    shop = BlackMarketShop()

    if action in ("q", "quit", "exit"):
        print("👋 Neural link terminated.")
        return False

    if action == "status":
        print_hud(engine)
        return True

    if action in ("story", "lore"):
        print_story(engine)
        return True

    if action in ("world", "city", "grid"):
        print_world(engine)
        return True

    if action in ("lay_low", "laylow", "wait", "rest"):
        turns = 1
        if len(parts) > 1:
            if not parts[1].isdigit():
                print("Usage: lay_low [1-3] (ghost the connection and recover CPU)")
                return True
            turns = int(parts[1])
        ok, msg = engine.lay_low(turns)
        print(msg)
        return True

    if action in ("news", "wire", "headlines"):
        limit = 12
        if len(parts) > 1 and parts[1].isdigit():
            limit = max(1, min(60, int(parts[1])))
        print_news(engine, limit)
        return True

    if action in ("hunter", "hunters", "radar"):
        print_hunters(engine)
        return True

    if action in ("counter", "countermeasure", "counter_ice"):
        method = "logic_bomb"
        if len(parts) >= 3 and parts[1].lower() in ("hunter", "ice", "aegis", "netwatch"):
            method = parts[2]
        elif len(parts) >= 2 and parts[1].lower() not in ("hunter", "ice", "aegis", "netwatch"):
            method = parts[1]
        ok, msg = engine.counter_hunter(method=method)
        print(msg)
        return True

    if action in ("contract", "contracts", "bounty", "job"):
        print_contract(engine)
        return True

    if action in ("accept_job", "take_job", "accept_contract"):
        if len(parts) < 2:
            print("Usage: accept_job <contract_id>  (run `contracts` to list posted offers)")
            return True
        ok, msg = engine.accept_contract(parts[1])
        print(msg)
        return True

    if action in ("drop_offer", "pass_offer"):
        if len(parts) < 2:
            print("Usage: drop_offer <contract_id>  (30 CR, or a one-turn broker cooldown if broke)")
            return True
        ok, msg = engine.drop_offer(parts[1])
        print(msg)
        return True

    if action in ("decline_contract", "decline_job", "decline"):
        ok, msg = engine.decline_contract()
        print(msg)
        return True

    if action in ("quests", "missions", "jobs"):
        print_quests(engine)
        return True

    if action in ("contacts", "crew", "operatives"):
        print_contacts(engine)
        return True

    if action in ("contact", "talk", "interact"):
        if len(parts) < 2:
            print("Usage: contact <handle | name> [talk | job | favor | ally | defy]")
            return True
        mode = parts[2] if len(parts) > 2 else "talk"
        ok, msg, _ = engine.interact_contact(parts[1], mode)
        print(msg)
        return True

    if action in ("accept", "take", "accept_quest"):
        if len(parts) < 2:
            print("Usage: accept <quest_id> (see `quests`)")
            return True
        ok, msg = engine.accept_quest(parts[1])
        print(msg)
        return True

    if action == "scan":
        ok, msg, _ = engine.scan_surroundings()
        print(msg)
        return True

    if action in ("move", "cd", "ssh"):
        if len(parts) < 2:
            print("Usage: move <ip | hostname | node_id>")
            return True
        node = engine.find_node(parts[1])
        target_id = node.node_id if node else parts[1]
        ok, msg = engine.move_to(target_id)
        print(msg)
        return True

    if action in ("probe", "nmap"):
        if len(parts) < 2:
            print("Usage: probe <ip | hostname | node_id> (e.g. `probe 192.168.1.10`)")
            return True
        ok, summary, _ = engine.probe_host(parts[1])
        print(summary)
        if ok:
            fp = engine.host_fingerprint(parts[1])
            if fp.get("ok"):
                print(f"OS: {fp['os_name']} | Uptime: {fp['uptime_days']}d ({fp['uptime_hours']}h) | Patch: {fp['patch_level']}")
                print(f"Staff on shift ({fp['current_shift']}): {fp['employees_on_shift']}/{fp['employees_total']}")
        return True

    if action in ("traceroute", "tracert", "route"):
        if len(parts) < 2:
            print("Usage: traceroute <ip | hostname | node_id> (e.g. `traceroute 172.16.80.1`)")
            return True
        route = engine.trace_route(parts[1])
        if not route.get("ok"):
            print(f"Traceroute failed: {route.get('reason', 'unreachable')}.")
            return True
        print(f"Route to {route['target']} ({route['hop_count']} hops, {route['total_latency_ms']}ms):")
        for index, hop in enumerate(route["hops"], start=1):
            print(f"  {index:>2}  {hop['ip_address']:<15} {hop['hostname']:<26} {hop['latency_ms']}ms")
        return True

    if action in ("hack", "breach"):
        if len(parts) < 2:
            print("Usage: hack <node_id | ip> [port]")
            return True
        target_query = parts[1]
        # If user passed a port number (e.g. hack 192.168.1.10 21)
        if len(parts) >= 3 and parts[2].isdigit():
            ok, msg = engine.exploit_service(target_query, int(parts[2]))
            print(msg)
            return True
        # Resolve node_id if target_query is IP or hostname
        node = engine.find_node(target_query)
        target_id = node.node_id if node else target_query
        execute_hack_puzzle(engine, target_id, auto_solve=auto_solve)
        return True

    if action in ("exploit", "use"):
        if len(parts) < 2:
            exploits_list = ', '.join(engine.deck.exploits) if engine.deck.exploits else 'None'
            print(f"Usage: exploit <ip> <port> (e.g. `exploit 192.168.1.10 21`)\n       exploit <chip_name> [target] (Loaded chips: {exploits_list})")
            return True
        # Check if second arg is digit -> service port exploit
        if len(parts) >= 3 and parts[2].isdigit():
            cve_arg = parts[3] if len(parts) > 3 else None
            ok, msg = engine.exploit_service(parts[1], int(parts[2]), cve_id=cve_arg)
            print(msg)
            return True
        exploit_name = parts[1]
        target = parts[2] if len(parts) > 2 else None
        ok, msg = engine.use_exploit(exploit_name, target)
        print(msg)
        return True

    if action in ("ls", "dir"):
        target = parts[1] if len(parts) > 1 else None
        ok, output, _ = engine.list_files(target)
        print(output)
        return True

    if action == "cat":
        if len(parts) < 2:
            print("Usage: cat [ip] <filepath> (e.g. `cat /etc/hosts` or `cat local /home/deck/notes.txt`)")
            return True
        if len(parts) == 2:
            path_arg = parts[1]
            if path_arg.startswith(("/home/deck", "/loot", "/bin")):
                ok, output, _ = engine.read_local_file(path_arg)
            else:
                ok, output, _ = engine.read_file(engine.state.current_node_id, path_arg)
        else:
            target_arg = parts[1].lower()
            if target_arg in ("local", "localhost", "myip", "deck", "10.99.0.2", "127.0.0.1"):
                ok, output, _ = engine.read_local_file(parts[2])
            else:
                ok, output, _ = engine.read_file(parts[1], parts[2])
        print(output)
        return True

    if action in ("download", "steal"):
        if len(parts) < 2:
            print("Usage: steal [ip] <filepath> (e.g. `steal /data/corporate_slush_fund.csv`)")
            return True
        if len(parts) == 2:
            target = engine.state.current_node_id
            filepath = parts[1]
        else:
            target = parts[1]
            filepath = parts[2]
        ok, msg, _ = engine.download_file(target, filepath)
        print(msg)
        return True

    if action in ("wipe_logs", "wipe", "clean_logs"):
        target = parts[1] if len(parts) > 1 else engine.state.current_node_id
        ok, msg = engine.wipe_logs(target)
        print(msg)
        return True

    if action == "spoof":
        ok, msg = engine.spoof_ip()
        print(msg)
        return True

    if action in ("overdrive", "od", "surge"):
        ok, msg = engine.overdrive()
        print(msg)
        return True

    if action in ("stance", "posture"):
        if len(parts) < 2:
            print(f"Current stance: {engine.deck.operating_stance.upper()} | Options: balanced, stealth, overclock, analysis")
            return True
        ok, msg = engine.set_stance(parts[1])
        print(msg)
        return True

    if action in ("proxy", "add_proxy"):
        if len(parts) < 2:
            print("Usage: proxy <breached_host> (route telemetry through a breached host, -15% trace per hop, costs 1 CPU)")
            return True
        ok, msg = engine.add_proxy_hop(parts[1])
        print(msg)
        return True

    if action in ("unproxy", "sever_proxy"):
        target = parts[1] if len(parts) > 1 else None
        ok, msg = engine.sever_proxy(target)
        print(msg)
        return True

    if action in ("quickhack", "qh"):
        if len(parts) < 2:
            print("Usage: quickhack <host> (instant breach on a tier 1-2 adjacent host at a steep CPU/trace cost)")
            return True
        ok, msg = engine.quickhack(parts[1])
        print(msg)
        return True

    if action in ("forecast", "preview", "odds"):
        act = parts[1] if len(parts) > 1 else ""
        tgt = parts[2] if len(parts) > 2 else ""
        if not act:
            print("Usage: forecast <scan|probe|overdrive|spoof|lay_low|quickhack|jackout> [target]")
            return True
        fc = engine.action_forecast(act, tgt)
        if not fc.get("ok"):
            print(f"Forecast: {act} blocked — {fc.get('reason', 'unavailable')}.")
            return True
        bits = [f"CPU {fc.get('cpu_delta', 0):+d}"]
        if fc.get("trace_gain"):
            bits.append(f"trace +{fc['trace_gain']}%")
        if fc.get("trace_reduction"):
            bits.append(f"trace -{fc['trace_reduction']}%")
        if fc.get("turns"):
            bits.append(f"{fc['turns']} turn(s)")
        print(f"Forecast {fc.get('action')}: {', '.join(bits)}. {fc.get('notes', '')}")
        return True

    if action in ("intel", "threat_intel"):
        if len(parts) < 2 or parts[1].lower() not in ("reveal", "forge"):
            print(f"Threat intel: {engine.deck.threat_intel_count} fragment(s). Usage: intel reveal <host> | intel forge")
            return True
        mode = parts[1].lower()
        target = parts[2] if len(parts) > 2 else None
        ok, msg = engine.spend_threat_intel(mode, target)
        print(msg)
        return True

    if action in ("jackout", "cash_out"):
        ok, msg = engine.jackout()
        print(msg)
        if ok:
            # Update career meta-progression through the shared run lifecycle.
            profile = save_mgr.load_career()
            engine.settle_career(profile)
            if save_mgr.save_career(profile):
                save_mgr.delete_run(engine.run_id)
                print("📂 Career progression profile updated.")
            else:
                print("❌ Career update failed: progress is NOT persisted.")
            print_run_summary(engine)
        return True

    if action == "shop":
        print_shop(
            shop,
            engine.deck,
            price_multiplier=engine.shop_price_multiplier(),
            street_discount=engine.street_standing_discount,
        )
        return True

    if action == "buy":
        if len(parts) < 2:
            print("Usage: buy <item_id> (e.g. `buy overclock_cpu`)")
            return True
        item = shop.catalog.get(parts[1])
        ok, msg = shop.purchase(engine.deck, parts[1], price_multiplier=engine.shop_price_multiplier())
        print(msg)
        if ok and (item is None or item.category != "consumable"):
            profile = save_mgr.load_career()
            profile.purchased_upgrades.append(parts[1])
            profile.banked_creds = engine.deck.cryptocreds
            save_mgr.save_career(profile)
        return True

    if action in ("myip", "whoami"):
        print(f"[*] Cyberdeck Local Identity: {engine.deck.local_hostname} ({engine.deck.local_ip}) [{engine.deck.model_name}]")
        return True

    if action in ("myfiles", "local_ls", "myloot"):
        ok, out, _ = engine.list_local_files()
        print(out)
        return True

    if action in ("phish", "spearphish"):
        if len(parts) < 2:
            print("Usage: phish <ip | hostname>")
            return True
        ok, msg, _ = engine.phish_target(parts[1])
        print(msg)
        return True

    if action in ("workshop", "recipes"):
        print_workshop(engine)
        return True

    if action == "craft":
        if len(parts) < 2:
            print_workshop(engine)
            return True
        ok, msg = engine.craft_virus(parts[1])
        print(msg)
        if ok:
            profile = save_mgr.load_career()
            profile.banked_creds = engine.deck.cryptocreds
            save_mgr.save_career(profile)
        return True

    if action in ("keylogger", "deploy_keylogger"):
        target = parts[1] if len(parts) > 1 else engine.state.current_node_id
        ok, msg = engine.deploy_daemon(target, "keylogger")
        print(msg)
        return True

    if action in ("daemons", "ps"):
        print_daemons(engine)
        return True

    if action in ("cve", "cves", "exploits"):
        print_cves(engine)
        return True

    if action in ("firewall", "fw"):
        target = parts[1] if len(parts) > 1 else engine.state.current_node_id
        ok, msg, _ = engine.get_firewall_status(target)
        print(msg)
        return True

    if action in ("bypass", "bypass_firewall"):
        if len(parts) < 3:
            print("Usage: bypass <ip> <port> [knock | fragment | tunnel] (e.g. `bypass 192.168.1.20 22 knock`)")
            return True
        target = parts[1]
        try:
            port = int(parts[2])
        except ValueError:
            print(f"❌ Invalid port '{parts[2]}'. Usage: bypass <ip> <port> [knock | fragment | tunnel]")
            return True
        method = parts[3] if len(parts) > 3 else "knock"
        ok, msg = engine.bypass_firewall(target, port, method)
        print(msg)
        return True

    if action in ("av", "antivirus", "edr"):
        target = parts[1] if len(parts) > 1 else engine.state.current_node_id
        ok, msg, _ = engine.get_antivirus_status(target)
        print(msg)
        return True

    if action in ("evade", "evade_av", "kill_av"):
        target = parts[1] if len(parts) > 1 else engine.state.current_node_id
        method = parts[2] if len(parts) > 2 else "rootkit"
        ok, msg = engine.evade_antivirus(target, method)
        print(msg)
        return True

    if action in ("social", "social_engineer", "pretext", "vishing", "bait"):
        if len(parts) < 2:
            print("Usage: social <ip> [pretext | bait | spear_phish | vishing] [employee_name]")
            return True
        target = parts[1]
        vector = parts[2] if len(parts) > 2 else (action if action in ("pretext", "vishing", "bait") else "pretext")
        emp = parts[3] if len(parts) > 3 else None
        ok, msg, _ = engine.social_engineer(target, vector=vector, employee_name=emp)
        print(msg)
        return True

    if action == "career":
        print_career(save_mgr.load_career())
        return True

    if action in ("reset_career", "reset_profile"):
        if len(parts) < 2 or parts[1].upper() != "CONFIRM":
            print("Usage: reset_career CONFIRM")
            return True
        had_career = save_mgr.career_file.exists() or save_mgr.career_file.with_suffix(".bak").exists()
        backup = save_mgr.backup_career()
        if had_career and backup is None:
            print("❌ Career backup failed; reset aborted. Your profile was not changed.")
            return True
        save_mgr.delete_career()
        save_mgr.delete_all_saves()
        fresh = CareerProfile()
        replayed = GameEngine(
            seed=engine.seed + 1,
            career_profile=fresh,
            difficulty=engine.difficulty,
        )
        engine.__dict__.update(replayed.__dict__)
        save_mgr.mark_autosave_baseline(engine)
        if backup:
            print(f"Career reset. Previous profile backed up to {backup}.")
        else:
            print("Career reset. No previous profile existed.")
        return True

    if action in ("alias", "handle"):
        if len(parts) < 2:
            print("Usage: alias <name>")
            return True
        name = " ".join(parts[1:])[:24]
        if not name.strip():
            print("Usage: alias <name>")
            return True
        profile = save_mgr.load_career()
        profile.alias = name.strip()
        if save_mgr.save_career(profile):
            print(f"Alias set to {profile.alias}.")
        else:
            print("❌ Alias could not be saved.")
        return True

    if action in ("reroll", "contract_reroll"):
        ok, msg = engine.reroll_contract_offers()
        print(msg)
        return True

    if action in ("hall", "leaderboard"):
        difficulty = parts[1].lower() if len(parts) > 1 else "all"
        if difficulty not in ("all", "easy", "normal", "hard"):
            print("Usage: hall [all|easy|normal|hard]")
            return True
        print_hall(save_mgr.load_career(), difficulty)
        return True

    if action in ("tutorial", "tips", "manual"):
        print_tutorial(engine, save_mgr.load_career())
        return True

    if action in ("rival", "rivals"):
        rival = engine.rival_summary()
        if not rival:
            print("No active rival netrunner on this grid.")
        else:
            print("\n+-------------------------------- RIVAL NETRUNNER ---------------------------+")
            print(f"[*] Handle:    {rival['name']} ({rival['handle']}) // Skill {rival['skill']}/3")
            print(f"[*] Activity:  {rival['contracts_stolen']} contract(s) stolen | next move in {rival['turns_until']} turn(s)")
            print(f"[*] Profile:   {rival['tagline']}")
            print("Counter with: counter_rival (costs 2 CPU, delays the next move by 5 turns)")
            print("+----------------------------------------------------------------------------+")
        return True

    if action in ("counter_rival", "counter_rival_netrunner", "trace_rival"):
        ok, msg = engine.counter_rival()
        print(msg)
        return True

    if action in ("replay", "seed"):
        if len(parts) < 2:
            print("Usage: replay <1-5>")
            return True
        try:
            index = int(parts[1])
        except ValueError:
            print("Usage: replay <1-5>")
            return True
        profile = save_mgr.load_career()
        history = profile.run_history[-5:] if isinstance(profile.run_history, list) else []
        if not 1 <= index <= len(history):
            print("Usage: replay <1-5>")
            return True
        record = history[-index]
        seed = record.get("seed")
        if not isinstance(seed, int):
            print("Usage: replay <1-5>")
            return True
        replayed = GameEngine(seed=seed, career_profile=profile)
        engine.__dict__.update(replayed.__dict__)
        save_mgr.mark_autosave_baseline(engine)
        print(f"Replaying run {index} // seed {seed}.")
        return True

    if action == "save":
        raw_slot = parts[1] if len(parts) > 1 else 1
        try:
            slot = save_mgr.normalize_slot(raw_slot)
        except ValueError:
            print("Usage: save [1|2|3]")
            return True
        if slot == "auto":
            print("AUTOSAVE is automatic; choose manual slot 1, 2, or 3.")
            return True
        name = " ".join(parts[2:]) if len(parts) > 2 else None
        path = save_mgr.save(engine, slot, name=name)
        if path:
            save_mgr.claim_slot(slot)
            label = save_mgr.slot_label(slot)
            if save_mgr.clean_name(name):
                label = f"{label} // {save_mgr.clean_name(name)}"
            print(f"💾 Infiltration progress saved to {label} ({path}).")
        else:
            print("❌ Save failed: the file could not be replaced after 5 attempts; progress is NOT persisted.")
        return True

    if action == "load":
        raw_slot = parts[1] if len(parts) > 1 else 1
        try:
            slot = save_mgr.normalize_slot(raw_slot)
        except ValueError:
            print("Usage: load [1|2|3|auto]")
            return True
        loaded = save_mgr.load(slot)
        if loaded:
            engine.__dict__.update(loaded.__dict__)
            print(f"📂 Loaded saved infiltration session from {save_mgr.slot_label(slot)}.")
        else:
            print(f"No saved game found in {save_mgr.slot_label(slot)}.")
        return True

    if action == "saves":
        print_save_slots(save_mgr.list_saves())
        return True

    if action in ("rename", "rename_slot"):
        if len(parts) < 2:
            print("Usage: rename <1|2|3> <name>")
            return True
        try:
            slot = save_mgr.normalize_slot(parts[1])
        except ValueError:
            print("Usage: rename <1|2|3> <name>")
            return True
        if slot == "auto":
            print("AUTOSAVE cannot be renamed.")
            return True
        name = " ".join(parts[2:])
        label = save_mgr.slot_label(slot)
        if save_mgr.rename_slot(slot, name):
            suffix = f" to '{save_mgr.clean_name(name)}'" if save_mgr.clean_name(name) else " (label cleared)"
            print(f"Renamed {label}{suffix}.")
        else:
            print(f"No checkpoint in {label}.")
        return True

    if action in ("delete", "delete_save"):
        if len(parts) < 2:
            print("Usage: delete <1|2|3|auto>")
            return True
        try:
            slot = save_mgr.normalize_slot(parts[1])
        except ValueError:
            print("Usage: delete <1|2|3|auto>")
            return True
        label = save_mgr.slot_label(slot)
        if save_mgr.has_save(slot):
            save_mgr.delete_save(slot)
            print(f"Deleted {label} checkpoint.")
        else:
            print(f"No checkpoint in {label}.")
        return True

    print(f"Unknown command: '{action}'. Commands: contract, bounty, accept_job, drop_offer, decline_contract, reroll, story, quests, contacts, contact, accept, world, news, hunter, counter, probe, exploit, cve, firewall, bypass, av, evade, social, phish, craft, workshop, keylogger, daemons, myip, myfiles, ls, cat, steal, wipe_logs, move, scan, overdrive, stance, proxy, quickhack, intel, spoof, cash_out, shop, buy, rival, counter_rival, tutorial, career, hall, alias, reset_career, status, save, load, saves, rename, delete, replay, quit")
    return True


def handle_run_completion(engine: GameEngine, save_mgr: SaveManager) -> Optional[CareerProfile]:
    """Persist career stats and clean up savegame when run concludes (victory or game-over)."""
    if engine.run_settled or not (engine.state.is_victory or engine.state.is_game_over):
        return None

    profile = save_mgr.load_career()
    if engine.state.is_victory:
        safe_print("\n🎉 MISSION SUCCESSFUL: System Core infiltrated. All unbanked loot extracted.")
    elif engine.state.is_game_over:
        safe_print("\n💀 CONNECTION TERMINATED: Security ICE traced and burned your cyberdeck.")

    engine.settle_career(profile)
    if save_mgr.save_career(profile):
        save_mgr.delete_run(engine.run_id)
    else:
        safe_print("❌ Career update failed: progress is NOT persisted.")
    print_run_summary(engine)
    return profile


def main(argv: Optional[List[str]] = None) -> int:
    setup_terminal_encoding()
    parser = argparse.ArgumentParser(prog="cyberpulse", description="Retro-cyberpunk terminal hacking simulation game")
    parser.add_argument("--version", action="version", version=f"CyberPulse {__version__}")
    parser.add_argument("--seed", type=int, default=1337, help="Deterministic world seed")
    parser.add_argument(
        "--difficulty", choices=("easy", "normal", "hard"), default="normal",
        help="Run difficulty (default: normal)",
    )
    parser.add_argument(
        "--allegiance", choices=("none", "syndicate", "street"), default="none",
        help="Starting faction patron (default: none)",
    )
    parser.add_argument("--daily", action="store_true", help="Start the deterministic daily challenge for today")
    parser.add_argument("--data-dir", type=Path, default=None, help="Savegame data directory")
    parser.add_argument("--exec", dest="commands", default=None, help="Execute semicolon-separated commands and exit")
    parser.add_argument("--auto-solve", action="store_true", help="Auto-solve hacking minigames (for testing/automation)")
    parser.add_argument("--web", action="store_true", help="Launch interactive Web Cyberdeck browser interface")
    parser.add_argument("--host", default="127.0.0.1", help="Web server bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8420, help="Web server bind port (default: 8420)")
    parser.add_argument("--no-browser", action="store_true", help="Do not automatically launch system web browser")

    args = parser.parse_args(argv)
    data_dir = args.data_dir or get_default_data_dir()
    daily_key_value, seed_value = daily_run() if args.daily else ("", args.seed)
    daily_mod = daily_modifier() if args.daily else None
    daily_modifier_id = daily_mod.modifier_id if daily_mod else ""

    # Web Cyberdeck execution mode
    if args.web:
        from cyberpulse.server import run_web
        run_web(
            host=args.host,
            port=args.port,
            data_dir=data_dir,
            seed=seed_value,
            open_browser=not args.no_browser,
            daily_key=daily_key_value,
            difficulty=args.difficulty,
            daily_modifier=daily_modifier_id,
            allegiance=args.allegiance,
        )
        return 0

    save_mgr = SaveManager(data_dir)
    career = save_mgr.load_career()
    engine = GameEngine(
        seed=seed_value,
        career_profile=career,
        difficulty=args.difficulty,
        daily_modifier=daily_modifier_id,
        allegiance=args.allegiance,
    )
    engine.daily_key = daily_key_value
    save_mgr.mark_autosave_baseline(engine)
    if args.daily:
        print(f"DAILY RUN {daily_key_value} // seed {seed_value}")
        if daily_mod:
            print(f"DAILY MODIFIER: {daily_mod.name} // {daily_mod.description}")

    # Batch script execution mode
    if args.commands:
        cmds = args.commands.split(";")
        notice_seen = engine.state.contract_notice
        for c in cmds:
            try:
                if not run_command(c, engine, save_mgr, auto_solve=args.auto_solve):
                    break
                save_mgr.autosave(engine)
                if engine.state.contract_notice and engine.state.contract_notice != notice_seen:
                    print(f"\n[!] {engine.state.contract_notice}")
                notice_seen = engine.state.contract_notice
                if engine.state.is_victory or engine.state.is_game_over:
                    break
            except EOFError:
                print("👋 Input stream closed during a minigame; stopping batch execution.")
                break
        handle_run_completion(engine, save_mgr)
        return 0

    # Interactive mode
    print("Initializing CyberPulse...")
    menu_action = show_main_menu(engine, save_mgr)
    if menu_action == "quit":
        return 0
    if menu_action == "daily":
        daily_key_value, daily_seed = daily_run()
        daily_mod = daily_modifier()
        career = save_mgr.load_career()
        engine = GameEngine(
            seed=daily_seed,
            career_profile=career,
            difficulty=args.difficulty,
            daily_modifier=daily_mod.modifier_id,
            allegiance=args.allegiance,
        )
        engine.daily_key = daily_key_value
        save_mgr.mark_autosave_baseline(engine)
        print(f"DAILY RUN {daily_key_value} // seed {daily_seed}")
        print(f"DAILY MODIFIER: {daily_mod.name} // {daily_mod.description}")
    if menu_action == "load":
        slot = choose_load_slot(save_mgr)
        loaded = save_mgr.load(slot) if slot else None
        if loaded:
            engine.__dict__.update(loaded.__dict__)
            print(f"📂 Loaded saved infiltration session from {save_mgr.slot_label(slot)}.")
        else:
            print("No saved infiltration loaded. Starting a new run.")
    print_hud(engine)
    if career.successful_runs == 0 and career.failed_runs == 0:
        print("\n[!] FIRST RUN: type `tutorial` for the five-step field manual.")
    notice_seen = engine.state.contract_notice
    while not engine.state.is_game_over and not engine.state.is_victory and not engine.state.is_jacked_out:
        try:
            line = input("\ncyberpulse> ")
            if not run_command(line, engine, save_mgr, auto_solve=args.auto_solve):
                break
            save_mgr.autosave(engine)
            if engine.state.contract_notice and engine.state.contract_notice != notice_seen:
                print(f"\n[!] {engine.state.contract_notice}")
            notice_seen = engine.state.contract_notice
        except (KeyboardInterrupt, EOFError):
            print("\n👋 Disconnected.")
            break

    handle_run_completion(engine, save_mgr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
