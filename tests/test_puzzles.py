"""Unit tests for CyberPulse hacking mini-game puzzles."""

import unittest
from cyberpulse.puzzles import BufferPuzzle, FrequencyPuzzle, HashCrackPuzzle, puzzle_from_dict


class TestPuzzles(unittest.TestCase):
    def test_frequency_puzzle_tuning(self):
        puzzle = FrequencyPuzzle(target_freq=50.0, tolerance=0.5)
        # Off target
        success, msg = puzzle.tune(40.0)
        self.assertFalse(success)
        self.assertIn("TOO LOW", msg)

        # On target
        success, msg = puzzle.tune(50.2)
        self.assertTrue(success)
        self.assertIn("RESONANCE LOCKED", msg)

    def test_frequency_exhaustion(self):
        puzzle = FrequencyPuzzle(target_freq=50.0, tolerance=0.2)
        puzzle.tune(10.0)
        puzzle.tune(10.0)
        success, msg = puzzle.tune(10.0)
        self.assertFalse(success)
        self.assertIn("FAILED", msg)

    def test_buffer_puzzle_verification(self):
        puzzle = BufferPuzzle(
            matrix=[["1C", "FF"], ["7A", "BD"]],
            target_seq=["1C", "7A"],
        )
        # Invalid sequence
        ok, msg = puzzle.verify_sequence(["1C", "BD"])
        self.assertFalse(ok)
        self.assertIn("CORRUPTION", msg)

        # Correct sequence
        ok, msg = puzzle.verify_sequence(["1C", "7A"])
        self.assertTrue(ok)
        self.assertIn("EXPLOIT EXECUTED", msg)

    def test_frequency_near_miss_grants_one_bonus_attempt(self):
        puzzle = FrequencyPuzzle(target_freq=50.0, tolerance=0.8)
        ok, _ = puzzle.tune(51.9)
        self.assertFalse(ok)
        self.assertTrue(puzzle.near_miss)
        self.assertEqual(puzzle.attempts_left, 2)

        self.assertTrue(puzzle.claim_near_miss_bonus())
        self.assertEqual(puzzle.attempts_left, 3)
        self.assertFalse(puzzle.claim_near_miss_bonus())
        self.assertEqual(puzzle.attempts_left, 3)

    def test_buffer_near_miss_grants_one_retry(self):
        puzzle = BufferPuzzle(matrix=[["1C", "FF"], ["7A", "BD"]], target_seq=["1C", "7A"])
        ok, _ = puzzle.verify_sequence(["1C", "BD"])
        self.assertFalse(ok)
        self.assertTrue(puzzle.near_miss)
        self.assertTrue(puzzle.claim_near_miss_bonus())
        self.assertFalse(puzzle.claim_near_miss_bonus())

    def test_hash_near_miss_grants_one_bonus_attempt(self):
        puzzle = HashCrackPuzzle(target_word="CYBER", word_list=["CYBER", "GHOST", "PULSE"])
        ok, _ = puzzle.guess("CYBEZ")
        self.assertFalse(ok)
        self.assertTrue(puzzle.near_miss)
        self.assertEqual(puzzle.attempts_left, 3)

        self.assertTrue(puzzle.claim_near_miss_bonus())
        self.assertEqual(puzzle.attempts_left, 4)
        self.assertFalse(puzzle.claim_near_miss_bonus())

    def test_frequency_difficulty_table_by_tier(self):
        tier1 = FrequencyPuzzle.difficulty_for_tier(1)
        self.assertEqual(tier1["tolerance"], 2.5)
        self.assertLess(tier1["min_freq"], tier1["max_freq"])
        legacy = FrequencyPuzzle.difficulty_for_tier(9)
        self.assertEqual(legacy["tolerance"], 0.8)
        # generate() honors the tier table but keeps the legacy default
        # (attempts stay 3 everywhere so existing attempt-count tests hold)
        p1 = FrequencyPuzzle.generate(1337, security_level=1)
        self.assertEqual(p1.tolerance, 2.5)
        self.assertEqual(p1.attempts_left, 3)
        self.assertGreaterEqual(p1.target_freq, 35.0)
        self.assertLessEqual(p1.target_freq, 65.0)
        p0 = FrequencyPuzzle.generate(1337)
        self.assertEqual(p0.tolerance, 0.8)
        self.assertEqual(p0.attempts_left, 3)

    def test_tier1_binary_search_solve_rate(self):
        wins, used = 0, 0
        for seed in range(50):
            p = FrequencyPuzzle.generate(seed, security_level=1)
            lo, hi = p.min_freq, p.max_freq
            solved = False
            for _ in range(p.attempts_left):
                guess = round((lo + hi) / 2, 1)
                ok, msg = p.tune(guess)
                if ok:
                    solved = True
                    used += 1
                    break
                used += 1
                if "TOO HIGH" in msg:
                    hi = guess
                else:
                    lo = guess
            if solved:
                wins += 1
        self.assertGreaterEqual(wins, 40)
        self.assertLessEqual(used / max(1, wins), 3.0)

    def test_hash_length_mismatch_is_not_near_miss(self):
        short = HashCrackPuzzle(target_word="CYBER", word_list=["CYBER", "GHOST", "PULSE"])
        ok, _ = short.guess("CYBE")
        self.assertFalse(ok)
        self.assertFalse(short.near_miss)
        long = HashCrackPuzzle(target_word="CYBER", word_list=["CYBER", "GHOST", "PULSE"])
        ok, _ = long.guess("CYBERX")
        self.assertFalse(ok)
        self.assertFalse(long.near_miss)

    def test_frequency_rejects_non_numeric_input(self):
        puzzle = FrequencyPuzzle(target_freq=50.0, tolerance=0.5)
        ok, msg = puzzle.tune("not-a-number")
        self.assertFalse(ok)
        self.assertIn("Invalid frequency", msg)
        self.assertEqual(puzzle.attempts_left, 3)

    def test_puzzle_from_dict_rejects_non_dict(self):
        self.assertIsNone(puzzle_from_dict(None))
        self.assertIsNone(puzzle_from_dict("frequency"))
        self.assertIsNone(puzzle_from_dict([]))

    def test_hash_crack_puzzle(self):
        puzzle = HashCrackPuzzle(target_word="CYBER", word_list=["CYBER", "GHOST", "PULSE"])
        # Partial match
        ok, msg = puzzle.guess("PULSE")
        self.assertFalse(ok)
        self.assertIn("ACCESS DENIED", msg)

        # Full match
        ok, msg = puzzle.guess("CYBER")
        self.assertTrue(ok)
        self.assertIn("ACCESS GRANTED", msg)


if __name__ == "__main__":
    unittest.main()
