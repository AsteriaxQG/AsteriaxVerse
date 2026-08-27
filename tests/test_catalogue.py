from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from core.constants import APP_UPDATE_MANIFEST_URL, APP_VERSION, DISCORD_URL, TWITCH_URL
from core.database import DataRepository, UserStore, format_price, location_label
from core.updater import version_key


ROOT = Path(__file__).resolve().parents[1]
DATABASE = ROOT / "data" / "asteriax_sc.db"


class CatalogueSnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo = DataRepository(DATABASE)

    def test_sqlite_integrity(self) -> None:
        with sqlite3.connect(DATABASE) as connection:
            self.assertEqual(connection.execute("PRAGMA integrity_check").fetchone()[0], "ok")

    def test_live_version_and_minimum_coverage(self) -> None:
        meta = self.repo.meta()
        counts = self.repo.meta_counts()
        self.assertLessEqual(version_key(meta["app_version"]), version_key(APP_VERSION))
        self.assertEqual(meta["game_version"], "4.10.0")
        self.assertGreaterEqual(counts["purchasable_vehicles"], 184)
        self.assertGreaterEqual(counts["purchasable_items"], 2790)
        self.assertGreaterEqual(counts["categories"], 60)

    def test_every_sale_resolves_to_an_active_location(self) -> None:
        with sqlite3.connect(DATABASE) as connection:
            missing_items = connection.execute(
                """
                SELECT COUNT(*) FROM item_offers o
                LEFT JOIN items i ON i.id = o.item_id
                LEFT JOIN terminals t ON t.id = o.terminal_id
                WHERE i.id IS NULL OR t.id IS NULL OR t.is_available_live <> 1
                """
            ).fetchone()[0]
            missing_vehicles = connection.execute(
                """
                SELECT COUNT(*) FROM vehicle_offers o
                LEFT JOIN vehicles v ON v.id = o.vehicle_id
                LEFT JOIN terminals t ON t.id = o.terminal_id
                WHERE v.id IS NULL OR t.id IS NULL OR t.is_available_live <> 1
                """
            ).fetchone()[0]
        self.assertEqual(missing_items, 0)
        self.assertEqual(missing_vehicles, 0)

    def test_required_item_families_are_present(self) -> None:
        with sqlite3.connect(DATABASE) as connection:
            rows = connection.execute(
                """
                SELECT DISTINCT i.section
                FROM items i JOIN item_offers o ON o.item_id = i.id AND o.price_buy > 0
                """
            ).fetchall()
        sections = {row[0] for row in rows}
        required = {
            "Armor",
            "Undersuits",
            "Personal Weapons",
            "Vehicle Weapons",
            "Systems",
            "Avionics",
            "Utility",
        }
        self.assertTrue(required.issubset(sections))

    def test_ammunition_and_magazines_are_searchable(self) -> None:
        magazines = self.repo.search_items(sections=["Personal Weapons"], search="Magazine")
        self.assertGreaterEqual(len(magazines), 25)
        self.assertTrue(any("P4-AR" in row["name"] for row in magazines))

    def test_all_buyable_vehicles_have_a_price_and_location(self) -> None:
        vehicles = self.repo.search_vehicles()
        self.assertEqual(len(vehicles), self.repo.meta_counts()["purchasable_vehicles"])
        for row in vehicles:
            self.assertGreater(row["price_min"], 0)
            self.assertNotEqual(location_label(row), "Lieu non renseigné")

    def test_alpha_410_vehicle_shop_additions(self) -> None:
        expected = {
            "Aurora Mk II": {904_932, 952_560},
            "Hull B": {7_541_100, 7_938_000},
            "L-22 Alpha Wolf": {4_536_000},
            "Golem Ox": {1_149_120, 1_209_600},
            "UTV": {75_600},
        }
        for name, prices in expected.items():
            with self.subTest(vehicle=name):
                rows = self.repo.search_vehicles(search=name)
                self.assertTrue(any(row["name"] == name for row in rows))
                vehicle = next(row for row in rows if row["name"] == name)
                offers = self.repo.vehicle_offers(int(vehicle["id"]))
                self.assertEqual({int(row["price_buy"]) for row in offers}, prices)
                self.assertTrue(all(location_label(row) != "Lieu non renseigné" for row in offers))

    def test_price_format(self) -> None:
        self.assertEqual(format_price(1290366), "1 290 366 aUEC")
        self.assertEqual(format_price(None), "—")

    def test_global_search_and_shop_inventory(self) -> None:
        self.assertTrue(any(row["kind"] == "vehicle" for row in self.repo.global_search("Cutlass")))
        shops = self.repo.search_terminals(search="CenterMass")
        self.assertGreaterEqual(len(shops), 1)
        inventory = self.repo.terminal_inventory(int(shops[0]["id"]))
        self.assertGreater(len(inventory), 0)
        self.assertTrue({row["kind"] for row in inventory}.issubset({"item", "vehicle"}))

    def test_shopping_plan_has_total_and_route(self) -> None:
        item = self.repo.search_items(search="P4-AR", limit=1)[0]
        vehicle = self.repo.search_vehicles(search="Cutlass Black", limit=1)[0]
        plan = self.repo.shopping_plan(
            [
                {"kind": "item", "entity_id": item["id"], "quantity": 3, "purchased": 0},
                {"kind": "vehicle", "entity_id": vehicle["id"], "quantity": 1, "purchased": 0},
            ]
        )
        self.assertGreater(plan["total"], 0)
        self.assertGreaterEqual(len(plan["groups"]), 1)
        self.assertEqual(len(plan["entries"]), 2)


