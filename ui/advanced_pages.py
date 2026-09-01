"""Asteriax Verse advanced comparison, discovery and update interfaces."""

from __future__ import annotations

import json
import queue
import threading
import tkinter as tk
import webbrowser
from datetime import datetime
from tkinter import filedialog, messagebox
from typing import Any

import customtkinter as ctk

from core.constants import (
    APP_AUTHOR,
    APP_NAME,
    APP_RELEASE_NOTES,
    APP_VERSION,
    COLORS,
    DISCORD_URL,
    ITEM_SCOPES,
    PATCH_410_CATALOGUE_HIGHLIGHTS,
    RSI_LIVE_PATCH_URL,
    TWITCH_URL,
    translate_category,
    translate_section,
)
from core.database import format_price, location_label, price_freshness_label
from core.paths import user_data_dir
from core.translation_fr import (
    DEFAULT_TRANSLATION_SOURCE,
    TRANSLATION_SOURCES,
    find_game_installations,
    install_french_translation,
    restore_english,
    translation_source_details,
    translation_source_url,
    translation_status,
    validate_game_folder,
)
from core.updater import can_self_update, download_app_update, launch_app_update
from ui.widgets import EmptyState, SectionTitle, TreeTable, labelled_combo


KIND_LABELS = {"item": "Objet", "vehicle": "Vaisseau", "terminal": "Boutique"}


def _entity_iid(kind: str, entity_id: int) -> str:
    return f"{kind}:{int(entity_id)}"


def _parse_iid(iid: str) -> tuple[str, int] | None:
    try:
        kind, raw_id = iid.split(":", 1)
        return kind, int(raw_id)
    except (AttributeError, TypeError, ValueError):
        return None


class AdvancedPage(ctk.CTkFrame):
    title = ""
    subtitle = ""

    def __init__(self, master: Any, app: Any):
        super().__init__(master, fg_color="transparent")
        self.app = app

    def on_show(self) -> None:
        self.refresh_data()

    def refresh_data(self) -> None:
        pass


class GlobalSearchDialog(ctk.CTkToplevel):
    """Keyboard-first search across vehicles, items and active shops."""

    def __init__(self, app: Any):
        super().__init__(app)
        self.app = app
        self.rows: dict[str, dict[str, Any]] = {}
        self._debounce: str | None = None
        self.title("Recherche globale — Asteriax Verse")
        self.geometry("980x620")
        self.minsize(760, 470)
        self.transient(app)
        self.configure(fg_color=COLORS["background"])
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, padx=24, pady=(22, 10), sticky="ew")
        top.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            top,
            text="Recherche globale",
            font=("Segoe UI Semibold", 23),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(
            top,
            text="Vaisseaux, équipements et boutiques dans un seul champ.",
            font=("Segoe UI", 10),
            text_color=COLORS["muted"],
            anchor="w",
        ).grid(row=1, column=0, pady=(2, 0), sticky="ew")
        ctk.CTkLabel(
            top,
            text="Échap pour fermer",
            font=("Segoe UI Semibold", 8),
            text_color=COLORS["muted_2"],
        ).grid(row=0, column=1, rowspan=2, padx=(10, 0))

        self.query = tk.StringVar()
        self.entry = ctk.CTkEntry(
            self,
            textvariable=self.query,
            placeholder_text="Ex. Cutlass, Attrition, armure, CenterMass…",
            height=44,
            corner_radius=11,
            border_width=1,
            border_color=COLORS["accent"],
            fg_color=COLORS["panel"],
            text_color=COLORS["text"],
            placeholder_text_color=COLORS["muted_2"],
            font=("Segoe UI", 12),
        )
        self.entry.grid(row=1, column=0, padx=24, pady=(0, 12), sticky="ew")
        self.entry.bind("<KeyRelease>", self._schedule)
        self.entry.bind("<Down>", self._focus_results)
        self.entry.bind("<Return>", lambda _event: self.open_selected())

        self.table = TreeTable(
            self,
            [
                ("kind", "TYPE", 95, "center"),
                ("name", "NOM", 220, "w"),
                ("detail", "DÉTAIL", 245, "w"),
                ("price", "MEILLEUR PRIX", 135, "e"),
                ("location", "LIEU", 220, "w"),
            ],
            on_double_click=lambda _iid: self.open_selected(),
        )
        self.table.grid(row=2, column=0, padx=24, pady=(0, 12), sticky="nsew")
        self.result_label = ctk.CTkLabel(
            self,
            text="Commencez à taper pour rechercher.",
            font=("Segoe UI", 9),
            text_color=COLORS["muted"],
            anchor="w",
        )
        self.result_label.grid(row=3, column=0, padx=28, pady=(0, 18), sticky="ew")

        self.bind("<Escape>", lambda _event: self.destroy())
        self.bind("<Control-k>", lambda _event: self.entry.focus_set())
        self.refresh_results()
        self.after(80, self.entry.focus_set)

    def _schedule(self, _event: Any = None) -> None:
        if self._debounce:
            self.after_cancel(self._debounce)
        self._debounce = self.after(180, self.refresh_results)

    def _focus_results(self, _event: Any = None) -> str:
        children = self.table.tree.get_children()
        if children:
            self.table.select(children[0])
            self.table.tree.focus_set()
        return "break"

    def refresh_results(self) -> None:
        query = self.query.get().strip()
        if len(query) >= 2:
            rows = self.app.repo.global_search(query)
        elif not query:
            rows = self._recent_results()
        else:
            rows = []
        self.rows = {_entity_iid(row["kind"], row["id"]): row for row in rows}
        self.table.populate(
            (
                iid,
                (
                    KIND_LABELS.get(row["kind"], row["kind"]),
                    row["name"],
                    row.get("subtitle") or "—",
                    format_price(row.get("price_min")),
                    row.get("location") or "—",
                ),
                False,
            )
            for iid, row in self.rows.items()
        )
        if not query:
            label = (
                "Consultés récemment · commencez à taper pour rechercher"
                if rows
                else "Commencez à taper pour rechercher."
            )
        elif len(query) < 2:
            label = "Saisissez au moins deux caractères."
        else:
            label = f"{len(rows)} résultat(s) · Entrée ou double-clic pour ouvrir"
        self.result_label.configure(text=label)

    def _recent_results(self) -> list[dict[str, Any]]:
        resolved = self.app.repo.resolve_entities(self.app.user_store.recent_entries(12))
        rows: list[dict[str, Any]] = []
        for row in resolved:
            detail = row.get("detail") or {}
            if row.get("kind") == "vehicle":
                subtitle = " • ".join(
                    value
                    for value in (
                        detail.get("manufacturer"),
                        detail.get("vehicle_class"),
                        detail.get("roles"),
                    )
                    if value
                )
            else:
                subtitle = " • ".join(
                    value
                    for value in (
                        translate_category(detail.get("category")),
                        detail.get("manufacturer"),
                    )
                    if value
                )
            rows.append(
                {
                    "kind": row["kind"],
                    "id": int(row["entity_id"]),
                    "name": row["name"],
                    "subtitle": subtitle,
                    "price_min": row.get("price_min"),
                    "location": row.get("location"),
                }
            )
        return rows

    def open_selected(self) -> None:
        parsed = _parse_iid(self.table.selected_id())
        if not parsed and self.rows:
            parsed = _parse_iid(next(iter(self.rows)))
        if not parsed:
            return
        self.destroy()
        self.app.open_entity(*parsed)


