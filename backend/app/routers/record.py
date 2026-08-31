"""Record your own reference samples.

The Day-1 experiment showed dictionary clips do not transfer to a different
signer: only 2 of 8 live attempts had the correct sign nearest, and the
correct/wrong distance ranges overlapped, so no threshold could separate them.
The fix is data, not code -- references performed by the people who will
actually use it (docs/DATA_STRATEGY.md, Source 3).

Boundaries are MANUAL here. Auto-segmentation guesses where a sign starts from
a motion threshold; when recording a template the person knows exactly, and a
wrong boundary poisons every future match against that reference. Leading and
trailing stillness is trimmed automatically so the edges still look like what
live capture produces.

Protocol (client -> server)
    {"type": "start"}                       begin a take
    binary   4-byte LE timestamp + JPEG     frames, same as recognition
    {"type": "stop"}                        end the take, get its stats back
    {"type": "keep", "sign_code": "...", "participant_code": "..."}
    {"type": "discard"}

Server -> client
    {"type": "ready" | "recording" | "captured" | "saved" | "error", ...}
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import re

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select, text

from ..config import settings
from ..db import SessionLocal
from ..models import Sign, SignReference, TestParticipant
from .recognize import FrameProcessor

log = logging.getLogger("ishara.record")
router = APIRouter(tags=["recording"])

# A take shorter than this is a slip, not a sign.
MIN_TAKE_S = 0.4
MAX_TAKE_S = 8.0
# Stillness below this is trimmed from the head and tail of a take.
TRIM_MOTION = 0.010
SAFE_CODE = re.compile(r"^[A-Z0-9_]{1,40}$")


def reference_dir():
    return settings.repo_root / "experiments" / "day1" / "references"


def _trim(motions: list[float], start: int, end: int) -> tuple[int, int]:
    """Drop leading and trailing stillness, keeping the movement itself."""
    lo, hi = start, end
    while lo < hi - 4 and motions[lo] < TRIM_MOTION:
        lo += 1
    while hi > lo + 4 and motions[hi - 1] < TRIM_MOTION:
        hi -= 1
    return lo, hi


@router.websocket("/ws/record")
async def record(ws: WebSocket) -> None:
    await ws.accept()

    processor = FrameProcessor()
    error = processor.start()

    await ws.send_json({
        "type": "ready",
        "landmarks": processor.available,
        "reason": error,
    })
    if not processor.available:
        await ws.close()
        return

    recording = False
    start_index = 0
    pending = None          # the take waiting for keep/discard

    try:
        while True:
            message = await ws.receive()
            if message.get("type") == "websocket.disconnect":
                break

            payload = message.get("bytes")
            if payload is not None:
                result = await processor.push(payload)
                if result is None:
                    continue
                motion, frame = result
                processor.frames.append(frame)
                processor.times.append(processor._arrived)
                processor.motions.append(motion)
                # Only bound memory while idle; never mid-take.
                if not recording and len(processor.frames) > 400:
                    drop = len(processor.frames) - 400
                    del processor.frames[:drop]
                    del processor.times[:drop]
                    del processor.motions[:drop]
                continue

            text_message = message.get("text")
            if text_message is None:
                continue
            try:
                data = json.loads(text_message)
            except (ValueError, TypeError):
                continue

            kind = data.get("type")

            # ------------------------------------------------------ start
            if kind == "start":
                processor.frames.clear()
                processor.times.clear()
                processor.motions.clear()
                processor._previous = None
                start_index = 0
                recording = True
                pending = None
                await ws.send_json({"type": "recording"})

            # ------------------------------------------------------ stop
            elif kind == "stop":
                if not recording:
                    continue
                recording = False
                end_index = len(processor.frames)
                lo, hi = _trim(processor.motions, start_index, end_index)

                sequence = processor.take_sequence(lo, hi)
                if sequence is None or len(sequence) < 4:
                    await ws.send_json({
                        "type": "error",
                        "reason": "That take was too short to use. Hold the sign a little longer.",
                    })
                    continue

                duration = len(sequence) / (sequence.fps or 30.0)
                tracked = int((sequence.left_present | sequence.right_present).sum())
                visibility = round(tracked / len(sequence), 3)

                problems = []
                if duration < MIN_TAKE_S:
                    problems.append(f"only {duration:.1f}s long")
                if duration > MAX_TAKE_S:
                    problems.append(f"{duration:.1f}s is unusually long")
                if visibility < 0.6:
                    problems.append(
                        f"hands tracked in only {visibility * 100:.0f}% of frames"
                    )

                pending = sequence
                await ws.send_json({
                    "type": "captured",
                    "frames": len(sequence),
                    "duration_s": round(duration, 2),
                    "hand_visibility": visibility,
                    "trimmed_from": round((end_index - start_index) / 25.0, 2),
                    "problems": problems,
                })

            # ------------------------------------------------------ keep
            elif kind == "keep":
                if pending is None:
                    await ws.send_json({"type": "error", "reason": "No take to save."})
                    continue

                sign_code = str(data.get("sign_code") or "").strip().upper()
                participant_code = str(data.get("participant_code") or "P01").strip().upper()
                if not SAFE_CODE.match(sign_code) or not SAFE_CODE.match(participant_code):
                    await ws.send_json({"type": "error", "reason": "Invalid sign or participant code."})
                    continue

                db = SessionLocal()
                try:
                    sign = db.scalar(select(Sign).where(Sign.code == sign_code))
                    if sign is None:
                        await ws.send_json({"type": "error", "reason": f"Unknown sign {sign_code}."})
                        continue

                    participant = db.scalar(
                        select(TestParticipant).where(
                            TestParticipant.participant_code == participant_code
                        )
                    )
                    if participant is None:
                        participant = TestParticipant(
                            participant_code=participant_code,
                            is_unseen=False,   # anyone who contributes a reference is now seen
                            notes="Recorded own reference samples",
                        )
                        db.add(participant)
                        db.flush()

                    # Consent for the purposes this recording is actually used
                    # for. Self-recorded, so the evidence is the act itself --
                    # public release is NOT granted here (I8).
                    for purpose in ("development", "internal_testing"):
                        exists = db.execute(
                            text("SELECT 1 FROM consents WHERE participant_id = :p "
                                 "AND purpose = :q"),
                            {"p": str(participant.id), "q": purpose},
                        ).first()
                        if not exists:
                            db.execute(
                                text("INSERT INTO consents (participant_id, purpose, granted, "
                                     "granted_on, evidence_ref) VALUES (:p, :q, true, "
                                     "current_date, :e)"),
                                {"p": str(participant.id), "q": purpose,
                                 "e": "Self-recorded via the reference recording page"},
                            )

                    directory = reference_dir()
                    directory.mkdir(parents=True, exist_ok=True)
                    existing = len(list(directory.glob(f"{sign_code}_{participant_code}_*.npz")))
                    name = f"{sign_code}_{participant_code}_{existing + 1:02d}"
                    path = directory / f"{name}.npz"

                    from ..services import landmarks as lm

                    lm.save(
                        path,
                        pending,
                        sign_code=sign_code,
                        source_video=f"live:{participant_code}",
                        start_s=0.0,
                        end_s=round(len(pending) / (pending.fps or 30.0), 3),
                        source_fps=round(pending.fps or 30.0, 3),
                    )

                    db.add(
                        SignReference(
                            sign_id=sign.id,
                            landmark_path=f"experiments/day1/references/{name}.npz",
                            extractor_version=lm.EXTRACTOR_VERSION,
                            frame_count=len(pending),
                            source_fps=pending.fps,
                            participant_id=participant.id,
                            is_augmented=False,
                            is_active=True,
                        )
                    )
                    db.commit()

                    total = len(list(directory.glob(f"{sign_code}_{participant_code}_*.npz")))
                    pending = None
                    await ws.send_json({
                        "type": "saved",
                        "name": name,
                        "sign_code": sign_code,
                        "takes_for_sign": total,
                    })
                except Exception as exc:  # noqa: BLE001
                    db.rollback()
                    log.exception("could not save reference")
                    await ws.send_json({"type": "error", "reason": str(exc)[:200]})
                finally:
                    db.close()

            # ------------------------------------------------------ discard
            elif kind == "discard":
                pending = None
                await ws.send_json({"type": "ready", "landmarks": True})

    except WebSocketDisconnect:
        pass
    except Exception as exc:  # noqa: BLE001
        log.exception("record socket failed")
        try:
            await ws.send_json({"type": "error", "reason": str(exc)[:200]})
        except Exception:  # noqa: BLE001
            pass
    finally:
        processor.close()
