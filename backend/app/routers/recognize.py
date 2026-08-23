"""Recognition WebSocket.

Protocol (client -> server):
    {"type": "hello"}
    {"type": "motion", "value": 0.031}     motion energy for one frame
    {"type": "arm", "sign": "FEVER", "outcome": "recognized"}   dev/demo aid
    {"type": "reset"}

Protocol (server -> client):
    {"type": "ready" | "capturing" | "analyzing" | "recognized"
             | "unknown_ambiguous" | "unknown_no_match" | "aborted" | "discarded",
     "engine": "stub", ...}

The state machine and the unknown gate here are real and will not change when
the model lands. Only the scoring is stubbed — every event says so.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import text

from ..db import SessionLocal, db_state
from ..services import snapshot
from ..services.recognition import (
    EventType,
    RecognitionEvent,
    SegmentationMachine,
    StubEngine,
    apply_unknown_gate,
    engine,
    is_stub,
    similarity_from_distance,
)

log = logging.getLogger("psl.recognize")
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


@router.websocket("/ws/recognize")
async def recognize(ws: WebSocket) -> None:
    await ws.accept()

    codes, config, overrides = _load_context()
    if isinstance(engine, StubEngine):
        engine.set_vocabulary(codes)

    machine = SegmentationMachine()

    await ws.send_json(
        {
            "type": "ready",
            "engine": getattr(engine, "name", "stub"),
            "is_stub": is_stub(),
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

    if not codes:
        await ws.send_json(
            {
                "type": "aborted",
                "engine": getattr(engine, "name", "stub"),
                "reason": "No signs are Reliable + Enabled — the vocabulary is empty. "
                          "Seed content and enable signs before signing.",
            }
        )

    try:
        while True:
            msg = await ws.receive_json()
            kind = msg.get("type")

            if kind == "reset":
                machine = SegmentationMachine()
                await ws.send_json({"type": "ready", "engine": getattr(engine, "name", "stub")})
                continue

            if kind == "arm" and isinstance(engine, StubEngine):
                engine.arm(msg.get("sign"), msg.get("outcome"))
                continue

            if kind != "motion":
                continue

            event = machine.push(float(msg.get("value", 0.0)))
            if event:
                await ws.send_json(event.as_dict())

            if event and event.type is EventType.ANALYZING:
                frames, duration = machine.take_segment()

                # Incidental movement is discarded silently — a scratched nose
                # must not produce an "unknown" prompt.
                if machine.too_short(duration):
                    machine.finish()
                    await ws.send_json(
                        RecognitionEvent(
                            EventType.DISCARDED,
                            engine=getattr(engine, "name", "stub"),
                            duration_ms=duration,
                            reason="Too short to be a sign",
                        ).as_dict()
                    )
                    continue

                candidates = engine.score(frames)
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

                result = RecognitionEvent(
                    type=outcome,
                    engine=getattr(engine, "name", "stub"),
                    sign_code=best.sign_code if best and outcome is EventType.RECOGNIZED else None,
                    similarity=(
                        similarity_from_distance(best.distance, config.get("sigma", 0.35))
                        if best
                        else None
                    ),
                    d1=round(best.distance, 4) if best else None,
                    d2_diff_label=round(rival, 4) if rival is not None else None,
                    duration_ms=duration,
                )
                machine.finish()
                await ws.send_json(result.as_dict())

    except WebSocketDisconnect:
        return
    except Exception as exc:  # noqa: BLE001
        log.exception("recognition socket failed")
        try:
            await ws.send_json({"type": "aborted", "reason": str(exc)})
        except Exception:  # noqa: BLE001
            pass
