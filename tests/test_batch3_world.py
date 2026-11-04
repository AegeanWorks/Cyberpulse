"""Batch 3 world fairness regression tests."""

import random
import unittest

from cyberpulse import world
from cyberpulse.models import NetWatchHunter, Node, NodeStatus, NodeType, WorldState


def _node(nid, status=NodeStatus.BREACHED, sec=1, breached_turn=0):
    return Node(
        node_id=nid,
        name=nid,
        node_type=NodeType.DATA_VAULT,
        ip_address="10.0.9.99",
        hostname=nid,
        security_level=sec,
        status=status,
        breached_turn=breached_turn,
        reward_claimed=True,
    )


class TestWorldFairness(unittest.TestCase):
    def test_tier_rank_rejects_unknown(self):
        self.assertEqual(world.tier_rank("BOGUS"), -1)
        self.assertEqual(world.tier_rank("GREEN"), 0)

    def test_confused_hunter_ignores_dangling_neighbor(self):
        nodes = {"a": _node("a", status=NodeStatus.DISCOVERED)}
        nodes["a"].connected_ids = ["ghost"]
        hunter = NetWatchHunter(hunter_id="h1", name="A", current_node_id="a",
                                status="confused", confused_turns=2)
        rng = random.Random(1)
        world.step_hunter(hunter, nodes, "a", rng)
        self.assertIn(hunter.current_node_id, nodes)

    def test_resecure_order_is_fair(self):
        nodes = {
            "node_a": _node("node_a", breached_turn=0),
            "node_b": _node("node_b", breached_turn=0),
        }
        counts = {"node_a": 0, "node_b": 0}
        for tick in range(12, 212):
            for pick in world.plan_resecures(9, tick, 100, nodes, "safe"):
                counts[pick] += 1
        total = counts["node_a"] + counts["node_b"]
        self.assertGreater(total, 20)
        for nid in counts:
            share = counts[nid] / total
            self.assertGreater(share, 0.30)
            self.assertLess(share, 0.70)

    def test_deploy_hunter_sorted_spawn(self):
        w = WorldState(alert_level=90, minute=12 * 60)
        nodes = {
            "z9": _node("z9", status=NodeStatus.DISCOVERED),
            "a1": _node("a1", status=NodeStatus.DISCOVERED),
        }
        h = world.deploy_hunter(w, nodes, tick=5)
        self.assertIsNotNone(h)


if __name__ == "__main__":
    unittest.main()
