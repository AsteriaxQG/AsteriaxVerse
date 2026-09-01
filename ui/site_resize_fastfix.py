"""Reduce resize/maximize jank in the Asteriax Verse desktop shell."""

from __future__ import annotations

from typing import Any

from core.constants import COLORS
from ui import site_shell
from ui import site_ships_fastfix

_RESIZE_SETTLE_MS = 150
_NAV_SETTLE_MS = 80


def install_resize_fastfix() -> None:
    """Patch resize handling before the application window is created."""
    site_shell._schedule_responsive_nav = _schedule_responsive_nav
    site_shell._responsive_nav = _responsive_nav

    original_poll = site_ships_fastfix._poll_images

    def quiet_image_poll(page: Any) -> None:
        if getattr(page.app, "_site_resize_in_progress", False):
            page.after(90, lambda: quiet_image_poll(page))
            return
        original_poll(page)

    site_ships_fastfix._poll_images = quiet_image_poll


def _resize_mode(width: int) -> str:
    if width < 1040:
        return "tiny"
    if width < 1210:
        return "compact"
    return "full"


def _schedule_responsive_nav(app: Any, event: Any) -> None:
    if event.widget is not app:
        return
    try:
        width = max(1, int(event.width))
        height = max(1, int(event.height))
    except Exception:
        return

    previous = getattr(app, "_site_last_root_size", None)
    if previous == (width, height):
        return
    app._site_last_root_size = (width, height)
    app._site_resize_in_progress = True

    desired_mode = _resize_mode(width)
    if desired_mode != getattr(app, "_site_responsive_mode", None):
        try:
            pending = getattr(app, "_site_resize_after", None)
            if pending:
                app.after_cancel(pending)
        except Exception:
            pass
        app._site_resize_after = app.after(
            _NAV_SETTLE_MS,
            lambda mode=desired_mode: _apply_responsive_mode(app, mode),
        )

    _suspend_heavy_ship_content(app)

    try:
        pending_finish = getattr(app, "_site_resize_finish_after", None)
        if pending_finish:
            app.after_cancel(pending_finish)
    except Exception:
        pass
    app._site_resize_finish_after = app.after(
        _RESIZE_SETTLE_MS,
        lambda: _finish_resize(app),
    )


def _apply_responsive_mode(app: Any, mode: str) -> None:
    try:
        current_mode = _resize_mode(int(app.winfo_width()))
    except Exception:
        current_mode = mode
    if current_mode != mode:
        return
    _responsive_nav(app, forced_mode=mode)


def _responsive_nav(app: Any, forced_mode: str | None = None) -> None:
    try:
        width = int(app.winfo_width())
    except Exception:
        return
    mode = forced_mode or _resize_mode(width)
    if mode == getattr(app, "_site_responsive_mode", None):
        return

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
        if mode == "tiny":
            text = tiny_labels[name]
            width_value = 46
        elif mode == "compact":
            text = short_labels[name]
            width_value = 66 if name not in {"equipment", "compare", "settings"} else 72
        else:
            text = app.site_nav_labels[name]
            width_value = 84 if name not in {"equipment", "compare", "updates"} else 102
        try:
            button.configure(text=text, width=width_value)
        except Exception:
            pass

    try:
        if mode == "full":
            app.site_brand_subtitle.grid()
        else:
            app.site_brand_subtitle.grid_remove()
        app.site_search_button.configure(
            text="⌕" if mode == "tiny" else "⌕  Rechercher",
            width=48 if mode == "tiny" else 126,
        )
    except Exception:
        pass

    app._site_responsive_mode = mode


def _suspend_heavy_ship_content(app: Any) -> None:
    if getattr(app, "current_page", "") != "ships":
        return
    page = getattr(app, "pages", {}).get("ships")
    content = getattr(page, "site_ship_content", None)
    if content is None or getattr(app, "_site_ship_content_suspended", False):
        return
    try:
        if content.winfo_ismapped():
            content.grid_remove()
            app._site_ship_content_suspended = True
    except Exception:
        pass


def _finish_resize(app: Any) -> None:
    app._site_resize_in_progress = False
    try:
        _responsive_nav(app)
    except Exception:
        pass

    if getattr(app, "_site_ship_content_suspended", False):
        page = getattr(app, "pages", {}).get("ships")
        content = getattr(page, "site_ship_content", None)
        try:
            if content is not None and getattr(app, "current_page", "") == "ships":
                content.grid()
        except Exception:
            pass
        app._site_ship_content_suspended = False
