"""Delta-23 failing-first: hostile numerics must not crash DeckOS/arcs helpers."""
import unittest
from cyberpulse import deckos
from cyberpulse.arcs import arc_stage, stage_info
from cyberpulse.engine import GameEngine


class TestDelta23Hardening(unittest.TestCase):
    def test_recent_history_survives_inf(self):
        e = GameEngine(seed=1)
        # must not raise OverflowError
        out = deckos.recent_history(e, float("inf"))
        self.assertIsInstance(out, list)

    def test_arc_stage_survives_inf(self):
        self.assertEqual(arc_stage("mira", float("inf")), 0)
        self.assertEqual(arc_stage("mira", float("nan")), 0)

    def test_stage_info_survives_inf(self):
        self.assertEqual(stage_info("mira", float("inf")),
                         {"label": "", "text": "", "bonus": ""})

    def test_sysinfo_survives_hostile_deck(self):
        e = GameEngine(seed=1)
        e.deck.max_cpu = float("inf")
        e.deck.cpu_cycles = float("nan")
        info = deckos.sysinfo(e)
        self.assertIsInstance(info, dict)

    def test_list_processes_survives_hostile_turn(self):
        e = GameEngine(seed=1)
        e.state.turns_elapsed = float("inf")
        procs = deckos.list_processes(e)
        self.assertIsInstance(procs, list)


if __name__ == "__main__":
    unittest.main()
