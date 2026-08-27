"""Read-only catalogue queries and the small per-user favourites store."""

from __future__ import annotations

import json
import sqlite3
import threading
from collections import OrderedDict
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable, Iterator

from .manufacturers import (
    official_vehicle_names,
    vehicle_manufacturer_label,
    vehicle_manufacturer_sources,
)


PERFORMANCE_INDEXES = (
    "CREATE INDEX IF NOT EXISTS idx_items_filters ON items(section, category, manufacturer, size)",
    "CREATE INDEX IF NOT EXISTS idx_item_offers_price ON item_offers(price_buy, item_id, terminal_id)",
    "CREATE INDEX IF NOT EXISTS idx_vehicle_offers_price ON vehicle_offers(price_buy, vehicle_id, terminal_id)",
    "CREATE INDEX IF NOT EXISTS idx_terminals_live_location ON terminals(is_available_live, star_system, planet)",
)


def ensure_performance_indexes(database_path: str | Path) -> None:
    """Add read-optimised indexes to existing user catalogues once and safely."""

    with sqlite3.connect(Path(database_path), timeout=15) as connection:
        for statement in PERFORMANCE_INDEXES:
            connection.execute(statement)
        connection.execute("PRAGMA optimize")


def format_price(value: float | int | None) -> str:
    """Format an aUEC amount with French grouping."""

    if value is None:
        return "—"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "—"
    if number <= 0:
        return "—"
    rounded = int(round(number))
    return f"{rounded:,}".replace(",", " ") + " aUEC"


def format_timestamp(value: int | float | None) -> str:
    if not value:
        return "—"
    from datetime import datetime

    try:
        return datetime.fromtimestamp(float(value)).strftime("%d/%m/%Y")
    except (OSError, OverflowError, TypeError, ValueError):
        return "—"


def location_label(row: dict[str, Any] | sqlite3.Row, *, include_shop: bool = True) -> str:
    """Build a compact System › Planet › Place › Shop breadcrumb."""

    getter = row.get if isinstance(row, dict) else lambda key: row[key] if key in row.keys() else None
    candidates = [
        getter("star_system"),
        getter("planet"),
        getter("moon"),
        getter("city"),
        getter("space_station"),
        getter("outpost"),
        getter("poi"),
    ]
    if include_shop:
        candidates.append(getter("terminal_name"))
    clean: list[str] = []
    seen: set[str] = set()
    for value in candidates:
        if not value:
            continue
        text = str(value).strip()
        key = text.casefold()
        # Terminal names often contain their city; exact duplicates are removed
        # while useful descriptive names remain intact.
        if key not in seen:
            clean.append(text)
            seen.add(key)
    return "  ›  ".join(clean) or "Lieu non renseigné"


