"""Batch 7 puzzle deserialization regression tests."""

import unittest

from cyberpulse.puzzles import (
    BufferPuzzle,
    FrequencyPuzzle,
    HashCrackPuzzle,
    puzzle_from_dict,
)


class TestPuzzleHardening(unittest.TestCase):
    def test_frequency_rejects_nonfinite(self):
        for bad in ({"target_freq": float("nan"), "tolerance": 0.5},
                    {"target_freq": float("inf"), "tolerance": 0.5},
                    {"target_freq": 50.0, "tolerance": float("nan")},
                    {"target_freq": "rich", "tolerance": 0.5},
                    {"tolerance": 0.5},
                    "nope"):
            self.assertIsNone(puzzle_from_dict({"type": "frequency", **(bad if isinstance(bad, dict) else {})} if isinstance(bad, str) else {"type": "frequency", **bad}))

    def test_buffer_rejects_malformed(self):
        good = BufferPuzzle(matrix=[["1C"]], target_seq=["1C"]).to_dict()
        self.assertIsNotNone(puzzle_from_dict(good))
        for bad in ({"type": "buffer", "matrix": "nope", "target_seq": ["1C"]},
                    {"type": "buffer", "matrix": [["1C"]], "target_seq": "nope"},
                    {"type": "buffer", "matrix": [["1C"]], "target_seq": []},
                    {"type": "buffer", "matrix": [[1]], "target_seq": ["1C"]},
                    {"type": "buffer"},
                    {"type": "nope"}):
            self.assertIsNone(puzzle_from_dict(bad), msg=repr(bad))

    def test_hash_rejects_malformed(self):
        good = HashCrackPuzzle(target_word="CYBER", word_list=["CYBER"]).to_dict()
        self.assertIsNotNone(puzzle_from_dict(good))
        for bad in ({"type": "hash", "target_word": "", "word_list": ["CYBER"]},
                    {"type": "hash", "target_word": "CYBER", "word_list": []},
                    {"type": "hash", "target_word": "CYBER", "word_list": [""]},
                    {"type": "hash", "target_word": 1, "word_list": ["CYBER"]},
                    {"type": "hash"}):
            self.assertIsNone(puzzle_from_dict(bad), msg=repr(bad))

    def test_round_trip_survives(self):
        for p in (FrequencyPuzzle(target_freq=50.0).to_dict(),
                  BufferPuzzle(matrix=[["1C"]], target_seq=["1C"]).to_dict(),
                  HashCrackPuzzle(target_word="CYBER", word_list=["CYBER", "GHOST"]).to_dict()):
            self.assertIsNotNone(puzzle_from_dict(p))


if __name__ == "__main__":
    unittest.main()
