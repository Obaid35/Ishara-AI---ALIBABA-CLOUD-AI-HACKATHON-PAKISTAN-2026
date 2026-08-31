"""Recognition WebSocket.

The browser streams camera frames; landmark extraction, segmentation and the
unknown gate all run here on the Python side (D035). The browser never decides
anything -- it only captures and displays.

Client -> server
    binary   4-byte LE uint32 capture timestamp (ms) + JPEG bytes
    {"type": "hello"}
    {"type": "motion", "value": n}   fallback when frames cannot be sent
    {"type": "arm", "sign": "...", "outcome": "..."}   stub/demo aid only
    {"type": "reset"}

Server -> client
    {"type": "ready" | "capturing" | "analyzing" | "recognized"
             | "unknown_ambiguous" | "unknown_no_match" | "aborted" | "discarded",
     "engine": "dtw" | "stub", ...}

The state machine and the gate are identical whichever engine is installed.
"""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import text

from ..db import SessionLocal, db_state
from ..services import snapshot
from ..services import recognition as recog
from ..services.recognition import (
    K_END,
    THETA_END,
    EventType,
    RecognitionEvent,
    SegmentationMachine,
    StubEngine,
    apply_unknown_gate,
    is_stub,
    similarity_from_distance,
)

log = logging.getLogger("ishara.recognize")
router = APIRouter(tags=["recognition"])

FALLBACK_CONFIG = {"tau_accept": 0.55, "delta_margin": 0.15, "sigma": 0.35}


def _load_context() -> tuple[list[str], dict, dict[str, float]]:
    """Vocabulary, active thresholds and per-sign overrides."""
    if db_state.available or db_state.probe():
        db = SessionLocal()
        try:
            codes = [
                r[0]
                for r in db.execute(text("SELECT code FROM v_production_vocabulary ORDER BY code"))
            ]
            row = db.execute(
                text(
                    "SELECT tau_accept, delta_margin, sigma FROM recognition_config "
                    "WHERE is_active LIMIT 1"
                )
            ).first()
            config = dict(row._mapping) if row else dict(FALLBACK_CONFIG)
            overrides = {
                r[0]: float(r[1])
                for r in db.execute(
                    text(
                        "SELECT code, delta_margin_override FROM signs "
                        "WHERE delta_margin_override IS NOT NULL"
                    )
                )
            }
            return codes, {k: float(v) for k, v in config.items()}, overrides
        finally:
            db.close()

    codes = [s.get("code") for s in snapshot.load("signs.json") if s.get("code")]
    return codes, dict(FALLBACK_CONFIG), {}