class DataRepository:
    """Stateless catalogue access; each query gets a short-lived connection."""

    def __init__(self, database_path: str | Path):
        self.path = Path(database_path)
        self._query_cache: OrderedDict[tuple[Any, ...], list[dict[str, Any]]] = OrderedDict()
        self._cache_lock = threading.RLock()
        self._cache_limit = 8
        self.cache_hits = 0

    def _cached_rows(self, key: tuple[Any, ...]) -> list[dict[str, Any]] | None:
        with self._cache_lock:
            cached = self._query_cache.pop(key, None)
            if cached is None:
                return None
            self._query_cache[key] = cached
            self.cache_hits += 1
            return [dict(row) for row in cached]

    def _remember_rows(
        self,
        key: tuple[Any, ...],
        rows: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        snapshot = [dict(row) for row in rows]
        with self._cache_lock:
            self._query_cache[key] = snapshot
            while len(self._query_cache) > self._cache_limit:
                self._query_cache.popitem(last=False)
        return [dict(row) for row in snapshot]

    def clear_cache(self) -> None:
        with self._cache_lock:
            self._query_cache.clear()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path, timeout=15)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only = ON")
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    @staticmethod
    def _dicts(rows: Iterable[sqlite3.Row]) -> list[dict[str, Any]]:
        return [dict(row) for row in rows]

    @staticmethod
    def _vehicle_record(row: sqlite3.Row | dict[str, Any]) -> dict[str, Any]:
        record = dict(row)
        record["manufacturer"] = vehicle_manufacturer_label(
            record.get("manufacturer"),
            vehicle_name=record.get("name"),
            name_full=record.get("name_full"),
        )
        return record

    @classmethod
    def _vehicle_dicts(cls, rows: Iterable[sqlite3.Row]) -> list[dict[str, Any]]:
        return [cls._vehicle_record(row) for row in rows]

    def meta(self) -> dict[str, str]:
        with self._connect() as connection:
            return {row["key"]: row["value"] for row in connection.execute("SELECT key, value FROM meta")}

    def meta_counts(self) -> dict[str, int]:
        raw = self.meta().get("counts", "{}")
        try:
            parsed = json.loads(raw)
            return {str(k): int(v) for k, v in parsed.items()}
        except (TypeError, ValueError, json.JSONDecodeError):
            return {}

    def dashboard_stats(self) -> dict[str, int]:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    (SELECT COUNT(DISTINCT vehicle_id) FROM vehicle_offers WHERE price_buy > 0)
                        AS vehicles,
                    (SELECT COUNT(DISTINCT item_id) FROM item_offers WHERE price_buy > 0)
                        AS items,
                    (SELECT COUNT(DISTINCT terminal_id) FROM (
                        SELECT terminal_id FROM item_offers WHERE price_buy > 0
                        UNION
                        SELECT terminal_id FROM vehicle_offers WHERE price_buy > 0
                    )) AS locations,
                    (SELECT COUNT(DISTINCT i.category_id)
                        FROM items i JOIN item_offers o ON o.item_id = i.id
                        WHERE o.price_buy > 0) AS categories
                """
            ).fetchone()
            return dict(row)

    def coverage_by_section(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT i.section,
                       COUNT(DISTINCT i.id) AS item_count,
                       COUNT(DISTINCT o.terminal_id) AS shop_count,
                       MIN(CASE WHEN o.price_buy > 0 THEN o.price_buy END) AS price_min
                FROM items i
                JOIN item_offers o ON o.item_id = i.id AND o.price_buy > 0
                GROUP BY i.section
                ORDER BY item_count DESC, i.section COLLATE NOCASE
                """
            ).fetchall()
            return self._dicts(rows)

    def latest_game_versions(self, limit: int = 7) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT game_version, release_timestamp
                FROM game_versions
                ORDER BY release_timestamp DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return self._dicts(rows)

    def item_filter_options(self, sections: list[str] | None = None) -> dict[str, list[str]]:
        clauses = ["EXISTS (SELECT 1 FROM item_offers o WHERE o.item_id = i.id AND o.price_buy > 0)"]
        params: list[Any] = []
        if sections:
            clauses.append(f"i.section IN ({','.join('?' for _ in sections)})")
            params.extend(sections)
        where = " AND ".join(clauses)
        with self._connect() as connection:
            result: dict[str, list[str]] = {}
            for key, column in (
                ("sections", "section"),
                ("categories", "category"),
                ("manufacturers", "manufacturer"),
                ("sizes", "size"),
            ):
                rows = connection.execute(
                    f"""
                    SELECT DISTINCT i.{column} AS value
                    FROM items i
                    WHERE {where} AND COALESCE(i.{column}, '') <> ''
                    ORDER BY i.{column} COLLATE NOCASE
                    """,
                    params,
                ).fetchall()
                result[key] = [str(row["value"]) for row in rows]
            locations = connection.execute(
                """
                SELECT DISTINCT t.star_system, t.planet
                FROM terminals t
                JOIN item_offers o ON o.terminal_id = t.id AND o.price_buy > 0
                ORDER BY t.star_system COLLATE NOCASE, t.planet COLLATE NOCASE
                """
            ).fetchall()
            result["systems"] = sorted({row["star_system"] for row in locations if row["star_system"]})
            result["planets"] = sorted({row["planet"] for row in locations if row["planet"]})
            return result

    def search_items(
        self,
        *,
        sections: list[str] | None = None,
        search: str = "",
        section: str = "",
        category: str = "",
        manufacturer: str = "",
        size: str = "",
        star_system: str = "",
        planet: str = "",
        maximum_price: float | None = None,
        only_purchasable: bool = True,
        ids: set[int] | None = None,
        limit: int = 6000,
    ) -> list[dict[str, Any]]:
        cache_key = (
            "items",
            tuple(sections or ()),
            search.strip().casefold(),
            section,
            category,
            manufacturer,
            size,
            star_system,
            planet,
            maximum_price,
            only_purchasable,
            tuple(sorted(ids)) if ids is not None else None,
            int(limit),
        )
        cached = self._cached_rows(cache_key)
        if cached is not None:
            return cached
        offer_clauses = ["o.price_buy > 0"]
        offer_params: list[Any] = []
        if star_system:
            offer_clauses.append("t.star_system = ?")
            offer_params.append(star_system)
        if planet:
            offer_clauses.append("t.planet = ?")
            offer_params.append(planet)
        if maximum_price is not None and maximum_price > 0:
            offer_clauses.append("o.price_buy <= ?")
            offer_params.append(maximum_price)

        item_clauses: list[str] = ["1 = 1"]
        item_params: list[Any] = []
        if sections:
            item_clauses.append(f"i.section IN ({','.join('?' for _ in sections)})")
            item_params.extend(sections)
        if search.strip():
            needle = f"%{search.strip()}%"
            item_clauses.append(
                "(i.name LIKE ? COLLATE NOCASE OR i.manufacturer LIKE ? COLLATE NOCASE "
                "OR i.category LIKE ? COLLATE NOCASE)"
            )
            item_params.extend([needle, needle, needle])
        if section:
            item_clauses.append("i.section = ?")
            item_params.append(section)
        if category:
            item_clauses.append("i.category = ?")
            item_params.append(category)
        if manufacturer:
            item_clauses.append("i.manufacturer = ?")
            item_params.append(manufacturer)
        if size:
            item_clauses.append("i.size = ?")
            item_params.append(size)
        if ids is not None:
            if not ids:
                return []
            item_clauses.append(f"i.id IN ({','.join('?' for _ in ids)})")
            item_params.extend(sorted(ids))

        join = "JOIN" if only_purchasable or star_system or planet or maximum_price else "LEFT JOIN"
        sql = f"""
            WITH ranked_offer AS (
                SELECT o.item_id, o.price_buy, o.date_modified,
                       t.name AS terminal_name, t.star_system, t.planet, t.moon,
                       t.city, t.space_station, t.outpost, t.poi,
                       ROW_NUMBER() OVER (
                           PARTITION BY o.item_id
                           ORDER BY o.price_buy ASC, o.date_modified DESC, t.name COLLATE NOCASE
                       ) AS rank_no
                FROM item_offers o
                JOIN terminals t ON t.id = o.terminal_id
                WHERE {' AND '.join(offer_clauses)}
            )
            SELECT i.id, i.name, i.section, i.category, i.manufacturer, i.size,
                   i.color, i.color2, i.quality, i.game_version, i.wiki,
                   r.price_buy AS price_min, r.date_modified AS price_date,
                   r.terminal_name, r.star_system, r.planet, r.moon, r.city,
                   r.space_station, r.outpost, r.poi
            FROM items i
            {join} ranked_offer r ON r.item_id = i.id AND r.rank_no = 1
            WHERE {' AND '.join(item_clauses)}
            ORDER BY i.name COLLATE NOCASE
            LIMIT ?
        """
        params = offer_params + item_params + [limit]
        with self._connect() as connection:
            rows = self._dicts(connection.execute(sql, params).fetchall())
        return self._remember_rows(cache_key, rows)

    def item_detail(self, item_id: int) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
            return dict(row) if row else None

    def item_offers(self, item_id: int) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT o.price_buy, o.price_sell, o.date_modified,
                       t.name AS terminal_name, t.fullname AS terminal_fullname,
                       t.star_system, t.planet, t.orbit_name, t.moon, t.city,
                       t.space_station, t.outpost, t.poi
                FROM item_offers o
                JOIN terminals t ON t.id = o.terminal_id
                WHERE o.item_id = ? AND o.price_buy > 0
                ORDER BY o.price_buy ASC, t.star_system COLLATE NOCASE,
                         t.planet COLLATE NOCASE, t.name COLLATE NOCASE
                """,
                (item_id,),
            ).fetchall()
            return self._dicts(rows)

    def vehicle_filter_options(self) -> dict[str, list[str]]:
        with self._connect() as connection:
            manufacturers = connection.execute(
                """
                SELECT DISTINCT v.manufacturer AS value
                FROM vehicles v JOIN vehicle_offers o ON o.vehicle_id = v.id
                WHERE o.price_buy > 0 AND COALESCE(v.manufacturer, '') <> ''
                ORDER BY v.manufacturer COLLATE NOCASE
                """
            ).fetchall()
            locations = connection.execute(
                """
                SELECT DISTINCT t.star_system, t.planet
                FROM terminals t JOIN vehicle_offers o ON o.terminal_id = t.id
                WHERE o.price_buy > 0
                ORDER BY t.star_system COLLATE NOCASE, t.planet COLLATE NOCASE
                """
            ).fetchall()
            labels = {
                vehicle_manufacturer_label(row["value"])
                for row in manufacturers
                if row["value"]
            }
            return {
                "manufacturers": sorted(labels, key=str.casefold),
                "systems": sorted({row["star_system"] for row in locations if row["star_system"]}),
                "planets": sorted({row["planet"] for row in locations if row["planet"]}),
            }

    def search_vehicles(
        self,
        *,
        search: str = "",
        manufacturer: str = "",
        vehicle_type: str = "",
        star_system: str = "",
        planet: str = "",
        maximum_price: float | None = None,
        ids: set[int] | None = None,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        cache_key = (
            "vehicles",
            search.strip().casefold(),
            manufacturer,
            vehicle_type,
            star_system,
            planet,
            maximum_price,
            tuple(sorted(ids)) if ids is not None else None,
            int(limit),
        )
        cached = self._cached_rows(cache_key)
        if cached is not None:
            return cached
        offer_clauses = ["o.price_buy > 0"]
        offer_params: list[Any] = []
        if star_system:
            offer_clauses.append("t.star_system = ?")
            offer_params.append(star_system)
        if planet:
            offer_clauses.append("t.planet = ?")
            offer_params.append(planet)
        if maximum_price is not None and maximum_price > 0:
            offer_clauses.append("o.price_buy <= ?")
            offer_params.append(maximum_price)

        clauses = ["1 = 1"]
        params: list[Any] = []
        if search.strip():
            needle = f"%{search.strip()}%"
            clauses.append(
                "(v.name LIKE ? COLLATE NOCASE OR v.name_full LIKE ? COLLATE NOCASE "
                "OR v.manufacturer LIKE ? COLLATE NOCASE OR v.roles LIKE ? COLLATE NOCASE)"
            )
            params.extend([needle, needle, needle, needle])
        if manufacturer:
            sources = vehicle_manufacturer_sources(manufacturer)
            audited_names = official_vehicle_names(manufacturer)
            manufacturer_parts = [f"v.manufacturer IN ({','.join('?' for _ in sources)})"]
            params.extend(sources)
            if audited_names:
                manufacturer_parts.append(
                    f"v.name COLLATE NOCASE IN ({','.join('?' for _ in audited_names)})"
                )
                params.extend(audited_names)
            clauses.append(f"({' OR '.join(manufacturer_parts)})")
        if vehicle_type == "Vaisseaux":
            clauses.append("v.is_ground_vehicle = 0")
        elif vehicle_type == "Véhicules terrestres":
            clauses.append("v.is_ground_vehicle = 1")
        if ids is not None:
            if not ids:
                return []
            clauses.append(f"v.id IN ({','.join('?' for _ in ids)})")
            params.extend(sorted(ids))

        sql = f"""
            WITH ranked_offer AS (
                SELECT o.vehicle_id, o.price_buy, o.date_modified,
                       t.name AS terminal_name, t.star_system, t.planet, t.moon,
                       t.city, t.space_station, t.outpost, t.poi,
                       ROW_NUMBER() OVER (
                           PARTITION BY o.vehicle_id
                           ORDER BY o.price_buy ASC, o.date_modified DESC, t.name COLLATE NOCASE
                       ) AS rank_no
                FROM vehicle_offers o
                JOIN terminals t ON t.id = o.terminal_id
                WHERE {' AND '.join(offer_clauses)}
            )
            SELECT v.id, v.name, v.name_full, v.manufacturer, v.scu, v.crew,
                   v.mass, v.width, v.height, v.length, v.pad_type,
                   v.is_ground_vehicle, v.is_spaceship, v.is_concept, v.roles,
                   v.game_version, v.url_photo,
                   r.price_buy AS price_min, r.date_modified AS price_date,
                   r.terminal_name, r.star_system, r.planet, r.moon, r.city,
                   r.space_station, r.outpost, r.poi
            FROM vehicles v
            JOIN ranked_offer r ON r.vehicle_id = v.id AND r.rank_no = 1
            WHERE {' AND '.join(clauses)}
            ORDER BY v.name COLLATE NOCASE
            LIMIT ?
        """
        query_params = offer_params + params + [limit]
        with self._connect() as connection:
            rows = self._vehicle_dicts(connection.execute(sql, query_params).fetchall())
        return self._remember_rows(cache_key, rows)

    def vehicle_detail(self, vehicle_id: int) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM vehicles WHERE id = ?", (vehicle_id,)).fetchone()
            return self._vehicle_record(row) if row else None

    def vehicle_offers(self, vehicle_id: int) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT o.price_buy, o.date_modified,
                       t.name AS terminal_name, t.fullname AS terminal_fullname,
                       t.star_system, t.planet, t.orbit_name, t.moon, t.city,
                       t.space_station, t.outpost, t.poi
                FROM vehicle_offers o
                JOIN terminals t ON t.id = o.terminal_id
                WHERE o.vehicle_id = ? AND o.price_buy > 0
                ORDER BY o.price_buy ASC, t.star_system COLLATE NOCASE,
                         t.planet COLLATE NOCASE, t.name COLLATE NOCASE
                """,
                (vehicle_id,),
            ).fetchall()
            return self._dicts(rows)

    def location_filter_options(self) -> dict[str, list[str]]:
        """Return systems and planets containing at least one active shop."""

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT DISTINCT star_system, planet
                FROM terminals
                WHERE is_available_live = 1
                  AND (
                    EXISTS (SELECT 1 FROM item_offers io WHERE io.terminal_id = terminals.id AND io.price_buy > 0)
                    OR EXISTS (SELECT 1 FROM vehicle_offers vo WHERE vo.terminal_id = terminals.id AND vo.price_buy > 0)
                  )
                ORDER BY star_system COLLATE NOCASE, planet COLLATE NOCASE
                """
            ).fetchall()
        return {
            "systems": sorted({str(row["star_system"]) for row in rows if row["star_system"]}, key=str.casefold),
            "planets": sorted({str(row["planet"]) for row in rows if row["planet"]}, key=str.casefold),
        }

    def search_terminals(
        self,
        *,
        search: str = "",
        star_system: str = "",
        planet: str = "",
        limit: int = 1500,
    ) -> list[dict[str, Any]]:
        clauses = [
            "t.is_available_live = 1",
            "(EXISTS (SELECT 1 FROM item_offers io WHERE io.terminal_id = t.id AND io.price_buy > 0) "
            " OR EXISTS (SELECT 1 FROM vehicle_offers vo WHERE vo.terminal_id = t.id AND vo.price_buy > 0))",
        ]
        params: list[Any] = []
        if search.strip():
            needle = f"%{search.strip()}%"
            clauses.append(
                "(t.name LIKE ? COLLATE NOCASE OR t.fullname LIKE ? COLLATE NOCASE "
                "OR t.displayname LIKE ? COLLATE NOCASE OR t.company LIKE ? COLLATE NOCASE "
                "OR t.city LIKE ? COLLATE NOCASE OR t.space_station LIKE ? COLLATE NOCASE)"
            )
            params.extend([needle] * 6)
        if star_system:
            clauses.append("t.star_system = ?")
            params.append(star_system)
        if planet:
            clauses.append("t.planet = ?")
            params.append(planet)
        params.append(limit)
        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT t.*,
                       (SELECT COUNT(DISTINCT io.item_id) FROM item_offers io
                        WHERE io.terminal_id = t.id AND io.price_buy > 0) AS item_count,
                       (SELECT COUNT(DISTINCT vo.vehicle_id) FROM vehicle_offers vo
                        WHERE vo.terminal_id = t.id AND vo.price_buy > 0) AS vehicle_count
                FROM terminals t
                WHERE {' AND '.join(clauses)}
                ORDER BY t.star_system COLLATE NOCASE, t.planet COLLATE NOCASE,
                         t.name COLLATE NOCASE
                LIMIT ?
                """,
                params,
            ).fetchall()
        return self._dicts(rows)

    def terminal_detail(self, terminal_id: int) -> dict[str, Any] | None:
        rows = self.search_terminals(limit=2000)
        return next((row for row in rows if int(row["id"]) == int(terminal_id)), None)

    def terminal_inventory(self, terminal_id: int) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT 'item' AS kind, i.id, i.name, i.section, i.category,
                       i.manufacturer, i.size, o.price_buy
                FROM item_offers o
                JOIN items i ON i.id = o.item_id
                WHERE o.terminal_id = ? AND o.price_buy > 0
                UNION ALL
                SELECT 'vehicle' AS kind, v.id, v.name, 'Vehicles' AS section,
                       CASE WHEN v.is_ground_vehicle = 1 THEN 'Véhicule terrestre' ELSE 'Vaisseau' END AS category,
                       v.manufacturer, NULL AS size, o.price_buy
                FROM vehicle_offers o
                JOIN vehicles v ON v.id = o.vehicle_id
                WHERE o.terminal_id = ? AND o.price_buy > 0
                ORDER BY name COLLATE NOCASE
                """,
                (int(terminal_id), int(terminal_id)),
            ).fetchall()
        records = self._dicts(rows)
        for record in records:
            if record.get("kind") == "vehicle":
                record["manufacturer"] = vehicle_manufacturer_label(
                    record.get("manufacturer"),
                    vehicle_name=record.get("name"),
                )
        return records

    def global_search(self, query: str, limit: int = 36) -> list[dict[str, Any]]:
        """Search purchasable items, vehicles and active shops at once."""

        query = query.strip()
        if not query:
            return []
        per_kind = max(8, limit // 3 + 3)
        results: list[dict[str, Any]] = []
        for row in self.search_items(search=query, limit=per_kind):
            results.append(
                {
                    "kind": "item",
                    "id": int(row["id"]),
                    "name": row["name"],
                    "subtitle": " • ".join(
                        value for value in (row.get("category"), row.get("manufacturer")) if value
                    ),
                    "price_min": row.get("price_min"),
                    "location": location_label(row),
                }
            )
        for row in self.search_vehicles(search=query, limit=per_kind):
            results.append(
                {
                    "kind": "vehicle",
                    "id": int(row["id"]),
                    "name": row["name"],
                    "subtitle": " • ".join(
                        value for value in (row.get("manufacturer"), row.get("roles")) if value
                    ),
                    "price_min": row.get("price_min"),
                    "location": location_label(row),
                }
            )
        for row in self.search_terminals(search=query, limit=per_kind):
            results.append(
                {
                    "kind": "terminal",
                    "id": int(row["id"]),
                    "name": row["name"],
                    "subtitle": row.get("company") or "Boutique",
                    "price_min": None,
                    "location": location_label(row, include_shop=False),
                }
            )

        needle = query.casefold()

        def score(row: dict[str, Any]) -> tuple[int, int, str]:
            name = str(row.get("name") or "").casefold()
            match = 0 if name == needle else 1 if name.startswith(needle) else 2
            kind_rank = {"vehicle": 0, "item": 1, "terminal": 2}.get(str(row.get("kind")), 3)
            return match, kind_rank, name

        return sorted(results, key=score)[:limit]

    def resolve_entities(self, entries: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
        """Attach catalogue names, prices and locations to user-store rows."""

        resolved: list[dict[str, Any]] = []
        for entry in entries:
            kind = str(entry.get("kind") or "")
            entity_id = int(entry.get("entity_id") or 0)
            detail = self.item_detail(entity_id) if kind == "item" else self.vehicle_detail(entity_id)
            if not detail:
                continue
            offers = self.item_offers(entity_id) if kind == "item" else self.vehicle_offers(entity_id)
            best = offers[0] if offers else {}
            resolved.append(
                {
                    **entry,
                    "name": detail.get("name") or f"#{entity_id}",
                    "manufacturer": detail.get("manufacturer") or "—",
                    "category": detail.get("category") if kind == "item" else detail.get("roles"),
                    "size": detail.get("size") if kind == "item" else detail.get("scu"),
                    "price_min": best.get("price_buy"),
                    "location": location_label(best) if best else "Lieu non renseigné",
                    "detail": detail,
                    "best_offer": best,
                }
            )
        return resolved

    def shopping_plan(self, entries: Iterable[dict[str, Any]]) -> dict[str, Any]:
        """Group each entry's cheapest offer into a readable travel plan."""

        resolved = self.resolve_entities(entries)
        groups: dict[str, dict[str, Any]] = {}
        total = 0.0
        missing: list[str] = []
        for row in resolved:
            offer = row.get("best_offer") or {}
            price = float(row.get("price_min") or 0)
            quantity = max(1, int(row.get("quantity") or 1))
            if not offer or price <= 0:
                missing.append(str(row.get("name") or "Objet inconnu"))
                continue
            total += price * quantity
            label = location_label(offer)
            group = groups.setdefault(
                label,
                {
                    "label": label,
                    "star_system": offer.get("star_system") or "",
                    "planet": offer.get("planet") or "",
                    "place": offer.get("city") or offer.get("space_station") or offer.get("outpost") or "",
                    "terminal": offer.get("terminal_name") or "",
                    "lines": [],
                    "subtotal": 0.0,
                },
            )
            line_total = price * quantity
            group["subtotal"] += line_total
            group["lines"].append(
                {
                    "kind": row["kind"],
                    "entity_id": row["entity_id"],
                    "name": row["name"],
                    "quantity": quantity,
                    "unit_price": price,
                    "total": line_total,
                }
            )
        ordered = sorted(
            groups.values(),
            key=lambda group: (
                str(group["star_system"]).casefold(),
                str(group["planet"]).casefold(),
                str(group["place"]).casefold(),
                str(group["terminal"]).casefold(),
            ),
        )
        return {"total": total, "groups": ordered, "missing": missing, "entries": resolved}


