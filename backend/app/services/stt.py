"""Doctor voice input (P1).

Transcription is not wired up yet. Phrase matching IS implemented and is the
part that carries the safety property: transcribed speech is matched against
a CLOSED list of already-verified phrases. The system never generates PSL —
speech only selects an existing verified question, and the doctor confirms
the match before the video plays (D029).

Fallback chain (docs/TECH_STACK.md §9):
    Groq whisper-large-v3-turbo -> Groq whisper-large-v3
                                -> local faster-whisper small int8
                                -> manual phrase buttons (always available)
"""

from __future__ import annotations

import difflib
import re
import unicodedata
from dataclasses import dataclass

from ..config import settings

# Below this, nothing plays and the doctor uses the buttons. Rejecting is
# always safer than selecting the nearest phrase regardless of distance.
MATCH_THRESHOLD = 0.62


@dataclass
class PhraseCandidate:
    code: str
    urdu_text: str
    english_text: str
    aliases: list[str]


@dataclass
class MatchResult:
    matched: bool
    code: str | None = None
    score: float = 0.0
    transcript: str = ""
    reason: str | None = None


_PUNCT = re.compile(r"[^\w\s؀-ۿ]", re.UNICODE)


def normalise(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "").strip().lower()
    value = _PUNCT.sub(" ", value)
    return re.sub(r"\s+", " ", value)


def match_phrase(transcript: str, phrases: list[PhraseCandidate]) -> MatchResult:
    """Match a transcript against the closed, verified phrase list."""
    target = normalise(transcript)
    if not target:
        return MatchResult(False, transcript=transcript, reason="Empty transcription")

    best_code: str | None = None
    best_score = 0.0

    for phrase in phrases:
        options = [phrase.urdu_text, phrase.english_text, *(phrase.aliases or [])]
        for option in options:
            candidate = normalise(option)
            if not candidate:
                continue
            score = difflib.SequenceMatcher(None, target, candidate).ratio()
            # Containment is a strong signal for short spoken questions.
            if candidate and candidate in target:
                score = max(score, 0.90)
            if score > best_score:
                best_score, best_code = score, phrase.code

    if best_score < MATCH_THRESHOLD:
        return MatchResult(
            False,
            score=round(best_score, 3),
            transcript=transcript,
            reason="No verified phrase matched confidently. Please use the buttons.",
        )

    return MatchResult(True, code=best_code, score=round(best_score, 3), transcript=transcript)


# --------------------------------------------------------------- transcription adapters

class TranscriptionUnavailable(RuntimeError):
    pass


def provider_status() -> dict:
    return {
        "groq_configured": bool(settings.groq_api_key),
        "groq_model": settings.groq_stt_model,
        "local_model": settings.local_stt_model,
        "local_available": _local_available(),
        "any_available": bool(settings.groq_api_key) or _local_available(),
        "fallback": "manual phrase buttons are always available",
    }


def _local_available() -> bool:
    try:
        import faster_whisper  # noqa: F401
    except ImportError:
        return False
    return True


def transcribe(audio_bytes: bytes, filename: str = "audio.webm") -> str:
    """Not wired up yet.

    Groq path:  client.audio.transcriptions.create(model=settings.groq_stt_model, ...)
    Local path: WhisperModel(settings.local_stt_model, device="cpu",
                             compute_type=settings.local_stt_compute)
    """
    raise TranscriptionUnavailable(
        "Speech-to-text is not wired up yet. Doctor voice input is P1; "
        "the phrase buttons remain fully functional."
    )