class LocationsPage(AdvancedPage):
    title = "Boutiques & lieux"
    subtitle = "Explorez chaque commerce et son inventaire achetable en jeu."

    def __init__(self, master: Any, app: Any):
        super().__init__(master, app)
        self._loaded = False
        self._debounce: str | None = None
        self._query_generation = 0
        self._saved_filter_state: dict[str, Any] = {}
        self.rows: dict[int, dict[str, Any]] = {}
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        panel = ctk.CTkFrame(
            self,
            fg_color=COLORS["panel"],
            corner_radius=14,
            border_width=1,
            border_color=COLORS["border"],
        )
        panel.grid(row=0, column=0, pady=(0, 12), sticky="ew")
        panel.grid_columnconfigure(0, weight=1)
        self.search_var = tk.StringVar()
        self.search_entry = ctk.CTkEntry(
            panel,
            textvariable=self.search_var,
            placeholder_text="Rechercher une boutique, une ville, une station ou une société…",
            height=38,
            corner_radius=9,
            border_color=COLORS["border"],
            fg_color=COLORS["panel_alt"],
            text_color=COLORS["text"],
        )
        self.search_entry.grid(row=0, column=0, padx=14, pady=13, sticky="ew")
        self.search_entry.bind("<KeyRelease>", self._schedule_refresh)
        self.result_label = ctk.CTkLabel(panel, text="", width=105, text_color=COLORS["muted"], font=("Segoe UI", 9))
        self.result_label.grid(row=0, column=1, padx=8)
        self.system_var = tk.StringVar(value="Tous")
        self.planet_var = tk.StringVar(value="Toutes")
        saved = self.app.user_store.get_json_setting("filters:locations", {})
        if isinstance(saved, dict):
            self._saved_filter_state = saved
            self.search_var.set(str(saved.get("search") or ""))
            self.system_var.set(str(saved.get("system") or "Tous"))
            self.planet_var.set(str(saved.get("planet") or "Toutes"))
        self.system_wrap = ctk.CTkFrame(panel, fg_color="transparent")
        self.system_wrap.grid(row=0, column=2, padx=5, pady=8)
        self.planet_wrap = ctk.CTkFrame(panel, fg_color="transparent")
        self.planet_wrap.grid(row=0, column=3, padx=(5, 14), pady=8)

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew")
        content.grid_rowconfigure(0, weight=1)
        content.grid_columnconfigure(0, weight=3, minsize=460)
        content.grid_columnconfigure(1, weight=2, minsize=300)
        self.table = TreeTable(
            content,
            [
                ("name", "BOUTIQUE", 210, "w"),
                ("system", "SYSTÈME", 85, "center"),
                ("planet", "PLANÈTE", 100, "w"),
                ("items", "OBJETS", 70, "center"),
                ("ships", "VAISSEAUX", 85, "center"),
            ],
            on_select=self._show_detail,
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
        )
        self.detail.grid(row=0, column=1, sticky="nsew")
        self.detail.grid_columnconfigure(0, weight=1)
        self._empty_detail()

    def _schedule_refresh(self, _event: Any = None) -> None:
        if self._debounce:
            self.after_cancel(self._debounce)
        delay = 340 if self.app.performance_mode else 220
        self._debounce = self.after(delay, self.refresh_data)

    def _build_filters(self) -> None:
        for wrap in (self.system_wrap, self.planet_wrap):
            for child in wrap.winfo_children():
                child.destroy()
        options = self.app.repo.location_filter_options()
        labelled_combo(
            self.system_wrap,
            label="Système",
            variable=self.system_var,
            values=["Tous"] + options["systems"],
            command=lambda _value: self.refresh_data(),
            width=145,
        ).pack()
        labelled_combo(
            self.planet_wrap,
            label="Planète",
            variable=self.planet_var,
            values=["Toutes"] + options["planets"],
            command=lambda _value: self.refresh_data(),
            width=145,
        ).pack()

    def on_show(self) -> None:
        if not self._loaded:
            self._build_filters()
            self._loaded = True
        self.refresh_data()

    def refresh_data(self, select_id: int | None = None) -> None:
        self._debounce = None
        if not self._loaded:
            return
        query = {
            "search": self.search_var.get(),
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
        self._save_filters()
        results: queue.SimpleQueue[tuple[list[dict[str, Any]] | None, Exception | None]] = queue.SimpleQueue()

        def worker() -> None:
            try:
                results.put((self.app.repo.search_terminals(**query), None))
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
            self._apply_location_results(rows or [], error, generation, selected_before)

        threading.Thread(target=worker, name="asteriax-locations", daemon=True).start()
        self.after(35, poll)

    def _apply_location_results(
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
        self.rows = {int(row["id"]): row for row in rows}
        self.table.populate(
            (
                str(row["id"]),
                (
                    row["name"],
                    row.get("star_system") or "—",
                    row.get("planet") or row.get("moon") or "—",
                    row.get("item_count") or 0,
                    row.get("vehicle_count") or 0,
                ),
                False,
            )
            for row in rows
        )
        self.result_label.configure(text=f"{len(rows)} lieux")
        target = select_id if select_id in self.rows else None
        if target is None and rows and not self.app.performance_mode:
            target = int(rows[0]["id"])
        if target is not None:
            self.table.select(str(target))
        elif rows:
            self._empty_detail("Sélectionnez une boutique", "Les lieux sont chargés par blocs pour garder l’interface fluide.")
        else:
            self._empty_detail("Aucune boutique", "Modifiez la recherche ou les filtres.")

    def _save_filters(self) -> None:
        sort_column, sort_reverse = self.table.sort_state() if hasattr(self, "table") else (None, False)
        self.app.user_store.set_json_setting(
            "filters:locations",
            {
                "search": self.search_var.get(),
                "system": self.system_var.get(),
                "planet": self.planet_var.get(),
                "sort_column": sort_column,
                "sort_reverse": sort_reverse,
            },
        )

    def open_entity(self, terminal_id: int) -> None:
        if not self._loaded:
            self._build_filters()
            self._loaded = True
        self.search_var.set("")
        self.system_var.set("Tous")
        self.planet_var.set("Toutes")
        self.refresh_data(select_id=int(terminal_id))

    def _clear_detail(self) -> None:
        for child in self.detail.winfo_children():
            child.destroy()

    def _empty_detail(self, title: str = "Sélectionnez une boutique", message: str = "Son trajet et tout son inventaire apparaîtront ici.") -> None:
        self._clear_detail()
        EmptyState(self.detail, title, message).grid(row=0, column=0, sticky="nsew")

    def _show_detail(self, iid: str) -> None:
        if not iid:
            return
        terminal_id = int(iid)
        detail = self.rows.get(terminal_id) or self.app.repo.terminal_detail(terminal_id)
        if not detail:
            self._empty_detail("Boutique introuvable", "La base a peut-être été mise à jour.")
            return
        inventory = self.app.repo.terminal_inventory(terminal_id)
        self._clear_detail()
        ctk.CTkLabel(
            self.detail,
            text=(detail.get("company") or "COMMERCE").upper(),
            font=("Segoe UI Semibold", 8),
            text_color=COLORS["accent"],
            anchor="w",
        ).grid(row=0, column=0, padx=16, pady=(16, 4), sticky="ew")
        ctk.CTkLabel(
            self.detail,
            text=detail.get("name") or "Boutique",
            wraplength=310,
            justify="left",
            font=("Segoe UI Semibold", 19),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=1, column=0, padx=16, sticky="ew")
        route = location_label(detail, include_shop=False)
        ctk.CTkLabel(
            self.detail,
            text=route,
            wraplength=310,
            justify="left",
            font=("Segoe UI", 9),
            text_color=COLORS["muted"],
            anchor="w",
        ).grid(row=2, column=0, padx=16, pady=(5, 10), sticky="ew")
        ctk.CTkButton(
            self.detail,
            text="Copier le trajet",
            command=lambda: self.app.copy_to_clipboard(route, "Trajet copié"),
            height=32,
            corner_radius=8,
            fg_color="transparent",
            hover_color=COLORS["panel_hover"],
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["accent"],
        ).grid(row=3, column=0, padx=16, pady=(0, 13), sticky="ew")
        ctk.CTkLabel(
            self.detail,
            text=f"INVENTAIRE  ·  {len(inventory)}",
            font=("Segoe UI Semibold", 8),
            text_color=COLORS["muted"],
            anchor="w",
        ).grid(row=4, column=0, padx=16, pady=(0, 7), sticky="ew")
        inv_table = TreeTable(
            self.detail,
            [
                ("name", "OBJET", 165, "w"),
                ("type", "TYPE", 90, "w"),
                ("price", "PRIX", 110, "e"),
            ],
            on_double_click=lambda selected: self.app.open_entity(*(_parse_iid(selected) or ("", 0))),
        )
        inv_table.grid(row=5, column=0, padx=16, pady=(0, 16), sticky="ew")
        inv_table.configure(height=min(520, max(170, 37 * min(len(inventory), 12))))
        inv_table.populate(
            (
                _entity_iid(row["kind"], row["id"]),
                (row["name"], translate_category(row.get("category")), format_price(row.get("price_buy"))),
                False,
            )
            for row in inventory
        )


class ShoppingPage(AdvancedPage):
    title = "Liste de courses"
    subtitle = "Budget total et itinéraire regroupé selon les meilleurs prix."

    def __init__(self, master: Any, app: Any):
        super().__init__(master, app)
        self.rows: dict[str, dict[str, Any]] = {}
        self.plan: dict[str, Any] = {}
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        summary = ctk.CTkFrame(
            self,
            fg_color=COLORS["panel"],
            corner_radius=14,
            border_width=1,
            border_color=COLORS["border"],
        )
        summary.grid(row=0, column=0, pady=(0, 12), sticky="ew")
        summary.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(summary, text="BUDGET TOTAL", font=("Segoe UI Semibold", 8), text_color=COLORS["muted_2"]).grid(
            row=0, column=0, padx=(16, 8), pady=(11, 0), sticky="w"
        )
        self.total_label = ctk.CTkLabel(summary, text="0 aUEC", font=("Segoe UI Semibold", 23), text_color=COLORS["accent"])
        self.total_label.grid(row=1, column=0, padx=(16, 8), pady=(0, 11), sticky="w")
        self.count_label = ctk.CTkLabel(summary, text="", font=("Segoe UI", 9), text_color=COLORS["muted"])
        self.count_label.grid(row=0, column=1, rowspan=2, padx=10, sticky="w")
        ctk.CTkButton(
            summary,
            text="Copier l’itinéraire",
            command=self.copy_route,
            width=150,
            height=34,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color=COLORS["background"],
        ).grid(row=0, column=2, rowspan=2, padx=8)
        ctk.CTkButton(
            summary,
            text="Vider",
            command=self.clear_all,
            width=80,
            height=34,
            fg_color="transparent",
            border_width=1,
            border_color=COLORS["border"],
            hover_color=COLORS["panel_hover"],
            text_color=COLORS["muted"],
        ).grid(row=0, column=3, rowspan=2, padx=(0, 14))

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew")
        content.grid_rowconfigure(0, weight=1)
        content.grid_columnconfigure(0, weight=3, minsize=500)
        content.grid_columnconfigure(1, weight=2, minsize=300)
        left = ctk.CTkFrame(content, fg_color="transparent")
        left.grid(row=0, column=0, padx=(0, 10), sticky="nsew")
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(0, weight=1)
        self.table = TreeTable(
            left,
            [
                ("name", "ACHAT", 190, "w"),
                ("type", "TYPE", 80, "center"),
                ("qty", "QTÉ", 55, "center"),
                ("unit", "UNITAIRE", 115, "e"),
                ("total", "TOTAL", 125, "e"),
                ("status", "ÉTAT", 70, "center"),
            ],
            on_double_click=lambda iid: self.open_iid(iid),
        )
        self.table.grid(row=0, column=0, sticky="nsew")
        controls = ctk.CTkFrame(left, fg_color="transparent")
        controls.grid(row=1, column=0, pady=(8, 0), sticky="ew")
        for column in range(6):
            controls.grid_columnconfigure(column, weight=1)
        actions = [
            ("− Quantité", lambda: self.change_quantity(-1)),
            ("+ Quantité", lambda: self.change_quantity(1)),
            ("✓ Acheté", self.toggle_purchased),
            ("Ouvrir", lambda: self.open_iid(self.table.selected_id())),
            ("Retirer", self.remove_selected),
            ("Effacer achetés", self.clear_purchased),
        ]
        for column, (label, command) in enumerate(actions):
            ctk.CTkButton(
                controls,
                text=label,
                command=command,
                height=32,
                corner_radius=8,
                fg_color=COLORS["panel"],
                hover_color=COLORS["panel_hover"],
                border_width=1,
                border_color=COLORS["border"],
                text_color=COLORS["text"],
                font=("Segoe UI Semibold", 8),
            ).grid(row=0, column=column, padx=(0 if column == 0 else 3, 0 if column == 5 else 3), sticky="ew")

        self.route = ctk.CTkScrollableFrame(
            content,
            fg_color=COLORS["panel"],
            corner_radius=14,
            border_width=1,
            border_color=COLORS["border"],
        )
        self.route.grid(row=0, column=1, sticky="nsew")
        self.route.grid_columnconfigure(0, weight=1)

    def refresh_data(self) -> None:
        entries = self.app.user_store.shopping_entries()
        self.plan = self.app.repo.shopping_plan(entries)
        resolved = self.plan.get("entries", [])
        self.rows = {_entity_iid(row["kind"], row["entity_id"]): row for row in resolved}
        self.table.populate(
            (
                iid,
                (
                    row["name"],
                    KIND_LABELS.get(row["kind"], row["kind"]),
                    row.get("quantity") or 1,
                    format_price(row.get("price_min")),
                    format_price(float(row.get("price_min") or 0) * int(row.get("quantity") or 1)),
                    "Acheté" if row.get("purchased") else "À faire",
                ),
                bool(row.get("purchased")),
            )
            for iid, row in self.rows.items()
        )
        self.total_label.configure(text=format_price(self.plan.get("total")) if self.plan.get("total") else "0 aUEC")
        pending = sum(1 for row in resolved if not row.get("purchased"))
        self.count_label.configure(text=f"{len(resolved)} ligne(s) · {pending} à acheter · {len(self.plan.get('groups', []))} étape(s)")
        self._render_route()

    def _render_route(self) -> None:
        for child in self.route.winfo_children():
            child.destroy()
        groups = self.plan.get("groups", [])
        if not groups:
            EmptyState(
                self.route,
                "Liste vide",
                "Ajoutez des objets ou des vaisseaux depuis leur fiche pour préparer votre tournée.",
            ).grid(row=0, column=0, sticky="nsew")
            return
        ctk.CTkLabel(
            self.route,
            text="ITINÉRAIRE CONSEILLÉ",
            font=("Segoe UI Semibold", 9),
            text_color=COLORS["accent"],
            anchor="w",
        ).grid(row=0, column=0, padx=16, pady=(16, 4), sticky="ew")
        ctk.CTkLabel(
            self.route,
            text="Meilleurs prix regroupés par système et planète.",
            font=("Segoe UI", 8),
            text_color=COLORS["muted"],
            anchor="w",
        ).grid(row=1, column=0, padx=16, pady=(0, 12), sticky="ew")
        for index, group in enumerate(groups, start=1):
            card = ctk.CTkFrame(self.route, fg_color=COLORS["panel_alt"], corner_radius=10)
            card.grid(row=index + 1, column=0, padx=14, pady=(0, 8), sticky="ew")
            card.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(
                card,
                text=f"ÉTAPE {index}",
                font=("Segoe UI Semibold", 7),
                text_color=COLORS["accent"],
                anchor="w",
            ).grid(row=0, column=0, padx=12, pady=(9, 1), sticky="ew")
            ctk.CTkLabel(
                card,
                text=group["label"],
                wraplength=290,
                justify="left",
                font=("Segoe UI Semibold", 10),
                text_color=COLORS["text"],
                anchor="w",
            ).grid(row=1, column=0, padx=12, sticky="ew")
            lines = "\n".join(f"{line['quantity']}× {line['name']}" for line in group["lines"])
            ctk.CTkLabel(
                card,
                text=lines,
                wraplength=290,
                justify="left",
                font=("Segoe UI", 8),
                text_color=COLORS["muted"],
                anchor="w",
            ).grid(row=2, column=0, padx=12, pady=(4, 2), sticky="ew")
            ctk.CTkLabel(
                card,
                text=f"Sous-total : {format_price(group['subtotal'])}",
                font=("Segoe UI Semibold", 8),
                text_color=COLORS["warning"],
                anchor="w",
            ).grid(row=3, column=0, padx=12, pady=(2, 9), sticky="ew")

    def selected(self) -> tuple[str, int] | None:
        return _parse_iid(self.table.selected_id())

    def change_quantity(self, delta: int) -> None:
        parsed = self.selected()
        if not parsed:
            return
        row = self.rows.get(_entity_iid(*parsed), {})
        self.app.user_store.set_shopping_quantity(parsed[0], parsed[1], int(row.get("quantity") or 1) + delta)
        self.refresh_data()

    def toggle_purchased(self) -> None:
        parsed = self.selected()
        if parsed:
            self.app.user_store.toggle_shopping_purchased(*parsed)
            self.refresh_data()

    def remove_selected(self) -> None:
        parsed = self.selected()
        if parsed:
            self.app.user_store.remove_from_shopping(*parsed)
            self.refresh_data()

    def clear_purchased(self) -> None:
        self.app.user_store.clear_shopping(purchased_only=True)
        self.refresh_data()

    def clear_all(self) -> None:
        if self.rows and messagebox.askyesno("Vider la liste", "Supprimer toute la liste de courses ?", parent=self):
            self.app.user_store.clear_shopping()
            self.refresh_data()

    def open_iid(self, iid: str) -> None:
        parsed = _parse_iid(iid)
        if parsed:
            self.app.open_entity(*parsed)

    def copy_route(self) -> None:
        groups = self.plan.get("groups", [])
        if not groups:
            self.app.show_notice("La liste de courses est vide.", COLORS["warning"])
            return
        lines = [f"{APP_NAME} — tournée d’achat", f"Budget : {format_price(self.plan.get('total'))}", ""]
        for index, group in enumerate(groups, start=1):
            lines.append(f"{index}. {group['label']}")
            lines.extend(f"   • {line['quantity']}× {line['name']} — {format_price(line['total'])}" for line in group["lines"])
            lines.append("")
        self.app.copy_to_clipboard("\n".join(lines).strip(), "Itinéraire copié")


class ComparePage(AdvancedPage):
    title = "Comparateur"
    subtitle = "Comparez jusqu’à trois modèles ou équipements côte à côte."

    def __init__(self, master: Any, app: Any):
        super().__init__(master, app)
        self.kind = "vehicle"
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, pady=(0, 12), sticky="ew")
        top.grid_columnconfigure(1, weight=1)
        self.segment = ctk.CTkSegmentedButton(
            top,
            values=["Vaisseaux", "Objets"],
            command=self._change_kind,
            selected_color=COLORS["accent"],
            selected_hover_color=COLORS["accent_hover"],
            unselected_color=COLORS["panel"],
            unselected_hover_color=COLORS["panel_hover"],
            text_color=COLORS["background"],
        )
        self.segment.grid(row=0, column=0, sticky="w")
        self.segment.set("Vaisseaux")
        ctk.CTkLabel(
            top,
            text="Ajoutez un élément depuis sa fiche avec le bouton Comparer.",
            font=("Segoe UI", 9),
            text_color=COLORS["muted"],
        ).grid(row=0, column=1, padx=14, sticky="w")
        ctk.CTkButton(
            top,
            text="Vider la comparaison",
            command=self.clear,
            width=145,
            height=33,
            fg_color="transparent",
            border_width=1,
            border_color=COLORS["border"],
            hover_color=COLORS["panel_hover"],
            text_color=COLORS["muted"],
        ).grid(row=0, column=2, sticky="e")
        self.summary_label = ctk.CTkLabel(
            self,
            text="",
            height=34,
            corner_radius=9,
            fg_color=COLORS["accent_dark"],
            text_color=COLORS["accent"],
            font=("Segoe UI Semibold", 9),
            anchor="w",
        )
        self.summary_label.grid(row=1, column=0, pady=(0, 10), sticky="ew")
        self.cards = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0)
        self.cards.grid(row=2, column=0, sticky="nsew")

    def _change_kind(self, value: str) -> None:
        self.kind = "vehicle" if value == "Vaisseaux" else "item"
        self.refresh_data()

    def refresh_data(self) -> None:
        for child in self.cards.winfo_children():
            child.destroy()
        ids = self.app.user_store.comparison_ids(self.kind)
        rows = self.app.repo.resolve_entities(
            {"kind": self.kind, "entity_id": entity_id} for entity_id in ids
        )
        if not rows:
            self.summary_label.configure(
                text="  Ajoutez deux ou trois éléments pour afficher les écarts de prix et de capacité."
            )
            self.cards.grid_columnconfigure(0, weight=1)
            EmptyState(
                self.cards,
                "Rien à comparer",
                "Ouvrez une fiche puis cliquez sur Comparer. Vous pouvez ajouter jusqu’à trois éléments.",
            ).grid(row=0, column=0, sticky="nsew")
            return
        prices = [
            float(row.get("price_min") or 0)
            for row in rows
            if float(row.get("price_min") or 0) > 0
        ]
        cheapest = min(prices) if prices else 0.0
        cargo_values = [float((row.get("detail") or {}).get("scu") or 0) for row in rows]
        largest_cargo = max(cargo_values, default=0.0)
        self.summary_label.configure(text=self._comparison_summary(rows, cheapest, largest_cargo))
        for column in range(3):
            self.cards.grid_columnconfigure(column, weight=1, uniform="compare")
        for column, row in enumerate(rows):
            detail = row["detail"]
            row_price = float(row.get("price_min") or 0)
            is_cheapest = bool(cheapest and row_price == cheapest)
            has_largest_cargo = bool(
                self.kind == "vehicle"
                and largest_cargo
                and float(detail.get("scu") or 0) == largest_cargo
            )
            card = ctk.CTkFrame(
                self.cards,
                fg_color=COLORS["panel"],
                corner_radius=14,
                border_width=1,
                border_color=COLORS["accent"] if is_cheapest else COLORS["border"],
            )
            card.grid(row=0, column=column, padx=(0 if column == 0 else 5, 0 if column == len(rows) - 1 else 5), sticky="nsew")
            card.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(
                card,
                text="MEILLEUR PRIX" if is_cheapest else KIND_LABELS[self.kind].upper(),
                font=("Segoe UI Semibold", 8),
                text_color=COLORS["accent"],
                anchor="w",
            ).grid(row=0, column=0, padx=15, pady=(15, 3), sticky="ew")
            ctk.CTkLabel(
                card,
                text=row["name"],
                wraplength=210,
                justify="left",
                font=("Segoe UI Semibold", 17),
                text_color=COLORS["text"],
                anchor="w",
            ).grid(row=1, column=0, padx=15, sticky="ew")
            if self.kind == "vehicle":
                metrics = [
                    ("Constructeur", detail.get("manufacturer"), False),
                    ("Classe", detail.get("vehicle_class"), False),
                    ("Rôle", detail.get("roles"), False),
                    ("Cargo", f"{detail.get('scu'):g} SCU" if detail.get("scu") else "—", has_largest_cargo),
                    ("Équipage", detail.get("crew"), False),
                    ("Longueur", f"{detail.get('length'):g} m" if detail.get("length") else "—", False),
                    ("Pad", detail.get("pad_type"), False),
                ]
            else:
                metrics = [
                    ("Fabricant", detail.get("manufacturer"), False),
                    ("Famille", translate_section(detail.get("section")), False),
                    ("Catégorie", translate_category(detail.get("category")), False),
                    ("Taille", f"S{detail.get('size')}" if detail.get("size") else "—", False),
                    ("Qualité", detail.get("quality") or "—", False),
                    ("Version", detail.get("game_version") or "—", False),
                ]
            row_index = 2
            for label, value, highlighted in metrics:
                metric = ctk.CTkFrame(card, fg_color="transparent")
                metric.grid(row=row_index, column=0, padx=15, pady=(10 if row_index == 2 else 2, 0), sticky="ew")
                metric.grid_columnconfigure(1, weight=1)
                ctk.CTkLabel(metric, text=label.upper(), font=("Segoe UI Semibold", 7), text_color=COLORS["muted_2"]).grid(row=0, column=0, sticky="w")
                ctk.CTkLabel(
                    metric,
                    text=str(value or "—"),
                    wraplength=125,
                    justify="right",
                    font=("Segoe UI Semibold" if highlighted else "Segoe UI", 8),
                    text_color=COLORS["accent"] if highlighted else COLORS["text"],
                ).grid(row=0, column=1, sticky="e")
                row_index += 1
            price = ctk.CTkFrame(card, fg_color=COLORS["accent_dark"], corner_radius=9)
            price.grid(row=row_index, column=0, padx=15, pady=(13, 6), sticky="ew")
            ctk.CTkLabel(price, text=format_price(row.get("price_min")), font=("Segoe UI Semibold", 15), text_color=COLORS["text"]).pack(pady=(7, 0))
            if cheapest and row_price > cheapest:
                ctk.CTkLabel(
                    price,
                    text=f"+ {format_price(row_price - cheapest)} par rapport au moins cher",
                    font=("Segoe UI Semibold", 7),
                    text_color=COLORS["warning"],
                ).pack(pady=(1, 0))
            ctk.CTkLabel(price, text=row.get("location") or "—", wraplength=225, justify="center", font=("Segoe UI", 7), text_color=COLORS["muted"]).pack(padx=7, pady=(2, 0))
            freshness = price_freshness_label(row.get("price_date"))
            ctk.CTkLabel(
                price,
                text=freshness,
                font=("Segoe UI Semibold", 7),
                text_color=COLORS["warning"] if "revérifier" in freshness else COLORS["muted_2"],
            ).pack(padx=7, pady=(1, 7))
            buttons = ctk.CTkFrame(card, fg_color="transparent")
            buttons.grid(row=row_index + 1, column=0, padx=15, pady=(2, 15), sticky="ew")
            buttons.grid_columnconfigure((0, 1), weight=1)
            ctk.CTkButton(
                buttons,
                text="Ouvrir",
                command=lambda k=self.kind, i=row["entity_id"]: self.app.open_entity(k, i),
                height=31,
                fg_color=COLORS["accent"],
                hover_color=COLORS["accent_hover"],
                text_color=COLORS["background"],
            ).grid(row=0, column=0, padx=(0, 3), sticky="ew")
            ctk.CTkButton(
                buttons,
                text="Retirer",
                command=lambda k=self.kind, i=row["entity_id"]: self.remove(k, i),
                height=31,
                fg_color="transparent",
                border_width=1,
                border_color=COLORS["border"],
                hover_color=COLORS["panel_hover"],
                text_color=COLORS["muted"],
            ).grid(row=0, column=1, padx=(3, 0), sticky="ew")

    def remove(self, kind: str, entity_id: int) -> None:
        self.app.user_store.remove_comparison(kind, entity_id)
        self.refresh_data()

    def clear(self) -> None:
        self.app.user_store.clear_comparisons(self.kind)
        self.refresh_data()

    def _comparison_summary(
        self,
        rows: list[dict[str, Any]],
        cheapest: float,
        largest_cargo: float,
    ) -> str:
        if len(rows) == 1:
            return "  Ajoutez encore un élément pour calculer les écarts."
        parts: list[str] = []
        if cheapest:
            cheapest_row = next(row for row in rows if float(row.get("price_min") or 0) == cheapest)
            parts.append(f"Meilleur prix : {cheapest_row['name']} ({format_price(cheapest)})")
        if self.kind == "vehicle" and largest_cargo:
            cargo_row = next(
                row for row in rows if float((row.get("detail") or {}).get("scu") or 0) == largest_cargo
            )
            parts.append(f"Plus grand cargo : {cargo_row['name']} ({largest_cargo:g} SCU)")
        return "  " + "   •   ".join(parts or ["Comparaison prête"])


