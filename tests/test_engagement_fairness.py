"""Fairness proofs for the engagement loop: honest odds, capped comebacks, no farms.

All claims pair with a measurement (deterministic seeds). No behavior is
changed here; these tests lock in the numbers the design asserts.
"""

import random
import unittest

from cyberpulse.engine import GameEngine
from cyberpulse.models import CareerProfile, Node, NodeType
from cyberpulse.puzzles import FrequencyPuzzle
from cyberpulse.rewards import REWARD_SCHEDULE, roll_breach_reward
from cyberpulse.world import apply_resecure


class FixedRng:
    def __init__(self, roll):
        self.roll = roll

    def random(self):
        return self.roll

    def choice(self, seq):
        return seq[0]


def make_node(base=200):
    return Node(
        node_id="vault_fair",
        name="Fair Vault",
        node_type=NodeType.DATA_VAULT,
        security_level=2,
        credits_reward=base,
    )


def bisect_solve_rate(tier, seeds=50):
    """Scripted bisection solver over fixed seeds; returns solve fraction."""
    solved = 0
    for seed in range(seeds):
        puzzle = FrequencyPuzzle.generate(seed, security_level=tier)
        lo, hi = puzzle.min_freq, puzzle.max_freq
        for _ in range(3):
            guess = (lo + hi) / 2.0
            ok, msg = puzzle.tune(guess)
            if ok:
                solved += 1
                break
            if "TOO HIGH" in msg:
                hi = guess
            else:
                lo = guess
    return solved / seeds


