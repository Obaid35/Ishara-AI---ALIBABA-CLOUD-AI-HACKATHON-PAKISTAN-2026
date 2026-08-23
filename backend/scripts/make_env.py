"""Generate .env from .env.example.

    python scripts/make_env.py --db-password "..." [--admin-password "..."]

Kept as a script rather than an inline one-liner in setup.bat because the
password needs real handling: it goes into DATABASE_URL as a URL component, so
characters like @ : / # ? must be percent-encoded there while staying literal
in POSTGRES_PASSWORD. Getting that wrong produces a .env that looks fine and
fails with a confusing parse error.

Never prints the password. Never overwrites an existing .env.
"""

from __future__ import annotations

import argparse
import secrets
import sys
from pathlib import Path
from urllib.parse import quote

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = REPO_ROOT / ".env.example"
TARGET = REPO_ROOT / ".env"


def build(db_password: str, admin_password: str, db_user: str = "postgres") -> str:
    text = EXAMPLE.read_text(encoding="utf-8")

    # Literal in the discrete field...
    text = text.replace("POSTGRES_PASSWORD=change_me", f"POSTGRES_PASSWORD={db_password}")

    # ...but percent-encoded inside the URL. A password of "p@ss:word" would
    # otherwise make DATABASE_URL unparseable.
    encoded = quote(db_password, safe="")
    text = text.replace(
        f"{db_user}:change_me@",
        f"{db_user}:{encoded}@",
    )

    text = text.replace("JWT_SECRET=change_me", f"JWT_SECRET={secrets.token_urlsafe(48)}")
    text = text.replace(
        "SEED_ADMIN_PASSWORD=change_me", f"SEED_ADMIN_PASSWORD={admin_password}"
    )
    return text


def verify(text: str) -> list[str]:
    """Catch a malformed result before it becomes a confusing runtime error."""
    problems: list[str] = []
    values = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip()

    url = values.get("DATABASE_URL", "")
    if not url.startswith("postgresql://"):
        problems.append("DATABASE_URL does not start with postgresql://")
    elif "@" not in url:
        problems.append("DATABASE_URL has no host section - the password may contain a newline")
    else:
        tail = url.rsplit("@", 1)[1]
        if "/" not in tail or ":" not in tail:
            problems.append(f"DATABASE_URL host section looks wrong: {tail}")

    for key in ("POSTGRES_PASSWORD", "JWT_SECRET", "SEED_ADMIN_PASSWORD"):
        if not values.get(key):
            problems.append(f"{key} is empty")
        elif values[key] == "change_me":
            problems.append(f"{key} was not replaced")

    return problems


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-password", required=True)
    parser.add_argument("--admin-password", default="admin123")
    parser.add_argument("--db-user", default="postgres")
    parser.add_argument("--force", action="store_true", help="overwrite an existing .env")
    args = parser.parse_args()

    if TARGET.exists() and not args.force:
        print("  .env already exists - leaving it untouched")
        return 0

    if not EXAMPLE.exists():
        print(f"  [X] {EXAMPLE.name} is missing", file=sys.stderr)
        return 1

    # Guard against the classic piped-input failure, where set /p swallows
    # several lines at once and the password silently contains newlines.
    db_password = args.db_password
    admin_password = args.admin_password or "admin123"
    if "\n" in db_password or "\r" in db_password:
        print(
            "  [X] The password contains a line break. If you piped input to setup.bat,\n"
            "      use CRLF line endings, or pass --db-password directly.",
            file=sys.stderr,
        )
        return 1
    if not db_password.strip():
        print("  [X] The database password is empty", file=sys.stderr)
        return 1

    text = build(db_password, admin_password, args.db_user)

    problems = verify(text)
    if problems:
        print("  [X] Generated .env failed validation:", file=sys.stderr)
        for item in problems:
            print(f"      - {item}", file=sys.stderr)
        return 1

    TARGET.write_text(text, encoding="utf-8")
    print("  [ok] .env created (gitignored - never commit it)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