class LoadoutPage(AdvancedPage):
    title = "Planificateur de loadout"
    subtitle = "Préparez l’équipement d’un vaisseau et son budget d’achat."

    def __init__(self, master: Any, app: Any):
        super().__init__(master, app)
        self.vehicle_map: dict[str, int] = {}
        self.item_rows: dict[int, dict[str, Any]] = {}
        self.loadout_rows: dict[int, dict[str, Any]] = {}
        self._loaded = False
        self._debounce: str | None = None
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        ship_panel = ctk.CTkFrame(
            self,
            fg_color=COLORS["panel"],
            corner_radius=14,
            border_width=1,
            border_color=COLORS["border"],
        )
        ship_panel.grid(row=0, column=0, pady=(0, 9), sticky="ew")
        ship_panel.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            ship_panel,
            text="VAISSEAU À ÉQUIPER",
            font=("Segoe UI Semibold", 8),
            text_color=COLORS["muted_2"],
        ).grid(row=0, column=0, padx=(15, 10), pady=13)
        self.vehicle_var = tk.StringVar(value="Choisir un vaisseau…")
        self.vehicle_combo = ctk.CTkComboBox(
            ship_panel,
            variable=self.vehicle_var,
            values=["Choisir un vaisseau…"],
            command=self._select_vehicle,
            height=36,
            state="readonly",
            fg_color=COLORS["panel_alt"],
            border_color=COLORS["border"],
            button_color=COLORS["border"],
            dropdown_fg_color=COLORS["panel_alt"],
            dropdown_hover_color=COLORS["accent_dark"],
            text_color=COLORS["text"],
        )
        self.vehicle_combo.grid(row=0, column=1, padx=5, pady=10, sticky="ew")
        self.budget_label = ctk.CTkLabel(ship_panel, text="0 aUEC", width=145, font=("Segoe UI Semibold", 16), text_color=COLORS["accent"])
        self.budget_label.grid(row=0, column=2, padx=10)
        ctk.CTkButton(
            ship_panel,
            text="Ajouter au panier",
            command=self.add_all_to_shopping,
            width=135,
            height=34,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color=COLORS["background"],
        ).grid(row=0, column=3, padx=(0, 14))

        warning = ctk.CTkFrame(self, fg_color="#2A2214", corner_radius=9, border_width=1, border_color="#6B5425")
        warning.grid(row=1, column=0, pady=(0, 9), sticky="ew")
        ctk.CTkLabel(
            warning,
            text=(
                "Compatibilité : la source de prix ne fournit pas tous les hardpoints. "
                "Le planificateur filtre par famille et taille sans inventer une compatibilité technique ; vérifiez le montage en jeu."
            ),
            wraplength=980,
            justify="left",
            font=("Segoe UI", 8),
            text_color="#D8C69E",
            anchor="w",
        ).pack(fill="x", padx=12, pady=8)

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=2, column=0, sticky="nsew")
        content.grid_rowconfigure(2, weight=1)
        content.grid_columnconfigure((0, 1), weight=1, uniform="loadout")
        left_filters = ctk.CTkFrame(content, fg_color=COLORS["panel"], corner_radius=12, border_width=1, border_color=COLORS["border"])
        left_filters.grid(row=0, column=0, padx=(0, 5), pady=(0, 8), sticky="ew")
        left_filters.grid_columnconfigure(0, weight=1)
        self.search_var = tk.StringVar()
        search = ctk.CTkEntry(
            left_filters,
            textvariable=self.search_var,
            placeholder_text="Rechercher un composant, canon, missile…",
            height=34,
            fg_color=COLORS["panel_alt"],
            border_color=COLORS["border"],
            text_color=COLORS["text"],
        )
        search.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        search.bind("<KeyRelease>", self._schedule_refresh)
        self.category_var = tk.StringVar(value="Toutes")
        self.size_var = tk.StringVar(value="Toutes")
        self.category_wrap = ctk.CTkFrame(left_filters, fg_color="transparent")
        self.category_wrap.grid(row=0, column=1, padx=4, pady=6)
        self.size_wrap = ctk.CTkFrame(left_filters, fg_color="transparent")
        self.size_wrap.grid(row=0, column=2, padx=(4, 10), pady=6)
        SectionTitle(content, "Équipements disponibles", "Double-cliquez ou utilisez Ajouter.").grid(row=1, column=0, padx=(4, 5), pady=(4, 8), sticky="sw")
        SectionTitle(content, "Loadout préparé", "Quantités et coût selon les meilleurs prix.").grid(row=1, column=1, padx=(10, 0), pady=(4, 8), sticky="sw")

        left = ctk.CTkFrame(content, fg_color="transparent")
        left.grid(row=2, column=0, padx=(0, 5), sticky="nsew")
        left.grid_rowconfigure(0, weight=1)
        left.grid_columnconfigure(0, weight=1)
        self.items_table = TreeTable(
            left,
            [
                ("name", "ÉQUIPEMENT", 190, "w"),
                ("category", "CATÉGORIE", 120, "w"),
                ("size", "TAILLE", 60, "center"),
                ("price", "PRIX", 110, "e"),
            ],
            on_double_click=lambda _iid: self.add_selected(),
        )
        self.items_table.grid(row=0, column=0, sticky="nsew")
        ctk.CTkButton(
            left,
            text="+ Ajouter au loadout",
            command=self.add_selected,
            height=34,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color=COLORS["background"],
        ).grid(row=1, column=0, pady=(8, 0), sticky="ew")

        right = ctk.CTkFrame(content, fg_color="transparent")
        right.grid(row=2, column=1, padx=(5, 0), sticky="nsew")
        right.grid_rowconfigure(0, weight=1)
        right.grid_columnconfigure(0, weight=1)
        self.loadout_table = TreeTable(
            right,
            [
                ("name", "ÉQUIPEMENT", 190, "w"),
                ("qty", "QTÉ", 55, "center"),
                ("unit", "UNITAIRE", 110, "e"),
                ("total", "TOTAL", 115, "e"),
            ],
            on_double_click=lambda iid: self.app.open_item(int(iid)) if iid else None,
        )
        self.loadout_table.grid(row=0, column=0, sticky="nsew")
        buttons = ctk.CTkFrame(right, fg_color="transparent")
        buttons.grid(row=1, column=0, pady=(8, 0), sticky="ew")
        buttons.grid_columnconfigure((0, 1, 2, 3), weight=1)
        for column, (label, command) in enumerate(
            [("− Qté", lambda: self.change_loadout(-1)), ("+ Qté", lambda: self.change_loadout(1)), ("Retirer", self.remove_loadout), ("Vider", self.clear_loadout)]
        ):
            ctk.CTkButton(
                buttons,
                text=label,
                command=command,
                height=34,
                fg_color=COLORS["panel"],
                hover_color=COLORS["panel_hover"],
                border_width=1,
                border_color=COLORS["border"],
                text_color=COLORS["text"],
            ).grid(row=0, column=column, padx=(0 if column == 0 else 3, 0 if column == 3 else 3), sticky="ew")

    def _schedule_refresh(self, _event: Any = None) -> None:
        if self._debounce:
            self.after_cancel(self._debounce)
        self._debounce = self.after(220, self.refresh_candidates)

    def on_show(self) -> None:
        if not self._loaded:
            vehicles = self.app.repo.search_vehicles()
            self.vehicle_map = {f"{row['name']} — {row.get('manufacturer') or '—'}": int(row["id"]) for row in vehicles}
            self.vehicle_combo.configure(values=["Choisir un vaisseau…"] + list(self.vehicle_map))
            options = self.app.repo.item_filter_options(list(ITEM_SCOPES["ship_gear"]["sections"]))
            category_map = {translate_category(value): value for value in options["categories"]}
            self.category_map = category_map
            for child in self.category_wrap.winfo_children():
                child.destroy()
            for child in self.size_wrap.winfo_children():
                child.destroy()
            labelled_combo(
                self.category_wrap,
                label="Catégorie",
                variable=self.category_var,
                values=["Toutes"] + sorted(category_map, key=str.casefold),
                command=lambda _value: self.refresh_candidates(),
                width=145,
            ).pack()
            labelled_combo(
                self.size_wrap,
                label="Taille",
                variable=self.size_var,
                values=["Toutes"] + options["sizes"],
                command=lambda _value: self.refresh_candidates(),
                width=90,
            ).pack()
            active = int(self.app.user_store.get_setting("active_loadout_vehicle", "0") or 0)
            if active:
                label = next((name for name, entity_id in self.vehicle_map.items() if entity_id == active), "")
                if label:
                    self.vehicle_var.set(label)
            self._loaded = True
        self.refresh_candidates()
        self.refresh_loadout()

    def _select_vehicle(self, label: str) -> None:
        vehicle_id = self.vehicle_map.get(label, 0)
        self.app.user_store.set_setting("active_loadout_vehicle", str(vehicle_id))
        self.refresh_loadout()

    def active_vehicle_id(self) -> int:
        return int(self.vehicle_map.get(self.vehicle_var.get(), 0))

    def set_vehicle(self, vehicle_id: int) -> None:
        if not self._loaded:
            self.on_show()
        label = next((name for name, entity_id in self.vehicle_map.items() if entity_id == int(vehicle_id)), "")
        if label:
            self.vehicle_var.set(label)
            self.app.user_store.set_setting("active_loadout_vehicle", str(int(vehicle_id)))
            self.refresh_loadout()

    def refresh_candidates(self) -> None:
        if not self._loaded:
            return
        category = self.category_map.get(self.category_var.get(), "")
        rows = self.app.repo.search_items(
            sections=list(ITEM_SCOPES["ship_gear"]["sections"]),
            search=self.search_var.get(),
            category=category,
            size="" if self.size_var.get() == "Toutes" else self.size_var.get(),
            limit=2500,
        )
        self.item_rows = {int(row["id"]): row for row in rows}
        self.items_table.populate(
            (
                str(row["id"]),
                (row["name"], translate_category(row.get("category")), f"S{row['size']}" if row.get("size") else "—", format_price(row.get("price_min"))),
                False,
            )
            for row in rows
        )

    def refresh_loadout(self) -> None:
        vehicle_id = self.active_vehicle_id()
        entries = self.app.user_store.loadout_entries(vehicle_id) if vehicle_id else []
        rows = self.app.repo.resolve_entities(entries)
        self.loadout_rows = {int(row["entity_id"]): row for row in rows}
        total = sum(float(row.get("price_min") or 0) * int(row.get("quantity") or 1) for row in rows)
        self.budget_label.configure(text=format_price(total) if total else "0 aUEC")
        self.loadout_table.populate(
            (
                str(row["entity_id"]),
                (row["name"], row.get("quantity") or 1, format_price(row.get("price_min")), format_price(float(row.get("price_min") or 0) * int(row.get("quantity") or 1))),
                False,
            )
            for row in rows
        )

    def add_selected(self) -> None:
        item_id = int(self.items_table.selected_id() or 0)
        self.add_external_item(item_id)

    def add_external_item(self, item_id: int) -> bool:
        vehicle_id = self.active_vehicle_id()
        if not vehicle_id:
            self.app.show_notice("Choisissez d’abord un vaisseau pour ce loadout.", COLORS["warning"])
            return False
        if not item_id:
            return False
        detail = self.app.repo.item_detail(int(item_id))
        if not detail or detail.get("section") not in ITEM_SCOPES["ship_gear"]["sections"]:
            self.app.show_notice("Cet objet n’est pas un équipement de vaisseau.", COLORS["warning"])
            return False
        self.app.user_store.add_to_loadout(vehicle_id, int(item_id))
        self.refresh_loadout()
        self.app.show_notice("Équipement ajouté au loadout.")
        return True

    def change_loadout(self, delta: int) -> None:
        vehicle_id = self.active_vehicle_id()
        item_id = int(self.loadout_table.selected_id() or 0)
        row = self.loadout_rows.get(item_id)
        if vehicle_id and row:
            self.app.user_store.set_loadout_quantity(vehicle_id, item_id, int(row.get("quantity") or 1) + delta)
            self.refresh_loadout()

    def remove_loadout(self) -> None:
        vehicle_id = self.active_vehicle_id()
        item_id = int(self.loadout_table.selected_id() or 0)
        if vehicle_id and item_id:
            self.app.user_store.set_loadout_quantity(vehicle_id, item_id, 0)
            self.refresh_loadout()

    def clear_loadout(self) -> None:
        vehicle_id = self.active_vehicle_id()
        if vehicle_id:
            self.app.user_store.clear_loadout(vehicle_id)
            self.refresh_loadout()

    def add_all_to_shopping(self) -> None:
        if not self.loadout_rows:
            self.app.show_notice("Ce loadout est vide.", COLORS["warning"])
            return
        for row in self.loadout_rows.values():
            self.app.user_store.add_to_shopping("item", int(row["entity_id"]), int(row.get("quantity") or 1))
        self.app.refresh_page("shopping")
        self.app.show_notice("Loadout ajouté à la liste de courses.")


