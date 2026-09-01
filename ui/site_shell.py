"""Website-inspired desktop shell for Asteriax Verse."""

from __future__ import annotations

from typing import Any

import customtkinter as ctk
from tkinter import ttk

from core.constants import APP_AUTHOR, APP_VERSION, COLORS
from ui.site_dashboard import dashboard_refresh
from ui.site_ships import install_ship_cards

_INSTALLED = False

_SITE_COLORS = {
    "background": "#050B11",
    "sidebar": "#07131C",
    "panel": "#0B1721",
    "panel_alt": "#0E202C",
    "panel_hover": "#12303D",
    "border": "#193746",
    "accent": "#4ED9FF",
    "accent_hover": "#7BE6FF",
    "accent_dark": "#0E3545",
    "blue": "#76A9FF",
    "warning": "#F4C15D",
    "danger": "#FF7885",
    "text": "#F2F8FC",
    "muted": "#94AABC",
    "muted_2": "#60798B",
    "success": "#69E2A7",
}

def install_site_shell() -> None:
    """Patch the desktop shell before :func:`ui.app.run` creates the window."""
    global _INSTALLED
    if _INSTALLED:
        return

    COLORS.update(_SITE_COLORS)

    from ui import app as app_module

    AsteriaxApp = app_module.AsteriaxApp
    DashboardPage = app_module.DashboardPage
    ShipsPage = app_module.ShipsPage

    original_init = AsteriaxApp.__init__
    original_show_page = AsteriaxApp.show_page

    DashboardPage.title = "Accueil"
    DashboardPage.subtitle = "Le Verse, plus clair. Directement sur ton bureau."
    DashboardPage.refresh_data = dashboard_refresh
    install_ship_cards(ShipsPage)

    def themed_init(self: Any, *args: Any, **kwargs: Any) -> None:
        original_init(self, *args, **kwargs)
        _apply_site_layout(self)
        _apply_tree_styles(self)
        self.after(40, lambda: _style_current_page(self))

    def themed_show_page(self: Any, name: str, *args: Any, **kwargs: Any) -> Any:
        result = original_show_page(self, name, *args, **kwargs)
        _refresh_active_tab(self, name)
        _toggle_page_header(self, name)
        self.after(25, lambda: _style_current_page(self))
        return result

    AsteriaxApp.__init__ = themed_init
    AsteriaxApp.show_page = themed_show_page
    _INSTALLED = True


