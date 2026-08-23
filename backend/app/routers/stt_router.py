"""Doctor voice input (P1).

Speech only SELECTS a verified phrase; it never generates PSL. The matched
phrase is returned for confirmation — the client must not auto-play it (D029).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..db import get_db_optional
from ..services import snapshot
from ..services.stt import (
    PhraseCandidate,
    TranscriptionUnavailable,
    match_phrase,
    provider_status,
    transcribe,
)

router = APIRouter(prefix="/api/stt", tags=["stt"])


class MatchRequest(BaseModel):
    transcript: str


def _phrases(db: Session | None) -> list[PhraseCandidate]:
    if db is None:
        rows = snapshot.load("doctor_phrases.json")
    else:
        rows = [
            dict(r._mapping)
            for r in db.execute(
                text(
                    "SELECT dp.code, dp.urdu_text, dp.english_text, dp.stt_aliases "
                    "FROM doctor_phrases dp WHERE dp.is_enabled"
                )
            )
        ]
    return [
        PhraseCandidate(
            code=r["code"],
            urdu_text=r.get("urdu_text", ""),
            english_text=r.get("english_text", ""),
            aliases=list(r.get("stt_aliases") or []),
        )
        for r in rows
    ]


@router.get("/status")
def status_endpoint():
    return provider_status() | {
        "transcription_wired": False,
        "note": "Doctor voice input is P1 and not wired up yet. The phrase "
                "buttons remain fully functional.",
    }


@router.post("/match")
def match(payload: MatchRequest, db: Session | None = Depends(get_db_optional)):
    """Match an already-obtained transcript against the verified phrase list.

    Usable today: paste or type a transcript and see which verified phrase it
    selects. This is the safety-critical half of the feature and it is real.
    """
    result = match_phrase(payload.transcript, _phrases(db))
    return {
        "matched": result.matched,
        "code": result.code,
        "score": result.score,
        "transcript": result.transcript,
        "reason": result.reason,
        "requires_confirmation": True,
    }


@router.post("/transcribe")
async def transcribe_endpoint(
    audio: UploadFile = File(...), db: Session | None = Depends(get_db_optional)
):
    try:
        transcript = transcribe(await audio.read(), audio.filename or "audio.webm")
    except TranscriptionUnavailable as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc

    result = match_phrase(transcript, _phrases(db))
    return {
        "transcript": transcript,
        "matched": result.matched,
        "code": result.code,
        "score": result.score,
        "reason": result.reason,
        "requires_confirmation": True,
    }
