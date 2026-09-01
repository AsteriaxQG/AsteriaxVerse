import sqlite3
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class WebsiteCatalogTests(unittest.TestCase):
    def test_requested_concepts_are_present_in_local_fallback(self):
        with sqlite3.connect(ROOT / "data" / "asteriax_sc.db") as connection:
            connection.row_factory = sqlite3.Row
            rows = {
                row["name"]: row
                for row in connection.execute(
                    """
                    SELECT name, is_concept, scu, crew, url_photo
                    FROM vehicles
                    WHERE name IN ('Endeavor', 'Arrastra')
                    """
                )
            }
        self.assertEqual({"Endeavor", "Arrastra"}, set(rows))
        for row in rows.values():
            self.assertEqual(1, row["is_concept"])
            self.assertGreater(row["scu"], 0)
            self.assertTrue(row["crew"])
            self.assertTrue(row["url_photo"])

    def test_official_rsi_ship_matrix_is_the_primary_catalog(self):
        source = (ROOT / "functions" / "api" / "ships.js").read_text(encoding="utf-8")
        self.assertIn("robertsspaceindustries.com/ship-matrix/index", source)
        self.assertIn("robertsspaceindustries.com/graphql", source)
        self.assertIn("AsteriaxPledgeStore", source)
        self.assertIn("store_checked", source)
        self.assertIn("RSI Ship Matrix officielle", source)
        self.assertIn("Star Citizen Wiki API (secours, RSI indisponible)", source)

    def test_concepts_load_without_an_ingame_offer(self):
        source = (ROOT / "website" / "app.js").read_text(encoding="utf-8")
        self.assertIn("FROM vehicles v LEFT JOIN ranked r", source)
        self.assertIn("v.is_concept=1 AND v.url_photo IS NOT NULL", source)

    def test_catalog_merges_aliases_and_preserves_rsi_status(self):
        source = (ROOT / "website" / "shipcatalog.js").read_text(encoding="utf-8")
        self.assertIn("catalogMatchKey", source)
        self.assertIn("starlifter", source)
        self.assertIn('"flight-ready":"Flight Ready"', source)
        self.assertIn("Achat en jeu", source)
        self.assertIn("Boutique RSI", source)
        self.assertIn("Indisponible actuellement", source)
        self.assertIn("Non vérifié", source)
        self.assertNotIn("CURRENT_STATUS_OVERRIDES", source)

    def test_ship_detail_has_safe_image_fallback_and_full_dimensions(self):
        source = (ROOT / "website" / "shipcatalog.js").read_text(encoding="utf-8")
        self.assertIn("catalog_beam", source)
        self.assertIn("catalog_height", source)
        self.assertIn("catalog_mass", source)
        self.assertIn("addEventListener('error'", source)
        self.assertNotIn("this.parentElement.innerHTML='<div", source)
        styles = (ROOT / "website" / "catalog-fixes.css").read_text(encoding="utf-8")
        self.assertIn("object-fit:contain", styles)
        self.assertIn(".modal-close", styles)

    def test_news_has_images_and_real_refresh_control(self):
        html = (ROOT / "website" / "index.html").read_text(encoding="utf-8")
        client = (ROOT / "website" / "news.js").read_text(encoding="utf-8")
        api = (ROOT / "functions" / "api" / "news.js").read_text(encoding="utf-8")
        self.assertIn('id="refreshNews"', html)
        self.assertIn("x.image", client)
        self.assertIn("refresh=1", client)
        self.assertIn("parseImage", api)
        self.assertIn("if(!force)", api)


if __name__ == "__main__":
    unittest.main()
