"""Unit and integration tests for CyberPulse HTTP REST server."""

import json
import shutil
import socket
import tempfile
import threading
import unittest
from unittest import mock
import urllib.error
import urllib.error
import urllib.request
from pathlib import Path

from cyberpulse.server import CyberdeckSession, create_server


class TestCyberdeckServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = Path(tempfile.mkdtemp())
        # Bind to port 0 so the OS assigns an ephemeral free port
        cls.server = create_server(host="127.0.0.1", port=0, data_dir=cls.temp_dir, seed=1337)
        cls.port = cls.server.server_address[1]
        cls.base_url = f"http://127.0.0.1:{cls.port}"

        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def _get(self, path: str):
        url = f"{self.base_url}{path}"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            data = resp.read().decode("utf-8")
            return resp.status, json.loads(data)

    def _post(self, path: str, payload: dict):
        url = f"{self.base_url}{path}"
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            data = resp.read().decode("utf-8")
            return resp.status, json.loads(data)

    def test_get_state(self):
        status, data = self._get("/api/state")
        self.assertEqual(status, 200)
        self.assertEqual(data["seed"], 1337)
        self.assertIn("node_gateway", data["nodes"])
        self.assertEqual(data["current_node"]["node_id"], "node_gateway")
        self.assertIn("deck", data)
        self.assertIn("career", data)
        self.assertIn("lethal", data["extraction_risk"])
        contract = data["state"]["active_contract"]
        self.assertEqual(contract["risk_tier"], "priority")
        self.assertGreater(contract["expires_turn"], 0)
        self.assertGreater(contract["bonus_creds"], 0)
        self.assertEqual(len(data["state"]["contract_offers"]), 3)
        side_nodes = [
            node for nid, node in data["nodes"].items() if nid.startswith("node_side_")
        ]
        self.assertGreaterEqual(len(side_nodes), 2)
        self.assertTrue(all(node["node_type"] == "DATA_VAULT" for node in side_nodes))
        self.assertTrue(all(node["ip_address"].startswith("10.0.9.") for node in side_nodes))

    def test_rival_state_and_counter_action(self):
        session = self.server.RequestHandlerClass.server_session
        rival = session.engine.state.rival
        self.assertIsNotNone(rival)
        rival.next_move_turn = session.engine.state.turns_elapsed + 8
        session.engine.deck.cpu_cycles = 8
        before = rival.next_move_turn

        status, res = self._post("/api/action", {"action": "counter_rival"})

        self.assertEqual(status, 200)
        self.assertTrue(res["ok"], res.get("message"))
        self.assertIn("Counter-traced", res["message"])
        self.assertEqual(res["state"]["rival"]["next_move_turn"], before + 5)
        self.assertEqual(res["state"]["deck"]["cpu_cycles"], 6)

    def test_buying_a_consumable_does_not_persist_a_career_upgrade(self):
        session = self.server.RequestHandlerClass.server_session
        old_creds = session.engine.deck.cryptocreds
        old_insurance = session.engine.deck.extraction_insurance
        session.engine.deck.cryptocreds = 1000
        try:
            status, res = self._post("/api/action", {
                "action": "shop_buy",
                "item_id": "dead_mans_switch",
            })
            self.assertEqual(status, 200)
            self.assertTrue(res["ok"], res.get("message"))
            self.assertTrue(session.engine.deck.extraction_insurance)
            profile = session.save_mgr.load_career()
            self.assertNotIn("dead_mans_switch", profile.purchased_upgrades)
        finally:
            session.engine.deck.cryptocreds = old_creds
            session.engine.deck.extraction_insurance = old_insurance

    def test_get_shop(self):
        status, data = self._get("/api/shop")
        self.assertEqual(status, 200)
        self.assertIn("items", data)
        self.assertGreater(len(data["items"]), 0)
        self.assertIn("street_discount", data)

    def test_get_world_state_and_grid_fields(self):
        status, res = self._get("/api/world")
        self.assertEqual(status, 200)
        self.assertIn("clock", res["world"])
        self.assertIn("alert_level", res["world"])
        self.assertIn("shift_effect", res["world"])
        self.assertIn("news", res)

        status, data = self._get("/api/state")
        self.assertEqual(status, 200)
        self.assertIn("world", data)
        self.assertEqual(data["world"]["alert_level"], 10)

    def test_market_markup_reaches_shop_endpoint(self):
        session = self.server.RequestHandlerClass.server_session
        session.engine.state.world.market_index = 1.25
        try:
            status, res = self._get("/api/shop")
            self.assertEqual(status, 200)
            self.assertEqual(res["market_multiplier"], 1.25)
            overclock = next(i for i in res["items"] if i["item_id"] == "overclock_cpu")
            self.assertEqual(overclock["cost"], 188)
            self.assertEqual(overclock["base_cost"], 150)
        finally:
            session.engine.state.world.market_index = 1.0

    def test_reset_career_requires_confirmation(self):
        with self.assertRaises(urllib.error.HTTPError) as refused:
            self._post("/api/action", {"action": "reset_career"})
        self.assertEqual(refused.exception.code, 400)

        status, res = self._post("/api/action", {
            "action": "reset_career",
            "confirm": "RESET",
        })
        self.assertEqual(status, 200)
        self.assertTrue(res["ok"], res.get("message"))
        self.assertEqual(res["state"]["career"]["alias"], "ZeroCool")
        self.assertEqual(res["state"]["career"]["successful_runs"], 0)

    def test_rename_alias_action(self):
        status, res = self._post("/api/action", {"action": "rename_alias", "name": "NightFox"})

        self.assertEqual(status, 200)
        self.assertTrue(res["ok"], res.get("message"))
        self.assertEqual(res["state"]["career"]["alias"], "NightFox")
        self.assertIn("NightFox", res["message"])

        self._post("/api/action", {"action": "rename_alias", "name": "ZeroCool"})

    def test_get_career(self):
        status, data = self._get("/api/career")
        self.assertEqual(status, 200)
        self.assertIn("alias", data)
        self.assertIn("banked_creds", data)
        self.assertEqual(len(data["achievement_catalog"]), 16)
        self.assertTrue(all("unlocked" in entry for entry in data["achievement_catalog"]))
        self.assertEqual(data["faction_ranks"]["syndicate"], "Associate")
        self.assertEqual(data["faction_ranks"]["street"], "Lookout")

    def test_action_scan_and_spoof(self):
        # Scan
        status, res = self._post("/api/action", {"action": "scan"})
        self.assertEqual(status, 200)
        self.assertTrue(res["ok"])
        self.assertIn("Scanned", res["message"])

        # Spoof
        status, res_spoof = self._post("/api/action", {"action": "spoof"})
        self.assertEqual(status, 200)
        self.assertTrue(res_spoof["ok"])

    def test_puzzle_endpoint_and_solve(self):
        # Request frequency puzzle on proxy_a
        status, pdata = self._get("/api/puzzle?node_id=node_proxy_a")
        self.assertEqual(status, 200)
        self.assertTrue(pdata["ok"])
        self.assertEqual(pdata["puzzle_type"], "frequency")

        # Guess wrong frequency
        status, res = self._post("/api/puzzle/solve", {"guess": 10.0})
        self.assertEqual(status, 200)
        self.assertTrue(res["ok"])
        self.assertFalse(res["solved"])

    def test_static_not_found(self):
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self._get("/missing_asset.xyz")
        self.assertEqual(ctx.exception.code, 404)
        ctx.exception.close()

    def test_static_path_traversal_blocked(self):
        # Raw socket: urllib would normalize dot segments before sending, hiding the defect.
        # Two levels up from cyberpulse/static/ reaches the repository root README.md.
        with socket.create_connection(("127.0.0.1", self.port), timeout=3) as sock:
            sock.sendall(b"GET /../../README.md HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: close\r\n\r\n")
            response = b""
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response += chunk
        status_line = response.split(b"\r\n", 1)[0]
        self.assertIn(b"404", status_line)

    def test_static_assets_served(self):
        # GET /
        url = f"{self.base_url}/"
        with urllib.request.urlopen(url, timeout=3.0) as resp:
            self.assertEqual(resp.status, 200)
            self.assertIn("text/html", resp.headers.get("Content-Type", ""))
            html = resp.read().decode("utf-8")
            self.assertIn("CYBERPULSE", html)
            self.assertIn('id="grid-ticker"', html)
            self.assertIn('id="grid-alert"', html)
            self.assertIn('id="grid-shift-effect"', html)
            self.assertIn('id="btn-lay-low"', html)

        # GET /style.css
        url_css = f"{self.base_url}/style.css"
        with urllib.request.urlopen(url_css, timeout=3.0) as resp:
            self.assertEqual(resp.status, 200)
            self.assertIn("text/css", resp.headers.get("Content-Type", ""))
            css = resp.read().decode("utf-8")
            self.assertIn("--font-mono", css)
            self.assertIn(".grid-bar", css)

        # GET /app.js
        url_js = f"{self.base_url}/app.js"
        with urllib.request.urlopen(url_js, timeout=3.0) as resp:
            self.assertEqual(resp.status, 200)
            self.assertIn("javascript", resp.headers.get("Content-Type", ""))
            js = resp.read().decode("utf-8")
            self.assertIn("SoundFX", js)
            self.assertIn("renderGridTicker", js)
            self.assertIn("handleLayLow", js)
            self.assertIn("grid-shift-effect", js)

    def test_server_simulation_actions(self):
        # 1. Probe proxy a
        status, probe_res = self._post("/api/action", {"action": "probe", "target": "192.168.1.10"})
        self.assertEqual(status, 200)
        self.assertTrue(probe_res["ok"])
        self.assertIn("Nmap scan report", probe_res["message"])
        self.assertIn("node_proxy_a", probe_res["state"]["state"]["probed_nodes"])

        # 2. Exploit FTP port 21
        status, exp_res = self._post("/api/action", {"action": "exploit_service", "target": "192.168.1.10", "port": 21})
        self.assertEqual(status, 200)
        self.assertTrue(exp_res["ok"])
        self.assertIn("EXPLOIT SUCCESSFUL", exp_res["message"])

        # 3. List files
        status, ls_res = self._post("/api/action", {"action": "list_files", "target": "192.168.1.10"})
        self.assertEqual(status, 200)
        self.assertTrue(ls_res["ok"])
        self.assertTrue(len(ls_res["files"]) >= 1)

        # 4. Read file
        status, cat_res = self._post("/api/action", {"action": "read_file", "target": "192.168.1.10", "path": "/home/admin/network_map.txt"})
        self.assertEqual(status, 200)
        self.assertTrue(cat_res["ok"])
        self.assertIn("Subnet topology", cat_res["content"])

        # 5. Download file
        status, dl_res = self._post("/api/action", {"action": "download_file", "target": "192.168.1.10", "path": "/home/admin/network_map.txt"})
        self.assertEqual(status, 200)
        self.assertTrue(dl_res["ok"])
        self.assertIn("EXFILTRATION COMPLETE", dl_res["message"])

        # 6. Wipe logs
        status, wipe_res = self._post("/api/action", {"action": "wipe_logs", "target": "192.168.1.10"})
        self.assertEqual(status, 200)
        self.assertTrue(wipe_res["ok"])
        self.assertIn("LOGS SANITIZED", wipe_res["message"])

    def test_get_workshop_and_local_files(self):
        # 1. Test GET /api/workshop
        status, data = self._get("/api/workshop")
        self.assertEqual(status, 200)
        self.assertIn("recipes", data)
        self.assertGreater(len(data["recipes"]), 0)

        # 2. Test GET /api/local_files
        status, ldata = self._get("/api/local_files")
        self.assertEqual(status, 200)
        self.assertEqual(ldata["ip"], "10.99.0.2")
        self.assertEqual(ldata["hostname"], "rig.netrunner.local")
        self.assertIsInstance(ldata["files"], list)
        self.assertIsInstance(ldata["daemons"], list)

    def test_tactical_stance_proxy_and_quickhack_actions(self):
        self._post("/api/action", {"action": "reset", "seed": 7})
        try:
            status, stance = self._post("/api/action", {"action": "stance", "stance": "stealth"})
            self.assertEqual(status, 200)
            self.assertTrue(stance["ok"])
            self.assertEqual(stance["state"]["deck"]["operating_stance"], "stealth")

            status, hack = self._post("/api/action", {"action": "quickhack", "target": "192.168.1.10"})
            self.assertEqual(status, 200)
            self.assertTrue(hack["ok"])
            self.assertIn("QUICKHACK LANDED", hack["message"])
            self.assertEqual(hack["state"]["nodes"]["node_proxy_a"]["status"], "BREACHED")

            status, proxy = self._post("/api/action", {"action": "proxy", "target": "192.168.1.10"})
            self.assertEqual(status, 200)
            self.assertTrue(proxy["ok"])
            self.assertEqual(proxy["state"]["deck"]["proxy_chain"], ["node_proxy_a"])

            status, sever = self._post("/api/action", {"action": "sever_proxy"})
            self.assertEqual(status, 200)
            self.assertTrue(sever["ok"])
            self.assertEqual(sever["state"]["deck"]["proxy_chain"], [])
        finally:
            self._post("/api/action", {"action": "reset", "seed": 1337})

    def test_intel_action_reveals_and_forges(self):
        self._post("/api/action", {"action": "reset", "seed": 11})
        try:
            status, denied = self._post("/api/action", {"action": "intel", "mode": "reveal", "target": "node_vault_1"})
            self.assertEqual(status, 200)
            self.assertFalse(denied["ok"])
            self.assertIn("INSUFFICIENT THREAT INTEL", denied["message"])

            state = denied["state"]
            self.assertGreaterEqual(state["deck"]["threat_intel_count"], 0)
            session = self.server.RequestHandlerClass.server_session
            session.engine.deck.threat_intel_count = 2

            status, reveal = self._post("/api/action", {"action": "intel", "mode": "reveal", "target": "node_vault_1"})
            self.assertEqual(status, 200)
            self.assertTrue(reveal["ok"])
            self.assertIn("INTEL REVEAL", reveal["message"])
            self.assertEqual(reveal["state"]["deck"]["threat_intel_count"], 1)
            self.assertTrue(reveal["state"]["nodes"]["node_vault_1"]["ports"])

            status, forge = self._post("/api/action", {"action": "intel", "mode": "forge"})
            self.assertEqual(status, 200)
            self.assertFalse(forge["ok"])
            self.assertIn("INSUFFICIENT THREAT INTEL", forge["message"])
        finally:
            self._post("/api/action", {"action": "reset", "seed": 1337})

    def test_server_phish_craft_and_daemon(self):
        # 1. Phish target
        status, phish_res = self._post("/api/action", {"action": "phish", "target": "192.168.1.10"})
        self.assertEqual(status, 200)
        self.assertTrue(phish_res["ok"])
        self.assertIn("PHISHING SUCCESS", phish_res["message"])

        # 2. Deploy daemon fails when target is not breached
        status, d_fail = self._post("/api/action", {"action": "deploy_daemon", "target": "192.168.1.10", "daemon_type": "keylogger"})
        self.assertEqual(status, 200)
        self.assertFalse(d_fail["ok"])
        self.assertIn("not breached", d_fail["message"])

        # Breach host via exploit service
        self._post("/api/action", {"action": "exploit_service", "target": "192.168.1.10", "port": 21})

        # Deploy daemon succeeds now that host is breached
        status, d_res = self._post("/api/action", {"action": "deploy_daemon", "target": "192.168.1.10", "daemon_type": "keylogger"})
        self.assertEqual(status, 200)
        self.assertTrue(d_res["ok"])
        self.assertIn("DAEMON INITIALIZED", d_res["message"])

        # 3. Craft invalid recipe gives error
        try:
            status, craft_err = self._post("/api/action", {"action": "craft", "recipe": "non_existent_recipe"})
            self.assertEqual(status, 200)
            self.assertFalse(craft_err["ok"])
            self.assertIn("Unknown recipe", craft_err["message"])
        finally:
            # Reset server session state for subsequent test isolation
            self._post("/api/action", {"action": "reset", "seed": 1337})

    def test_get_cves_firewall_antivirus(self):
        # 1. GET /api/cves
        status, cve_data = self._get("/api/cves")
        self.assertEqual(status, 200)
        self.assertIn("cves", cve_data)
        self.assertGreaterEqual(len(cve_data["cves"]), 5)
        cve_ids = [c["cve_id"] for c in cve_data["cves"]]
        self.assertIn("CVE-2023-38606", cve_ids)

        # 2. GET /api/firewall
        status, fw_data = self._get("/api/firewall?ip=192.168.1.10")
        self.assertEqual(status, 200)
        self.assertTrue(fw_data["ok"])
        self.assertIn("firewall", fw_data)
        self.assertTrue(fw_data["firewall"]["enabled"])
        self.assertGreater(len(fw_data["firewall"]["rules"]), 0)

        # 3. GET /api/antivirus
        status, av_data = self._get("/api/antivirus?ip=192.168.1.10")
        self.assertEqual(status, 200)
        self.assertTrue(av_data["ok"])
        self.assertIn("antivirus", av_data)
        self.assertIn("DefenderBasic", av_data["antivirus"]["name"])

    def test_firewall_bypass_evade_and_social(self):
        try:
            # 1. Bypass blocked port 22 on proxy_b
            status, bp_res = self._post("/api/action", {
                "action": "bypass",
                "target": "192.168.1.20",
                "port": 22,
                "method": "knock",
            })
            self.assertEqual(status, 200)
            self.assertTrue(bp_res["ok"])
            self.assertIn("FIREWALL BYPASSED", bp_res["message"])
            self.assertIn("Port 22/tcp rule deactivated", bp_res["message"])

            # 2. Evade AV on proxy_a
            status, ev_res = self._post("/api/action", {
                "action": "evade",
                "target": "192.168.1.10",
                "method": "rootkit",
            })
            self.assertEqual(status, 200)
            self.assertTrue(ev_res["ok"])
            self.assertIn("ANTIVIRUS EVADED", ev_res["message"])

            # 3. Multi-vector social engineering on proxy_a
            status, soc_res = self._post("/api/action", {
                "action": "social",
                "target": "192.168.1.10",
                "vector": "pretext",
            })
            self.assertEqual(status, 200)
            self.assertTrue(soc_res["ok"])
            self.assertIn("SOCIAL ENGINEERING SUCCESS", soc_res["message"])

            # 4. Exploit service specifying known CVE
            status, exp_cve = self._post("/api/action", {
                "action": "exploit_service",
                "target": "192.168.1.10",
                "port": 21,
                "cve_id": "CVE-2011-2523",
            })
            self.assertEqual(status, 200)
            self.assertTrue(exp_cve["ok"])
            self.assertIn("CVE-2011-2523", exp_cve["message"])
        finally:
            self._post("/api/action", {"action": "reset", "seed": 1337})


    def test_malformed_port_is_rejected_with_json_error(self):
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self._post("/api/action", {"action": "bypass", "target": "192.168.1.20", "port": "not-a-number"})
        self.assertEqual(ctx.exception.code, 400)
        payload = json.loads(ctx.exception.read().decode("utf-8"))
        ctx.exception.close()
        self.assertFalse(payload["ok"])

    def test_craft_accepts_recipe_name_from_web_client(self):
        self._post("/api/action", {"action": "reset", "seed": 1337})

        status, res = self._post("/api/action", {"action": "craft", "recipe": "trace_cleaner"})

        self.assertEqual(status, 200)
        self.assertTrue(res["ok"])
        self.assertIn("trace_cleaner", res["state"]["deck"]["exploits"])

    def test_json_responses_do_not_enable_wildcard_cors(self):
        with urllib.request.urlopen(f"{self.base_url}/api/state", timeout=3.0) as resp:
            self.assertIsNone(resp.headers.get("Access-Control-Allow-Origin"))

    def test_reset_accepts_float_seed(self):
        status, res = self._post("/api/action", {"action": "reset", "seed": 42.9})
        self.assertEqual(status, 200)
        self.assertTrue(res["ok"])
        self.assertEqual(res["state"]["seed"], 42)

    def test_reset_rejects_invalid_seed(self):
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self._post("/api/action", {"action": "reset", "seed": "not-a-seed"})
        self.assertEqual(ctx.exception.code, 400)
        payload = json.loads(ctx.exception.read().decode("utf-8"))
        ctx.exception.close()
        self.assertFalse(payload["ok"])

    def test_puzzle_retry_keeps_remaining_attempts(self):
        self._post("/api/action", {"action": "reset", "seed": 1337})
        status, first = self._get("/api/puzzle?node_id=node_proxy_a")
        self.assertEqual(status, 200)
        self.assertEqual(first["attempts_left"], 3)

        self._post("/api/puzzle/solve", {"guess": 0.0})
        status, second = self._get("/api/puzzle?node_id=node_proxy_a")

        self.assertEqual(status, 200)
        self.assertEqual(second["attempts_left"], 2)

    def test_buffer_near_miss_grants_one_web_retry_then_locks_host(self):
        self._post("/api/action", {"action": "reset", "seed": 1337})
        _, puzzle = self._get("/api/puzzle?node_id=node_proxy_b")
        target_seq = puzzle["target_seq"]
        near_seq = [target_seq[0], "ZZ"]

        _, first = self._post("/api/puzzle/solve", {"guess": near_seq})
        self.assertFalse(first["solved"])
        self.assertTrue(first["near_miss"])
        self.assertTrue(first["near_miss_bonus"])
        self.assertIn("NEAR-MISS SURGE", first["message"])

        _, second = self._post("/api/puzzle/solve", {"guess": near_seq})
        self.assertFalse(second["solved"])
        self.assertFalse(second["near_miss_bonus"])
        self.assertIn("HOST LOCKDOWN", second["message"])
        self.assertGreater(second["state"]["nodes"]["node_proxy_b"]["lockdown_until_turn"], 0)

    def test_victory_settles_career_once(self):
        data_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, data_dir, ignore_errors=True)
        session = CyberdeckSession(data_dir=data_dir, seed=7)
        session.engine.state.is_victory = True
        session.engine.state.unbanked_creds = 175
        session.engine.state.best_combo = 3

        first = session.get_full_state()
        second = session.get_full_state()

        self.assertEqual(first["career"]["successful_runs"], 1)
        self.assertEqual(second["career"]["successful_runs"], 1)
        self.assertEqual(second["career"]["banked_creds"], 275)
        self.assertEqual(second["career"]["best_combo"], 3)
        self.assertEqual(second["state"]["unbanked_creds"], 0)
        self.assertEqual(second["run_summary"]["outcome"], "victory")

    def test_game_over_settles_failed_run_once(self):
        data_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, data_dir, ignore_errors=True)
        session = CyberdeckSession(data_dir=data_dir, seed=7)
        session.engine.state.is_game_over = True

        first = session.get_full_state()
        second = session.get_full_state()

        self.assertEqual(first["career"]["failed_runs"], 1)
        self.assertEqual(second["career"]["failed_runs"], 1)

    def test_craft_persists_banked_spend(self):
        session = self.server.RequestHandlerClass.server_session
        session.save_mgr.career_file.unlink(missing_ok=True)
        session.save_mgr.career_file.with_suffix(".bak").unlink(missing_ok=True)
        self._post("/api/action", {"action": "reset", "seed": 1337})
        status, res = self._post("/api/action", {"action": "craft", "recipe": "trace_cleaner"})

        self.assertEqual(status, 200)
        self.assertTrue(res["ok"])
        self.assertEqual(res["state"]["deck"]["cryptocreds"], 20)
        self.assertEqual(res["state"]["career"]["banked_creds"], 20)

    def test_forecast_endpoint_matches_engine_costs(self):
        status, data = self._get("/api/forecast?action=scan")
        self.assertEqual(status, 200)
        self.assertTrue(data["ok"])
        self.assertEqual(data["cpu_delta"], 1)
        self.assertEqual(data["turns"], 1)

    def test_route_endpoint_reports_hops(self):
        status, data = self._get("/api/route?target=node_central_core")
        self.assertEqual(status, 200)
        self.assertTrue(data["ok"])
        self.assertGreaterEqual(data["hop_count"], 2)
        self.assertEqual(data["hops"][-1]["node_id"], "node_central_core")
        self.assertGreater(data["total_latency_ms"], 0)

    def test_web_settlement_does_not_delete_unowned_save(self):
        data_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, data_dir, ignore_errors=True)
        session = CyberdeckSession(data_dir=data_dir, seed=7)
        saved = session.save_mgr.save(session.engine)
        self.assertIsNotNone(saved)
        self.assertTrue(session.save_mgr.save_file.exists())

        session.engine.state.is_victory = True
        session.get_full_state()

        self.assertTrue(session.save_mgr.save_file.exists())

    def test_state_includes_story_quests_and_contacts(self):
        status, res = self._get("/api/state")
        self.assertEqual(status, 200)
        self.assertIn("story", res)
        self.assertIn("run_summary", res)
        self.assertIn("quests", res)
        self.assertIn("contacts", res)
        self.assertEqual([step["step_id"] for step in res["tutorial"]], [
            "scan", "probe", "breach", "loot", "jackout",
        ])
        self.assertEqual(res["story"]["act"], 1)
        self.assertEqual(res["run_summary"]["outcome"], "active")
        self.assertTrue(any(q["quest_id"] == "q_gateway" for q in res["quests"]))
        self.assertTrue(any(c["contact_id"] == "mira" for c in res["contacts"]))

    def test_overdrive_action(self):
        self._post("/api/action", {"action": "reset", "seed": 1337})
        status, res = self._post("/api/action", {"action": "overdrive"})
        self.assertEqual(status, 200)
        self.assertTrue(res["ok"])
        self.assertEqual(res["state"]["state"]["combo_streak"], 1)
        self.assertEqual(res["state"]["state"]["trace_percent"], 8)
        self.assertEqual(res["state"]["deck"]["cpu_cycles"], 8)

    def test_contact_talk_job_and_favor_actions(self):
        self._post("/api/action", {"action": "reset", "seed": 1337})
        status, res = self._post("/api/action", {"action": "contact", "contact_id": "kilo", "mode": "talk"})
        self.assertEqual(status, 200)
        self.assertTrue(res["ok"])
        self.assertIn("Kilo", res["message"])

        status, res = self._post("/api/action", {"action": "contact", "contact_id": "kilo", "mode": "job"})
        self.assertTrue(res["ok"])
        self.assertIn("QUEST ACCEPTED", res["message"])
        self.assertTrue(any(q["quest_id"] == "q_side_craft" and q["accepted"] for q in res["state"]["quests"]))

        self._post("/api/action", {"action": "overdrive"})
        status, res = self._post("/api/action", {"action": "contact", "contact_id": "kilo", "mode": "favor"})
        self.assertTrue(res["ok"])
        self.assertIn("CPU restored", res["message"])
        self.assertEqual(res["state"]["deck"]["cpu_cycles"], res["state"]["deck"]["max_cpu"])

    def test_agent_zero_alliance_action(self):
        session = self.server.RequestHandlerClass.server_session
        session.engine.state.story_act = 3
        try:
            status, res = self._post("/api/action", {
                "action": "contact",
                "contact_id": "zero",
                "mode": "ally",
            })
            self.assertEqual(status, 200)
            self.assertTrue(res["ok"])
            self.assertIn("ALLIANCE FORGED", res["message"])
            self.assertEqual(res["state"]["story"]["choice"], "zero_ally")
            self.assertEqual(res["state"]["story"]["choice_label"], "ALLIED WITH AGENT ZERO")
            self.assertTrue(any(
                c["contact_id"] == "zero" and not c["pact_available"]
                for c in res["state"]["contacts"]
            ))
        finally:
            self._post("/api/action", {"action": "reset", "seed": 1337})

    def test_accept_quest_action_respects_trust_gate(self):
        self._post("/api/action", {"action": "reset", "seed": 1337})
        status, blocked = self._post("/api/action", {"action": "accept_quest", "quest_id": "q_side_ghost"})
        self.assertEqual(status, 200)
        self.assertFalse(blocked["ok"])
        self.assertIn("trust", blocked["message"])

        status, primary = self._post("/api/action", {"action": "accept_quest", "quest_id": "q_side_craft"})
        self.assertTrue(primary["ok"])
        status, res = self._post("/api/action", {"action": "accept_quest", "quest_id": "q_side_ghost"})
        self.assertEqual(status, 200)
        self.assertTrue(res["ok"])
        self.assertTrue(any(q["quest_id"] == "q_side_ghost" and q["accepted"] for q in res["state"]["quests"]))

    def test_contract_board_decline_and_accept_action(self):
        self._post("/api/action", {"action": "reset", "seed": 1337})
        _, declined = self._post("/api/action", {"action": "decline_contract"})
        self.assertTrue(declined["ok"])
        self.assertIsNone(declined["state"]["state"]["active_contract"])
        offers = declined["state"]["state"]["contract_offers"]
        self.assertEqual(len(offers), 3)
        offer_id = offers[0]["contract_id"]
        self._post("/api/action", {"action": "lay_low", "turns": 1})

        _, accepted = self._post(
            "/api/action", {"action": "accept_contract", "contract_id": offer_id}
        )

        self.assertTrue(accepted["ok"])
        active = accepted["state"]["state"]["active_contract"]
        self.assertEqual(active["contract_id"], offer_id)
        self.assertGreater(active["expires_turn"], 0)
        self.assertEqual(len(accepted["state"]["state"]["contract_offers"]), 3)

    def test_drop_offer_action_spends_broker_fee(self):
        self._post("/api/action", {"action": "reset", "seed": 1337})
        session = self.server.RequestHandlerClass.server_session
        with session.lock:
            session.engine.deck.cryptocreds = 100
        _, state = self._get("/api/state")
        offer_id = state["state"]["contract_offers"][0]["contract_id"]
        before = state["deck"]["cryptocreds"]

        _, dropped = self._post("/api/action", {"action": "drop_offer", "contract_id": offer_id})

        self.assertTrue(dropped["ok"])
        self.assertEqual(dropped["state"]["deck"]["cryptocreds"], before - 30)
        self.assertEqual(len(dropped["state"]["state"]["contract_offers"]), 3)
        self.assertNotIn(
            offer_id,
            [offer["contract_id"] for offer in dropped["state"]["state"]["contract_offers"]],
        )

    def test_accept_quest_after_jackout_is_rejected(self):
        self._post("/api/action", {"action": "reset", "seed": 1337})
        try:
            status, res = self._post("/api/action", {"action": "jackout"})
            self.assertTrue(res["ok"])

            status, res = self._post("/api/action", {"action": "accept_quest", "quest_id": "q_side_ghost"})

            self.assertEqual(status, 200)
            self.assertFalse(res["ok"])
            self.assertIn("jacked out", res["message"])
        finally:
            # Restore the shared session so later tests do not inherit the jacked-out run.
            self._post("/api/action", {"action": "reset", "seed": 1337})

    def test_static_assets_do_not_wait_for_session_lock(self):
        session = self.server.RequestHandlerClass.server_session
        acquired = threading.Event()
        release = threading.Event()

        def hold_session_lock():
            with session.lock:
                acquired.set()
                release.wait(3)

        thread = threading.Thread(target=hold_session_lock, daemon=True)
        thread.start()
        self.assertTrue(acquired.wait(1))
        try:
            with urllib.request.urlopen(f"{self.base_url}/style.css", timeout=1.0) as resp:
                self.assertEqual(resp.status, 200)
        finally:
            release.set()
            thread.join(2)

    def test_get_world_and_state_contains_hunters(self):
        status, data = self._get("/api/world")
        self.assertEqual(status, 200)
        self.assertIn("world", data)
        self.assertIn("active_hunters_count", data["world"])
        self.assertIn("hunters", data["world"])
        self.assertIn("nearest_hunter_distance", data["world"])

        status, state = self._get("/api/state")
        self.assertEqual(status, 200)
        self.assertIn("world", state)
        self.assertIn("hunters", state["world"])

    def test_counter_hunter_api_action(self):
        # When no hunter active
        status, res = self._post("/api/action", {"action": "counter", "method": "logic_bomb"})
        self.assertEqual(status, 200)
        self.assertFalse(res["ok"])
        self.assertIn("No active NetWatch hunters", res["message"])

    def test_lay_low_api_action(self):
        session = self.server.RequestHandlerClass.server_session
        engine = session.engine
        world = engine.state.world
        saved = (
            world.alert_level,
            world.minute,
            world.day,
            world.turns_since_event,
            engine.state.trace_percent,
            engine.deck.cpu_cycles,
            engine.state.turns_elapsed,
        )
        world.alert_level = 0
        world.turns_since_event = -50
        engine.state.trace_percent = 0
        engine.deck.cpu_cycles = 0
        start_turns = engine.state.turns_elapsed
        try:
            status, res = self._post("/api/action", {"action": "lay_low", "turns": 2})
            self.assertEqual(status, 200)
            self.assertTrue(res["ok"])
            self.assertIn("LAY LOW", res["message"])
            self.assertEqual(res["state"]["state"]["turns_elapsed"], start_turns + 2)
            self.assertEqual(res["state"]["deck"]["cpu_cycles"], 2)
            self.assertIn("shift_effect", res["state"]["world"])

            status, alias = self._post("/api/action", {"action": "wait", "turns": 1})
            self.assertEqual(status, 200)
            self.assertTrue(alias["ok"])
            self.assertIn("LAY LOW", alias["message"])
        finally:
            (
                world.alert_level,
                world.minute,
                world.day,
                world.turns_since_event,
                engine.state.trace_percent,
                engine.deck.cpu_cycles,
                engine.state.turns_elapsed,
            ) = saved


