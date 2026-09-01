"""Main CustomTkinter interface for Asteriax Verse."""

from __future__ import annotations

import json
import hashlib
import io
import queue
import re
import threading
import tkinter as tk
import urllib.parse
import urllib.request
import urllib.error
import webbrowser
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from tkinter import messagebox
from typing import Any, Callable

import customtkinter as ctk
from PIL import Image

from core.constants import (
    APP_AUTHOR,
    APP_NAME,
    APP_RELEASE_NOTES,
    APP_VERSION,
    CATEGORY_TRANSLATIONS,
    COLORS,
    DISCORD_URL,
    ITEM_SCOPES,
    NEWS_ITEMS,
    RSI_KNOWN_ISSUES_URL,
    RSI_LIVE_PATCH_URL,
    RSI_PATCHES_URL,
    RSI_ROADMAP_URL,
    RSI_STATUS_URL,
    SECTION_TRANSLATIONS,
    UEX_API_DOCS_URL,
    UEX_SITE_URL,
    TWITCH_URL,
    VERIFIED_LIVE_DATE,
    VERIFIED_LIVE_VERSION,
    WIKI_SHIPS_URL,
    translate_category,
    translate_section,
)
from core.database import (
    DataRepository,
    UserStore,
    ensure_performance_indexes,
    format_price,
    format_timestamp,
    location_label,
    price_freshness_label,
)
from core.paths import data_database_path, resource_path, user_data_dir, user_database_path
from core.sync import fetch_json, sync_database
from core.updater import check_app_update as fetch_app_update, consume_update_result
from ui.advanced_pages import (
    ComparePage,
    GlobalSearchDialog,
    LocationsPage,
    SettingsPage,
    UpdatesPage,
)
from ui.widgets import EmptyState, SectionTitle, StatCard, TreeTable, configure_ttk_styles, labelled_combo


def _short_location(row: dict[str, Any]) -> str:
    for key in ("city", "space_station", "outpost", "moon", "planet", "star_system"):
        if row.get(key):
            return str(row[key])
    return "—"


def _safe_json_list(raw: str | None) -> list[str]:
    try:
        parsed = json.loads(raw or "[]")
        return [str(value) for value in parsed] if isinstance(parsed, list) else []
    except (TypeError, ValueError, json.JSONDecodeError):
        return []


_VEHICLE_IMAGE_HOSTS = {
    "assets.uexcorp.space",
    "cdn.uexcorp.space",
    "media.robertsspaceindustries.com",
    "robertsspaceindustries.com",
}
_VEHICLE_IMAGE_LIMIT = 8 * 1024 * 1024


def _load_vehicle_photo(url: str) -> Image.Image | None:
    """Return a validated cached ship image from an approved data host."""

    parsed = urllib.parse.urlparse(str(url or "").strip())
    if parsed.scheme != "https" or (parsed.hostname or "").casefold() not in _VEHICLE_IMAGE_HOSTS:
        return None
    cache_dir = user_data_dir() / "vehicle_images"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / f"{hashlib.sha256(url.encode('utf-8')).hexdigest()}.jpg"
    if cache_path.exists():
        try:
            with Image.open(cache_path) as cached:
                image = cached.convert("RGB")
                image.load()
                return image
        except (OSError, ValueError):
            cache_path.unlink(missing_ok=True)
    request = urllib.request.Request(
        url,
        headers={"User-Agent": f"{APP_NAME}/{APP_VERSION}", "Accept": "image/*"},
    )
    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            final = urllib.parse.urlparse(response.geturl())
            if final.scheme != "https" or (final.hostname or "").casefold() not in _VEHICLE_IMAGE_HOSTS:
                return None
            announced = int(response.headers.get("Content-Length") or 0)
            if announced > _VEHICLE_IMAGE_LIMIT:
                return None
            payload = response.read(_VEHICLE_IMAGE_LIMIT + 1)
        if not payload or len(payload) > _VEHICLE_IMAGE_LIMIT:
            return None
        with Image.open(io.BytesIO(payload)) as downloaded:
            image = downloaded.convert("RGB")
            image.load()
        image.thumbnail((720, 400), Image.Resampling.LANCZOS)
        image.save(cache_path, format="JPEG", quality=86, optimize=True)
        return image
    except (OSError, ValueError, urllib.error.URLError):
        return None


def _responsive_catalogue_split(event: Any, table: Any, detail: Any) -> None:
    """Give the table the full width when a catalogue page becomes narrow."""

    content = event.widget
    compact = int(getattr(event, "width", 0) or 0) < 1020
    if getattr(content, "_asteriax_compact_split", None) == compact:
        return
    content._asteriax_compact_split = compact
    if compact:
        content.grid_columnconfigure(0, weight=1, minsize=0)
        content.grid_columnconfigure(1, weight=0, minsize=0)
        content.grid_rowconfigure(0, weight=3)
        content.grid_rowconfigure(1, weight=2)
        table.grid_configure(row=0, column=0, columnspan=2, padx=0, pady=(0, 10))
        detail.grid_configure(row=1, column=0, columnspan=2)
    else:
        content.grid_columnconfigure(0, weight=5, minsize=620)
        content.grid_columnconfigure(1, weight=2, minsize=300)
        content.grid_rowconfigure(0, weight=1)
        content.grid_rowconfigure(1, weight=0)
        table.grid_configure(row=0, column=0, columnspan=1, padx=(0, 10), pady=0)
        detail.grid_configure(row=0, column=1, columnspan=1)


class BasePage(ctk.CTkFrame):
    title = ""
    subtitle = ""

    def __init__(self, master: Any, app: "AsteriaxApp"):
        super().__init__(master, fg_color="transparent")
        self.app = app

    def on_show(self) -> None:
        pass

    def refresh_data(self) -> None:
        pass


class DashboardPage(BasePage):
    title = "Vue d'ensemble"
    subtitle = "Tout le Verse, dans une base claire et rapide."

    def __init__(self, master: Any, app: "AsteriaxApp"):
        super().__init__(master, app)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color=COLORS["accent_dark"],
        )
        self.scroll.grid(row=0, column=0, sticky="nsew")
        self.scroll.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="stat")
        self._built = False

    def on_show(self) -> None:
        self.refresh_data()

    def refresh_data(self) -> None:
        for child in self.scroll.winfo_children():
            child.destroy()
        self._built = True
        stats = self.app.repo.dashboard_stats()
        meta = self.app.repo.meta()

        hero = ctk.CTkFrame(
            self.scroll,
            fg_color=COLORS["panel"],
            corner_radius=16,
            border_width=1,
            border_color=COLORS["border"],
        )
        hero.grid(row=0, column=0, columnspan=4, pady=(0, 16), sticky="ew")
        hero.grid_columnconfigure(0, weight=1)
        badge = ctk.CTkLabel(
            hero,
            text=f"  DONNÉES LIVE {meta.get('game_version', '—')}  ",
            height=26,
            corner_radius=13,
            fg_color=COLORS["accent_dark"],
            text_color=COLORS["accent"],
            font=("Segoe UI Semibold", 11),
        )
        badge.grid(row=0, column=0, padx=24, pady=(22, 8), sticky="w")
        ctk.CTkLabel(
            hero,
            text="Bienvenue dans Asteriax Verse",
            font=("Segoe UI Semibold", 25),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=1, column=0, padx=24, sticky="ew")
        ctk.CTkLabel(
            hero,
            text=(
                "Trouvez un vaisseau, une arme, une armure ou un composant, puis voyez immédiatement "
                "son meilleur prix et chaque boutique où l'acheter."
            ),
            wraplength=780,
            justify="left",
            font=("Segoe UI", 13),
            text_color=COLORS["muted"],
            anchor="w",
        ).grid(row=2, column=0, padx=24, pady=(7, 22), sticky="ew")
        ctk.CTkButton(
            hero,
            text="Voir les vaisseaux",
            command=lambda: self.app.show_page("ships"),
            width=160,
            height=38,
            corner_radius=9,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color=COLORS["background"],
            font=("Segoe UI Semibold", 12),
        ).grid(row=0, column=1, rowspan=2, padx=(10, 24), pady=22, sticky="e")

        cards = [
            (str(stats.get("vehicles", 0)), "VAISSEAUX & VÉHICULES", "vendus actuellement en jeu", COLORS["accent"]),
            (str(stats.get("items", 0)), "OBJETS ACHETABLES", "armes, armures et composants", COLORS["blue"]),
            (str(stats.get("locations", 0)), "BOUTIQUES ACTIVES", "dans Stanton, Pyro et Nyx", COLORS["warning"]),
            (str(stats.get("categories", 0)), "CATÉGORIES", "couverture de l'inventaire", COLORS["success"]),
        ]
        for column, (value, label, caption, color) in enumerate(cards):
            StatCard(self.scroll, value=value, label=label, caption=caption, color=color).grid(
                row=1, column=column, padx=(0 if column == 0 else 6, 0 if column == 3 else 6), pady=(0, 18), sticky="nsew"
            )

        quick_title = SectionTitle(
            self.scroll,
            "Accès rapide",
            "Les recherches les plus utiles en jeu.",
        )
        quick_title.grid(row=2, column=0, columnspan=4, pady=(0, 10), sticky="ew")
        quick_actions = [
            ("VAISSEAUX", "179 modèles vendus en aUEC", "ships", COLORS["accent"]),
            ("ÉQUIPEMENT DE VAISSEAU", "Composants, canons, missiles", "equipment:ship_gear", COLORS["blue"]),
            ("ÉQUIPEMENT PERSONNEL", "Armures, armes, accessoires", "equipment:personal_gear", COLORS["warning"]),
        ]
        for column, (title, caption, page_name, color) in enumerate(quick_actions):
            panel = ctk.CTkFrame(
                self.scroll,
                fg_color=COLORS["panel"],
                corner_radius=14,
                border_width=1,
                border_color=COLORS["border"],
            )
            panel.grid(row=3, column=column, columnspan=1 if column < 2 else 2, padx=(0 if column == 0 else 6, 0 if column == 2 else 6), pady=(0, 18), sticky="nsew")
            panel.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(
                panel,
                text="●",
                text_color=color,
                font=("Segoe UI", 13),
            ).grid(row=0, column=0, padx=18, pady=(17, 6), sticky="w")
            ctk.CTkLabel(
                panel,
                text=title,
                text_color=COLORS["text"],
                font=("Segoe UI Semibold", 13),
                anchor="w",
            ).grid(row=1, column=0, padx=18, sticky="ew")
            ctk.CTkLabel(
                panel,
                text=caption,
                text_color=COLORS["muted"],
                font=("Segoe UI", 11),
                anchor="w",
            ).grid(row=2, column=0, padx=18, pady=(3, 13), sticky="ew")
            ctk.CTkButton(
                panel,
                text="Explorer  →",
                command=lambda name=page_name: self.app.open_navigation_target(name),
                height=30,
                corner_radius=7,
                fg_color="transparent",
                hover_color=COLORS["accent_dark"],
                border_width=1,
                border_color=COLORS["border"],
                text_color=COLORS["accent"],
                font=("Segoe UI Semibold", 11),
            ).grid(row=3, column=0, padx=18, pady=(0, 17), sticky="ew")

        SectionTitle(
            self.scroll,
            "Actualités LIVE",
            "Les dernières nouveautés importantes · double-cliquez sur une ligne pour ouvrir sa source.",
        ).grid(row=4, column=0, columnspan=4, pady=(0, 10), sticky="ew")
        self._news_urls = {
            str(index): str(item.get("url") or "")
            for index, item in enumerate(NEWS_ITEMS)
        }
        news_table = TreeTable(
            self.scroll,
            [
                ("date", "DATE", 105, "center"),
                ("category", "CATÉGORIE", 135, "center"),
                ("news", "NOUVEAUTÉ", 510, "w"),
                ("source", "SOURCE", 135, "center"),
            ],
            on_double_click=self._open_news,
        )
        news_table.grid(row=5, column=0, columnspan=4, pady=(0, 22), sticky="nsew")
        news_table.configure(height=270)
        news_table.populate(
            (
                str(index),
                (
                    item.get("date") or "—",
                    item.get("category") or "ACTUALITÉ",
                    item.get("title") or "—",
                    item.get("source") or "—",
                ),
                False,
            )
            for index, item in enumerate(NEWS_ITEMS)
        )

        SectionTitle(
            self.scroll,
            "Couverture des données",
            "Nombre d'objets actuellement achetables par grande famille.",
        ).grid(row=6, column=0, columnspan=4, pady=(0, 10), sticky="ew")
        coverage = TreeTable(
            self.scroll,
            [
                ("section", "FAMILLE", 240, "w"),
                ("items", "OBJETS", 100, "center"),
                ("shops", "BOUTIQUES", 110, "center"),
                ("price", "PRIX À PARTIR DE", 170, "e"),
            ],
        )
        coverage.grid(row=7, column=0, columnspan=4, pady=(0, 22), sticky="nsew")
        coverage.configure(height=310)
        coverage.populate(
            (
                str(index),
                (
                    translate_section(row.get("section")),
                    row.get("item_count", 0),
                    row.get("shop_count", 0),
                    format_price(row.get("price_min")),
                ),
                False,
            )
            for index, row in enumerate(self.app.repo.coverage_by_section())
        )

        recent = self.app.repo.resolve_entities(self.app.user_store.recent_entries(8))
        if recent:
            SectionTitle(
                self.scroll,
                "Consultés récemment",
                "Retrouvez instantanément vos dernières recherches.",
            ).grid(row=8, column=0, columnspan=4, pady=(0, 10), sticky="ew")
            recent_table = TreeTable(
                self.scroll,
                [
                    ("name", "NOM", 240, "w"),
                    ("type", "TYPE", 110, "center"),
                    ("price", "MEILLEUR PRIX", 160, "e"),
                    ("location", "LIEU", 260, "w"),
                ],
                on_double_click=self._open_recent,
            )
            recent_table.grid(row=9, column=0, columnspan=4, pady=(0, 22), sticky="ew")
            recent_table.configure(height=245)
            recent_table.populate(
                (
                    f"{row['kind']}:{row['entity_id']}",
                    (
                        row["name"],
                        "Vaisseau" if row["kind"] == "vehicle" else "Objet",
                        format_price(row.get("price_min")),
                        row.get("location") or "—",
                    ),
                    False,
                )
                for row in recent
            )

    def _open_recent(self, iid: str) -> None:
        try:
            kind, raw_id = iid.split(":", 1)
            self.app.open_entity(kind, int(raw_id))
        except (TypeError, ValueError):
            return

    def _open_news(self, iid: str) -> None:
        url = getattr(self, "_news_urls", {}).get(iid, "")
        if url:
            webbrowser.open(url)
        else:
            self.app.show_notice("Cette actualité provient du catalogue Asteriax Verse.")


