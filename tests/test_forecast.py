"""Failing-first tests for read-only action forecasts (no balance numbers change)."""

import unittest

from cyberpulse.engine import GameEngine


class TestActionForecast(unittest.TestCase):
    def test_scan_forecast_matches_engine_costs_and_is_pure(self):
        engine = GameEngine(seed=1337)
        before = (engine.deck.cpu_cycles, engine.state.trace_percent, engine.state.turns_elapsed)
        fc = engine.action_forecast("scan")
        self.assertTrue(fc["ok"])
        self.assertEqual(fc["cpu_delta"], 1)
        self.assertEqual(fc["trace_gain"], engine.mitigated_trace(5))
        self.assertEqual(fc["turns"], 1)
        after = (engine.deck.cpu_cycles, engine.state.trace_percent, engine.state.turns_elapsed)
        self.assertEqual(before, after)

    def test_overdrive_forecast_and_block_at_high_trace(self):
        engine = GameEngine(seed=1337)
        fc = engine.action_forecast("overdrive")
        self.assertTrue(fc["ok"])
        self.assertEqual(fc["cpu_delta"], -2)
        self.assertEqual(fc["trace_gain"], engine.mitigated_trace(8))
        engine.state.trace_percent = 95
        blocked = engine.action_forecast("overdrive")
        self.assertFalse(blocked["ok"])

    def test_spoof_forecast_reduces_trace(self):
        engine = GameEngine(seed=1337)
        engine.state.trace_percent = 60
        fc = engine.action_forecast("spoof")
        self.assertTrue(fc["ok"])
        self.assertEqual(fc["cpu_delta"], -3)
        self.assertLess(fc["projected_trace"], 60)

    def test_quickhack_forecast_per_security_tier(self):
        engine = GameEngine(seed=1337)
        fc = engine.action_forecast("quickhack", "node_proxy_a")
        node = engine.nodes["node_proxy_a"]
        if node.security_level <= 2 and node.status != "BREACHED":
            self.assertTrue(fc["ok"])
            self.assertEqual(fc["cpu_delta"], -(2 + node.security_level))
            self.assertEqual(fc["trace_gain"], engine.mitigated_trace(10 + node.security_level * 4))
        else:
            self.assertIn("ok", fc)

    def test_quickhack_forecast_includes_district_heat(self):
        engine = GameEngine(seed=1234)
        engine.state.world.alert_level = 80
        hood = engine.host_district("node_proxy_a")
        self.assertEqual(hood["patrol"], "heavy")
        fc = engine.action_forecast("quickhack", "node_proxy_a")
        node = engine.nodes["node_proxy_a"]
        if fc["ok"]:
            self.assertIn("District heat", fc["notes"])
            self.assertEqual(
                fc["trace_gain"],
                engine.mitigated_trace(10 + node.security_level * 4) + engine.mitigated_trace(1),
            )
        else:
            self.assertIn("ok", fc)

    def test_counter_forecast_reflects_zero_arc_discount(self):
        engine = GameEngine(seed=1337)
        before = (engine.deck.cpu_cycles, engine.state.trace_percent, engine.state.turns_elapsed)
        fc = engine.action_forecast("counter_rival")
        self.assertTrue(fc["ok"])
        self.assertEqual(fc["cpu_delta"], -2)
        self.assertEqual(fc["turns"], 0)
        engine._find_contact("zero").trust = 2
        fc = engine.action_forecast("counter")
        self.assertTrue(fc["ok"])
        self.assertEqual(fc["cpu_delta"], -1)
        self.assertIn("Zero arc", fc["notes"])
        after = (engine.deck.cpu_cycles, engine.state.trace_percent, engine.state.turns_elapsed)
        self.assertEqual(before, after)

    def test_wipe_forecast_reflects_archivist_arc(self):
        engine = GameEngine(seed=1337)
        engine.complete_breach("node_proxy_a")
        engine.state.trace_percent = 50
        fc = engine.action_forecast("wipe", "node_proxy_a")
        self.assertTrue(fc["ok"])
        self.assertEqual(fc["trace_reduction"], 20)
        self.assertEqual(fc["projected_trace"], 30)
        self.assertEqual(fc["turns"], 1)
        engine._find_contact("archivist").trust = 4
        fc = engine.action_forecast("wipe_logs", "node_proxy_a")
        self.assertTrue(fc["ok"])
        self.assertEqual(fc["trace_reduction"], 25)
        self.assertEqual(fc["projected_trace"], 25)
        self.assertIn("deep scrub", fc["notes"])

    def test_unknown_action_is_rejected(self):
        engine = GameEngine(seed=1337)
        fc = engine.action_forecast("no_such_action")
        self.assertFalse(fc["ok"])

    def test_move_forecast_names_district_crossing(self):
        engine = GameEngine(seed=1337)
        engine.complete_breach("node_proxy_a")
        fc = engine.action_forecast("move", "node_proxy_a")
        self.assertTrue(fc["ok"])
        self.assertEqual(fc["cpu_delta"], 1)
        self.assertEqual(fc["trace_gain"], engine.mitigated_trace(2))
        self.assertEqual(fc["turns"], 1)
        self.assertIn("Enters Neon Row grid", fc["notes"])
        blocked = engine.action_forecast("move", "node_vault_1")
        self.assertFalse(blocked["ok"])

    def test_deploy_forecast_shows_passive_yield(self):
        engine = GameEngine(seed=1337)
        engine.deck.cpu_cycles = 8
        engine.complete_breach("node_proxy_a")
        node = engine.nodes["node_proxy_a"]
        fc = engine.action_forecast("deploy", "node_proxy_a")
        self.assertTrue(fc["ok"], fc)
        self.assertEqual(fc["cpu_delta"], -2)
        self.assertEqual(fc["trace_gain"], 0)
        self.assertEqual(fc["turns"], 0)
        self.assertIn(f"+{15 + node.security_level * 5} unbanked", fc["notes"])
        engine._find_contact("kilo").trust = 4
        fc = engine.action_forecast("daemon", "node_proxy_a")
        self.assertIn("Kilo arc yield", fc["notes"])

    def test_intel_forecasts_gate_on_fragments(self):
        engine = GameEngine(seed=1337)
        engine.deck.threat_intel_count = 0
        self.assertFalse(engine.action_forecast("reveal", "node_proxy_b")["ok"])
        self.assertFalse(engine.action_forecast("forge")["ok"])
        engine.deck.threat_intel_count = 1
        fc = engine.action_forecast("reveal", "node_proxy_b")
        self.assertTrue(fc["ok"], fc)
        self.assertEqual(fc.get("intel_delta"), -1)
        self.assertEqual(fc["trace_gain"], 0)
        engine.deck.threat_intel_count = 2
        fc = engine.action_forecast("forge")
        self.assertTrue(fc["ok"], fc)
        self.assertEqual(fc.get("intel_delta"), -2)

    def test_proxy_forecast_shows_dampening(self):
        engine = GameEngine(seed=1337)
        engine.deck.cpu_cycles = 8
        engine.complete_breach("node_proxy_a")
        fc = engine.action_forecast("proxy", "node_proxy_a")
        self.assertTrue(fc["ok"], fc)
        self.assertEqual(fc["cpu_delta"], -1)
        self.assertEqual(fc["trace_gain"], 0)
        self.assertIn("-15% trace generation", fc["notes"])
        self.assertFalse(engine.action_forecast("sever")["ok"])
        ok, _ = engine.add_proxy_hop("node_proxy_a")
        self.assertTrue(ok)
        fc = engine.action_forecast("sever")
        self.assertTrue(fc["ok"], fc)
        self.assertEqual(fc["trace_reduction"], min(15, engine.state.trace_percent))

    def test_hunter_forecast_lists_ready_countermeasures(self):
        engine = GameEngine(seed=1337)
        self.assertFalse(engine.action_forecast("counter_hunter")["ok"])
        engine.state.world.alert_level = 80
        engine.state.rival.status = "inactive"
        engine.advance_turn()
        self.assertTrue(any(h.status in ("hunting", "confused", "intercepted")
                            for h in engine.state.world.hunters))
        engine.deck.cpu_cycles = 1
        fc = engine.action_forecast("hunter")
        self.assertFalse(fc["ok"])
        engine.deck.cpu_cycles = 8
        fc = engine.action_forecast("counter_hunter")
        self.assertTrue(fc["ok"], fc)
        self.assertIn("cpu_burst READY", fc["notes"])
        engine.deck.exploits.append("logic_bomb")
        fc = engine.action_forecast("countermeasure")
        self.assertIn("logic_bomb READY", fc["notes"])

    def test_social_forecast_shows_lure_odds(self):
        engine = GameEngine(seed=1337)
        fc = engine.action_forecast("social", "node_proxy_a")
        self.assertTrue(fc["ok"], fc)
        self.assertEqual(fc["cpu_delta"], -1)
        self.assertEqual(fc["trace_gain"], engine.mitigated_trace(6))
        self.assertEqual(fc["turns"], 1)
        self.assertIn("success on", fc["notes"])
        self.assertIn(engine.host_district("node_proxy_a")["district"], fc["notes"])

    def test_bypass_forecast_lists_blocked_ports(self):
        engine = GameEngine(seed=1337)
        node = engine.nodes["node_proxy_a"]
        blocked_ports = [r.port for r in (node.firewall.rules if node.firewall else [])
                         if r.action == "BLOCK" and not r.bypassed]
        fc = engine.action_forecast("bypass", "node_proxy_a")
        if blocked_ports:
            self.assertTrue(fc["ok"], fc)
            self.assertEqual(fc["cpu_delta"], -1)
            self.assertEqual(fc["trace_gain"], engine.mitigated_trace(5))
        else:
            self.assertFalse(fc["ok"])

    def test_evade_forecast_blocks_without_active_av(self):
        engine = GameEngine(seed=1337)
        fc = engine.action_forecast("evade", "node_gateway")
        self.assertIn("ok", fc)
        node = engine.nodes["node_proxy_a"]
        if node.antivirus and node.antivirus.enabled and not node.antivirus.evaded:
            engine.deck.cpu_cycles = 8
            fc = engine.action_forecast("evade", "node_proxy_a")
            self.assertTrue(fc["ok"], fc)
            self.assertEqual(fc["cpu_delta"], -2)
            self.assertEqual(fc["trace_gain"], engine.mitigated_trace(6))

    def test_combo_rate_preview_caps_at_fifty_percent(self):
        engine = GameEngine(seed=1337)
        engine.state.combo_streak = 9
        preview = engine.combo_rate_preview()
        self.assertEqual(preview["next_rate"], 0.5)
        self.assertEqual(preview["unbanked_at_risk"], engine.state.unbanked_creds)

    def test_jackout_forecast_matches_extraction_risk(self):
        engine = GameEngine(seed=1337)
        engine.state.trace_percent = 60
        fc = engine.action_forecast("jackout")
        risk = engine.extraction_risk()
        self.assertTrue(fc["ok"])
        self.assertEqual(fc["projected_trace"], risk["projected_trace"])
        self.assertEqual(fc["lethal"], risk["lethal"])

    def test_cli_blocked_forecast_has_no_double_period(self):
        import io
        import shutil
        import tempfile
        from contextlib import redirect_stdout
        from pathlib import Path

        from cyberpulse.cli import main

        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(["--data-dir", str(tmp), "--seed", "1337", "--exec", "forecast bogus; traceroute node_missing"])
        self.assertEqual(code, 0)
        self.assertNotIn("..", buf.getvalue())
        self.assertIn("Forecast: bogus blocked", buf.getvalue())

    def test_cli_forecast_command_reports_costs(self):
        import io
        import shutil
        import tempfile
        from contextlib import redirect_stdout
        from pathlib import Path

        from cyberpulse.cli import main

        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(["--data-dir", str(tmp), "--seed", "1337", "--exec", "forecast scan"])
        self.assertEqual(code, 0)
        self.assertIn("Forecast scan", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
