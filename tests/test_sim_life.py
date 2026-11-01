"""Failing-first tests for lifelike simulation: routes, fingerprints, work shifts."""

import unittest

from cyberpulse.engine import GameEngine
from cyberpulse.models import EmployeeProfile, Node, NodeStatus, NodeType


class TestSimLife(unittest.TestCase):
    def test_nodes_carry_host_fingerprint(self):
        engine = GameEngine(seed=1337)
        for node in engine.nodes.values():
            self.assertTrue(str(getattr(node, "os_name", "")).strip(), node.node_id)
            self.assertGreaterEqual(int(getattr(node, "uptime_hours", 0)), 0)
            self.assertTrue(str(getattr(node, "patch_level", "")).strip(), node.node_id)

    def test_fingerprint_defaults_backfill_legacy_nodes(self):
        legacy = Node(
            node_id="n-old", name="Old", node_type=NodeType.FIREWALL,
            security_level=1, status=NodeStatus.LOCKED,
        )
        restored = Node.from_dict(legacy.to_dict())
        # to_dict roundtrip keeps new fields; from_dict of a dict WITHOUT
        # them (pre-sim save) must still build via defaults.
        bare = {"node_id": "n-old", "name": "Old", "node_type": NodeType.FIREWALL,
                "security_level": 1, "status": NodeStatus.LOCKED}
        rebuilt = Node.from_dict(dict(bare))
        self.assertTrue(str(rebuilt.os_name).strip())
        self.assertIn("patch", rebuilt.patch_level.lower())

    def test_employees_have_work_shifts(self):
        engine = GameEngine(seed=1337)
        shifts = set()
        for node in engine.nodes.values():
            for emp in node.employees:
                self.assertIn(emp.work_shift, ("day", "night", "swing"))
                shifts.add(emp.work_shift)
        self.assertGreaterEqual(len(shifts), 1)

    def test_legacy_employee_defaults_to_day_shift(self):
        emp = EmployeeProfile(name="X", role="Ops", email="x@y.z")
        self.assertEqual(emp.work_shift, "day")

    def test_traceroute_reports_hops_and_latency(self):
        engine = GameEngine(seed=1337)
        route = engine.trace_route("node_vault_1")
        self.assertTrue(route["ok"])
        self.assertGreaterEqual(len(route["hops"]), 2)
        self.assertEqual(route["hops"][0]["node_id"], engine.state.current_node_id)
        self.assertEqual(route["hops"][-1]["node_id"], "node_vault_1")
        self.assertGreater(route["total_latency_ms"], 0)
        for hop in route["hops"]:
            self.assertGreater(hop["latency_ms"], 0)
            self.assertIn("ip_address", hop)

    def test_traceroute_is_deterministic(self):
        first = GameEngine(seed=4242).trace_route("node_central_core")
        second = GameEngine(seed=4242).trace_route("node_central_core")
        self.assertEqual(first, second)

    def test_traceroute_rejects_unknown_host(self):
        engine = GameEngine(seed=1337)
        route = engine.trace_route("node_missing")
        self.assertFalse(route["ok"])

    def test_host_fingerprint_summarizes_target(self):
        engine = GameEngine(seed=1337)
        fp = engine.host_fingerprint("node_proxy_a")
        self.assertTrue(fp["ok"])
        self.assertIn("os_name", fp)
        self.assertIn("open_ports", fp)
        self.assertIn("employees_on_shift", fp)


if __name__ == "__main__":
    unittest.main()
