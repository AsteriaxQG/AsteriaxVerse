"""Site-inspired desktop shell for Asteriax Verse.

This module keeps the existing CustomTkinter pages and data logic intact while
moving the primary navigation into a compact horizontal top bar, matching the
visual language of the AsteriaxVerse website.
"""

from __future__ import annotations

from typing import Any

import customtkinter as ctk

from core.constants import APP_AUTHOR, APP_VERSION, COLORS

_INSTALLED = False


def install_site_shell() -> None:
    """Patch the desktop shell before :func:`ui.app.run` creates the window."""
    global _INSTALLED
    if _INSTALLED:
        return

    from ui.app import AsteriaxApp

    original_init = AsteriaxApp.__init__
    original_show_page = AsteriaxApp.show_page

    def themed_init(self: Any, *args: Any, **kwargs: Any) -> None:
        original_init(self, *args, **kwargs)
        _apply_site_layout(self)

    def themed_show_page(self: Any, name: str, *args: Any, **kwargs: Any) -> Any:
        result = original_show_page(self, name, *args, **kwargs)
        _refresh_active_tab(self, name)
        return result

    AsteriaxApp.__init__ = themed_init
    AsteriaxApp.show_page = themed_show_page
    _INSTALLED = True


def _apply_site_layout(app: Any) -> None:
    """Replace the visible sidebar with a site-like horizontal navigation bar."""
    try:
        app.sidebar.grid_remove()
    except Exception:
        pass

    app.grid_rowconfigure(0, weight=0)
    app.grid_rowconfigure(1, weight=1)
    app.grid_columnconfigure(0, weight=1)
    app.grid_columnconfigure(1, weight=0)

    app.main.grid_configure(row=1, column=0, columnspan=2, sticky="nsew")
    app.main.configure(fg_color=COLORS["background"])

    try:
        app.sidebar_toggle.grid_remove()
    except Exception:
        pass

    try:
        app.page_container.grid_configure(padx=26, pady=(0, 18))
    except Exception:
        pass

    try:
        header = app.page_title.master
        header.configure(fg_color="transparent", height=82)
        app.page_title.configure(font=("Segoe UI Semibold", 25))
        app.page_subtitle.configure(font=("Segoe UI", 12), text_color=COLORS["muted"])
    except Exception:
        pass

    topbar = ctk.CTkFrame(
        app,
        height=74,
        corner_radius=0,
        fg_color="#08131C",
        border_width=1,
        border_color="#193342",
    )
    topbar.grid(row=0, column=0, columnspan=2, sticky="ew")
    topbar.grid_propagate(False)
    topbar.grid_columnconfigure(1, weight=1)
    app.site_topbar = topbar

    brand = ctk.CTkFrame(topbar, fg_color="transparent")
    brand.grid(row=0, column=0, padx=(22, 20), pady=10, sticky="w")
    ctk.CTkLabel(
        brand,
        text="AsteriaxVerse",
        text_color=COLORS["text"],
        font=("Segoe UI Semibold", 18),
        anchor="w",
    ).grid(row=0, column=0, sticky="w")
    ctk.CTkLabel(
        brand,
        text=f"Star Citizen Companion  ·  par {APP_AUTHOR}",
        text_color=COLORS["muted_2"],
        font=("Segoe UI", 9),
        anchor="w",
    ).grid(row=1, column=0, sticky="w")

    nav = ctk.CTkFrame(
        topbar,
        fg_color="#0A1822",
        corner_radius=12,
        border_width=1,
        border_color=COLORS["border"],
    )
    nav.grid(row=0, column=1, padx=(0, 14), pady=13, sticky="e")
    app.site_nav_buttons = {}

    entries = [
        ("dashboard", "Accueil"),
        ("ships", "Vaisseaux"),
        ("equipment", "Équipements"),
        ("locations", "Explorer"),
        ("compare", "Comparateur"),
        ("updates", "Mises à jour"),
        ("settings", "Réglages"),
    ]

    for column, (name, label) in enumerate(entries):
        button = ctk.CTkButton(
            nav,
            text=label,
            command=lambda page=name: app.show_page(page),
            width=82 if name not in {"equipment", "compare", "updates"} else 102,
            height=36,
            corner_radius=9,
            fg_color="transparent",
            hover_color="#102B39",
            border_width=0,
            text_color=COLORS["muted"],
            font=("Segoe UI Semibold", 10),
        )
        button.grid(row=0, column=column, padx=(5 if column == 0 else 2, 5 if column == len(entries) - 1 else 2), pady=5)
        app.site_nav_buttons[name] = button

    search = ctk.CTkButton(
        topbar,
        text="⌕  Rechercher",
        command=app.open_global_search,
        width=124,
        height=40,
        corner_radius=10,
        fg_color="#0D202B",
        hover_color="#123140",
        border_width=1,
        border_color="#2A5062",
        text_color="#DFF8FF",
        font=("Segoe UI Semibold", 10),
    )
    search.grid(row=0, column=2, padx=(0, 20), pady=13, sticky="e")

    version = ctk.CTkLabel(
        topbar,
        text=f"v{APP_VERSION}",
        text_color=COLORS["muted_2"],
        font=("Segoe UI", 8),
    )
    version.place(relx=1.0, x=-23, y=58, anchor="e")

    _refresh_active_tab(app, getattr(app, "current_page", "dashboard"))


def _refresh_active_tab(app: Any, active_name: str) -> None:
    buttons = getattr(app, "site_nav_buttons", {})
    for name, button in buttons.items():
        active = name == active_name
        try:
            button.configure(
                fg_color="#123442" if active else "transparent",
                text_color="#7FEAFF" if active else COLORS["muted"],
                border_width=1 if active else 0,
                border_color="#2B728B" if active else COLORS["border"],
            )
        except Exception:
            continue
