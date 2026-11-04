"""Batch 6 DeckOS/arcs/story regression tests."""

import unittest

from cyberpulse import deckos
from cyberpulse.arcs import arc_stage, stage_info
from cyberpulse.engine import GameEngine
from cyberpulse.story import dialogue_for


class FakeEngine:
    def __init__(self):
        from cyberpulse.models import GameState
        self.state = GameState(seed=1, current_node_id="node_gateway")
        self.deck = type("D", (), {"active_daemons": []})()


class TestBatch6(unittest.TestCase):
    def test_kill_rejects_float_and_bool_pid(self):
        e = GameEngine(seed=1)
        ok, msg = deckos.kill_process(e, 3.5)
        self.assertFalse(ok)
        self.assertIn("Invalid PID", msg)
        ok2, _ = deckos.kill_process(e, True)
        self.assertFalse(ok2)

    def test_history_repairs_corrupt_shape(self):
        e = FakeEngine()
        e.state.cmd_history = "oops"
        deckos.record_history(e, "newcmd")
        self.assertIsInstance(e.state.cmd_history, list)
        self.assertIn("newcmd", e.state.cmd_history)
        e.state.cmd_history = {"bad": 1}
        deckos.record_history(e, "again")
        self.assertIn("again", e.state.cmd_history)

    def test_arc_stage_rejects_non_numeric(self):
        self.assertEqual(arc_stage("mira", "abc"), 0)
        self.assertEqual(arc_stage("mira", None), 0)
        self.assertEqual(stage_info("mira", "abc"), {"label": "", "text": "", "bonus": ""})
        self.assertEqual(stage_info("mira", 99), {"label": "", "text": "", "bonus": ""})

    def test_locked_contact_dialogue_no_spoiler(self):
        self.assertEqual(dialogue_for("archivist", 1), "The channel is quiet. Earn access to this operative.")
        self.assertEqual(dialogue_for("zero", 1), "The channel is quiet. Earn access to this operative.")
        self.assertNotEqual(dialogue_for("archivist", 2), dialogue_for("archivist", 1))
        self.assertIn("Mira", dialogue_for("mira", 1))

    def test_cold_wallet_reconcile_after_prior_loot(self):
        e = GameEngine(seed=1337)
        e.state.story_act = 2
        e._sync_story_quests()
        e.complete_breach("node_proxy_a")
        e.complete_breach("node_proxy_b")
        e.download_file("node_proxy_a", "/home/admin/network_map.txt")
        e.download_file("node_proxy_b", "/home/secops/credentials.bak")
        from unittest.mock import patch
        with patch.object(e, "_contact_trust", return_value=2):
            # ensure kilo trust meets required_trust=2 for q_arc_cold_wallet
            for c in e.state.contacts:
                if c.contact_id == "kilo":
                    c.trust = 2
            ok, msg = e.accept_quest("q_arc_cold_wallet")
        q = next(q for q in e.state.quests if q.quest_id == "q_arc_cold_wallet")
        self.assertTrue(q.completed)
        self.assertGreaterEqual(q.progress, 2)


if __name__ == "__main__":
    unittest.main()
