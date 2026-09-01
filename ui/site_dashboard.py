"""Website-like home page for the Asteriax Verse desktop app."""

from __future__ import annotations

import webbrowser
from datetime import datetime
from typing import Any

import customtkinter as ctk

from core.constants import APP_AUTHOR, APP_VERSION, COLORS, NEWS_ITEMS

def dashboard_refresh(page: Any) -> None:
    for child in page.scroll.winfo_children():
        child.destroy()

    stats = page.app.repo.dashboard_stats()
    meta = page.app.repo.meta()
    version = str(meta.get("game_version") or "—")

    for column in range(4):
        page.scroll.grid_columnconfigure(column, weight=1, uniform="home")

    hero = ctk.CTkFrame(
        page.scroll,
        fg_color="#091822",
        corner_radius=20,
        border_width=1,
        border_color="#1B4254",
    )
    hero.grid(row=0, column=0, columnspan=4, pady=(8, 18), sticky="ew")
    hero.grid_columnconfigure(0, weight=3)
    hero.grid_columnconfigure(1, weight=2)

    left = ctk.CTkFrame(hero, fg_color="transparent")
    left.grid(row=0, column=0, padx=(28, 18), pady=28, sticky="nsew")
    left.grid_columnconfigure(0, weight=1)
    ctk.CTkLabel(
        left,
        text="ASTERIAXVERSE DESKTOP",
        text_color=COLORS["accent"],
        font=("Segoe UI Semibold", 10),
        anchor="w",
    ).grid(row=0, column=0, sticky="ew")
    ctk.CTkLabel(
        left,
        text="Le Verse, plus clair.",
        text_color=COLORS["text"],
        font=("Segoe UI Semibold", 30),
        anchor="w",
    ).grid(row=1, column=0, pady=(7, 0), sticky="ew")
    ctk.CTkLabel(
        left,
        text="Directement sur ton bureau.",
        text_color=COLORS["accent"],
        font=("Segoe UI Semibold", 24),
        anchor="w",
    ).grid(row=2, column=0, sticky="ew")
    ctk.CTkLabel(
        left,
        text=(
            "Vaisseaux, équipements, prix, boutiques et mises à jour Star Citizen dans une interface "
            "rapide, lisible et utilisable même hors ligne."
        ),
        wraplength=700,
        justify="left",
        text_color=COLORS["muted"],
        font=("Segoe UI", 12),
        anchor="w",
    ).grid(row=3, column=0, pady=(11, 18), sticky="ew")

    actions = ctk.CTkFrame(left, fg_color="transparent")
    actions.grid(row=4, column=0, sticky="w")
    ctk.CTkButton(
        actions,
        text="Explorer les vaisseaux",
        command=lambda: page.app.show_page("ships"),
        height=40,
        corner_radius=9,
        fg_color=COLORS["accent"],
        hover_color=COLORS["accent_hover"],
        text_color=COLORS["background"],
        font=("Segoe UI Semibold", 11),
    ).grid(row=0, column=0, padx=(0, 8))
    ctk.CTkButton(
        actions,
        text="Voir les équipements",
        command=lambda: page.app.show_page("equipment"),
        height=40,
        corner_radius=9,
        fg_color="#0D2633",
        hover_color="#123847",
        border_width=1,
        border_color="#2B6073",
        text_color=COLORS["text"],
        font=("Segoe UI Semibold", 11),
    ).grid(row=0, column=1)

    live = ctk.CTkFrame(
        hero,
        fg_color="#0C202B",
        corner_radius=16,
        border_width=1,
        border_color="#245166",
    )
    live.grid(row=0, column=1, padx=(12, 26), pady=26, sticky="nsew")
    live.grid_columnconfigure(0, weight=1)
    ctk.CTkLabel(live, text="DONNÉES LIVE", text_color=COLORS["muted"], font=("Segoe UI Semibold", 10), anchor="w").grid(
        row=0, column=0, padx=18, pady=(17, 0), sticky="ew"
    )
    ctk.CTkLabel(live, text=version, text_color=COLORS["accent"], font=("Segoe UI Semibold", 22), anchor="w").grid(
        row=1, column=0, padx=18, pady=(2, 13), sticky="ew"
    )
    live_rows = [
        ("●", COLORS["success"], "Catalogue SQLite prêt"),
        ("●", COLORS["accent"], "Mises à jour intégrées"),
        ("●", COLORS["blue"], "Mode hors ligne disponible"),
    ]
    for row_index, (dot, color, label) in enumerate(live_rows, start=2):
        line = ctk.CTkFrame(live, fg_color="transparent")
        line.grid(row=row_index, column=0, padx=18, pady=(0, 9), sticky="ew")
        ctk.CTkLabel(line, text=dot, text_color=color, font=("Segoe UI", 10), width=16).pack(side="left")
        ctk.CTkLabel(line, text=label, text_color=COLORS["muted"], font=("Segoe UI", 11)).pack(side="left", padx=(5, 0))
    ctk.CTkLabel(
        live,
        text=f"AsteriaxVerse {APP_VERSION} · {APP_AUTHOR}",
        text_color=COLORS["muted_2"],
        font=("Segoe UI", 9),
        anchor="w",
    ).grid(row=5, column=0, padx=18, pady=(7, 16), sticky="ew")

    stat_data = [
        (str(stats.get("vehicles", 0)), "Vaisseaux & véhicules", "Catalogue en jeu", COLORS["accent"]),
        (str(stats.get("items", 0)), "Équipements", "Objets achetables", COLORS["blue"]),
        (str(stats.get("locations", 0)), "Boutiques", "Lieux référencés", COLORS["warning"]),
        (str(stats.get("categories", 0)), "Catégories", "Familles de données", COLORS["success"]),
    ]
    for column, item in enumerate(stat_data):
        _dashboard_stat(page.scroll, column, *item)

    _section_header(page.scroll, 2, "ACCÈS RAPIDE", "Retrouve immédiatement ce dont tu as besoin dans le Verse.")
    quick = [
        ("✦", "Vaisseaux", "Catalogue complet, prix, caractéristiques et concessions.", "ships"),
        ("⚙", "Équipements", "Composants de vaisseau et équipement personnel.", "equipment"),
        ("⌖", "Explorer", "Boutiques, stations et destinations du Persistent Universe.", "locations"),
    ]
    spans = [(0, 1), (1, 1), (2, 2)]
    for index, (icon, title, caption, target) in enumerate(quick):
        column, span = spans[index]
        card = ctk.CTkFrame(page.scroll, fg_color=COLORS["panel"], corner_radius=16, border_width=1, border_color=COLORS["border"])
        card.grid(row=3, column=column, columnspan=span, padx=(0 if column == 0 else 6, 0 if column + span == 4 else 6), pady=(0, 18), sticky="nsew")
        card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(card, text=icon, text_color=COLORS["accent"], font=("Segoe UI Semibold", 20), anchor="w").grid(row=0, column=0, padx=18, pady=(17, 5), sticky="ew")
        ctk.CTkLabel(card, text=title, text_color=COLORS["text"], font=("Segoe UI Semibold", 15), anchor="w").grid(row=1, column=0, padx=18, sticky="ew")
        ctk.CTkLabel(card, text=caption, wraplength=360, justify="left", text_color=COLORS["muted"], font=("Segoe UI", 10), anchor="w").grid(row=2, column=0, padx=18, pady=(5, 14), sticky="ew")
        ctk.CTkButton(
            card,
            text="Ouvrir  →",
            command=lambda name=target: page.app.show_page(name),
            height=32,
            corner_radius=8,
            fg_color="transparent",
            hover_color=COLORS["panel_hover"],
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["accent"],
            font=("Segoe UI Semibold", 10),
        ).grid(row=3, column=0, padx=18, pady=(0, 17), sticky="ew")

    _section_header(page.scroll, 4, "ACTUALITÉS & PATCH", "Les dernières informations intégrées au logiciel.")
    news = sorted(NEWS_ITEMS, key=_news_sort_key, reverse=True)[:4]
    for index, item in enumerate(news):
        row = 5 + index // 2
        column = (index % 2) * 2
        card = ctk.CTkFrame(page.scroll, fg_color=COLORS["panel"], corner_radius=15, border_width=1, border_color=COLORS["border"])
        card.grid(row=row, column=column, columnspan=2, padx=(0 if column == 0 else 7, 7 if column == 0 else 0), pady=(0, 12), sticky="nsew")
        card.grid_columnconfigure(0, weight=1)
        meta_label = f"{item.get('category') or 'ACTU'}  ·  {item.get('date') or '—'}"
        ctk.CTkLabel(card, text=meta_label, text_color=COLORS["accent"], font=("Segoe UI Semibold", 9), anchor="w").grid(row=0, column=0, padx=17, pady=(15, 5), sticky="ew")
        ctk.CTkLabel(card, text=item.get("title") or "Actualité Star Citizen", wraplength=520, justify="left", text_color=COLORS["text"], font=("Segoe UI Semibold", 12), anchor="w").grid(row=1, column=0, padx=17, sticky="ew")
        source = item.get("source") or "AsteriaxVerse"
        ctk.CTkLabel(card, text=source, text_color=COLORS["muted_2"], font=("Segoe UI", 9), anchor="w").grid(row=2, column=0, padx=17, pady=(6, 13), sticky="ew")
        url = str(item.get("url") or "")
        if url:
            ctk.CTkButton(
                card,
                text="Ouvrir la source  ↗",
                command=lambda link=url: webbrowser.open(link),
                width=118,
                height=29,
                corner_radius=8,
                fg_color="#0D2633",
                hover_color="#123847",
                border_width=1,
                border_color=COLORS["border"],
                text_color=COLORS["accent"],
                font=("Segoe UI Semibold", 9),
            ).grid(row=0, column=1, rowspan=3, padx=(8, 16), pady=15)

    recent = page.app.repo.resolve_entities(page.app.user_store.recent_entries(6))
    final_row = 7
    if recent:
        _section_header(page.scroll, 7, "CONSULTÉS RÉCEMMENT", "Reprends rapidement là où tu t’étais arrêté.")
        final_row = 8
        for index, item in enumerate(recent[:6]):
            column = index % 3
            row = 8 + index // 3
            card = ctk.CTkFrame(page.scroll, fg_color=COLORS["panel_alt"], corner_radius=13, border_width=1, border_color=COLORS["border"])
            card.grid(row=row, column=column if column < 2 else 2, columnspan=1 if column < 2 else 2, padx=(0 if column == 0 else 5, 0 if column == 2 else 5), pady=(0, 10), sticky="nsew")
            card.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(card, text="VAISSEAU" if item.get("kind") == "vehicle" else "ÉQUIPEMENT", text_color=COLORS["muted_2"], font=("Segoe UI Semibold", 8), anchor="w").grid(row=0, column=0, padx=13, pady=(11, 2), sticky="ew")
            ctk.CTkLabel(card, text=str(item.get("name") or "—"), text_color=COLORS["text"], font=("Segoe UI Semibold", 11), anchor="w").grid(row=1, column=0, padx=13, sticky="ew")
            ctk.CTkButton(
                card,
                text="Ouvrir →",
                command=lambda kind=item.get("kind"), entity_id=item.get("entity_id"): page.app.open_entity(str(kind), int(entity_id)),
                height=28,
                corner_radius=7,
                fg_color="transparent",
                hover_color=COLORS["panel_hover"],
                text_color=COLORS["accent"],
                font=("Segoe UI Semibold", 9),
            ).grid(row=2, column=0, padx=10, pady=(5, 8), sticky="ew")
        final_row = 10

    footer = ctk.CTkFrame(page.scroll, fg_color="transparent")
    footer.grid(row=final_row + 1, column=0, columnspan=4, pady=(12, 20), sticky="ew")
    ctk.CTkLabel(
        footer,
        text=f"© AsteriaxVerse · Créé par {APP_AUTHOR}",
        text_color=COLORS["muted_2"],
        font=("Segoe UI", 9),
    ).pack()


