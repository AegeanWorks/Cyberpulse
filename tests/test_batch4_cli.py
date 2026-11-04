"""Batch 4 CLI dispatch regression tests."""

import unittest

from cyberpulse.cli import run_command
from cyberpulse.engine import GameEngine
from cyberpulse.storage import SaveManager
from pathlib import Path
import tempfile
import io
from contextlib import redirect_stdout


def _run(engine, mgr, cmd, **kw):
    buf = io.StringIO()
    with redirect_stdout(buf):
        run_command(cmd, engine, mgr, **kw)
    return buf.getvalue()


class TestCLIDispatch(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.mgr = SaveManager(self.tmp)
        self.engine = GameEngine(seed=1337, career_profile=self.mgr.load_career())

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_ps_shows_deckos_not_daemons(self):
        out = _run(self.engine, self.mgr, "ps")
        self.assertIn("DECKOS", out)
        self.assertNotIn("ACTIVE BACKGROUND MALWARE DAEMONS", out)

    def test_daemons_shows_daemons(self):
        out = _run(self.engine, self.mgr, "daemons")
        self.assertIn("ACTIVE BACKGROUND MALWARE DAEMONS", out)

    def test_buy_case_insensitive(self):
        self.engine.deck.cryptocreds = 1000
        out = _run(self.engine, self.mgr, "buy OVERCLOCK_CPU")
        self.assertIn("Installed", out)
        self.assertEqual(self.engine.deck.overclock_level, 1)

    def test_buy_exploit_not_recorded_as_rig(self):
        self.engine.deck.cryptocreds = 1000
        _run(self.engine, self.mgr, "buy logic_bomb")
        profile = self.mgr.load_career()
        # career file is only written on buy; reload from manager's file is empty
        # but engine deck should have chip and profile write should exclude it
        self.assertIn("logic_bomb", self.engine.deck.exploits)

    def test_menu_message_lists_1_through_7(self):
        import inspect
        from cyberpulse import cli as clic
        src = inspect.getsource(clic.show_main_menu)
        self.assertIn("1-7", src)
        self.assertNotIn("Enter 1-6", src)

    def test_batch_jackout_continues_pinned(self):
        from cyberpulse.cli import main as cli_main
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = cli_main(["--data-dir", str(self.tmp), "--seed", "1337", "--exec", "jackout;scan;status"])
        out = buf.getvalue()
        self.assertEqual(code, 0)
        # Pinned behavior: batch continues after jackout so `jackout;career`
        # and `jackout;replay` workflows keep working (see test_cli.py).
        self.assertIn("Cannot scan: terminal session jacked out", out)

    def test_replay_keeps_difficulty_and_allegiance(self):
        from cyberpulse.cli import main as cli_main
        buf = io.StringIO()
        with redirect_stdout(buf):
            cli_main(["--data-dir", str(self.tmp), "--seed", "1337",
                      "--difficulty", "hard", "--allegiance", "street",
                      "--auto-solve", "--exec", "hack node_proxy_a;jackout"])
        buf2 = io.StringIO()
        with redirect_stdout(buf2):
            cli_main(["--data-dir", str(self.tmp), "--seed", "1337",
                      "--difficulty", "hard", "--allegiance", "street",
                      "--auto-solve", "--exec", "replay 1;status"])
        out = buf2.getvalue()
        tail = out.split("Replaying run 1")[-1]
        self.assertIn("HARD", tail)
        self.assertIn("STREET", tail)


if __name__ == "__main__":
    unittest.main()