class FrameProcessor:
    """Per-connection MediaPipe pipeline.

    Holistic is stateful and not thread-safe, so each socket owns one instance
    and every call is pushed to a worker thread -- inference is far too slow to
    run on the event loop.
    """

    def __init__(self) -> None:
        self.available = False
        self._holistic = None
        self._cv2 = None
        self._np = None
        self._mp = None
        self._lm = None
        self.frames: list = []
        self.times: list[float] = []      # capture time per frame, seconds
        self.motions: list[float] = []    # motion energy per frame
        self._previous = None
        # VIDEO mode requires strictly increasing timestamps for the lifetime
        # of the landmarker instance.
        self._timestamp_ms = 0

    def start(self) -> str | None:
        try:
            import cv2
            import mediapipe as mp
            import numpy as np
            from mediapipe.tasks.python import BaseOptions
            from mediapipe.tasks.python.vision import (
                HolisticLandmarker,
                HolisticLandmarkerOptions,
                RunningMode,
            )

            from ..services import landmarks as lm
        except ImportError as exc:
            return f"landmark extraction unavailable ({exc.name})"

        model = lm.model_path()
        if not model.exists():
            return f"model bundle missing at {model.name}"

        self._cv2, self._np, self._mp, self._lm = cv2, np, mp, lm
        # Same model and options as offline extraction. If these diverge, live
        # features stop matching the stored references and DTW silently degrades.
        self._holistic = HolisticLandmarker.create_from_options(
            HolisticLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=str(model)),
                running_mode=RunningMode.VIDEO,
                min_pose_detection_confidence=0.5,
                min_pose_landmarks_confidence=0.5,
                min_hand_landmarks_confidence=0.5,
            )
        )
        self.available = True
        return None

    def close(self) -> None:
        if self._holistic is not None:
            try:
                self._holistic.close()
            except Exception:  # noqa: BLE001
                pass
            self._holistic = None

    @staticmethod
    def split_payload(payload: bytes) -> tuple[float | None, bytes]:
        """Separate the client capture timestamp from the JPEG bytes.

        The client stamps each frame at CAPTURE time. Server arrival time is
        useless here: MediaPipe inference is slower than the camera, so frames
        queue and arrival order reflects processing speed, not signing speed.
        Resampling on that wrong rate stretches the sequence and DTW fails.
        """
        if len(payload) > 4 and payload[4:6] == b"\xff\xd8":   # JPEG SOI marker
            ms = int.from_bytes(payload[:4], "little")
            return ms / 1000.0, payload[4:]
        return None, payload

    def _process_sync(self, payload: bytes):
        cv2, np, mp, lm = self._cv2, self._np, self._mp, self._lm
        buffer = np.frombuffer(payload, dtype=np.uint8)
        image = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
        if image is None:
            return None
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        self._timestamp_ms += 33          # ~30 fps; only monotonicity matters
        return lm.process_results(
            self._holistic.detect_for_video(mp_image, self._timestamp_ms)
        )

    async def push(self, payload: bytes) -> tuple[float, object] | None:
        """Decode + extract one frame. Returns (motion_energy, frame)."""
        import time

        stamped, jpeg = self.split_payload(payload)
        # Fall back to arrival time only if the client sent no timestamp.
        self._arrived = stamped if stamped is not None else time.monotonic()
        frame = await asyncio.to_thread(self._process_sync, jpeg)
        if frame is None:
            return None

        motion = 0.0
        previous = self._previous
        if previous is not None:
            np, lm = self._np, self._lm
            deltas = []
            for sl, now_present, before_present in (
                (lm.LEFT_SLICE, frame.left_present, previous.left_present),
                (lm.RIGHT_SLICE, frame.right_present, previous.right_present),
            ):
                if now_present and before_present:
                    now = frame.features[sl].reshape(-1, 2)
                    before = previous.features[sl].reshape(-1, 2)
                    deltas.append(np.linalg.norm(now - before, axis=1))
            if deltas:
                motion = float(np.concatenate(deltas).mean())

        self._previous = frame
        return motion, frame

    def take_sequence(self, start: int, end: int):
        """Build a resampled Sequence from the captured frames.

        The frame rate is MEASURED from arrival times, never assumed. Guessing
        it stretches or compresses the sequence relative to the references, and
        DTW's band constraint then cannot align them at all -- everything comes
        back unknown with plausible-looking distances.
        """
        lm = self._lm
        window = self.frames[start:end]
        stamps = self.times[start:end]
        if len(window) < 2:
            return None

        # Trim the trailing rest frames. Capture only ends after K_END frames
        # below the motion floor, so every window carries a tail of stillness.
        # On a 0.9s sign that tail is a third of the clip and it drags the DTW
        # distance up badly; on a 2.2s sign it barely registers.
        energies = self.motions[start:end]
        if len(energies) == len(window):
            cut = len(window)
            # Remove AT MOST K_END frames: capture ends after exactly that many
            # sub-threshold frames, so this undoes the detection tail and no
            # more. Trimming further ate into slow signs like DOCTOR and
            # PAIN_IN_EYE, whose real movement dips below the floor mid-sign.
            floor = max(0, len(window) - K_END)
            while cut > floor and cut > 4 and energies[cut - 1] < THETA_END:
                cut -= 1
            if cut >= 4:
                window = window[:cut]
                stamps = stamps[:cut]

        fps = 15.0
        if len(stamps) >= 2:
            span = stamps[-1] - stamps[0]
            if span > 1e-3:
                fps = (len(stamps) - 1) / span
        fps = max(5.0, min(fps, 120.0))

        return lm.resample(lm.build_sequence(window, fps), target_fps=30.0)


