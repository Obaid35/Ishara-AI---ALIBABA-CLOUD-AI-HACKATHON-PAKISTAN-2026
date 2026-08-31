"""Public content endpoints.

These are reachable WITHOUT authentication — the communication screen must
work for a patient who has no account (D018).

All read paths fall back to the JSON snapshot when PostgreSQL is unavailable.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..db import db_state, get_db_optional
from ..services import snapshot

router = APIRouter(prefix="/api", tags=["content"])


class ResolveRequest(BaseModel):
    concepts: list[str]


@router.get("/signs")
def list_signs(db: Session | None = Depends(get_db_optional)):
    """The production vocabulary — the only sign list quoted publicly."""
    if db is None:
        return {"source": "snapshot", "signs": snapshot.load("signs.json")}
    rows = db.execute(
        text(
            "SELECT code, urdu_meaning, english_meaning, is_demo_critical "
            "FROM v_production_vocabulary ORDER BY code"
        )
    )
    return {"source": "database", "signs": [dict(r._mapping) for r in rows]}


@router.get("/messages")
def list_messages(db: Session | None = Depends(get_db_optional)):
    if db is None:
        return {"source": "snapshot", "messages": snapshot.load("messages.json")}
    rows = db.execute(
        text(
            "SELECT code, urdu_text, english_text, priority, is_demo_critical, "
            "       audio_path, audio_ok, concept_sequence "
            "FROM v_demoable_messages ORDER BY code"
        )
    )
    return {"source": "database", "messages": [dict(r._mapping) for r in rows]}


@router.post("/messages/resolve")
def resolve_message(payload: ResolveRequest, db: Session | None = Depends(get_db_optional)):
    """Map a recognised concept sequence to a controlled Urdu message.

    Deterministic lookup — no LLM (D022). If the sequence has no template we
    return the recognised concepts and the base message for the first concept,
    rather than inventing a sentence.
    """
    wanted = " + ".join(payload.concepts)

    if db is None:
        messages = snapshot.load("messages.json")
        exact = next((m for m in messages if m.get("concept_sequence") == wanted), None)
        base = next(
            (m for m in messages if m.get("concept_sequence") == (payload.concepts[0] if payload.concepts else "")),
            None,
        )
        source = "snapshot"
    else:
        rows = [
            dict(r._mapping)
            for r in db.execute(
                text(
                    "SELECT code, urdu_text, english_text, audio_path, audio_ok, "
                    "       concept_sequence FROM v_demoable_messages"
                )
            )
        ]
        exact = next((m for m in rows if m["concept_sequence"] == wanted), None)
        base = next(
            (m for m in rows if m["concept_sequence"] == (payload.concepts[0] if payload.concepts else "")),
            None,
        )
        source = "database"

    if exact:
        return {"source": source, "matched": "exact", "concepts": payload.concepts, "message": exact}
    if base:
        return {
            "source": source,
            "matched": "base",
            "concepts": payload.concepts,
            "message": base,
            "note": "No template for this exact sequence — showing the base message. "
                    "The extra concepts are displayed but not spoken.",
        }
    return {
        "source": source,
        "matched": "none",
        "concepts": payload.concepts,
        "message": None,
        "note": "No supported message for these concepts.",
    }


@router.get("/doctor-phrases")
def list_doctor_phrases(db: Session | None = Depends(get_db_optional)):
    """Enabled phrases grouped by category."""
    if db is None:
        rows = snapshot.load("doctor_phrases.json")
        source = "snapshot"
    else:
        rows = [
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
        source = "database"

    grouped: dict[str, dict] = {}
    for row in rows:
        code = row.get("category_code") or "other"
        grouped.setdefault(
            code,
            {
                "code": code,
                "name_en": row.get("category_name_en") or "Other",
                "name_ur": row.get("category_name_ur") or "دیگر",
                "sort_order": row.get("category_sort_order") or 99,
                "phrases": [],
            },
        )["phrases"].append(row)

    categories = sorted(grouped.values(), key=lambda c: c["sort_order"])
    return {"source": source, "categories": categories}


@router.get("/reference-clips")
def reference_clips():
    """Where each sign's reference performance sits inside its source video.

    The trimmed clips written by the extractor use an OpenCV codec browsers do
    not decode, so rather than re-encode we point at the ORIGINAL dictionary
    video (H.264) and let the player show only the relevant range.
    """
    import json

    from ..config import settings

    report = settings.repo_root / "experiments" / "day1" / "extraction_report.json"
    if not report.exists():
        return {"clips": {}}

    try:
        data = json.loads(report.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"clips": {}}

    clips: dict[str, dict] = {}
    for entry in data.get("signs", []):
        samples = entry.get("samples") or []
        code, source = entry.get("code"), entry.get("source")
        if not code or not source or not samples:
            continue
        first = samples[0]
        clips[code] = {
            "video": f"/media/psl-videos/{source}",
            "start_s": first.get("start_s"),
            "end_s": first.get("end_s"),
            "samples": len(samples),
        }
    return {"clips": clips}