def _dashboard_stat(master: Any, column: int, value: str, label: str, caption: str, color: str) -> None:
    card = ctk.CTkFrame(master, fg_color=COLORS["panel"], corner_radius=15, border_width=1, border_color=COLORS["border"])
    card.grid(row=1, column=column, padx=(0 if column == 0 else 5, 0 if column == 3 else 5), pady=(0, 18), sticky="nsew")
    ctk.CTkLabel(card, text=value, text_color=color, font=("Segoe UI Semibold", 24), anchor="w").pack(anchor="w", padx=16, pady=(14, 0))
    ctk.CTkLabel(card, text=label, text_color=COLORS["text"], font=("Segoe UI Semibold", 10), anchor="w").pack(anchor="w", padx=16, pady=(2, 0))
    ctk.CTkLabel(card, text=caption, text_color=COLORS["muted_2"], font=("Segoe UI", 9), anchor="w").pack(anchor="w", padx=16, pady=(2, 14))


def _section_header(master: Any, row: int, title: str, subtitle: str) -> None:
    frame = ctk.CTkFrame(master, fg_color="transparent")
    frame.grid(row=row, column=0, columnspan=4, pady=(7, 10), sticky="ew")
    ctk.CTkLabel(frame, text=title, text_color=COLORS["accent"], font=("Segoe UI Semibold", 9), anchor="w").pack(anchor="w")
    ctk.CTkLabel(frame, text=subtitle, text_color=COLORS["muted"], font=("Segoe UI", 11), anchor="w").pack(anchor="w", pady=(3, 0))


def _news_sort_key(item: dict[str, str]) -> datetime:
    try:
        return datetime.strptime(str(item.get("date") or ""), "%d/%m/%Y")
    except ValueError:
        return datetime.min
