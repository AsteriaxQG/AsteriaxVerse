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
        bordercolor=COLORS["border"],
        lightcolor=COLORS["border"],
        darkcolor=COLORS["border"],
        borderwidth=0,
        rowheight=40,
        font=("Segoe UI", 12),
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
        padding=(8, 10),
        font=("Segoe UI Semibold", 11),
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
            font=("Segoe UI Semibold", 11),
            text_color=COLORS["muted"],
            anchor="w",
        ).grid(row=1, column=1, padx=(0, 12), sticky="ew")
        ctk.CTkLabel(
            self,
            text=caption,
            font=("Segoe UI", 9),
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
                font=("Segoe UI", 10),
                text_color=COLORS["muted"],
                anchor="w",
            ).grid(row=1, column=0, pady=(2, 0), sticky="ew")


class TreeTable(ctk.CTkFrame):
    """Dark ttk.Treeview wrapped in a rounded CustomTkinter panel."""

    def __init__(
        self,
        master: Any,
        columns: list[tuple[str, str, int, str]],
        *,
        on_select: Callable[[str], None] | None = None,
        on_double_click: Callable[[str], None] | None = None,
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
        ids = [column[0] for column in columns]
        self.tree = ttk.Treeview(
            self,
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
            self.tree.column(column_id, width=width, minwidth=45, anchor=anchor, stretch=column_id in {"name", "location"})
        scrollbar = ttk.Scrollbar(
            self,
            orient="vertical",
            command=self.tree.yview,
            style="Asteriax.Vertical.TScrollbar",
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.grid(row=0, column=0, padx=(8, 0), pady=8, sticky="nsew")
        scrollbar.grid(row=0, column=1, padx=(0, 7), pady=8, sticky="ns")
        horizontal = ttk.Scrollbar(
            self,
            orient="horizontal",
            command=self.tree.xview,
            style="Asteriax.Horizontal.TScrollbar",
        )
        self.tree.configure(xscrollcommand=horizontal.set)
        horizontal.grid(row=1, column=0, padx=8, pady=(0, 7), sticky="ew")
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

    def populate(self, rows: Iterable[tuple[str, tuple[Any, ...], bool]]) -> None:
        self._rows = list(rows)
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
        self._rows.sort(
            key=lambda row: self._natural_sort_key(
                row[1][column_index] if column_index < len(row[1]) else None
            ),
            reverse=self._sort_reverse,
        )
        for index, (column_id, heading, _width, _anchor) in enumerate(self._columns):
            marker = ""
            if index == self._sort_column:
                marker = "  ▼" if self._sort_reverse else "  ▲"
            self.tree.heading(
                column_id,
                text=heading + marker,
                command=lambda position=index: self.sort_by(position),
            )
        self._render_rows()
        if selected:
            self.select(selected)

    def _render_rows(self) -> None:
        self.clear()
        for index, (iid, values, favourite) in enumerate(self._rows):
            tags = []
            if index % 2:
                tags.append("odd")
            if favourite:
                tags.append("favourite")
            self.tree.insert("", "end", iid=iid, values=values, tags=tuple(tags))

    def select(self, iid: str) -> None:
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
        font=("Segoe UI Semibold", 8),
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
        font=("Segoe UI", 10),
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
            font=("Segoe UI", 10),
            text_color=COLORS["muted"],
        ).pack(pady=(7, 25))
