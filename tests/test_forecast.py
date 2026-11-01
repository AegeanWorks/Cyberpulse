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

    def test_unknown_action_is_rejected(self):
        engine = GameEngine(seed=1337)
        fc = engine.action_forecast("no_such_action")
        self.assertFalse(fc["ok"])

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
