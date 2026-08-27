from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from core.constants import APP_UPDATE_MANIFEST_URL, APP_VERSION, DISCORD_URL, TWITCH_URL
from core.database import DataRepository, UserStore, ensure_performance_indexes, format_price, location_label
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

    def test_repeated_catalogue_search_uses_an_isolated_cache_copy(self) -> None:
        self.repo.clear_cache()
        first = self.repo.search_items(search="laser")
        self.assertGreater(len(first), 0)
        hits_before = self.repo.cache_hits
        original_name = first[0]["name"]
        first[0]["name"] = "mutation locale"
        second = self.repo.search_items(search="laser")
        self.assertEqual(self.repo.cache_hits, hits_before + 1)
        self.assertEqual(second[0]["name"], original_name)

    def test_performance_indexes_can_upgrade_an_existing_database(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "catalogue.db"
            with sqlite3.connect(database) as connection:
                connection.executescript(
                    """
                    CREATE TABLE items(section TEXT, category TEXT, manufacturer TEXT, size INTEGER);
                    CREATE TABLE item_offers(price_buy REAL, item_id INTEGER, terminal_id INTEGER);
                    CREATE TABLE vehicle_offers(price_buy REAL, vehicle_id INTEGER, terminal_id INTEGER);
                    CREATE TABLE terminals(is_available_live INTEGER, star_system TEXT, planet TEXT);
                    """
                )
            ensure_performance_indexes(database)
            with sqlite3.connect(database) as connection:
                names = {
                    row[0]
                    for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type = 'index' AND name LIKE 'idx_%'"
                    )
                }
            self.assertTrue(
                {
                    "idx_items_filters",
                    "idx_item_offers_price",
                    "idx_vehicle_offers_price",
                    "idx_terminals_live_location",
                }.issubset(names)
            )

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

    def test_canonical_vehicle_manufacturers(self) -> None:
        options = self.repo.vehicle_filter_options()["manufacturers"]
        for brand in ("RSI", "MISC", "ARGO", "CNOU", "Grey's Market"):
            self.assertIn(brand, options)
        for legal_name in (
            "Roberts Space Industries",
            "Musashi Industrial and Starflight Concern",
            "Argo Astronautics",
            "Grey&apos;s Market",
        ):
            self.assertNotIn(legal_name, options)

        expected = {
            "Asgard": "Anvil",
            "MOTH": "ARGO",
            "MTC": "Greycat",
            "Prowler Utility": "Esperia",
            "Shiv": "Grey's Market",
            "L-22 Alpha Wolf": "Kruger",
            "Hull B": "MISC",
            "Clipper": "Drake",
            "Hermes": "RSI",
            "Meteor": "RSI",
            "Salvation": "RSI",
        }
        for name, manufacturer in expected.items():
            with self.subTest(vehicle=name):
                row = next(row for row in self.repo.search_vehicles(search=name) if row["name"] == name)
                self.assertEqual(row["manufacturer"], manufacturer)

        rsi_rows = self.repo.search_vehicles(manufacturer="RSI")
        self.assertGreaterEqual(len(rsi_rows), 20)
        self.assertTrue(all(row["manufacturer"] == "RSI" for row in rsi_rows))

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
        self.assertEqual(APP_VERSION, "1.4.3")
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

    def test_fluid_catalogues_and_responsive_mode_are_wired(self) -> None:
        source = (ROOT / "ui" / "app.py").read_text(encoding="utf-8")
        advanced = (ROOT / "ui" / "advanced_pages.py").read_text(encoding="utf-8")
        widgets = (ROOT / "ui" / "widgets.py").read_text(encoding="utf-8")
        self.assertGreaterEqual(source.count("page_size=self.app.catalog_page_size"), 2)
        self.assertIn("page_size=self.app.catalog_page_size", advanced)
        self.assertIn("threading.Thread(target=worker", source)
        self.assertIn("threading.Thread(target=worker", advanced)
        self.assertIn('setting_bool("performance_mode"', source)
        self.assertIn("_apply_responsive_layout", source)
        self.assertIn("def _visible_rows", widgets)

    def test_per_user_windows_installer_is_configured(self) -> None:
        installer = (ROOT / "installer" / "AsteriaxVerse.iss").read_text(encoding="utf-8")
        workflow = (ROOT / ".github" / "workflows" / "build-windows.yml").read_text(encoding="utf-8")
        manifest = json.loads((ROOT / "INSTALLER_MANIFEST.example.json").read_text(encoding="utf-8"))
        self.assertIn("DefaultDirName={localappdata}\\Programs\\Asteriax Verse", installer)
        self.assertIn("PrivilegesRequired=lowest", installer)
        self.assertIn("UninstallDisplayIcon={app}\\{#MyAppExeName}", installer)
        self.assertIn("{autoprograms}\\Asteriax Verse", installer)
        self.assertIn("{autodesktop}\\Asteriax Verse", installer)
        self.assertIn("Inno Setup 6", workflow)
        self.assertIn("AsteriaxVerse-Setup.exe", workflow)
        self.assertEqual(manifest["version"], APP_VERSION)
        self.assertEqual(manifest["install_scope"], "current_user")

    def test_update_check_has_visible_feedback_and_timeout(self) -> None:
        source = (ROOT / "ui" / "advanced_pages.py").read_text(encoding="utf-8")
        app_source = (ROOT / "ui" / "app.py").read_text(encoding="utf-8")
        self.assertIn("self.update_idletasks()", source)
        self.assertIn("_app_check_timed_out", source)
        self.assertIn("Vérification de la version Asteriax Verse", source)
        self.assertIn("Étape 3/4", source)
        self.assertIn("Voir les nouveautés", source)
        self.assertIn("Étape 4/4", app_source)
        self.assertIn("consume_update_result()", app_source)


if __name__ == "__main__":
    unittest.main()
