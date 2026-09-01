"""Fast card rendering, ship images and whole-card clicks for Asteriax Verse."""

from __future__ import annotations

import io
import math
import queue
import threading
from collections import OrderedDict
from typing import Any
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

import customtkinter as ctk
from PIL import Image, ImageOps

from core.constants import COLORS, USER_AGENT
from core.database import format_price
from ui import site_ships

_PAGE_SIZE = 20
_BATCH_SIZE = 4
_IMAGE_SIZE = (300, 113)
_IMAGE_DOWNLOAD_LIMIT = 8 * 1024 * 1024
_IMAGE_CACHE_LIMIT = 80
_IMAGE_SEMAPHORE = threading.BoundedSemaphore(4)
_RSI_ROOT = "https://robertsspaceindustries.com"


def install_ship_fastfix(ShipsPage: Any) -> None:
    """Layer the 1.7.5 ship-catalogue fixes over the 1.7.4 card renderer."""
    original_build = ShipsPage._build_content
    original_apply = ShipsPage._apply_vehicle_results

    def build(page: Any) -> None:
        original_build(page)
        page.card_page_size = _PAGE_SIZE
        page._ship_image_cache = OrderedDict()
        page._ship_image_pending = set()
        page._ship_image_queue = queue.SimpleQueue()
        page._ship_image_polling = False
        page._ship_render_token = 0
        _replace_page_size_caption(page)

    def apply(page: Any, *args: Any, **kwargs: Any) -> None:
        old_mode = bool(page.app.performance_mode)
        page.app.performance_mode = True
        try:
            original_apply(page, *args, **kwargs)
        finally:
            page.app.performance_mode = old_mode

    ShipsPage._build_content = build
    ShipsPage._apply_vehicle_results = apply
    site_ships._ships_render_page = _render_page


def _replace_page_size_caption(page: Any) -> None:
    stack = [getattr(page, "site_ship_content", None)]
    while stack:
        widget = stack.pop()
        if widget is None:
            continue
        try:
            if widget.cget("text") == "30 modèles par page":
                widget.configure(text="20 modèles par page · images chargées à la demande")
                return
        except Exception:
            pass
        try:
            stack.extend(widget.winfo_children())
        except Exception:
            pass


def _render_page(page: Any) -> None:
    page._ship_render_token = int(getattr(page, "_ship_render_token", 0)) + 1
    token = page._ship_render_token
    for child in page.card_scroll.winfo_children():
        child.destroy()
    page._ship_card_widgets = {}

    rows = page._ship_rows
    page_size = int(getattr(page, "card_page_size", _PAGE_SIZE) or _PAGE_SIZE)
    total_pages = max(1, math.ceil(len(rows) / page_size))
    page.card_page = max(0, min(total_pages - 1, page.card_page))
    start = page.card_page * page_size
    visible = rows[start : start + page_size]

    page.card_page_label.configure(text=f"Page {page.card_page + 1} / {total_pages}")
    page.card_prev.configure(state="normal" if page.card_page > 0 else "disabled")
    page.card_next.configure(state="normal" if page.card_page + 1 < total_pages else "disabled")

    if not visible:
        ctk.CTkLabel(
            page.card_scroll,
            text="Aucun vaisseau pour ces filtres.",
            text_color=COLORS["muted"],
            font=("Segoe UI", 12),
        ).grid(row=0, column=0, columnspan=2, pady=40)
        return

    def render_batch(offset: int = 0) -> None:
        if token != getattr(page, "_ship_render_token", -1) or not page.winfo_exists():
            return
        end = min(len(visible), offset + _BATCH_SIZE)
        for index in range(offset, end):
            _create_card(page, visible[index], index, token)
        if end < len(visible):
            page.after(1, lambda: render_batch(end))
        else:
            selected = page.table.selected_id()
            if selected.isdigit():
                site_ships._ships_highlight(page, int(selected))

    render_batch()


