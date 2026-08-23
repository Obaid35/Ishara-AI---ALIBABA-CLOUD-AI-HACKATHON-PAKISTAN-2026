"""Minimal migration runner.

    python -m app.migrate           # apply pending migrations
    python -m app.migrate --status  # list applied / pending
    python -m app.migrate --reset   # DROP the schema and reapply (dev only)

Migrations are plain SQL in db/migrations, applied in filename order and never
edited after being applied.
"""

from __future__ import annotations

import argparse
import sys

from sqlalchemy import text

from .config import settings
from .db import engine

MIGRATIONS_DIR = settings.repo_root / "db" / "migrations"

_TRACKING_TABLE = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    filename   text PRIMARY KEY,
    applied_at timestamptz NOT NULL DEFAULT now()
);
"""


def _files() -> list:
    if not MIGRATIONS_DIR.exists():
        return []
    return sorted(MIGRATIONS_DIR.glob("*.sql"))


def _applied(conn) -> set[str]:
    conn.execute(text(_TRACKING_TABLE))
    rows = conn.execute(text("SELECT filename FROM schema_migrations")).fetchall()
    return {r[0] for r in rows}


def status() -> None:
    with engine.begin() as conn:
        done = _applied(conn)
    for path in _files():
        mark = "applied" if path.name in done else "PENDING"
        print(f"  [{mark:>7}] {path.name}")


def migrate() -> None:
    files = _files()
    if not files:
        print("No migration files found.")
        return
    with engine.begin() as conn:
        done = _applied(conn)
    for path in files:
        if path.name in done:
            print(f"  = {path.name} (already applied)")
            continue
        sql = path.read_text(encoding="utf-8")
        print(f"  + applying {path.name} ...", end=" ")
        # Executed through a raw DBAPI cursor with no parameters. SQLAlchemy
        # would hand psycopg2 an empty parameter set, and psycopg2 then treats
        # every '%' as a placeholder — which breaks the '%' format specifiers
        # in the PL/pgSQL RAISE statements that carry our invariant messages.
        raw = engine.raw_connection()
        try:
            cursor = raw.cursor()
            cursor.execute(_TRACKING_TABLE)
            cursor.execute(sql)
            cursor.execute("INSERT INTO schema_migrations (filename) VALUES (%s)", (path.name,))
            raw.commit()
        except Exception:
            raw.rollback()
            raise
        finally:
            raw.close()
        print("ok")


def reset() -> None:
    print("Dropping and recreating the public schema (development only)...")
    with engine.begin() as conn:
        conn.exec_driver_sql("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
    migrate()


def main() -> None:
    parser = argparse.ArgumentParser(description="PSL Bridge migrations")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--reset", action="store_true", help="DESTRUCTIVE: drops all data")
    args = parser.parse_args()

    try:
        if args.status:
            status()
        elif args.reset:
            reset()
        else:
            migrate()
    except Exception as exc:  # noqa: BLE001
        print(f"\nMigration failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