def _apply_site_layout(app: Any) -> None:
    try:
        app.sidebar.grid_remove()
    except Exception:
        pass

    app.configure(fg_color=COLORS["background"])
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
        app.page_container.grid_configure(padx=28, pady=(0, 20))
    except Exception:
        pass

    try:
        header = app.page_title.master
        app.site_page_header = header
        header.configure(fg_color="transparent", height=76)
        app.page_title.configure(font=("Segoe UI Semibold", 27), text_color=COLORS["text"])
        app.page_subtitle.configure(font=("Segoe UI", 12), text_color=COLORS["muted"])
    except Exception:
        pass

    topbar = ctk.CTkFrame(
        app,
        height=78,
        corner_radius=0,
        fg_color="#07131C",
        border_width=1,
        border_color="#193746",
    )
    topbar.grid(row=0, column=0, columnspan=2, sticky="ew")
    topbar.grid_propagate(False)
    topbar.grid_columnconfigure(1, weight=1)
    app.site_topbar = topbar

    brand = ctk.CTkFrame(topbar, fg_color="transparent")
    brand.grid(row=0, column=0, padx=(24, 18), pady=11, sticky="w")
    app.site_brand = brand
    ctk.CTkLabel(
        brand,
        text="ASTERIAXVERSE",
        text_color=COLORS["accent"],
        font=("Segoe UI Semibold", 10),
        anchor="w",
    ).grid(row=0, column=0, sticky="w")
    ctk.CTkLabel(
        brand,
        text="Star Citizen Companion",
        text_color=COLORS["text"],
        font=("Segoe UI Semibold", 17),
        anchor="w",
    ).grid(row=1, column=0, sticky="w")
    app.site_brand_subtitle = ctk.CTkLabel(
        brand,
        text=f"Créé par {APP_AUTHOR}",
        text_color=COLORS["muted_2"],
        font=("Segoe UI", 9),
        anchor="w",
    )
    app.site_brand_subtitle.grid(row=2, column=0, sticky="w")

    nav = ctk.CTkFrame(
        topbar,
        fg_color="#091B26",
        corner_radius=12,
        border_width=1,
        border_color=COLORS["border"],
    )
    nav.grid(row=0, column=1, padx=(0, 14), pady=14, sticky="e")
    app.site_nav = nav
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
    app.site_nav_labels = {name: label for name, label in entries}

    for column, (name, label) in enumerate(entries):
        button = ctk.CTkButton(
            nav,
            text=label,
            command=lambda page=name: app.show_page(page),
            width=84 if name not in {"equipment", "compare", "updates"} else 102,
            height=38,
            corner_radius=9,
            fg_color="transparent",
            hover_color="#103141",
            border_width=0,
            text_color=COLORS["muted"],
            font=("Segoe UI Semibold", 10),
        )
        button.grid(
            row=0,
            column=column,
            padx=(5 if column == 0 else 2, 5 if column == len(entries) - 1 else 2),
            pady=5,
        )
        app.site_nav_buttons[name] = button

    search = ctk.CTkButton(
        topbar,
        text="⌕  Rechercher",
        command=app.open_global_search,
        width=126,
        height=42,
        corner_radius=10,
        fg_color="#0D2633",
        hover_color="#123847",
        border_width=1,
        border_color="#2B6073",
        text_color="#E5FAFF",
        font=("Segoe UI Semibold", 10),
    )
    search.grid(row=0, column=2, padx=(0, 22), pady=14, sticky="e")
    app.site_search_button = search

    version = ctk.CTkLabel(
        topbar,
        text=f"v{APP_VERSION}",
        text_color=COLORS["muted_2"],
        font=("Segoe UI", 8),
    )
    version.place(relx=1.0, x=-25, y=62, anchor="e")

    app.bind("<Configure>", lambda event: _schedule_responsive_nav(app, event), add="+")
    _refresh_active_tab(app, getattr(app, "current_page", "dashboard"))
    _toggle_page_header(app, getattr(app, "current_page", "dashboard"))


def _schedule_responsive_nav(app: Any, event: Any) -> None:
    if event.widget is not app:
        return
    try:
        if getattr(app, "_site_resize_after", None):
            app.after_cancel(app._site_resize_after)
        app._site_resize_after = app.after(90, lambda: _responsive_nav(app))
    except Exception:
        pass


def _responsive_nav(app: Any) -> None:
    try:
        width = int(app.winfo_width())
    except Exception:
        return
    compact = width < 1210
    tiny = width < 1040
    short_labels = {
        "dashboard": "Accueil",
        "ships": "Vaisseaux",
        "equipment": "Équip.",
        "locations": "Explorer",
        "compare": "Comparer",
        "updates": "MAJ",
        "settings": "Réglages",
    }
    tiny_labels = {
        "dashboard": "⌂",
        "ships": "✦",
        "equipment": "⚙",
        "locations": "⌖",
        "compare": "⇄",
        "updates": "↻",
        "settings": "⋯",
    }
    for name, button in getattr(app, "site_nav_buttons", {}).items():
        if tiny:
            text = tiny_labels[name]
            width_value = 46
        elif compact:
            text = short_labels[name]
            width_value = 66 if name not in {"equipment", "compare", "settings"} else 72
        else:
            text = app.site_nav_labels[name]
            width_value = 84 if name not in {"equipment", "compare", "updates"} else 102
        button.configure(text=text, width=width_value)
    try:
        app.site_brand_subtitle.grid_remove() if compact else app.site_brand_subtitle.grid()
        app.site_search_button.configure(text="⌕" if tiny else "⌕  Rechercher", width=48 if tiny else 126)
    except Exception:
        pass


