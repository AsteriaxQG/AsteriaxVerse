"""Download UEX data and build the local read-optimised SQLite snapshot.

Only public, unauthenticated read endpoints are used.  A fresh database is
built next to the active one and swapped in atomically after validation, so a
network interruption can never destroy the user's working offline cache.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable

from .constants import (
    APP_AUTHOR,
    APP_VERSION,
    PATCH_410_RELEASE_TIMESTAMP,
    PATCH_410_VEHICLE_OFFERS,
    UEX_API_BASE,
    USER_AGENT,
    VERIFIED_LIVE_VERSION,
)
from .manufacturers import vehicle_manufacturer_label

ProgressCallback = Callable[[float, str], None]


class SyncError(RuntimeError):
    """Raised when a snapshot cannot be downloaded or validated."""


def _notify(callback: ProgressCallback | None, fraction: float, message: str) -> None:
    if callback:
        callback(max(0.0, min(1.0, fraction)), message)


def fetch_json(endpoint: str, *, attempts: int = 4, timeout: int = 90) -> Any:
    """Fetch one public UEX endpoint with bounded retries."""

    url = urllib.parse.urljoin(UEX_API_BASE, endpoint)
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
            "Cache-Control": "no-cache",
        },
    )
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                payload = json.load(response)
            if not isinstance(payload, dict):
                raise SyncError(f"Réponse inattendue pour {endpoint}")
            if payload.get("status") != "ok":
                detail = payload.get("message") or payload.get("status") or "erreur inconnue"
                raise SyncError(f"UEX a refusé {endpoint}: {detail}")
            return payload.get("data")
        except (OSError, ValueError, urllib.error.HTTPError, SyncError) as exc:
            last_error = exc
            if attempt + 1 < attempts:
                time.sleep(1.25 * (2**attempt))
    raise SyncError(f"Impossible de télécharger {endpoint}: {last_error}")


def _create_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        PRAGMA journal_mode = OFF;
        PRAGMA synchronous = OFF;
        PRAGMA temp_store = MEMORY;
        PRAGMA foreign_keys = OFF;

        CREATE TABLE meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE categories (
            id INTEGER PRIMARY KEY,
            section TEXT NOT NULL,
            name TEXT NOT NULL,
            is_game_related INTEGER NOT NULL DEFAULT 0,
            is_mining INTEGER NOT NULL DEFAULT 0,
            date_modified INTEGER
        );

        CREATE TABLE items (
            id INTEGER PRIMARY KEY,
            parent_id INTEGER,
            category_id INTEGER,
            company_id INTEGER,
            vehicle_id INTEGER,
            name TEXT NOT NULL,
            section TEXT,
            category TEXT,
            manufacturer TEXT,
            vehicle_name TEXT,
            slug TEXT,
            size TEXT,
            uuid TEXT,
            color TEXT,
            color2 TEXT,
            url_store TEXT,
            wiki TEXT,
            quality INTEGER,
            is_exclusive_pledge INTEGER NOT NULL DEFAULT 0,
            is_exclusive_subscriber INTEGER NOT NULL DEFAULT 0,
            is_exclusive_concierge INTEGER NOT NULL DEFAULT 0,
            is_commodity INTEGER NOT NULL DEFAULT 0,
            is_harvestable INTEGER NOT NULL DEFAULT 0,
            notification_json TEXT,
            game_version TEXT,
            date_added INTEGER,
            date_modified INTEGER
        );

        CREATE TABLE terminals (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            fullname TEXT,
            displayname TEXT,
            code TEXT,
            type TEXT,
            star_system TEXT,
            planet TEXT,
            orbit_name TEXT,
            moon TEXT,
            space_station TEXT,
            outpost TEXT,
            city TEXT,
            poi TEXT,
            company TEXT,
            is_available INTEGER NOT NULL DEFAULT 0,
            is_available_live INTEGER NOT NULL DEFAULT 0,
            is_shop_fps INTEGER NOT NULL DEFAULT 0,
            is_shop_vehicle INTEGER NOT NULL DEFAULT 0,
            game_version TEXT,
            date_modified INTEGER
        );

        CREATE TABLE item_offers (
            id INTEGER PRIMARY KEY,
            item_id INTEGER NOT NULL,
            category_id INTEGER,
            terminal_id INTEGER NOT NULL,
            price_buy REAL NOT NULL DEFAULT 0,
            price_sell REAL NOT NULL DEFAULT 0,
            date_added INTEGER,
            date_modified INTEGER
        );

        CREATE TABLE vehicles (
            id INTEGER PRIMARY KEY,
            company_id INTEGER,
            parent_id INTEGER,
            name TEXT NOT NULL,
            name_full TEXT,
            manufacturer TEXT,
            slug TEXT,
            uuid TEXT,
            scu REAL,
            crew TEXT,
            mass REAL,
            width REAL,
            height REAL,
            length REAL,
            quantum_fuel REAL,
            hydrogen_fuel REAL,
            pad_type TEXT,
            is_concept INTEGER NOT NULL DEFAULT 0,
            is_ground_vehicle INTEGER NOT NULL DEFAULT 0,
            is_spaceship INTEGER NOT NULL DEFAULT 0,
            is_cargo INTEGER NOT NULL DEFAULT 0,
            is_combat INTEGER NOT NULL DEFAULT 0,
            is_exploration INTEGER NOT NULL DEFAULT 0,
            is_industrial INTEGER NOT NULL DEFAULT 0,
            is_mining INTEGER NOT NULL DEFAULT 0,
            is_salvage INTEGER NOT NULL DEFAULT 0,
            is_medical INTEGER NOT NULL DEFAULT 0,
            is_racing INTEGER NOT NULL DEFAULT 0,
            is_refuel INTEGER NOT NULL DEFAULT 0,
            is_repair INTEGER NOT NULL DEFAULT 0,
            roles TEXT,
            url_photo TEXT,
            wiki_url TEXT,
            game_version TEXT,
            date_added INTEGER,
            date_modified INTEGER
        );

        CREATE TABLE vehicle_offers (
            id INTEGER PRIMARY KEY,
            vehicle_id INTEGER NOT NULL,
            terminal_id INTEGER NOT NULL,
            price_buy REAL NOT NULL,
            date_added INTEGER,
            date_modified INTEGER
        );

        CREATE TABLE game_versions (
            id INTEGER PRIMARY KEY,
            game_version TEXT NOT NULL,
            release_timestamp INTEGER
        );

        CREATE INDEX idx_items_name ON items(name COLLATE NOCASE);
        CREATE INDEX idx_items_scope ON items(section, category);
        CREATE INDEX idx_items_manufacturer ON items(manufacturer);
        CREATE INDEX idx_item_offers_item ON item_offers(item_id, price_buy);
        CREATE INDEX idx_item_offers_terminal ON item_offers(terminal_id);
        CREATE INDEX idx_vehicles_name ON vehicles(name COLLATE NOCASE);
        CREATE INDEX idx_vehicles_company ON vehicles(manufacturer);
        CREATE INDEX idx_vehicle_offers_vehicle ON vehicle_offers(vehicle_id, price_buy);
        CREATE INDEX idx_vehicle_offers_terminal ON vehicle_offers(terminal_id);
        CREATE INDEX idx_terminals_location ON terminals(star_system, planet, city);

        PRAGMA user_version = 1;
        """
    )