class CatalogPage(BasePage):
    """Generic item catalogue used for ship gear, personal gear and all items."""

    def __init__(
        self,
        master: Any,
        app: "AsteriaxApp",
        *,
        scope_key: str,
        title: str,
        subtitle: str,
    ):
        super().__init__(master, app)
        self.scope_key = scope_key
        self.title = title
        self.subtitle = subtitle
        self.sections = list(ITEM_SCOPES[scope_key]["sections"])
        self.rows_by_id: dict[int, dict[str, Any]] = {}
        self._loaded = False
        self._debounce_id: str | None = None
        self._query_generation = 0
        self._saved_filter_state: dict[str, Any] = {}

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build_filters()
        self._build_content()

    def _build_filters(self) -> None:
        panel = ctk.CTkFrame(
            self,
            fg_color=COLORS["panel"],
            corner_radius=14,
            border_width=1,
            border_color=COLORS["border"],
        )
        panel.grid(row=0, column=0, pady=(0, 12), sticky="ew")
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_columnconfigure(1, weight=0)

        search_wrap = ctk.CTkFrame(panel, fg_color="transparent")
        search_wrap.grid(row=0, column=0, columnspan=5, padx=14, pady=(13, 9), sticky="ew")
        search_wrap.grid_columnconfigure(0, weight=1)
        self.search_var = tk.StringVar()
        self.search_entry = ctk.CTkEntry(
            search_wrap,
            textvariable=self.search_var,
            placeholder_text="Rechercher un nom, un fabricant ou une catégorie…",
            height=38,
            corner_radius=9,
            border_width=1,
            border_color=COLORS["border"],
            fg_color=COLORS["panel_alt"],
            text_color=COLORS["text"],
            placeholder_text_color=COLORS["muted_2"],
            font=("Segoe UI", 12),
        )
        self.search_entry.grid(row=0, column=0, sticky="ew")
        self.search_entry.bind("<KeyRelease>", self._schedule_refresh)
        self.result_label = ctk.CTkLabel(
            search_wrap,
            text="",
            font=("Segoe UI Semibold", 11),
            text_color=COLORS["muted"],
            width=120,
        )
        self.result_label.grid(row=0, column=1, padx=12)
        ctk.CTkButton(
            search_wrap,
            text="Réinitialiser",
            command=self.reset_filters,
            width=105,
            height=34,
            corner_radius=8,
            fg_color="transparent",
            hover_color=COLORS["panel_hover"],
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["muted"],
            font=("Segoe UI Semibold", 11),
        ).grid(row=0, column=2)

        self.section_var = tk.StringVar(value="Toutes")
        self.category_var = tk.StringVar(value="Toutes")
        self.manufacturer_var = tk.StringVar(value="Tous")
        self.size_var = tk.StringVar(value="Toutes")
        self.system_var = tk.StringVar(value="Tous")
        self.planet_var = tk.StringVar(value="Toutes")
        saved = self.app.user_store.get_json_setting(f"filters:{self.scope_key}", {})
        if isinstance(saved, dict):
            self._saved_filter_state = saved
            self.search_var.set(str(saved.get("search") or ""))
            self.section_var.set(str(saved.get("section") or "Toutes"))
            self.category_var.set(str(saved.get("category") or "Toutes"))
            self.manufacturer_var.set(str(saved.get("manufacturer") or "Tous"))
            self.size_var.set(str(saved.get("size") or "Toutes"))
            self.system_var.set(str(saved.get("system") or "Tous"))
            self.planet_var.set(str(saved.get("planet") or "Toutes"))
        self.filter_row = ctk.CTkFrame(panel, fg_color="transparent")
        self.filter_row.grid(row=1, column=0, columnspan=5, padx=14, pady=(0, 13), sticky="ew")
        for column in range(6):
            self.filter_row.grid_columnconfigure(column, weight=1, uniform="filter")
        self.chip_row = ctk.CTkFrame(panel, fg_color="transparent")
        self.chip_row.grid(row=2, column=0, columnspan=5, padx=14, pady=(0, 11), sticky="ew")

    def _build_filter_combos(self) -> None:
        for child in self.filter_row.winfo_children():
            child.destroy()
        options = self.app.repo.item_filter_options(self.sections)

        self.section_map = {translate_section(value): value for value in options["sections"]}
        self.category_map = {translate_category(value): value for value in options["categories"]}
        section_values = ["Toutes"] + sorted(self.section_map, key=str.casefold)
        category_values = ["Toutes"] + sorted(self.category_map, key=str.casefold)
        configs = [
            ("Famille", self.section_var, section_values),
            ("Catégorie", self.category_var, category_values),
            ("Fabricant", self.manufacturer_var, ["Tous"] + options["manufacturers"]),
            ("Taille", self.size_var, ["Toutes"] + options["sizes"]),
            ("Système", self.system_var, ["Tous"] + options["systems"]),
            ("Planète", self.planet_var, ["Toutes"] + options["planets"]),
        ]
        for column, (label, variable, values) in enumerate(configs):
            frame = labelled_combo(
                self.filter_row,
                label=label,
                variable=variable,
                values=values,
                command=lambda _value: self.refresh_results(),
                width=135,
            )
            frame.grid(row=0, column=column, padx=(0 if column == 0 else 4, 0 if column == 5 else 4), sticky="ew")

    def _build_content(self) -> None:
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew")
        content.grid_rowconfigure(0, weight=1)
        content.grid_columnconfigure(0, weight=5, minsize=620)
        content.grid_columnconfigure(1, weight=2, minsize=300)
        self.table = TreeTable(
            content,
            [
                ("name", "OBJET", 210, "w"),
                ("category", "CATÉGORIE", 135, "w"),
                ("size", "TAILLE", 80, "center"),
                ("price", "MEILLEUR PRIX", 140, "e"),
                ("location", "LIEU", 150, "w"),
            ],
            on_select=self._on_select,
            on_sort=lambda _column, _reverse: self._save_filters(),
            page_size=self.app.catalog_page_size,
        )
        self.table.grid(row=0, column=0, padx=(0, 10), sticky="nsew")
        sort_column = self._saved_filter_state.get("sort_column")
        if isinstance(sort_column, int):
            self.table.restore_sort(sort_column, bool(self._saved_filter_state.get("sort_reverse")))
        self.detail = ctk.CTkScrollableFrame(
            content,
            fg_color=COLORS["panel"],
            corner_radius=14,
            border_width=1,
            border_color=COLORS["border"],
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color=COLORS["accent_dark"],
        )
        self.detail.grid(row=0, column=1, sticky="nsew")
        self.detail.grid_columnconfigure(0, weight=1)
        content.bind(
            "<Configure>",
            lambda event: _responsive_catalogue_split(event, self.table, self.detail),
            add="+",
        )
        self._show_empty_detail()

    def _schedule_refresh(self, _event: Any = None) -> None:
        if self._debounce_id:
            self.after_cancel(self._debounce_id)
        delay = 340 if self.app.performance_mode else 240
        self._debounce_id = self.after(delay, self.refresh_results)

    def reset_filters(self, *, refresh: bool = True) -> None:
        self.search_var.set("")
        self.section_var.set("Toutes")
        self.category_var.set("Toutes")
        self.manufacturer_var.set("Tous")
        self.size_var.set("Toutes")
        self.system_var.set("Tous")
        self.planet_var.set("Toutes")
        if refresh:
            self.refresh_results()

    def _render_filter_chips(self) -> None:
        for child in self.chip_row.winfo_children():
            child.destroy()
        configs = [
            ("Famille", self.section_var, "Toutes"),
            ("Catégorie", self.category_var, "Toutes"),
            ("Fabricant", self.manufacturer_var, "Tous"),
            ("Taille", self.size_var, "Toutes"),
            ("Système", self.system_var, "Tous"),
            ("Planète", self.planet_var, "Toutes"),
        ]
        active = [(label, variable, default) for label, variable, default in configs if variable.get() != default]
        if not active:
            ctk.CTkLabel(
                self.chip_row,
                text="Aucun filtre actif · cliquez sur un titre de colonne pour trier",
                font=("Segoe UI", 10),
                text_color=COLORS["muted_2"],
                anchor="w",
            ).pack(side="left")
            return
        ctk.CTkLabel(
            self.chip_row,
            text="FILTRES ACTIFS",
            font=("Segoe UI Semibold", 10),
            text_color=COLORS["muted_2"],
        ).pack(side="left", padx=(0, 7))
        for label, variable, default in active:
            ctk.CTkButton(
                self.chip_row,
                text=f"{label}: {variable.get()}  ×",
                command=lambda var=variable, value=default: (var.set(value), self.refresh_results()),
                width=0,
                height=25,
                corner_radius=12,
                fg_color=COLORS["accent_dark"],
                hover_color=COLORS["panel_hover"],
                text_color=COLORS["accent"],
                font=("Segoe UI Semibold", 10),
            ).pack(side="left", padx=(0, 5))

    def _save_filters(self) -> None:
        sort_column, sort_reverse = self.table.sort_state() if hasattr(self, "table") else (None, False)
        self.app.user_store.set_json_setting(
            f"filters:{self.scope_key}",
            {
                "search": self.search_var.get(),
                "section": self.section_var.get(),
                "category": self.category_var.get(),
                "manufacturer": self.manufacturer_var.get(),
                "size": self.size_var.get(),
                "system": self.system_var.get(),
                "planet": self.planet_var.get(),
                "sort_column": sort_column,
                "sort_reverse": sort_reverse,
            },
        )

    def on_show(self) -> None:
        if not self._loaded:
            self._build_filter_combos()
            self.refresh_results()
            self._loaded = True

    def refresh_data(self) -> None:
        self._loaded = False
        if self.winfo_ismapped():
            self.on_show()

    def refresh_results(self, select_id: int | None = None) -> None:
        self._debounce_id = None
        section_value = self.section_map.get(self.section_var.get(), "") if hasattr(self, "section_map") else ""
        category_value = self.category_map.get(self.category_var.get(), "") if hasattr(self, "category_map") else ""
        query = {
            "sections": list(self.sections),
            "search": self.search_var.get(),
            "section": section_value,
            "category": category_value,
            "manufacturer": "" if self.manufacturer_var.get() == "Tous" else self.manufacturer_var.get(),
            "size": "" if self.size_var.get() == "Toutes" else self.size_var.get(),
            "star_system": "" if self.system_var.get() == "Tous" else self.system_var.get(),
            "planet": "" if self.planet_var.get() == "Toutes" else self.planet_var.get(),
            "only_purchasable": True,
        }
        self._query_generation += 1
        generation = self._query_generation
        selected_before = select_id
        if selected_before is None:
            current = self.table.selected_id()
            selected_before = int(current) if current.isdigit() else None
        self.result_label.configure(text="Chargement…")
        self._render_filter_chips()
        self._save_filters()
        results: queue.SimpleQueue[tuple[list[dict[str, Any]] | None, Exception | None]] = queue.SimpleQueue()

        def worker() -> None:
            try:
                results.put((self.app.repo.search_items(**query), None))
            except Exception as exc:
                results.put((None, exc))

        def poll() -> None:
            if generation != self._query_generation or not self.winfo_exists():
                return
            try:
                rows, error = results.get_nowait()
            except queue.Empty:
                self.after(35, poll)
                return
            self._apply_item_results(rows or [], error, generation, selected_before)

        threading.Thread(target=worker, name=f"asteriax-items-{self.scope_key}", daemon=True).start()
        self.after(35, poll)

    def _apply_item_results(
        self,
        rows: list[dict[str, Any]],
        error: Exception | None,
        generation: int,
        select_id: int | None,
    ) -> None:
        if generation != self._query_generation:
            return
        if error:
            self.result_label.configure(text="Erreur")
            self.app.show_notice(f"Recherche impossible : {error}", COLORS["danger"])
            return
        self.rows_by_id = {int(row["id"]): row for row in rows}
        self.table.populate(
            (
                str(row["id"]),
                (
                    str(row["name"]),
                    translate_category(row.get("category")),
                    f"S{row['size']}" if row.get("size") else "—",
                    format_price(row.get("price_min")),
                    _short_location(row),
                ),
                False,
            )
            for row in rows
        )
        self.result_label.configure(text=f"{len(rows):,}".replace(",", " ") + " résultats")
        target = select_id if select_id in self.rows_by_id else None
        if target is None and rows and not self.app.performance_mode:
            target = int(rows[0]["id"])
        if target is not None:
            self.table.select(str(target))
        elif rows:
            self._show_empty_detail("Sélectionnez un objet", "Les résultats sont chargés par blocs pour garder l’interface fluide.")
        else:
            self._show_empty_detail("Aucun objet", "Modifiez les filtres pour élargir la recherche.")

    def open_entity(self, entity_id: int) -> None:
        self.reset_filters(refresh=False)
        detail = self.app.repo.item_detail(entity_id)
        if detail:
            self.search_var.set(str(detail.get("name") or ""))
        self.refresh_results(select_id=entity_id)

    def _on_select(self, iid: str) -> None:
        if not iid:
            return
        try:
            item_id = int(iid)
        except ValueError:
            return
        self._show_item_detail(item_id)

    def _clear_detail(self) -> None:
        for child in self.detail.winfo_children():
            child.destroy()

    def _show_empty_detail(self, title: str = "Sélectionnez un objet", message: str = "Ses caractéristiques, ses prix et toutes ses boutiques apparaîtront ici.") -> None:
        self._clear_detail()
        EmptyState(self.detail, title, message).grid(row=0, column=0, sticky="nsew")

    def _show_item_detail(self, item_id: int) -> None:
        detail = self.app.repo.item_detail(item_id)
        if not detail:
            self._show_empty_detail("Objet introuvable", "La base a peut-être été mise à jour.")
            return
        offers = self.app.repo.item_offers(item_id)
        self.app.record_recent("item", item_id)
        self._clear_detail()

        ctk.CTkLabel(
            self.detail,
            text=translate_section(detail.get("section")).upper(),
            font=("Segoe UI Semibold", 11),
            text_color=COLORS["accent"],
            anchor="w",
        ).grid(row=0, column=0, padx=16, pady=(15, 4), sticky="ew")
        ctk.CTkLabel(
            self.detail,
            text=detail.get("name") or "Objet",
            wraplength=310,
            justify="left",
            font=("Segoe UI Semibold", 19),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=1, column=0, padx=16, sticky="ew")
        sub = "  •  ".join(
            value
            for value in (
                translate_category(detail.get("category")),
                str(detail.get("manufacturer") or "Fabricant inconnu"),
                f"Taille {detail.get('size')}" if detail.get("size") else "",
            )
            if value
        )
        ctk.CTkLabel(
            self.detail,
            text=sub,
            wraplength=310,
            justify="left",
            font=("Segoe UI", 11),
            text_color=COLORS["muted"],
            anchor="w",
        ).grid(row=2, column=0, padx=16, pady=(5, 13), sticky="ew")

        actions = ctk.CTkFrame(self.detail, fg_color="transparent")
        actions.grid(row=3, column=0, padx=16, pady=(0, 14), sticky="ew")
        actions.grid_columnconfigure((0, 1), weight=1, uniform="itemaction")
        ctk.CTkButton(
            actions,
            text="⇄ Comparer",
            command=lambda: self.app.add_to_comparison("item", item_id),
            height=32,
            corner_radius=8,
            fg_color=COLORS["panel_alt"],
            hover_color=COLORS["panel_hover"],
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            font=("Segoe UI Semibold", 10),
        ).grid(row=0, column=0, padx=(0, 3), sticky="ew")
        ctk.CTkButton(
            actions,
            text="Copier le nom",
            command=lambda: self.app.copy_to_clipboard(str(detail.get("name") or ""), "Nom copié"),
            height=32,
            corner_radius=8,
            fg_color=COLORS["panel_alt"],
            hover_color=COLORS["panel_hover"],
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            font=("Segoe UI Semibold", 10),
        ).grid(row=0, column=1, padx=(3, 0), sticky="ew")

        if offers:
            best = offers[0]
            price_panel = ctk.CTkFrame(self.detail, fg_color=COLORS["accent_dark"], corner_radius=11)
            price_panel.grid(row=5, column=0, padx=16, pady=(0, 14), sticky="ew")
            price_panel.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(
                price_panel,
                text="MEILLEUR PRIX",
                font=("Segoe UI Semibold", 10),
                text_color=COLORS["accent"],
                anchor="w",
            ).grid(row=0, column=0, padx=13, pady=(10, 0), sticky="ew")
            ctk.CTkLabel(
                price_panel,
                text=format_price(best.get("price_buy")),
                font=("Segoe UI Semibold", 20),
                text_color=COLORS["text"],
                anchor="w",
            ).grid(row=1, column=0, padx=13, pady=(1, 0), sticky="ew")
            ctk.CTkLabel(
                price_panel,
                text=location_label(best),
                wraplength=285,
                justify="left",
                font=("Segoe UI", 11),
                text_color=COLORS["muted"],
                anchor="w",
            ).grid(row=2, column=0, padx=13, pady=(3, 1), sticky="ew")
            freshness = price_freshness_label(best.get("date_modified"))
            ctk.CTkLabel(
                price_panel,
                text=freshness,
                font=("Segoe UI Semibold", 10),
                text_color=COLORS["warning"] if "revérifier" in freshness else COLORS["muted_2"],
                anchor="w",
            ).grid(row=3, column=0, padx=13, pady=(0, 10), sticky="ew")
            ctk.CTkButton(
                price_panel,
                text="Copier",
                command=lambda route=location_label(best): self.app.copy_to_clipboard(route, "Trajet copié"),
                width=70,
                height=27,
                corner_radius=7,
                fg_color="transparent",
                hover_color=COLORS["panel_hover"],
                border_width=1,
                border_color=COLORS["border"],
                text_color=COLORS["accent"],
                font=("Segoe UI Semibold", 10),
            ).grid(row=1, column=1, rowspan=3, padx=(4, 10), pady=(3, 9))

        ctk.CTkLabel(
            self.detail,
            text=f"TOUTES LES BOUTIQUES  ·  {len(offers)}",
            font=("Segoe UI Semibold", 11),
            text_color=COLORS["muted"],
            anchor="w",
        ).grid(row=6, column=0, padx=16, pady=(3, 7), sticky="ew")
        row_index = 7
        for index, offer in enumerate(offers):
            card = ctk.CTkFrame(
                self.detail,
                fg_color=COLORS["panel_alt"],
                corner_radius=9,
                border_width=1 if index == 0 else 0,
                border_color=COLORS["accent"] if index == 0 else COLORS["border"],
            )
            card.grid(row=row_index, column=0, padx=16, pady=(0, 7), sticky="ew")
            card.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(
                card,
                text=format_price(offer.get("price_buy")),
                font=("Segoe UI Semibold", 13),
                text_color=COLORS["text"],
                anchor="w",
            ).grid(row=0, column=0, padx=11, pady=(8, 0), sticky="ew")
            ctk.CTkLabel(
                card,
                text=location_label(offer),
                wraplength=285,
                justify="left",
                font=("Segoe UI", 10),
                text_color=COLORS["muted"],
                anchor="w",
            ).grid(row=1, column=0, padx=11, pady=(2, 1), sticky="ew")
            freshness = price_freshness_label(offer.get("date_modified"))
            ctk.CTkLabel(
                card,
                text=freshness,
                font=("Segoe UI Semibold", 10),
                text_color=COLORS["warning"] if "revérifier" in freshness else COLORS["muted_2"],
                anchor="w",
            ).grid(row=2, column=0, padx=11, pady=(0, 8), sticky="ew")
            row_index += 1
        if detail.get("wiki"):
            ctk.CTkButton(
                self.detail,
                text="Ouvrir la fiche wiki  ↗",
                command=lambda url=detail["wiki"]: webbrowser.open(url),
                height=32,
                corner_radius=8,
                fg_color="transparent",
                hover_color=COLORS["panel_hover"],
                border_width=1,
                border_color=COLORS["border"],
                text_color=COLORS["accent"],
                font=("Segoe UI Semibold", 11),
            ).grid(row=row_index, column=0, padx=16, pady=(8, 16), sticky="ew")


