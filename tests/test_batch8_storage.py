"""Batch 8 persistence regression tests."""

import json
import tempfile
import unittest
from pathlib import Path

from cyberpulse.engine import GameEngine
from cyberpulse.storage import SaveManager


class TestPersistenceHardening(unittest.TestCase):
    def test_list_saves_survives_hostile_numerics(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = SaveManager(Path(tmp))
            e = GameEngine(seed=1)
            mgr.save(e, 1)
            payload = json.loads(mgr.slot_path(1).read_text())
            payload["state"]["turns_elapsed"] = "rich"
            payload["deck"]["cryptocreds"] = float("inf")
            payload["state"]["trace_percent"] = float("nan")
            payload["meta"]["saved_at"] = 1e300
            mgr.slot_path(1).write_text(json.dumps(payload))
            saves = mgr.list_saves()
            entry = next(s for s in saves if str(s["slot"]) == "1")
            self.assertEqual(entry["turns"], 0)
            self.assertEqual(entry["creds"], 0)
            self.assertEqual(entry["trace"], 0)

    def test_delete_run_leaves_unowned_same_run(self):
        # Pinned isolation: settle purges only slots this interface claimed,
        # even when the file belongs to the same run (see
        # test_web_settlement_does_not_delete_unowned_save).
        with tempfile.TemporaryDirectory() as tmp:
            mgr = SaveManager(Path(tmp))
            e = GameEngine(seed=1)
            mgr.save(e, 1)
            mgr.delete_run(e.run_id)
            self.assertTrue(mgr.slot_path(1).exists())

    def test_delete_run_leaves_other_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            mgr = SaveManager(Path(tmp))
            e1 = GameEngine(seed=1)
            e2 = GameEngine(seed=2)
            mgr.save(e1, 1)
            mgr.claim_slot(1)
            mgr.save(e2, 2)
            mgr.claim_slot(2)
            mgr.delete_run(e1.run_id)
            self.assertFalse(mgr.slot_path(1).exists())
            self.assertTrue(mgr.slot_path(2).exists())


if __name__ == "__main__":
    unittest.main()
