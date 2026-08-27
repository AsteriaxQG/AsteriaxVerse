"""Secure in-app update helpers for the portable Windows executable."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable

from .constants import APP_UPDATE_MANIFEST_URL, APP_VERSION, USER_AGENT
from .paths import user_data_dir


MAX_UPDATE_BYTES = 250 * 1024 * 1024
OFFICIAL_DOWNLOAD_HOSTS = {"github.com", "raw.githubusercontent.com"}
APPLY_UPDATE_FLAG = "--asteriax-apply-update"
UPDATE_RESULT_FILENAME = "update_result.json"
ProgressCallback = Callable[[float, str], None]


def version_key(value: str) -> tuple[int, ...]:
    """Turn common dotted versions into a tuple suitable for comparisons."""

    parts: list[int] = []
    for raw in str(value or "").strip().lstrip("vV").split("."):
        digits = "".join(character for character in raw if character.isdigit())
        parts.append(int(digits or 0))
    return tuple(parts or [0])


def can_self_update() -> bool:
    """Return whether this process is the packaged Windows executable."""

    return os.name == "nt" and bool(getattr(sys, "frozen", False)) and str(sys.executable).lower().endswith(".exe")


def _validate_https_url(value: str, *, official_download: bool = False) -> str:
    url = str(value or "").strip()
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Le lien de mise à jour doit utiliser une adresse HTTPS valide.")
    if official_download and parsed.hostname.casefold() not in OFFICIAL_DOWNLOAD_HOSTS:
        raise ValueError("Le fichier de mise à jour ne provient pas du dépôt officiel Asteriax Verse.")
    if official_download and not parsed.path.casefold().startswith("/asteriaxqg/asteriaxverse/"):
        raise ValueError("Le chemin du fichier de mise à jour officiel est invalide.")
    return url


def _normalise_sha256(value: str) -> str:
    checksum = str(value or "").strip().casefold()
    if not re.fullmatch(r"[0-9a-f]{64}", checksum):
        raise ValueError("La publication ne contient pas d’empreinte SHA-256 valide.")
    return checksum


def _normalise_size(value: Any) -> int:
    try:
        size = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("La publication ne contient pas de taille de fichier valide.") from exc
    if size <= 0 or size > MAX_UPDATE_BYTES:
        raise ValueError("La taille annoncée pour la mise à jour est invalide.")
    return size


def check_app_update(
    manifest_url: str = APP_UPDATE_MANIFEST_URL,
    *,
    timeout: int = 10,
) -> dict[str, Any]:
    """Read and validate the official release manifest."""

    url = str(manifest_url or "").strip()
    if not url:
        return {
            "configured": False,
            "available": False,
            "current_version": APP_VERSION,
            "latest_version": APP_VERSION,
            "download_url": "",
            "release_notes": "",
            "sha256": "",
            "size": 0,
        }
    _validate_https_url(url)
    parsed = urllib.parse.urlsplit(url)
    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    query.append(("asteriax_cache", str(time.time_ns())))
    request_url = urllib.parse.urlunsplit(
        (parsed.scheme, parsed.netloc, parsed.path, urllib.parse.urlencode(query), parsed.fragment)
    )
    request = urllib.request.Request(
        request_url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.load(response)
    if not isinstance(payload, dict):
        raise ValueError("Le manifeste de mise à jour est invalide.")

    latest = str(payload.get("version") or "").strip()
    if not latest:
        raise ValueError("Le manifeste ne contient aucune version.")
    available = version_key(latest) > version_key(APP_VERSION)
    download_url = str(payload.get("download_url") or payload.get("release_url") or "").strip()
    checksum = str(payload.get("sha256") or "").strip().casefold()
    size_value = payload.get("size") or 0

    if available:
        download_url = _validate_https_url(download_url, official_download=True)
        checksum = _normalise_sha256(checksum)
        size_value = _normalise_size(size_value)

    return {
        "configured": True,
        "available": available,
        "current_version": APP_VERSION,
        "latest_version": latest,
        "download_url": download_url,
        "release_notes": str(payload.get("release_notes") or ""),
        "sha256": checksum,
        "size": int(size_value or 0),
    }


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_app_update(
    update_info: dict[str, Any],
    progress: ProgressCallback | None = None,
    *,
    timeout: int = 45,
) -> Path:
    """Download a verified Windows executable without opening a browser."""

    if not can_self_update():
        raise RuntimeError("La mise à jour intégrée est disponible uniquement depuis AsteriaxVerse.exe.")

    version = str(update_info.get("latest_version") or "").strip()
    safe_version = re.sub(r"[^0-9A-Za-z._-]", "_", version) or "update"
    url = _validate_https_url(str(update_info.get("download_url") or ""), official_download=True)
    expected_hash = _normalise_sha256(str(update_info.get("sha256") or ""))
    expected_size = _normalise_size(update_info.get("size"))

    update_dir = user_data_dir() / "updates"
    update_dir.mkdir(parents=True, exist_ok=True)
    final_path = update_dir / f"AsteriaxVerse-{safe_version}.exe"
    partial_path = final_path.with_suffix(".exe.part")

    if final_path.exists():
        if final_path.stat().st_size == expected_size and hmac.compare_digest(_file_sha256(final_path), expected_hash):
            if progress:
                progress(1.0, "Mise à jour déjà téléchargée et vérifiée.")
            return final_path
        final_path.unlink(missing_ok=True)

    partial_path.unlink(missing_ok=True)
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/octet-stream"},
    )
    digest = hashlib.sha256()
    downloaded = 0
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response, partial_path.open("wb") as target:
            _validate_https_url(response.geturl(), official_download=True)
            announced = int(response.headers.get("Content-Length") or 0)
            if announced and announced > MAX_UPDATE_BYTES:
                raise ValueError("Le fichier proposé dépasse la taille maximale autorisée.")
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                downloaded += len(chunk)
                if downloaded > MAX_UPDATE_BYTES or downloaded > expected_size:
                    raise ValueError("Le fichier téléchargé dépasse la taille annoncée.")
                target.write(chunk)
                digest.update(chunk)
                if progress:
                    progress(min(0.99, downloaded / expected_size), f"Téléchargement… {downloaded * 100 // expected_size} %")

        if downloaded != expected_size:
            raise ValueError("La taille du fichier téléchargé ne correspond pas au manifeste.")
        if not hmac.compare_digest(digest.hexdigest(), expected_hash):
            raise ValueError("L’empreinte SHA-256 du fichier téléchargé est incorrecte.")
        with partial_path.open("rb") as stream:
            if stream.read(2) != b"MZ":
                raise ValueError("Le fichier reçu n’est pas un exécutable Windows valide.")
        os.replace(partial_path, final_path)
    except Exception:
        partial_path.unlink(missing_ok=True)
        raise

    if progress:
        progress(1.0, "Téléchargement terminé et vérifié.")
    return final_path


def _append_update_log(log_path: Path, message: str) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with log_path.open("a", encoding="utf-8") as stream:
        stream.write(f"[{timestamp}] {message}\n")


def _write_update_result(log_path: Path, checksum: str) -> Path:
    result_path = log_path.parent / UPDATE_RESULT_FILENAME
    temporary = result_path.with_suffix(".json.tmp")
    payload = {
        "version": APP_VERSION,
        "installed_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        "sha256": checksum,
    }
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, result_path)
    return result_path


def consume_update_result(result_path: Path | None = None) -> dict[str, str] | None:
    """Return and remove the success marker created by the integrated updater."""

    path = Path(result_path) if result_path is not None else user_data_dir() / "updates" / UPDATE_RESULT_FILENAME
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or str(payload.get("version") or "") != APP_VERSION:
            return None
        return {
            "version": APP_VERSION,
            "installed_at": str(payload.get("installed_at") or ""),
            "sha256": str(payload.get("sha256") or ""),
        }
    except (OSError, ValueError, json.JSONDecodeError):
        return None
    finally:
        path.unlink(missing_ok=True)


def _process_exists(process_id: int) -> bool:
    if process_id <= 0:
        return False
    try:
        if os.name == "nt":
            import ctypes

            handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, process_id)
            if not handle:
                return False
            ctypes.windll.kernel32.CloseHandle(handle)
            return True
        os.kill(process_id, 0)
        return True
    except (OSError, ValueError):
        return False


def apply_downloaded_update(
    source: Path,
    target: Path,
    checksum: str,
    old_process_id: int,
    log_path: Path,
    *,
    wait_timeout: float = 120.0,
) -> Path:
    """Replace the old executable from the newly downloaded executable itself."""

    source = Path(source).resolve()
    target = Path(target).resolve()
    expected_hash = _normalise_sha256(checksum)
    stage = target.with_name(target.name + ".new")
    backup = target.with_name(target.name + ".old")
    _append_update_log(log_path, f"Moteur intégré démarré depuis {source}")

    if not source.is_file() or source.suffix.casefold() != ".exe":
        raise FileNotFoundError("Le nouvel exécutable est introuvable.")
    if not hmac.compare_digest(_file_sha256(source), expected_hash):
        raise ValueError("Le nouvel exécutable ne correspond plus au SHA-256 publié.")

    deadline = time.monotonic() + max(1.0, float(wait_timeout))
    while _process_exists(int(old_process_id)):
        if time.monotonic() >= deadline:
            raise TimeoutError("L’ancienne version ne s’est pas fermée dans le délai prévu.")
        time.sleep(0.25)

    last_error: OSError | None = None
    for attempt in range(1, 31):
        try:
            stage.unlink(missing_ok=True)
            shutil.copy2(source, stage)
            if not hmac.compare_digest(_file_sha256(stage), expected_hash):
                raise OSError("La copie temporaire est corrompue.")
            if target.exists():
                shutil.copy2(target, backup)
            os.replace(stage, target)
            last_error = None
            break
        except OSError as exc:
            last_error = exc
            _append_update_log(log_path, f"Tentative {attempt}/30 : {exc}")
            time.sleep(0.5)
    if last_error is not None:
        raise last_error
    if not hmac.compare_digest(_file_sha256(target), expected_hash):
        raise ValueError("Le fichier installé ne correspond pas au SHA-256 publié.")

    creation_flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(
        subprocess, "CREATE_NEW_PROCESS_GROUP", 0
    )
    result_path = _write_update_result(log_path, expected_hash)
    try:
        process = subprocess.Popen(
            [str(target)],
            cwd=str(target.parent),
            close_fds=True,
            creationflags=creation_flags,
        )
    except OSError:
        result_path.unlink(missing_ok=True)
        raise
    _append_update_log(log_path, f"Version installée et relancée (PID {process.pid}).")
    backup.unlink(missing_ok=True)
    return target


def run_update_bootstrap(arguments: list[str] | None = None) -> int | None:
    """Handle the hidden updater mode before importing the graphical interface."""

    args = list(sys.argv[1:] if arguments is None else arguments)
    if not args or args[0] != APPLY_UPDATE_FLAG:
        return None
    if len(args) != 5:
        return 2

    target = Path(args[1])
    checksum = args[2]
    try:
        old_process_id = int(args[3])
    except ValueError:
        return 2
    log_path = Path(args[4])
    try:
        apply_downloaded_update(
            Path(sys.executable),
            target,
            checksum,
            old_process_id,
            log_path,
        )
        return 0
    except Exception as exc:
        _append_update_log(log_path, f"ÉCHEC : {type(exc).__name__}: {exc}")
        backup = target.with_name(target.name + ".old")
        stage = target.with_name(target.name + ".new")
        result_path = log_path.parent / UPDATE_RESULT_FILENAME
        try:
            stage.unlink(missing_ok=True)
            result_path.unlink(missing_ok=True)
            if backup.exists():
                os.replace(backup, target)
                _append_update_log(log_path, "Ancienne version restaurée.")
            if target.exists():
                subprocess.Popen([str(target)], cwd=str(target.parent), close_fds=True)
        except OSError as recovery_error:
            _append_update_log(log_path, f"Restauration impossible : {recovery_error}")
        return 1


def launch_app_update(package_path: Path, update_info: dict[str, Any]) -> Path:
    """Start the downloaded EXE in integrated updater mode."""

    if not can_self_update():
        raise RuntimeError("La mise à jour intégrée est disponible uniquement depuis AsteriaxVerse.exe.")
    source = Path(package_path).resolve()
    target = Path(sys.executable).resolve()
    if not source.is_file() or source.suffix.casefold() != ".exe":
        raise FileNotFoundError("Le fichier de mise à jour vérifié est introuvable.")
    if not os.access(target.parent, os.W_OK):
        raise PermissionError(
            "Le dossier contenant AsteriaxVerse.exe n’est pas modifiable. "
            "Placez le logiciel dans un dossier personnel avant de le mettre à jour."
        )
    checksum = _normalise_sha256(str(update_info.get("sha256") or ""))
    if not hmac.compare_digest(_file_sha256(source), checksum):
        raise ValueError("Le fichier de mise à jour a changé avant son installation.")

    update_dir = user_data_dir() / "updates"
    update_dir.mkdir(parents=True, exist_ok=True)
    installer_log = update_dir / "update_error.log"
    installer_log.unlink(missing_ok=True)
    creation_flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(
        subprocess, "CREATE_NEW_PROCESS_GROUP", 0
    )
    process = subprocess.Popen(
        [
            str(source),
            APPLY_UPDATE_FLAG,
            str(target),
            checksum,
            str(os.getpid()),
            str(installer_log),
        ],
        cwd=str(update_dir),
        close_fds=True,
        creationflags=creation_flags,
    )
    _append_update_log(installer_log, f"Moteur intégré lancé (PID {process.pid}).")
    return installer_log
