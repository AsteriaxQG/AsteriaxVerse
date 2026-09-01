"""Card-based ship catalogue for the Asteriax Verse desktop app."""

from __future__ import annotations

import math
from typing import Any

import customtkinter as ctk
import tkinter as tk

from core.constants import COLORS
from core.database import format_price


class _CardSelection:
    """Compatibility object for the existing filtering and selection logic."""

    def __init__(self) -> None:
        self._selected = ""

    def selected_id(self) -> str:
        return self._selected

    def select(self, iid: str) -> None:
        self._selected = str(iid or "")

    def sort_state(self) -> tuple[None, bool]:
        return None, False

    def restore_sort(self, *_args: Any, **_kwargs: Any) -> None:
        return None

    def populate(self, *_args: Any, **_kwargs: Any) -> None:
        return None


def install_ship_cards(ShipsPage: Any) -> None:
    ShipsPage._build_content = _ships_build_content
    ShipsPage._apply_vehicle_results = _ships_apply_vehicle_results
    ShipsPage._save_filters = _ships_save_filters
    ShipsPage._render_filter_chips = _ships_render_filter_chips

def _ships_build_content(page: Any) -> None:
    content = ctk.CTkFrame(page, fg_color="transparent")
    content.grid(row=1, column=0, sticky="nsew")
    content.grid_rowconfigure(0, weight=1)
    content.grid_columnconfigure(0, weight=3, minsize=590)
    content.grid_columnconfigure(1, weight=2, minsize=310)
    page.site_ship_content = content

    left = ctk.CTkFrame(content, fg_color="transparent")
    left.grid(row=0, column=0, padx=(0, 11), sticky="nsew")
    left.grid_rowconfigure(1, weight=1)
    left.grid_columnconfigure(0, weight=1)

    toolbar = ctk.CTkFrame(left, fg_color=COLORS["panel"], corner_radius=13, border_width=1, border_color=COLORS["border"])
    toolbar.grid(row=0, column=0, pady=(0, 10), sticky="ew")
    toolbar.grid_columnconfigure(0, weight=1)
    ctk.CTkLabel(toolbar, text="AFFICHAGE CARTES", text_color=COLORS["accent"], font=("Segoe UI Semibold", 9), anchor="w").grid(row=0, column=0, padx=13, pady=(8, 0), sticky="ew")
    ctk.CTkLabel(toolbar, text="30 modèles par page", text_color=COLORS["muted_2"], font=("Segoe UI", 8), anchor="w").grid(row=1, column=0, padx=13, pady=(0, 8), sticky="ew")

    page.sort_var = tk.StringVar(value=str(page._saved_filter_state.get("card_sort") or "Nom A–Z"))
    sort_menu = ctk.CTkOptionMenu(
        toolbar,
        variable=page.sort_var,
        values=["Nom A–Z", "Prix croissant", "Prix décroissant", "SCU décroissant"],
        command=lambda _value: page.refresh_results(),
        width=150,
        height=34,
        corner_radius=8,
        fg_color=COLORS["panel_alt"],
        button_color="#123442",
        button_hover_color="#18485A",
        text_color=COLORS["text"],
        font=("Segoe UI", 10),
    )
    sort_menu.grid(row=0, column=1, rowspan=2, padx=7, pady=8)

    page.card_page_label = ctk.CTkLabel(toolbar, text="Page 1 / 1", text_color=COLORS["muted"], font=("Segoe UI Semibold", 9))
    page.card_page_label.grid(row=0, column=2, rowspan=2, padx=(2, 7))
    page.card_prev = ctk.CTkButton(toolbar, text="←", command=lambda: _ships_change_page(page, -1), width=34, height=32, corner_radius=8, fg_color="transparent", hover_color=COLORS["panel_hover"], border_width=1, border_color=COLORS["border"], text_color=COLORS["accent"])
    page.card_prev.grid(row=0, column=3, rowspan=2, padx=2)
    page.card_next = ctk.CTkButton(toolbar, text="→", command=lambda: _ships_change_page(page, 1), width=34, height=32, corner_radius=8, fg_color="transparent", hover_color=COLORS["panel_hover"], border_width=1, border_color=COLORS["border"], text_color=COLORS["accent"])
    page.card_next.grid(row=0, column=4, rowspan=2, padx=(2, 10))

    page.card_scroll = ctk.CTkScrollableFrame(
        left,
        fg_color="transparent",
        corner_radius=0,
        scrollbar_button_color=COLORS["border"],
        scrollbar_button_hover_color=COLORS["accent_dark"],
    )
    page.card_scroll.grid(row=1, column=0, sticky="nsew")
    page.card_scroll.grid_columnconfigure((0, 1), weight=1, uniform="shipcard")

    page.detail = ctk.CTkScrollableFrame(
        content,
        fg_color=COLORS["panel"],
        corner_radius=16,
        border_width=1,
        border_color=COLORS["border"],
        scrollbar_button_color=COLORS["border"],
        scrollbar_button_hover_color=COLORS["accent_dark"],
    )
    page.detail.grid(row=0, column=1, sticky="nsew")
    page.detail.grid_columnconfigure(0, weight=1)

    page.table = _CardSelection()
    page._ship_rows = []
    page._ship_card_widgets = {}
    page.card_page = 0
    page.card_page_size = 30
    page._show_empty_detail("Sélectionnez un modèle", "Ouvre une carte pour afficher ses caractéristiques, son meilleur prix et toutes ses concessions.")


