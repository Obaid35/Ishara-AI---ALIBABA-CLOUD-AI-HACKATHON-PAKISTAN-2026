"""Backend preflight checks.

Run before starting the app to catch the things that otherwise fail silently
or produce a confusing half-working demo.

Exit codes:
    0  everything ready
    1  fatal - the app cannot usefully start
    2  ready, but with warnings worth seeing

Usage:
    python scripts/preflight.py
    python scripts/preflight.py --quiet     only problems
"""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

OK, WARN, FAIL = "[ok]", "[!!]", "[X]"

problems: list[str] = []
warnings: list[str] = []


def say(mark: str, text: str, quiet: bool) -> None:
    if quiet and mark == OK:
        return
    print(f"  {mark} {text}")


def fatal(text: str, fix: str) -> None:
    problems.append(f"{text}\n       fix: {fix}")


def warn(text: str, fix: str) -> None:
    warnings.append(f"{text}\n       fix: {fix}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    q = args.quiet

    # ------------------------------------------------------ python packages
    required = {
        "fastapi": "fastapi",
        "uvicorn": "uvicorn",
        "sqlalchemy": "sqlalchemy",
        "psycopg2": "psycopg2-binary",
        "pydantic": "pydantic",
        "jwt": "PyJWT",
        "bcrypt": "bcrypt",
        "dotenv": "python-dotenv",
        "email_validator": "email-validator",
    }
    missing = []
    for module, package in required.items():
        try:
            importlib.import_module(module)
        except ImportError:
            missing.append(package)

    if missing:
        say(FAIL, f"Python packages missing: {', '.join(missing)}", q)
        fatal(
            f"Python packages missing: {', '.join(missing)}",
            "cd backend && python -m pip install -r requirements.txt   (or run setup.bat)",
        )
        # Without these nothing else can be checked.
        return report()
    say(OK, f"Python packages installed ({len(required)})", q)

    # ------------------------------------------------------ configuration
    from app.config import settings  # noqa: E402

    env_path = settings.repo_root / ".env"
    if not env_path.exists():
        say(FAIL, ".env is missing", q)
        fatal(".env is missing", "copy .env.example to .env and fill in local values")
        return report()
    say(OK, ".env present", q)

    if settings.jwt_secret in ("", "change_me"):
        say(WARN, "JWT_SECRET is still the example value", q)
        warn(
            "JWT_SECRET is still the example value",
            'set a real one: python -c "import secrets; print(secrets.token_urlsafe(48))"',
        )

    # ------------------------------------------------------ database
    from app.db import SessionLocal, db_state  # noqa: E402
    from sqlalchemy import text  # noqa: E402

    if not db_state.probe():
        say(WARN, f"PostgreSQL unreachable - {db_state.last_error}", q)
        from app.services import snapshot  # noqa: E402

        if snapshot.available():
            info = snapshot.info()
            say(OK, f"Snapshot fallback present (exported {info['exported_at']})", q)
            warn(
                "PostgreSQL unreachable - starting in read-only SNAPSHOT mode",
                "start the PostgreSQL service to enable admin editing",
            )
            return report()
        fatal(
            "PostgreSQL unreachable and no snapshot exists",
            "start PostgreSQL, or run setup.bat to create and seed the database",
        )
        return report()
    say(OK, "PostgreSQL reachable", q)

    db = SessionLocal()
    try:
        # -------------------------------------------------- migrations
        applied = db.execute(
            text(
                "SELECT count(*) FROM information_schema.tables "
                "WHERE table_name = 'schema_migrations'"
            )
        ).scalar()
        if not applied:
            say(FAIL, "Migrations have never been applied", q)
            fatal(
                "Migrations have never been applied",
                "cd backend && python -m app.migrate",
            )
            return report()

        done = {r[0] for r in db.execute(text("SELECT filename FROM schema_migrations"))}
        on_disk = {p.name for p in (settings.repo_root / "db" / "migrations").glob("*.sql")}
        pending = sorted(on_disk - done)
        if pending:
            say(FAIL, f"Pending migrations: {', '.join(pending)}", q)
            fatal(
                f"Pending migrations: {', '.join(pending)}",
                "cd backend && python -m app.migrate",
            )
            return report()
        say(OK, f"Migrations applied ({len(done)})", q)

        # -------------------------------------------------- content
        signs = db.execute(text("SELECT count(*) FROM v_production_vocabulary")).scalar() or 0
        messages = db.execute(text("SELECT count(*) FROM v_demoable_messages")).scalar() or 0
        phrases = db.execute(text("SELECT count(*) FROM v_demoable_doctor_phrases")).scalar() or 0
        users = db.execute(text("SELECT count(*) FROM users WHERE is_active")).scalar() or 0

        if users == 0:
            say(FAIL, "No active user accounts", q)
            fatal("No active user accounts", "cd backend && python -m app.seed")
        else:
            say(OK, f"{users} active user account(s)", q)

        if signs == 0:
            say(WARN, "No signs are Reliable + Enabled - the vocabulary is empty", q)
            warn(
                "No signs are Reliable + Enabled - nothing can be recognised",
                "run: python -m app.seed --dev-content   (or enable signs in /admin/signs)",
            )
        else:
            say(OK, f"{signs} reliable signs, {messages} messages, {phrases} doctor phrases", q)

        # -------------------------------------------------- audio
        stale = db.execute(
            text(
                "SELECT count(*) FROM patient_messages pm WHERE pm.audio_asset_id IS NOT NULL "
                "AND pm.audio_source_checksum IS DISTINCT FROM "
                "message_text_checksum(pm.urdu_text, pm.kokoro_input)"
            )
        ).scalar() or 0
        if stale:
            say(WARN, f"{stale} message(s) have stale audio - playback is blocked", q)
            warn(
                f"{stale} message(s) have stale audio",
                "cd backend && python scripts/generate_audio.py --placeholder",
            )

        registered = [
            r[0]
            for r in db.execute(
                text(
                    "SELECT a.path FROM patient_messages pm "
                    "JOIN assets a ON a.id = pm.audio_asset_id WHERE pm.is_enabled"
                )
            )
        ]
        absent = [p for p in registered if not (settings.repo_root / p).exists()]
        if absent:
            say(WARN, f"{len(absent)} audio file(s) registered but missing on disk", q)
            warn(
                f"{len(absent)} audio file(s) missing on disk",
                "cd backend && python scripts/generate_audio.py --placeholder",
            )
        elif registered and not stale:
            say(OK, f"{len(registered)} audio files present and current", q)

        # -------------------------------------------------- demo readiness
        blockers = db.execute(text("SELECT count(*) FROM v_demo_readiness")).scalar() or 0
        gaps = db.execute(text("SELECT count(*) FROM v_permission_gaps")).scalar() or 0
        if blockers:
            say(WARN, f"{blockers} demo-critical item(s) not ready - see /admin", q)
        if gaps:
            say(WARN, f"{gaps} asset(s) in use without settled rights - see /admin/assets", q)
        if not blockers and not gaps:
            say(OK, "Demo readiness clear, no permission gaps", q)

    finally:
        db.close()

    return report()


def report() -> int:
    if problems:
        print()
        print("  Cannot start:")
        for item in problems:
            print(f"    - {item}")
        return 1
    if warnings:
        print()
        print("  Warnings:")
        for item in warnings:
            print(f"    - {item}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
