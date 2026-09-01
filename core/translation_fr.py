"""Safe installer for the community French localization of Star Citizen."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable, Iterable

from .constants import USER_AGENT
from .paths import user_data_dir


TRANSLATION_LANGUAGE = "french_(france)"
DEFAULT_TRANSLATION_SOURCE = "scefra"
TRANSLATION_PROJECT_URL = "https://github.com/SPEED0U/Scefra"
TRANSLATION_LIVE_URL = (
    "https://raw.githubusercontent.com/SPEED0U/Scefra/"
    "main/french_(france)/global.ini"
)
TRANSLATION_PTU_URL = (
    "https://raw.githubusercontent.com/Dymerz/StarCitizen-Localization/"
    "ptu/data/Localization/french_(france)/global.ini"
)
TRANSLATION_SOURCES: dict[str, dict[str, str]] = {
    "scefra": {
        "label": "Scefra — autre traduction (recommandée)",
        "short_label": "Scefra",
        "project_url": "https://github.com/SPEED0U/Scefra",
        "live_url": TRANSLATION_LIVE_URL,
        "ptu_url": "",
        "description": "Autre base française, corrigée par la communauté. Disponible pour LIVE.",
    },
    "classic": {
        "label": "Traduction classique — Circuspes",
        "short_label": "Circuspes classique",
        "project_url": "https://github.com/Dymerz/StarCitizen-Localization",
        "live_url": (
            "https://raw.githubusercontent.com/Dymerz/StarCitizen-Localization/"
            "main/data/Localization/french_(france)/global.ini"
        ),
        "ptu_url": TRANSLATION_PTU_URL,
        "description": "Ancienne traduction utilisée par Asteriax Verse. Compatible LIVE et PTU.",
    },
}
MAX_TRANSLATION_BYTES = 64 * 1024 * 1024
MIN_TRANSLATION_BYTES = 5 * 1024
ProgressCallback = Callable[[float, str], None]


def _translation_root(state_root: Path | None = None) -> Path:
    root = Path(state_root) if state_root is not None else user_data_dir() / "translations"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _channel_marker(path: Path) -> bool:
    return (path / "StarCitizen_Launcher.exe").is_file() or (path / "Data.p4k").is_file()


def _channel_candidates(path: Path) -> list[Path]:
    candidate = path.expanduser()
    if candidate.is_file():
        candidate = candidate.parent
    choices: list[Path] = []
    if _channel_marker(candidate):
        choices.append(candidate)
    roots = [candidate, candidate / "StarCitizen"]
    for root in roots:
        if not root.is_dir():
            continue
        for name in ("LIVE", "PTU", "EPTU", "HOTFIX", "TECH-PREVIEW"):
            channel = root / name
            if _channel_marker(channel):
                choices.append(channel)
    unique: dict[str, Path] = {}
    for choice in choices:
        unique.setdefault(str(choice.resolve()).casefold(), choice.resolve())
    return list(unique.values())


def validate_game_folder(value: str | os.PathLike[str]) -> Path:
    """Return an exact Star Citizen channel folder, preferring LIVE."""

    raw = str(value or "").strip().strip('"')
    if not raw:
        raise ValueError("Sélectionnez le dossier de Star Citizen.")
    candidates = _channel_candidates(Path(raw))
    if not candidates:
        raise ValueError(
            "Ce dossier ne contient pas StarCitizen_Launcher.exe ni Data.p4k. "
            "Sélectionnez le dossier LIVE, PTU ou le dossier StarCitizen."
        )
    candidates.sort(key=lambda path: (path.name.upper() != "LIVE", str(path).casefold()))
    return candidates[0]


def _launcher_log_candidates() -> list[Path]:
    appdata = os.environ.get("APPDATA")
    if not appdata:
        return []
    log_path = Path(appdata) / "rsilauncher" / "logs" / "log.log"
    if not log_path.is_file():
        return []
    try:
        content = log_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    patterns = (
        r"Launching Star Citizen\s+.*?\s+from\s+\(([^)]+)\)",
        r"Installing Star Citizen\s+.*?\s+at\s+([^\"\r\n]+?)(?:\s+\(|\"|$)",
        r'"libraryFolder"\s*:\s*"([^"]+)"',
    )
    found: list[Path] = []
    for pattern in patterns:
        for match in re.finditer(pattern, content, flags=re.IGNORECASE):
            value = match.group(1).replace("\\\\", "\\").strip()
            base = Path(value)
            found.extend((base, base / "StarCitizen"))
    return found


def find_game_installations(extra_candidates: Iterable[str | os.PathLike[str]] = ()) -> list[Path]:
    """Find valid LIVE/PTU installations without scanning whole disks."""

    candidates: list[Path] = [Path(value) for value in extra_candidates if str(value or "").strip()]
    candidates.extend(_launcher_log_candidates())
    candidates.extend(
        [
            Path("C:/Program Files/Roberts Space Industries/StarCitizen"),
            Path("C:/Roberts Space Industries/StarCitizen"),
            Path("C:/RSI/StarCitizen"),
        ]
    )
    discovered: dict[str, Path] = {}
    for candidate in candidates:
        for channel in _channel_candidates(candidate):
            discovered.setdefault(str(channel).casefold(), channel)
    result = list(discovered.values())
    result.sort(key=lambda path: (path.name.upper() != "LIVE", str(path).casefold()))
    return result


def translation_source_details(source_key: str = DEFAULT_TRANSLATION_SOURCE) -> dict[str, str]:
    key = str(source_key or DEFAULT_TRANSLATION_SOURCE).strip().casefold()
    source = TRANSLATION_SOURCES.get(key)
    if source is None:
        raise ValueError("Cette traduction française n’est pas reconnue.")
    return {"key": key, **source}


def translation_source_url(
    game_folder: Path, source_key: str = DEFAULT_TRANSLATION_SOURCE
) -> str:
    source = translation_source_details(source_key)
    key = "live_url" if game_folder.name.upper() == "LIVE" else "ptu_url"
    url = source.get(key, "")
    if not url:
        raise ValueError(
            f"La traduction {source['short_label']} n’est pas disponible pour le canal "
            f"{game_folder.name.upper()}. Choisissez la traduction classique pour ce canal."
        )
    return url


def _validate_source_url(value: str) -> str:
    url = str(value or "").strip()
    parsed = urllib.parse.urlparse(url)
    allowed_paths = (
        "/SPEED0U/Scefra/main/french_(france)/global.ini",
        "/Dymerz/StarCitizen-Localization/main/data/Localization/french_(france)/global.ini",
        "/Dymerz/StarCitizen-Localization/ptu/data/Localization/french_(france)/global.ini",
    )
    if (
        parsed.scheme != "https"
        or parsed.hostname != "raw.githubusercontent.com"
        or parsed.username
        or parsed.password
        or parsed.path not in allowed_paths
    ):
        raise ValueError("La source de traduction française n’est pas autorisée.")
    return url


def _state_key(game_folder: Path) -> str:
    normalized = str(game_folder.resolve()).replace("\\", "/").casefold()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:20]


def _state_file(root: Path) -> Path:
    return root / "state.json"


def _load_state(root: Path) -> dict[str, Any]:
    path = _state_file(root)
    if not path.is_file():
        return {"targets": {}}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict) and isinstance(payload.get("targets"), dict):
            return payload
    except (OSError, ValueError, json.JSONDecodeError):
        pass
    return {"targets": {}}


def _save_state(root: Path, state: dict[str, Any]) -> None:
    path = _state_file(root)
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, path)


def _read_cfg(path: Path) -> str:
    if not path.is_file():
        return ""
    payload = path.read_bytes()
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return payload.decode(encoding)
        except UnicodeDecodeError:
            continue
    return payload.decode("utf-8", errors="replace")


def _french_cfg(content: str) -> str:
    kept = [
        line
        for line in content.splitlines()
        if not re.match(r"^\s*g_language(?:Audio)?\s*=", line, flags=re.IGNORECASE)
    ]
    while kept and not kept[-1].strip():
        kept.pop()
    kept.extend((f"g_language = {TRANSLATION_LANGUAGE}", "g_languageAudio = english"))
    return "\n".join(kept) + "\n"


def _english_cfg(content: str) -> str:
    kept = [
        line
        for line in content.splitlines()
        if not re.match(r"^\s*g_language(?:Audio)?\s*=", line, flags=re.IGNORECASE)
    ]
    while kept and not kept[-1].strip():
        kept.pop()
    kept.extend(("g_language = english", "g_languageAudio = english"))
    return "\n".join(kept) + "\n"


def _without_language_cfg(content: str) -> str:
    kept = [
        line
        for line in content.splitlines()
        if not re.match(r"^\s*g_language(?:Audio)?\s*=", line, flags=re.IGNORECASE)
    ]
    while kept and not kept[-1].strip():
        kept.pop()
    return ("\n".join(kept) + "\n") if kept else ""


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".asteriax.tmp")
    try:
        temporary.write_bytes(payload)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _validate_translation_payload(payload: bytes) -> None:
    if len(payload) < MIN_TRANSLATION_BYTES:
        raise ValueError("Le fichier français téléchargé est anormalement petit.")
    if len(payload) > MAX_TRANSLATION_BYTES:
        raise ValueError("Le fichier français téléchargé dépasse la taille autorisée.")
    sample = payload[:4096].lstrip(b"\xef\xbb\xbf\x00\t\r\n ").lower()
    if sample.startswith((b"<!doctype", b"<html", b"{\"message\"")):
        raise ValueError("La source a renvoyé une page web au lieu du fichier de traduction.")
    if payload.count(b"=") < 100 or payload.count(b"\n") < 100:
        raise ValueError("Le fichier reçu ne ressemble pas à une localisation Star Citizen complète.")


def _download_translation(
    url: str,
    progress: ProgressCallback | None,
    *,
    timeout: int,
) -> bytes:
    source = _validate_source_url(url)
    request = urllib.request.Request(
        source,
        headers={"User-Agent": USER_AGENT, "Accept": "text/plain, application/octet-stream"},
    )
    chunks: list[bytes] = []
    downloaded = 0
    with urllib.request.urlopen(request, timeout=timeout) as response:
        _validate_source_url(response.geturl())
        announced = int(response.headers.get("Content-Length") or 0)
        if announced > MAX_TRANSLATION_BYTES:
            raise ValueError("Le fichier français annoncé dépasse la taille autorisée.")
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            downloaded += len(chunk)
            if downloaded > MAX_TRANSLATION_BYTES:
                raise ValueError("Le fichier français dépasse la taille autorisée.")
            chunks.append(chunk)
            if progress:
                fraction = downloaded / announced if announced else min(0.9, downloaded / (12 * 1024 * 1024))
                progress(min(0.9, max(0.03, fraction * 0.9)), f"Téléchargement du français… {downloaded // 1024:,} Ko")
    payload = b"".join(chunks)
    _validate_translation_payload(payload)
    return payload


def translation_status(
    game_folder: str | os.PathLike[str], *, state_root: Path | None = None
) -> dict[str, Any]:
    channel = validate_game_folder(game_folder)
    global_ini = channel / "data" / "Localization" / TRANSLATION_LANGUAGE / "global.ini"
    cfg = _read_cfg(channel / "user.cfg")
    configured = bool(
        re.search(
            rf"^\s*g_language\s*=\s*{re.escape(TRANSLATION_LANGUAGE)}\s*$",
            cfg,
            flags=re.IGNORECASE | re.MULTILINE,
        )
    )
    root = _translation_root(state_root)
    entry = _load_state(root).get("targets", {}).get(_state_key(channel), {})
    source_key = str(entry.get("source_key") or "")
    source_label = "Installation manuelle"
    if source_key in TRANSLATION_SOURCES:
        source_label = TRANSLATION_SOURCES[source_key]["short_label"]
    return {
        "game_folder": str(channel),
        "channel": channel.name.upper(),
        "installed": global_ini.is_file() and configured,
        "file_present": global_ini.is_file(),
        "configured": configured,
        "managed": bool(entry),
        "installed_at": str(entry.get("installed_at") or ""),
        "sha256": str(entry.get("sha256") or ""),
        "source_key": source_key,
        "source_label": source_label,
        "source_url": str(entry.get("source_url") or ""),
    }


def install_french_translation(
    game_folder: str | os.PathLike[str],
    progress: ProgressCallback | None = None,
    *,
    state_root: Path | None = None,
    source_key: str = DEFAULT_TRANSLATION_SOURCE,
    source_url: str | None = None,
    timeout: int = 45,
) -> dict[str, Any]:
    """Install or update French after saving the pre-Asteriax state once."""

    channel = validate_game_folder(game_folder)
    root = _translation_root(state_root)
    source = translation_source_details(source_key)
    url = _validate_source_url(source_url or translation_source_url(channel, source["key"]))
    if progress:
        progress(0.01, f"Connexion à {source['short_label']}…")
    payload = _download_translation(url, progress, timeout=timeout)

    global_ini = channel / "data" / "Localization" / TRANSLATION_LANGUAGE / "global.ini"
    user_cfg = channel / "user.cfg"
    state = _load_state(root)
    targets = state.setdefault("targets", {})
    key = _state_key(channel)
    entry = targets.get(key)
    if not isinstance(entry, dict):
        backup = root / "backups" / key
        backup.mkdir(parents=True, exist_ok=True)
        entry = {
            "game_folder": str(channel),
            "backup_dir": str(backup),
            "original_global_ini": global_ini.is_file(),
            "original_user_cfg": user_cfg.is_file(),
        }
        if global_ini.is_file():
            shutil.copy2(global_ini, backup / "global.ini")
        if user_cfg.is_file():
            shutil.copy2(user_cfg, backup / "user.cfg")
        targets[key] = entry
        _save_state(root, state)

    if progress:
        progress(0.93, "Installation et configuration du jeu…")
    previous_global = global_ini.read_bytes() if global_ini.is_file() else None
    previous_cfg = user_cfg.read_bytes() if user_cfg.is_file() else None
    try:
        _atomic_write(global_ini, payload)
        _atomic_write(user_cfg, _french_cfg(_read_cfg(user_cfg)).encode("utf-8"))
    except Exception:
        # Keep an update failure from leaving the game half configured.
        if previous_global is None:
            global_ini.unlink(missing_ok=True)
        else:
            _atomic_write(global_ini, previous_global)
        if previous_cfg is None:
            user_cfg.unlink(missing_ok=True)
        else:
            _atomic_write(user_cfg, previous_cfg)
        raise
    entry.update(
        {
            "installed_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "source_url": url,
            "source_key": source["key"],
            "sha256": hashlib.sha256(payload).hexdigest(),
        }
    )
    _save_state(root, state)
    if progress:
        progress(1.0, "Traduction française installée.")
    return translation_status(channel, state_root=root)


def restore_english(
    game_folder: str | os.PathLike[str], *, state_root: Path | None = None
) -> dict[str, Any]:
    """Restore the exact pre-install files, or switch safely to English."""

    channel = validate_game_folder(game_folder)
    root = _translation_root(state_root)
    state = _load_state(root)
    targets = state.setdefault("targets", {})
    key = _state_key(channel)
    entry = targets.get(key)
    global_ini = channel / "data" / "Localization" / TRANSLATION_LANGUAGE / "global.ini"
    user_cfg = channel / "user.cfg"

    if isinstance(entry, dict):
        backup = Path(str(entry.get("backup_dir") or ""))
        if entry.get("original_global_ini") and (backup / "global.ini").is_file():
            _atomic_write(global_ini, (backup / "global.ini").read_bytes())
        else:
            global_ini.unlink(missing_ok=True)
        if entry.get("original_user_cfg") and (backup / "user.cfg").is_file():
            _atomic_write(user_cfg, (backup / "user.cfg").read_bytes())
        else:
            remaining_cfg = _without_language_cfg(_read_cfg(user_cfg))
            if remaining_cfg:
                _atomic_write(user_cfg, remaining_cfg.encode("utf-8"))
            else:
                user_cfg.unlink(missing_ok=True)
        targets.pop(key, None)
        _save_state(root, state)
    else:
        global_ini.unlink(missing_ok=True)
        _atomic_write(user_cfg, _english_cfg(_read_cfg(user_cfg)).encode("utf-8"))

    language_dir = global_ini.parent
    try:
        language_dir.rmdir()
    except OSError:
        pass
    return translation_status(channel, state_root=root)
