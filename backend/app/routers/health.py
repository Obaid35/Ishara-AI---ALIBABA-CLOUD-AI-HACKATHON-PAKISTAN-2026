"""Health and degraded-mode reporting.

The frontend uses this to decide whether to show the degraded-mode indicator.
Silent degradation during a judged demo is worse than a visible one.
"""

from __future__ import annotations

from fastapi import APIRouter

from ..db import db_state
from ..services import snapshot
from ..services.recognition import is_stub
from ..services.stt import provider_status
from ..services.tts import is_available as kokoro_available

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health():
    db_ok = db_state.available or db_state.probe()
    stt = provider_status()

    degradations = []
    if not db_ok:
        degradations.append("Running on the JSON snapshot — content is read-only.")
    if is_stub():
        degradations.append("Recognition engine is a STUB — results are simulated.")
    if not kokoro_available():
        degradations.append("Kokoro is not installed — live speech generation is unavailable.")
    if not stt["any_available"]:
        degradations.append("Speech-to-text is unavailable — use the phrase buttons.")

    return {
        "status": "ok",
        "database": {
            "mode": db_state.mode,
            "available": db_ok,
            "error": db_state.last_error,
        },
        "snapshot": snapshot.info(),
        "recognition": {"engine": "stub" if is_stub() else "live", "is_stub": is_stub()},
        "speech": {
            "primary": "pre-generated WAV",
            "kokoro_installed": kokoro_available(),
        },
        "stt": stt,
        "degradations": degradations,
        "internet_required": False,
    }
