"""Urdu speech endpoints.

Speech is only ever triggered by an explicit patient action (D010). This
router resolves and serves audio; it never decides to speak.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..db import get_db_optional
from ..services import snapshot, tts

router = APIRouter(prefix="/api/speech", tags=["speech"])


def _message_row(db: Session | None, code: str) -> dict | None:
    if db is None:
        return next((m for m in snapshot.load("messages.json") if m.get("code") == code), None)
    row = db.execute(
        text(
            "SELECT pm.code, pm.urdu_text, pm.kokoro_input, pm.audio_source_checksum, "
            "       a.path AS audio_path "
            "FROM patient_messages pm "
            "LEFT JOIN assets a ON a.id = pm.audio_asset_id "
            "WHERE pm.code = :code AND pm.is_enabled"
        ),
        {"code": code},
    ).first()
    return dict(row._mapping) if row else None


@router.get("/resolve/{code}")
def resolve(code: str, db: Session | None = Depends(get_db_optional)):
    """Can this message be spoken, and if not, exactly why?"""
    row = _message_row(db, code)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"No enabled message '{code}'")

    if db is None:
        # The snapshot is pre-filtered through the invariants.
        ok = bool(row.get("audio_ok")) and bool(row.get("audio_path"))
        return {
            "ok": ok,
            "url": f"/api/speech/file/{code}" if ok else None,
            "reason": None if ok else "Audio unavailable in snapshot mode.",
        }

    result = tts.resolve_audio(
        code=code,
        urdu_text=row["urdu_text"],
        kokoro_input=row["kokoro_input"],
        stored_checksum=row["audio_source_checksum"],
        asset_path=row["audio_path"],
    )
    return {
        "ok": result.ok,
        "url": result.url,
        "reason": result.reason,
        "stale": result.stale,
        "missing_file": result.missing_file,
    }


@router.get("/file/{code}")
def audio_file(code: str, db: Session | None = Depends(get_db_optional)):
    row = _message_row(db, code)
    if not row or not row.get("audio_path"):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No audio for this message")

    if db is not None:
        result = tts.resolve_audio(
            code=code,
            urdu_text=row["urdu_text"],
            kokoro_input=row["kokoro_input"],
            stored_checksum=row["audio_source_checksum"],
            asset_path=row["audio_path"],
        )
        if not result.ok:
            # I3 — never serve audio that no longer matches the on-screen text.
            raise HTTPException(status.HTTP_409_CONFLICT, result.reason or "Audio unavailable")

    path = tts.audio_file_path(row["audio_path"])
    if not path.exists():
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            f"Audio file missing on disk: {row['audio_path']}. "
            "Pre-generate the P0 audio set before the demo.",
        )
    return FileResponse(path, media_type="audio/wav")


@router.get("/status")
def speech_status():
    return {
        "primary": "pre-generated WAV",
        "fallback": "live Kokoro generation",
        "kokoro_installed": tts.is_available(),
        "note": "P0 plays pre-generated audio from assets/audio. Live generation "
                "is the fallback path and is not wired up yet.",
    }
