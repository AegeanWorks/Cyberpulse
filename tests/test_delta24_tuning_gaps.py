"""Delta-24: lock in tuning-table single-source gaps found since last 3 pushes."""
import unittest

from cyberpulse import deckos
from cyberpulse.arcs import arc_status, district_grid, live_bonuses
from cyberpulse.engine import GameEngine
from cyberpulse import rewards
from cyberpulse.rewards import REWARD_SCHEDULE
from cyberpulse import scoring


class TestDaemonForecastSingleSource(unittest.TestCase):
    def test_forecast_uses_daemon_constants(self):
        e = GameEngine(seed=7)
        e.scan_surroundings()
        current = e.get_current_node()
        target = next(n for n in current.connected_ids if n in e.nodes)
        # breach first so deploy/daemon forecast path is reachable
        ok, _ = e.complete_breach(target)
        self.assertTrue(ok)
        forecast = e.action_forecast("deploy", target)
        self.assertTrue(forecast["ok"])
        expected = e.DAEMON_BASE_YIELD + e.nodes[target].security_level * e.DAEMON_YIELD_PER_SECURITY
        self.assertIn(f"+{expected} ", forecast["notes"])
        self.assertIn(f"+{e.DAEMON_DETECTION_RISK}%", forecast["notes"])

    def test_deploy_and_forecast_agree_on_base(self):
        e = GameEngine(seed=7)
        e.scan_surroundings()
        current = e.get_current_node()
        target = next(n for n in current.connected_ids if n in e.nodes)
        e.complete_breach(target)
        forecast = e.action_forecast("deploy", target)
        ok, msg = e.deploy_daemon(target)
        self.assertTrue(ok)
        # both surfaces state the same base yield number
        expected = e.DAEMON_BASE_YIELD + e.nodes[target].security_level * e.DAEMON_YIELD_PER_SECURITY
        self.assertIn(f"+{expected}", forecast["notes"])
        self.assertIn(f"+{expected}", msg)


class TestDeckOSHardening(unittest.TestCase):
    def test_sysinfo_load_survives_hostile_cpu(self):
        e = GameEngine(seed=1)
        # poison a process cpu via hostile daemon shape
        e.state.turns_elapsed = 0
        info = deckos.sysinfo(e)
        self.assertIsInstance(info["load"], int)
        # inject hostile cpu directly through procs monkeypatch
        orig = deckos.list_processes
        try:
            deckos.list_processes = lambda eng: [{"pid": 1, "cpu": float("inf")}, {"pid": 2, "cpu": "x"}]
            info = deckos.sysinfo(e)
            self.assertEqual(info["load"], 0)
        finally:
            deckos.list_processes = orig

    def test_kill_process_survives_huge_int(self):
        e = GameEngine(seed=1)
        ok, msg = deckos.kill_process(e, 10 ** 100)
        self.assertFalse(ok)
        self.assertIsInstance(msg, str)

    def test_recent_history_bool_limit(self):
        e = GameEngine(seed=1)
        out = deckos.recent_history(e, True)
        self.assertIsInstance(out, list)


class TestArcsHardening(unittest.TestCase):
    def test_arc_status_survives_hostile_trust(self):
        e = GameEngine(seed=1)
        for c in e.state.contacts:
            c.trust = float("inf")
        out = arc_status(e.state.contacts)
        self.assertTrue(all(r["trust"] == 0 for r in out))

    def test_live_bonuses_survives_hostile_trust(self):
        e = GameEngine(seed=1)
        for c in e.state.contacts:
            c.trust = "hostile"
        live = live_bonuses(e)
        self.assertFalse(any(live.values()))

    def test_district_grid_survives_hostile_alert(self):
        rows = district_grid(float("inf"), float("nan"), "x")
        self.assertEqual(len(rows), 5)

    def test_contact_trust_survives_inf(self):
        e = GameEngine(seed=1)
        e.state.contacts[0].trust = float("inf")
        self.assertEqual(e._contact_trust(e.state.contacts[0].contact_id), 0)

    def test_hop_latency_survives_inf(self):
        class Fake:
            security_level = float("inf")
            node_id = "n"
        self.assertIsInstance(GameEngine.hop_latency_ms(Fake()), int)


class TestRewardAliases(unittest.TestCase):
    def test_aliases_track_schedule(self):
        old_chip = REWARD_SCHEDULE["chip_rate"]
        REWARD_SCHEDULE["chip_rate"] = 0.33
        try:
            self.assertEqual(rewards.CHIP_DROP_RATE, 0.33)
        finally:
            REWARD_SCHEDULE["chip_rate"] = old_chip
        self.assertEqual(rewards.CHIP_DROP_RATE, old_chip)


class TestScoringResilience(unittest.TestCase):
    def test_mutated_weights_fall_back(self):
        backup = dict(scoring.SCORE_WEIGHTS)
        try:
            scoring.SCORE_WEIGHTS["combo"] = float("inf")
            del scoring.SCORE_WEIGHTS["quests"]
            res = scoring.score_run(gained=100, best_combo=2, quests_done=1,
                                    nodes_breached=1, outcome="victory",
                                    contract_completed=True, main_story_complete=True)
            self.assertIsInstance(res["score"], int)
            # fallback 150 * 1 = 150 when key missing
            self.assertEqual(res["breakdown"]["quests"], 150)
        finally:
            scoring.SCORE_WEIGHTS.clear()
            scoring.SCORE_WEIGHTS.update(backup)


if __name__ == "__main__":
    unittest.main()
