"""Unit tests for Black Market Shop in CyberPulse."""

import unittest
from cyberpulse.models import CyberDeck
from cyberpulse.shop import BlackMarketShop


class TestShop(unittest.TestCase):
    def setUp(self):
        self.shop = BlackMarketShop()
        self.deck = CyberDeck(cryptocreds=500)

    def test_list_items(self):
        items = self.shop.list_available(self.deck)
        self.assertGreaterEqual(len(items), 4)
        item_ids = [it["item_id"] for it in items]
        self.assertIn("overclock_cpu", item_ids)
        self.assertIn("ice_dampener", item_ids)

    def test_purchase_cpu_overclock(self):
        initial_cpu = self.deck.max_cpu
        ok, msg = self.shop.purchase(self.deck, "overclock_cpu")
        self.assertTrue(ok)
        self.assertEqual(self.deck.max_cpu, initial_cpu + 2)
        self.assertEqual(self.deck.overclock_level, 1)
        self.assertEqual(self.deck.cryptocreds, 350)  # 500 - 150

    def test_purchase_ice_dampener(self):
        ok, msg = self.shop.purchase(self.deck, "ice_dampener")
        self.assertTrue(ok)
        self.assertEqual(self.deck.ice_dampener_level, 1)
        self.assertEqual(self.deck.cryptocreds, 250)  # 500 - 250

    def test_purchase_insufficient_funds(self):
        self.deck.cryptocreds = 50
        ok, msg = self.shop.purchase(self.deck, "overclock_cpu")
        self.assertFalse(ok)
        self.assertIn("Insufficient funds", msg)

    def test_purchase_max_level(self):
        self.deck.cryptocreds = 2000
        # Buy 3 times to hit max level
        self.shop.purchase(self.deck, "overclock_cpu")
        self.shop.purchase(self.deck, "overclock_cpu")
        self.shop.purchase(self.deck, "overclock_cpu")
        self.assertEqual(self.deck.overclock_level, 3)

        # 4th time should fail
        ok, msg = self.shop.purchase(self.deck, "overclock_cpu")
        self.assertFalse(ok)
        self.assertIn("maximum level", msg)

    def test_dead_mans_switch_is_a_one_use_consumable(self):
        items = {item["item_id"]: item for item in self.shop.list_available(self.deck)}
        self.assertIn("dead_mans_switch", items)
        self.assertEqual(items["dead_mans_switch"]["category"], "consumable")

        ok, message = self.shop.purchase(self.deck, "dead_mans_switch")

        self.assertTrue(ok)
        self.assertIn("armed", message.lower())
        self.assertTrue(self.deck.extraction_insurance)
        self.assertEqual(self.deck.cryptocreds, 350)

        again, message = self.shop.purchase(self.deck, "dead_mans_switch")
        self.assertFalse(again)
        self.assertIn("already", message.lower())

    def test_market_markup_raises_prices(self):
        items = self.shop.list_available(self.deck, price_multiplier=1.20)
        overclock = next(it for it in items if it["item_id"] == "overclock_cpu")
        self.assertEqual(overclock["cost"], 180)
        self.assertEqual(overclock["base_cost"], 150)

        ok, msg = self.shop.purchase(self.deck, "overclock_cpu", price_multiplier=1.20)
        self.assertTrue(ok)
        self.assertEqual(self.deck.cryptocreds, 320)

    def test_market_discount_lowers_prices(self):
        items = self.shop.list_available(self.deck, price_multiplier=0.85)
        dampener = next(it for it in items if it["item_id"] == "ice_dampener")
        self.assertEqual(dampener["cost"], 212)

        ok, msg = self.shop.purchase(self.deck, "ice_dampener", price_multiplier=0.85)
        self.assertTrue(ok)
        self.assertEqual(self.deck.cryptocreds, 288)

    def test_invalid_market_multiplier_falls_back_to_base_price(self):
        self.assertEqual(self.shop.price_for(self.shop.catalog["overclock_cpu"], "not-a-number"), 150)
        self.assertEqual(self.shop.price_for(self.shop.catalog["overclock_cpu"], 0), 150)

    def test_explicit_empty_catalog_is_honored(self):
        shop = BlackMarketShop({})
        self.assertEqual(shop.catalog, {})
        self.assertEqual(shop.list_available(self.deck), [])

    def test_none_catalog_falls_back_to_default(self):
        shop = BlackMarketShop(None)
        self.assertGreaterEqual(len(shop.catalog), 4)


if __name__ == "__main__":
    unittest.main()