def _create_card(page: Any, row: dict[str, Any], index: int, token: int) -> None:
    vehicle_id = int(row["id"])
    grid_row, grid_col = divmod(index, 2)
    card = ctk.CTkFrame(
        page.card_scroll,
        fg_color=COLORS["panel"],
        corner_radius=15,
        border_width=1,
        border_color=COLORS["border"],
    )
    card.grid(
        row=grid_row,
        column=grid_col,
        padx=(0 if grid_col == 0 else 6, 6 if grid_col == 0 else 0),
        pady=(0, 10),
        sticky="nsew",
    )
    card.grid_columnconfigure(0, weight=1)
    page._ship_card_widgets[vehicle_id] = card

    image_label = ctk.CTkLabel(
        card,
        text="Chargement de l’image…" if row.get("url_photo") else "Image non disponible",
        height=_IMAGE_SIZE[1],
        fg_color=COLORS["panel_alt"],
        corner_radius=11,
        text_color=COLORS["muted_2"],
        font=("Segoe UI", 9),
    )
    image_label.grid(row=0, column=0, padx=12, pady=(12, 9), sticky="ew")

    kind = "VÉHICULE TERRESTRE" if row.get("is_ground_vehicle") else "VAISSEAU"
    kind_label = ctk.CTkLabel(
        card, text=kind, text_color=COLORS["accent"], font=("Segoe UI Semibold", 8), anchor="w"
    )
    kind_label.grid(row=1, column=0, padx=14, sticky="ew")
    name_label = ctk.CTkLabel(
        card,
        text=str(row.get("name") or "Modèle"),
        wraplength=285,
        justify="left",
        text_color=COLORS["text"],
        font=("Segoe UI Semibold", 15),
        anchor="w",
    )
    name_label.grid(row=2, column=0, padx=14, pady=(2, 0), sticky="ew")
    maker_label = ctk.CTkLabel(
        card,
        text=str(row.get("manufacturer") or "Constructeur inconnu"),
        text_color=COLORS["muted"],
        font=("Segoe UI", 10),
        anchor="w",
    )
    maker_label.grid(row=3, column=0, padx=14, pady=(2, 8), sticky="ew")

    info = "  ·  ".join(
        part
        for part in (
            str(row.get("vehicle_class") or "Multirôle"),
            f"{row.get('scu', 0):g} SCU" if row.get("scu") else "",
        )
        if part
    )
    info_label = ctk.CTkLabel(
        card,
        text=info,
        text_color=COLORS["muted_2"],
        font=("Segoe UI", 9),
        anchor="w",
    )
    info_label.grid(row=4, column=0, padx=14, sticky="ew")
    price_label = ctk.CTkLabel(
        card,
        text=format_price(row.get("price_min")),
        text_color=COLORS["accent"],
        font=("Segoe UI Semibold", 12),
        anchor="w",
    )
    price_label.grid(row=5, column=0, padx=14, pady=(4, 8), sticky="ew")

    buttons = ctk.CTkFrame(card, fg_color="transparent")
    buttons.grid(row=6, column=0, padx=12, pady=(0, 12), sticky="ew")
    buttons.grid_columnconfigure((0, 1), weight=1, uniform="cardbutton")
    ctk.CTkButton(
        buttons,
        text="Voir la fiche →",
        command=lambda vid=vehicle_id: site_ships._ships_select(page, vid),
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

    command = lambda _event=None, vid=vehicle_id: site_ships._ships_select(page, vid)
    for widget in (card, image_label, kind_label, name_label, maker_label, info_label, price_label):
        widget.bind("<Button-1>", command, add="+")

    _load_image(page, image_label, str(row.get("url_photo") or ""), token)


def _normalise_url(raw: str) -> str:
    value = str(raw or "").strip()
    if not value:
        return ""
    if value.startswith("//"):
        value = "https:" + value
    elif value.startswith("/"):
        value = urljoin(_RSI_ROOT, value)
    parsed = urlparse(value)
    return value if parsed.scheme in {"http", "https"} and parsed.netloc else ""


def _load_image(page: Any, label: Any, raw_url: str, token: int) -> None:
    url = _normalise_url(raw_url)
    if not url:
        return

    cache: OrderedDict[str, Any] = page._ship_image_cache
    cached = cache.get(url)
    if cached is not None:
        cache.move_to_end(url)
        _apply_image(page, label, cached, token)
        return

    key = (url, id(label), token)
    if key in page._ship_image_pending:
        return
    page._ship_image_pending.add(key)

    def worker() -> None:
        image: Image.Image | None = None
        try:
            with _IMAGE_SEMAPHORE:
                request = Request(
                    url,
                    headers={
                        "User-Agent": USER_AGENT,
                        "Accept": "image/avif,image/webp,image/png,image/jpeg,image/*;q=0.8,*/*;q=0.5",
                    },
                )
                with urlopen(request, timeout=5) as response:
                    payload = response.read(_IMAGE_DOWNLOAD_LIMIT + 1)
                if len(payload) > _IMAGE_DOWNLOAD_LIMIT:
                    raise ValueError("image trop volumineuse")
                with Image.open(io.BytesIO(payload)) as source:
                    converted = source.convert("RGB")
                    image = ImageOps.fit(converted, _IMAGE_SIZE, method=Image.Resampling.LANCZOS)
        except Exception:
            image = None
        page._ship_image_queue.put((key, url, label, token, image))

    threading.Thread(target=worker, name=f"ship-image-{token}", daemon=True).start()
    _ensure_image_poll(page)


def _ensure_image_poll(page: Any) -> None:
    if page._ship_image_polling:
        return
    page._ship_image_polling = True
    page.after(35, lambda: _poll_images(page))


def _poll_images(page: Any) -> None:
    if not page.winfo_exists():
        return
    processed = 0
    while processed < 8:
        try:
            key, url, label, token, image = page._ship_image_queue.get_nowait()
        except queue.Empty:
            break
        page._ship_image_pending.discard(key)
        processed += 1
        if image is None:
            if token == getattr(page, "_ship_render_token", -1):
                try:
                    if label.winfo_exists():
                        label.configure(text="Image indisponible")
                except Exception:
                    pass
            continue
        ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=_IMAGE_SIZE)
        cache: OrderedDict[str, Any] = page._ship_image_cache
        cache[url] = ctk_image
        cache.move_to_end(url)
        while len(cache) > _IMAGE_CACHE_LIMIT:
            cache.popitem(last=False)
        _apply_image(page, label, ctk_image, token)

    if page._ship_image_pending or not page._ship_image_queue.empty():
        page.after(35, lambda: _poll_images(page))
    else:
        page._ship_image_polling = False


def _apply_image(page: Any, label: Any, image: Any, token: int) -> None:
    if token != getattr(page, "_ship_render_token", -1):
        return
    try:
        if label.winfo_exists():
            label.configure(image=image, text="")
    except Exception:
        pass