def _as_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _as_float(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _role_names(vehicle: dict[str, Any]) -> str:
    roles = []
    mapping = [
        ("is_cargo", "Cargo"),
        ("is_military", "Combat"),
        ("is_bomber", "Bombardier"),
        ("is_exploration", "Exploration"),
        ("is_industrial", "Industriel"),
        ("is_mining", "Minage"),
        ("is_salvage", "Récupération"),
        ("is_medical", "Médical"),
        ("is_racing", "Course"),
        ("is_refuel", "Ravitaillement"),
        ("is_repair", "Réparation"),
        ("is_passenger", "Transport"),
        ("is_science", "Science"),
        ("is_datarunner", "Données"),
    ]
    for key, label in mapping:
        if _as_int(vehicle.get(key)):
            roles.append(label)
    return ", ".join(dict.fromkeys(roles)) or "Polyvalent"


def _insert_many(
    connection: sqlite3.Connection,
    sql: str,
    rows: Iterable[tuple[Any, ...]],
) -> None:
    connection.executemany(sql, rows)


def _add_patch_vehicle_offers(
    parameters: dict[str, Any],
    vehicles: list[dict[str, Any]],
    terminals: list[dict[str, Any]],
    offers: list[dict[str, Any]],
    warnings: list[str],
) -> tuple[list[dict[str, Any]], list[str]]:
    """Fill the short UEX ship-shop lag for the verified Alpha 4.10 catalogue.

    CIG's patch note is authoritative for availability, while the prices were
    checked in game. A provider offer always wins: an exact vehicle/terminal
    pair is never overwritten or duplicated.
    """

    global_parameters = parameters.get("global", {}) if isinstance(parameters, dict) else {}
    game_version = str(global_parameters.get("game_version") or "")
    if not game_version.startswith("4.10"):
        return list(offers), []

    vehicle_ids = {
        str(row.get("name") or "").strip().casefold(): _as_int(row.get("id"))
        for row in vehicles
        if _as_int(row.get("id"))
    }
    terminal_ids = {
        str(row.get("name") or "").strip().casefold(): _as_int(row.get("id"))
        for row in terminals
        if _as_int(row.get("id")) and _as_int(row.get("is_available_live"))
    }
    merged = [dict(row) for row in offers]
    existing = {
        (_as_int(row.get("id_vehicle")), _as_int(row.get("id_terminal")))
        for row in merged
    }
    applied: list[str] = []

    for index, supplement in enumerate(PATCH_410_VEHICLE_OFFERS, start=1):
        vehicle_name = str(supplement["vehicle"])
        terminal_name = str(supplement["terminal"])
        vehicle_id = vehicle_ids.get(vehicle_name.casefold(), 0)
        terminal_id = terminal_ids.get(terminal_name.casefold(), 0)
        if not vehicle_id or not terminal_id:
            missing = vehicle_name if not vehicle_id else terminal_name
            warnings.append(f"Correctif 4.10 introuvable dans UEX : {missing}")
            continue
        pair = (vehicle_id, terminal_id)
        if pair in existing:
            continue
        merged.append(
            {
                "id": -410_000 - index,
                "id_vehicle": vehicle_id,
                "id_terminal": terminal_id,
                "price_buy": float(supplement["price"]),
                "date_added": PATCH_410_RELEASE_TIMESTAMP,
                "date_modified": PATCH_410_RELEASE_TIMESTAMP,
            }
        )
        existing.add(pair)
        applied.append(f"{vehicle_name} · {terminal_name}")

    return merged, applied


def _build_database(
    target: Path,
    datasets: dict[str, Any],
    items: list[dict[str, Any]],
    warnings: list[str],
) -> dict[str, int]:
    categories: list[dict[str, Any]] = datasets["categories"]
    terminals: list[dict[str, Any]] = datasets["terminals"]
    vehicles: list[dict[str, Any]] = datasets["vehicles"]
    item_offers: list[dict[str, Any]] = datasets["item_offers"]
    vehicle_offers: list[dict[str, Any]] = datasets["vehicle_offers"]
    versions: list[dict[str, Any]] = datasets["versions"]
    parameters: dict[str, Any] = datasets["parameters"]

    vehicle_offers, supplemented_offers = _add_patch_vehicle_offers(
        parameters,
        vehicles,
        terminals,
        vehicle_offers,
        warnings,
    )

    items_by_id = {_as_int(row.get("id")): row for row in items if _as_int(row.get("id"))}
    terminals_by_id = {
        _as_int(row.get("id")): row for row in terminals if _as_int(row.get("id"))
    }
    vehicles_by_id = {
        _as_int(row.get("id")): row for row in vehicles if _as_int(row.get("id"))
    }

    unresolved_items = {
        _as_int(row.get("id_item"))
        for row in item_offers
        if _as_int(row.get("id_item")) not in items_by_id
    }
    unresolved_item_terminals = {
        _as_int(row.get("id_terminal"))
        for row in item_offers
        if _as_int(row.get("id_terminal")) not in terminals_by_id
    }
    unresolved_vehicles = {
        _as_int(row.get("id_vehicle"))
        for row in vehicle_offers
        if _as_int(row.get("id_vehicle")) not in vehicles_by_id
    }
    unresolved_vehicle_terminals = {
        _as_int(row.get("id_terminal"))
        for row in vehicle_offers
        if _as_int(row.get("id_terminal")) not in terminals_by_id
    }
    if unresolved_items:
        warnings.append(f"{len(unresolved_items)} objets tarifés sans fiche UEX")
    if unresolved_item_terminals:
        warnings.append(f"{len(unresolved_item_terminals)} boutiques objet introuvables")
    if unresolved_vehicles:
        warnings.append(f"{len(unresolved_vehicles)} véhicules tarifés sans fiche UEX")
    if unresolved_vehicle_terminals:
        warnings.append(f"{len(unresolved_vehicle_terminals)} concessions introuvables")

    valid_item_offers = [
        row
        for row in item_offers
        if _as_int(row.get("id_item")) in items_by_id
        and _as_int(row.get("id_terminal")) in terminals_by_id
        and _as_int(terminals_by_id[_as_int(row.get("id_terminal"))].get("is_available_live"))
        and (_as_float(row.get("price_buy")) > 0 or _as_float(row.get("price_sell")) > 0)
    ]
    valid_vehicle_offers = [
        row
        for row in vehicle_offers
        if _as_int(row.get("id_vehicle")) in vehicles_by_id
        and _as_int(row.get("id_terminal")) in terminals_by_id
        and _as_int(terminals_by_id[_as_int(row.get("id_terminal"))].get("is_available_live"))
        and _as_float(row.get("price_buy")) > 0
    ]
    if not items_by_id or not valid_item_offers or not valid_vehicle_offers:
        raise SyncError("Le jeu de données reçu est incomplet; l'ancienne base a été conservée.")

    if target.exists():
        target.unlink()
    connection = sqlite3.connect(target)
    try:
        _create_schema(connection)

        _insert_many(
            connection,
            "INSERT INTO categories VALUES (?, ?, ?, ?, ?, ?)",
            (
                (
                    _as_int(c.get("id")),
                    c.get("section") or "Other",
                    c.get("name") or "Other",
                    _as_int(c.get("is_game_related")),
                    _as_int(c.get("is_mining")),
                    _as_int(c.get("date_modified")),
                )
                for c in categories
            ),
        )

        _insert_many(
            connection,
            """
            INSERT INTO items VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?
            )
            """,
            (
                (
                    item_id,
                    _as_int(item.get("id_parent")),
                    _as_int(item.get("id_category")),
                    _as_int(item.get("id_company")),
                    _as_int(item.get("id_vehicle")),
                    item.get("name") or f"Objet #{item_id}",
                    item.get("section"),
                    item.get("category"),
                    item.get("company_name"),
                    item.get("vehicle_name"),
                    item.get("slug"),
                    str(item.get("size") or "").strip(),
                    item.get("uuid"),
                    item.get("color"),
                    item.get("color2"),
                    item.get("url_store"),
                    item.get("wiki"),
                    _as_int(item.get("quality")),
                    _as_int(item.get("is_exclusive_pledge")),
                    _as_int(item.get("is_exclusive_subscriber")),
                    _as_int(item.get("is_exclusive_concierge")),
                    _as_int(item.get("is_commodity")),
                    _as_int(item.get("is_harvestable")),
                    json.dumps(item.get("notification"), ensure_ascii=False)
                    if item.get("notification")
                    else None,
                    item.get("game_version"),
                    _as_int(item.get("date_added")),
                    _as_int(item.get("date_modified")),
                )
                for item_id, item in items_by_id.items()
            ),
        )

        _insert_many(
            connection,
            """
            INSERT INTO terminals VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            (
                (
                    terminal_id,
                    terminal.get("name") or f"Terminal #{terminal_id}",
                    terminal.get("fullname"),
                    terminal.get("displayname"),
                    terminal.get("code"),
                    terminal.get("type"),
                    terminal.get("star_system_name"),
                    terminal.get("planet_name"),
                    terminal.get("orbit_name"),
                    terminal.get("moon_name"),
                    terminal.get("space_station_name"),
                    terminal.get("outpost_name"),
                    terminal.get("city_name"),
                    terminal.get("poi_name"),
                    terminal.get("company_name"),
                    _as_int(terminal.get("is_available")),
                    _as_int(terminal.get("is_available_live")),
                    _as_int(terminal.get("is_shop_fps")),
                    _as_int(terminal.get("is_shop_vehicle")),
                    terminal.get("game_version"),
                    _as_int(terminal.get("date_modified")),
                )
                for terminal_id, terminal in terminals_by_id.items()
            ),
        )

        _insert_many(
            connection,
            "INSERT INTO item_offers VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                (
                    _as_int(offer.get("id")),
                    _as_int(offer.get("id_item")),
                    _as_int(offer.get("id_category")),
                    _as_int(offer.get("id_terminal")),
                    _as_float(offer.get("price_buy")),
                    _as_float(offer.get("price_sell")),
                    _as_int(offer.get("date_added")),
                    _as_int(offer.get("date_modified")),
                )
                for offer in valid_item_offers
            ),
        )

        _insert_many(
            connection,
            """
            INSERT INTO vehicles VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            (
                (
                    vehicle_id,
                    _as_int(vehicle.get("id_company")),
                    _as_int(vehicle.get("id_parent")),
                    vehicle.get("name") or f"Véhicule #{vehicle_id}",
                    vehicle.get("name_full"),
                    vehicle_manufacturer_label(
                        vehicle.get("company_name"),
                        vehicle_name=vehicle.get("name"),
                        name_full=vehicle.get("name_full"),
                    ),
                    vehicle.get("slug"),
                    vehicle.get("uuid"),
                    _as_float(vehicle.get("scu")),
                    str(vehicle.get("crew") or ""),
                    _as_float(vehicle.get("mass")),
                    _as_float(vehicle.get("width")),
                    _as_float(vehicle.get("height")),
                    _as_float(vehicle.get("length")),
                    _as_float(vehicle.get("fuel_quantum")),
                    _as_float(vehicle.get("fuel_hydrogen")),
                    vehicle.get("pad_type"),
                    _as_int(vehicle.get("is_concept")),
                    _as_int(vehicle.get("is_ground_vehicle")),
                    _as_int(vehicle.get("is_spaceship")),
                    _as_int(vehicle.get("is_cargo")),
                    _as_int(vehicle.get("is_military") or vehicle.get("is_bomber")),
                    _as_int(vehicle.get("is_exploration")),
                    _as_int(vehicle.get("is_industrial")),
                    _as_int(vehicle.get("is_mining")),
                    _as_int(vehicle.get("is_salvage")),
                    _as_int(vehicle.get("is_medical")),
                    _as_int(vehicle.get("is_racing")),
                    _as_int(vehicle.get("is_refuel")),
                    _as_int(vehicle.get("is_repair")),
                    _role_names(vehicle),
                    vehicle.get("url_photo"),
                    vehicle.get("wiki"),
                    vehicle.get("game_version"),
                    _as_int(vehicle.get("date_added")),
                    _as_int(vehicle.get("date_modified")),
                )
                for vehicle_id, vehicle in vehicles_by_id.items()
            ),
        )

        _insert_many(
            connection,
            "INSERT INTO vehicle_offers VALUES (?, ?, ?, ?, ?, ?)",
            (
                (
                    _as_int(offer.get("id")),
                    _as_int(offer.get("id_vehicle")),
                    _as_int(offer.get("id_terminal")),
                    _as_float(offer.get("price_buy")),
                    _as_int(offer.get("date_added")),
                    _as_int(offer.get("date_modified")),
                )
                for offer in valid_vehicle_offers
            ),
        )

        _insert_many(
            connection,
            "INSERT INTO game_versions VALUES (?, ?, ?)",
            (
                (
                    _as_int(version.get("id")),
                    str(version.get("game_version") or ""),
                    _as_int(version.get("date_added")),
                )
                for version in versions
                if _as_int(version.get("id"))
            ),
        )

        global_parameters = parameters.get("global", {}) if isinstance(parameters, dict) else {}
        counts = {
            "categories": len(categories),
            "items": len(items_by_id),
            "purchasable_items": len(
                {_as_int(row.get("id_item")) for row in valid_item_offers if _as_float(row.get("price_buy")) > 0}
            ),
            "item_offers": len(valid_item_offers),
            "vehicles": len(vehicles_by_id),
            "purchasable_vehicles": len(
                {_as_int(row.get("id_vehicle")) for row in valid_vehicle_offers}
            ),
            "vehicle_offers": len(valid_vehicle_offers),
            "official_vehicle_supplements": len(supplemented_offers),
            "terminals": len(terminals_by_id),
        }
        meta = {
            "app_version": APP_VERSION,
            "author": APP_AUTHOR,
            "source": "UEX API 2.0",
            "source_url": UEX_API_BASE,
            "synced_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "game_version": str(global_parameters.get("game_version") or "inconnue"),
            "ptu_version": str(global_parameters.get("game_version_ptu") or ""),
            "verified_official_build": VERIFIED_LIVE_VERSION,
            "warnings": json.dumps(warnings, ensure_ascii=False),
            "vehicle_supplements": json.dumps(supplemented_offers, ensure_ascii=False),
            "counts": json.dumps(counts, ensure_ascii=False),
        }
        connection.executemany("INSERT INTO meta(key, value) VALUES (?, ?)", meta.items())
        connection.commit()
        connection.execute("PRAGMA optimize")
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise SyncError(f"Échec du contrôle SQLite: {integrity}")
        return counts
    finally:
        connection.close()


def sync_database(
    output_path: str | os.PathLike[str],
    progress: ProgressCallback | None = None,
) -> dict[str, Any]:
    """Download every required dataset and atomically replace ``output_path``."""

    output = Path(output_path).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f"{output.name}.updating")
    if temporary.exists():
        temporary.unlink()

    _notify(progress, 0.01, "Connexion à UEX…")
    endpoint_map = {
        "parameters": "data_parameters/",
        "versions": "game_versions_all/",
        "categories": "categories?type=item",
        "terminals": "terminals/",
        "vehicles": "vehicles/",
        "item_offers": "items_prices_all/",
        "vehicle_offers": "vehicles_purchases_prices_all/",
    }
    datasets: dict[str, Any] = {}
    with ThreadPoolExecutor(max_workers=4, thread_name_prefix="uex-core") as executor:
        futures = {executor.submit(fetch_json, endpoint): key for key, endpoint in endpoint_map.items()}
        completed = 0
        for future in as_completed(futures):
            key = futures[future]
            datasets[key] = future.result()
            completed += 1
            _notify(
                progress,
                0.04 + completed / len(futures) * 0.18,
                f"Téléchargement des données principales ({completed}/{len(futures)})…",
            )

    categories = datasets.get("categories")
    if not isinstance(categories, list) or not categories:
        raise SyncError("La liste des catégories UEX est vide.")

    _notify(progress, 0.23, "Récupération de toutes les catégories d'objets…")
    all_items: dict[int, dict[str, Any]] = {}
    warnings: list[str] = []
    with ThreadPoolExecutor(max_workers=4, thread_name_prefix="uex-items") as executor:
        futures = {
            executor.submit(fetch_json, f"items?id_category={_as_int(category.get('id'))}"): category
            for category in categories
            if _as_int(category.get("id"))
        }
        completed = 0
        for future in as_completed(futures):
            category = futures[future]
            rows = future.result()
            # UEX returns JSON null for a valid but currently empty category.
            if rows is None:
                rows = []
            if not isinstance(rows, list):
                raise SyncError(f"Catégorie UEX invalide: {category.get('name')}")
            for row in rows:
                item_id = _as_int(row.get("id"))
                if item_id:
                    all_items[item_id] = row
            completed += 1
            _notify(
                progress,
                0.23 + completed / max(1, len(futures)) * 0.49,
                f"Objets et équipements ({completed}/{len(futures)})…",
            )

    _notify(progress, 0.76, "Validation des prix et des lieux…")
    try:
        counts = _build_database(temporary, datasets, list(all_items.values()), warnings)
        _notify(progress, 0.95, "Contrôle d'intégrité de la base…")
        # Windows briefly locks SQLite files while a query is closing.  Retry
        # the final atomic swap for a few seconds instead of discarding an
        # otherwise valid two-minute download.
        for attempt in range(12):
            try:
                os.replace(temporary, output)
                break
            except PermissionError:
                if attempt == 11:
                    raise
                time.sleep(0.25)
    except Exception:
        if temporary.exists():
            temporary.unlink()
        raise

    _notify(progress, 1.0, "Données à jour et prêtes.")
    parameters = datasets.get("parameters") or {}
    game_version = (parameters.get("global") or {}).get("game_version") if isinstance(parameters, dict) else None
    return {
        "path": str(output),
        "game_version": game_version or "inconnue",
        "counts": counts,
        "warnings": warnings,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Créer la base hors ligne Asteriax Verse")
    parser.add_argument("--output", required=True, help="Chemin du fichier SQLite à créer")
    args = parser.parse_args()

    def console_progress(fraction: float, message: str) -> None:
        print(f"[{fraction * 100:5.1f}%] {message}", flush=True)

    result = sync_database(args.output, console_progress)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