class ShipsPage(BasePage):
    title = "Vaisseaux & véhicules"
    subtitle = "Tous les modèles actuellement vendus en jeu contre des aUEC."
    _photo_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="asteriax-ship-photo")

    def __init__(self, master: Any, app: "AsteriaxApp"):
        super().__init__(master, app)
        self.rows_by_id: dict[int, dict[str, Any]] = {}
        self._loaded = False
        self._debounce_id: str | None = None
        self._query_generation = 0
        self._saved_filter_state: dict[str, Any] = {}
        self._gallery_page = 0
        self._gallery_page_size = 24
        self._gallery_images: dict[int, ctk.CTkImage] = {}
        self._gallery_photo_labels: dict[int, Any] = {}
        self._photo_requested: set[int] = set()
        self._photo_results: queue.SimpleQueue[tuple[int, Image.Image | None]] = queue.SimpleQueue()
        self._photo_polling = False
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build_filters()
        self._build_content()

    def _build_filters(self) -> None:
        panel = ctk.CTkFrame(
            self,
            fg_color=COLORS["panel"],
            corner_radius=14,
            border_width=1,
            border_color=COLORS["border"],
        )
        panel.grid(row=0, column=0, pady=(0, 12), sticky="ew")
        panel.grid_columnconfigure(0, weight=1)
        search = ctk.CTkFrame(panel, fg_color="transparent")
        search.grid(row=0, column=0, padx=14, pady=(13, 9), sticky="ew")
        search.grid_columnconfigure(0, weight=1)
        self.search_var = tk.StringVar()
        entry = ctk.CTkEntry(
            search,
            textvariable=self.search_var,
            placeholder_text="Rechercher un vaisseau, un constructeur ou un rôle…",
            height=38,
            corner_radius=9,
            border_width=1,
            border_color=COLORS["border"],
            fg_color=COLORS["panel_alt"],
            text_color=COLORS["text"],
            placeholder_text_color=COLORS["muted_2"],
            font=("Segoe UI", 12),
        )
        entry.grid(row=0, column=0, sticky="ew")
        entry.bind("<KeyRelease>", self._schedule_refresh)
        self.result_label = ctk.CTkLabel(search, text="", width=120, text_color=COLORS["muted"], font=("Segoe UI Semibold", 11))
        self.result_label.grid(row=0, column=1, padx=12)
        self.view_var = tk.StringVar(value="Tableau")
        self.view_switch = ctk.CTkSegmentedButton(
            search,
            values=["Tableau", "Galerie"],
            variable=self.view_var,
            command=self._set_view,
            width=175,
            height=34,
            corner_radius=9,
            fg_color=COLORS["panel_alt"],
            selected_color=COLORS["accent_dark"],
            selected_hover_color=COLORS["accent_dark"],
            unselected_color=COLORS["panel_alt"],
            unselected_hover_color=COLORS["panel_hover"],
            text_color=COLORS["text"],
            font=("Segoe UI Semibold", 11),
        )
        self.view_switch.grid(row=0, column=2, padx=(0, 8))
        ctk.CTkButton(
            search,
            text="Réinitialiser",
            command=self.reset_filters,
            width=105,
            height=34,
            corner_radius=8,
            fg_color="transparent",
            hover_color=COLORS["panel_hover"],
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["muted"],
            font=("Segoe UI Semibold", 11),
        ).grid(row=0, column=3)
        self.manufacturer_var = tk.StringVar(value="Tous")
        self.type_var = tk.StringVar(value="Tous")
        self.class_var = tk.StringVar(value="Toutes")
        self.system_var = tk.StringVar(value="Tous")
        self.planet_var = tk.StringVar(value="Toutes")
        saved = self.app.user_store.get_json_setting("filters:ships", {})
        if isinstance(saved, dict):
            self._saved_filter_state = saved
            self.search_var.set(str(saved.get("search") or ""))
            self.manufacturer_var.set(str(saved.get("manufacturer") or "Tous"))
            self.type_var.set(str(saved.get("type") or "Tous"))
            self.class_var.set(str(saved.get("class") or "Toutes"))
            self.system_var.set(str(saved.get("system") or "Tous"))
            self.planet_var.set(str(saved.get("planet") or "Toutes"))
            self.view_var.set(str(saved.get("view") or "Tableau"))
        self.filter_row = ctk.CTkFrame(panel, fg_color="transparent")
        self.filter_row.grid(row=1, column=0, padx=14, pady=(0, 13), sticky="ew")
        for column in range(5):
            self.filter_row.grid_columnconfigure(column, weight=1, uniform="shipfilter")
        self.chip_row = ctk.CTkFrame(panel, fg_color="transparent")
        self.chip_row.grid(row=2, column=0, padx=14, pady=(0, 11), sticky="ew")

    def _build_filter_combos(self) -> None:
        for child in self.filter_row.winfo_children():
            child.destroy()
        options = self.app.repo.vehicle_filter_options()
        configs = [
            ("Constructeur", self.manufacturer_var, ["Tous"] + options["manufacturers"]),
            ("Type", self.type_var, ["Tous", "Vaisseaux", "Véhicules terrestres"]),
            ("Classe", self.class_var, ["Toutes"] + options["classes"]),
            ("Système", self.system_var, ["Tous"] + options["systems"]),
            ("Planète", self.planet_var, ["Toutes"] + options["planets"]),
        ]
        for column, (label, variable, values) in enumerate(configs):
            labelled_combo(
                self.filter_row,
                label=label,
                variable=variable,
                values=values,
                command=lambda _value: self.refresh_results(),
                width=185,
            ).grid(row=0, column=column, padx=(0 if column == 0 else 4, 0 if column == 4 else 4), sticky="ew")

    def _build_content(self) -> None:
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew")
        content.grid_rowconfigure(0, weight=1)
        content.grid_columnconfigure(0, weight=5, minsize=620)
        content.grid_columnconfigure(1, weight=2, minsize=300)
        self.primary_view = ctk.CTkFrame(content, fg_color="transparent", corner_radius=0)
        self.primary_view.grid(row=0, column=0, padx=(0, 10), sticky="nsew")
        self.primary_view.grid_rowconfigure(0, weight=1)
        self.primary_view.grid_columnconfigure(0, weight=1)
        self.table = TreeTable(
            self.primary_view,
            [
                ("name", "MODÈLE", 190, "w"),
                ("maker", "CONSTRUCTEUR", 170, "w"),
                ("class", "CLASSE", 140, "center"),
                ("scu", "SCU", 55, "center"),
                ("price", "MEILLEUR PRIX", 140, "e"),
                ("location", "LIEU", 135, "w"),
            ],
            on_select=self._on_select,
            on_sort=lambda _column, _reverse: self._save_filters(),
            page_size=self.app.catalog_page_size,
        )
        self.table.grid(row=0, column=0, sticky="nsew")
        sort_column = self._saved_filter_state.get("sort_column")
        if isinstance(sort_column, int):
            self.table.restore_sort(sort_column, bool(self._saved_filter_state.get("sort_reverse")))
        self.gallery = ctk.CTkScrollableFrame(
            self.primary_view,
            fg_color="transparent",
            corner_radius=0,
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color=COLORS["accent_dark"],
        )
        self.gallery.grid(row=0, column=0, sticky="nsew")
        self.gallery.grid_remove()
        self.gallery.grid_columnconfigure((0, 1, 2), weight=1, uniform="shipcard")
        self.detail = ctk.CTkScrollableFrame(
            content,
            fg_color=COLORS["panel"],
            corner_radius=14,
            border_width=1,
            border_color=COLORS["border"],
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color=COLORS["accent_dark"],
        )
        self.detail.grid(row=0, column=1, sticky="nsew")
        self.detail.grid_columnconfigure(0, weight=1)
        content.bind(
            "<Configure>",
            lambda event: _responsive_catalogue_split(event, self.primary_view, self.detail),
            add="+",
        )
        self._show_empty_detail()
        self._set_view(self.view_var.get())

    def _set_view(self, value: str) -> None:
        mode = "Galerie" if value == "Galerie" else "Tableau"
        self.view_var.set(mode)
        if not hasattr(self, "gallery"):
            return
        if mode == "Galerie":
            self.table.grid_remove()
            self.gallery.grid()
            self._render_gallery(list(self.rows_by_id.values()))
        else:
            self.gallery.grid_remove()
            self.table.grid()
        self._save_filters()

    def _schedule_refresh(self, _event: Any = None) -> None:
        if self._debounce_id:
            self.after_cancel(self._debounce_id)
        delay = 340 if self.app.performance_mode else 240
        self._debounce_id = self.after(delay, self.refresh_results)

    def reset_filters(self, *, refresh: bool = True) -> None:
        self.search_var.set("")
        self.manufacturer_var.set("Tous")
        self.type_var.set("Tous")
        self.class_var.set("Toutes")
        self.system_var.set("Tous")
        self.planet_var.set("Toutes")
        if refresh:
            self.refresh_results()

    def _render_filter_chips(self) -> None:
        for child in self.chip_row.winfo_children():
            child.destroy()
        configs = [
            ("Constructeur", self.manufacturer_var, "Tous"),
            ("Type", self.type_var, "Tous"),
            ("Classe", self.class_var, "Toutes"),
            ("Système", self.system_var, "Tous"),
            ("Planète", self.planet_var, "Toutes"),
        ]
        active = [(label, variable, default) for label, variable, default in configs if variable.get() != default]
        if not active:
            ctk.CTkLabel(
                self.chip_row,
                text="Aucun filtre actif · cliquez sur un titre de colonne pour trier",
                font=("Segoe UI", 10),
                text_color=COLORS["muted_2"],
                anchor="w",
            ).pack(side="left")
            return
        ctk.CTkLabel(self.chip_row, text="FILTRES ACTIFS", font=("Segoe UI Semibold", 10), text_color=COLORS["muted_2"]).pack(side="left", padx=(0, 7))
        for label, variable, default in active:
            ctk.CTkButton(
                self.chip_row,
                text=f"{label}: {variable.get()}  ×",
                command=lambda var=variable, value=default: (var.set(value), self.refresh_results()),
                width=0,
                height=25,
                corner_radius=12,
                fg_color=COLORS["accent_dark"],
                hover_color=COLORS["panel_hover"],
                text_color=COLORS["accent"],
                font=("Segoe UI Semibold", 10),
            ).pack(side="left", padx=(0, 5))

    def _save_filters(self) -> None:
        sort_column, sort_reverse = self.table.sort_state() if hasattr(self, "table") else (None, False)
        self.app.user_store.set_json_setting(
            "filters:ships",
            {
                "search": self.search_var.get(),
                "manufacturer": self.manufacturer_var.get(),
                "type": self.type_var.get(),
                "class": self.class_var.get(),
                "system": self.system_var.get(),
                "planet": self.planet_var.get(),
                "view": self.view_var.get(),
                "sort_column": sort_column,
                "sort_reverse": sort_reverse,
            },
        )

    def on_show(self) -> None:
        if not self._loaded:
            self._build_filter_combos()
            self.refresh_results()
            self._loaded = True

    def refresh_data(self) -> None:
        self._loaded = False
        if self.winfo_ismapped():
            self.on_show()

    def refresh_results(self, select_id: int | None = None) -> None:
        self._debounce_id = None
        query = {
            "search": self.search_var.get(),
            "manufacturer": "" if self.manufacturer_var.get() == "Tous" else self.manufacturer_var.get(),
            "vehicle_type": "" if self.type_var.get() == "Tous" else self.type_var.get(),
            "vehicle_class": "" if self.class_var.get() == "Toutes" else self.class_var.get(),
            "star_system": "" if self.system_var.get() == "Tous" else self.system_var.get(),
            "planet": "" if self.planet_var.get() == "Toutes" else self.planet_var.get(),
        }
        self._query_generation += 1
        generation = self._query_generation
        selected_before = select_id
        if selected_before is None:
            current = self.table.selected_id()
            selected_before = int(current) if current.isdigit() else None
        self.result_label.configure(text="Chargement…")
        self._render_filter_chips()
        self._save_filters()
        results: queue.SimpleQueue[tuple[list[dict[str, Any]] | None, Exception | None]] = queue.SimpleQueue()

        def worker() -> None:
            try:
                results.put((self.app.repo.search_vehicles(**query), None))
            except Exception as exc:
                results.put((None, exc))

        def poll() -> None:
            if generation != self._query_generation or not self.winfo_exists():
                return
            try:
                rows, error = results.get_nowait()
            except queue.Empty:
                self.after(35, poll)
                return
            self._apply_vehicle_results(rows or [], error, generation, selected_before)

        threading.Thread(target=worker, name="asteriax-vehicles", daemon=True).start()
        self.after(35, poll)

    def _apply_vehicle_results(
        self,
        rows: list[dict[str, Any]],
        error: Exception | None,
        generation: int,
        select_id: int | None,
    ) -> None:
        if generation != self._query_generation:
            return
        if error:
            self.result_label.configure(text="Erreur")
            self.app.show_notice(f"Recherche impossible : {error}", COLORS["danger"])
            return
        self.rows_by_id = {int(row["id"]): row for row in rows}
        self.table.populate(
            (
                str(row["id"]),
                (
                    str(row["name"]),
                    row.get("manufacturer") or "—",
                    row.get("vehicle_class") or "—",
                    f"{row.get('scu', 0):g}" if row.get("scu") else "—",
                    format_price(row.get("price_min")),
                    _short_location(row),
                ),
                False,
            )
            for row in rows
        )
        self._gallery_page = 0
        if self.view_var.get() == "Galerie":
            self._render_gallery(rows)
        self.result_label.configure(text=f"{len(rows)} modèles")
        target = select_id if select_id in self.rows_by_id else None
        if target is None and rows and not self.app.performance_mode:
            target = int(rows[0]["id"])
        if target is not None:
            self.table.select(str(target))
        elif rows:
            self._show_empty_detail("Sélectionnez un modèle", "Les résultats sont chargés par blocs pour garder l’interface fluide.")
        else:
            self._show_empty_detail("Aucun modèle", "Modifiez les filtres pour élargir la recherche.")

    def _render_gallery(self, rows: list[dict[str, Any]]) -> None:
        for child in self.gallery.winfo_children():
            child.destroy()
        self._gallery_photo_labels = {}
        if not rows:
            EmptyState(self.gallery, "Aucun modèle", "Modifiez les filtres pour élargir la recherche.").grid(
                row=0, column=0, columnspan=3, pady=30, sticky="ew"
            )
            return
        pages = max(1, (len(rows) + self._gallery_page_size - 1) // self._gallery_page_size)
        self._gallery_page = max(0, min(self._gallery_page, pages - 1))
        start = self._gallery_page * self._gallery_page_size
        visible = rows[start : start + self._gallery_page_size]
        for index, row in enumerate(visible):
            self._build_vehicle_card(index // 3, index % 3, row)
        footer_row = (len(visible) + 2) // 3
        footer = ctk.CTkFrame(
            self.gallery,
            fg_color=COLORS["panel"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"],
        )
        footer.grid(row=footer_row, column=0, columnspan=3, padx=5, pady=(8, 16), sticky="ew")
        footer.grid_columnconfigure(1, weight=1)
        ctk.CTkButton(
            footer,
            text="‹  Précédent",
            command=lambda: self._change_gallery_page(-1),
            state="normal" if self._gallery_page > 0 else "disabled",
            width=120,
            height=34,
            corner_radius=9,
            fg_color=COLORS["panel_alt"],
            hover_color=COLORS["panel_hover"],
            text_color=COLORS["text"],
        ).grid(row=0, column=0, padx=10, pady=10)
        ctk.CTkLabel(
            footer,
            text=f"Page {self._gallery_page + 1} / {pages}  ·  {len(rows)} modèles",
            font=("Segoe UI Semibold", 11),
            text_color=COLORS["muted"],
        ).grid(row=0, column=1)
        ctk.CTkButton(
            footer,
            text="Suivant  ›",
            command=lambda: self._change_gallery_page(1),
            state="normal" if self._gallery_page + 1 < pages else "disabled",
            width=120,
            height=34,
            corner_radius=9,
            fg_color=COLORS["panel_alt"],
            hover_color=COLORS["panel_hover"],
            text_color=COLORS["text"],
        ).grid(row=0, column=2, padx=10, pady=10)

    def _build_vehicle_card(self, grid_row: int, grid_column: int, row: dict[str, Any]) -> None:
        vehicle_id = int(row["id"])
        card = ctk.CTkFrame(
            self.gallery,
            fg_color=COLORS["panel"],
            corner_radius=15,
            border_width=1,
            border_color=COLORS["border"],
        )
        card.grid(row=grid_row, column=grid_column, padx=5, pady=5, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)
        photo = ctk.CTkLabel(
            card,
            text="CHARGEMENT DE L’IMAGE…" if row.get("url_photo") else "PHOTO INDISPONIBLE",
            height=126,
            corner_radius=11,
            fg_color=COLORS["panel_alt"],
            text_color=COLORS["muted_2"],
            font=("Segoe UI Semibold", 10),
        )
        photo.grid(row=0, column=0, padx=9, pady=(9, 8), sticky="ew")
        self._gallery_photo_labels[vehicle_id] = photo
        self._queue_vehicle_photo(vehicle_id, str(row.get("url_photo") or ""))
        ctk.CTkLabel(
            card,
            text=str(row.get("name") or "Vaisseau"),
            wraplength=230,
            justify="left",
            font=("Segoe UI Semibold", 16),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=1, column=0, padx=12, sticky="ew")
        ctk.CTkLabel(
            card,
            text=f"{row.get('manufacturer') or '—'}  ·  {row.get('vehicle_class') or 'Multirôle'}",
            wraplength=230,
            justify="left",
            font=("Segoe UI", 11),
            text_color=COLORS["muted"],
            anchor="w",
        ).grid(row=2, column=0, padx=12, pady=(3, 8), sticky="ew")
        ctk.CTkLabel(
            card,
            text=format_price(row.get("price_min")),
            font=("Segoe UI Semibold", 15),
            text_color=COLORS["accent"],
            anchor="w",
        ).grid(row=3, column=0, padx=12, sticky="ew")
        ctk.CTkLabel(
            card,
            text=_short_location(row),
            wraplength=230,
            justify="left",
            font=("Segoe UI", 10),
            text_color=COLORS["muted_2"],
            anchor="w",
        ).grid(row=4, column=0, padx=12, pady=(1, 9), sticky="ew")
        ctk.CTkButton(
            card,
            text="Voir la fiche",
            command=lambda value=vehicle_id: self._open_gallery_vehicle(value),
            height=34,
            corner_radius=9,
            fg_color=COLORS["accent_dark"],
            hover_color=COLORS["panel_hover"],
            text_color=COLORS["accent"],
            font=("Segoe UI Semibold", 11),
        ).grid(row=5, column=0, padx=12, pady=(0, 11), sticky="ew")

    def _change_gallery_page(self, delta: int) -> None:
        self._gallery_page += delta
        self._render_gallery(list(self.rows_by_id.values()))
        try:
            self.gallery._parent_canvas.yview_moveto(0)
        except (AttributeError, tk.TclError):
            pass

    def _open_gallery_vehicle(self, vehicle_id: int) -> None:
        self.table.select(str(vehicle_id))
        self._show_vehicle_detail(vehicle_id)

    def _queue_vehicle_photo(self, vehicle_id: int, url: str) -> None:
        label = self._gallery_photo_labels.get(vehicle_id)
        cached = self._gallery_images.get(vehicle_id)
        if label is not None and cached is not None:
            label.configure(text="", image=cached)
            return
        if not url or vehicle_id in self._photo_requested:
            return
        self._photo_requested.add(vehicle_id)
        future = self._photo_pool.submit(_load_vehicle_photo, url)
        future.add_done_callback(
            lambda completed, value=vehicle_id: self._store_photo_result(value, completed)
        )
        if not self._photo_polling:
            self._photo_polling = True
            self.after(80, self._poll_vehicle_photos)

    def _store_photo_result(self, vehicle_id: int, completed: Any) -> None:
        try:
            image = completed.result()
        except Exception:
            image = None
        self._photo_results.put((vehicle_id, image))

    def _poll_vehicle_photos(self) -> None:
        try:
            while True:
                vehicle_id, image = self._photo_results.get_nowait()
                self._photo_requested.discard(vehicle_id)
                label = self._gallery_photo_labels.get(vehicle_id)
                if label is None or not label.winfo_exists():
                    continue
                if image is None:
                    label.configure(text="PHOTO INDISPONIBLE")
                    continue
                displayed = ctk.CTkImage(light_image=image, dark_image=image, size=(230, 126))
                self._gallery_images[vehicle_id] = displayed
                while len(self._gallery_images) > 48:
                    self._gallery_images.pop(next(iter(self._gallery_images)))
                label.configure(text="", image=displayed)
        except queue.Empty:
            pass
        if self._photo_requested:
            self.after(80, self._poll_vehicle_photos)
        else:
            self._photo_polling = False

    def open_entity(self, entity_id: int) -> None:
        self.reset_filters(refresh=False)
        detail = self.app.repo.vehicle_detail(entity_id)
        if detail:
            self.search_var.set(str(detail.get("name") or ""))
        self.refresh_results(select_id=entity_id)

    def _on_select(self, iid: str) -> None:
        if iid:
            self._show_vehicle_detail(int(iid))

    def _clear_detail(self) -> None:
        for child in self.detail.winfo_children():
            child.destroy()

    def _show_empty_detail(self, title: str = "Sélectionnez un modèle", message: str = "Ses caractéristiques, son meilleur prix et toutes ses concessions apparaîtront ici.") -> None:
        self._clear_detail()
        EmptyState(self.detail, title, message).grid(row=0, column=0, sticky="nsew")

    def _show_vehicle_detail(self, vehicle_id: int) -> None:
        detail = self.app.repo.vehicle_detail(vehicle_id)
        if not detail:
            self._show_empty_detail("Modèle introuvable", "La base a peut-être été mise à jour.")
            return
        offers = self.app.repo.vehicle_offers(vehicle_id)
        self.app.record_recent("vehicle", vehicle_id)
        self._clear_detail()
        kind = "VÉHICULE TERRESTRE" if detail.get("is_ground_vehicle") else "VAISSEAU"
        ctk.CTkLabel(
            self.detail,
            text=kind,
            font=("Segoe UI Semibold", 11),
            text_color=COLORS["accent"],
            anchor="w",
        ).grid(row=0, column=0, padx=16, pady=(15, 4), sticky="ew")
        ctk.CTkLabel(
            self.detail,
            text=detail.get("name") or "Vaisseau",
            wraplength=310,
            justify="left",
            font=("Segoe UI Semibold", 20),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=1, column=0, padx=16, sticky="ew")
        ctk.CTkLabel(
            self.detail,
            text=(
                f"{detail.get('manufacturer') or 'Constructeur inconnu'}  •  "
                f"{detail.get('vehicle_class') or 'Multirôle'}  •  {detail.get('roles') or 'Polyvalent'}"
            ),
            wraplength=310,
            justify="left",
            font=("Segoe UI", 11),
            text_color=COLORS["muted"],
            anchor="w",
        ).grid(row=2, column=0, padx=16, pady=(5, 12), sticky="ew")

        metrics = ctk.CTkFrame(self.detail, fg_color=COLORS["panel_alt"], corner_radius=10)
        metrics.grid(row=3, column=0, padx=16, pady=(0, 12), sticky="ew")
        metrics.grid_columnconfigure((0, 1, 2), weight=1, uniform="metric")
        values = [
            (f"{detail.get('scu', 0):g}" if detail.get("scu") else "—", "SCU"),
            (detail.get("crew") or "—", "ÉQUIPAGE"),
            (f"{detail.get('length', 0):g} m" if detail.get("length") else "—", "LONGUEUR"),
        ]
        for column, (value, label) in enumerate(values):
            ctk.CTkLabel(metrics, text=value, font=("Segoe UI Semibold", 13), text_color=COLORS["text"]).grid(
                row=0, column=column, padx=7, pady=(9, 0)
            )
            ctk.CTkLabel(metrics, text=label, font=("Segoe UI Semibold", 10), text_color=COLORS["muted_2"]).grid(
                row=1, column=column, padx=7, pady=(0, 9)
            )

        actions = ctk.CTkFrame(self.detail, fg_color="transparent")
        actions.grid(row=4, column=0, padx=16, pady=(0, 13), sticky="ew")
        actions.grid_columnconfigure((0, 1), weight=1, uniform="shipaction")
        action_data = [
            ("⇄ Comparer", lambda: self.app.add_to_comparison("vehicle", vehicle_id), COLORS["panel_alt"], COLORS["text"]),
            ("Copier le nom", lambda: self.app.copy_to_clipboard(str(detail.get("name") or ""), "Nom copié"), COLORS["panel_alt"], COLORS["text"]),
        ]
        for column, (label, command, color, text_color) in enumerate(action_data):
            ctk.CTkButton(
                actions,
                text=label,
                command=command,
                height=32,
                corner_radius=8,
                fg_color=color,
                hover_color=COLORS["panel_hover"],
                border_width=1,
                border_color=COLORS["border"],
                text_color=text_color,
                font=("Segoe UI Semibold", 10),
            ).grid(row=0, column=column, padx=(0 if column == 0 else 3, 0 if column == 1 else 3), sticky="ew")

        if offers:
            best = offers[0]
            price_panel = ctk.CTkFrame(self.detail, fg_color=COLORS["accent_dark"], corner_radius=11)
            price_panel.grid(row=6, column=0, padx=16, pady=(0, 14), sticky="ew")
            price_panel.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(price_panel, text="MEILLEUR PRIX", font=("Segoe UI Semibold", 10), text_color=COLORS["accent"], anchor="w").grid(
                row=0, column=0, padx=13, pady=(10, 0), sticky="ew"
            )
            ctk.CTkLabel(price_panel, text=format_price(best.get("price_buy")), font=("Segoe UI Semibold", 20), text_color=COLORS["text"], anchor="w").grid(
                row=1, column=0, padx=13, pady=(1, 0), sticky="ew"
            )
            ctk.CTkLabel(price_panel, text=location_label(best), wraplength=285, justify="left", font=("Segoe UI", 11), text_color=COLORS["muted"], anchor="w").grid(
                row=2, column=0, padx=13, pady=(3, 1), sticky="ew"
            )
            freshness = price_freshness_label(best.get("date_modified"))
            ctk.CTkLabel(
                price_panel,
                text=freshness,
                font=("Segoe UI Semibold", 10),
                text_color=COLORS["warning"] if "revérifier" in freshness else COLORS["muted_2"],
                anchor="w",
            ).grid(row=3, column=0, padx=13, pady=(0, 10), sticky="ew")
            ctk.CTkButton(
                price_panel,
                text="Copier",
                command=lambda route=location_label(best): self.app.copy_to_clipboard(route, "Trajet copié"),
                width=70,
                height=27,
                corner_radius=7,
                fg_color="transparent",
                hover_color=COLORS["panel_hover"],
                border_width=1,
                border_color=COLORS["border"],
                text_color=COLORS["accent"],
                font=("Segoe UI Semibold", 10),
            ).grid(row=1, column=1, rowspan=3, padx=(4, 10), pady=(3, 9))

        ctk.CTkLabel(
            self.detail,
            text=f"TOUTES LES CONCESSIONS  ·  {len(offers)}",
            font=("Segoe UI Semibold", 11),
            text_color=COLORS["muted"],
            anchor="w",
        ).grid(row=7, column=0, padx=16, pady=(3, 7), sticky="ew")
        row_index = 8
        for index, offer in enumerate(offers):
            card = ctk.CTkFrame(
                self.detail,
                fg_color=COLORS["panel_alt"],
                corner_radius=9,
                border_width=1 if index == 0 else 0,
                border_color=COLORS["accent"] if index == 0 else COLORS["border"],
            )
            card.grid(row=row_index, column=0, padx=16, pady=(0, 7), sticky="ew")
            card.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(card, text=format_price(offer.get("price_buy")), font=("Segoe UI Semibold", 13), text_color=COLORS["text"], anchor="w").grid(
                row=0, column=0, padx=11, pady=(8, 0), sticky="ew"
            )
            ctk.CTkLabel(card, text=location_label(offer), wraplength=285, justify="left", font=("Segoe UI", 10), text_color=COLORS["muted"], anchor="w").grid(
                row=1, column=0, padx=11, pady=(2, 1), sticky="ew"
            )
            freshness = price_freshness_label(offer.get("date_modified"))
            ctk.CTkLabel(
                card,
                text=freshness,
                font=("Segoe UI Semibold", 10),
                text_color=COLORS["warning"] if "revérifier" in freshness else COLORS["muted_2"],
                anchor="w",
            ).grid(row=2, column=0, padx=11, pady=(0, 8), sticky="ew")
            row_index += 1


class FavoritesPage(BasePage):
    title = "Mes favoris"
    subtitle = "Gardez sous la main vos achats et équipements prioritaires."

    def __init__(self, master: Any, app: "AsteriaxApp"):
        super().__init__(master, app)
        self.grid_columnconfigure((0, 1), weight=1, uniform="fav")
        self.grid_rowconfigure(1, weight=1)
        self.item_rows: dict[int, dict[str, Any]] = {}
        self.vehicle_rows: dict[int, dict[str, Any]] = {}
        self._build()

    def _build(self) -> None:
        self.item_title = SectionTitle(self, "Objets favoris", "Armures, armes et composants.")
        self.item_title.grid(row=0, column=0, padx=(0, 7), pady=(0, 9), sticky="ew")
        self.ship_title = SectionTitle(self, "Vaisseaux favoris", "Vaisseaux et véhicules terrestres.")
        self.ship_title.grid(row=0, column=1, padx=(7, 0), pady=(0, 9), sticky="ew")
        left = ctk.CTkFrame(self, fg_color="transparent")
        left.grid(row=1, column=0, padx=(0, 7), sticky="nsew")
        left.grid_rowconfigure(0, weight=1)
        left.grid_columnconfigure(0, weight=1)
        right = ctk.CTkFrame(self, fg_color="transparent")
        right.grid(row=1, column=1, padx=(7, 0), sticky="nsew")
        right.grid_rowconfigure(0, weight=1)
        right.grid_columnconfigure(0, weight=1)
        self.item_table = TreeTable(
            left,
            [
                ("name", "OBJET", 210, "w"),
                ("price", "PRIX", 125, "e"),
                ("location", "LIEU", 125, "w"),
            ],
            on_double_click=lambda iid: self.open_item(iid),
        )
        self.item_table.grid(row=0, column=0, sticky="nsew")
        self.vehicle_table = TreeTable(
            right,
            [
                ("name", "MODÈLE", 210, "w"),
                ("price", "PRIX", 125, "e"),
                ("location", "LIEU", 125, "w"),
            ],
            on_double_click=lambda iid: self.open_vehicle(iid),
        )
        self.vehicle_table.grid(row=0, column=0, sticky="nsew")
        self._button_row(left, 1, self.open_selected_item, self.remove_selected_item)
        self._button_row(right, 1, self.open_selected_vehicle, self.remove_selected_vehicle)

    def _button_row(self, master: Any, row: int, open_command: Callable[[], None], remove_command: Callable[[], None]) -> None:
        buttons = ctk.CTkFrame(master, fg_color="transparent")
        buttons.grid(row=row, column=0, pady=(9, 0), sticky="ew")
        buttons.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkButton(
            buttons,
            text="Ouvrir",
            command=open_command,
            height=34,
            corner_radius=8,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color=COLORS["background"],
            font=("Segoe UI Semibold", 11),
        ).grid(row=0, column=0, padx=(0, 5), sticky="ew")
        ctk.CTkButton(
            buttons,
            text="Retirer",
            command=remove_command,
            height=34,
            corner_radius=8,
            fg_color="transparent",
            hover_color=COLORS["panel_hover"],
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["muted"],
            font=("Segoe UI Semibold", 11),
        ).grid(row=0, column=1, padx=(5, 0), sticky="ew")

    def on_show(self) -> None:
        self.refresh_data()

    def refresh_data(self) -> None:
        item_ids = self.app.user_store.ids("item")
        vehicle_ids = self.app.user_store.ids("vehicle")
        items = self.app.repo.search_items(ids=item_ids) if item_ids else []
        vehicles = self.app.repo.search_vehicles(ids=vehicle_ids) if vehicle_ids else []
        self.item_rows = {int(row["id"]): row for row in items}
        self.vehicle_rows = {int(row["id"]): row for row in vehicles}
        self.item_table.populate(
            (
                str(row["id"]),
                (row["name"], format_price(row.get("price_min")), _short_location(row)),
                True,
            )
            for row in items
        )
        self.vehicle_table.populate(
            (
                str(row["id"]),
                (row["name"], format_price(row.get("price_min")), _short_location(row)),
                True,
            )
            for row in vehicles
        )
        self.item_title.winfo_children()[0].configure(text=f"Objets favoris  ·  {len(items)}")
        self.ship_title.winfo_children()[0].configure(text=f"Vaisseaux favoris  ·  {len(vehicles)}")

    def open_item(self, iid: str) -> None:
        if iid:
            self.app.open_item(int(iid))

    def open_vehicle(self, iid: str) -> None:
        if iid:
            self.app.open_vehicle(int(iid))

    def open_selected_item(self) -> None:
        self.open_item(self.item_table.selected_id())

    def open_selected_vehicle(self) -> None:
        self.open_vehicle(self.vehicle_table.selected_id())

    def remove_selected_item(self) -> None:
        iid = self.item_table.selected_id()
        if iid and self.app.user_store.is_favourite("item", int(iid)):
            self.app.user_store.toggle("item", int(iid))
            self.refresh_data()

    def remove_selected_vehicle(self) -> None:
        iid = self.vehicle_table.selected_id()
        if iid and self.app.user_store.is_favourite("vehicle", int(iid)):
            self.app.user_store.toggle("vehicle", int(iid))
            self.refresh_data()


class DataPage(BasePage):
    title = "Patch & sources"
    subtitle = "Version LIVE, fraîcheur du cache et provenance de chaque donnée."

    def __init__(self, master: Any, app: "AsteriaxApp"):
        super().__init__(master, app)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color=COLORS["accent_dark"],
        )
        self.scroll.grid(row=0, column=0, sticky="nsew")
        self.scroll.grid_columnconfigure((0, 1), weight=1, uniform="data")
        self._built = False

    def on_show(self) -> None:
        if not self._built:
            self.refresh_data()

    def refresh_data(self) -> None:
        for child in self.scroll.winfo_children():
            child.destroy()
        self._built = True
        meta = self.app.repo.meta()
        counts = self.app.repo.meta_counts()
        synced = meta.get("synced_at", "")
        try:
            sync_label = datetime.fromisoformat(synced).astimezone().strftime("%d/%m/%Y à %H:%M")
        except (TypeError, ValueError):
            sync_label = synced or "inconnue"

        live = ctk.CTkFrame(
            self.scroll,
            fg_color=COLORS["panel"],
            corner_radius=16,
            border_width=1,
            border_color=COLORS["border"],
        )
        live.grid(row=0, column=0, columnspan=2, pady=(0, 15), sticky="ew")
        live.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(live, text="VERSION DES DONNÉES", font=("Segoe UI Semibold", 11), text_color=COLORS["accent"], anchor="w").grid(
            row=0, column=0, padx=22, pady=(19, 4), sticky="ew"
        )
        ctk.CTkLabel(live, text=f"Star Citizen {meta.get('game_version', '—')} LIVE", font=("Segoe UI Semibold", 25), text_color=COLORS["text"], anchor="w").grid(
            row=1, column=0, padx=22, sticky="ew"
        )
        ctk.CTkLabel(
            live,
            text=f"Synchronisation locale : {sync_label}  •  PTU signalé : {meta.get('ptu_version') or '—'}",
            font=("Segoe UI", 12),
            text_color=COLORS["muted"],
            anchor="w",
        ).grid(row=2, column=0, padx=22, pady=(5, 19), sticky="ew")
        source_cards = [
            (
                "DONNÉES DU JEU",
                "UEX API 2.0",
                f"{counts.get('purchasable_items', 0)} objets • {counts.get('purchasable_vehicles', 0)} vaisseaux/véhicules • prix et boutiques",
                UEX_SITE_URL,
            ),
            (
                "VERSION OFFICIELLE",
                VERIFIED_LIVE_VERSION,
                f"Build LIVE vérifié le {VERIFIED_LIVE_DATE} auprès de Roberts Space Industries.",
                RSI_LIVE_PATCH_URL,
            ),
        ]
        for column, (eyebrow, title, text, url) in enumerate(source_cards):
            card = ctk.CTkFrame(
                self.scroll,
                fg_color=COLORS["panel"],
                corner_radius=14,
                border_width=1,
                border_color=COLORS["border"],
            )
            card.grid(row=1, column=column, padx=(0, 7) if column == 0 else (7, 0), pady=(0, 15), sticky="nsew")
            card.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(card, text=eyebrow, font=("Segoe UI Semibold", 10), text_color=COLORS["muted_2"], anchor="w").grid(
                row=0, column=0, padx=17, pady=(16, 4), sticky="ew"
            )
            ctk.CTkLabel(card, text=title, font=("Segoe UI Semibold", 17), text_color=COLORS["text"], anchor="w").grid(
                row=1, column=0, padx=17, sticky="ew"
            )
            ctk.CTkLabel(card, text=text, wraplength=430, justify="left", font=("Segoe UI", 11), text_color=COLORS["muted"], anchor="w").grid(
                row=2, column=0, padx=17, pady=(5, 12), sticky="ew"
            )
            ctk.CTkButton(
                card,
                text="Ouvrir la source  ↗",
                command=lambda target=url: webbrowser.open(target),
                height=31,
                corner_radius=7,
                fg_color="transparent",
                hover_color=COLORS["panel_hover"],
                border_width=1,
                border_color=COLORS["border"],
                text_color=COLORS["accent"],
                font=("Segoe UI Semibold", 11),
            ).grid(row=3, column=0, padx=17, pady=(0, 16), sticky="ew")

        SectionTitle(self.scroll, "Liens officiels et contrôles", "Pour suivre le prochain patch et vérifier l'état du jeu.").grid(
            row=2, column=0, columnspan=2, pady=(0, 9), sticky="ew"
        )
        links = ctk.CTkFrame(
            self.scroll,
            fg_color=COLORS["panel"],
            corner_radius=14,
            border_width=1,
            border_color=COLORS["border"],
        )
        links.grid(row=3, column=0, columnspan=2, pady=(0, 15), sticky="ew")
        links.grid_columnconfigure((0, 1, 2), weight=1, uniform="link")
        link_data = [
            ("Notes de patch", RSI_PATCHES_URL),
            ("État des serveurs", RSI_STATUS_URL),
            ("Problèmes connus", RSI_KNOWN_ISSUES_URL),
            ("Roadmap RSI", RSI_ROADMAP_URL),
            ("Liste des vaisseaux vérifiée", WIKI_SHIPS_URL),
            ("Documentation UEX", UEX_API_DOCS_URL),
            ("Discord AsteriaxTTV", DISCORD_URL),
            ("Twitch AsteriaxTTV", TWITCH_URL),
        ]
        for index, (label, url) in enumerate(link_data):
            ctk.CTkButton(
                links,
                text=f"{label}  ↗",
                command=lambda target=url: webbrowser.open(target),
                height=36,
                corner_radius=8,
                fg_color=COLORS["panel_alt"],
                hover_color=COLORS["panel_hover"],
                border_width=1,
                border_color=COLORS["border"],
                text_color=COLORS["text"],
                font=("Segoe UI Semibold", 11),
            ).grid(row=index // 3, column=index % 3, padx=8, pady=8, sticky="ew")

        SectionTitle(self.scroll, "Versions récentes", "Historique fourni par UEX à partir des publications CIG.").grid(
            row=4, column=0, columnspan=2, pady=(0, 9), sticky="ew"
        )
        versions = TreeTable(
            self.scroll,
            [
                ("version", "VERSION", 220, "w"),
                ("date", "DATE DE SORTIE", 220, "w"),
                ("channel", "CANAL", 150, "center"),
            ],
        )
        versions.grid(row=5, column=0, columnspan=2, pady=(0, 15), sticky="ew")
        versions.configure(height=275)
        versions.populate(
            (
                str(index),
                (row.get("game_version"), format_timestamp(row.get("release_timestamp")), "LIVE"),
                index == 0,
            )
            for index, row in enumerate(self.app.repo.latest_game_versions())
        )

        warning = ctk.CTkFrame(
            self.scroll,
            fg_color="#2A2214",
            corner_radius=12,
            border_width=1,
            border_color="#6B5425",
        )
        warning.grid(row=6, column=0, columnspan=2, pady=(0, 15), sticky="ew")
        warning.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            warning,
            text="À SAVOIR",
            font=("Segoe UI Semibold", 10),
            text_color=COLORS["warning"],
            anchor="w",
        ).grid(row=0, column=0, padx=15, pady=(12, 3), sticky="ew")
        ctk.CTkLabel(
            warning,
            text=(
                "UEX est une base communautaire : un prix peut évoluer après un hotfix, varier selon une remise locale "
                "ou être corrigé après un relevé en jeu. Le bouton de mise à jour recharge l'intégralité des données."
            ),
            wraplength=920,
            justify="left",
            font=("Segoe UI", 11),
            text_color="#D8C69E",
            anchor="w",
        ).grid(row=1, column=0, padx=15, pady=(0, 12), sticky="ew")

        about = ctk.CTkFrame(
            self.scroll,
            fg_color=COLORS["panel"],
            corner_radius=14,
            border_width=1,
            border_color=COLORS["border"],
        )
        about.grid(row=7, column=0, columnspan=2, pady=(0, 20), sticky="ew")
        if getattr(self.app, "logo_full", None):
            ctk.CTkLabel(about, text="", image=self.app.logo_full).pack(pady=(15, 3))
        ctk.CTkLabel(
            about,
            text=f"{APP_NAME}  ·  version {APP_VERSION}",
            font=("Segoe UI Semibold", 14),
            text_color=COLORS["text"],
        ).pack(pady=(3, 3))
        ctk.CTkLabel(
            about,
            text=f"Imaginé et créé pour la communauté par {APP_AUTHOR}",
            font=("Segoe UI", 12),
            text_color=COLORS["accent"],
        ).pack(pady=(0, 3))
        ctk.CTkLabel(
            about,
            text="Projet non officiel, sans affiliation avec Cloud Imperium Games.",
            font=("Segoe UI", 10),
            text_color=COLORS["muted_2"],
        ).pack(pady=(0, 15))


class TabbedHubPage(BasePage):
    """Container for closely related pages without multiplying sidebar entries."""

    def __init__(
        self,
        master: Any,
        app: "AsteriaxApp",
        *,
        sections: list[tuple[str, str, Callable[[], Any]]],
        default_section: str,
    ):
        super().__init__(master, app)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._labels = {key: label for key, label, _factory in sections}
        self._keys_by_label = {label: key for key, label, _factory in sections}
        self._factories = {key: factory for key, _label, factory in sections}
        self._children: dict[str, Any] = {}
        self._current_section = ""

        switch_card = ctk.CTkFrame(
            self,
            fg_color=COLORS["panel"],
            corner_radius=14,
            border_width=1,
            border_color=COLORS["border"],
        )
        switch_card.grid(row=0, column=0, pady=(0, 12), sticky="ew")
        switch_card.grid_columnconfigure(0, weight=1)
        self.section_switch = ctk.CTkSegmentedButton(
            switch_card,
            values=[label for _key, label, _factory in sections],
            command=self._select_label,
            height=38,
            corner_radius=10,
            fg_color=COLORS["panel_alt"],
            selected_color=COLORS["accent_dark"],
            selected_hover_color=COLORS["accent_dark"],
            unselected_color=COLORS["panel_alt"],
            unselected_hover_color=COLORS["panel_hover"],
            text_color=COLORS["text"],
            font=("Segoe UI Semibold", 12),
        )
        self.section_switch.grid(row=0, column=0, padx=8, pady=8, sticky="ew")

        self.content = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.content.grid(row=1, column=0, sticky="nsew")
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)
        self.show_section(default_section, notify=False)

    def _select_label(self, label: str) -> None:
        self.show_section(self._keys_by_label[label])

    def child_page(self, key: str, *, create: bool = True) -> Any | None:
        page = self._children.get(key)
        if page is None and create:
            page = self._factories[key]()
            self._children[key] = page
        return page

    def show_section(self, key: str, *, notify: bool = True) -> None:
        if key not in self._factories:
            return
        previous = self._children.get(self._current_section)
        page = self.child_page(key)
        if previous is not None and previous is not page:
            previous.grid_remove()
        page.grid(row=0, column=0, sticky="nsew")
        page.tkraise()
        self._current_section = key
        self.section_switch.set(self._labels[key])
        if notify:
            page.on_show()

    def on_show(self) -> None:
        page = self.child_page(self._current_section)
        if page is not None:
            page.on_show()

    def refresh_data(self) -> None:
        for page in self._children.values():
            page.refresh_data()


class EquipmentHubPage(TabbedHubPage):
    title = "Équipements"
    subtitle = "Composants de vaisseau, armures, armes, munitions et accessoires."

    def __init__(self, master: Any, app: "AsteriaxApp"):
        super().__init__(
            master,
            app,
            sections=[
                (
                    "ship_gear",
                    "Équipement de vaisseau",
                    lambda: CatalogPage(
                        self.content,
                        app,
                        scope_key="ship_gear",
                        title="Équipement de vaisseau",
                        subtitle="Composants, canons, missiles, modules de minage et utilitaires.",
                    ),
                ),
                (
                    "personal_gear",
                    "Équipement personnel",
                    lambda: CatalogPage(
                        self.content,
                        app,
                        scope_key="personal_gear",
                        title="Équipement personnel",
                        subtitle="Armures, sous-combinaisons, vêtements, armes, munitions et accessoires.",
                    ),
                ),
            ],
            default_section="ship_gear",
        )

    def open_entity(self, section: str, entity_id: int) -> None:
        self.show_section(section, notify=False)
        page = self.child_page(section)
        if isinstance(page, CatalogPage):
            page.open_entity(entity_id)


class MaintenanceHubPage(TabbedHubPage):
    title = "Mises à jour"
    subtitle = "Logiciel, données Star Citizen, patch LIVE et sources officielles."

    def __init__(self, master: Any, app: "AsteriaxApp"):
        super().__init__(
            master,
            app,
            sections=[
                ("updates", "Logiciel & données", lambda: UpdatesPage(self.content, app)),
                ("data", "Patch & sources", lambda: DataPage(self.content, app)),
            ],
            default_section="updates",
        )


class AsteriaxApp(ctk.CTk):
    """Top-level window, navigation, background updates and shared actions."""

    def __init__(self) -> None:
        super().__init__(fg_color=COLORS["background"])
        self.database_path = data_database_path()
        self.user_store = UserStore(user_database_path())
        ensure_performance_indexes(self.database_path)
        self.repo = DataRepository(self.database_path)
        self.performance_mode = self.user_store.setting_bool("performance_mode", False)
        self.catalog_page_size = 100 if self.performance_mode else 220
        self._updating = False
        self._remote_game_version = ""
        self._notice_after: str | None = None
        self._search_dialog: GlobalSearchDialog | None = None
        self._sidebar_user_preference = self.user_store.setting_bool("sidebar_collapsed", False)
        self._sidebar_collapsed = self._sidebar_user_preference
        self._responsive_compact = False
        self._responsive_after: str | None = None

        self.title(f"{APP_NAME} — Star Citizen Companion")
        default_geometry = "1440x880"
        saved_geometry = self.user_store.get_setting("window_geometry", default_geometry)
        geometry = saved_geometry if re.fullmatch(r"\d+x\d+(?:[+-]\d+){0,2}", saved_geometry) else default_geometry
        self.geometry(geometry)
        self.minsize(1040, 700)
        try:
            icon = resource_path("assets", "asteriax.ico")
            if icon.exists():
                self.iconbitmap(str(icon))
        except (OSError, tk.TclError):
            pass

        self._load_images()
        configure_ttk_styles(self)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self._build_sidebar()
        self._build_main()
        self._create_pages()
        self._set_sidebar_collapsed(self._sidebar_collapsed, persist=False)

        remembered = self.user_store.get_setting("last_page", "dashboard")
        self.show_page(remembered)
        self.bind_all("<Control-k>", lambda _event: self.open_global_search(), add="+")
        self.bind_all("<Control-f>", lambda _event: self.open_global_search(), add="+")
        self.bind("<Configure>", self._schedule_responsive_layout, add="+")
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        if self.user_store.setting_bool("show_splash", True) and not self.performance_mode:
            self.after(180, self._show_splash)
        if self.user_store.setting_bool("check_patch_startup", True):
            self.after(1200, lambda: self.check_game_update(self._startup_patch_result))
        self.after(1500, self._announce_completed_app_update)

    def _schedule_responsive_layout(self, event: Any) -> None:
        if event.widget is not self:
            return
        if self._responsive_after:
            try:
                self.after_cancel(self._responsive_after)
            except tk.TclError:
                pass
        self._responsive_after = self.after(160, self._apply_responsive_layout)

    def _apply_responsive_layout(self) -> None:
        self._responsive_after = None
        width = self.winfo_width()
        if width < 1160 and not self._responsive_compact:
            self._responsive_compact = True
            self._set_sidebar_collapsed(True, persist=False)
        elif width > 1280 and self._responsive_compact:
            self._responsive_compact = False
            self._set_sidebar_collapsed(self._sidebar_user_preference, persist=False)

    def _announce_completed_app_update(self) -> None:
        result = consume_update_result()
        if not result:
            return
        installed_at = result.get("installed_at") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.user_store.set_setting("last_app_update_version", APP_VERSION)
        self.user_store.set_setting("last_app_update_at", installed_at)
        self.show_notice(
            f"Étape 4/4 · Mise à jour {APP_VERSION} installée avec succès.",
            COLORS["success"],
            9000,
        )
        messagebox.showinfo(
            "Mise à jour terminée",
            f"Asteriax Verse {APP_VERSION} a été installé et redémarré avec succès.\n\n"
            + "\n".join(f"• {line}" for line in APP_RELEASE_NOTES),
            parent=self,
        )

    def _load_images(self) -> None:
        self.logo_mark: ctk.CTkImage | None = None
        self.logo_full: ctk.CTkImage | None = None
        try:
            mark_path = resource_path("assets", "asteriax_mark.png")
            full_path = resource_path("assets", "asteriax_logo.png")
            if mark_path.exists():
                mark = Image.open(mark_path)
                self.logo_mark = ctk.CTkImage(light_image=mark, dark_image=mark, size=(58, 58))
            if full_path.exists():
                full = Image.open(full_path)
                self.logo_full = ctk.CTkImage(light_image=full, dark_image=full, size=(185, 126))
        except (OSError, ValueError):
            self.logo_mark = None
            self.logo_full = None

    def _show_splash(self) -> None:
        if not self.winfo_exists():
            return
        splash = ctk.CTkToplevel(self)
        splash.overrideredirect(True)
        splash.configure(fg_color=COLORS["background"])
        splash.attributes("-topmost", True)
        width, height = 520, 360
        x = max(0, self.winfo_rootx() + (self.winfo_width() - width) // 2)
        y = max(0, self.winfo_rooty() + (self.winfo_height() - height) // 2)
        splash.geometry(f"{width}x{height}+{x}+{y}")
        panel = ctk.CTkFrame(
            splash,
            fg_color=COLORS["panel"],
            corner_radius=20,
            border_width=1,
            border_color=COLORS["border"],
        )
        panel.pack(fill="both", expand=True, padx=8, pady=8)
        if self.logo_full:
            ctk.CTkLabel(panel, text="", image=self.logo_full).pack(pady=(42, 8))
        ctk.CTkLabel(panel, text=APP_NAME, font=("Segoe UI Semibold", 25), text_color=COLORS["text"]).pack()
        ctk.CTkLabel(
            panel,
            text=f"STAR CITIZEN COMPANION  ·  VERSION {APP_VERSION}",
            font=("Segoe UI Semibold", 10),
            text_color=COLORS["accent"],
        ).pack(pady=(4, 0))
        splash.after(1150, splash.destroy)

    def _build_sidebar(self) -> None:
        self.sidebar = ctk.CTkFrame(self, width=270, corner_radius=0, fg_color=COLORS["sidebar"])
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_columnconfigure(0, weight=1)
        self.sidebar.grid_rowconfigure(2, weight=1)

        self.sidebar_brand = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.sidebar_brand.grid(row=0, column=0, padx=16, pady=(15, 14), sticky="ew")
        self.sidebar_brand.grid_columnconfigure(1, weight=1)
        if self.logo_mark:
            self.brand_mark = ctk.CTkLabel(self.sidebar_brand, text="", image=self.logo_mark, width=58, height=58)
        else:
            self.brand_mark = ctk.CTkLabel(
                self.sidebar_brand,
                text="AX",
                width=54,
                height=54,
                corner_radius=13,
                fg_color=COLORS["accent"],
                font=("Segoe UI Black", 20),
                text_color=COLORS["background"],
            )
        self.brand_mark.grid(row=0, column=0, rowspan=2, padx=(0, 9))
        self.brand_name = ctk.CTkLabel(
            self.sidebar_brand,
            text="ASTERIAX",
            font=("Segoe UI Semibold", 18),
            text_color=COLORS["text"],
            anchor="w",
        )
        self.brand_name.grid(row=0, column=1, sticky="sw")
        self.brand_subtitle = ctk.CTkLabel(
            self.sidebar_brand,
            text="VERSE  /  SC COMPANION",
            font=("Segoe UI Semibold", 11),
            text_color=COLORS["accent"],
            anchor="w",
        )
        self.brand_subtitle.grid(row=1, column=1, sticky="nw")

        self.nav_title = ctk.CTkLabel(
            self.sidebar,
            text="NAVIGATION",
            font=("Segoe UI Semibold", 12),
            text_color=COLORS["muted_2"],
            anchor="w",
        )
        self.nav_title.grid(row=1, column=0, padx=23, pady=(0, 5), sticky="ew")
        self.nav_frame = ctk.CTkFrame(
            self.sidebar,
            fg_color=COLORS["panel"],
            corner_radius=16,
            border_width=1,
            border_color=COLORS["border"],
        )
        self.nav_frame.grid(row=2, column=0, padx=10, pady=(2, 0), sticky="nsew")
        self.nav_frame.grid_columnconfigure(0, weight=1)
        entries = [
            ("dashboard", "⌂", "Accueil"),
            ("ships", "✦", "Vaisseaux & véhicules"),
            ("equipment", "⚙", "Équipements"),
            ("locations", "⌖", "Boutiques & lieux"),
            ("compare", "⇄", "Comparateur"),
            ("updates", "↻", "Mises à jour"),
            ("settings", "⋯", "Réglages & communauté"),
        ]
        self.nav_meta = {name: (icon, label) for name, icon, label in entries}
        self.nav_buttons: dict[str, ctk.CTkButton] = {}
        for row, (name, icon, label) in enumerate(entries):
            button = ctk.CTkButton(
                self.nav_frame,
                text=f"{icon}  {label}",
                command=lambda page=name: self.show_page(page),
                height=40,
                corner_radius=11,
                anchor="w",
                fg_color=COLORS["panel_alt"],
                hover_color=COLORS["panel_hover"],
                text_color=COLORS["muted"],
                border_width=1,
                border_color=COLORS["border"],
                font=("Segoe UI Semibold", 13),
            )
            button.grid(
                row=row,
                column=0,
                padx=8,
                pady=(8 if row == 0 else 3, 8 if row == len(entries) - 1 else 3),
                sticky="ew",
            )
            self.nav_buttons[name] = button

        self.sidebar_footer = ctk.CTkFrame(
            self.sidebar,
            fg_color=COLORS["panel"],
            corner_radius=11,
            border_width=1,
            border_color=COLORS["border"],
        )
        self.sidebar_footer.grid(row=3, column=0, padx=12, pady=12, sticky="ew")
        ctk.CTkLabel(
            self.sidebar_footer,
            text=f"{APP_AUTHOR}  ·  v{APP_VERSION}",
            font=("Segoe UI Semibold", 13),
            text_color=COLORS["accent"],
        ).pack(pady=(8, 4))
        community = ctk.CTkFrame(self.sidebar_footer, fg_color="transparent")
        community.pack(padx=7, pady=(0, 7), fill="x")
        community.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkButton(
            community,
            text="Discord",
            command=lambda: webbrowser.open(DISCORD_URL),
            height=31,
            fg_color="#5865F2",
            hover_color="#6875F5",
            text_color="#FFFFFF",
            font=("Segoe UI Semibold", 12),
        ).grid(row=0, column=0, padx=(0, 2), sticky="ew")
        ctk.CTkButton(
            community,
            text="Twitch",
            command=lambda: webbrowser.open(TWITCH_URL),
            height=31,
            fg_color="#9146FF",
            hover_color="#A364FF",
            text_color="#FFFFFF",
            font=("Segoe UI Semibold", 12),
        ).grid(row=0, column=1, padx=(2, 0), sticky="ew")

    def _build_main(self) -> None:
        self.main = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.main.grid(row=0, column=1, sticky="nsew")
        self.main.grid_rowconfigure(1, weight=1)
        self.main.grid_columnconfigure(0, weight=1)
        header = ctk.CTkFrame(self.main, height=92, corner_radius=0, fg_color="transparent")
        header.grid(row=0, column=0, padx=20, sticky="ew")
        header.grid_columnconfigure(1, weight=1)
        self.sidebar_toggle = ctk.CTkButton(
            header,
            text="☰",
            command=self.toggle_sidebar,
            width=38,
            height=36,
            corner_radius=9,
            fg_color=COLORS["panel"],
            hover_color=COLORS["panel_hover"],
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            font=("Segoe UI Semibold", 14),
        )
        self.sidebar_toggle.grid(row=0, column=0, rowspan=2, padx=(0, 12))
        self.page_title = ctk.CTkLabel(
            header,
            text="",
            font=("Segoe UI Semibold", 26),
            text_color=COLORS["text"],
            anchor="w",
        )
        self.page_title.grid(row=0, column=1, pady=(17, 0), sticky="ew")
        self.page_subtitle = ctk.CTkLabel(
            header,
            text="",
            font=("Segoe UI", 12),
            text_color=COLORS["muted"],
            anchor="w",
        )
        self.page_subtitle.grid(row=1, column=1, pady=(2, 14), sticky="ew")
        self.search_button = ctk.CTkButton(
            header,
            text="⌕  Rechercher   Ctrl+K",
            command=self.open_global_search,
            width=170,
            height=36,
            corner_radius=9,
            fg_color=COLORS["panel"],
            hover_color=COLORS["panel_hover"],
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["muted"],
            font=("Segoe UI Semibold", 12),
        )
        self.search_button.grid(row=0, column=2, rowspan=2, padx=(10, 8))
        self.live_badge = ctk.CTkLabel(
            header,
            text="",
            width=105,
            height=29,
            corner_radius=14,
            fg_color=COLORS["accent_dark"],
            text_color=COLORS["accent"],
            font=("Segoe UI Semibold", 13),
        )
        self.live_badge.grid(row=0, column=3, rowspan=2, padx=(0, 8))
        self.patch_update_button = ctk.CTkButton(
            header,
            text="Nouveau patch",
            command=lambda: self.show_page("updates"),
            width=145,
            height=36,
            corner_radius=9,
            fg_color=COLORS["warning"],
            hover_color="#FFD778",
            text_color=COLORS["background"],
            font=("Segoe UI Semibold", 12),
        )
        self.patch_update_button.grid(row=0, column=4, rowspan=2)
        self.patch_update_button.grid_remove()

        self.page_container = ctk.CTkFrame(self.main, fg_color="transparent", corner_radius=0)
        self.page_container.grid(row=1, column=0, padx=20, pady=(0, 12), sticky="nsew")
        self.page_container.grid_rowconfigure(0, weight=1)
        self.page_container.grid_columnconfigure(0, weight=1)

        self.sync_bar = ctk.CTkFrame(
            self.main,
            fg_color=COLORS["panel"],
            corner_radius=10,
            border_width=1,
            border_color=COLORS["border"],
        )
        self.sync_bar.grid(row=2, column=0, padx=20, pady=(0, 8), sticky="ew")
        self.sync_bar.grid_columnconfigure(0, weight=1)
        self.sync_status = ctk.CTkLabel(
            self.sync_bar,
            text="",
            font=("Segoe UI", 10),
            text_color=COLORS["muted"],
            anchor="w",
        )
        self.sync_status.grid(row=0, column=0, padx=12, pady=(7, 2), sticky="ew")
        self.sync_progress = ctk.CTkProgressBar(
            self.sync_bar,
            height=7,
            corner_radius=4,
            fg_color=COLORS["panel_alt"],
            progress_color=COLORS["accent"],
        )
        self.sync_progress.grid(row=1, column=0, padx=12, pady=(0, 8), sticky="ew")
        self.sync_bar.grid_remove()

        self.notice_bar = ctk.CTkFrame(
            self.main,
            fg_color=COLORS["panel"],
            corner_radius=9,
            border_width=1,
            border_color=COLORS["accent"],
        )
        self.notice_bar.grid(row=3, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.notice_label = ctk.CTkLabel(
            self.notice_bar,
            text="",
            font=("Segoe UI Semibold", 10),
            text_color=COLORS["text"],
            anchor="w",
        )
        self.notice_label.pack(fill="x", padx=12, pady=8)
        self.notice_bar.grid_remove()
        self._refresh_live_badge()

    def _create_pages(self) -> None:
        # Building every page up front left ten complete widget trees stacked in
        # the same grid cell. Tk then resized all of them on every window-size
        # event, including the invisible pages. Factories keep startup light and
        # ensure that only pages opened by the user exist.
        self._page_factories: dict[str, Callable[[], Any]] = {
            "dashboard": lambda: DashboardPage(self.page_container, self),
            "ships": lambda: ShipsPage(self.page_container, self),
            "equipment": lambda: EquipmentHubPage(self.page_container, self),
            "all_items": lambda: CatalogPage(
                self.page_container,
                self,
                scope_key="all",
                title="Tous les objets",
                subtitle="L'intégralité des objets actuellement achetables dans le Persistent Universe.",
            ),
            "locations": lambda: LocationsPage(self.page_container, self),
            "compare": lambda: ComparePage(self.page_container, self),
            "updates": lambda: MaintenanceHubPage(self.page_container, self),
            "settings": lambda: SettingsPage(self.page_container, self),
        }
        self.pages: dict[str, Any] = {}
        self.current_page = ""

    def _get_page(self, name: str) -> Any:
        page = self.pages.get(name)
        if page is None:
            page = self._page_factories[name]()
            self.pages[name] = page
        return page

    def show_page(self, name: str) -> None:
        legacy_routes = {
            "ship_gear": ("equipment", "ship_gear"),
            "personal_gear": ("equipment", "personal_gear"),
            "data": ("updates", "data"),
            "translation": ("settings", ""),
        }
        name, section = legacy_routes.get(name, (name, ""))
        if name not in self._page_factories:
            name = "dashboard"
        previous = self.pages.get(self.current_page)
        page = self._get_page(name)
        if previous is not None and previous is not page:
            # Unmapping the previous page prevents Tk/CustomTkinter from
            # recalculating its complete layout during a maximize/restore.
            previous.grid_remove()
        page.grid(row=0, column=0, sticky="nsew")
        self.current_page = name
        page.tkraise()
        self.page_title.configure(text=page.title)
        self.page_subtitle.configure(text=page.subtitle)
        for key, button in self.nav_buttons.items():
            active = key == name
            button.configure(
                fg_color=COLORS["accent_dark"] if active else COLORS["panel_alt"],
                text_color=COLORS["accent"] if active else COLORS["muted"],
                border_color=COLORS["accent"] if active else COLORS["border"],
            )
        if self.user_store.setting_bool("remember_state", True):
            self.user_store.set_setting("last_page", name)
        if isinstance(page, EquipmentHubPage) and section:
            page.show_section(section, notify=False)
        elif isinstance(page, MaintenanceHubPage) and section:
            page.show_section(section, notify=False)
        page.on_show()

    def open_navigation_target(self, target: str) -> None:
        if target.startswith("equipment:"):
            self.show_page(target.split(":", 1)[1])
        else:
            self.show_page(target)

    def refresh_page(self, name: str) -> None:
        if name in self.pages:
            self.pages[name].refresh_data()

    def open_entity(self, kind: str, entity_id: int) -> None:
        if kind == "item":
            self.open_item(entity_id)
        elif kind == "vehicle":
            self.open_vehicle(entity_id)
        elif kind == "terminal":
            self.open_terminal(entity_id)

    def open_item(self, item_id: int) -> None:
        detail = self.repo.item_detail(int(item_id)) or {}
        section = detail.get("section")
        if section in ITEM_SCOPES["ship_gear"]["sections"]:
            equipment_section = "ship_gear"
        elif section in ITEM_SCOPES["personal_gear"]["sections"]:
            equipment_section = "personal_gear"
        else:
            # Le catalogue général reste un écran interne pour les objets qui
            # n'appartiennent à aucune des deux grandes familles visibles.
            page = self._get_page("all_items")
            self.show_page("all_items")
            if isinstance(page, CatalogPage):
                page.open_entity(int(item_id))
            return
        self.show_page(equipment_section)
        page = self._get_page("equipment")
        if isinstance(page, EquipmentHubPage):
            page.open_entity(equipment_section, int(item_id))

    def open_vehicle(self, vehicle_id: int) -> None:
        page = self._get_page("ships")
        self.show_page("ships")
        if isinstance(page, ShipsPage):
            page.open_entity(int(vehicle_id))

    def open_terminal(self, terminal_id: int) -> None:
        page = self._get_page("locations")
        self.show_page("locations")
        if isinstance(page, LocationsPage):
            page.open_entity(int(terminal_id))

    def open_global_search(self) -> None:
        try:
            if self._search_dialog and self._search_dialog.winfo_exists():
                self._search_dialog.lift()
                self._search_dialog.entry.focus_set()
                return
        except tk.TclError:
            pass
        self._search_dialog = GlobalSearchDialog(self)

    def record_recent(self, kind: str, entity_id: int) -> None:
        self.user_store.add_recent(kind, int(entity_id))

    def add_to_comparison(self, kind: str, entity_id: int) -> None:
        if self.user_store.add_comparison(kind, int(entity_id)):
            self.refresh_page("compare")
            self.show_notice("Ajouté au comparateur.")
        else:
            self.show_notice("Le comparateur contient déjà trois éléments de ce type.", COLORS["warning"])

    def copy_to_clipboard(self, text: str, notice: str = "Copié") -> None:
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update_idletasks()
        self.show_notice(notice)

    def show_notice(self, message: str, color: str | None = None, duration: int = 3800) -> None:
        accent = color or COLORS["success"]
        self.notice_bar.configure(border_color=accent)
        self.notice_label.configure(text=message, text_color=accent)
        self.notice_bar.grid()
        if self._notice_after:
            try:
                self.after_cancel(self._notice_after)
            except tk.TclError:
                pass
        self._notice_after = self.after(duration, self.notice_bar.grid_remove)

    def toggle_sidebar(self) -> None:
        self._set_sidebar_collapsed(not self._sidebar_collapsed)

    def _set_sidebar_collapsed(self, collapsed: bool, *, persist: bool = True) -> None:
        self._sidebar_collapsed = bool(collapsed)
        self.sidebar.configure(width=82 if collapsed else 270)
        if collapsed:
            self.brand_name.grid_remove()
            self.brand_subtitle.grid_remove()
            self.nav_title.grid_remove()
            self.sidebar_footer.grid_remove()
            self.sidebar_brand.grid_configure(padx=8)
            self.brand_mark.grid_configure(padx=0)
            self.nav_frame.grid_configure(padx=8)
        else:
            self.brand_name.grid()
            self.brand_subtitle.grid()
            self.nav_title.grid()
            self.sidebar_footer.grid()
            self.sidebar_brand.grid_configure(padx=16)
            self.brand_mark.grid_configure(padx=(0, 9))
            self.nav_frame.grid_configure(padx=10)
        for name, button in self.nav_buttons.items():
            icon, label = self.nav_meta[name]
            button.configure(text=icon if collapsed else f"{icon}  {label}", anchor="center" if collapsed else "w")
        if persist:
            self._sidebar_user_preference = bool(collapsed)
            self.user_store.set_setting("sidebar_collapsed", "1" if collapsed else "0")

    def _refresh_live_badge(self) -> None:
        try:
            version = self.repo.meta().get("game_version", "—")
        except Exception:
            version = "—"
        self.live_badge.configure(text=f"●  LIVE {version}")

    @staticmethod
    def _game_version_key(value: str) -> tuple[int, int, int, int]:
        numbers = [int(raw) for raw in re.findall(r"\d+", str(value or ""))[:4]]
        numbers.extend([0] * (4 - len(numbers)))
        return tuple(numbers[:4])  # type: ignore[return-value]

    def check_game_update(
        self,
        callback: Callable[[dict[str, Any] | None, Exception | None], None] | None = None,
    ) -> None:
        def worker() -> None:
            try:
                payload = fetch_json("data_parameters/", attempts=1, timeout=10)
                remote = ""
                if isinstance(payload, dict):
                    global_data = payload.get("global") or {}
                    if isinstance(global_data, dict):
                        remote = str(global_data.get("game_version") or "")
                local = str(self.repo.meta().get("game_version") or "")
                if not remote:
                    raise RuntimeError("Version LIVE non renseignée par la source.")
                result = {
                    "local_version": local,
                    "remote_version": remote,
                    "available": self._game_version_key(remote) > self._game_version_key(local),
                }
                self.after(0, lambda: self._finish_game_check(result, None, callback))
            except Exception as exc:
                self.after(0, lambda error=exc: self._finish_game_check(None, error, callback))

        threading.Thread(target=worker, name="asteriax-patch-check", daemon=True).start()

    def _finish_game_check(
        self,
        result: dict[str, Any] | None,
        error: Exception | None,
        callback: Callable[[dict[str, Any] | None, Exception | None], None] | None,
    ) -> None:
        if result and result.get("available"):
            self._remote_game_version = str(result.get("remote_version") or "")
            self.patch_update_button.configure(text=f"Patch {self._remote_game_version} disponible")
            self.patch_update_button.grid()
        elif not error:
            self._remote_game_version = ""
            self.patch_update_button.grid_remove()
        if callback:
            callback(result, error)

    def _startup_patch_result(self, result: dict[str, Any] | None, error: Exception | None) -> None:
        if error or not result or not result.get("available"):
            return
        remote = result.get("remote_version") or "nouveau patch"
        self.show_notice(f"Star Citizen {remote} est disponible : ouvrez l’onglet Mises à jour.", COLORS["warning"], 7000)
        if self.user_store.setting_bool("auto_sync_patch", False):
            self.start_update()

    def check_app_update(
        self,
        callback: Callable[[dict[str, Any] | None, Exception | None], None] | None = None,
    ) -> None:
        results: queue.SimpleQueue[tuple[dict[str, Any] | None, Exception | None]] = queue.SimpleQueue()

        def worker() -> None:
            try:
                results.put((fetch_app_update(), None))
            except Exception as exc:
                results.put((None, exc))

        def poll_result() -> None:
            try:
                result, error = results.get_nowait()
            except queue.Empty:
                if self.winfo_exists():
                    self.after(80, poll_result)
                return
            self._finish_app_check(result, error, callback)

        threading.Thread(target=worker, name="asteriax-app-update-check", daemon=True).start()
        self.after(80, poll_result)

    def _finish_app_check(
        self,
        result: dict[str, Any] | None,
        error: Exception | None,
        callback: Callable[[dict[str, Any] | None, Exception | None], None] | None,
    ) -> None:
        if callback:
            callback(result, error)
            return
        if error:
            self.show_notice(f"Vérification impossible : {error}", COLORS["danger"])
        elif result and result.get("available"):
            self.show_notice(f"Asteriax Verse {result.get('latest_version')} est disponible.", COLORS["warning"])
        elif result and result.get("configured"):
            self.show_notice("Asteriax Verse est à jour.")
        else:
            self.show_notice("Le canal de mise à jour du logiciel n’est pas encore configuré.", COLORS["muted"])

    def start_update(self) -> None:
        if self._updating:
            self.show_notice("Une synchronisation est déjà en cours.", COLORS["warning"])
            return
        self._updating = True
        try:
            self._sync_before_counts = self.repo.meta_counts()
        except Exception:
            self._sync_before_counts = {}
        self.sync_status.configure(text="Connexion…", text_color=COLORS["muted"])
        self.sync_progress.set(0)
        self.sync_bar.grid()
        self.patch_update_button.configure(state="disabled")
        updates_page = self._visible_updates_page()
        if isinstance(updates_page, UpdatesPage):
            updates_page.update_game_button.configure(state="disabled", text="Synchronisation…")

        def update_progress(fraction: float, message: str) -> None:
            self.after(0, lambda f=fraction, m=message: (self.sync_progress.set(f), self.sync_status.configure(text=m)))

        def worker() -> None:
            try:
                result = sync_database(self.database_path, update_progress)
                self.after(0, lambda: self._finish_update(result, None))
            except Exception as exc:
                self.after(0, lambda error=exc: self._finish_update(None, error))

        threading.Thread(target=worker, name="asteriax-data-update", daemon=True).start()

    def _finish_update(self, result: dict[str, Any] | None, error: Exception | None) -> None:
        self._updating = False
        self.patch_update_button.configure(state="normal")
        updates_page = self._visible_updates_page()
        if error:
            if isinstance(updates_page, UpdatesPage):
                updates_page.update_game_button.configure(state="normal", text="Réessayer la synchronisation")
            self.sync_status.configure(text=f"Échec : {error} · l’ancienne base a été conservée.", text_color=COLORS["danger"])
            self.show_notice("Mise à jour impossible : la base hors ligne a été conservée.", COLORS["danger"], 7000)
            self.after(9000, self.sync_bar.grid_remove)
            return
        self.repo = DataRepository(self.database_path)
        self._refresh_live_badge()
        self.patch_update_button.grid_remove()
        self._remote_game_version = ""
        for page in self.pages.values():
            try:
                page.refresh_data()
            except tk.TclError:
                pass
        version = (result or {}).get("game_version", "—")
        counts = (result or {}).get("counts", {})
        previous_counts = getattr(self, "_sync_before_counts", {})
        vehicle_delta = int(counts.get("purchasable_vehicles", 0)) - int(
            previous_counts.get("purchasable_vehicles", 0) or 0
        )
        item_delta = int(counts.get("purchasable_items", 0)) - int(
            previous_counts.get("purchasable_items", 0) or 0
        )
        changes = []
        if vehicle_delta:
            changes.append(f"{vehicle_delta:+d} vaisseaux")
        if item_delta:
            changes.append(f"{item_delta:+d} objets")
        change_label = " · changements : " + ", ".join(changes) if changes else " · aucun changement de quantité"
        if isinstance(updates_page, UpdatesPage):
            updates_page._game_result(
                {"local_version": version, "remote_version": version, "available": False},
                None,
            )
        self.sync_progress.set(1)
        self.sync_status.configure(
            text=(
                f"Star Citizen {version} prêt · {counts.get('purchasable_vehicles', 0)} vaisseaux · "
                f"{counts.get('purchasable_items', 0)} objets revalidés{change_label}."
            ),
            text_color=COLORS["success"],
        )
        self.show_notice(f"Données Star Citizen {version} mises à jour.")
        self.after(6000, self.sync_bar.grid_remove)

    def _visible_updates_page(self) -> UpdatesPage | None:
        page = self.pages.get("updates")
        if isinstance(page, MaintenanceHubPage):
            child = page.child_page("updates", create=False)
            return child if isinstance(child, UpdatesPage) else None
        return page if isinstance(page, UpdatesPage) else None

    def _on_close(self) -> None:
        if self.user_store.setting_bool("remember_state", True):
            self.user_store.set_setting("window_geometry", self.geometry())
            self.user_store.set_setting("last_page", self.current_page or "dashboard")
        self.destroy()


def run() -> None:
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    # Une hausse modérée et uniforme rend le contenu de chaque page plus
    # lisible sans casser la disposition sur les écrans 1080p.
    ctk.set_widget_scaling(1.12)
    app = AsteriaxApp()
    app.mainloop()
