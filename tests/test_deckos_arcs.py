"""DeckOS computer simulation + operative arcs + district sim (Cyberpulse 0.5.0)."""

import io
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from cyberpulse.arcs import arc_stage, arc_status, district_grid, ensure_arc_quests
from cyberpulse.cli import main as cli_main
from cyberpulse.deckos import kill_process, list_processes, recent_history, record_history, sysinfo
from cyberpulse.engine import GameEngine


class DeckOSTest(unittest.TestCase):
    def setUp(self):
        self.engine = GameEngine(seed=1337)

    def test_process_table_has_base_system_procs(self):
        procs = list_processes(self.engine)
        names = [p["name"] for p in procs]
        for expected in ("init", "netstack", "iced", "cryptod", "questd"):
            self.assertIn(expected, names)

    def test_sysinfo_reports_uptime_and_specs(self):
        info = sysinfo(self.engine)
        for key in ("hostname", "ip", "cpu", "trace", "uptime", "banked", "unbanked"):
            self.assertIn(key, info)

    def test_kill_unknown_pid_fails(self):
        ok, msg = kill_process(self.engine, 9999)
        self.assertFalse(ok)
        self.assertIn("No process", msg)

    def test_kill_protected_proc_fails(self):
        ok, msg = kill_process(self.engine, 1)
        self.assertFalse(ok)
        self.assertIn("protected", msg)

    def test_kill_invalid_pid_returns_false(self):
        for bad in ("abc", None, "3.5"):
            ok, _ = kill_process(self.engine, bad)
            self.assertFalse(ok)

    def test_recent_history_invalid_limit_falls_back(self):
        record_history(self.engine, "scan")
        self.assertEqual(recent_history(self.engine, "abc"), ["scan"])

    def test_history_roundtrip(self):
        record_history(self.engine, "scan")
        record_history(self.engine, "ps")
        self.assertEqual(recent_history(self.engine, 2)[-2:], ["scan", "ps"])

    def test_engine_summaries_present(self):
        deckos = self.engine.deckos_summary()
        self.assertIn("processes", deckos)
        arcs = self.engine.arcs_summary()
        self.assertEqual(len(arcs["arcs"]), 4)
        districts = self.engine.district_summary()["districts"]
        self.assertEqual(len(districts), 5)
        world = self.engine.world_summary()
        self.assertEqual(len(world["districts"]), 5)


class ArcsTest(unittest.TestCase):
    def setUp(self):
        self.engine = GameEngine(seed=42)

    def test_arc_stages_start_at_zero(self):
        for contact in self.engine.state.contacts:
            self.assertEqual(arc_stage(contact.contact_id, contact.trust), 0)

    def test_arc_stage_thresholds(self):
        self.assertEqual(arc_stage("mira", 2), 1)
        self.assertEqual(arc_stage("mira", 4), 2)
        self.assertEqual(arc_stage("mira", 6), 3)

    def test_arc_quests_backfilled_for_new_runs(self):
        ids = {q.quest_id for q in self.engine.state.quests}
        self.assertIn("q_arc_cold_wallet", ids)
        self.assertIn("q_arc_dead_letter", ids)

    def test_arc_quests_backfilled_for_old_saves(self):
        self.engine.state.quests = [q for q in self.engine.state.quests
                                    if not q.quest_id.startswith("q_arc_")]
        added = ensure_arc_quests(self.engine)
        self.assertEqual(added, 2)

    def test_district_grid_deterministic(self):
        first = district_grid(7, 3, 60)
        second = district_grid(7, 3, 60)
        self.assertEqual(first, second)
        self.assertEqual(len(first), 5)


if __name__ == "__main__":
    unittest.main()


class CLIParityTest(unittest.TestCase):
    def test_deckos_arcs_districts_forecast_commands(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = cli_main([
                "--data-dir", str(tmp), "--seed", "1337", "--exec",
                "ps; arcs; districts; history; sysinfo; uptime; forecast counter_rival; contract",
            ])
        self.assertEqual(code, 0)
        out = buf.getvalue()
        for marker in ("DECKOS", "OPERATIVE ARCS", "DISTRICTS", "Forecast counter_rival"):
            self.assertIn(marker, out)
        from cyberpulse.arcs import DISTRICTS as _DISTRICTS
        self.assertIn("SYNDICATE JOB BOARD", out)
        self.assertTrue(any(d["name"] in out for d in _DISTRICTS))
