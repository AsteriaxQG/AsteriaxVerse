"""Reusable visual building blocks for the desktop interface."""

from __future__ import annotations

import tkinter as tk
import re
from tkinter import ttk
from typing import Any, Callable, Iterable

import customtkinter as ctk

from core.constants import COLORS


def configure_ttk_styles(root: tk.Misc) -> None:
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure(
        "Asteriax.Treeview",
        background=COLORS["panel"],
        fieldbackground=COLORS["panel"],
        foreground=COLORS["text"],
        bordercolor=COLORS["panel"],
        lightcolor=COLORS["panel"],
        darkcolor=COLORS["panel"],
        borderwidth=0,
        relief="flat",
        rowheight=44,
        font=("Segoe UI", 13),
    )
    # ``clam`` draws a square field border around Treeview widgets even when
    # ``borderwidth`` is zero.  Keeping only the tree area lets the rounded
    # CustomTkinter shell provide the visible outline instead.
    style.layout(
        "Asteriax.Treeview",
        [("Treeview.treearea", {"sticky": "nswe"})],
    )
    style.map(
        "Asteriax.Treeview",
        background=[("selected", COLORS["accent_dark"])],
        foreground=[("selected", COLORS["text"])],
    )
    style.configure(
        "Asteriax.Treeview.Heading",
        background=COLORS["panel_alt"],
        foreground=COLORS["muted"],
        bordercolor=COLORS["border"],
        lightcolor=COLORS["border"],
        darkcolor=COLORS["border"],
        borderwidth=0,
        relief="flat",
        padding=(11, 11),
        font=("Segoe UI Semibold", 13),
    )
    style.map(
        "Asteriax.Treeview.Heading",
        background=[("active", COLORS["panel_hover"])],
        foreground=[("active", COLORS["text"])],
    )
    style.configure(
        "Asteriax.Vertical.TScrollbar",
        troughcolor=COLORS["panel"],
        background=COLORS["border"],
        bordercolor=COLORS["panel"],
        arrowcolor=COLORS["muted"],
        gripcount=0,
    )
    style.configure(
        "Asteriax.Horizontal.TScrollbar",
        troughcolor=COLORS["panel"],
        background=COLORS["border"],
        bordercolor=COLORS["panel"],
        arrowcolor=COLORS["muted"],
        gripcount=0,
    )


class StatCard(ctk.CTkFrame):
    def __init__(self, master: Any, *, value: str, label: str, caption: str, color: str):
        super().__init__(
            master,
            fg_color=COLORS["panel"],
            corner_radius=14,
            border_width=1,
            border_color=COLORS["border"],
        )
        self.grid_columnconfigure(1, weight=1)
        marker = ctk.CTkFrame(self, width=5, height=58, corner_radius=3, fg_color=color)
        marker.grid(row=0, column=0, rowspan=3, padx=(16, 14), pady=18, sticky="ns")
        marker.grid_propagate(False)
        ctk.CTkLabel(
            self,
            text=value,
            font=("Segoe UI Semibold", 27),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=1, padx=(0, 12), pady=(14, 0), sticky="ew")
        ctk.CTkLabel(
            self,
            text=label,
            font=("Segoe UI Semibold", 13),
            text_color=COLORS["muted"],
            anchor="w",
        ).grid(row=1, column=1, padx=(0, 12), sticky="ew")
        ctk.CTkLabel(
            self,
            text=caption,
            font=("Segoe UI", 11),
            text_color=COLORS["muted_2"],
            anchor="w",
        ).grid(row=2, column=1, padx=(0, 12), pady=(0, 13), sticky="ew")


class SectionTitle(ctk.CTkFrame):
    def __init__(self, master: Any, title: str, subtitle: str = ""):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            self,
            text=title,
            font=("Segoe UI Semibold", 17),
            text_color=COLORS["text"],
            anchor="w",
        ).grid(row=0, column=0, sticky="ew")
        if subtitle:
            ctk.CTkLabel(
                self,
                text=subtitle,
                font=("Segoe UI", 12),
                text_color=COLORS["muted"],
                anchor="w",
            ).grid(row=1, column=0, pady=(2, 0), sticky="ew")


