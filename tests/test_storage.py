"""Unit tests for CyberPulse savegame and career profile persistence."""

import json
import math
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from cyberpulse.engine import GameEngine
from cyberpulse.models import CareerProfile
from cyberpulse.storage import SaveManager


class TestStorage(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.temp_dir, ignore_errors=True)
        self.save_mgr = SaveManager(self.temp_dir)

    def test_save_and_load(self):
        engine = GameEngine(seed=42)
        engine.deck.cryptocreds = 850
        engine.state.trace_percent = 35
        engine.daily_key = "2026-10-30"
        engine.difficulty = "hard"
        engine.daily_modifier = "thin_ice"
        engine.allegiance = "street"
        engine.allegiance_shop_discount = 0.05

        path = self.save_mgr.save(engine)
        self.assertTrue(path.exists())

        loaded = self.save_mgr.load()
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.seed, 42)
        self.assertEqual(loaded.deck.cryptocreds, 850)
        self.assertEqual(loaded.state.trace_percent, 35)
        self.assertEqual(loaded.daily_key, "2026-10-30")
        self.assertEqual(loaded.difficulty, "hard")
        self.assertEqual(loaded.daily_modifier, "thin_ice")
        self.assertEqual(loaded.allegiance, "street")
        self.assertAlmostEqual(loaded.allegiance_shop_discount, 0.05)

    def test_load_nonexistent(self):
        self.assertIsNone(self.save_mgr.load())

    def test_save_preserves_story_quests_and_contacts(self):
        engine = GameEngine(seed=42)
        engine.complete_breach("node_proxy_a")
        engine.state.story_act = 2
        engine.state.story_choice = "zero_ally"
        self.save_mgr.save(engine)

        loaded = self.save_mgr.load()

        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.state.story_act, 2)
        self.assertEqual(loaded.state.story_choice, "zero_ally")
        self.assertEqual(loaded._find_quest("q_gateway").progress, 1)
        self.assertEqual(len(loaded.state.contacts), 4)
        self.assertTrue(loaded.state.story_log)

    def test_save_preserves_tactical_deck_state(self):
        engine = GameEngine(seed=42)
        engine.deck.operating_stance = "stealth"
        engine.deck.cpu_cycles = 8
        engine.complete_breach("node_proxy_a")
        engine.add_proxy_hop("node_proxy_a")
        engine.deck.threat_intel_count = 3
        engine.probe_host("node_proxy_a")

        self.save_mgr.save(engine)
        loaded = self.save_mgr.load()

        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.deck.operating_stance, "stealth")
        self.assertEqual(loaded.deck.proxy_chain, ["node_proxy_a"])
        self.assertEqual(loaded.deck.threat_intel_count, 3)
        self.assertIn("node_proxy_a", loaded.state.probed_nodes)

    def test_save_preserves_rival_state_and_backfills_old_saves(self):
        engine = GameEngine(seed=42)
        engine.state.rival.contracts_stolen = 2
        self.save_mgr.save(engine)

        loaded = self.save_mgr.load()

        self.assertIsNotNone(loaded.state.rival)
        self.assertEqual(loaded.state.rival.contracts_stolen, 2)

        payload = json.loads(self.save_mgr.save_file.read_text(encoding="utf-8"))
        payload["state"].pop("rival", None)
        self.save_mgr.save_file.write_text(json.dumps(payload), encoding="utf-8")
        backfilled = self.save_mgr.load()
        self.assertIsNotNone(backfilled.state.rival)

    def test_save_restores_the_run_start_faction_snapshot(self):
        profile = CareerProfile(faction_standing={"syndicate": 10, "street": 10})
        self.save_mgr.save_career(profile)
        engine = GameEngine(seed=42, career_profile=profile)
        self.save_mgr.save(engine)

        changed = CareerProfile(faction_standing={"syndicate": 20, "street": 20})
        self.save_mgr.save_career(changed)
        loaded = self.save_mgr.load()

        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.faction_standing, {"syndicate": 10, "street": 10})
        self.assertAlmostEqual(loaded.contract_standing_bonus, 0.10)
        self.assertAlmostEqual(loaded.street_standing_discount, 0.10)

    def test_save_preserves_extraction_insurance(self):
        engine = GameEngine(seed=42)
        engine.deck.extraction_insurance = True

        self.save_mgr.save(engine)
        loaded = self.save_mgr.load()

        self.assertIsNotNone(loaded)
        self.assertTrue(loaded.deck.extraction_insurance)

    def test_load_backfills_story_for_old_save(self):
        engine = GameEngine(seed=42)
        engine.state.quests = []
        engine.state.contacts = []
        engine.state.story_log = []
        self.save_mgr.save(engine)

        loaded = self.save_mgr.load()

        self.assertIsNotNone(loaded)
        self.assertEqual(len(loaded.state.quests), 9)
        self.assertEqual(len(loaded.state.contacts), 4)
        self.assertTrue(loaded.state.story_log)
        self.assertEqual(loaded.state.story_choice, "")
        ids = {q.quest_id for q in loaded.state.quests}
        self.assertIn("q_arc_cold_wallet", ids)
        self.assertIn("q_arc_dead_letter", ids)

    def test_career_save_and_load(self):
        profile = CareerProfile(
            alias="CrashOverride",
            banked_creds=450,
            lifetime_creds=1250,
            successful_runs=4,
            current_streak=2,
            best_combo=6,
            purchased_upgrades=["overclock_cpu"],
        )
        path = self.save_mgr.save_career(profile)
        self.assertTrue(path.exists())

        restored = self.save_mgr.load_career()
        self.assertEqual(restored.alias, "CrashOverride")
        self.assertEqual(restored.banked_creds, 450)
        self.assertEqual(restored.successful_runs, 4)
        self.assertEqual(restored.current_streak, 2)
        self.assertEqual(restored.best_combo, 6)
        self.assertIn("overclock_cpu", restored.purchased_upgrades)

    def test_corrupt_primary_does_not_overwrite_a_good_backup(self):
        engine = GameEngine(seed=77)
        engine.deck.cryptocreds = 500
        self.save_mgr.save(engine)
        engine.deck.cryptocreds = 600
        self.save_mgr.save(engine)

        self.save_mgr.save_file.write_text("{ corrupt primary", encoding="utf-8")
        engine.deck.cryptocreds = 700
        self.assertTrue(self.save_mgr.save(engine))

        backup = self.save_mgr.save_file.with_suffix(".bak")
        payload = json.loads(backup.read_text(encoding="utf-8"))
        self.assertEqual(payload["deck"]["cryptocreds"], 500)

        self.save_mgr.save_file.write_text("{ corrupt again", encoding="utf-8")
        recovered = self.save_mgr.load()
        self.assertIsNotNone(recovered)
        self.assertEqual(recovered.deck.cryptocreds, 500)

    def test_list_saves_falls_back_when_timestamp_is_not_finite(self):
        engine = GameEngine(seed=78)
        self.save_mgr.save(engine)
        payload = json.loads(self.save_mgr.save_file.read_text(encoding="utf-8"))
        payload["meta"]["saved_at"] = float("nan")
        self.save_mgr.save_file.write_text(json.dumps(payload), encoding="utf-8")

        saves = self.save_mgr.list_saves()

        self.assertEqual(len(saves), 1)
        self.assertTrue(math.isfinite(saves[0]["saved_at"]))
        self.assertGreater(saves[0]["saved_at"], 0)

    def test_career_run_history_round_trips(self):
        profile = CareerProfile(alias="Archivist", achievements=["veteran", "ghost_protocol"])
        profile.run_history.append({
            "outcome": "jackout",
            "seed": 1337,
            "turns": 12,
            "creds": 420,
            "best_combo": 3,
            "finished_at": 100.0,
        })

        self.save_mgr.save_career(profile)
        restored = self.save_mgr.load_career()

        self.assertEqual(len(restored.run_history), 1)
        self.assertEqual(restored.run_history[0]["outcome"], "jackout")
        self.assertEqual(restored.run_history[0]["creds"], 420)
        self.assertEqual(restored.achievements, ["veteran", "ghost_protocol"])

    def test_backup_and_delete_career_preserve_a_recovery_copy(self):
        profile = CareerProfile(alias="BackupMe", banked_creds=777)
        self.save_mgr.save_career(profile)

        backup = self.save_mgr.backup_career()

        self.assertIsNotNone(backup)
        self.assertTrue(backup.exists())
        payload = json.loads(backup.read_text(encoding="utf-8"))
        self.assertEqual(payload["alias"], "BackupMe")
        self.assertEqual(payload["banked_creds"], 777)

        self.save_mgr.delete_career()

        self.assertEqual(self.save_mgr.load_career().alias, "ZeroCool")
        self.assertTrue(backup.exists())

    def test_delete_all_saves_removes_every_slot(self):
        engine = GameEngine(seed=42)
        self.save_mgr.save(engine, 1)
        self.save_mgr.save(engine, 2)
        self.save_mgr.autosave(engine)

        self.save_mgr.delete_all_saves()

        self.assertFalse(self.save_mgr.has_save())
        for key in ("1", "2", "auto"):
            self.assertFalse(self.save_mgr.slot_path(key).exists())

    def test_career_faction_standing_round_trips(self):
        profile = CareerProfile(alias="Broker", faction_standing={"syndicate": 14, "street": 7})

        self.save_mgr.save_career(profile)
        restored = self.save_mgr.load_career()

        self.assertEqual(restored.faction_standing, {"syndicate": 14, "street": 7})

    def test_career_hall_of_fame_round_trips(self):
        profile = CareerProfile(alias="Champion", hall_of_fame=[
            {"run_id": "run-1", "score": 1250, "outcome": "victory", "seed": 1337},
            {"run_id": "run-2", "score": 800, "outcome": "jackout", "seed": 42},
        ])

        self.save_mgr.save_career(profile)
        restored = self.save_mgr.load_career()

        self.assertEqual(len(restored.hall_of_fame), 2)
        self.assertEqual(restored.hall_of_fame[0]["score"], 1250)
        self.assertEqual(restored.hall_of_fame[0]["run_id"], "run-1")

    def test_career_default_fallback(self):
        fallback = self.save_mgr.load_career()
        self.assertEqual(fallback.alias, "ZeroCool")
        self.assertEqual(fallback.successful_runs, 0)
        self.assertEqual(fallback.best_combo, 0)

    def test_old_career_payload_uses_best_combo_default(self):
        profile = CareerProfile.from_dict({"alias": "OldTimer", "banked_creds": 55})
        self.assertEqual(profile.alias, "OldTimer")
        self.assertEqual(profile.best_combo, 0)

    def test_load_corrupted_save_with_backup_recovery(self):
        engine = GameEngine(seed=77)
        engine.deck.cryptocreds = 999
        self.save_mgr.save(engine)
        self.save_mgr.save(engine)  # Second save ensures .bak exists

        # Corrupt primary save file
        with open(self.save_mgr.save_file, "w", encoding="utf-8") as f:
            f.write("{ invalid json corrupted ")

        # Recovery from .bak should restore state and quarantine corrupted file
        recovered = self.save_mgr.load()
        self.assertIsNotNone(recovered)
        self.assertEqual(recovered.deck.cryptocreds, 999)

        # Check quarantine file was created
        quarantine_files = list(self.temp_dir.glob("savegame.json.corrupt_*"))
        self.assertEqual(len(quarantine_files), 1)

    def test_load_corrupted_career_with_backup_recovery(self):
        profile = CareerProfile(alias="Neo", banked_creds=7000)
        self.save_mgr.save_career(profile)

        # Trigger second save to ensure .bak exists
        profile.banked_creds = 7500
        self.save_mgr.save_career(profile)

        # Corrupt primary career file
        with open(self.save_mgr.career_file, "w", encoding="utf-8") as f:
            f.write("<<<not a json>>>")

        recovered = self.save_mgr.load_career()
        self.assertIn(recovered.banked_creds, (7000, 7500))

    def test_delete_save(self):
        engine = GameEngine(seed=101)
        self.save_mgr.save(engine)
        self.assertTrue(self.save_mgr.save_file.exists())
        self.save_mgr.delete_save()
        self.assertFalse(self.save_mgr.save_file.exists())

    def test_rng_state_is_preserved_across_save_and_load(self):
        engine = GameEngine(seed=123)
        engine.state.turns_elapsed = 15
        self.save_mgr.save(engine)

        # The next roll must continue the live sequence, not restart from seed + turn.
        expected_roll = engine.rng.random()
        loaded = self.save_mgr.load()

        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.rng.random(), expected_roll)

    def test_old_save_without_rng_state_keeps_legacy_reseed(self):
        import json
        import random

        engine = GameEngine(seed=123)
        engine.state.turns_elapsed = 15
        self.save_mgr.save(engine)
        payload = json.loads(self.save_mgr.save_file.read_text(encoding="utf-8"))
        payload.pop("rng_state", None)
        self.save_mgr.save_file.write_text(json.dumps(payload), encoding="utf-8")

        loaded = self.save_mgr.load()

        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.rng.random(), random.Random(123 + 15).random())

    def test_save_preserves_pending_puzzle_attempts(self):
        engine = GameEngine(seed=42)
        ok, _, puzzle, _ = engine.get_or_create_puzzle("node_proxy_a")
        self.assertTrue(ok)
        puzzle.tune(0.0)
        self.assertEqual(puzzle.attempts_left, 2)
        self.save_mgr.save(engine)

        loaded = self.save_mgr.load()

        self.assertIsNotNone(loaded)
        restored = loaded.pending_puzzles.get("node_proxy_a")
        self.assertIsNotNone(restored)
        self.assertEqual(restored.attempts_left, 2)
        self.assertEqual(restored.target_freq, puzzle.target_freq)

    def test_save_preserves_contract_offer_board(self):
        engine = GameEngine(seed=42)
        offer_ids = [offer.contract_id for offer in engine.state.contract_offers]
        self.save_mgr.save(engine)

        loaded = self.save_mgr.load()

        self.assertIsNotNone(loaded)
        self.assertEqual(
            [offer.contract_id for offer in loaded.state.contract_offers],
            offer_ids,
        )
        self.assertEqual(
            [offer.deadline_turns for offer in loaded.state.contract_offers],
            [offer.deadline_turns for offer in engine.state.contract_offers],
        )

    def test_old_offer_save_without_contract_sequence_gets_safe_migration(self):
        import json

        engine = GameEngine(seed=42)
        self.save_mgr.save(engine)
        payload = json.loads(self.save_mgr.save_file.read_text(encoding="utf-8"))
        payload["state"].pop("contract_seq", None)
        self.save_mgr.save_file.write_text(json.dumps(payload), encoding="utf-8")

        loaded = self.save_mgr.load()

        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.state.contract_seq, 10000)
        loaded.state.contract_offers = []
        loaded._refresh_contract_offers()
        self.assertTrue(loaded.state.contract_offers)
        self.assertTrue(
            all(int(offer.contract_id.rsplit("_", 1)[1]) > 10000 for offer in loaded.state.contract_offers)
        )

    def test_old_active_contract_save_without_sequence_gets_safe_migration(self):
        import json

        engine = GameEngine(seed=42)
        self.assertIsNotNone(engine.state.active_contract)
        engine.state.contract_offers = []
        self.save_mgr.save(engine)
        payload = json.loads(self.save_mgr.save_file.read_text(encoding="utf-8"))
        payload["state"].pop("contract_seq", None)
        self.save_mgr.save_file.write_text(json.dumps(payload), encoding="utf-8")

        loaded = self.save_mgr.load()

        self.assertIsNotNone(loaded)
        self.assertGreaterEqual(loaded.state.contract_seq, 10000)
        self.assertTrue(
            all(int(offer.contract_id.rsplit("_", 1)[1]) > 10000 for offer in loaded.state.contract_offers)
        )

    def test_contract_sequence_persists_and_prevents_id_collisions(self):
        engine = GameEngine(seed=42)
        old_ids = {offer.contract_id for offer in engine.state.contract_offers}
        seq_before = engine.state.contract_seq
        self.save_mgr.save(engine)

        loaded = self.save_mgr.load()
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.state.contract_seq, seq_before)
        loaded.state.contract_offers = []
        loaded._refresh_contract_offers()
        new_ids = {offer.contract_id for offer in loaded.state.contract_offers}

        self.assertTrue(new_ids)
        self.assertFalse(old_ids & new_ids)

    def test_failed_replace_reports_no_save(self):
        engine = GameEngine(seed=5)

        with (
            mock.patch("cyberpulse.storage.os.replace", side_effect=OSError("locked")),
            mock.patch("cyberpulse.storage.time.sleep"),
        ):
            path = self.save_mgr.save(engine)

        self.assertIsNone(path)
        self.assertFalse(self.save_mgr.save_file.exists())
        self.assertEqual(list(self.temp_dir.glob(".tmp_*")), [])

    def test_slots_are_isolated_and_listed_with_progress(self):
        engine = GameEngine(seed=42)
        engine.deck.cryptocreds = 100
        engine.state.turns_elapsed = 7
        engine.state.trace_percent = 14
        self.save_mgr.save(engine, 1)

        engine.deck.cryptocreds = 250
        engine.state.turns_elapsed = 12
        engine.state.trace_percent = 31
        self.save_mgr.save(engine, 2)

        slot_one = self.save_mgr.load(1)
        slot_two = self.save_mgr.load(2)

        self.assertIsNotNone(slot_one)
        self.assertIsNotNone(slot_two)
        self.assertEqual(slot_one.deck.cryptocreds, 100)
        self.assertEqual(slot_two.deck.cryptocreds, 250)
        self.assertNotEqual(self.save_mgr.slot_path(1), self.save_mgr.slot_path(2))

        saves = {entry["slot"]: entry for entry in self.save_mgr.list_saves()}
        self.assertEqual(set(saves), {"1", "2"})
        self.assertEqual(saves["2"]["label"], "SLOT 2")
        self.assertEqual(saves["2"]["kind"], "manual")
        self.assertEqual(saves["2"]["turns"], 12)
        self.assertEqual(saves["2"]["creds"], 250)
        self.assertEqual(saves["2"]["trace"], 31)

    def test_autosave_writes_once_per_state_change(self):
        engine = GameEngine(seed=7)
        self.save_mgr.mark_autosave_baseline(engine)

        self.assertIsNone(self.save_mgr.autosave(engine))
        self.assertFalse(self.save_mgr.autosave_file.exists())

        engine.state.trace_percent = 12
        first = self.save_mgr.autosave(engine)
        self.assertIsNotNone(first)
        self.assertTrue(self.save_mgr.autosave_file.exists())
        self.assertIsNone(self.save_mgr.autosave(engine))

        engine.state.trace_percent = 20
        self.assertIsNotNone(self.save_mgr.autosave(engine))
        saves = {entry["slot"]: entry for entry in self.save_mgr.list_saves()}
        self.assertEqual(saves["auto"]["kind"], "auto")
        self.assertEqual(saves["auto"]["label"], "AUTOSAVE")
        self.assertEqual(saves["auto"]["trace"], 20)

    def test_autosave_refuses_a_finished_run(self):
        engine = GameEngine(seed=8)
        engine.state.is_victory = True

        self.assertIsNone(self.save_mgr.autosave(engine))
        self.assertFalse(self.save_mgr.autosave_file.exists())

    def test_delete_run_removes_every_checkpoint_of_that_run_only(self):
        first = GameEngine(seed=11)
        self.save_mgr.save(first, 1)
        self.save_mgr.claim_slot(1)
        self.save_mgr.save(first, 2)
        self.save_mgr.claim_slot(2)
        first.state.trace_percent = 9
        self.save_mgr.autosave(first)

        second = GameEngine(seed=12)
        self.save_mgr.save(second, 3)
        self.save_mgr.claim_slot(3)

        self.save_mgr.delete_run(first.run_id)

        self.assertFalse(self.save_mgr.slot_path(1).exists())
        self.assertFalse(self.save_mgr.slot_path(2).exists())
        self.assertFalse(self.save_mgr.autosave_file.exists())
        self.assertTrue(self.save_mgr.slot_path(3).exists())
        self.assertTrue(self.save_mgr.load(3))

    def test_legacy_save_without_run_id_is_still_slot_one(self):
        import json

        engine = GameEngine(seed=13)
        self.save_mgr.save(engine, 1)
        payload = json.loads(self.save_mgr.save_file.read_text(encoding="utf-8"))
        payload.pop("run_id", None)
        payload.pop("meta", None)
        self.save_mgr.save_file.write_text(json.dumps(payload), encoding="utf-8")

        loaded = self.save_mgr.load(1)

        self.assertIsNotNone(loaded)
        saves = self.save_mgr.list_saves()
        self.assertEqual([entry["slot"] for entry in saves], ["1"])
        self.assertTrue(self.save_mgr.has_save())

        self.save_mgr.delete_run(loaded.run_id)
        self.assertFalse(self.save_mgr.has_save(1))

    def test_save_stores_and_lists_a_slot_name(self):
        engine = GameEngine(seed=21)
        engine.state.trace_percent = 12

        self.assertIsNotNone(self.save_mgr.save(engine, 2, name="  Night   Run  "))

        saves = {entry["slot"]: entry for entry in self.save_mgr.list_saves()}
        self.assertEqual(saves["2"]["name"], "Night Run")
        self.assertEqual(saves["2"]["label"], "SLOT 2")
        loaded = self.save_mgr.load(2)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.state.trace_percent, 12)

    def test_save_without_a_name_preserves_the_existing_name(self):
        engine = GameEngine(seed=22)
        self.save_mgr.save(engine, 1, name="Stealth Run")

        self.save_mgr.save(engine, 1)

        saves = {entry["slot"]: entry for entry in self.save_mgr.list_saves()}
        self.assertEqual(saves["1"]["name"], "Stealth Run")

    def test_rename_slot_preserves_checkpoint_and_timestamp(self):
        engine = GameEngine(seed=23)
        engine.state.trace_percent = 44
        self.save_mgr.save(engine, 3, name="Old Label")
        before = {entry["slot"]: entry for entry in self.save_mgr.list_saves()}["3"]

        renamed = self.save_mgr.rename_slot(3, "Vault Run")

        self.assertTrue(renamed)
        after = {entry["slot"]: entry for entry in self.save_mgr.list_saves()}["3"]
        self.assertEqual(after["name"], "Vault Run")
        self.assertEqual(after["saved_at"], before["saved_at"])
        self.assertEqual(after["trace"], 44)
        loaded = self.save_mgr.load(3)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.state.trace_percent, 44)

    def test_rename_legacy_save_keeps_its_display_timestamp(self):
        import json

        engine = GameEngine(seed=27)
        self.save_mgr.save(engine, 1)
        payload = json.loads(self.save_mgr.save_file.read_text(encoding="utf-8"))
        payload.pop("meta", None)
        self.save_mgr.save_file.write_text(json.dumps(payload), encoding="utf-8")
        before = self.save_mgr.list_saves()[0]

        self.assertTrue(self.save_mgr.rename_slot(1, "Legacy Run"))

        after = self.save_mgr.list_saves()[0]
        self.assertEqual(after["name"], "Legacy Run")
        self.assertEqual(after["saved_at"], before["saved_at"])
        self.assertEqual(after["turns"], before["turns"])

    def test_slot_name_is_trimmed_and_capped(self):
        engine = GameEngine(seed=24)
        self.save_mgr.save(engine, 1, name="  " + "x" * 50 + "  ")

        saves = {entry["slot"]: entry for entry in self.save_mgr.list_saves()}
        self.assertEqual(saves["1"]["name"], "x" * 32)

    def test_rename_missing_or_auto_slot_is_refused(self):
        engine = GameEngine(seed=25)
        self.assertFalse(self.save_mgr.rename_slot(2, "Ghost"))
        self.save_mgr.save(engine, "auto")

        self.assertFalse(self.save_mgr.rename_slot("auto", "Auto Label"))

    def test_delete_save_only_removes_the_requested_slot(self):
        engine = GameEngine(seed=26)
        self.save_mgr.save(engine, 1)
        self.save_mgr.save(engine, 2)

        self.save_mgr.delete_save(2)

        self.assertTrue(self.save_mgr.slot_path(1).exists())
        self.assertFalse(self.save_mgr.slot_path(2).exists())
        self.assertIsNotNone(self.save_mgr.load(1))

    def test_invalid_slot_is_rejected(self):
        engine = GameEngine(seed=14)

        with self.assertRaises(ValueError):
            self.save_mgr.save(engine, 9)
        with self.assertRaises(ValueError):
            self.save_mgr.load("nightmare")


if __name__ == "__main__":
    unittest.main()