def _ships_save_filters(page: Any) -> None:
    page.app.user_store.set_json_setting(
        "filters:ships",
        {
            "search": page.search_var.get(),
            "manufacturer": page.manufacturer_var.get(),
            "type": page.type_var.get(),
            "class": page.class_var.get(),
            "system": page.system_var.get(),
            "planet": page.planet_var.get(),
            "card_sort": page.sort_var.get() if hasattr(page, "sort_var") else "Nom A–Z",
        },
    )


def _ships_render_filter_chips(page: Any) -> None:
    for child in page.chip_row.winfo_children():
        child.destroy()
    configs = [
        ("Constructeur", page.manufacturer_var, "Tous"),
        ("Type", page.type_var, "Tous"),
        ("Classe", page.class_var, "Toutes"),
        ("Système", page.system_var, "Tous"),
        ("Planète", page.planet_var, "Toutes"),
    ]
    active = [(label, variable, default) for label, variable, default in configs if variable.get() != default]
    if not active:
        ctk.CTkLabel(page.chip_row, text="Aucun filtre actif · les vaisseaux sont présentés sous forme de cartes", font=("Segoe UI", 10), text_color=COLORS["muted_2"], anchor="w").pack(side="left")
        return
    ctk.CTkLabel(page.chip_row, text="FILTRES ACTIFS", font=("Segoe UI Semibold", 10), text_color=COLORS["muted_2"]).pack(side="left", padx=(0, 7))
    for label, variable, default in active:
        ctk.CTkButton(
            page.chip_row,
            text=f"{label}: {variable.get()}  ×",
            command=lambda var=variable, value=default: (var.set(value), page.refresh_results()),
            width=0,
            height=25,
            corner_radius=12,
            fg_color=COLORS["accent_dark"],
            hover_color=COLORS["panel_hover"],
            text_color=COLORS["accent"],
            font=("Segoe UI Semibold", 10),
        ).pack(side="left", padx=(0, 5))