class TestCyberdeckSaveLoadSession(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.temp_dir, True)
        self.session = CyberdeckSession(data_dir=self.temp_dir, seed=7)

    def test_save_then_load_restores_exact_progress(self):
        engine = self.session.engine
        scanned, _, _ = engine.scan_surroundings()
        self.assertTrue(scanned)
        puzzle_ok, _, _, _ = engine.get_or_create_puzzle("node_proxy_a")
        self.assertTrue(puzzle_ok)
        saved_trace = engine.state.trace_percent
        saved_turn = engine.state.turns_elapsed

        saved, message = self.session.save_run()

        self.assertTrue(saved, message)
        self.assertIn("saved", message.lower())
        self.assertTrue(self.session.save_mgr.has_save())

        self.session.engine.state.turns_elapsed = 9
        loaded, message = self.session.load_run()

        self.assertTrue(loaded, message)
        self.assertIn("Loaded", message)
        self.assertEqual(self.session.engine.state.trace_percent, saved_trace)
        self.assertEqual(self.session.engine.state.turns_elapsed, saved_turn)
        self.assertIn("node_proxy_a", self.session.engine.pending_puzzles)

    def test_load_without_a_save_reports_a_missing_run(self):
        loaded, message = self.session.load_run()

        self.assertFalse(loaded)
        self.assertIn("No saved run", message)

    def test_terminal_run_is_not_saved(self):
        self.session.engine.state.is_victory = True

        saved, message = self.session.save_run()

        self.assertFalse(saved)
        self.assertIn("nothing left to save", message)
        self.assertFalse(self.session.save_mgr.has_save())

    def test_finishing_a_run_deletes_an_earlier_save(self):
        saved, message = self.session.save_run()
        self.assertTrue(saved, message)
        self.assertTrue(self.session.save_mgr.has_save())

        self.session.engine.state.is_victory = True
        state = self.session.get_full_state()

        self.assertFalse(state["has_save"])
        self.assertTrue(self.session.engine.run_settled)

    def test_save_run_accepts_a_named_slot(self):
        self.session.engine.state.trace_percent = 21

        saved, message = self.session.save_run(2)
        self.assertTrue(saved, message)
        self.assertIn("SLOT 2", message)

        self.session.engine.state.trace_percent = 80
        loaded, message = self.session.load_run(2)

        self.assertTrue(loaded, message)
        self.assertIn("SLOT 2", message)
        self.assertEqual(self.session.engine.state.trace_percent, 21)

    def test_autosave_starts_after_baseline_and_tracks_changes(self):
        self.assertEqual(self.session.get_full_state()["saves"], [])

        self.session.engine.state.trace_percent = 17
        state = self.session.get_full_state()

        auto = [entry for entry in state["saves"] if entry["slot"] == "auto"]
        self.assertEqual(len(auto), 1)
        self.assertEqual(auto[0]["trace"], 17)
        self.assertTrue(self.session.save_mgr.autosave_file.exists())

    def test_reset_can_start_a_daily_run(self):
        with mock.patch("cyberpulse.server.daily_run", return_value=("2026-10-30", 20261030)):
            state = self.session.reset_game(daily=True)

        self.assertEqual(state["daily_key"], "2026-10-30")
        self.assertEqual(state["seed"], 20261030)
        self.assertEqual(self.session.engine.daily_key, "2026-10-30")

    def test_manual_save_refuses_the_auto_slot(self):
        saved, message = self.session.save_run("auto")

        self.assertFalse(saved)
        self.assertIn("automatic", message)
        self.assertFalse(self.session.save_mgr.autosave_file.exists())

    def test_autosave_can_be_loaded_from_its_slot(self):
        self.session.engine.state.trace_percent = 33
        self.assertIsNotNone(self.session.save_mgr.autosave(self.session.engine))

        loaded, message = self.session.load_run("auto")

        self.assertTrue(loaded, message)
        self.assertIn("AUTOSAVE", message)
        self.assertEqual(self.session.engine.state.trace_percent, 33)

    def test_named_slot_can_be_renamed_without_reloading_it(self):
        self.session.engine.state.trace_percent = 18
        saved, message = self.session.save_run(3, name="Night Run")
        self.assertTrue(saved, message)

        renamed, message = self.session.rename_save(3, "Vault Run")
        self.assertTrue(renamed, message)
        saves = {entry["slot"]: entry for entry in self.session.get_full_state()["saves"]}
        self.assertEqual(saves["3"]["name"], "Vault Run")
        self.assertEqual(saves["3"]["trace"], 18)

    def test_delete_save_leaves_the_live_run_untouched(self):
        self.session.engine.state.trace_percent = 77
        self.assertTrue(self.session.save_run(2)[0])

        deleted, message = self.session.delete_save(2)

        self.assertTrue(deleted, message)
        self.assertFalse(self.session.save_mgr.has_save(2))
        self.assertEqual(self.session.engine.state.trace_percent, 77)
        self.assertEqual(self.session.get_full_state()["state"]["trace_percent"], 77)

    def test_invalid_slot_is_rejected(self):
        with self.assertRaises(ValueError):
            self.session.save_run(9)

    def test_settlement_deletes_every_checkpoint_of_the_run(self):
        self.session.engine.state.trace_percent = 5
        self.assertTrue(self.session.save_run(1)[0])
        self.session.engine.state.trace_percent = 6
        self.assertTrue(self.session.save_run(3)[0])
        self.session.engine.state.trace_percent = 7
        self.assertIsNotNone(self.session.save_mgr.autosave(self.session.engine))

        self.session.engine.state.is_victory = True
        state = self.session.get_full_state()

        self.assertTrue(self.session.engine.run_settled)
        self.assertFalse(state["has_save"])
        self.assertEqual(state["saves"], [])


class TestCyberdeckSaveLoadAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = Path(tempfile.mkdtemp())
        cls.server = create_server(host="127.0.0.1", port=0, data_dir=cls.temp_dir, seed=5)
        cls.port = cls.server.server_address[1]
        cls.base_url = f"http://127.0.0.1:{cls.port}"
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def _post(self, payload: dict):
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/action",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def _state(self):
        with urllib.request.urlopen(f"{self.base_url}/api/state", timeout=3.0) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def test_save_and_continue_round_trip(self):
        self.assertFalse(self._state()["has_save"])

        missing = self._post({"action": "load"})
        self.assertFalse(missing["ok"])
        self.assertIn("No saved run", missing["message"])

        scan = self._post({"action": "scan"})
        self.assertTrue(scan["ok"])
        self.assertEqual(scan["state"]["state"]["trace_percent"], 5)

        saved = self._post({"action": "save"})
        self.assertTrue(saved["ok"], saved.get("message"))
        self.assertTrue(saved["state"]["has_save"])

        second_scan = self._post({"action": "scan"})
        self.assertEqual(second_scan["state"]["state"]["trace_percent"], 10)

        loaded = self._post({"action": "load"})
        self.assertTrue(loaded["ok"], loaded.get("message"))
        self.assertEqual(loaded["state"]["state"]["trace_percent"], 5)
        self.assertEqual(loaded["state"]["state"]["turns_elapsed"], 1)


class TestCyberdeckSaveSlotsAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = Path(tempfile.mkdtemp())
        cls.server = create_server(host="127.0.0.1", port=0, data_dir=cls.temp_dir, seed=15)
        cls.port = cls.server.server_address[1]
        cls.base_url = f"http://127.0.0.1:{cls.port}"
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def _post(self, payload: dict):
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/action",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def test_reset_career_aborts_when_backup_fails(self):
        session = self.server.RequestHandlerClass.server_session
        profile = session.save_mgr.load_career()
        profile.alias = "KeepMe"
        session.save_mgr.save_career(profile)
        with mock.patch.object(session.save_mgr, "_write_atomic", return_value=None):
            try:
                self._post({"action": "reset_career", "confirm": "RESET"})
            except urllib.error.HTTPError as exc:
                self.assertEqual(exc.code, 500)
            else:
                self.fail("reset_career should fail when the backup cannot be written")
        self.assertEqual(session.save_mgr.load_career().alias, "KeepMe")

    def test_reroll_contracts_action(self):
        self._post({"action": "reset", "seed": 5})
        self.server.RequestHandlerClass.server_session.engine.deck.cryptocreds = 100
        res = self._post({"action": "reroll_contracts"})

        self.assertTrue(res["ok"], res.get("message"))
        self.assertIn("Rerolled", res["message"])
        self.assertEqual(res["state"]["deck"]["cryptocreds"], 50)
        self.assertEqual(len(res["state"]["state"]["contract_offers"]), 3)

    def test_reset_accepts_faction_allegiance(self):
        res = self._post({
            "action": "reset",
            "allegiance": "street",
            "difficulty": "normal",
        })

        self.assertTrue(res["ok"], res.get("message"))
        self.assertEqual(res["state"]["allegiance"], "street")
        self.assertLess(
            res["state"]["shop_items"][0]["cost"],
            self._post({"action": "reset", "allegiance": "none"})["state"]["shop_items"][0]["cost"],
        )

    def test_invalid_or_named_difficulty_reset(self):
        res = self._post({"action": "reset", "difficulty": "hard"})

        self.assertTrue(res["ok"], res.get("message"))
        self.assertEqual(res["state"]["difficulty"], "hard")
        self.assertEqual(res["state"]["state"]["world"]["alert_level"], 25)

        fallback = self._post({"action": "reset", "difficulty": "nightmare"})
        self.assertEqual(fallback["state"]["difficulty"], "normal")

    def test_daily_reset_over_http(self):
        with mock.patch("cyberpulse.server.daily_run", return_value=("2026-10-30", 20261030)):
            res = self._post({"action": "reset", "daily": True})

        self.assertTrue(res["ok"], res.get("message"))
        self.assertEqual(res["state"]["daily_key"], "2026-10-30")
        self.assertEqual(res["state"]["seed"], 20261030)
        self.assertIsNotNone(res["state"]["daily_modifier"])
        self.assertIn("Daily run 2026-10-30", res["message"])

    def test_name_rename_and_delete_over_http(self):
        saved = self._post({"action": "save", "slot": 3, "name": "Night Run"})
        self.assertTrue(saved["ok"], saved.get("message"))
        self.assertIn("Night Run", saved["message"])
        slot_three = {entry["slot"]: entry for entry in saved["state"]["saves"]}["3"]
        self.assertEqual(slot_three["name"], "Night Run")

        renamed = self._post({"action": "rename_save", "slot": 3, "name": "Vault Run"})
        self.assertTrue(renamed["ok"], renamed.get("message"))
        slot_three = {entry["slot"]: entry for entry in renamed["state"]["saves"]}["3"]
        self.assertEqual(slot_three["name"], "Vault Run")

        trace_before = renamed["state"]["state"]["trace_percent"]
        deleted = self._post({"action": "delete_save", "slot": 3})

        self.assertTrue(deleted["ok"], deleted.get("message"))
        self.assertNotIn("3", {entry["slot"] for entry in deleted["state"]["saves"]})
        self.assertEqual(deleted["state"]["state"]["trace_percent"], trace_before)

    def test_named_slot_round_trip_and_autosave_payload(self):
        scanned = self._post({"action": "scan"})
        self.assertEqual(scanned["state"]["state"]["trace_percent"], 5)
        auto_slots = [entry for entry in scanned["state"]["saves"] if entry["slot"] == "auto"]
        self.assertEqual(len(auto_slots), 1)
        self.assertEqual(auto_slots[0]["trace"], 5)

        saved = self._post({"action": "save", "slot": 2})
        self.assertTrue(saved["ok"], saved.get("message"))
        self.assertIn("SLOT 2", saved["message"])
        self.assertIn("2", {entry["slot"] for entry in saved["state"]["saves"]})

        self._post({"action": "scan"})
        loaded = self._post({"action": "load", "slot": 2})

        self.assertTrue(loaded["ok"], loaded.get("message"))
        self.assertEqual(loaded["state"]["state"]["trace_percent"], 5)
        self.assertEqual(loaded["state"]["state"]["turns_elapsed"], 1)


    def test_web_actions_mirror_into_deckos_history(self):
        res = self._post({"action": "scan"})
        self.assertIn("scan", res["state"]["state"].get("cmd_history", []))
        # Meta actions stay out of the shell history.
        saved = self._post({"action": "save", "slot": 1})
        self.assertTrue(saved["ok"], saved.get("message"))
        hist = saved["state"]["state"].get("cmd_history", [])
        self.assertFalse(any(str(entry).startswith("save") for entry in hist))

    def test_state_nodes_carry_district_tags(self):
        session = self.server.RequestHandlerClass.server_session
        tags = session.engine.node_districts()
        self.assertTrue(tags)
        self.assertEqual(set(tags), set(session.engine.nodes))
        for nid, tag in tags.items():
            self.assertIn("district", tag)
            self.assertIn(tag["district_patrol"], ("light", "standard", "heavy"))
        full = session.get_full_state()
        self.assertTrue(full["state"]["contract_offers"])
        for offer in full["state"]["contract_offers"]:
            self.assertIn("district", offer)
            self.assertIn(offer["district_patrol"], ("light", "standard", "heavy"))


if __name__ == "__main__":
    unittest.main()


