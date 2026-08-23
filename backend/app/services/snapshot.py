"""JSON snapshot export and load.

PostgreSQL is a demo dependency, so it gets a fallback like everything else
(D021). The export is filtered through the content invariants, so unverified
or unpermitted content cannot leak into the fallback path.

Snapshot mode is read-only: recognition, messages, audio and doctor playback
work; admin editing and test recording require the live database.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from ..config import settings

FILES = ("signs.json", "messages.json", "doctor_phrases.json", "meta.json")


def snapshot_dir() -> Path:
    return settings.snapshot_dir


def export(db: Session) -> dict[str, int]:
    out = snapshot_dir()
    out.mkdir(parents=True, exist_ok=True)

    signs = [
        dict(r._mapping)
        for r in db.execute(
            text(
                "SELECT code, urdu_meaning, english_meaning, is_demo_critical "
                "FROM v_production_vocabulary ORDER BY code"
            )
        )
    ]

    messages = [
        dict(r._mapping)
        for r in db.execute(
            text(
                "SELECT code, urdu_text, english_text, priority, is_demo_critical, "
                "       audio_path, audio_ok, concept_sequence "
                "FROM v_demoable_messages ORDER BY code"
            )
        )
    ]

    phrases = [
        dict(r._mapping)
        for r in db.execute(
            text(
                "SELECT code, urdu_text, english_text, priority, is_demo_critical, "
                "       sort_order, category_code, category_name_en, category_name_ur, "
                "       category_sort_order, video_path "
                "FROM v_demoable_doctor_phrases "
                "ORDER BY category_sort_order, sort_order"
            )
        )
    ]

    meta = {
        "exported_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "signs": len(signs),
        "messages": len(messages),
        "doctor_phrases": len(phrases),
        "note": "Read-only demo fallback. Contains only enabled, demoable content. "
                "No users, participants, consents or audit entries.",
    }

    _write(out / "signs.json", signs)
    _write(out / "messages.json", messages)
    _write(out / "doctor_phrases.json", phrases)
    _write(out / "meta.json", meta)

    return {"signs": len(signs), "messages": len(messages), "doctor_phrases": len(phrases)}


def _write(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def load(name: str) -> Any:
    path = snapshot_dir() / name
    if not path.exists():
        return [] if name != "meta.json" else {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return [] if name != "meta.json" else {}


def available() -> bool:
    return (snapshot_dir() / "messages.json").exists()


def info() -> dict:
    meta = load("meta.json") or {}
    return {
        "available": available(),
        "exported_at": meta.get("exported_at"),
        "counts": {
            "signs": meta.get("signs", 0),
            "messages": meta.get("messages", 0),
            "doctor_phrases": meta.get("doctor_phrases", 0),
        },
    }
