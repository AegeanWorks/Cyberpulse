"""Live arc bonuses + district sweep mechanics (Cyberpulse 0.5.0)."""

import hashlib
import unittest
from unittest.mock import patch

from cyberpulse.arcs import ARC_EPILOGUES, arc_epilogue_lines, arc_status, district_grid, live_bonuses
from cyberpulse.deckos import list_processes
from cyberpulse.engine import GameEngine


def _quiet(engine):
    """Neutralize ambient/rival randomness for deterministic tick assertions."""
    engine.state.rival.status = "inactive"


class ArcMechanicsTest(unittest.TestCase):
    def setUp(self):
        self.engine = GameEngine(seed=1337)
        _quiet(self.engine)

    def test_zero_arc_discounts_counter_rival(self):
        rival = self.engine.state.rival
        rival.status = "active"
        rival.next_move_turn = 10
        self.engine.deck.cpu_cycles = 8
        ok, msg = self.engine.counter_rival()
        self.assertTrue(ok)
        self.assertEqual(self.engine.deck.cpu_cycles, 6)
        self.assertNotIn("ZERO ARC", msg)

        self.engine.deck.cpu_cycles = 8
        self.engine._find_contact("zero").trust = 2
        ok, msg = self.engine.counter_rival()
        self.assertTrue(ok)
        self.assertEqual(self.engine.deck.cpu_cycles, 7)
        self.assertIn("ZERO ARC", msg)

    def test_zero_arc_counter_needs_only_one_cpu(self):
        self.engine.state.rival.status = "active"
        self.engine._find_contact("zero").trust = 2
        self.engine.deck.cpu_cycles = 1
        ok, _ = self.engine.counter_rival()
        self.assertTrue(ok)

    def test_kilo_arc_boosts_daemon_yield(self):
        self.engine.complete_breach("node_proxy_a")
        self.engine.deck.cpu_cycles = 8
        self.assertTrue(self.engine.deploy_daemon("192.168.1.10", "keylogger")[0])
        node = self.engine.nodes["node_proxy_a"]
        if node.antivirus:
            node.antivirus.evaded = True
        base_yield = self.engine.deck.active_daemons[0].yield_per_turn

        before = self.engine.state.unbanked_creds
        self.engine.tick_daemons()
        self.assertEqual(self.engine.state.unbanked_creds - before, base_yield)

        self.engine._find_contact("kilo").trust = 4
        before = self.engine.state.unbanked_creds
        self.engine.tick_daemons()
        self.assertEqual(self.engine.state.unbanked_creds - before,
                         base_yield + max(1, base_yield // 10))

    def test_archivist_arc_deepens_wipe(self):
        self.engine.complete_breach("node_proxy_a")
        self.engine.complete_breach("node_proxy_b")
        self.engine.state.trace_percent = 50
        ok, _ = self.engine.wipe_logs("node_proxy_a")
        self.assertTrue(ok)
        self.assertEqual(self.engine.state.trace_percent, 30)

        self.engine._find_contact("archivist").trust = 4
        self.engine.state.trace_percent = 50
        ok, _ = self.engine.wipe_logs("node_proxy_b")
        self.assertTrue(ok)
        self.assertEqual(self.engine.state.trace_percent, 25)

    def test_mira_arc_cools_grid_on_syndicate_contract(self):
        self.engine.state.trace_percent = 0
        self.engine.state.world.alert_level = 50
        self.assertEqual(self.engine._decay_alert(0), 48)

        self.engine._find_contact("mira").trust = 6
        self.engine.state.world.alert_level = 50
        self.assertEqual(self.engine._decay_alert(0), 47)

    def test_mira_arc_needs_syndicate_contract(self):
        self.engine._find_contact("mira").trust = 6
        self.engine.state.active_contract = None
        self.engine.state.trace_percent = 0
        self.engine.state.world.alert_level = 50
        self.assertEqual(self.engine._decay_alert(0), 48)

    def test_district_sweep_adds_trace_under_black_alert(self):
        self.engine.state.world.alert_level = 80
        self.engine.state.trace_percent = 0
        heavy = [d for d in district_grid(1337, 0, 80) if d["patrol"] == "heavy"]
        with patch("cyberpulse.engine.ambient_event_for", return_value=None):
            msgs = self.engine.tick_world()
        expected = 2 + (1 if len(heavy) >= 2 else 0)
        self.assertEqual(self.engine.state.trace_percent, expected)
        if len(heavy) >= 2:
            self.assertTrue(any("DISTRICT SWEEP" in m for m in msgs))
            self.assertTrue(any("sweep" in item["headline"].lower()
                                for item in self.engine.news_feed(60)))
        else:
            self.assertFalse(any("DISTRICT SWEEP" in m for m in msgs))

    def test_district_grid_matches_hashlib_reference(self):
        ref = int(hashlib.sha256("cyberpulse-district:1337:0:neon_row".encode()).hexdigest()[:8], 16) % 100
        rows = district_grid(1337, 0, 80)
        neon = next(d for d in rows if d["key"] == "neon_row")
        self.assertEqual(neon["load"], min(100, max(5, (ref + 80 // 2 + 0 * 7) % 100)))

    def test_live_bonuses_reflect_trust_and_contract(self):
        self.assertEqual(live_bonuses(self.engine),
                         {"mira_decay": False, "kilo_yield": False, "kilo_overdrive": False,
                          "archivist_wipe": False, "zero_counter": False})
        self.engine._find_contact("mira").trust = 6
        self.engine._find_contact("kilo").trust = 4
        self.engine._find_contact("archivist").trust = 4
        self.engine._find_contact("zero").trust = 2
        live = live_bonuses(self.engine)
        self.assertTrue(all(live.values()))

    def test_arc_epilogues_fire_only_at_stage_three(self):
        self.assertEqual(arc_epilogue_lines(self.engine.state.contacts), [])
        self.engine._find_contact("mira").trust = 3
        self.assertEqual(arc_epilogue_lines(self.engine.state.contacts), [])
        self.engine._find_contact("mira").trust = 6
        self.engine._find_contact("kilo").trust = 6
        lines = arc_epilogue_lines(self.engine.state.contacts)
        self.assertEqual(len(lines), 2)
        self.assertIn(ARC_EPILOGUES["mira"], lines)
        self.assertIn(ARC_EPILOGUES["kilo"], lines)

    def test_run_summary_carries_arc_epilogues(self):
        self.engine.state.is_game_over = True
        self.engine._find_contact("archivist").trust = 6
        summary = self.engine.run_summary()
        self.assertIn(ARC_EPILOGUES["archivist"], summary["epilogue"])

    def test_adjust_trust_announces_stage_crossings(self):
        mira = self.engine._find_contact("mira")
        mira.trust = 1
        line = self.engine._adjust_trust(mira, 1)
        self.assertIsNotNone(line)
        self.assertIn("ARC ADVANCE", line)
        self.assertIn("Reliable Asset", line)
        self.assertEqual(mira.trust, 2)
        self.assertIn(line, self.engine.state.message_log)

    def test_adjust_trust_silent_without_crossing(self):
        mira = self.engine._find_contact("mira")
        mira.trust = 0
        before = len(self.engine.state.message_log)
        self.assertIsNone(self.engine._adjust_trust(mira, 1))
        self.assertEqual(mira.trust, 1)
        self.assertEqual(len(self.engine.state.message_log), before)

    def test_adjust_trust_floors_at_minus_one(self):
        zero = self.engine._find_contact("zero")
        zero.trust = 0
        self.assertIsNone(self.engine._adjust_trust(zero, -1))
        self.assertEqual(zero.trust, -1)
        self.assertIsNone(self.engine._adjust_trust(zero, -5))
        self.assertEqual(zero.trust, -1)

    def test_accept_quest_carries_arc_unlock(self):
        self.engine._find_contact("kilo").trust = 1
        ok, msg = self.engine.accept_quest("q_side_craft")
        self.assertTrue(ok)
        self.assertIn("ARC ADVANCE", msg)
        self.assertEqual(self.engine._find_contact("kilo").trust, 2)

    def test_archivist_arc_opens_extra_offer_slot(self):
        self.assertEqual(self.engine._contract_board_size(), 3)
        self.engine._find_contact("archivist").trust = 2
        self.assertEqual(self.engine._contract_board_size(), 4)
        self.engine.state.rival.status = "inactive"
        self.engine.state.contract_offers = []
        self.engine._refresh_contract_offers()
        self.assertGreaterEqual(len(self.engine.state.contract_offers), 3)
        self.assertLessEqual(len(self.engine.state.contract_offers), 4)

    def test_arc_status_carries_bonus_text(self):
        status = {a["contact_id"]: a for a in arc_status(self.engine.state.contacts)}
        self.assertIn("Next @ trust 2", status["mira"]["bonus"])
        self.engine._find_contact("mira").trust = 2
        status = {a["contact_id"]: a for a in arc_status(self.engine.state.contacts)}
        self.assertIn("rush window", status["mira"]["bonus"])

    def test_talk_names_the_loyalty_arc(self):
        ok, quiet, _ = self.engine.interact_contact("mira", "talk")
        self.assertTrue(ok)
        self.assertNotIn("arc, stage", quiet)
        self.engine._find_contact("mira").trust = 4
        ok, line, report = self.engine.interact_contact("mira", "talk")
        self.assertTrue(ok)
        self.assertIn("Syndicate Ledger arc, stage 2/3", line)
        self.assertIn("Syndicate Ledger arc, stage 2/3", report["dialogue"])

    def test_kilo_arc_discounts_overdrive(self):
        self.engine.deck.cpu_cycles = 8
        ok, msg = self.engine.overdrive()
        self.assertTrue(ok)
        self.assertEqual(self.engine.deck.cpu_cycles, 6)
        self.assertNotIn("KILO ARC", msg)

        self.engine.deck.cpu_cycles = 8
        self.engine._find_contact("kilo").trust = 2
        ok, msg = self.engine.overdrive()
        self.assertTrue(ok)
        self.assertEqual(self.engine.deck.cpu_cycles, 7)
        self.assertIn("KILO ARC", msg)

    def test_overdrive_forecast_reflects_kilo_arc(self):
        fc = self.engine.action_forecast("overdrive")
        self.assertTrue(fc["ok"])
        self.assertEqual(fc["cpu_delta"], -2)
        self.engine._find_contact("kilo").trust = 2
        fc = self.engine.action_forecast("overdrive")
        self.assertTrue(fc["ok"])
        self.assertEqual(fc["cpu_delta"], -1)
        self.assertIn("Kilo arc", fc["notes"])

    def test_contact_channels_carry_arc_stage(self):
        channels = {c["contact_id"]: c for c in self.engine.list_contacts()}
        self.assertEqual(channels["mira"]["arc_title"], "Syndicate Ledger")
        self.assertEqual(channels["mira"]["arc_stage"], 0)
        self.engine._find_contact("mira").trust = 4
        channels = {c["contact_id"]: c for c in self.engine.list_contacts()}
        self.assertEqual(channels["mira"]["arc_stage"], 2)
        self.assertEqual(channels["mira"]["arc_label"], "Fixer's Confidant")

    def test_mira_arc_extends_rush_window(self):
        self.engine.decline_contract()
        self.engine.state.contract_decline_until_turn = 0
        self.engine._find_contact("mira").trust = 2
        offer = self.engine.state.contract_offers[0]
        offer.giver = "mira"
        turns = self.engine.state.turns_elapsed
        ok, msg = self.engine.accept_contract(offer.contract_id)
        self.assertTrue(ok)
        self.assertEqual(offer.rush_turn, turns + max(4, offer.deadline_turns // 2) + 1)
        self.assertIn(f"rush by turn {offer.rush_turn}", msg)

    def test_mira_arc_covers_declines(self):
        self.engine._find_contact("mira").trust = 4
        ok, msg = self.engine.decline_contract()
        self.assertTrue(ok)
        self.assertEqual(self.engine._find_contact("mira").trust, 4)
        self.assertIn("covers the walk-away", msg)

    def test_kilo_arc_adds_street_standing_on_victory(self):
        from cyberpulse.models import CareerProfile
        self.engine.state.is_game_over = True
        self.engine.state.is_victory = True
        plain = CareerProfile()
        self.engine.settle_career(plain)

        engine = GameEngine(seed=1337)
        engine.state.is_game_over = True
        engine.state.is_victory = True
        engine._find_contact("kilo").trust = 6
        boosted = CareerProfile()
        engine.settle_career(boosted)

        self.assertEqual(
            boosted.faction_standing.get("street", 0),
            plain.faction_standing.get("street", 0) + 1,
        )

    def test_zero_arc_forecasts_black_ice(self):
        fc = self.engine.action_forecast("probe", "node_ice_perimeter")
        self.assertTrue(fc["ok"])
        self.assertNotIn("Zero's read", fc["notes"])
        self.engine._find_contact("zero").trust = 4
        fc = self.engine.action_forecast("probe", "node_ice_perimeter")
        self.assertTrue(fc["ok"])
        self.assertIn("Zero's read", fc["notes"])

    def test_zero_arc_extends_choice_epilogue(self):
        self.engine.state.is_game_over = True
        self.engine.state.story_choice = "zero_ally"
        summary = self.engine.run_summary()
        self.assertFalse(any("Equals don't knock" in line for line in summary["epilogue"]))
        self.engine._find_contact("zero").trust = 6
        summary = self.engine.run_summary()
        self.assertTrue(any("Equals don't knock" in line for line in summary["epilogue"]))

    def test_district_for_node_is_stable(self):
        from cyberpulse.arcs import DISTRICTS, district_for_node
        keys = {d["key"] for d in DISTRICTS}
        first = district_for_node(1337, "node_proxy_a")
        self.assertEqual(first, district_for_node(1337, "node_proxy_a"))
        self.assertIn(first["key"], keys)
        for nid in self.engine.nodes:
            self.assertIn(district_for_node(1337, nid)["key"], keys)

    def test_district_summary_partitions_all_hosts(self):
        rows = self.engine.district_summary()["districts"]
        seen = [host for row in rows for host in row.get("hosts", [])]
        self.assertEqual(sorted(seen), sorted(self.engine.nodes.keys()))
        for row in rows:
            self.assertIn("hosts", row)

    def test_breach_in_heavy_district_adds_heat(self):
        engine = GameEngine(seed=1234)
        engine.state.world.alert_level = 80
        engine.state.trace_percent = 10
        self.assertEqual(engine.host_district("node_proxy_a")["patrol"], "heavy")
        ok, msg = engine.complete_breach("node_proxy_a")
        self.assertTrue(ok)
        self.assertEqual(engine.state.trace_percent, 11)
        self.assertIn("DISTRICT HEAT", msg)

    def test_breach_outside_heavy_districts_adds_no_heat(self):
        self.engine.state.trace_percent = 10
        ok, msg = self.engine.complete_breach("node_proxy_a")
        self.assertTrue(ok)
        self.assertEqual(self.engine.state.trace_percent, 10)
        self.assertNotIn("DISTRICT HEAT", msg)

    def test_probe_report_carries_district(self):
        ok, msg, report = self.engine.probe_host("node_gateway")
        self.assertTrue(ok)
        self.assertIn("District:", msg)
        hood = self.engine.host_district("node_gateway")
        self.assertEqual(report["district"], hood["district"])
        self.assertEqual(report["district_patrol"], hood["patrol"])

    def test_hunter_deployment_names_its_district(self):
        from cyberpulse.arcs import DISTRICTS
        self.engine.state.world.alert_level = 80
        self.engine.state.rival.status = "inactive"
        self.engine.advance_turn()
        deploy_msgs = [m for m in self.engine.state.message_log if "NETWATCH HUNTER" in m]
        self.assertTrue(deploy_msgs)
        names = [d["name"] for d in DISTRICTS]
        self.assertTrue(any(any(name in m for name in names) for m in deploy_msgs))

    def test_hunter_clash_names_the_grid(self):
        self.engine.state.world.alert_level = 70
        self.engine.state.rival.status = "inactive"
        self.engine.advance_turn()
        hunter = self.engine.state.world.hunters[0]
        curr_node = self.engine.get_current_node()
        hunter.current_node_id = curr_node.connected_ids[0]
        hunter.status = "hunting"
        self.engine.deck.cpu_cycles = 5
        self.engine.advance_turn()
        clash = [m for m in self.engine.state.message_log if "NETWATCH CLASH" in m]
        self.assertTrue(clash)
        self.assertIn("grid lockdown", clash[-1])
        self.assertIn(self.engine.host_district(curr_node.node_id)["district"], clash[-1])

    def test_deckos_probe_names_hunter_district(self):
        self.engine.state.world.alert_level = 80
        self.engine.state.rival.status = "inactive"
        self.engine.advance_turn()
        procs = list_processes(self.engine)
        probes = [p for p in procs if p["name"] == "netwatch_probe"]
        self.assertTrue(probes)
        self.assertTrue(all("sweeping" in p["desc"] and "grid" in p["desc"] for p in probes))

    def test_offer_district_maps_targets_to_streets(self):
        hood = self.engine.host_district("node_proxy_a")
        tag = self.engine.offer_district("192.168.1.10")
        self.assertEqual(tag["district"], hood["district"])
        self.assertEqual(tag["district_patrol"], hood["patrol"])
        wildcat = self.engine.offer_district("")
        self.assertEqual(wildcat["district"], "WILDCAT GRID")
        self.assertEqual(self.engine.offer_district("9.9.9.9")["district"], "WILDCAT GRID")

    def test_resecure_names_the_district_grid(self):
        from unittest.mock import patch as _patch
        engine = GameEngine(seed=1337)
        engine.state.rival.status = "inactive"
        engine.complete_breach("node_proxy_a")
        engine.state.turns_elapsed = 15
        engine.state.world.alert_level = 90
        engine.state.trace_percent = 10
        with _patch("cyberpulse.engine.ambient_event_for", return_value=None):
            engine.tick_world()
        resec = [m for m in engine.state.message_log if "re-secured" in m]
        self.assertTrue(resec)
        self.assertTrue(any("grid back under corporate control" in m for m in resec))
        self.assertIn(engine.host_district("node_proxy_a")["district"],
                      " ".join(resec))
        wire = [item["headline"] for item in engine.news_feed(60)]
        self.assertIn(
            f"({engine.host_district('node_proxy_a')['district']} grid)",
            " ".join(h for h in wire if "re-secured" in h),
        )

    def test_intel_reveal_names_the_district(self):
        self.engine.deck.threat_intel_count = 1
        hood = self.engine.host_district("node_proxy_b")
        ok, msg = self.engine.spend_threat_intel("reveal", "node_proxy_b")
        self.assertTrue(ok, msg)
        self.assertIn(hood["district"], msg)

    def test_run_summary_tracks_district_coverage(self):
        from cyberpulse.models import NodeStatus

        def coverage(eng):
            return {eng.host_district(nid)["district"] for nid, node in eng.nodes.items()
                    if node.status == NodeStatus.BREACHED}
        expected = coverage(self.engine)
        summary = self.engine.run_summary()
        self.assertEqual(summary["districts_compromised_count"], len(expected))
        self.assertEqual(summary["districts_compromised"], sorted(expected))
        self.engine.complete_breach("node_proxy_a")
        expected = coverage(self.engine)
        summary = self.engine.run_summary()
        self.assertIn(self.engine.host_district("node_proxy_a")["district"],
                      summary["districts_compromised"])
        self.assertEqual(summary["districts_compromised_count"], len(expected))

    def test_ambient_events_name_their_district(self):
        from cyberpulse.world import AmbientEvent
        fixed = self.engine._ambient_district("street_chatter")
        self.assertEqual(fixed, "Neon Row")
        self.assertEqual(self.engine._ambient_district("freelance_wire"), "Dead Archive")
        self.assertEqual(self.engine._ambient_district("corporate_pr"), "Ledger Heights")
        self.assertEqual(self.engine._ambient_district("crackdown"), "Black ICE Ward")
        rows = self.engine.district_summary()["districts"]
        heaviest = max(rows, key=lambda row: row["load"])["name"]
        self.assertEqual(self.engine._ambient_district("grid_brownout"), heaviest)
        self.assertEqual(self.engine._ambient_district("ice_patrol"), heaviest)
        self.assertEqual(self.engine._ambient_district("something_unknown"), "")
        msgs = self.engine._apply_ambient_event(
            AmbientEvent(key="street_chatter", source="StreetFeed",
                         headline="Chrome vendors hawk bootleg ICE burners in the night market.")
        )
        self.assertIn("[Neon Row]", msgs[0])
        wire = [item["headline"] for item in self.engine.news_feed(60)]
        self.assertTrue(any("Neon Row" in h for h in wire))

    def test_reveal_effect_names_the_district(self):
        from cyberpulse.world import AmbientEvent
        event = AmbientEvent(key="test", source="test",
                             headline="test reveal", reveal=True)
        msgs = self.engine._apply_ambient_event(event)
        self.assertTrue(msgs)
        self.assertIn("revealed", msgs[0])
        hood_names = [d for d in (self.engine.host_district(nid)["district"]
                                  for nid in self.engine.nodes)]
        self.assertTrue(any(name in msgs[0] for name in set(hood_names)))

    def test_move_across_districts_announces_the_crossing(self):
        self.engine.complete_breach("node_proxy_a")
        ok, msg = self.engine.move_to("node_proxy_a")
        self.assertTrue(ok)
        self.assertIn("Crossing into Neon Row grid", msg)


if __name__ == "__main__":
    unittest.main()
