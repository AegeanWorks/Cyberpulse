"""Batch 9 CLI parity regression tests."""

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from cyberpulse.cli import run_command
from cyberpulse.engine import GameEngine
from cyberpulse.storage import SaveManager
import shutil


def _run(engine, mgr, cmd):
    buf = io.StringIO()
    with redirect_stdout(buf):
        run_command(cmd, engine, mgr)
    return buf.getvalue()


class TestCLIParity(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.mgr = SaveManager(self.tmp)
        self.engine = GameEngine(seed=7, career_profile=self.mgr.load_career())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_load_refuses_finished_checkpoint(self):
        e = GameEngine(seed=7, career_profile=self.mgr.load_career())
        e.complete_breach("node_proxy_a")
        e.state.is_victory = True
        self.mgr.save(e, 1)
        before = self.engine.state.turns_elapsed
        out = _run(self.engine, self.mgr, "load 1")
        self.assertIn("finished run", out)
        self.assertEqual(self.engine.state.turns_elapsed, before)

    def test_reset_career_rejects_trailing_junk(self):
        out = _run(self.engine, self.mgr, "reset_career CONFIRM junk")
        self.assertIn("Usage: reset_career CONFIRM", out)


if __name__ == "__main__":
    unittest.main()
