"""Offline validation command for the bundled catalogue."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATABASE = ROOT / "data" / "asteriax_sc.db"


def main() -> int:
    checks: list[tuple[str, bool, str]] = []
    with sqlite3.connect(DATABASE) as connection:
        connection.row_factory = sqlite3.Row
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        checks.append(("Intégrité SQLite", integrity == "ok", integrity))
        meta = {
            row["key"]: row["value"]
            for row in connection.execute("SELECT key, value FROM meta")
        }
        counts = json.loads(meta.get("counts", "{}"))
        checks.append(("Version des données", meta.get("game_version") == "4.10.0", meta.get("game_version", "—")))
        checks.append(
            (
                "Vaisseaux achetables",
                counts.get("purchasable_vehicles", 0) >= 184,
                str(counts.get("purchasable_vehicles", 0)),
            )
        )
        checks.append(
            (
                "Objets achetables",
                counts.get("purchasable_items", 0) >= 2790,
                str(counts.get("purchasable_items", 0)),
            )
        )
        inactive = connection.execute(
            """
            SELECT COUNT(*) FROM (
                SELECT o.terminal_id FROM item_offers o
                JOIN terminals t ON t.id = o.terminal_id WHERE t.is_available_live <> 1
                UNION ALL
                SELECT o.terminal_id FROM vehicle_offers o
                JOIN terminals t ON t.id = o.terminal_id WHERE t.is_available_live <> 1
            )
            """
        ).fetchone()[0]
        checks.append(("Boutiques LIVE uniquement", inactive == 0, f"{inactive} offre(s) inactive(s)"))
        orphans = connection.execute(
            """
            SELECT
              (SELECT COUNT(*) FROM item_offers o LEFT JOIN items i ON i.id=o.item_id WHERE i.id IS NULL) +
              (SELECT COUNT(*) FROM vehicle_offers o LEFT JOIN vehicles v ON v.id=o.vehicle_id WHERE v.id IS NULL)
            """
        ).fetchone()[0]
        checks.append(("Références résolues", orphans == 0, f"{orphans} orpheline(s)"))
        additions = connection.execute(
            """
            SELECT COUNT(DISTINCT v.name)
            FROM vehicles v JOIN vehicle_offers o ON o.vehicle_id = v.id AND o.price_buy > 0
            WHERE v.name IN ('Aurora Mk II', 'Hull B', 'L-22 Alpha Wolf', 'Golem Ox', 'UTV')
            """
        ).fetchone()[0]
        checks.append(("Ajouts véhicules Alpha 4.10", additions == 5, f"{additions} / 5"))

    width = max(len(name) for name, _, _ in checks)
    print("ASTERIAX VERSE — VALIDATION DU CATALOGUE")
    print("=" * 48)
    for name, passed, detail in checks:
        print(f"{'OK' if passed else 'ERREUR':>6}  {name:<{width}}  {detail}")
    failures = [name for name, passed, _ in checks if not passed]
    if failures:
        print("\nValidation échouée : " + ", ".join(failures))
        return 1
    print("\nTous les contrôles sont validés.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
