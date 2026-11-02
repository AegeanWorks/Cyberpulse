"""Unit tests for deterministic rival generation."""

import unittest

from cyberpulse.rivals import (
    RIVAL_ACT_PRESSURE,
    generate_rival,
    rival_move_delay,
)


class TestRivalGeneration(unittest.TestCase):
    def test_rival_is_deterministic_for_a_seed(self):
        first = generate_rival(1337)
        second = generate_rival(1337)

        self.assertEqual(first.name, second.name)
        self.assertEqual(first.handle, second.handle)
        self.assertEqual(first.skill, second.skill)
        self.assertEqual(first.next_move_turn, second.next_move_turn)

    def test_rival_fields_are_within_design_bounds(self):
        rival = generate_rival(42)

        self.assertTrue(rival.name)
        self.assertTrue(rival.handle)
        self.assertTrue(1 <= rival.skill <= 3)
        self.assertTrue(6 <= rival.next_move_turn <= 8)
        self.assertEqual(rival.contracts_stolen, 0)
        self.assertEqual(rival.status, "active")


class TestRivalActEscalation(unittest.TestCase):
    def test_pressure_table_covers_all_acts(self):
        for act in (1, 2, 3, 4):
            self.assertIn(act, RIVAL_ACT_PRESSURE)

    def test_delay_shrinks_as_acts_progress(self):
        for skill in (1, 2, 3):
            delays = [rival_move_delay(skill, act, 1) for act in (1, 2, 3, 4)]
            self.assertEqual(delays, sorted(delays, reverse=True))
            self.assertGreater(delays[0], delays[-1])

    def test_delay_respects_floor(self):
        for skill in (1, 2, 3):
            for act in (1, 2, 3, 4):
                for jitter in (0, 1, 2):
                    self.assertGreaterEqual(rival_move_delay(skill, act, jitter), 3)

    def test_unknown_act_falls_back_to_baseline(self):
        for skill in (1, 2, 3):
            self.assertEqual(rival_move_delay(skill, 99, 1), rival_move_delay(skill, 3, 1))

    def test_tick_uses_act_pressure(self):
        from cyberpulse.engine import GameEngine

        delays = {}
        for act in (1, 4):
            eng = GameEngine(seed=4242)
            eng.state.story_act = act
            eng.state.rival.next_move_turn = eng.state.turns_elapsed
            eng._tick_rival()
            delays[act] = eng.state.rival.next_move_turn - eng.state.turns_elapsed
        self.assertGreater(delays[1], delays[4])

    def test_counter_rival_still_delays_five(self):
        from cyberpulse.engine import GameEngine

        eng = GameEngine(seed=4242)
        eng.deck.cpu_cycles = eng.deck.max_cpu
        before = eng.state.rival.next_move_turn
        ok, _ = eng.counter_rival()
        self.assertTrue(ok)
        self.assertEqual(eng.state.rival.next_move_turn, before + 5)


if __name__ == "__main__":
    unittest.main()
