"""Deterministic scripted play sessions for CyberPulse (stdlib only).

Each session plays a gentle but complete run with fixed seeds: scan, probe,
breach every reachable host, one overdrive, one daemon plus lay_low, then
jackout and settle. Prints an aggregate measurement (session length, return
signals, choice distribution, reward variance experienced) — never "fun".

Usage: python scripts/engagement_sim.py [num_sessions] [first_seed]
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cyberpulse.engine import GameEngine
from cyberpulse.models import CareerProfile, NodeStatus, NodeType


def reachable_targets(engine):
    """Hosts the runner may legally breach from its current position."""
    current = engine.get_current_node()
    out = []
    for node_id in current.connected_ids:
        node = engine.nodes.get(node_id)
        if node is None or node.status == NodeStatus.BREACHED:
            continue
        if node.node_type == NodeType.CENTRAL_CORE:
            continue
        ok, _ = engine.can_hack_node(node_id)
        if ok:
            out.append(node_id)
    return out


def run_scripted_session(seed, use_overdrive=True, use_daemon=True):
    """Play one gentle deterministic run; return its measurement dict."""
    engine = GameEngine(seed=seed)
    choices = {
        "stance": "balanced",
        "offers_seen": len(engine.state.contract_offers),
        "offer_accepted": None,
        "overdrive_used": 0,
        "daemon_used": False,
        "lay_low_used": 0,
    }
    engine.scan_surroundings()
    breached = 0
    reward_seen = {"standard": 0, "jackpot": 0, "chip": 0}
    progress = True
    while progress and not engine.state.is_game_over and breached < 12:
        progress = False
        for node_id in reachable_targets(engine):
            ok, _, _ = engine.probe_host(engine.nodes[node_id].ip_address)
            ok, msg = engine.complete_breach(node_id)
            if not ok:
                continue
            breached += 1
            progress = True
            if "JACKPOT" in msg:
                reward_seen["jackpot"] += 1
            elif "EXPLOIT CHIP" in msg:
                reward_seen["chip"] += 1
            else:
                reward_seen["standard"] += 1
            engine.move_to(node_id)
            if use_overdrive and breached == 2:
                ok, _ = engine.overdrive()
                choices["overdrive_used"] += 1 if ok else 0
            if use_daemon and breached == 3 and engine.deck.cpu_cycles >= 2:
                ok, _ = engine.deploy_daemon(node_id)
                if ok:
                    choices["daemon_used"] = True
                    ok, _ = engine.lay_low(2)
                    choices["lay_low_used"] += 2 if ok else 0
            if engine.state.is_game_over:
                break
    chips_held = [chip for chip in engine.deck.exploits if chip not in ("port_scan", "buffer_overflow", "spoof_ip")]
    current = engine.get_current_node()
    jacked_out = False
    if current.status == NodeStatus.BREACHED and not engine.state.is_game_over:
        ok, _ = engine.jackout()
        jacked_out = ok
    profile = CareerProfile()
    settled = engine.settle_career(profile)
    history = profile.run_history[-1] if profile.run_history else {}
    return {
        "seed": seed,
        "turns": engine.state.turns_elapsed,
        "breached": breached,
        "trace": engine.state.trace_percent,
        "unbanked": engine.state.unbanked_creds,
        "banked": engine.deck.cryptocreds,
        "jacked_out": jacked_out,
        "lockout": engine.state.is_game_over,
        "settled": settled,
        "net_gain": history.get("gained", 0),
        "score": history.get("score", 0),
        "chips_held": chips_held,
        "reward_seen": reward_seen,
        "choices": choices,
    }


def summarize(seeds):
    """Aggregate scripted sessions into one measurement dict."""
    sessions = [run_scripted_session(seed) for seed in seeds]
    total = len(sessions)
    gentle = [s for s in sessions if s["jacked_out"]]
    summary = {
        "sessions": total,
        "jackout_rate": (sum(1 for s in sessions if s["jacked_out"]) / total) if total else 0,
        "lockout_rate": (sum(1 for s in sessions if s["lockout"]) / total) if total else 0,
        "mean_turns": sum(s["turns"] for s in sessions) / total if total else 0,
        "mean_breached": sum(s["breached"] for s in sessions) / total if total else 0,
        "mean_net_gain": sum(s["net_gain"] for s in sessions) / total if total else 0,
        "mean_score": sum(s["score"] for s in sessions) / total if total else 0,
        "overdrive_uptake": sum(s["choices"]["overdrive_used"] > 0 for s in sessions),
        "daemon_uptake": sum(s["choices"]["daemon_used"] for s in sessions),
        "mean_offers_seen": sum(s["choices"]["offers_seen"] for s in sessions) / total if total else 0,
        "reward_seen": {
            key: sum(s["reward_seen"][key] for s in sessions)
            for key in ("standard", "jackpot", "chip")
        },
        "chips_held_total": sum(len(s["chips_held"]) for s in sessions),
    }
    summary["gentle_sessions"] = len(gentle)
    return summary


def main(argv):
    count = int(argv[1]) if len(argv) > 1 else 12
    first_seed = int(argv[2]) if len(argv) > 2 else 1000
    seeds = list(range(first_seed, first_seed + count))
    summary = summarize(seeds)
    print(f"sessions={summary['sessions']} seeds={first_seed}-{first_seed + count - 1}")
    print(f"jackout_rate={summary['jackout_rate']:.2f} lockout_rate={summary['lockout_rate']:.2f}")
    print(f"mean_turns={summary['mean_turns']:.1f} mean_breached={summary['mean_breached']:.1f}")
    print(f"mean_net_gain={summary['mean_net_gain']:.1f} mean_score={summary['mean_score']:.1f}")
    print(f"overdrive_uptake={summary['overdrive_uptake']} daemon_uptake={summary['daemon_uptake']} mean_offers_seen={summary['mean_offers_seen']:.1f}")
    seen = summary["reward_seen"]
    total_breaches = sum(seen.values()) or 1
    print(f"reward_seen standard={seen['standard']} jackpot={seen['jackpot']} chip_drops={seen['chip']} new_chips_held={summary['chips_held_total']} (over {total_breaches} breaches)")
    return summary


if __name__ == "__main__":
    main(sys.argv)