def _ships_apply_vehicle_results(page: Any, rows: list[dict[str, Any]], error: Exception | None, generation: int, select_id: int | None) -> None:
    if generation != page._query_generation:
        return
    if error:
        page.result_label.configure(text="Erreur")
        page.app.show_notice(f"Recherche impossible : {error}", COLORS["danger"])
        return

    sort_name = page.sort_var.get() if hasattr(page, "sort_var") else "Nom A–Z"
    sorted_rows = list(rows)
    if sort_name == "Prix croissant":
        sorted_rows.sort(key=lambda row: (float(row.get("price_min") or 10**18), str(row.get("name") or "").casefold()))
    elif sort_name == "Prix décroissant":
        sorted_rows.sort(key=lambda row: (float(row.get("price_min") or 0), str(row.get("name") or "").casefold()), reverse=True)
    elif sort_name == "SCU décroissant":
        sorted_rows.sort(key=lambda row: (float(row.get("scu") or 0), str(row.get("name") or "").casefold()), reverse=True)
    else:
        sorted_rows.sort(key=lambda row: str(row.get("name") or "").casefold())

    page.rows_by_id = {int(row["id"]): row for row in sorted_rows}
    page._ship_rows = sorted_rows
    page.result_label.configure(text=f"{len(sorted_rows)} modèles")
    page._save_filters()

    target = select_id if select_id in page.rows_by_id else None
    if target is None and sorted_rows and not page.app.performance_mode:
        target = int(sorted_rows[0]["id"])
    if target is not None:
        target_index = next((index for index, row in enumerate(sorted_rows) if int(row["id"]) == int(target)), 0)
        page.card_page = target_index // page.card_page_size
        page.table.select(str(target))
    else:
        page.card_page = 0
        page.table.select("")

    _ships_render_page(page)
    if target is not None:
        _ships_select(page, int(target), scroll=False)
    elif sorted_rows:
        page._show_empty_detail("Sélectionnez un modèle", "Choisis une carte pour ouvrir sa fiche détaillée.")
    else:
        page._show_empty_detail("Aucun modèle", "Modifie les filtres pour élargir la recherche.")


def _ships_change_page(page: Any, delta: int) -> None:
    total_pages = max(1, math.ceil(len(page._ship_rows) / page.card_page_size))
    new_page = max(0, min(total_pages - 1, page.card_page + delta))
    if new_page == page.card_page:
        return
    page.card_page = new_page
    page.table.select("")
    _ships_render_page(page)
    page._show_empty_detail("Sélectionnez un modèle", "Choisis une carte pour ouvrir sa fiche détaillée.")