class UpdatesPage(AdvancedPage):
    title = "Mises à jour"
    subtitle = "Logiciel Asteriax Verse et données LIVE de Star Citizen."

    def __init__(self, master: Any, app: Any):
        super().__init__(master, app)
        self.app_update_info: dict[str, Any] = {}
        self._app_installing = False
        self._app_check_sequence = 0
        self._app_check_timeout_id: str | None = None
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0)
        scroll.grid(row=0, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        software = ctk.CTkFrame(
            scroll,
            fg_color=COLORS["panel"],
            corner_radius=16,
            border_width=1,
            border_color=COLORS["border"],
        )
        software.grid(row=0, column=0, pady=(0, 14), sticky="ew")
        software.grid_columnconfigure(1, weight=1)
        if getattr(app, "logo_mark", None):
            ctk.CTkLabel(software, text="", image=app.logo_mark).grid(row=0, column=0, rowspan=4, padx=22, pady=20)
        ctk.CTkLabel(
            software,
            text="MISE À JOUR DU LOGICIEL",
            font=("Segoe UI Semibold", 8),
            text_color=COLORS["accent"],
            anchor="w",
        ).grid(row=0, column=1, padx=(0, 15), pady=(20, 3), sticky="ew")
        ctk.CTkLabel(
            software,
            text=f"{APP_NAME} {APP_VERSION}",
            font=("Segoe UI Semibold", 23),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=1, column=1, padx=(0, 15), sticky="ew")
        self.app_status = ctk.CTkLabel(
            software,
            text="Cliquez sur Vérifier pour rechercher une nouvelle publication.",
            wraplength=620,
            justify="left",
            font=("Segoe UI", 9),
            text_color=COLORS["muted"],
            anchor="w",
        )
        self.app_status.grid(row=2, column=1, padx=(0, 15), pady=(4, 18), sticky="ew")
        self.app_meta = ctk.CTkLabel(
            software,
            text=self._app_meta_text(),
            font=("Segoe UI", 9),
            text_color=COLORS["muted_2"],
            anchor="w",
        )
        self.app_meta.grid(row=3, column=1, padx=(0, 15), pady=(0, 10), sticky="ew")
        self.app_progress = ctk.CTkProgressBar(
            software,
            height=7,
            corner_radius=4,
            progress_color=COLORS["accent"],
            fg_color=COLORS["border"],
        )
        self.app_progress.set(0)
        self.app_progress.grid(row=4, column=1, padx=(0, 15), pady=(0, 18), sticky="ew")
        self.app_progress.grid_remove()
        app_actions = ctk.CTkFrame(software, fg_color="transparent")
        app_actions.grid(row=0, column=2, rowspan=5, padx=18, pady=18)
        self.check_app_button = ctk.CTkButton(
            app_actions,
            text="Vérifier maintenant",
            command=lambda: self.check_app(manual=True),
            width=175,
            height=36,
            fg_color=COLORS["panel_alt"],
            hover_color=COLORS["panel_hover"],
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["text"],
        )
        self.check_app_button.pack(pady=(0, 7))
        self.install_app_button = ctk.CTkButton(
            app_actions,
            text="Logiciel à jour",
            command=self.install_app_update,
            width=175,
            height=36,
            state="disabled",
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color=COLORS["background"],
        )
        self.install_app_button.pack()
        self.release_notes_button = ctk.CTkButton(
            app_actions,
            text="Voir les nouveautés",
            command=self.show_release_notes,
            width=175,
            height=34,
            fg_color="transparent",
            hover_color=COLORS["panel_hover"],
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["muted"],
        )
        self.release_notes_button.pack(pady=(7, 0))

        game = ctk.CTkFrame(
            scroll,
            fg_color=COLORS["panel"],
            corner_radius=16,
            border_width=1,
            border_color=COLORS["border"],
        )
        game.grid(row=1, column=0, pady=(0, 14), sticky="ew")
        game.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            game,
            text="DONNÉES STAR CITIZEN",
            font=("Segoe UI Semibold", 8),
            text_color=COLORS["blue"],
            anchor="w",
        ).grid(row=0, column=0, padx=22, pady=(20, 3), sticky="ew")
        self.game_version_label = ctk.CTkLabel(
            game,
            text="Version locale : —",
            font=("Segoe UI Semibold", 23),
            text_color=COLORS["text"],
            anchor="w",
        )
        self.game_version_label.grid(row=1, column=0, padx=22, sticky="ew")
        self.game_status = ctk.CTkLabel(
            game,
            text="Vérification de la version LIVE…",
            wraplength=720,
            justify="left",
            font=("Segoe UI", 9),
            text_color=COLORS["muted"],
            anchor="w",
        )
        self.game_status.grid(row=2, column=0, padx=22, pady=(4, 20), sticky="ew")
        game_actions = ctk.CTkFrame(game, fg_color="transparent")
        game_actions.grid(row=0, column=1, rowspan=3, padx=20, pady=18)
        self.check_game_button = ctk.CTkButton(
            game_actions,
            text="Vérifier le patch LIVE",
            command=self.check_game,
            width=190,
            height=36,
            fg_color=COLORS["panel_alt"],
            hover_color=COLORS["panel_hover"],
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["text"],
        )
        self.check_game_button.pack(pady=(0, 7))
        self.update_game_button = ctk.CTkButton(
            game_actions,
            text="Données à jour",
            command=app.start_update,
            width=190,
            height=36,
            state="disabled",
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color=COLORS["background"],
        )
        self.update_game_button.pack()

        patch_news = ctk.CTkFrame(
            scroll,
            fg_color=COLORS["panel"],
            corner_radius=16,
            border_width=1,
            border_color=COLORS["border"],
        )
        patch_news.grid(row=2, column=0, pady=(0, 14), sticky="ew")
        patch_news.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            patch_news,
            text="NOUVEAUTÉS CATALOGUE · ALPHA 4.10",
            font=("Segoe UI Semibold", 8),
            text_color=COLORS["accent"],
            anchor="w",
        ).grid(row=0, column=0, padx=20, pady=(16, 5), sticky="ew")
        ctk.CTkLabel(
            patch_news,
            text="\n".join(f"•  {line}" for line in PATCH_410_CATALOGUE_HIGHLIGHTS),
            wraplength=790,
            justify="left",
            font=("Segoe UI", 9),
            text_color=COLORS["muted"],
            anchor="w",
        ).grid(row=1, column=0, padx=20, pady=(0, 16), sticky="ew")
        ctk.CTkButton(
            patch_news,
            text="Patch officiel 4.10  ↗",
            command=lambda: webbrowser.open(RSI_LIVE_PATCH_URL),
            width=180,
            height=34,
            fg_color=COLORS["panel_alt"],
            hover_color=COLORS["panel_hover"],
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["text"],
        ).grid(row=0, column=1, rowspan=2, padx=20, pady=16)

        explanation = ctk.CTkFrame(
            scroll,
            fg_color=COLORS["panel_alt"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"],
        )
        explanation.grid(row=3, column=0, pady=(0, 20), sticky="ew")
        ctk.CTkLabel(
            explanation,
            text="COMMENT ÇA FONCTIONNE",
            font=("Segoe UI Semibold", 8),
            text_color=COLORS["muted_2"],
            anchor="w",
        ).pack(fill="x", padx=16, pady=(13, 3))
        ctk.CTkLabel(
            explanation,
            text=(
                "Asteriax Verse vérifie le numéro du patch sans modifier vos fichiers. "
                "Le bouton d’actualisation reste disponible, car les boutiques communautaires peuvent être complétées "
                "plusieurs heures après la sortie d’un patch. "
                "Pendant le téléchargement, l’ancienne base reste consultable."
            ),
            wraplength=940,
            justify="left",
            font=("Segoe UI", 9),
            text_color=COLORS["muted"],
            anchor="w",
        ).pack(fill="x", padx=16, pady=(0, 13))

    def on_show(self) -> None:
        self.refresh_data()
        self.check_game()
        self.check_app(manual=False)

    def refresh_data(self) -> None:
        try:
            version = self.app.repo.meta().get("game_version", "—")
        except Exception:
            version = "—"
        self.game_version_label.configure(text=f"Version locale : {version} LIVE")
        self.app_meta.configure(text=self._app_meta_text())

    def _app_meta_text(self) -> str:
        last_check = self.app.user_store.get_setting("last_app_update_check", "jamais")
        last_version = self.app.user_store.get_setting("last_app_update_version", "—")
        last_install = self.app.user_store.get_setting("last_app_update_at", "jamais")
        return (
            f"Installée : v{APP_VERSION}  ·  Dernière vérification : {last_check}  ·  "
            f"Dernière installation : v{last_version} ({last_install})"
        )

    def show_release_notes(self) -> None:
        remote_version = str(self.app_update_info.get("latest_version") or APP_VERSION)
        remote_notes = str(self.app_update_info.get("release_notes") or "").strip()
        notes = remote_notes or "\n".join(f"• {line}" for line in APP_RELEASE_NOTES)
        messagebox.showinfo(
            f"Nouveautés Asteriax Verse {remote_version}",
            notes,
            parent=self,
        )

    def check_game(self) -> None:
        self.check_game_button.configure(state="disabled", text="Vérification…")
        self.game_status.configure(text="Connexion au service de version LIVE…", text_color=COLORS["muted"])
        self.app.check_game_update(self._game_result)

    def _game_result(self, result: dict[str, Any] | None, error: Exception | None) -> None:
        self.check_game_button.configure(state="normal", text="Vérifier le patch LIVE")
        if error:
            self.game_status.configure(text=f"Vérification impossible : {error}", text_color=COLORS["danger"])
            self.update_game_button.configure(state="normal", text="Actualiser tout le catalogue")
            self.update_game_button.pack()
            return
        result = result or {}
        remote = result.get("remote_version") or "—"
        if result.get("available"):
            self.game_status.configure(
                text=f"Nouveau patch LIVE détecté : {remote}. La base locale peut maintenant être synchronisée.",
                text_color=COLORS["warning"],
            )
            self.update_game_button.configure(state="normal", text=f"Mettre à jour vers {remote}")
            self.update_game_button.pack()
        else:
            self.game_status.configure(
                text=(
                    f"La base correspond à la version LIVE détectée ({remote}). "
                    "Vous pouvez tout de même recharger les prix et inventaires."
                ),
                text_color=COLORS["success"],
            )
            self.update_game_button.configure(state="normal", text="Actualiser tout le catalogue")
            self.update_game_button.pack()

    def check_app(self, *, manual: bool = True) -> None:
        if self._app_installing:
            return
        self._app_check_sequence += 1
        sequence = self._app_check_sequence
        self.check_app_button.configure(state="disabled", text="Vérification…")
        self.app_status.configure(text="Recherche d’une publication Asteriax Verse…", text_color=COLORS["muted"])
        self.update_idletasks()
        if manual:
            self.app.show_notice("Vérification de la version Asteriax Verse…", COLORS["accent"], 2200)
        if self._app_check_timeout_id:
            try:
                self.after_cancel(self._app_check_timeout_id)
            except tk.TclError:
                pass
        self._app_check_timeout_id = self.after(15000, lambda: self._app_check_timed_out(sequence))
        self.app.check_app_update(
            lambda result, error, token=sequence: self._app_result(result, error, token)
        )

    def _app_check_timed_out(self, sequence: int) -> None:
        if sequence != self._app_check_sequence:
            return
        self._app_check_sequence += 1
        self._app_check_timeout_id = None
        self.check_app_button.configure(state="normal", text="Réessayer")
        self.app_status.configure(
            text="La vérification n’a pas répondu après 15 secondes. Vérifiez la connexion ou le pare-feu, puis réessayez.",
            text_color=COLORS["danger"],
        )

    def _app_result(
        self,
        result: dict[str, Any] | None,
        error: Exception | None,
        sequence: int,
    ) -> None:
        if sequence != self._app_check_sequence:
            return
        if self._app_check_timeout_id:
            try:
                self.after_cancel(self._app_check_timeout_id)
            except tk.TclError:
                pass
        self._app_check_timeout_id = None
        self.check_app_button.configure(state="normal", text="Vérifier maintenant")
        checked_at = datetime.now().strftime("%d/%m/%Y à %H:%M")
        self.app.user_store.set_setting("last_app_update_check", checked_at)
        self.app_meta.configure(text=self._app_meta_text())
        if error:
            self.app_status.configure(text=f"Vérification impossible : {error}", text_color=COLORS["danger"])
            return
        self.app_update_info = result or {}
        if not self.app_update_info.get("configured"):
            self.app_status.configure(
                text="Le canal officiel n’est pas encore configuré. Les nouvelles archives seront annoncées sur Discord et Twitch.",
                text_color=COLORS["muted"],
            )
            self.install_app_button.configure(state="disabled", text="Canal à configurer")
        elif self.app_update_info.get("available"):
            latest = self.app_update_info.get("latest_version") or "nouvelle version"
            size = int(self.app_update_info.get("size") or 0)
            size_label = f" · {size / 1024 / 1024:.1f} Mo" if size else ""
            notes = str(self.app_update_info.get("release_notes") or "").strip()
            detail = f"\n{notes}" if notes else ""
            self.app_status.configure(
                text=f"Asteriax Verse {latest} est disponible{size_label}.{detail}",
                text_color=COLORS["warning"],
            )
            ready = bool(
                self.app_update_info.get("download_url")
                and self.app_update_info.get("sha256")
                and self.app_update_info.get("size")
                and can_self_update()
            )
            state = "normal" if ready else "disabled"
            self.install_app_button.configure(state=state, text=f"Mettre à jour vers {latest}")
        else:
            self.app_status.configure(text="Vous utilisez la dernière version disponible.", text_color=COLORS["success"])
            self.install_app_button.configure(state="disabled", text="Logiciel à jour")

    def install_app_update(self) -> None:
        if self._app_installing or not self.app_update_info.get("available"):
            return
        if not can_self_update():
            messagebox.showinfo(
                "Mise à jour Asteriax Verse",
                "La mise à jour intégrée fonctionne depuis AsteriaxVerse.exe. "
                "Cette session a été lancée depuis les sources Python.",
                parent=self,
            )
            return
        latest = str(self.app_update_info.get("latest_version") or "nouvelle version")
        size = int(self.app_update_info.get("size") or 0)
        confirmed = messagebox.askyesno(
            "Installer la mise à jour",
            f"Télécharger et installer Asteriax Verse {latest} ({size / 1024 / 1024:.1f} Mo) ?\n\n"
            "Le fichier sera vérifié, puis le logiciel se fermera et redémarrera automatiquement. "
            "Vos réglages et vos données personnelles seront conservés.",
            parent=self,
        )
        if not confirmed:
            return

        self._app_installing = True
        self.check_app_button.configure(state="disabled")
        self.install_app_button.configure(state="disabled", text="Téléchargement… 0 %")
        self.app_status.configure(
            text="Étape 1/4 · Téléchargement sécurisé depuis GitHub…",
            text_color=COLORS["accent"],
        )
        self.app_progress.set(0)
        self.app_progress.grid()

        def progress(fraction: float, message: str) -> None:
            percentage = max(0, min(100, round(float(fraction) * 100)))
            self.after(
                0,
                lambda p=percentage, m=message: (
                    self.install_app_button.configure(text=f"Téléchargement… {p} %"),
                    self.app_progress.set(min(0.68, float(p) / 100 * 0.68)),
                    self.app_status.configure(text=f"Étape 1/4 · {m}", text_color=COLORS["accent"]),
                ),
            )

        def worker() -> None:
            try:
                package = download_app_update(self.app_update_info, progress)
                self.after(
                    0,
                    lambda: self._set_app_install_phase(
                        0.78,
                        "Étape 2/4 · Fichier téléchargé et vérifié par SHA-256.",
                    ),
                )
                launch_app_update(package, self.app_update_info)
                self.after(0, self._app_update_ready)
            except Exception as exc:
                self.after(0, lambda error=exc: self._app_update_failed(error))

        threading.Thread(target=worker, name="asteriax-self-update", daemon=True).start()

    def _set_app_install_phase(self, fraction: float, message: str) -> None:
        self.app_progress.set(max(0.0, min(1.0, fraction)))
        self.app_status.configure(text=message, text_color=COLORS["accent"])

    def _app_update_ready(self) -> None:
        latest = str(self.app_update_info.get("latest_version") or "")
        self.app_status.configure(
            text=f"Étape 3/4 · Asteriax Verse {latest} est installé. Redémarrage automatique…",
            text_color=COLORS["success"],
        )
        self.app_progress.set(0.94)
        self.install_app_button.configure(text="Redémarrage…", state="disabled")
        self.app.show_notice("Mise à jour vérifiée · redémarrage en cours", COLORS["success"], 5000)
        self.app.after(700, self.app.destroy)

    def _app_update_failed(self, error: Exception) -> None:
        self._app_installing = False
        latest = str(self.app_update_info.get("latest_version") or "nouvelle version")
        self.check_app_button.configure(state="normal", text="Réessayer la vérification")
        self.install_app_button.configure(state="normal", text=f"Réessayer {latest}")
        self.app_status.configure(text=f"Mise à jour impossible : {error}", text_color=COLORS["danger"])
        self.app_progress.grid_remove()


class TranslationPage(AdvancedPage):
    title = "Traduction française"
    subtitle = "Installez et actualisez la traduction communautaire de Star Citizen en un clic."

    def __init__(self, master: Any, app: Any):
        super().__init__(master, app)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._busy = False
        self._events: queue.Queue[tuple[str, Any]] = queue.Queue()
        self._source_labels = {
            details["label"]: key for key, details in TRANSLATION_SOURCES.items()
        }

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0)
        scroll.grid(row=0, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        hero = ctk.CTkFrame(
            scroll,
            fg_color=COLORS["panel"],
            corner_radius=16,
            border_width=1,
            border_color=COLORS["accent_dark"],
        )
        hero.grid(row=0, column=0, pady=(0, 14), sticky="ew")
        hero.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            hero,
            text="STAR CITIZEN EN FRANÇAIS",
            font=("Segoe UI Semibold", 22),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, padx=20, pady=(18, 3), sticky="ew")
        ctk.CTkLabel(
            hero,
            text=(
                "Interface et textes du jeu traduits par la communauté. Les voix restent en anglais. "
                "Le pack est indépendant de CIG et peut contenir quelques textes encore en anglais."
            ),
            wraplength=850,
            justify="left",
            font=("Segoe UI", 11),
            text_color=COLORS["muted"],
            anchor="w",
        ).grid(row=1, column=0, padx=20, pady=(0, 18), sticky="ew")
        ctk.CTkButton(
            hero,
            text="Voir le projet source  ↗",
            command=self.open_translation_project,
            width=180,
            height=36,
            fg_color=COLORS["panel_alt"],
            hover_color=COLORS["panel_hover"],
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["accent"],
        ).grid(row=0, column=1, rowspan=2, padx=20)

        SectionTitle(
            scroll,
            "Installation du jeu",
            "Asteriax Verse cherche automatiquement le canal LIVE. Vous pouvez aussi choisir LIVE, PTU ou EPTU.",
        ).grid(row=1, column=0, pady=(0, 9), sticky="ew")
        folder_card = ctk.CTkFrame(
            scroll,
            fg_color=COLORS["panel"],
            corner_radius=14,
            border_width=1,
            border_color=COLORS["border"],
        )
        folder_card.grid(row=2, column=0, pady=(0, 14), sticky="ew")
        folder_card.grid_columnconfigure(0, weight=1)
        self.folder_var = tk.StringVar(value=app.user_store.get_setting("translation_game_folder", ""))
        self.folder_entry = ctk.CTkEntry(
            folder_card,
            textvariable=self.folder_var,
            height=40,
            corner_radius=10,
            font=("Segoe UI", 11),
            fg_color=COLORS["panel_alt"],
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            placeholder_text=r"C:\Program Files\Roberts Space Industries\StarCitizen\LIVE",
        )
        self.folder_entry.grid(row=0, column=0, padx=(15, 8), pady=15, sticky="ew")
        ctk.CTkButton(
            folder_card,
            text="Détecter",
            command=self.detect_game,
            width=100,
            height=40,
            corner_radius=10,
            fg_color=COLORS["panel_alt"],
            hover_color=COLORS["panel_hover"],
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["text"],
        ).grid(row=0, column=1, padx=4, pady=15)
        ctk.CTkButton(
            folder_card,
            text="Parcourir…",
            command=self.browse_game,
            width=110,
            height=40,
            corner_radius=10,
            fg_color=COLORS["panel_alt"],
            hover_color=COLORS["panel_hover"],
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["text"],
        ).grid(row=0, column=2, padx=(4, 15), pady=15)

        saved_source = app.user_store.get_setting("translation_source", DEFAULT_TRANSLATION_SOURCE)
        if saved_source not in TRANSLATION_SOURCES:
            saved_source = DEFAULT_TRANSLATION_SOURCE
        self.source_var = tk.StringVar(value=TRANSLATION_SOURCES[saved_source]["label"])
        source_row = ctk.CTkFrame(folder_card, fg_color="transparent")
        source_row.grid(row=1, column=0, columnspan=3, padx=15, pady=(0, 15), sticky="ew")
        source_row.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            source_row,
            text="Traduction utilisée",
            font=("Segoe UI Semibold", 10),
            text_color=COLORS["muted"],
            anchor="w",
        ).grid(row=0, column=0, padx=(0, 12))
        self.source_menu = ctk.CTkOptionMenu(
            source_row,
            variable=self.source_var,
            values=list(self._source_labels),
            command=self._source_changed,
            height=38,
            corner_radius=10,
            fg_color=COLORS["panel_alt"],
            button_color=COLORS["accent_dark"],
            button_hover_color=COLORS["accent"],
            dropdown_fg_color=COLORS["panel"],
            dropdown_hover_color=COLORS["panel_hover"],
            text_color=COLORS["text"],
            font=("Segoe UI", 10),
        )
        self.source_menu.grid(row=0, column=1, sticky="ew")
        self.source_note = ctk.CTkLabel(
            source_row,
            text="",
            wraplength=760,
            justify="left",
            font=("Segoe UI", 9),
            text_color=COLORS["muted_2"],
            anchor="w",
        )
        self.source_note.grid(row=1, column=0, columnspan=2, pady=(6, 0), sticky="ew")
        self._source_changed(self.source_var.get())

        status_card = ctk.CTkFrame(
            scroll,
            fg_color=COLORS["panel"],
            corner_radius=16,
            border_width=1,
            border_color=COLORS["border"],
        )
        status_card.grid(row=3, column=0, pady=(0, 14), sticky="ew")
        status_card.grid_columnconfigure(0, weight=1)
        self.status_title = ctk.CTkLabel(
            status_card,
            text="Dossier du jeu à détecter",
            font=("Segoe UI Semibold", 17),
            text_color=COLORS["text"],
            anchor="w",
        )
        self.status_title.grid(row=0, column=0, padx=20, pady=(17, 3), sticky="ew")
        self.channel_badge = ctk.CTkLabel(
            status_card,
            text="—",
            width=80,
            height=29,
            corner_radius=14,
            fg_color=COLORS["panel_alt"],
            text_color=COLORS["muted"],
            font=("Segoe UI Semibold", 10),
        )
        self.channel_badge.grid(row=0, column=1, padx=20, pady=(17, 3))
        self.status_detail = ctk.CTkLabel(
            status_card,
            text="Cliquez sur Détecter ou sélectionnez votre dossier LIVE.",
            wraplength=850,
            justify="left",
            font=("Segoe UI", 10),
            text_color=COLORS["muted"],
            anchor="w",
        )
        self.status_detail.grid(row=1, column=0, columnspan=2, padx=20, pady=(0, 10), sticky="ew")
        self.translation_progress = ctk.CTkProgressBar(
            status_card,
            height=8,
            corner_radius=4,
            fg_color=COLORS["panel_alt"],
            progress_color=COLORS["accent"],
        )
        self.translation_progress.grid(row=2, column=0, columnspan=2, padx=20, pady=(0, 12), sticky="ew")
        self.translation_progress.set(0)
        self.translation_progress.grid_remove()

        actions = ctk.CTkFrame(status_card, fg_color="transparent")
        actions.grid(row=3, column=0, columnspan=2, padx=20, pady=(0, 18), sticky="ew")
        actions.grid_columnconfigure((0, 1), weight=1)
        self.install_button = ctk.CTkButton(
            actions,
            text="Installer / mettre à jour le français",
            command=self.install_translation,
            height=42,
            corner_radius=11,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color=COLORS["background"],
            font=("Segoe UI Semibold", 11),
        )
        self.install_button.grid(row=0, column=0, padx=(0, 6), sticky="ew")
        self.restore_button = ctk.CTkButton(
            actions,
            text="Restaurer l’anglais",
            command=self.restore_translation,
            height=42,
            corner_radius=11,
            fg_color=COLORS["panel_alt"],
            hover_color=COLORS["panel_hover"],
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["muted"],
            font=("Segoe UI Semibold", 11),
        )
        self.restore_button.grid(row=0, column=1, padx=(6, 0), sticky="ew")

        ctk.CTkLabel(
            scroll,
            text=(
                "Sécurité : une sauvegarde de global.ini et user.cfg est créée avant la première installation. "
                "Asteriax Verse ne modifie aucun exécutable du jeu et ne touche pas à Easy Anti-Cheat. "
                "Fermez Star Citizen avant l’installation."
            ),
            wraplength=900,
            justify="left",
            font=("Segoe UI", 9),
            text_color=COLORS["muted_2"],
            anchor="w",
        ).grid(row=4, column=0, padx=5, pady=(0, 20), sticky="ew")

        if not self.folder_var.get():
            self.detect_game(silent=True)
        else:
            self.refresh_status()

    def on_show(self) -> None:
        self.refresh_status()

    def detect_game(self, silent: bool = False) -> None:
        previous = self.folder_var.get().strip()
        installations = find_game_installations([previous] if previous else [])
        if not installations:
            if not silent:
                self.app.show_notice("Installation Star Citizen introuvable : utilisez Parcourir…", COLORS["warning"], 6000)
            self.refresh_status()
            return
        self.folder_var.set(str(installations[0]))
        self.app.user_store.set_setting("translation_game_folder", str(installations[0]))
        self.refresh_status()
        if not silent:
            self.app.show_notice(f"Star Citizen {installations[0].name.upper()} détecté.")

    def browse_game(self) -> None:
        selected = filedialog.askdirectory(title="Sélectionner StarCitizen, LIVE, PTU ou EPTU")
        if not selected:
            return
        self.folder_var.set(selected)
        self.refresh_status(show_error=True)

    def _selected_folder(self) -> str:
        channel = validate_game_folder(self.folder_var.get())
        value = str(channel)
        self.folder_var.set(value)
        self.app.user_store.set_setting("translation_game_folder", value)
        return value

    def refresh_status(self, show_error: bool = False) -> None:
        if self._busy:
            return
        try:
            status = translation_status(self._selected_folder())
        except Exception as exc:
            self.status_title.configure(text="Dossier du jeu à sélectionner", text_color=COLORS["text"])
            self.status_detail.configure(text=str(exc), text_color=COLORS["muted"])
            self.channel_badge.configure(text="—", fg_color=COLORS["panel_alt"], text_color=COLORS["muted"])
            self.restore_button.configure(state="disabled")
            if show_error:
                messagebox.showerror("Dossier Star Citizen invalide", str(exc), parent=self)
            return
        installed = bool(status["installed"])
        if installed:
            installed_at = str(status.get("installed_at") or "date inconnue")
            installed_source = str(status.get("source_label") or "source inconnue")
            self.status_title.configure(text="Traduction française active", text_color=COLORS["success"])
            self.status_detail.configure(
                text=(
                    f"Pack {installed_source} installé · dernière installation : {installed_at}. "
                    "Relancez le jeu s’il était ouvert."
                ),
                text_color=COLORS["muted"],
            )
            self.install_button.configure(text="Mettre à jour la traduction")
        else:
            partial = bool(status["file_present"] or status["configured"])
            self.status_title.configure(
                text="Installation française incomplète" if partial else "Jeu actuellement en anglais",
                text_color=COLORS["warning"] if partial else COLORS["text"],
            )
            self.status_detail.configure(
                text=(
                    "Un ancien réglage partiel a été détecté : le bouton d’installation le réparera."
                    if partial
                    else "Le français n’est pas installé. Une sauvegarde sera créée avant toute modification."
                ),
                text_color=COLORS["muted"],
            )
            self.install_button.configure(text="Installer le français")
        self.channel_badge.configure(
            text=str(status["channel"]),
            fg_color=COLORS["accent_dark"],
            text_color=COLORS["accent"],
        )
        self.restore_button.configure(state="normal" if (installed or status["file_present"] or status["configured"]) else "disabled")

    def _set_busy(self, value: bool) -> None:
        self._busy = value
        state = "disabled" if value else "normal"
        self.install_button.configure(state=state)
        self.folder_entry.configure(state=state)
        self.source_menu.configure(state=state)
        if value:
            self.restore_button.configure(state="disabled")
            self.translation_progress.set(0)
            self.translation_progress.grid()
        else:
            self.translation_progress.grid_remove()

    def install_translation(self) -> None:
        try:
            folder = self._selected_folder()
            source_key = self._selected_source(folder)
        except Exception as exc:
            messagebox.showerror("Traduction française", str(exc), parent=self)
            return
        if not messagebox.askyesno(
            "Installer la traduction française",
            "Fermez Star Citizen avant de continuer.\n\nTélécharger et installer maintenant la dernière traduction communautaire française ?",
            parent=self,
        ):
            return
        self._set_busy(True)
        self.status_title.configure(text="Installation en cours…", text_color=COLORS["accent"])

        def progress(fraction: float, message: str) -> None:
            self._events.put(("progress", (fraction, message)))

        def worker() -> None:
            try:
                result = install_french_translation(folder, progress, source_key=source_key)
                self._events.put(("done", result))
            except Exception as exc:
                self._events.put(("error", exc))

        threading.Thread(target=worker, daemon=True).start()
        self.after(60, self._poll_events)

    def restore_translation(self) -> None:
        try:
            folder = self._selected_folder()
        except Exception as exc:
            messagebox.showerror("Dossier Star Citizen invalide", str(exc), parent=self)
            return
        if not messagebox.askyesno(
            "Restaurer l’anglais",
            "Restaurer les fichiers sauvegardés avant l’installation et remettre le jeu en anglais ?",
            parent=self,
        ):
            return
        self._set_busy(True)
        self.status_title.configure(text="Restauration en cours…", text_color=COLORS["accent"])

        def worker() -> None:
            try:
                result = restore_english(folder)
                self._events.put(("restored", result))
            except Exception as exc:
                self._events.put(("error", exc))

        threading.Thread(target=worker, daemon=True).start()
        self.after(60, self._poll_events)

    def _poll_events(self) -> None:
        try:
            while True:
                kind, payload = self._events.get_nowait()
                if kind == "progress":
                    fraction, message = payload
                    self.translation_progress.set(float(fraction))
                    self.status_detail.configure(text=str(message), text_color=COLORS["muted"])
                elif kind in {"done", "restored"}:
                    self._set_busy(False)
                    self.refresh_status()
                    message = "Traduction française installée avec succès." if kind == "done" else "Jeu restauré en anglais."
                    self.app.show_notice(message, COLORS["success"], 7000)
                    return
                elif kind == "error":
                    self._set_busy(False)
                    self.refresh_status()
                    messagebox.showerror(
                        "Traduction française",
                        f"L’opération a échoué :\n\n{payload}\n\nVérifiez votre connexion et les droits d’écriture du dossier du jeu.",
                        parent=self,
                    )
                    return
        except queue.Empty:
            pass
        if self._busy:
            self.after(60, self._poll_events)

    def _selected_source(self, folder: str | None = None) -> str:
        key = self._source_labels.get(self.source_var.get(), DEFAULT_TRANSLATION_SOURCE)
        if folder:
            translation_source_url(validate_game_folder(folder), key)
        return key

    def _source_changed(self, _label: str) -> None:
        key = self._selected_source()
        details = translation_source_details(key)
        self.app.user_store.set_setting("translation_source", key)
        note = details["description"]
        if key == "scefra":
            note += " Quelques accents peuvent encore mal s’afficher selon le texte."
        self.source_note.configure(text=note)

    def open_translation_project(self) -> None:
        details = translation_source_details(self._selected_source())
        webbrowser.open(details["project_url"])


