"""Interactive and deterministic cyberpunk hacking mini-game puzzles with near-miss feedback."""

import math
import random
from typing import List, Optional, Tuple


class FrequencyPuzzle:
    """Tuning resonance frequency puzzle with near-miss feedback mechanics."""

    DIFFICULTY_BY_TIER = {
        1: {"tolerance": 2.5, "min_freq": 35.0, "max_freq": 65.0},
        2: {"tolerance": 2.0, "min_freq": 35.0, "max_freq": 70.0},
    }
    DEFAULT_DIFFICULTY = {"tolerance": 0.8, "min_freq": 20.0, "max_freq": 99.0}

    def __init__(self, target_freq: float, tolerance: float = 0.5, attempts: int = 3,
                 min_freq: float = 20.0, max_freq: float = 99.0):
        self.target_freq = round(target_freq, 1)
        self.tolerance = tolerance
        self.attempts_left = attempts
        self.min_freq = min_freq
        self.max_freq = max_freq
        self.near_miss: bool = False
        self.near_miss_awarded: bool = False

    def claim_near_miss_bonus(self) -> bool:
        """Convert the first near miss into one extra tuning attempt."""
        if not self.near_miss or self.near_miss_awarded:
            return False
        self.near_miss_awarded = True
        self.attempts_left += 1
        return True

    def to_dict(self) -> dict:
        return {
            "type": "frequency",
            "target_freq": self.target_freq,
            "tolerance": self.tolerance,
            "attempts_left": self.attempts_left,
            "min_freq": self.min_freq,
            "max_freq": self.max_freq,
            "near_miss": self.near_miss,
            "near_miss_awarded": self.near_miss_awarded,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FrequencyPuzzle":
        if not isinstance(data, dict):
            raise ValueError("frequency puzzle payload must be an object")
        try:
            target = float(data["target_freq"])
            tolerance = float(data["tolerance"])
        except (KeyError, TypeError, ValueError, OverflowError) as exc:
            raise ValueError("frequency puzzle payload is corrupt") from exc
        if not math.isfinite(target) or not math.isfinite(tolerance):
            raise ValueError("frequency puzzle payload is corrupt")
        try:
            puzzle = cls(target_freq=target, tolerance=tolerance,
                         min_freq=float(data.get("min_freq", 20.0)),
                         max_freq=float(data.get("max_freq", 99.0)))
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError("frequency puzzle payload is corrupt") from exc
        try:
            puzzle.attempts_left = int(data.get("attempts_left", puzzle.attempts_left))
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError("frequency puzzle payload is corrupt") from exc
        puzzle.near_miss = bool(data.get("near_miss", False))
        puzzle.near_miss_awarded = bool(data.get("near_miss_awarded", False))
        return puzzle

    @classmethod
    def difficulty_for_tier(cls, security_level: int) -> dict:
        try:
            tier = int(security_level)
        except (TypeError, ValueError):
            tier = 3
        return dict(cls.DIFFICULTY_BY_TIER.get(tier, cls.DEFAULT_DIFFICULTY))

    @classmethod
    def generate(cls, seed: int, security_level: int = 3) -> "FrequencyPuzzle":
        rng = random.Random(seed)
        spec = cls.difficulty_for_tier(security_level)
        freq = rng.uniform(spec["min_freq"], spec["max_freq"])
        return cls(target_freq=freq, tolerance=spec["tolerance"],
                   min_freq=spec["min_freq"], max_freq=spec["max_freq"])

    def tune(self, guess: float) -> Tuple[bool, str]:
        """Test a frequency guess with near-miss detection."""
        try:
            guess = float(guess)
        except (TypeError, ValueError):
            return False, "⚠️  Invalid frequency input. Enter a number in GHz."
        self.attempts_left -= 1
        diff = guess - self.target_freq
        if abs(diff) <= self.tolerance:
            self.near_miss = False
            return True, f"🎯 RESONANCE LOCKED! Frequency aligned at {guess:.1f} GHz."

        self.near_miss = abs(diff) <= (self.tolerance * 2.5)
        hint = "TOO HIGH" if diff > 0 else "TOO LOW"
        near_miss_text = " [⚡ NEAR-MISS! Resonance harmonic almost locked!]" if self.near_miss else ""

        if self.attempts_left <= 0:
            return False, f"❌ FREQUENCY LOCK FAILED! Target was {self.target_freq:.1f} GHz."
        return False, f"⚠️  Signal off: {hint}.{near_miss_text} Attempts remaining: {self.attempts_left}."


class BufferPuzzle:
    """Memory buffer sequence matching puzzle with partial alignment detection."""

    def __init__(self, matrix: List[List[str]], target_seq: List[str]):
        self.matrix = matrix
        self.target_seq = target_seq
        self.near_miss: bool = False
        self.near_miss_awarded: bool = False

    def claim_near_miss_bonus(self) -> bool:
        """Convert the first near miss into one free retry before the host locks down."""
        if not self.near_miss or self.near_miss_awarded:
            return False
        self.near_miss_awarded = True
        return True

    def to_dict(self) -> dict:
        return {
            "type": "buffer",
            "matrix": [list(row) for row in self.matrix],
            "target_seq": list(self.target_seq),
            "near_miss": self.near_miss,
            "near_miss_awarded": self.near_miss_awarded,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BufferPuzzle":
        if not isinstance(data, dict):
            raise ValueError("buffer puzzle payload must be an object")
        matrix = data.get("matrix")
        target = data.get("target_seq")
        if (not isinstance(matrix, list) or not matrix
                or any(not isinstance(row, list) or not row
                       or any(not isinstance(cell, str) for cell in row) for row in matrix)):
            raise ValueError("buffer puzzle payload is corrupt")
        if (not isinstance(target, list) or not target
                or any(not isinstance(cell, str) for cell in target)):
            raise ValueError("buffer puzzle payload is corrupt")
        puzzle = cls(matrix=[list(row) for row in matrix], target_seq=list(target))
        puzzle.near_miss = bool(data.get("near_miss", False))
        puzzle.near_miss_awarded = bool(data.get("near_miss_awarded", False))
        return puzzle

    @classmethod
    def generate(cls, seed: int) -> "BufferPuzzle":
        rng = random.Random(seed)
        hex_pool = ["1C", "E9", "7A", "BD", "55", "FF"]
        matrix = [[rng.choice(hex_pool) for _ in range(4)] for _ in range(4)]
        seq_len = 2
        seq = [rng.choice(matrix[r]) for r in range(seq_len)]
        return cls(matrix=matrix, target_seq=seq)

    def verify_sequence(self, player_seq: List[str]) -> Tuple[bool, str]:
        """Verify whether player's sequence matches with near-miss feedback."""
        if player_seq == self.target_seq:
            self.near_miss = False
            return True, "💾 BUFFER OVERFLOW EXPLOIT EXECUTED! Memory injected."

        self.near_miss = len(player_seq) > 0 and len(self.target_seq) > 0 and player_seq[0] == self.target_seq[0]
        near_miss_text = " [⚡ NEAR-MISS! Primary buffer block aligned!]" if self.near_miss else ""
        return False, f"❌ BUFFER CORRUPTION! Expected {self.target_seq}, received {player_seq}.{near_miss_text}"


class HashCrackPuzzle:
    """Cryptographic password / hash cracking cipher puzzle with single-letter near miss."""

    WORDS = ["NEXUS", "CYBER", "GHOST", "PULSE", "LASER", "NEONX", "PROXY", "VIPER"]

    def __init__(self, target_word: str, word_list: List[str]):
        self.target_word = target_word.upper()
        self.word_list = [w.upper() for w in word_list]
        self.attempts_left = 4
        self.near_miss: bool = False
        self.near_miss_awarded: bool = False

    def claim_near_miss_bonus(self) -> bool:
        """Convert the first character-level near miss into one extra keyword attempt."""
        if not self.near_miss or self.near_miss_awarded:
            return False
        self.near_miss_awarded = True
        self.attempts_left += 1
        return True

    def to_dict(self) -> dict:
        return {
            "type": "hash",
            "target_word": self.target_word,
            "word_list": list(self.word_list),
            "attempts_left": self.attempts_left,
            "near_miss": self.near_miss,
            "near_miss_awarded": self.near_miss_awarded,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "HashCrackPuzzle":
        if not isinstance(data, dict):
            raise ValueError("hash puzzle payload must be an object")
        target = data.get("target_word")
        words = data.get("word_list")
        if not isinstance(target, str) or not target:
            raise ValueError("hash puzzle payload is corrupt")
        if (not isinstance(words, list) or not words
                or any(not isinstance(w, str) or not w for w in words)):
            raise ValueError("hash puzzle payload is corrupt")
        puzzle = cls(target_word=target, word_list=list(words))
        try:
            puzzle.attempts_left = int(data.get("attempts_left", puzzle.attempts_left))
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError("hash puzzle payload is corrupt") from exc
        puzzle.near_miss = bool(data.get("near_miss", False))
        puzzle.near_miss_awarded = bool(data.get("near_miss_awarded", False))
        return puzzle

    @classmethod
    def generate(cls, seed: int) -> "HashCrackPuzzle":
        rng = random.Random(seed)
        pool = rng.sample(cls.WORDS, 5)
        secret = rng.choice(pool)
        return cls(target_word=secret, word_list=pool)

    def guess(self, candidate: str) -> Tuple[bool, str]:
        """Evaluate a guess and return matching character count with near-miss detection."""
        self.attempts_left -= 1
        candidate = str(candidate).upper().strip()

        if candidate == self.target_word:
            self.near_miss = False
            return True, f"🔓 ACCESS GRANTED! Password hash cracked: '{self.target_word}'."

        matches = sum(1 for a, b in zip(candidate, self.target_word) if a == b)
        self.near_miss = len(candidate) == len(self.target_word) and matches == (len(self.target_word) - 1)
        near_miss_text = " [⚡ CRITICAL NEAR-MISS! Only 1 character off!]" if self.near_miss else ""

        if self.attempts_left <= 0:
            return False, f"🔒 TERMINAL LOCKED! Correct hash key was '{self.target_word}'."

        return False, f"⚠️  ACCESS DENIED: {matches}/{len(self.target_word)} correct letters.{near_miss_text} Attempts left: {self.attempts_left}."


PUZZLE_TYPES = {
    "frequency": FrequencyPuzzle,
    "buffer": BufferPuzzle,
    "hash": HashCrackPuzzle,
}


def puzzle_from_dict(data: dict) -> Optional[object]:
    """Restore a persisted puzzle payload, or None when the type is unknown."""
    if not isinstance(data, dict):
        return None
    puzzle_type = str(data.get("type", "")).lower()
    factory = PUZZLE_TYPES.get(puzzle_type)
    if factory is None:
        return None
    try:
        return factory.from_dict(data)
    except (AttributeError, KeyError, TypeError, ValueError, OverflowError):
        return None