def _ships_render_page(page: Any) -> None:
    for child in page.card_scroll.winfo_children():
        child.destroy()
    page._ship_card_widgets = {}
    rows = page._ship_rows
    page_size = page.card_page_size
    total_pages = max(1, math.ceil(len(rows) / page_size))
    page.card_page = max(0, min(total_pages - 1, page.card_page))
    start = page.card_page * page_size
    visible = rows[start : start + page_size]
    page.card_page_label.configure(text=f"Page {page.card_page + 1} / {total_pages}")
    page.card_prev.configure(state="normal" if page.card_page > 0 else "disabled")
    page.card_next.configure(state="normal" if page.card_page + 1 < total_pages else "disabled")

    if not visible:
        ctk.CTkLabel(page.card_scroll, text="Aucun vaisseau pour ces filtres.", text_color=COLORS["muted"], font=("Segoe UI", 12)).grid(row=0, column=0, columnspan=2, pady=40)
        return

    for index, row in enumerate(visible):
        vehicle_id = int(row["id"])
        grid_row = index // 2
        grid_col = index % 2
        card = ctk.CTkFrame(
            page.card_scroll,
            fg_color=COLORS["panel"],
            corner_radius=15,
            border_width=1,
            border_color=COLORS["border"],
        )
        card.grid(row=grid_row, column=grid_col, padx=(0 if grid_col == 0 else 6, 6 if grid_col == 0 else 0), pady=(0, 10), sticky="nsew")
        card.grid_columnconfigure(0, weight=1)
        page._ship_card_widgets[vehicle_id] = card

        kind = "VÉHICULE TERRESTRE" if row.get("is_ground_vehicle") else "VAISSEAU"
        ctk.CTkLabel(card, text=kind, text_color=COLORS["accent"], font=("Segoe UI Semibold", 8), anchor="w").grid(row=0, column=0, padx=14, pady=(13, 2), sticky="ew")
        ctk.CTkLabel(card, text=str(row.get("name") or "Modèle"), wraplength=260, justify="left", text_color=COLORS["text"], font=("Segoe UI Semibold", 15), anchor="w").grid(row=1, column=0, padx=14, sticky="ew")
        ctk.CTkLabel(card, text=str(row.get("manufacturer") or "Constructeur inconnu"), text_color=COLORS["muted"], font=("Segoe UI", 10), anchor="w").grid(row=2, column=0, padx=14, pady=(2, 10), sticky="ew")

        metrics = ctk.CTkFrame(card, fg_color=COLORS["panel_alt"], corner_radius=10)
        metrics.grid(row=3, column=0, padx=12, sticky="ew")
        metrics.grid_columnconfigure((0, 1), weight=1, uniform="cardmetric")
        ctk.CTkLabel(metrics, text=f"{row.get('scu', 0):g}" if row.get("scu") else "—", text_color=COLORS["text"], font=("Segoe UI Semibold", 11)).grid(row=0, column=0, padx=8, pady=(7, 0))
        ctk.CTkLabel(metrics, text="SCU", text_color=COLORS["muted_2"], font=("Segoe UI Semibold", 8)).grid(row=1, column=0, padx=8, pady=(0, 7))
        ctk.CTkLabel(metrics, text=format_price(row.get("price_min")), text_color=COLORS["accent"], font=("Segoe UI Semibold", 11)).grid(row=0, column=1, padx=8, pady=(7, 0))
        ctk.CTkLabel(metrics, text="MEILLEUR PRIX", text_color=COLORS["muted_2"], font=("Segoe UI Semibold", 8)).grid(row=1, column=1, padx=8, pady=(0, 7))

        ctk.CTkLabel(card, text=str(row.get("vehicle_class") or "Multirôle"), text_color=COLORS["muted_2"], font=("Segoe UI", 9), anchor="w").grid(row=4, column=0, padx=14, pady=(8, 6), sticky="ew")
        buttons = ctk.CTkFrame(card, fg_color="transparent")
        buttons.grid(row=5, column=0, padx=12, pady=(0, 12), sticky="ew")
        buttons.grid_columnconfigure((0, 1), weight=1, uniform="cardbutton")
        ctk.CTkButton(
            buttons,
            text="Voir la fiche →",
            command=lambda vid=vehicle_id: _ships_select(page, vid),
            height=31,
            corner_radius=8,
            fg_color="#123746",
            hover_color="#17495B",
            border_width=1,
            border_color="#2A6074",
            text_color=COLORS["accent"],
            font=("Segoe UI Semibold", 9),
        ).grid(row=0, column=0, padx=(0, 3), sticky="ew")
        ctk.CTkButton(
            buttons,
            text="⇄ Comparer",
            command=lambda vid=vehicle_id: page.app.add_to_comparison("vehicle", vid),
            height=31,
            corner_radius=8,
            fg_color="transparent",
            hover_color=COLORS["panel_hover"],
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["muted"],
            font=("Segoe UI Semibold", 9),
        ).grid(row=0, column=1, padx=(3, 0), sticky="ew")

    selected = page.table.selected_id()
    if selected.isdigit():
        _ships_highlight(page, int(selected))


def _ships_select(page: Any, vehicle_id: int, *, scroll: bool = True) -> None:
    page.table.select(str(vehicle_id))
    _ships_highlight(page, vehicle_id)
    page._show_vehicle_detail(vehicle_id)
    if scroll:
        try:
            page.detail._parent_canvas.yview_moveto(0.0)
        except Exception:
            pass


def _ships_highlight(page: Any, vehicle_id: int) -> None:
    for vid, card in getattr(page, "_ship_card_widgets", {}).items():
        try:
            selected = vid == vehicle_id
            card.configure(
                border_color="#47CFF3" if selected else COLORS["border"],
                border_width=2 if selected else 1,
                fg_color="#0D202B" if selected else COLORS["panel"],
            )
        except Exception:
            pass
