"""Batch 2 economy/math guard regression tests."""

import unittest

from cyberpulse.models import Node, NodeType
from cyberpulse.rewards import roll_breach_reward
from cyberpulse.scoring import score_run


class FakeRNG:
    def __init__(self, roll):
        self._roll = roll

    def random(self):
        return self._roll

    def choice(self, seq):
        return seq[0]


def _node(credits):
    return Node(
        node_id="n1",
        name="Test",
        node_type=NodeType.DATA_VAULT,
        ip_address="10.0.9.21",
        hostname="test.local",
        security_level=1,
        credits_reward=credits,
    )


class TestEconomyGuards(unittest.TestCase):
    def test_score_run_clamps_nonfinite(self):
        for bad in (float("nan"), float("inf"), float("-inf"), "rich", None):
            res = score_run(gained=bad, best_combo=0, quests_done=0, nodes_breached=0,
                            outcome="jackout", contract_completed=False, main_story_complete=False)
            self.assertEqual(res["breakdown"]["credits"], 0)

    def test_score_run_truncates_float(self):
        res = score_run(gained=99.9, best_combo=0, quests_done=0, nodes_breached=0,
                        outcome="jackout", contract_completed=False, main_story_complete=False)
        self.assertEqual(res["breakdown"]["credits"], 99)

    def test_jackpot_uses_integer_math(self):
        for base in (1, 3, 10 ** 30, 10 ** 400):
            node = _node(base)
            got, _, _ = roll_breach_reward(node, rng=FakeRNG(0.2))
            self.assertEqual(got, base * 5 // 2)


if __name__ == "__main__":
    unittest.main()
