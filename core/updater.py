"""Small, conservative update-manifest client for future signed releases."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any

from .constants import APP_UPDATE_MANIFEST_URL, APP_VERSION, USER_AGENT


def version_key(value: str) -> tuple[int, ...]:
    """Turn common dotted versions into a tuple suitable for comparisons."""

    parts: list[int] = []
    for raw in str(value or "").strip().lstrip("vV").split("."):
        digits = "".join(character for character in raw if character.isdigit())
        parts.append(int(digits or 0))
    return tuple(parts or [0])


def check_app_update(
    manifest_url: str = APP_UPDATE_MANIFEST_URL,
    *,
    timeout: int = 10,
) -> dict[str, Any]:
    """Read a release manifest without downloading or executing any binary."""

    url = str(manifest_url or "").strip()
    if not url:
        return {
            "configured": False,
            "available": False,
            "current_version": APP_VERSION,
            "latest_version": APP_VERSION,
            "download_url": "",
            "release_notes": "",
        }
    if urllib.parse.urlparse(url).scheme != "https":
        raise ValueError("Le manifeste de mise à jour doit utiliser HTTPS.")
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.load(response)
    if not isinstance(payload, dict):
        raise ValueError("Le manifeste de mise à jour est invalide.")
    latest = str(payload.get("version") or "").strip()
    download_url = str(payload.get("download_url") or payload.get("release_url") or "").strip()
    if not latest:
        raise ValueError("Le manifeste ne contient aucune version.")
    if download_url and urllib.parse.urlparse(download_url).scheme != "https":
        raise ValueError("Le lien de téléchargement doit utiliser HTTPS.")
    return {
        "configured": True,
        "available": version_key(latest) > version_key(APP_VERSION),
        "current_version": APP_VERSION,
        "latest_version": latest,
        "download_url": download_url,
        "release_notes": str(payload.get("release_notes") or ""),
    }