def _toggle_page_header(app: Any, page_name: str) -> None:
    header = getattr(app, "site_page_header", None)
    if header is None:
        return
    try:
        if page_name == "dashboard":
            header.grid_remove()
        else:
            header.grid()
    except Exception:
        pass


def _refresh_active_tab(app: Any, active_name: str) -> None:
    for name, button in getattr(app, "site_nav_buttons", {}).items():
        active = name == active_name
        try:
            button.configure(
                fg_color="#123B4B" if active else "transparent",
                text_color="#8DEAFF" if active else COLORS["muted"],
                border_width=1 if active else 0,
                border_color="#327A93" if active else COLORS["border"],
            )
        except Exception:
            continue


def _apply_tree_styles(app: Any) -> None:
    try:
        style = ttk.Style(app)
        for name in ("Treeview", "Asteriax.Treeview"):
            style.configure(
                name,
                background=COLORS["panel"],
                fieldbackground=COLORS["panel"],
                foreground=COLORS["text"],
                borderwidth=0,
                relief="flat",
                rowheight=34,
                font=("Segoe UI", 11),
            )
            style.map(
                name,
                background=[("selected", "#123B4B")],
                foreground=[("selected", COLORS["text"])],
            )
        for name in ("Treeview.Heading", "Asteriax.Treeview.Heading"):
            style.configure(
                name,
                background="#0C1D28",
                foreground=COLORS["muted"],
                relief="flat",
                borderwidth=0,
                font=("Segoe UI Semibold", 10),
                padding=(8, 10),
            )
    except Exception:
        pass


def _style_current_page(app: Any) -> None:
    page = getattr(app, "pages", {}).get(getattr(app, "current_page", ""))
    if page is None:
        return
    _style_widget_tree(page)


def _style_widget_tree(widget: Any, depth: int = 0) -> None:
    if depth > 8:
        return
    try:
        if isinstance(widget, ctk.CTkButton):
            fg = widget.cget("fg_color")
            primary = fg == COLORS["accent"]
            widget.configure(
                corner_radius=9,
                border_color=COLORS["border"] if not primary else COLORS["accent"],
                text_color=COLORS["background"] if primary else widget.cget("text_color"),
            )
        elif isinstance(widget, ctk.CTkEntry):
            widget.configure(
                height=max(38, int(widget.cget("height"))),
                corner_radius=9,
                border_color=COLORS["border"],
                fg_color=COLORS["panel_alt"],
            )
        elif isinstance(widget, ctk.CTkComboBox):
            widget.configure(
                height=max(38, int(widget.cget("height"))),
                corner_radius=9,
                border_color=COLORS["border"],
                fg_color=COLORS["panel_alt"],
                button_color="#123442",
                button_hover_color="#18485A",
            )
        elif isinstance(widget, ctk.CTkOptionMenu):
            widget.configure(
                height=max(38, int(widget.cget("height"))),
                corner_radius=9,
                fg_color=COLORS["panel_alt"],
                button_color="#123442",
                button_hover_color="#18485A",
            )
        elif isinstance(widget, ctk.CTkSegmentedButton):
            widget.configure(
                height=max(38, int(widget.cget("height"))),
                corner_radius=9,
                selected_color="#17495B",
                selected_hover_color="#1D5A70",
                unselected_color=COLORS["panel_alt"],
                unselected_hover_color=COLORS["panel_hover"],
            )
        elif isinstance(widget, ctk.CTkScrollableFrame):
            widget.configure(
                scrollbar_button_color=COLORS["border"],
                scrollbar_button_hover_color="#245269",
            )
        elif type(widget) is ctk.CTkFrame:
            fg = widget.cget("fg_color")
            if fg != "transparent":
                widget.configure(corner_radius=14)
        elif isinstance(widget, (ctk.CTkCheckBox, ctk.CTkSwitch)):
            widget.configure(fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"])
    except Exception:
        pass
    try:
        for child in widget.winfo_children():
            _style_widget_tree(child, depth + 1)
    except Exception:
        pass