class TestRewardBands(unittest.TestCase):
    def test_band_edges_match_stated_schedule(self):
        chip = REWARD_SCHEDULE["chip_rate"]
        edge = chip + REWARD_SCHEDULE["jackpot_rate"]
        _, _, drop = roll_breach_reward(make_node(), rng=FixedRng(chip - 1e-9))
        self.assertIsNotNone(drop)
        creds, desc, drop = roll_breach_reward(make_node(), rng=FixedRng(chip + 1e-9))
        self.assertIsNone(drop)
        self.assertIn("JACKPOT", desc)
        creds, desc, drop = roll_breach_reward(make_node(), rng=FixedRng(edge + 1e-9))
        self.assertIsNone(drop)
        self.assertNotIn("JACKPOT", desc)

    def test_jackpot_math_is_exact(self):
        chip = REWARD_SCHEDULE["chip_rate"]
        numer = REWARD_SCHEDULE["jackpot_numer"]
        denom = REWARD_SCHEDULE["jackpot_denom"]
        for base in (60, 100, 101, 200, 350):
            creds, _, _ = roll_breach_reward(make_node(base), rng=FixedRng(chip + 0.01))
            self.assertEqual(creds, base * numer // denom)

    def test_distribution_matches_stated_70_20_10(self):
        rng = random.Random(1234)
        node = make_node()
        chip = jackpot = 0
        n = 20000
        for _ in range(n):
            creds, _, drop = roll_breach_reward(node, rng=rng)
            if drop is not None:
                chip += 1
            elif creds > node.credits_reward:
                jackpot += 1
        self.assertAlmostEqual(chip / n, 0.10, delta=0.02)
        self.assertAlmostEqual(jackpot / n, 0.20, delta=0.02)


class TestSurgeAndForecastParity(unittest.TestCase):
    def test_extraction_preview_equals_applied_surge(self):
        for difficulty in ("easy", "normal", "hard"):
            for dampener in (0, 2):
                for trace in (0, 49, 50, 69, 70, 84, 85, 99):
                    engine = GameEngine(seed=7, difficulty=difficulty)
                    engine.deck.ice_dampener_level = dampener
                    engine.state.trace_percent = trace
                    risk = engine.extraction_risk()
                    expected = engine.mitigated_trace(engine.extraction_surge())
                    self.assertEqual(risk["surge"], expected)
                    self.assertEqual(risk["projected_trace"], min(100, trace + expected))
                    self.assertEqual(risk["lethal"], risk["projected_trace"] >= 100)

    def test_forecast_costs_match_engine_costs(self):
        cases = 0
        for difficulty in ("easy", "normal", "hard"):
            engine = GameEngine(seed=7, difficulty=difficulty)
            for action, raw, target in (
                ("scan", 5, ""),
                ("probe", 4, "node_gateway"),
                ("overdrive", 8, ""),
            ):
                forecast = engine.action_forecast(action, target)
                if forecast["ok"]:
                    self.assertEqual(forecast["trace_gain"], engine.mitigated_trace(raw))
                    cases += 1
        self.assertGreater(cases, 0)


class TestPuzzleSolvability(unittest.TestCase):
    def test_tier_curve_is_fair_then_hard(self):
        # Measured 2026-11-04 with the scripted bisection solver (50 seeds):
        # tier1=0.94 tier2=0.86 tier3=0.12 (quickhack is the intended tier-3 path).
        tier1 = bisect_solve_rate(1)
        tier2 = bisect_solve_rate(2)
        tier3 = bisect_solve_rate(3)
        self.assertGreaterEqual(tier1, 0.85)
        self.assertGreaterEqual(tier2, 0.75)
        self.assertGreaterEqual(tier1, tier2)
        self.assertGreaterEqual(tier2, tier3)
        self.assertLess(tier3, 0.30)

    def test_near_miss_grants_exactly_one_comeback(self):
        puzzle = FrequencyPuzzle.generate(3, security_level=3)
        target = puzzle.target_freq
        tol = puzzle.tolerance
        guess = target + tol * 2.0  # inside the window, outside tolerance
        ok, msg = puzzle.tune(guess)
        self.assertFalse(ok)
        self.assertTrue(puzzle.near_miss)
        self.assertTrue(puzzle.claim_near_miss_bonus())
        self.assertFalse(puzzle.claim_near_miss_bonus())


class TestExploitProbes(unittest.TestCase):
    def test_resecured_host_pays_nothing(self):
        engine = GameEngine(seed=42)
        engine.scan_surroundings()
        current = engine.get_current_node()
        target = next(n for n in current.connected_ids if n in engine.nodes)
        ok, _ = engine.complete_breach(target)
        self.assertTrue(ok)
        unbanked_after_first = engine.state.unbanked_creds
        combo_after_first = engine.state.combo_streak
        apply_resecure(engine.nodes[target])
        ok, msg = engine.complete_breach(target)
        self.assertTrue(ok)
        self.assertIn("No fresh data", msg)
        self.assertEqual(engine.state.unbanked_creds, unbanked_after_first)
        self.assertEqual(engine.state.combo_streak, combo_after_first)

    def test_overdrive_is_bounded_by_cpu(self):
        engine = GameEngine(seed=42)
        uses = 0
        while True:
            before = engine.state.unbanked_creds
            ok, _ = engine.overdrive()
            if not ok:
                break
            uses += 1
            self.assertEqual(engine.state.unbanked_creds - before, 10)
        self.assertEqual(uses, 5)  # 10 CPU / 2 per use on a fresh deck
        ok, msg = engine.overdrive()
        self.assertFalse(ok)
        self.assertIn("CPU", msg)

    def test_daemon_plus_lay_low_advances_the_clock(self):
        engine = GameEngine(seed=42)
        engine.scan_surroundings()
        current = engine.get_current_node()
        target = next(n for n in current.connected_ids if n in engine.nodes)
        ok, _ = engine.complete_breach(target)
        self.assertTrue(ok)
        ok, _ = engine.deploy_daemon(target)
        self.assertTrue(ok)
        turns_before = engine.state.turns_elapsed
        banked_before = engine.state.unbanked_creds
        ok, _ = engine.lay_low(2)
        self.assertTrue(ok)
        self.assertEqual(engine.state.turns_elapsed, turns_before + 2)
        self.assertGreater(engine.state.unbanked_creds, banked_before)
        self.assertLessEqual(engine.state.trace_percent, 100)

    def test_worm_chip_is_consumed(self):
        engine = GameEngine(seed=42)
        engine.scan_surroundings()
        current = engine.get_current_node()
        target = next(n for n in current.connected_ids if n in engine.nodes)
        engine.deck.exploits.append("worm_replicator")
        ok, _ = engine.use_exploit("worm_replicator", target)
        self.assertTrue(ok)
        self.assertNotIn("worm_replicator", engine.deck.exploits)


class TestScriptedSessions(unittest.TestCase):
    def test_scripted_run_is_deterministic(self):
        from scripts.engagement_sim import run_scripted_session

        first = run_scripted_session(1000)
        second = run_scripted_session(1000)
        self.assertEqual(first, second)

    def test_gentle_runs_settle_without_lockout(self):
        from scripts.engagement_sim import run_scripted_session

        for seed in range(1000, 1012):
            session = run_scripted_session(seed)
            self.assertTrue(session["settled"], f"seed {seed} did not settle")
            self.assertFalse(session["lockout"], f"seed {seed} locked out")
            self.assertTrue(session["jacked_out"], f"seed {seed} did not extract")


if __name__ == "__main__":
    unittest.main()
