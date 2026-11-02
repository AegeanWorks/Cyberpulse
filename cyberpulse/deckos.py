"""In-game DeckOS computer simulation: processes, sysinfo, uptime, command history.

Pure, deterministic helpers over GameEngine state. No RNG mutation: PIDs and
rogue-miner spawns derive from (seed, turn) so saves and replays stay stable.
"""

from typing import Any, Dict, List, Tuple

BASE_PROCESSES = (
    ("init", "deck init", "system"),
    ("netstack", "mesh routing + proxy hops", "system"),
    ("iced", "ICE trace monitor", "system"),
    ("cryptod", "wallet + bank ledger", "system"),
    ("questd", "contract + quest tracker", "system"),
)


def _rogue_present(seed: int, turn: int, alert: int) -> bool:
    """A rogue miner squats on the deck when the grid is hot (deterministic)."""
    if alert < 40:
        return False
    return ((int(seed) + int(turn) * 7) % 5) == 0


def list_processes(engine: Any) -> List[Dict[str, Any]]:
    """Build the DeckOS process table from live engine state."""
    state = engine.state
    deck = engine.deck
    turn = int(getattr(state, "turns_elapsed", 0))
    seed = int(getattr(engine, "seed", 0))
    alert = int(getattr(state.world, "alert_level", 0)) if hasattr(state, "world") else 0
    procs: List[Dict[str, Any]] = []
    pid = 1
    for name, desc, owner in BASE_PROCESSES:
        procs.append({"pid": pid, "name": name, "desc": desc, "owner": owner,
                      "cpu": 0, "killable": False})
        pid += 1
    for daemon in list(getattr(deck, "active_daemons", [])):
        dtype = getattr(daemon, "daemon_type", "daemon")
        host = getattr(daemon, "host_ip", "?")
        procs.append({"pid": pid, "name": f"{dtype}[{host}]",
                      "desc": f"passive listener on {host}", "owner": "user",
                      "cpu": 0, "killable": True,
                      "daemon_host": host, "daemon_type": dtype})
        pid += 1
    hunters = list(getattr(state.world, "hunters", [])) if hasattr(state, "world") else []
    active = [h for h in hunters if getattr(h, "status", "") in ("hunting", "confused", "intercepted")]
    for hunter in active:
        hood = engine.host_district(hunter.current_node_id)
        procs.append({"pid": pid, "name": "netwatch_probe",
                      "desc": f"hunter {getattr(hunter, 'name', '?')} sweeping {hood['district']} grid",
                      "owner": "netwatch", "cpu": 1, "killable": False})
        pid += 1
    if _rogue_present(seed, turn, alert):
        procs.append({"pid": pid, "name": "rogue_miner",
                      "desc": "unauthorized miner hogging 1 CPU (kill to reclaim)",
                      "owner": "rogue", "cpu": 1, "killable": True})
    return procs


def sysinfo(engine: Any) -> Dict[str, Any]:
    """Snapshot of the deck as a computer: specs, load, uptime, threat."""
    state = engine.state
    deck = engine.deck
    world = getattr(state, "world", None)
    turn = int(getattr(state, "turns_elapsed", 0))
    minutes_total = turn * 15
    uptime = f"{minutes_total // 60}h {minutes_total % 60:02d}m ({turn} turns)"
    max_cpu = int(getattr(deck, "max_cpu", 0))
    cpu = int(getattr(deck, "cpu_cycles", 0))
    procs = list_processes(engine)
    load = sum(int(p.get("cpu", 0)) for p in procs)
    return {
        "hostname": getattr(deck, "local_hostname", "rig.netrunner.local"),
        "ip": getattr(deck, "local_ip", "10.99.0.2"),
        "cpu": f"{cpu}/{max_cpu}",
        "cpu_free": max(0, max_cpu - cpu),
        "trace": int(getattr(state, "trace_percent", 0)),
        "alert": int(getattr(world, "alert_level", 0)) if world else 0,
        "uptime": uptime,
        "turns": turn,
        "processes": len(procs),
        "load": load,
        "ram_mb": int(getattr(deck, "max_ram_mb", 256)) if hasattr(deck, "max_ram_mb") else 256,
        "banked": int(getattr(deck, "cryptocreds", 0)),
        "unbanked": int(getattr(state, "unbanked_creds", 0)),
    }


def kill_process(engine: Any, pid: int) -> Tuple[bool, str]:
    """Terminate a killable DeckOS process. Rogue miners free CPU; daemons are recalled."""
    procs = list_processes(engine)
    target = next((p for p in procs if p["pid"] == int(pid)), None)
    if target is None:
        return False, f"No process with PID {pid}. Run `ps` to list the table."
    if not target.get("killable"):
        return False, f"PID {pid} ({target['name']}) is protected and cannot be killed."
    if target["name"] == "rogue_miner":
        engine.regenerate_cpu(1)
        engine._log_story(f"DeckOS reclaimed 1 CPU from rogue_miner (PID {pid}).")
        return True, f"Killed rogue_miner (PID {pid}): reclaimed 1 CPU cycle."
    # User daemon: recall it gracefully (stops its income, no trace penalty).
    host = target.get("daemon_host", "")
    removed = 0
    for daemon in list(getattr(engine.deck, "active_daemons", [])):
        if getattr(daemon, "host_ip", "") == host and getattr(daemon, "daemon_type", "") == target.get("daemon_type"):
            try:
                engine.deck.active_daemons.remove(daemon)
                removed += 1
                break
            except ValueError:
                break
    if removed:
        engine._log_story(f"DeckOS recalled daemon {target['name']} (PID {pid}).")
        return True, f"Recalled daemon {target['name']} (PID {pid}). Its income stops; host stays breached."
    return False, f"PID {pid} already exited."


def record_history(engine: Any, cmd_line: str) -> None:
    """Append a command to the run-scoped history (bounded, backfilled).

    Corrupt or foreign state shapes are skipped by type checks instead of
    exception handling, so history can never break command dispatch.
    """
    state = getattr(engine, "state", None)
    if state is None:
        return
    hist = getattr(state, "cmd_history", None)
    if hist is None:
        hist = []
        state.cmd_history = hist
    if not isinstance(hist, list):
        return
    text = str(cmd_line).strip()[:160]
    if text:
        hist.append(text)
        if len(hist) > 100:
            del hist[:-100]


def recent_history(engine: Any, limit: int = 10) -> List[str]:
    hist = list(getattr(engine.state, "cmd_history", []) or [])
    limit = max(1, min(50, int(limit)))
    return hist[-limit:]