class SettingsPage(AdvancedPage):
    title = "Réglages & communauté"
    subtitle = "Préférences locales, identité AsteriaxTTV et liens officiels."

    def __init__(self, master: Any, app: Any):
        super().__init__(master, app)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent", corner_radius=0)
        self.scroll.grid(row=0, column=0, sticky="nsew")
        self.scroll.grid_columnconfigure((0, 1), weight=1, uniform="settings")

        identity = ctk.CTkFrame(
            self.scroll,
            fg_color=COLORS["panel"],
            corner_radius=16,
            border_width=1,
            border_color=COLORS["border"],
        )
        identity.grid(row=0, column=0, columnspan=2, pady=(0, 14), sticky="ew")
        identity.grid_columnconfigure(1, weight=1)
        if getattr(app, "logo_full", None):
            ctk.CTkLabel(identity, text="", image=app.logo_full).grid(row=0, column=0, rowspan=4, padx=22, pady=18)
        ctk.CTkLabel(identity, text=APP_NAME, font=("Segoe UI Semibold", 25), text_color=COLORS["text"], anchor="w").grid(
            row=0, column=1, padx=(0, 16), pady=(20, 0), sticky="ew"
        )
        ctk.CTkLabel(identity, text=f"Créé par {APP_AUTHOR} · version {APP_VERSION}", font=("Segoe UI", 10), text_color=COLORS["accent"], anchor="w").grid(
            row=1, column=1, padx=(0, 16), pady=(3, 8), sticky="ew"
        )
        community = ctk.CTkFrame(identity, fg_color="transparent")
        community.grid(row=2, column=1, padx=(0, 20), pady=(0, 20), sticky="w")
        ctk.CTkButton(
            community,
            text="Rejoindre le Discord  ↗",
            command=lambda: webbrowser.open(DISCORD_URL),
            width=175,
            height=35,
            fg_color="#5865F2",
            hover_color="#6875F5",
            text_color="#FFFFFF",
        ).grid(row=0, column=0, padx=(0, 7))
        ctk.CTkButton(
            community,
            text="Chaîne Twitch  ↗",
            command=lambda: webbrowser.open(TWITCH_URL),
            width=150,
            height=35,
            fg_color="#9146FF",
            hover_color="#A364FF",
            text_color="#FFFFFF",
        ).grid(row=0, column=1)

        SectionTitle(self.scroll, "Comportement", "Ces réglages sont enregistrés uniquement sur votre ordinateur.").grid(
            row=1, column=0, columnspan=2, pady=(0, 9), sticky="ew"
        )
        self.patch_var = tk.BooleanVar(value=app.user_store.setting_bool("check_patch_startup", True))
        self.auto_sync_var = tk.BooleanVar(value=app.user_store.setting_bool("auto_sync_patch", False))
        self.remember_var = tk.BooleanVar(value=app.user_store.setting_bool("remember_state", True))
        self.splash_var = tk.BooleanVar(value=app.user_store.setting_bool("show_splash", True))
        self.performance_var = tk.BooleanVar(value=app.user_store.setting_bool("performance_mode", False))
        settings = [
            ("Vérifier les nouveaux patchs au démarrage", "Alerte lorsqu’une version LIVE plus récente est détectée.", "check_patch_startup", self.patch_var),
            ("Mettre les données à jour après un nouveau patch", "La synchronisation démarre en arrière-plan et l’ancienne base reste utilisable.", "auto_sync_patch", self.auto_sync_var),
            ("Mémoriser la page, la fenêtre et les filtres", "Retrouvez votre espace de travail au prochain lancement.", "remember_state", self.remember_var),
            ("Afficher l’écran de lancement AsteriaxTTV", "Affiche brièvement le logo lors de l’ouverture du logiciel.", "show_splash", self.splash_var),
            (
                "Mode performances",
                "Charge 100 lignes à la fois, évite la sélection automatique et désactive l’écran de lancement.",
                "performance_mode",
                self.performance_var,
            ),
        ]
        for index, (title, caption, key, variable) in enumerate(settings):
            card = ctk.CTkFrame(
                self.scroll,
                fg_color=COLORS["panel"],
                corner_radius=12,
                border_width=1,
                border_color=COLORS["border"],
            )
            card.grid(row=2 + index // 2, column=index % 2, padx=(0, 7) if index % 2 == 0 else (7, 0), pady=(0, 10), sticky="nsew")
            card.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(card, text=title, font=("Segoe UI Semibold", 11), text_color=COLORS["text"], anchor="w").grid(
                row=0, column=0, padx=15, pady=(13, 2), sticky="ew"
            )
            ctk.CTkLabel(card, text=caption, wraplength=390, justify="left", font=("Segoe UI", 8), text_color=COLORS["muted"], anchor="w").grid(
                row=1, column=0, padx=15, pady=(0, 13), sticky="ew"
            )
            ctk.CTkSwitch(
                card,
                text="",
                variable=variable,
                command=lambda k=key, v=variable: self._save_boolean_setting(k, v),
                progress_color=COLORS["accent"],
                button_color=COLORS["text"],
            ).grid(row=0, column=1, rowspan=2, padx=15)

        utility = ctk.CTkFrame(self.scroll, fg_color="transparent")
        utility.grid(row=5, column=0, columnspan=2, pady=(3, 20), sticky="ew")
        utility.grid_columnconfigure((0, 1), weight=1)
        ctk.CTkButton(
            utility,
            text="Ouvrir le dossier des données",
            command=lambda: webbrowser.open(user_data_dir().as_uri()),
            height=35,
            fg_color=COLORS["panel"],
            border_width=1,
            border_color=COLORS["border"],
            hover_color=COLORS["panel_hover"],
            text_color=COLORS["text"],
        ).grid(row=0, column=0, padx=(0, 5), sticky="ew")
        ctk.CTkButton(
            utility,
            text="Réinitialiser uniquement les filtres mémorisés",
            command=self.reset_filters,
            height=35,
            fg_color=COLORS["panel"],
            border_width=1,
            border_color=COLORS["border"],
            hover_color=COLORS["panel_hover"],
            text_color=COLORS["muted"],
        ).grid(row=0, column=1, padx=(5, 0), sticky="ew")

    def _save_boolean_setting(self, key: str, variable: tk.BooleanVar) -> None:
        self.app.user_store.set_setting(key, "1" if variable.get() else "0")
        if key == "performance_mode":
            self.app.show_notice("Le mode performances sera appliqué au prochain démarrage.", COLORS["accent"], 5500)

    def reset_filters(self) -> None:
        for key in ("filters:locations", "filters:ships", "filters:ship_gear", "filters:personal_gear", "filters:all"):
            self.app.user_store.set_setting(key, "{}")
        self.app.show_notice("Filtres mémorisés réinitialisés.")