class TreeTable(ctk.CTkFrame):
    """Dark ttk.Treeview wrapped in a rounded CustomTkinter panel."""

    _CENTERED_VALUE_COLUMNS = frozenset({"price", "location"})

    @classmethod
    def display_anchor(cls, column_id: str, requested_anchor: str) -> str:
        """Keep price and location values centred under their headings."""
        if column_id in cls._CENTERED_VALUE_COLUMNS:
            return "center"
        return requested_anchor

    def __init__(
        self,
        master: Any,
        columns: list[tuple[str, str, int, str]],
        *,
        on_select: Callable[[str], None] | None = None,
        on_double_click: Callable[[str], None] | None = None,
        on_sort: Callable[[int, bool], None] | None = None,
        page_size: int | None = None,
    ):
        super().__init__(
            master,
            fg_color=COLORS["panel"],
            corner_radius=14,
            border_width=1,
            border_color=COLORS["border"],
        )
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._columns = columns
        self._rows: list[tuple[str, tuple[Any, ...], bool]] = []
        self._sort_column: int | None = None
        self._sort_reverse = False
        self._on_sort = on_sort
        self._page_size = max(25, int(page_size)) if page_size else None
        self._page_index = 0
        self.table_shell = ctk.CTkFrame(
            self,
            fg_color=COLORS["panel_alt"],
            corner_radius=11,
            border_width=0,
        )
        self.table_shell.grid(row=0, column=0, padx=8, pady=(8, 6), sticky="nsew")
        self.table_shell.grid_rowconfigure(0, weight=1)
        self.table_shell.grid_columnconfigure(0, weight=1)
        ids = [column[0] for column in columns]
        self.tree = ttk.Treeview(
            self.table_shell,
            columns=ids,
            show="headings",
            style="Asteriax.Treeview",
            selectmode="browse",
        )
        for index, (column_id, heading, width, anchor) in enumerate(columns):
            self.tree.heading(
                column_id,
                text=heading,
                command=lambda position=index: self.sort_by(position),
            )
            self.tree.column(
                column_id,
                width=width,
                minwidth=45,
                anchor=self.display_anchor(column_id, anchor),
                stretch=column_id in {"name", "location"},
            )
        scrollbar = ttk.Scrollbar(
            self.table_shell,
            orient="vertical",
            command=self.tree.yview,
            style="Asteriax.Vertical.TScrollbar",
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.grid(row=0, column=0, padx=(6, 0), pady=(6, 0), sticky="nsew")
        scrollbar.grid(row=0, column=1, padx=(2, 6), pady=(7, 1), sticky="ns")
        horizontal = ttk.Scrollbar(
            self.table_shell,
            orient="horizontal",
            command=self.tree.xview,
            style="Asteriax.Horizontal.TScrollbar",
        )
        self.tree.configure(xscrollcommand=horizontal.set)
        horizontal.grid(row=1, column=0, padx=(7, 1), pady=(2, 6), sticky="ew")
        self.page_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.page_bar.grid(row=1, column=0, padx=8, pady=(0, 8), sticky="ew")
        self.page_bar.grid_columnconfigure(1, weight=1)
        self.previous_page_button = ctk.CTkButton(
            self.page_bar,
            text="‹  Précédent",
            command=lambda: self.change_page(-1),
            width=105,
            height=28,
            corner_radius=8,
            fg_color=COLORS["panel_alt"],
            hover_color=COLORS["panel_hover"],
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["muted"],
            font=("Segoe UI Semibold", 10),
        )
        self.previous_page_button.grid(row=0, column=0)
        self.page_label = ctk.CTkLabel(
            self.page_bar,
            text="",
            font=("Segoe UI Semibold", 10),
            text_color=COLORS["muted"],
        )
        self.page_label.grid(row=0, column=1, padx=10)
        self.next_page_button = ctk.CTkButton(
            self.page_bar,
            text="Suivant  ›",
            command=lambda: self.change_page(1),
            width=105,
            height=28,
            corner_radius=8,
            fg_color=COLORS["panel_alt"],
            hover_color=COLORS["panel_hover"],
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["muted"],
            font=("Segoe UI Semibold", 10),
        )
        self.next_page_button.grid(row=0, column=2)
        if self._page_size is None:
            self.page_bar.grid_remove()
        self.tree.tag_configure("odd", background=COLORS["panel_alt"])
        self.tree.tag_configure("favourite", foreground=COLORS["warning"])
        if on_select:
            self.tree.bind(
                "<<TreeviewSelect>>",
                lambda _event: on_select(self.selected_id()),
                add="+",
            )
        if on_double_click:
            self.tree.bind(
                "<Double-1>",
                lambda _event: on_double_click(self.selected_id()),
                add="+",
            )

    def selected_id(self) -> str:
        selection = self.tree.selection()
        return selection[0] if selection else ""

    def clear(self) -> None:
        children = self.tree.get_children()
        if children:
            self.tree.delete(*children)

    def populate(
        self,
        rows: Iterable[tuple[str, tuple[Any, ...], bool]],
        *,
        keep_page: bool = False,
    ) -> None:
        self._rows = list(rows)
        if self._sort_column is not None:
            self._sort_rows()
        if not keep_page:
            self._page_index = 0
        self._clamp_page()
        self._render_rows()

    @staticmethod
    def _natural_sort_key(value: Any) -> tuple[int, Any]:
        if value is None:
            return 2, ""
        if isinstance(value, (int, float)):
            return 0, float(value)
        text = str(value).replace("★", "").strip()
        if not text or text == "—":
            return 2, ""
        compact = text.replace("\u202f", "").replace(" ", "")
        numeric_patterns = (
            r"[-+]?\d+(?:[.,]\d+)?aUEC",
            r"S\d+(?:[.,]\d+)?",
            r"[-+]?\d+(?:[.,]\d+)?m",
            r"[-+]?\d+(?:[.,]\d+)?",
        )
        if any(re.fullmatch(pattern, compact, flags=re.IGNORECASE) for pattern in numeric_patterns):
            match = re.search(r"[-+]?\d+(?:[.,]\d+)?", compact)
            if match:
                return 0, float(match.group(0).replace(",", "."))
        return 1, text.casefold()

    def sort_by(self, column_index: int) -> None:
        if self._sort_column == column_index:
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_column = column_index
            self._sort_reverse = False
        selected = self.selected_id()
        self._sort_rows()
        self._page_index = 0
        self._update_headings()
        self._render_rows()
        if selected:
            self.select(selected)
        if self._on_sort:
            self._on_sort(self._sort_column, self._sort_reverse)

    def _sort_rows(self) -> None:
        if self._sort_column is None:
            return
        self._rows.sort(
            key=lambda row: self._natural_sort_key(
                row[1][self._sort_column] if self._sort_column < len(row[1]) else None
            ),
            reverse=self._sort_reverse,
        )

    def _update_headings(self) -> None:
        for index, (column_id, heading, _width, _anchor) in enumerate(self._columns):
            marker = ""
            if index == self._sort_column:
                marker = "  ▼" if self._sort_reverse else "  ▲"
            self.tree.heading(
                column_id,
                text=heading + marker,
                command=lambda position=index: self.sort_by(position),
            )

    def restore_sort(self, column_index: int | None, reverse: bool = False) -> None:
        if column_index is None or not 0 <= int(column_index) < len(self._columns):
            return
        self._sort_column = int(column_index)
        self._sort_reverse = bool(reverse)
        self._sort_rows()
        self._update_headings()
        self._render_rows()

    def sort_state(self) -> tuple[int | None, bool]:
        return self._sort_column, self._sort_reverse

    def _page_count(self) -> int:
        if self._page_size is None or not self._rows:
            return 1
        return max(1, (len(self._rows) + self._page_size - 1) // self._page_size)

    def _clamp_page(self) -> None:
        self._page_index = max(0, min(self._page_index, self._page_count() - 1))

    def change_page(self, delta: int) -> None:
        target = self._page_index + int(delta)
        if 0 <= target < self._page_count():
            self._page_index = target
            self._render_rows()

    def _visible_rows(self) -> list[tuple[str, tuple[Any, ...], bool]]:
        if self._page_size is None:
            return self._rows
        start = self._page_index * self._page_size
        return self._rows[start : start + self._page_size]

    def _update_pager(self) -> None:
        if self._page_size is None:
            return
        total = len(self._rows)
        start = self._page_index * self._page_size
        end = min(total, start + self._page_size)
        if total:
            label = f"{start + 1:,}–{end:,} sur {total:,}".replace(",", " ")
        else:
            label = "Aucun résultat"
        self.page_label.configure(text=label)
        self.previous_page_button.configure(state="normal" if self._page_index > 0 else "disabled")
        self.next_page_button.configure(
            state="normal" if self._page_index + 1 < self._page_count() else "disabled"
        )

    def _render_rows(self) -> None:
        self.clear()
        visible = self._visible_rows()
        first_index = self._page_index * (self._page_size or len(self._rows) or 1)
        for index, (iid, values, favourite) in enumerate(visible, start=first_index):
            tags = []
            if index % 2:
                tags.append("odd")
            if favourite:
                tags.append("favourite")
            self.tree.insert("", "end", iid=iid, values=values, tags=tuple(tags))
        self._update_pager()

    def select(self, iid: str) -> None:
        if not self.tree.exists(iid) and self._page_size is not None:
            for index, (row_id, _values, _favourite) in enumerate(self._rows):
                if row_id == iid:
                    self._page_index = index // self._page_size
                    self._render_rows()
                    break
        if self.tree.exists(iid):
            self.tree.selection_set(iid)
            self.tree.focus(iid)
            self.tree.see(iid)


def labelled_combo(
    master: Any,
    *,
    label: str,
    variable: tk.StringVar,
    values: list[str],
    command: Callable[[str], None] | None = None,
    width: int = 170,
) -> ctk.CTkFrame:
    frame = ctk.CTkFrame(master, fg_color="transparent")
    ctk.CTkLabel(
        frame,
        text=label.upper(),
        font=("Segoe UI Semibold", 10),
        text_color=COLORS["muted_2"],
        anchor="w",
    ).pack(fill="x", pady=(0, 4))
    combo = ctk.CTkComboBox(
        frame,
        variable=variable,
        values=values or ["Tous"],
        command=command,
        width=width,
        height=34,
        corner_radius=8,
        border_width=1,
        border_color=COLORS["border"],
        fg_color=COLORS["panel_alt"],
        button_color=COLORS["border"],
        button_hover_color=COLORS["panel_hover"],
        dropdown_fg_color=COLORS["panel_alt"],
        dropdown_hover_color=COLORS["accent_dark"],
        text_color=COLORS["text"],
        font=("Segoe UI", 12),
        state="readonly",
    )
    combo.pack(fill="x")
    return frame


class EmptyState(ctk.CTkFrame):
    def __init__(self, master: Any, title: str, message: str):
        super().__init__(master, fg_color="transparent")
        ctk.CTkLabel(
            self,
            text="◇",
            font=("Segoe UI", 40),
            text_color=COLORS["accent"],
        ).pack(pady=(30, 10))
        ctk.CTkLabel(
            self,
            text=title,
            font=("Segoe UI Semibold", 16),
            text_color=COLORS["text"],
        ).pack()
        ctk.CTkLabel(
            self,
            text=message,
            wraplength=320,
            justify="center",
            font=("Segoe UI", 12),
            text_color=COLORS["muted"],
        ).pack(pady=(7, 25))
