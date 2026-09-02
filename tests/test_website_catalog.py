import json
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
        self.assertIn('"active-production":"Production active"', source)
        self.assertIn('"long-term-production":"Production à long terme"', source)
        self.assertIn('"concept":"En concept"', source)
        self.assertIn("Prix en jeu", source)
        self.assertIn("Prix Pledge Store", source)
        self.assertIn("Indisponible actuellement", source)
        self.assertIn("Indisponible · Collector", source)
        self.assertIn("Non vérifié", source)
        self.assertIn("const normalizedName=v=>human(v?.name)||human(v?.name_full)||''", source)
        self.assertNotIn("Meilleur prix", source)
        self.assertNotIn("CURRENT_STATUS_OVERRIDES", source)

    def test_official_pledge_price_and_independent_price_sorts(self):
        api = (ROOT / "functions" / "api" / "ships.js").read_text(encoding="utf-8")
        client = (ROOT / "website" / "shipcatalog.js").read_text(encoding="utf-8")
        filters = (ROOT / "website" / "vehiclefilters.js").read_text(encoding="utf-8")
        enhance = (ROOT / "website" / "enhance.js").read_text(encoding="utf-8")
        html = (ROOT / "website" / "index.html").read_text(encoding="utf-8")
        self.assertIn("nativePrice { amount discounted discountDescription }", api)
        self.assertIn("pledge_price", api)
        self.assertIn("pledge_currency", api)
        self.assertIn("pledge_is_warbond", api)
        self.assertIn("snapshotStore", api)
        self.assertIn("RSI_STORE_SNAPSHOT_UPDATED_AT", api)
        self.assertIn("pledge_price:c.pledge_price", client)
        self.assertIn("pledge_collector:c.pledge_collector===true", client)
        self.assertIn("$ US", client)
        for value in ("auec-asc", "auec-desc", "pledge-asc", "pledge-desc"):
            self.assertIn(f'value="{value}"', html)
            self.assertIn(f"sort==='{value}'", filters)
        self.assertIn("aMissing?1:-1", filters)
        self.assertNotIn("bindSort('#vehicleSort'", enhance)

    def test_pledge_prices_have_an_automatic_official_snapshot(self):
        snapshot = (ROOT / "functions" / "api" / "ships-snapshot.js").read_text(encoding="utf-8")
        updater = (ROOT / "scripts" / "update-rsi-store.mjs").read_text(encoding="utf-8")
        workflow = (ROOT / ".github" / "workflows" / "update-rsi-store.yml").read_text(encoding="utf-8")
        self.assertIn("RSI_STORE_SNAPSHOT_UPDATED_AT", snapshot)
        self.assertIn("RSI_STORE_SNAPSHOT", snapshot)
        self.assertIn("robertsspaceindustries.com", updater)
        self.assertIn("nativePrice", updater)
        self.assertIn("application\\/ld\\+json", updater)
        self.assertIn("historical", updater)
        self.assertIn('cron: "*/10 15-17 * * *"', workflow)
        self.assertIn('cron: "17 */2 * * *"', workflow)
        self.assertIn("group: update-rsi-store", workflow)
        self.assertIn("node scripts/update-rsi-store.mjs", workflow)
        for ship in ("Endeavor", "Arrastra", "Odyssey"):
            self.assertIn(f'"title": "{ship}"', snapshot)
        entries = json.loads(snapshot.split("RSI_STORE_SNAPSHOT=", 1)[1].rsplit(";", 1)[0])
        offers = dict(entries)
        self.assertGreaterEqual(len(offers), 240)
        self.assertEqual(700, offers["odyssey"]["price"])
        self.assertFalse(offers["odyssey"]["available"])
        for key in ("auroramkicl", "auroramkies", "auroramkiln", "auroramkilx", "auroramkimr", "auroramkise"):
            self.assertFalse(offers[key]["available"])
            self.assertTrue(offers[key]["collector"])
            self.assertEqual("historical", offers[key]["price_kind"])
        self.assertTrue(offers["auroramkii"]["available"])
        self.assertFalse(offers["auroramkii"].get("collector", False))

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

    def test_hangar_only_contains_owned_ships_and_wishlist(self):
        html = (ROOT / "website" / "index.html").read_text(encoding="utf-8")
        client = (ROOT / "website" / "shipcatalog.js").read_text(encoding="utf-8")
        app = (ROOT / "website" / "app.js").read_text(encoding="utf-8")
        self.assertIn('data-hangar-level="owned">Mes vaisseaux', html)
        self.assertIn('data-hangar-level="wishlist">Wishlist', html)
        self.assertNotIn('data-hangar-level="items"', html)
        self.assertNotIn("hangarMode==='items'", client)
        self.assertNotIn("favButton('i'", app)
        self.assertIn("data-hangar-owned", client)
        self.assertIn("data-hangar-wish", client)

    def test_production_ships_and_news_order_are_preserved(self):
        ships = (ROOT / "functions" / "api" / "ships.js").read_text(encoding="utf-8")
        news_api = (ROOT / "functions" / "api" / "news.js").read_text(encoding="utf-8")
        news_client = (ROOT / "website" / "news.js").read_text(encoding="utf-8")
        self.assertIn("VERIFIED_PIPELINE_STATUS", ships)
        self.assertIn("active-production", ships)
        self.assertIn("long-term-production", ships)
        self.assertIn("sort((a,b)=>ageMinutes(a.posted)-ageMinutes(b.posted))", news_api)
        self.assertIn("il y a ${amount}", news_client)
        self.assertNotIn("replace(/\\ban?\\b/gi,'1')", news_client)

    def test_ptu_and_eptu_without_a_published_build_are_offline(self):
        status_api = (ROOT / "functions" / "api" / "status.js").read_text(encoding="utf-8")
        status_ui = (ROOT / "website" / "status-ui.js").read_text(encoding="utf-8")
        home = (ROOT / "website" / "home.js").read_text(encoding="utf-8")
        html = (ROOT / "website" / "index.html").read_text(encoding="utf-8")
        self.assertIn("ptuBuilds.length>0?environmentStatus(ptuRaw,true):'Hors ligne'", status_api)
        self.assertIn("eptuBuilds.length>0?environmentStatus('',true):'Hors ligne'", status_api)
        self.assertIn("(prefix==='Ptu'||prefix==='Eptu')?'Hors ligne':'Non publié'", status_ui)
        self.assertIn("(prefix==='Ptu'||prefix==='Eptu')?'Hors ligne':'Inconnu'", home)
        self.assertIn("home.js?v=5", html)
        self.assertIn("status-ui.js?v=4", html)

    def test_current_view_survives_reload(self):
        app = (ROOT / "website" / "app.js").read_text(encoding="utf-8")
        self.assertIn("viewFromHash", app)
        self.assertIn("history.pushState", app)
        self.assertIn("window.addEventListener('popstate'", app)
        self.assertIn("window.addEventListener('hashchange'", app)
        self.assertIn("restoreView();", app)

    def test_ship_catalog_is_paginated_by_24(self):
        client = (ROOT / "website" / "vehiclefilters.js").read_text(encoding="utf-8")
        html = (ROOT / "website" / "index.html").read_text(encoding="utf-8")
        self.assertIn("const PAGE_SIZE=24", client)
        self.assertIn("id='vehiclePagination'", client)
        self.assertIn("list.slice(start,start+PAGE_SIZE)", client)
        self.assertIn("Page précédente", client)
        self.assertIn("Page suivante", client)
        self.assertIn("vehiclefilters.js?v=5", html)

    def test_ship_cards_have_non_overlapping_hangar_actions(self):
        client = (ROOT / "website" / "shipcatalog.js").read_text(encoding="utf-8")
        styles = (ROOT / "website" / "catalog-fixes.css").read_text(encoding="utf-8")
        html = (ROOT / "website" / "index.html").read_text(encoding="utf-8")
        self.assertIn("cardHangarActions", client)
        self.assertIn("data-card-owned", client)
        self.assertIn("data-card-wish", client)
        self.assertIn("e.stopPropagation()", client)
        self.assertIn(".card-hangar-actions", styles)
        self.assertIn("max-width:calc(100% - 116px)", styles)
        self.assertIn("shipcatalog.js?v=13", html)

    def test_desktop_polish_and_catalog_performance(self):
        html = (ROOT / "website" / "index.html").read_text(encoding="utf-8")
        styles = (ROOT / "website" / "desktop-polish.css").read_text(encoding="utf-8")
        performance = (ROOT / "website" / "performance.js").read_text(encoding="utf-8")
        app = (ROOT / "website" / "app.js").read_text(encoding="utf-8")
        catalog = (ROOT / "website" / "shipcatalog.js").read_text(encoding="utf-8")
        self.assertIn("desktop-polish.css?v=2", html)
        self.assertIn("performance.js?v=1", html)
        self.assertIn("app.js?v=14", html)
        self.assertIn("position:static!important", styles)
        self.assertIn("top:auto!important", styles)
        self.assertIn(".detail-head{margin:0 0 26px;padding:0 2px 28px", styles)
        self.assertIn("grid-template-columns:repeat(4,minmax(0,1fr))", styles)
        self.assertIn("scrollbar-gutter:stable", styles)
        self.assertIn("const ITEM_PAGE_SIZE=48", performance)
        self.assertIn("itemPagination", performance)
        self.assertIn("list.slice(start,start+ITEM_PAGE_SIZE)", performance)
        self.assertIn("const debounce=", app)
        self.assertIn("debounce(()=>renderVehicles())", app)
        self.assertIn('decoding="async"', catalog)

    def test_mobile_layout_is_touch_friendly_and_safe_area_aware(self):
        html = (ROOT / "website" / "index.html").read_text(encoding="utf-8")
        styles = (ROOT / "website" / "mobile.css").read_text(encoding="utf-8")
        self.assertIn("viewport-fit=cover", html)
        self.assertIn("mobile.css?v=1", html)
        self.assertEqual(5, html.count("data-mobile-icon="))
        self.assertIn("env(safe-area-inset-bottom)", styles)
        self.assertIn("min-height:46px", styles)
        self.assertIn("height:100dvh", styles)
        self.assertIn("scroll-snap-type:x mandatory", styles)
        self.assertIn("@media (max-width:370px)", styles)
        self.assertIn("orientation:landscape", styles)

    def test_explorer_tab_is_completely_removed(self):
        html = (ROOT / "website" / "index.html").read_text(encoding="utf-8")
        app = (ROOT / "website" / "app.js").read_text(encoding="utf-8")
        self.assertNotIn('data-view="explore"', html)
        self.assertNotIn('id="explore"', html)
        self.assertNotIn("explore.js", html)
        self.assertNotIn("renderDirectories", app)
        self.assertFalse((ROOT / "website" / "explore.js").exists())
        self.assertIn("openManufacturer", app)
        self.assertIn("openLocation", app)


if __name__ == "__main__":
    unittest.main()
