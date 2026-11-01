"""Unit tests for presentation sprite registries and the CLI topology map."""

import unittest

from cyberpulse.cli import render_topology_map, topology_token
from cyberpulse.engine import GameEngine
from cyberpulse.models import (
    ENTITY_VISUALS,
    NODE_VISUALS,
    PUZZLE_VISUALS,
    SHOP_VISUALS,
    STATUS_VISUALS,
    WORLD_VISUALS,
    NodeStatus,
    NodeType,
    entity_visual,
    node_visual,
)


class TestVisualRegistries(unittest.TestCase):
    def test_every_node_type_has_sprite(self):
        for node_type in (
            NodeType.GATEWAY,
            NodeType.FIREWALL,
            NodeType.DATA_VAULT,
            NodeType.ICE_DEFENSE,
            NodeType.CENTRAL_CORE,
        ):
            meta = node_visual(node_type, NodeStatus.DISCOVERED)
            self.assertIn("glyph", meta)
            self.assertIn("shape", meta)
            self.assertTrue(meta["glyph"].strip())
            self.assertIn(meta["shape"], {"diamond", "hexagon", "vault", "triangle", "core"})

    def test_node_status_overlay_keeps_base_shape(self):
        base = node_visual(NodeType.FIREWALL)
        over = node_visual(NodeType.FIREWALL, NodeStatus.BREACHED)
        self.assertEqual(base["shape"], over["shape"])
        self.assertEqual(over["status_label"], "BREACHED")

    def test_entity_shop_puzzle_world_tables_nonempty(self):
        self.assertGreaterEqual(len(ENTITY_VISUALS), 8)
        self.assertIn("overclock_cpu", SHOP_VISUALS)
        self.assertIn("frequency", PUZZLE_VISUALS)
        self.assertIn("GREEN", WORLD_VISUALS)
        for table in (ENTITY_VISUALS, SHOP_VISUALS, PUZZLE_VISUALS, WORLD_VISUALS, STATUS_VISUALS):
            for key, meta in table.items():
                self.assertTrue(str(meta.get("glyph", "")).strip(), key)

    def test_entity_visual_falls_back_without_throwing(self):
        meta = entity_visual("no_such_key_xyz")
        self.assertTrue(meta["glyph"].strip())


class TestTopologyMap(unittest.TestCase):
    def test_fixed_slots_and_current_marker(self):
        engine = GameEngine(seed=1337)
        lines = render_topology_map(engine)
        self.assertEqual(len(lines), 5)
        self.assertIn("Topology Map", lines[0])
        # Gateway is the run start, so exactly one @ marker on the map.
        self.assertEqual("".join(lines).count("@"), 1)
        token = topology_token(engine, "node_gateway")
        self.assertIn("@", token)

    def test_unknown_node_renders_placeholder(self):
        engine = GameEngine(seed=7)
        self.assertEqual(topology_token(engine, "node_missing"), "[   ]")


if __name__ == "__main__":
    unittest.main()
