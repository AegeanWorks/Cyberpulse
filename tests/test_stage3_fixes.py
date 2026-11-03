"""Stage 3 P0 regression tests: verified swarm findings with reproductions."""

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from cyberpulse import deckos
from cyberpulse.engine import GameEngine
from cyberpulse.models import NodeStatus, RivalNetrunner
from cyberpulse.shop import BlackMarketShop
from cyberpulse.storage import SaveManager


class TestStage3P0Fixes(unittest.TestCase):
    def test_complete_breach_rejects_lockdown_host(self):
        e = GameEngine(seed=42)
        e.register_puzzle_failure("node_proxy_a", "burn")
        ok, _ = e.can_hack_node("node_proxy_a")
        self.assertFalse(ok)
        ok2, msg2 = e.complete_breach("node_proxy_a")
        self.assertFalse(ok2)
        self.assertIn("LOCKDOWN", msg2)
        self.assertNotEqual(e.nodes["node_proxy_a"].status, NodeStatus.BREACHED)

    def test_exploit_service_lockout_kill_leaves_port_unbreached(self):
        e = GameEngine(seed=42)
        n = e.nodes["node_proxy_a"]
        n.status = NodeStatus.DISCOVERED
        port = next(p for p in n.ports if p.vulnerable)
        e.state.trace_percent = 95
        ok, _ = e.exploit_service(n.node_id, port.port)
        self.assertFalse(ok)
        self.assertTrue(e.state.is_game_over)
        self.assertFalse(port.breached)

    def test_rival_from_dict_rejects_nonfinite(self):
        r = RivalNetrunner.from_dict({"name": "X", "handle": "h", "skill": float("inf")})
        self.assertEqual(r.skill, 1)
        r2 = RivalNetrunner.from_dict({"name": "X", "handle": "h", "next_move_turn": float("inf")})
        self.assertEqual(r2.next_move_turn, 6)

    def test_price_for_rejects_nonfinite_multiplier(self):
        shop = BlackMarketShop()
        item = shop.catalog["overclock_cpu"]
        self.assertEqual(shop.price_for(item, float("nan")), item.cost)
        self.assertEqual(shop.price_for(item, float("inf")), item.cost)

    def test_deckos_daemon_lists_host_ip_and_sysinfo_ram(self):
        e = GameEngine(seed=1337)
        e.complete_breach("node_proxy_a")
        e.deck.cpu_cycles = 8
        ok, _ = e.deploy_daemon("192.168.1.10", "keylogger")
        self.assertTrue(ok)
        procs = deckos.list_processes(e)
        names = [p["name"] for p in procs if p.get("killable")]
        self.assertTrue(any("192.168.1.10" in n for n in names))
        self.assertFalse(any("[?]" in n for n in names))
        info = deckos.sysinfo(e)
        self.assertEqual(info["ram_mb"], e.deck.max_ram)

    def test_write_atomic_mkstemp_failure_raises_oserror(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = SaveManager(Path(tmp))
            with mock.patch("cyberpulse.storage.tempfile.mkstemp", side_effect=OSError("nospace")):
                with self.assertRaises(OSError):
                    mgr.save(GameEngine(seed=5))


if __name__ == "__main__":
    unittest.main()
