"""Filesystem paths that work both from source and from a PyInstaller build."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


def resource_root() -> Path:
    """Directory containing packaged read-only resources."""

    frozen_root = getattr(sys, "_MEIPASS", None)
    if frozen_root:
        return Path(frozen_root)
    return Path(__file__).resolve().parents[1]


def resource_path(*parts: str) -> Path:
    return resource_root().joinpath(*parts)


def user_data_dir() -> Path:
    """Return a per-user writable application directory."""

    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or Path.home())
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME") or (Path.home() / ".local" / "share"))
    target = base / "AsteriaxVerse"
    target.mkdir(parents=True, exist_ok=True)
    return target


def data_database_path() -> Path:
    """Copy the bundled snapshot on first launch and return its writable path."""

    target = user_data_dir() / "asteriax_sc.db"
    bundled = resource_path("data", "asteriax_sc.db")
    if not target.exists():
        if not bundled.exists():
            raise FileNotFoundError(
                "La base de données embarquée est introuvable. "
                "Réinstallez Asteriax Verse."
            )
        shutil.copy2(bundled, target)
    return target


def user_database_path() -> Path:
    return user_data_dir() / "asteriax_user.db"


def log_path() -> Path:
    return user_data_dir() / "asteriax_verse.log"