class UserStoreTests(unittest.TestCase):
    def test_favourites_toggle(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = UserStore(Path(directory) / "user.db")
            self.assertFalse(store.is_favourite("vehicle", 42))
            self.assertTrue(store.toggle("vehicle", 42))
            self.assertTrue(store.is_favourite("vehicle", 42))
            self.assertFalse(store.toggle("vehicle", 42))
            self.assertFalse(store.is_favourite("vehicle", 42))

    def test_planning_state_and_preferences(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = UserStore(Path(directory) / "user.db")
            store.add_to_shopping("item", 12, 2)
            store.add_to_shopping("item", 12, 1)
            self.assertEqual(store.shopping_entries()[0]["quantity"], 3)
            store.toggle_shopping_purchased("item", 12)
            self.assertEqual(store.shopping_entries()[0]["purchased"], 1)
            self.assertTrue(store.add_comparison("vehicle", 7))
            self.assertEqual(store.comparison_ids("vehicle"), [7])
            store.add_recent("item", 12)
            self.assertEqual(store.recent_entries()[0]["entity_id"], 12)
            store.add_to_loadout(7, 12, 2)
            self.assertEqual(store.loadout_entries(7)[0]["quantity"], 2)
            store.set_json_setting("filters:test", {"planet": "ArcCorp"})
            self.assertEqual(store.get_json_setting("filters:test", {})["planet"], "ArcCorp")

    def test_brand_links_version_and_assets(self) -> None:
        self.assertEqual(APP_VERSION, "1.3.2")
        self.assertEqual(
            APP_UPDATE_MANIFEST_URL,
            "https://raw.githubusercontent.com/AsteriaxQG/AsteriaxVerse/main/UPDATE_MANIFEST.json",
        )
        manifest = json.loads((ROOT / "UPDATE_MANIFEST.json").read_text(encoding="utf-8"))
        template = json.loads((ROOT / "UPDATE_MANIFEST.example.json").read_text(encoding="utf-8"))
        self.assertLessEqual(version_key(manifest["version"]), version_key(APP_VERSION))
        self.assertEqual(template["version"], APP_VERSION)
        self.assertTrue(manifest["download_url"].startswith("https://raw.githubusercontent.com/AsteriaxQG/AsteriaxVerse/"))
        self.assertRegex(manifest["sha256"], r"^[0-9a-f]{64}$")
        self.assertGreater(manifest["size"], 0)
        self.assertTrue(DISCORD_URL.startswith("https://discord.com/invite/"))
        self.assertIn("twitch.tv/asteriaxttv", TWITCH_URL)
        self.assertGreater(version_key("1.2.0"), version_key("1.1.9"))
        for name in ("asteriax.ico", "asteriax_mark.png", "asteriax_logo.png", "version_info.txt"):
            self.assertTrue((ROOT / "assets" / name).is_file())

    def test_simplified_navigation(self) -> None:
        source = (ROOT / "ui" / "app.py").read_text(encoding="utf-8")
        nav_start = source.index("        entries = [")
        nav_end = source.index("        ]", nav_start)
        navigation = source[nav_start:nav_end]
        for page in ("all_items", "shopping", "loadouts", "favorites"):
            self.assertNotIn(f'(\"{page}\",', navigation)
        self.assertNotIn('text="Vérifier les mises à jour"', source)

    def test_only_the_visible_page_is_mapped(self) -> None:
        source = (ROOT / "ui" / "app.py").read_text(encoding="utf-8")
        self.assertIn("self._page_factories", source)
        self.assertIn("previous.grid_remove()", source)
        self.assertIn("page = self._get_page(name)", source)


if __name__ == "__main__":
    unittest.main()