class UserStore:
    """Small writable database containing local preferences and planning data."""

    VALID_KINDS = {"item", "vehicle"}

    def __init__(self, database_path: str | Path):
        self.path = Path(database_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialise()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _initialise(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS favourites (
                    kind TEXT NOT NULL,
                    entity_id INTEGER NOT NULL,
                    added_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (kind, entity_id)
                );
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS shopping_list (
                    kind TEXT NOT NULL,
                    entity_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL DEFAULT 1,
                    purchased INTEGER NOT NULL DEFAULT 0,
                    added_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (kind, entity_id)
                );
                CREATE TABLE IF NOT EXISTS comparisons (
                    kind TEXT NOT NULL,
                    entity_id INTEGER NOT NULL,
                    added_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (kind, entity_id)
                );
                CREATE TABLE IF NOT EXISTS recent (
                    kind TEXT NOT NULL,
                    entity_id INTEGER NOT NULL,
                    viewed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (kind, entity_id)
                );
                CREATE TABLE IF NOT EXISTS loadout_items (
                    vehicle_id INTEGER NOT NULL,
                    item_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL DEFAULT 1,
                    added_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (vehicle_id, item_id)
                );
                """
            )

    def ids(self, kind: str) -> set[int]:
        if kind not in self.VALID_KINDS:
            return set()
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT entity_id FROM favourites WHERE kind = ?", (kind,)
            ).fetchall()
            return {int(row["entity_id"]) for row in rows}

    def is_favourite(self, kind: str, entity_id: int) -> bool:
        if kind not in self.VALID_KINDS:
            return False
        with self._connect() as connection:
            return (
                connection.execute(
                    "SELECT 1 FROM favourites WHERE kind = ? AND entity_id = ?",
                    (kind, int(entity_id)),
                ).fetchone()
                is not None
            )

    def toggle(self, kind: str, entity_id: int) -> bool:
        if kind not in self.VALID_KINDS:
            raise ValueError(f"Type de favori invalide: {kind}")
        entity_id = int(entity_id)
        with self._connect() as connection:
            exists = connection.execute(
                "SELECT 1 FROM favourites WHERE kind = ? AND entity_id = ?",
                (kind, entity_id),
            ).fetchone()
            if exists:
                connection.execute(
                    "DELETE FROM favourites WHERE kind = ? AND entity_id = ?",
                    (kind, entity_id),
                )
                return False
            connection.execute(
                "INSERT INTO favourites(kind, entity_id) VALUES (?, ?)",
                (kind, entity_id),
            )
            return True

    def set_setting(self, key: str, value: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO settings(key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (key, value),
            )

    def get_setting(self, key: str, default: str = "") -> str:
        with self._connect() as connection:
            row = connection.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
            return str(row["value"]) if row else default

    def set_json_setting(self, key: str, value: Any) -> None:
        self.set_setting(key, json.dumps(value, ensure_ascii=False))

    def get_json_setting(self, key: str, default: Any) -> Any:
        raw = self.get_setting(key)
        if not raw:
            return default
        try:
            return json.loads(raw)
        except (TypeError, ValueError, json.JSONDecodeError):
            return default

    def setting_bool(self, key: str, default: bool = False) -> bool:
        raw = self.get_setting(key, "1" if default else "0").strip().casefold()
        return raw in {"1", "true", "yes", "oui", "on"}

    def add_recent(self, kind: str, entity_id: int, *, keep: int = 30) -> None:
        if kind not in self.VALID_KINDS:
            return
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO recent(kind, entity_id, viewed_at)
                VALUES (?, ?, strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
                ON CONFLICT(kind, entity_id) DO UPDATE SET viewed_at = excluded.viewed_at
                """,
                (kind, int(entity_id)),
            )
            old = connection.execute(
                "SELECT kind, entity_id FROM recent ORDER BY viewed_at DESC LIMIT -1 OFFSET ?",
                (max(1, int(keep)),),
            ).fetchall()
            connection.executemany(
                "DELETE FROM recent WHERE kind = ? AND entity_id = ?",
                ((row["kind"], row["entity_id"]) for row in old),
            )

    def recent_entries(self, limit: int = 12) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT kind, entity_id, viewed_at FROM recent ORDER BY viewed_at DESC LIMIT ?",
                (max(1, int(limit)),),
            ).fetchall()
        return [dict(row) for row in rows]

    def add_to_shopping(self, kind: str, entity_id: int, quantity: int = 1) -> None:
        if kind not in self.VALID_KINDS:
            raise ValueError(f"Type d'achat invalide: {kind}")
        quantity = max(1, int(quantity))
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO shopping_list(kind, entity_id, quantity)
                VALUES (?, ?, ?)
                ON CONFLICT(kind, entity_id) DO UPDATE SET
                    quantity = shopping_list.quantity + excluded.quantity,
                    purchased = 0
                """,
                (kind, int(entity_id), quantity),
            )

    def shopping_entries(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT kind, entity_id, quantity, purchased, added_at
                FROM shopping_list
                ORDER BY purchased, added_at, kind, entity_id
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def set_shopping_quantity(self, kind: str, entity_id: int, quantity: int) -> None:
        quantity = int(quantity)
        with self._connect() as connection:
            if quantity <= 0:
                connection.execute(
                    "DELETE FROM shopping_list WHERE kind = ? AND entity_id = ?",
                    (kind, int(entity_id)),
                )
            else:
                connection.execute(
                    "UPDATE shopping_list SET quantity = ? WHERE kind = ? AND entity_id = ?",
                    (quantity, kind, int(entity_id)),
                )

    def toggle_shopping_purchased(self, kind: str, entity_id: int) -> bool:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT purchased FROM shopping_list WHERE kind = ? AND entity_id = ?",
                (kind, int(entity_id)),
            ).fetchone()
            if not row:
                return False
            value = 0 if int(row["purchased"]) else 1
            connection.execute(
                "UPDATE shopping_list SET purchased = ? WHERE kind = ? AND entity_id = ?",
                (value, kind, int(entity_id)),
            )
            return bool(value)

    def remove_from_shopping(self, kind: str, entity_id: int) -> None:
        with self._connect() as connection:
            connection.execute(
                "DELETE FROM shopping_list WHERE kind = ? AND entity_id = ?",
                (kind, int(entity_id)),
            )

    def clear_shopping(self, *, purchased_only: bool = False) -> None:
        with self._connect() as connection:
            if purchased_only:
                connection.execute("DELETE FROM shopping_list WHERE purchased = 1")
            else:
                connection.execute("DELETE FROM shopping_list")

    def comparison_ids(self, kind: str) -> list[int]:
        if kind not in self.VALID_KINDS:
            return []
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT entity_id FROM comparisons WHERE kind = ? ORDER BY added_at",
                (kind,),
            ).fetchall()
        return [int(row["entity_id"]) for row in rows]

    def add_comparison(self, kind: str, entity_id: int, *, limit: int = 4) -> bool:
        if kind not in self.VALID_KINDS:
            return False
        entity_id = int(entity_id)
        with self._connect() as connection:
            if connection.execute(
                "SELECT 1 FROM comparisons WHERE kind = ? AND entity_id = ?",
                (kind, entity_id),
            ).fetchone():
                return True
            count = connection.execute(
                "SELECT COUNT(*) FROM comparisons WHERE kind = ?", (kind,)
            ).fetchone()[0]
            if count >= max(1, int(limit)):
                return False
            connection.execute(
                "INSERT INTO comparisons(kind, entity_id) VALUES (?, ?)",
                (kind, entity_id),
            )
            return True

    def remove_comparison(self, kind: str, entity_id: int) -> None:
        with self._connect() as connection:
            connection.execute(
                "DELETE FROM comparisons WHERE kind = ? AND entity_id = ?",
                (kind, int(entity_id)),
            )

    def clear_comparisons(self, kind: str) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM comparisons WHERE kind = ?", (kind,))

    def loadout_entries(self, vehicle_id: int) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT 'item' AS kind, item_id AS entity_id, quantity, added_at
                FROM loadout_items WHERE vehicle_id = ? ORDER BY added_at
                """,
                (int(vehicle_id),),
            ).fetchall()
        return [dict(row) for row in rows]

    def add_to_loadout(self, vehicle_id: int, item_id: int, quantity: int = 1) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO loadout_items(vehicle_id, item_id, quantity)
                VALUES (?, ?, ?)
                ON CONFLICT(vehicle_id, item_id) DO UPDATE SET
                    quantity = loadout_items.quantity + excluded.quantity
                """,
                (int(vehicle_id), int(item_id), max(1, int(quantity))),
            )

    def set_loadout_quantity(self, vehicle_id: int, item_id: int, quantity: int) -> None:
        with self._connect() as connection:
            if int(quantity) <= 0:
                connection.execute(
                    "DELETE FROM loadout_items WHERE vehicle_id = ? AND item_id = ?",
                    (int(vehicle_id), int(item_id)),
                )
            else:
                connection.execute(
                    "UPDATE loadout_items SET quantity = ? WHERE vehicle_id = ? AND item_id = ?",
                    (int(quantity), int(vehicle_id), int(item_id)),
                )

    def clear_loadout(self, vehicle_id: int) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM loadout_items WHERE vehicle_id = ?", (int(vehicle_id),))
