"""Urdu speech.

P0 path: play a pre-generated WAV from assets/audio (docs/TECH_STACK.md §5).
Fallback: generate live with Kokoro — not wired up yet.

The staleness guard is the important part and it IS implemented: if a
message's text changed after its audio was generated, the screen and the
speaker would disagree, which is a medical-safety failure, not a cosmetic bug.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from ..config import settings


def text_checksum(urdu_text: str, kokoro_input: str) -> str:
    """Must match message_text_checksum() in db/migrations/002."""
    return hashlib.md5(f"{urdu_text or ''}||{kokoro_input or ''}".encode("utf-8")).hexdigest()


@dataclass
class AudioResolution:
    ok: bool
    url: str | None = None
    reason: str | None = None
    stale: bool = False
    missing_file: bool = False


def resolve_audio(
    *,
    code: str,
    urdu_text: str,
    kokoro_input: str,
    stored_checksum: str | None,
    asset_path: str | None,
) -> AudioResolution:
    if not asset_path:
        return AudioResolution(False, reason="No audio has been generated for this message.")

    expected = text_checksum(urdu_text, kokoro_input)
    if stored_checksum != expected:
        # I3 — never play audio that no longer matches the on-screen text.
        return AudioResolution(
            False,
            stale=True,
            reason="Audio is stale: the text changed after this audio was generated.",
        )

    full = settings.repo_root / asset_path
    if not full.exists():
        return AudioResolution(
            False,
            missing_file=True,
            reason=f"Audio file is registered but missing on disk: {asset_path}",
        )

    return AudioResolution(True, url=f"/api/speech/file/{code}")


def audio_file_path(asset_path: str) -> Path:
    return settings.repo_root / asset_path


# --------------------------------------------------------------- Kokoro adapter

class KokoroNotInstalled(RuntimeError):
    pass


def generate(text: str, out_path: Path, voice: str | None = None) -> Path:
    """Live generation fallback. Not wired up yet.

    When Kokoro is installed, implement here:
        from kokoro import KPipeline
        pipeline = KPipeline(lang_code=settings.kokoro_lang)   # 'h' = Hindi
        ...write 24 kHz mono WAV to out_path...

    Input must be the Devanagari `kokoro_input`, never the Urdu script.
    """
    raise KokoroNotInstalled(
        "Kokoro is not installed. P0 uses pre-generated audio in assets/audio; "
        "live generation is the fallback path and is not wired up yet."
    )


def is_available() -> bool:
    try:
        import kokoro  # noqa: F401
    except ImportError:
        return False
    return True
