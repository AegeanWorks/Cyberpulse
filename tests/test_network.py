"""Unit tests for procedural network generation."""

import unittest
from cyberpulse.engine import KNOWN_CVES
from cyberpulse.models import NodeStatus, NodeType
from cyberpulse.network import SIDE_HOST_ANCHORS, SIDE_HOST_TEMPLATES, generate_network


class TestNetwork(unittest.TestCase):
    def test_network_topology(self):
        nodes = generate_network(seed=1337)
        self.assertIn("node_gateway", nodes)
        self.assertIn("node_central_core", nodes)

        # Gateway starts breached
        self.assertEqual(nodes["node_gateway"].status, NodeStatus.BREACHED)

        # Central core is security level 5
        self.assertEqual(nodes["node_central_core"].security_level, 5)
        self.assertEqual(nodes["node_central_core"].node_type, NodeType.CENTRAL_CORE)

    def test_deterministic_generation(self):
        net1 = generate_network(seed=999)
        net2 = generate_network(seed=999)
        self.assertEqual(list(net1.keys()), list(net2.keys()))
        for k in net1:
            self.assertEqual(net1[k].name, net2[k].name)
            self.assertEqual(net1[k].connected_ids, net2[k].connected_ids)

    def test_network_simulation_topology(self):
        nodes = generate_network(seed=42)
        for node in nodes.values():
            self.assertTrue(node.ip_address.count(".") == 3, f"{node.node_id} has invalid IP")
            self.assertTrue(len(node.hostname) > 0, f"{node.node_id} has empty hostname")
            self.assertTrue(len(node.ports) >= 1, f"{node.node_id} has no open ports")
            self.assertTrue(len(node.filesystem) >= 1, f"{node.node_id} has empty filesystem")

        # Specific node checks
        vault = nodes["node_vault_1"]
        self.assertEqual(vault.ip_address, "10.0.4.15")
        self.assertTrue(any(p.port == 3306 for p in vault.ports))
        self.assertTrue(any(f.path == "/data/corporate_slush_fund.csv" and f.is_target_data for f in vault.filesystem))

        proxy_a = nodes["node_proxy_a"]
        self.assertEqual(proxy_a.ip_address, "192.168.1.10")
        self.assertTrue(any(p.port == 21 and p.vulnerable for p in proxy_a.ports))


class TestProceduralSideHosts(unittest.TestCase):
    def _side_hosts(self, nodes):
        return {nid: node for nid, node in nodes.items() if nid.startswith("node_side_")}

    def _fingerprint(self, nodes):
        return tuple(
            (
                nid,
                node.name,
                node.security_level,
                node.puzzle_type,
                node.credits_reward,
                tuple(node.connected_ids),
            )
            for nid, node in sorted(self._side_hosts(nodes).items())
        )

    def test_same_seed_builds_the_same_side_subnet(self):
        first = generate_network(seed=2026)
        second = generate_network(seed=2026)

        self.assertEqual(self._fingerprint(first), self._fingerprint(second))

    def test_different_seeds_change_the_side_subnet(self):
        fingerprints = {self._fingerprint(generate_network(seed=seed)) for seed in (7, 42, 999, 2026)}

        self.assertGreater(len(fingerprints), 1)

    def test_side_hosts_are_wired_into_the_spine(self):
        nodes = generate_network(seed=42)
        side_hosts = self._side_hosts(nodes)

        self.assertIn(len(side_hosts), (2, 3))
        seen_ips = set()
        for node_id, node in side_hosts.items():
            self.assertEqual(node.status, NodeStatus.LOCKED)
            self.assertEqual(node.node_type, NodeType.DATA_VAULT)
            self.assertGreaterEqual(len(node.connected_ids), 1)
            self.assertLessEqual(node.security_level, 3)
            self.assertTrue(any(vfile.is_target_data for vfile in node.filesystem))
            self.assertTrue(any(port.vulnerable for port in node.ports))
            self.assertNotIn(node.ip_address, seen_ips)
            seen_ips.add(node.ip_address)
            for anchor in node.connected_ids:
                self.assertIn(anchor, SIDE_HOST_ANCHORS)
                self.assertIn(node_id, nodes[anchor].connected_ids)

    def test_campaign_spine_stays_fixed(self):
        nodes = generate_network(seed=2026)
        spine = {nid for nid in nodes if not nid.startswith("node_side_")}

        self.assertEqual(
            spine,
            {
                "node_gateway",
                "node_proxy_a",
                "node_proxy_b",
                "node_vault_1",
                "node_vault_2",
                "node_ice_perimeter",
                "node_central_core",
            },
        )
        self.assertEqual(nodes["node_vault_1"].ip_address, "10.0.4.15")
        self.assertTrue(
            any(
                vfile.path == "/data/corporate_slush_fund.csv" and vfile.is_target_data
                for vfile in nodes["node_vault_1"].filesystem
            )
        )


class TestSideHostTable(unittest.TestCase):
    def test_every_template_row_is_schema_valid(self):
        self.assertGreaterEqual(len(SIDE_HOST_TEMPLATES), 9)
        for template in SIDE_HOST_TEMPLATES:
            for key in ("name", "hostname", "payload", "file_path", "file_size_kb",
                        "content", "port", "service", "version", "exploit_tool",
                        "employee", "antivirus"):
                self.assertIn(key, template, f"missing {key}")
            self.assertEqual(len(template["employee"]), 4)
            av = template["antivirus"]
            self.assertTrue(av is None or len(av) == 4)

    def test_template_ports_hostnames_and_files_are_unique(self):
        for field in ("port", "hostname", "file_path"):
            values = [t[field] for t in SIDE_HOST_TEMPLATES]
            self.assertEqual(len(values), len(set(values)), f"duplicate {field}")

    def test_every_template_service_has_a_dedicated_or_universal_cve(self):
        targets = {cve.target_service for cve in KNOWN_CVES.values()}
        for template in SIDE_HOST_TEMPLATES:
            self.assertIn(template["service"], targets)

    def test_new_rows_appear_in_seeded_grids(self):
        seen = set()
        for seed in range(60):
            nodes = generate_network(seed=seed)
            for nid, node in nodes.items():
                if nid.startswith("node_side_"):
                    seen.add(node.hostname)
        for hostname in ("replica.sprawl.internal", "print.sprawl.internal",
                         "admin.skyline.internal"):
            self.assertIn(hostname, seen)


if __name__ == "__main__":
    unittest.main()