@router.websocket("/ws/recognize")
async def recognize(ws: WebSocket) -> None:
    await ws.accept()

    codes, config, overrides = _load_context()
    active = recog.engine
    if isinstance(active, StubEngine):
        active.set_vocabulary(codes)
    elif hasattr(active, "set_vocabulary"):
        active.set_vocabulary(codes)

    processor = FrameProcessor()
    processor_error = processor.start()
    machine = SegmentationMachine()
    engine_name = getattr(active, "name", "stub")

    await ws.send_json(
        {
            "type": "ready",
            "engine": engine_name,
            "is_stub": is_stub(),
            "landmarks": processor.available,
            "vocabulary_size": len(codes),
            "thresholds": config,
            "notice": (
                "Recognition engine is a STUB. Results are simulated and must not "
                "be presented as sign recognition."
            )
            if is_stub()
            else None,
        }
    )

    if processor_error:
        log.warning("Frame processing disabled: %s", processor_error)

    if not codes:
        await ws.send_json(
            {
                "type": "aborted",
                "engine": engine_name,
                "reason": "No signs are Reliable + Enabled — the vocabulary is empty.",
            }
        )

    async def finish_capture(duration_ms: int, start_index: int, end_index: int) -> None:
        """Score one completed motion and emit exactly one decision."""
        if machine.too_short(duration_ms):
            machine.finish()
            await ws.send_json(
                RecognitionEvent(
                    EventType.DISCARDED, engine=engine_name,
                    duration_ms=duration_ms, reason="Too short to be a sign",
                ).as_dict()
            )
            return

        sequence = None
        if processor.available:
            sequence = processor.take_sequence(start_index, end_index)
            candidates = active.score(sequence) if sequence is not None else []
        else:
            candidates = active.score([])

        outcome, best, _margin = apply_unknown_gate(
            candidates,
            tau_accept=config["tau_accept"],
            delta_margin=config["delta_margin"],
            per_sign_override=overrides,
        )

        rival = None
        if best:
            rival = next(
                (c.distance for c in sorted(candidates, key=lambda c: c.distance)
                 if c.sign_code != best.sign_code),
                None,
            )

        # How much of the capture actually had a hand tracked. Poor tracking
        # inflates every distance, so a bad run should be distinguishable from
        # a genuinely different signing style.
        visibility = None
        if sequence is not None and len(sequence) > 0:
            tracked = int((sequence.left_present | sequence.right_present).sum())
            visibility = round(tracked / len(sequence), 3)

        # Persist the captured sequence. A confident wrong answer is either a
        # mis-segmented window or a genuinely ambiguous sign, and the only way
        # to tell them apart afterwards is to still have the capture.
        capture_path = None
        if sequence is not None and len(sequence) >= 4:
            try:
                import time as _time

                from ..config import settings as _settings
                from ..services import landmarks as _lm

                captures = _settings.repo_root / "experiments" / "day1" / "captures"
                captures.mkdir(parents=True, exist_ok=True)
                name = f"capture_{int(_time.time() * 1000)}"
                _lm.save(captures / f"{name}.npz", sequence,
                         sign_code=best.sign_code if best else "",
                         source_video="live", start_s=0.0,
                         end_s=round(len(sequence) / (sequence.fps or 30.0), 3),
                         source_fps=round(sequence.fps or 30.0, 3))
                capture_path = f"experiments/day1/captures/{name}.npz"
            except Exception:  # noqa: BLE001 - diagnostics must never break a trial
                capture_path = None

        machine.finish()
        await ws.send_json(
            RecognitionEvent(
                type=outcome,
                engine=engine_name,
                best_sign_code=best.sign_code if best else None,
                hand_visibility=visibility,
                frames=len(sequence) if sequence is not None else None,
                capture_path=capture_path,
                sign_code=best.sign_code if best and outcome is EventType.RECOGNIZED else None,
                similarity=(
                    similarity_from_distance(best.distance, config.get("sigma", 0.35))
                    if best else None
                ),
                d1=round(best.distance, 4) if best else None,
                d2_diff_label=round(rival, 4) if rival is not None else None,
                duration_ms=duration_ms,
            ).as_dict()
        )

    capture_start = 0

    try:
        while True:
            message = await ws.receive()

            if message.get("type") == "websocket.disconnect":
                break

            payload = message.get("bytes")
            motion: float | None = None

            # ---------------------------------------------------- frames
            if payload is not None and processor.available:
                result = await processor.push(payload)
                if result is None:
                    continue
                motion, frame = result
                processor.frames.append(frame)
                processor.times.append(processor._arrived)
                processor.motions.append(motion)
                # Keep memory bounded on a long-lived socket.
                if len(processor.frames) > 900:
                    drop = len(processor.frames) - 900
                    processor.frames = processor.frames[drop:]
                    processor.times = processor.times[drop:]
                    processor.motions = processor.motions[drop:]
                    capture_start = max(0, capture_start - drop)

            # ---------------------------------------------------- control
            elif message.get("text") is not None:
                import json

                try:
                    data = json.loads(message["text"])
                except (ValueError, TypeError):
                    continue

                kind = data.get("type")
                if kind == "reset":
                    machine = SegmentationMachine()
                    processor.frames.clear()
                    processor.times.clear()
                    processor.motions.clear()
                    processor._previous = None
                    await ws.send_json({"type": "ready", "engine": engine_name})
                    continue
                if kind == "arm" and isinstance(active, StubEngine):
                    active.arm(data.get("sign"), data.get("outcome"))
                    continue
                if kind == "motion" and not processor.available:
                    # Fallback path: browser-computed motion, stub engine only.
                    motion = float(data.get("value", 0.0))
                else:
                    continue
            else:
                continue

            if motion is None:
                continue

            event = machine.push(motion)
            if not event:
                continue

            if event.type is EventType.CAPTURING:
                capture_start = max(0, len(processor.frames) - 1)

            await ws.send_json(event.as_dict())

            if event.type is EventType.ANALYZING:
                _frames, duration = machine.take_segment()
                await finish_capture(duration, capture_start, len(processor.frames))

    except WebSocketDisconnect:
        pass
    except Exception as exc:  # noqa: BLE001
        log.exception("recognition socket failed")
        try:
            await ws.send_json({"type": "aborted", "reason": str(exc)})
        except Exception:  # noqa: BLE001
            pass
    finally:
        processor.close()
