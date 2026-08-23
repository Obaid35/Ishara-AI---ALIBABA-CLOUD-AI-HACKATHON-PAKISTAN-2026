"""Sign recognition.

The real engine (MediaPipe Holistic -> normalised landmarks -> DTW) is not
wired up yet. This module defines the interface it must satisfy and ships a
STUB implementation so the rest of the system can be built and demonstrated.

Everything the stub emits is labelled `engine: "stub"`. It must never be
presented as recognition. See docs/RECOGNITION_SPEC.md for the real contract.

What is already real here, and will not change when the model lands:
  * the segmentation state machine and its parameters
  * the two-condition unknown gate, including the different-label rule
  * the event vocabulary the frontend consumes
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol


# --------------------------------------------------------------- parameters
# Initial values from docs/RECOGNITION_SPEC.md §2. Calibrate on Day 1.

THETA_START = 0.020     # motion energy to begin capture
K_START = 3             # consecutive frames above THETA_START
THETA_END = 0.010       # motion energy to end capture (hysteresis: < THETA_START)
K_END = 8               # consecutive frames below THETA_END
T_MIN_MS = 400          # shorter capture is discarded, never classified
T_MAX_MS = 3000         # longer capture aborts
T_REFRACTORY_MS = 600   # after a decision, before returning to READY


class State(str, Enum):
    READY = "ready"
    CAPTURING = "capturing"
    ANALYZING = "analyzing"
    REFRACTORY = "refractory"


class EventType(str, Enum):
    READY = "ready"
    CAPTURING = "capturing"
    ANALYZING = "analyzing"
    RECOGNIZED = "recognized"
    UNKNOWN_AMBIGUOUS = "unknown_ambiguous"
    UNKNOWN_NO_MATCH = "unknown_no_match"
    ABORTED = "aborted"
    DISCARDED = "discarded"


@dataclass
class Candidate:
    sign_code: str
    distance: float


@dataclass
class RecognitionEvent:
    type: EventType
    engine: str = "stub"
    sign_code: str | None = None
    similarity: float | None = None
    d1: float | None = None
    d2_diff_label: float | None = None
    duration_ms: int | None = None
    reason: str | None = None

    def as_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v is not None} | {
            "type": self.type.value,
            "engine": self.engine,
        }


# --------------------------------------------------------------- unknown gate

def apply_unknown_gate(
    candidates: list[Candidate],
    tau_accept: float,
    delta_margin: float,
    per_sign_override: dict[str, float] | None = None,
) -> tuple[EventType, Candidate | None, float | None]:
    """The two-condition gate from docs/RECOGNITION_SPEC.md §4.

    Condition A — absolute quality:      d1 <= tau_accept
    Condition B — separation:            (d2 - d1) / d1 >= delta_margin

    d2 is the best-scoring candidate carrying a DIFFERENT sign code. This
    detail is mandatory: a sign with several reference clips would otherwise
    rank its own other clips second, the margin would always look excellent,
    and Condition B would silently do nothing.
    """
    if not candidates:
        return EventType.UNKNOWN_NO_MATCH, None, None

    ranked = sorted(candidates, key=lambda c: c.distance)
    best = ranked[0]

    # Condition A
    if best.distance > tau_accept:
        return EventType.UNKNOWN_NO_MATCH, best, None

    # Condition B — against the best DIFFERENT label, not simply second place.
    rival = next((c for c in ranked[1:] if c.sign_code != best.sign_code), None)
    if rival is None:
        # Nothing else to confuse it with; Condition A alone decides.
        return EventType.RECOGNIZED, best, None

    margin = (rival.distance - best.distance) / best.distance if best.distance > 0 else float("inf")

    required = delta_margin
    if per_sign_override and best.sign_code in per_sign_override:
        # Overrides may only be stricter (I4); take the larger requirement.
        required = max(required, per_sign_override[best.sign_code])

    if margin < required:
        return EventType.UNKNOWN_AMBIGUOUS, best, margin

    return EventType.RECOGNIZED, best, margin


def similarity_from_distance(distance: float, sigma: float) -> float:
    """Display convenience only. No decision is ever made on this value."""
    import math

    return round(math.exp(-distance / sigma), 3)


# --------------------------------------------------------------- engine interface

class RecognitionEngine(Protocol):
    """What the real MediaPipe + DTW engine must implement."""

    name: str

    def score(self, sequence: list) -> list[Candidate]:
        """Return ranked candidates for one captured sign sequence."""
        ...


class StubEngine:
    """Deterministic-ish placeholder.

    Produces plausible distances so the gate, the UI and the state machine can
    be exercised end to end. It does NOT look at the video.
    """

    name = "stub"

    def __init__(self) -> None:
        self.vocabulary: list[str] = []
        self.forced_sign: str | None = None
        self.forced_outcome: str | None = None

    def set_vocabulary(self, codes: list[str]) -> None:
        self.vocabulary = codes

    def arm(self, sign_code: str | None, outcome: str | None = None) -> None:
        """Dev/demo aid: make the next capture resolve to a known result."""
        self.forced_sign = sign_code
        self.forced_outcome = outcome

    def score(self, sequence: list) -> list[Candidate]:
        if not self.vocabulary:
            return []

        rng = random.Random()
        target = self.forced_sign or rng.choice(self.vocabulary)
        outcome = self.forced_outcome
        self.forced_sign = None
        self.forced_outcome = None

        others = [c for c in self.vocabulary if c != target]
        rng.shuffle(others)

        if outcome == "no_match":
            best_d, rival_d = 0.85, 0.92
        elif outcome == "ambiguous":
            best_d, rival_d = 0.40, 0.43
        else:
            best_d, rival_d = 0.18, 0.55

        candidates = [Candidate(target, best_d)]
        if others:
            candidates.append(Candidate(others[0], rival_d))
        for i, code in enumerate(others[1:4]):
            candidates.append(Candidate(code, rival_d + 0.12 * (i + 1)))
        return candidates


# --------------------------------------------------------------- state machine

@dataclass
class SegmentationMachine:
    """Motion-energy segmentation with hysteresis.

    One completed motion produces AT MOST ONE decision (D027). The recognizer
    never emits a label per frame.
    """

    state: State = State.READY
    above_count: int = 0
    below_count: int = 0
    started_at_ms: float = 0.0
    refractory_until_ms: float = 0.0
    frames: list = field(default_factory=list)

    def _now(self) -> float:
        return time.monotonic() * 1000.0

    def push(self, motion: float, frame: object | None = None) -> RecognitionEvent | None:
        now = self._now()

        if self.state is State.REFRACTORY:
            if now >= self.refractory_until_ms:
                self.state = State.READY
                return RecognitionEvent(EventType.READY)
            return None

        if self.state is State.READY:
            if motion > THETA_START:
                self.above_count += 1
                if self.above_count >= K_START:
                    self.state = State.CAPTURING
                    self.started_at_ms = now
                    self.below_count = 0
                    self.frames = [frame] if frame is not None else []
                    return RecognitionEvent(EventType.CAPTURING)
            else:
                self.above_count = 0
            return None

        # CAPTURING
        if frame is not None:
            self.frames.append(frame)
        duration = now - self.started_at_ms

        if duration > T_MAX_MS:
            self._enter_refractory(now)
            return RecognitionEvent(
                EventType.ABORTED,
                duration_ms=int(duration),
                reason="Capture exceeded the maximum sign duration",
            )

        if motion < THETA_END:
            self.below_count += 1
            if self.below_count >= K_END:
                self.state = State.ANALYZING
                return RecognitionEvent(EventType.ANALYZING, duration_ms=int(duration))
        else:
            self.below_count = 0
        return None

    def take_segment(self) -> tuple[list, int]:
        duration = int(self._now() - self.started_at_ms)
        frames, self.frames = self.frames, []
        return frames, duration

    def finish(self) -> None:
        self._enter_refractory(self._now())

    def _enter_refractory(self, now: float) -> None:
        self.state = State.REFRACTORY
        self.refractory_until_ms = now + T_REFRACTORY_MS
        self.above_count = 0
        self.below_count = 0
        self.frames = []

    def too_short(self, duration_ms: int) -> bool:
        """Incidental movement is discarded silently, not reported as unknown."""
        return duration_ms < T_MIN_MS


# Module-level engine. Replace with the real implementation when MediaPipe +
# DTW land; nothing else in the application needs to change.
engine: RecognitionEngine = StubEngine()


def is_stub() -> bool:
    return getattr(engine, "name", "stub") == "stub"
