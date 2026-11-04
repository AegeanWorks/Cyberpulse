"""Batch 1 server hardening regression tests."""

import json
import shutil
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from cyberpulse.engine import GameEngine
from cyberpulse.models import NodeStatus
from cyberpulse.server import coerce_seed, create_server, strict_int


class TestServerHardeningUnit(unittest.TestCase):
    def test_coerce_seed_rejects_bool(self):
        with self.assertRaises(ValueError):
            coerce_seed(True)
        with self.assertRaises(ValueError):
            coerce_seed(False)

    def test_strict_int_accepts_int_and_int_string(self):
        self.assertEqual(strict_int(22, "port"), 22)
        self.assertEqual(strict_int("22", "port"), 22)

    def test_strict_int_rejects_float_bool_and_garbage(self):
        for bad in (22.9, True, False, "22.9", "abc", "", None, [22]):
            with self.assertRaises(ValueError, msg=repr(bad)):
                strict_int(bad, "port")

    def test_lay_low_rejects_float_and_bool(self):
        e = GameEngine(seed=42)
        ok, msg = e.lay_low(2.9)
        self.assertFalse(ok)
        ok2, _ = e.lay_low(True)
        self.assertFalse(ok2)

    def test_load_run_refuses_terminal_slot(self):
        from cyberpulse.server import CyberdeckSession
        tmp = Path(tempfile.mkdtemp())
        try:
            sess = CyberdeckSession(data_dir=tmp, seed=42)
            e = sess.engine
            e.complete_breach("node_proxy_a")
            e.state.is_victory = True
            sess.save_mgr.save(e, 1)
            ok, msg = sess.load_run(1)
            self.assertFalse(ok)
            self.assertIn("finished run", msg)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class TestServerHardeningLive(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = Path(tempfile.mkdtemp())
        cls.server = create_server(host="127.0.0.1", port=0, data_dir=cls.temp_dir, seed=1337)
        cls.port = cls.server.server_address[1]
        cls.base = f"http://127.0.0.1:{cls.port}"
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def test_post_rejects_non_json_content_type(self):
        url = f"{self.base}/api/action"
        body = json.dumps({"action": "scan"}).encode()
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "text/plain"}, method="POST")
        try:
            urllib.request.urlopen(req, timeout=3.0)
            self.fail("expected 415")
        except urllib.error.HTTPError as ex:
            self.assertEqual(ex.code, 415)

    def test_post_float_port_rejected(self):
        url = f"{self.base}/api/action"
        body = json.dumps({"action": "bypass", "target": "192.168.1.20", "port": 22.9, "method": "knock"}).encode()
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
        try:
            urllib.request.urlopen(req, timeout=3.0)
            self.fail("expected 400")
        except urllib.error.HTTPError as ex:
            self.assertEqual(ex.code, 400)

    def test_post_bool_seed_rejected(self):
        url = f"{self.base}/api/action"
        body = json.dumps({"action": "reset", "seed": True}).encode()
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
        try:
            urllib.request.urlopen(req, timeout=3.0)
            self.fail("expected 400")
        except urllib.error.HTTPError as ex:
            self.assertEqual(ex.code, 400)

    def test_unknown_api_returns_404_json(self):
        url = f"{self.base}/api/no_such_endpoint_xyz"
        req = urllib.request.Request(url, method="GET")
        try:
            urllib.request.urlopen(req, timeout=3.0)
            self.fail("expected 404")
        except urllib.error.HTTPError as ex:
            self.assertEqual(ex.code, 404)


if __name__ == "__main__":
    unittest.main()
