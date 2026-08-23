"""Generate the pre-generated Urdu audio set.

    python scripts/generate_audio.py --placeholder   # tones, no Kokoro needed
    python scripts/generate_audio.py                 # real Kokoro generation

P0 speech is pre-generated before the demo and played from disk
(docs/TECH_STACK.md §5). This script is what produces assets/audio/*.wav and
records the checksum that guards against the text and the audio drifting apart.

The Kokoro path is not wired up yet — see the `synthesize` function below.
Placeholder mode exists so the whole speech pipeline can be exercised now; the
files it writes are tones, are registered as placeholders, and must never be
presented as Urdu speech.
"""

from __future__ import annotations

import argparse
import hashlib
import math
import struct
import sys
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select, text  # noqa: E402

from app.config import settings  # noqa: E402
from app.db import SessionLocal  # noqa: E402
from app.models import Asset, AssetRights, PatientMessage  # noqa: E402

SAMPLE_RATE = 24_000


def checksum(urdu: str, kokoro: str) -> str:
    return hashlib.md5(f"{urdu or ''}||{kokoro or ''}".encode("utf-8")).hexdigest()


def write_placeholder_wav(path: Path, seed_text: str) -> None:
    """A short two-tone chime. Distinct per message, obviously not speech."""
    path.parent.mkdir(parents=True, exist_ok=True)
    base = 320 + (sum(ord(c) for c in seed_text) % 6) * 40
    frames = bytearray()
    for index, (freq, ms) in enumerate(((base, 140), (base * 1.5, 180))):
        count = int(SAMPLE_RATE * ms / 1000)
        for n in range(count):
            # Fade in/out so it does not click.
            envelope = min(1.0, n / 400, (count - n) / 400) * 0.25
            sample = int(32767 * envelope * math.sin(2 * math.pi * freq * n / SAMPLE_RATE))
            frames += struct.pack("<h", sample)
        if index == 0:
            frames += b"\x00\x00" * int(SAMPLE_RATE * 0.04)

    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(SAMPLE_RATE)
        handle.writeframes(bytes(frames))


def synthesize(kokoro_input: str, path: Path, voice: str) -> None:
    """Real generation. Not wired up yet.

        from kokoro import KPipeline
        pipeline = KPipeline(lang_code=settings.kokoro_lang)   # 'h' = Hindi
        for _, _, audio in pipeline(kokoro_input, voice=voice):
            ...write 24 kHz mono WAV to path...

    Input is the Devanagari `kokoro_input`, never the Urdu script.
    """
    raise SystemExit(
        "Kokoro is not installed or not wired up yet.\n"
        "Run with --placeholder to exercise the pipeline, or install Kokoro and\n"
        "implement synthesize() in this file."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate pre-generated Urdu audio.")
    parser.add_argument("--placeholder", action="store_true",
                        help="Write tone placeholders instead of speech.")
    parser.add_argument("--only", help="Generate a single message code.")
    parser.add_argument("--p0-only", action="store_true", help="Only P0 messages.")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        query = select(PatientMessage)
        if args.p0_only:
            query = query.where(PatientMessage.priority == "p0")
        if args.only:
            query = query.where(PatientMessage.code == args.only)
        messages = db.scalars(query).all()

        if not messages:
            print("No matching messages.")
            return

        voice = settings.kokoro_voice
        if not args.placeholder and not voice:
            raise SystemExit(
                "KOKORO_VOICE is not set in .env. Choose it with the Day-1 blind "
                "listening test across hf_alpha, hf_beta, hm_omega, hm_psi."
            )

        written = 0
        for message in messages:
            rel = f"assets/audio/{message.code.lower()}.wav"
            path = settings.repo_root / rel

            if args.placeholder:
                write_placeholder_wav(path, message.code)
            else:
                synthesize(message.kokoro_input, path, voice)

            asset = db.scalar(select(Asset).where(Asset.path == rel))
            if not asset:
                asset = Asset(kind="audio_wav", path=rel)
                db.add(asset)
                db.flush()
                db.add(
                    AssetRights(
                        asset_id=asset.id,
                        source_name="PLACEHOLDER tone" if args.placeholder else "Generated with Kokoro",
                        permission_status="own_recording",
                        permitted_development=True,
                        permitted_internal_testing=True,
                        permitted_demo_playback=True,
                    )
                )
            asset.bytes = path.stat().st_size

            message.audio_asset_id = asset.id
            # This is what stops the screen and the speaker ever disagreeing.
            message.audio_source_checksum = checksum(message.urdu_text, message.kokoro_input)
            written += 1
            print(f"  + {rel}")

        db.commit()
        kind = "placeholder tone" if args.placeholder else "Kokoro"
        print(f"\n{written} files written ({kind}).")
        if args.placeholder:
            print(
                "\n  WARNING: these are TONES, not Urdu speech. They exist so the\n"
                "  pipeline can be exercised. Replace with real Kokoro output before\n"
                "  any demo, and verify each one BY EAR with an Urdu speaker."
            )
    finally:
        db.close()


if __name__ == "__main__":
    main()
