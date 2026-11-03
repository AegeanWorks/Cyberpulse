"""Unit tests for CyberPulse domain models."""

import unittest
from cyberpulse.models import (
    BountyContract,
    CareerProfile,
    CyberDeck,
    EmployeeProfile,
    ExploitPayload,
    FirewallPolicy,
    FirewallRule,
    GameState,
    HostAntivirus,
    HostFirewall,
    MalwareDaemon,
    Node,
    NodeStatus,
    NodeType,
    PortService,
    RewardType,
    SecurityAwarenessLevel,
    SocialVectorType,
    VirtualFile,
    VirusCraftRecipe,
    apply_career_profile,
)


class TestModels(unittest.TestCase):
    def test_node_roundtrip(self):
        port = PortService(port=22, service="ssh", version="OpenSSH 7.2", vulnerable=True)
        vfile = VirtualFile(path="/etc/passwd", size_kb=2, content="root:x:0:0", value_creds=10)
        node = Node(
            node_id="n1",
            name="Proxy Server",
            node_type=NodeType.FIREWALL,
            security_level=2,
            status=NodeStatus.DISCOVERED,
            connected_ids=["n2"],
            trace_rate=15,
            credits_reward=100,
            ip_address="192.168.1.10",
            hostname="proxy.alpha",
            ports=[port],
            filesystem=[vfile],
        )
        data = node.to_dict()
        restored = Node.from_dict(data)
        self.assertEqual(restored.node_id, "n1")
        self.assertEqual(restored.node_type, NodeType.FIREWALL)
        self.assertEqual(restored.credits_reward, 100)
        self.assertEqual(restored.ip_address, "192.168.1.10")
        self.assertEqual(restored.hostname, "proxy.alpha")
        self.assertEqual(len(restored.ports), 1)
        self.assertEqual(restored.ports[0].port, 22)
        self.assertEqual(restored.ports[0].service, "ssh")
        self.assertEqual(len(restored.filesystem), 1)
        self.assertEqual(restored.filesystem[0].path, "/etc/passwd")

    def test_port_and_file_roundtrip(self):
        port = PortService(port=3306, service="mysql", version="MariaDB 10.3", vulnerable=True, exploit_tool="sql_inject")
        p_dict = port.to_dict()
        p_restored = PortService.from_dict(p_dict)
        self.assertEqual(p_restored.port, 3306)
        self.assertEqual(p_restored.exploit_tool, "sql_inject")

        vfile = VirtualFile(path="/data/secret.csv", size_kb=16, content="confidential", value_creds=200, is_target_data=True)
        f_dict = vfile.to_dict()
        f_restored = VirtualFile.from_dict(f_dict)
        self.assertEqual(f_restored.path, "/data/secret.csv")
        self.assertEqual(f_restored.value_creds, 200)
        self.assertTrue(f_restored.is_target_data)

    def test_deck_roundtrip(self):
        daemon = MalwareDaemon(daemon_id="d1", daemon_type="keylogger", target_node_id="n1", target_ip="192.168.1.10")
        deck = CyberDeck(cryptocreds=500, cpu_cycles=8, ice_dampener_level=1, active_daemons=[daemon])
        data = deck.to_dict()
        restored = CyberDeck.from_dict(data)
        self.assertEqual(restored.cryptocreds, 500)
        self.assertEqual(restored.cpu_cycles, 8)
        self.assertEqual(restored.ice_dampener_level, 1)
        self.assertEqual(restored.local_ip, "10.99.0.2")
        self.assertTrue(len(restored.local_filesystem) >= 1)
        self.assertEqual(len(restored.active_daemons), 1)
        self.assertEqual(restored.active_daemons[0].daemon_type, "keylogger")

    def test_recipe_roundtrip(self):
        recipe = VirusCraftRecipe(name="worm_prime", vector="worm", payload="credit_siphon", cost_creds=120)
        r_dict = recipe.to_dict()
        restored = VirusCraftRecipe.from_dict(r_dict)
        self.assertEqual(restored.name, "worm_prime")
        self.assertEqual(restored.vector, "worm")
        self.assertEqual(restored.payload, "credit_siphon")

    def test_game_state_roundtrip(self):
        contract = BountyContract(contract_id="c1", title="Heist", target_node_type=NodeType.DATA_VAULT)
        state = GameState(
            seed=42,
            current_node_id="node_gateway",
            trace_percent=25,
            unbanked_creds=150,
            lost_creds=42,
            active_contract=contract,
        )
        data = state.to_dict()
        restored = GameState.from_dict(data)
        self.assertEqual(restored.seed, 42)
        self.assertEqual(restored.trace_percent, 25)
        self.assertEqual(restored.unbanked_creds, 150)
        self.assertEqual(restored.lost_creds, 42)
        self.assertIsNotNone(restored.active_contract)
        self.assertEqual(restored.active_contract.contract_id, "c1")

    def test_game_state_backfills_missing_lost_creds(self):
        data = GameState(seed=1, current_node_id="node_gateway").to_dict()
        data.pop("lost_creds")
        self.assertEqual(GameState.from_dict(data).lost_creds, 0)

    def test_bounty_contract_objective_inference_and_deadline_roundtrip(self):
        legacy = BountyContract(
            contract_id="c-legacy",
            title="Legacy Wipe",
            target_node_type=NodeType.DATA_VAULT,
            target_file="/data/ledger.csv",
            wipe_logs_required=True,
        )
        self.assertEqual(legacy.objective_kind, "wipe")

        contract = BountyContract(
            contract_id="c-new",
            title="Deadline Job",
            target_node_type=NodeType.FIREWALL,
            target_ip="192.168.1.10",
            giver="mira",
            risk_tier="black",
            objective="breach",
            expires_turn=30,
            rush_turn=16,
            bonus_creds=90,
            description="Breach the border firewall.",
        )
        restored = BountyContract.from_dict(contract.to_dict())

        self.assertEqual(restored.objective_kind, "breach")
        self.assertEqual(restored.giver, "mira")
        self.assertEqual(restored.risk_tier, "black")
        self.assertEqual(restored.expires_turn, 30)
        self.assertEqual(restored.rush_turn, 16)
        self.assertEqual(restored.bonus_creds, 90)
        self.assertEqual(restored.description, "Breach the border firewall.")

    def test_career_profile_roundtrip(self):
        profile = CareerProfile(alias="Phantom", banked_creds=1200, current_streak=3)
        data = profile.to_dict()
        restored = CareerProfile.from_dict(data)
        self.assertEqual(restored.alias, "Phantom")
        self.assertEqual(restored.banked_creds, 1200)
        self.assertEqual(restored.current_streak, 3)

    def test_career_alias_is_trimmed_and_defaulted(self):
        self.assertEqual(CareerProfile.from_dict({"alias": "  Night   Fox  "}).alias, "Night Fox")
        self.assertEqual(CareerProfile.from_dict({"alias": ""}).alias, "ZeroCool")
        self.assertEqual(CareerProfile.from_dict({"alias": "x" * 40}).alias, "x" * 24)

    def test_old_career_payload_defaults_to_empty_run_history(self):
        restored = CareerProfile.from_dict({"alias": "OldTimer", "banked_creds": 55})

        self.assertEqual(restored.alias, "OldTimer")
        self.assertEqual(restored.run_history, [])
        self.assertEqual(restored.achievements, [])
        self.assertEqual(restored.daily_best, {})
        self.assertEqual(restored.daily_streak, 0)
        self.assertEqual(restored.best_daily_streak, 0)
        self.assertEqual(restored.last_daily_key, "")
        self.assertEqual(restored.hall_of_fame, [])
        self.assertEqual(restored.faction_standing, {"syndicate": 0, "street": 0})

    def test_career_daily_best_drops_malformed_values(self):
        restored = CareerProfile.from_dict({
            "daily_best": {
                "2026-10-30": 450,
                "2026-10-31": "bad",
                "2026-11-01": 120.9,
                "2026-11-02": float("nan"),
                "2026-11-03": float("inf"),
            },
        })

        self.assertEqual(restored.daily_best, {"2026-10-30": 450, "2026-11-01": 120})

    def test_career_history_drops_malformed_entries_and_keeps_recent(self):
        history = [{"outcome": "victory", "seed": index} for index in range(25)]
        history.insert(3, "not-a-record")

        restored = CareerProfile.from_dict({"run_history": history})

        self.assertEqual(len(restored.run_history), 20)
        self.assertEqual(restored.run_history[-1]["seed"], 24)
        self.assertTrue(all(isinstance(entry, dict) for entry in restored.run_history))

    def test_apply_career_profile(self):
        deck = CyberDeck()
        profile = CareerProfile(
            banked_creds=600,
            purchased_upgrades=["overclock_cpu", "expand_ram", "ice_dampener", "logic_bomb"],
        )
        apply_career_profile(deck, profile)
        self.assertEqual(deck.cryptocreds, 600)
        self.assertEqual(deck.overclock_level, 1)
        self.assertEqual(deck.max_cpu, 12)
        self.assertEqual(deck.ram_boost_level, 1)
        self.assertEqual(deck.max_ram, 96)
        self.assertEqual(deck.ice_dampener_level, 1)
        self.assertIn("logic_bomb", deck.exploits)

    def test_firewall_and_antivirus_models(self):
        rule = FirewallRule(rule_id="r1", port=80, action="BLOCK", bypassed=False)
        fw = HostFirewall(policy=FirewallPolicy.FILTER_PORTS, rules=[rule])
        self.assertTrue(fw.is_port_blocked(80))
        self.assertFalse(fw.is_port_blocked(22))

        # Test bypass
        rule.bypassed = True
        self.assertFalse(fw.is_port_blocked(80))

        # Test HostFirewall roundtrip
        fw_dict = fw.to_dict()
        fw_restored = HostFirewall.from_dict(fw_dict)
        self.assertEqual(fw_restored.policy, FirewallPolicy.FILTER_PORTS)
        self.assertEqual(len(fw_restored.rules), 1)
        self.assertEqual(fw_restored.rules[0].port, 80)
        self.assertTrue(fw_restored.rules[0].bypassed)

        # Test HostAntivirus roundtrip
        av = HostAntivirus(name="AegisShield", version="v2.1", alert_level=35, heuristic_sensitivity=4)
        av_dict = av.to_dict()
        av_restored = HostAntivirus.from_dict(av_dict)
        self.assertEqual(av_restored.name, "AegisShield")
        self.assertEqual(av_restored.alert_level, 35)
        self.assertEqual(av_restored.heuristic_sensitivity, 4)

    def test_exploit_payload_and_employee_models(self):
        exp = ExploitPayload(
            cve_id="CVE-2024-38812",
            name="SSH Heap Overflow",
            target_service="ssh",
            required_ram_mb=32,
            stealth_rating=4,
        )
        exp_dict = exp.to_dict()
        exp_restored = ExploitPayload.from_dict(exp_dict)
        self.assertEqual(exp_restored.cve_id, "CVE-2024-38812")
        self.assertEqual(exp_restored.target_service, "ssh")
        self.assertEqual(exp_restored.stealth_rating, 4)

        emp = EmployeeProfile(
            name="Sarah Connor",
            role="DevOps Lead",
            email="sconnor@cyber.local",
            awareness_level=SecurityAwarenessLevel.PARANOID,
        )
        emp_dict = emp.to_dict()
        emp_restored = EmployeeProfile.from_dict(emp_dict)
        self.assertEqual(emp_restored.name, "Sarah Connor")
        self.assertEqual(emp_restored.awareness_level, SecurityAwarenessLevel.PARANOID)
        self.assertFalse(emp_restored.compromised)

    def test_node_with_cyber_warfare_components(self):
        fw = HostFirewall(rules=[FirewallRule(rule_id="r1", port=21, action="BLOCK")])
        av = HostAntivirus(name="SentinelCore", alert_level=10)
        emp = EmployeeProfile(name="Bob Smith", role="Helpdesk", email="bob@corp.local")
        node = Node(
            node_id="n_corp",
            name="Corp Intranet",
            node_type=NodeType.DATA_VAULT,
            security_level=3,
            firewall=fw,
            antivirus=av,
            employees=[emp],
        )
        data = node.to_dict()
        restored = Node.from_dict(data)
        self.assertIsNotNone(restored.firewall)
        self.assertTrue(restored.firewall.is_port_blocked(21))
        self.assertIsNotNone(restored.antivirus)
        self.assertEqual(restored.antivirus.name, "SentinelCore")
        self.assertEqual(len(restored.employees), 1)
        self.assertEqual(restored.employees[0].name, "Bob Smith")

    def test_known_cves_deck_and_catalog(self):
        deck = CyberDeck()
        self.assertIn("CVE-2025-9901", deck.known_cves)
        self.assertIn("CVE-2022-0778", deck.known_cves)
        self.assertEqual(len(deck.known_cves), 8)

        data = deck.to_dict()
        restored = CyberDeck.from_dict(data)
        self.assertEqual(restored.known_cves, deck.known_cves)

    def test_known_cves_backfill_matches_default(self):
        self.assertEqual(CyberDeck.from_dict({}).known_cves, CyberDeck().known_cves)


if __name__ == "__main__":
    unittest.main()

