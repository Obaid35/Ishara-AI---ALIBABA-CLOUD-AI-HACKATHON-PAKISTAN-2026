"""Landmark extraction and normalisation.

THE SINGLE SOURCE OF TRUTH for turning a video frame into a feature vector.

Both paths must import from here:
  * offline reference extraction  (scripts/extract_references.py)
  * live recognition             (routers/recognize.py)

If the two ever diverge, DTW distances become silently wrong with no error
message. That is why `EXTRACTOR_VERSION` is stamped onto every saved reference
and checked before a reference is trusted.

Feature layout per frame (98 dims):
    [ 0:  2]  left hand ANCHOR  - wrist position in the body frame
    [ 2: 42]  left hand SHAPE   - 20 finger points relative to the wrist,
                                  divided by hand size
    [42: 44]  right hand ANCHOR
    [44: 84]  right hand SHAPE
    [84: 98]  pose subset       - nose, L/R shoulder, L/R elbow, L/R wrist

WHY ANCHOR AND SHAPE ARE SPLIT
------------------------------
Version 1 stored all 21 hand points as absolute body-relative positions. That
made a small placement difference catastrophic: if a signer holds the hand a
few centimetres lower on the chest than the reference signer, ALL 21 points
shift together and every one of them contributes error, even though the
movement is the same sign performed correctly.

Splitting them means a placement difference moves only the 2 anchor dims,
while the 40 shape dims still match. Dividing the shape by hand size also
makes it work across large and small hands.

This mirrors how a sign is actually described: WHERE the hand travels
(anchor trajectory) and WHAT the fingers do (shape). DTW then compares
the pattern rather than demanding identical coordinates.

Normalisation: translate to the shoulder midpoint, scale by shoulder width.
Without it, matching keys on the person rather than the sign.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# Bump whenever the feature layout, normalisation or MediaPipe version changes.
# Every stored reference records this; a mismatch means re-extract.
#
# MediaPipe 1.x removed the legacy `mp.solutions.holistic` API, so this targets
# the Tasks HolisticLandmarker. The two APIs return different result shapes;
# `process_results` accepts either, but the version string records which
# produced a given reference.
EXTRACTOR_VERSION = "holistic-tasks/2.0/98d-anchor-shape"

# Tasks API needs an explicit model bundle - it does not ship or auto-fetch one.
MODEL_FILENAME = "holistic_landmarker.task"
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/holistic_landmarker/"
    "holistic_landmarker/float16/latest/holistic_landmarker.task"
)


def model_path():
    from ..config import settings

    return settings.repo_root / "models" / MODEL_FILENAME

HAND_POINTS = 21
POSE_POINTS = 7
FEATURE_DIM = (HAND_POINTS * 2) * 2 + POSE_POINTS * 2  # 42 + 42 + 14 = 98

LEFT_SLICE = slice(0, 42)
RIGHT_SLICE = slice(42, 84)
POSE_SLICE = slice(84, 98)

# Within a hand block: first 2 dims locate the hand, the remaining 40 describe
# its shape. The cost function weights these separately.
ANCHOR_DIMS = 2
LEFT_ANCHOR = slice(0, 2)
LEFT_SHAPE = slice(2, 42)
RIGHT_ANCHOR = slice(42, 44)
RIGHT_SHAPE = slice(44, 84)

# MediaPipe hand landmarks: 0 is the wrist, 9 the middle-finger MCP knuckle.
# Wrist->knuckle is a stable proxy for hand size across people.
HAND_WRIST = 0
HAND_MIDDLE_MCP = 9
MIN_HAND_SPAN = 1e-4

# Indices into MediaPipe Holistic's 33-point pose landmark list.
POSE_NOSE = 0
POSE_L_SHOULDER, POSE_R_SHOULDER = 11, 12
POSE_L_ELBOW, POSE_R_ELBOW = 13, 14
POSE_L_WRIST, POSE_R_WRIST = 15, 16
POSE_SUBSET = [
    POSE_NOSE,
    POSE_L_SHOULDER, POSE_R_SHOULDER,
    POSE_L_ELBOW, POSE_R_ELBOW,
    POSE_L_WRIST, POSE_R_WRIST,
]

# Below this shoulder width (in normalised image units) the pose is too small
# or too unreliable to normalise against.
MIN_SHOULDER_WIDTH = 0.02


@dataclass
class Frame:
    """One processed frame."""

    features: np.ndarray          # (98,) float32, normalised
    left_present: bool
    right_present: bool
    pose_present: bool

    @property
    def any_hand(self) -> bool:
        return self.left_present or self.right_present


def empty_frame() -> Frame:
    return Frame(np.zeros(FEATURE_DIM, dtype=np.float32), False, False, False)


def _marks(landmarks):
    """Normalise the two MediaPipe result shapes to a plain sequence.

    Legacy Solutions returns an object with a `.landmark` field; Tasks returns
    a list directly (and for some landmarkers, a list of lists).
    """
    if landmarks is None:
        return None
    if hasattr(landmarks, "landmark"):          # legacy Solutions
        return landmarks.landmark
    if isinstance(landmarks, (list, tuple)):    # Tasks
        if not landmarks:
            return None
        first = landmarks[0]
        if isinstance(first, (list, tuple)):    # nested: take the first person
            return first or None
        return landmarks
    return None


def _points(landmarks, indices=None) -> np.ndarray:
    """MediaPipe landmarks -> (N, 2) array of x, y."""
    marks = _marks(landmarks)
    if marks is None:
        return np.zeros((0, 2), dtype=np.float32)
    if indices is None:
        return np.array([[m.x, m.y] for m in marks], dtype=np.float32)
    return np.array([[marks[i].x, marks[i].y] for i in indices], dtype=np.float32)


def process_results(results) -> Frame:
    """Turn one MediaPipe Holistic result into a normalised Frame.

    Accepts either a legacy `holistic.process()` result or a Tasks
    `HolisticLandmarkerResult`.
    """
    marks = _marks(getattr(results, "pose_landmarks", None))
    if marks is None or len(marks) <= max(POSE_SUBSET):
        # No body means no reliable normalisation anchor. The frame is unusable
        # rather than merely empty -- do not fall back to raw coordinates.
        return empty_frame()
    pose = getattr(results, "pose_landmarks", None)
    left_shoulder = np.array([marks[POSE_L_SHOULDER].x, marks[POSE_L_SHOULDER].y], dtype=np.float32)
    right_shoulder = np.array([marks[POSE_R_SHOULDER].x, marks[POSE_R_SHOULDER].y], dtype=np.float32)

    origin = (left_shoulder + right_shoulder) / 2.0
    scale = float(np.linalg.norm(left_shoulder - right_shoulder))
    if scale < MIN_SHOULDER_WIDTH:
        return empty_frame()

    def norm(points: np.ndarray) -> np.ndarray:
        return ((points - origin) / scale).astype(np.float32)

    features = np.zeros(FEATURE_DIM, dtype=np.float32)

    left_marks = _marks(getattr(results, "left_hand_landmarks", None))
    right_marks = _marks(getattr(results, "right_hand_landmarks", None))

    left_present = left_marks is not None and len(left_marks) == HAND_POINTS
    right_present = right_marks is not None and len(right_marks) == HAND_POINTS

    def hand_features(marks) -> np.ndarray:
        """2 anchor dims + 40 size-invariant shape dims."""
        points = _points(marks)                      # (21, 2) raw image coords
        wrist = points[HAND_WRIST]

        # Hand size from wrist to the middle knuckle, so a large and a small
        # hand making the same shape produce the same numbers.
        span = float(np.linalg.norm(points[HAND_MIDDLE_MCP] - wrist))
        if span < MIN_HAND_SPAN:
            span = MIN_HAND_SPAN

        anchor = norm(wrist.reshape(1, 2)).reshape(-1)          # where on the body
        shape = ((points[1:] - wrist) / span).astype(np.float32)  # what the fingers do
        return np.concatenate([anchor, shape.reshape(-1)])

    if left_present:
        features[LEFT_SLICE] = hand_features(left_marks)
    if right_present:
        features[RIGHT_SLICE] = hand_features(right_marks)

    features[POSE_SLICE] = norm(_points(pose, POSE_SUBSET)).reshape(-1)

    return Frame(features, left_present, right_present, True)


# --------------------------------------------------------------- sequences

@dataclass
class Sequence:
    """A run of frames, ready for DTW."""

    features: np.ndarray          # (T, 98)
    left_present: np.ndarray      # (T,) bool
    right_present: np.ndarray     # (T,) bool
    fps: float

    def __len__(self) -> int:
        return int(self.features.shape[0])

    @property
    def duration_s(self) -> float:
        return len(self) / self.fps if self.fps else 0.0

    def slice(self, start: int, end: int) -> "Sequence":
        return Sequence(
            self.features[start:end].copy(),
            self.left_present[start:end].copy(),
            self.right_present[start:end].copy(),
            self.fps,
        )


def build_sequence(frames: list[Frame], fps: float) -> Sequence:
    if not frames:
        return Sequence(np.zeros((0, FEATURE_DIM), np.float32),
                        np.zeros(0, bool), np.zeros(0, bool), fps)
    return Sequence(
        np.stack([f.features for f in frames]).astype(np.float32),
        np.array([f.left_present for f in frames], dtype=bool),
        np.array([f.right_present for f in frames], dtype=bool),
        fps,
    )


def motion_energy(sequence: Sequence) -> np.ndarray:
    """Per-frame motion energy in shoulder-width units.

    Measured over hand points that are present in BOTH the current and the
    previous frame, so a hand appearing or disappearing does not register as a
    huge jump. Same definition the live segmenter uses.
    """
    n = len(sequence)
    energy = np.zeros(n, dtype=np.float32)
    if n < 2:
        return energy

    for t in range(1, n):
        values: list[float] = []
        for anchor_sl, present in (
            (LEFT_ANCHOR, sequence.left_present),
            (RIGHT_ANCHOR, sequence.right_present),
        ):
            if present[t] and present[t - 1]:
                values.append(
                    float(
                        np.linalg.norm(
                            sequence.features[t, anchor_sl]
                            - sequence.features[t - 1, anchor_sl]
                        )
                    )
                )
        if values:
            energy[t] = float(np.mean(values))
    return energy


def resample(sequence: Sequence, target_fps: float = 30.0) -> Sequence:
    """Resample to a common frame rate.

    The source clips are not all the same fps (dictionary clips here are 24.8,
    the phone-recorded one is 30). DTW tolerates timing differences, but making
    the rate uniform keeps the band constraint and the length normalisation
    comparable across the vocabulary.
    """
    n = len(sequence)
    if n < 2 or not sequence.fps or abs(sequence.fps - target_fps) < 0.01:
        return sequence

    duration = n / sequence.fps
    target_n = max(2, int(round(duration * target_fps)))
    src = np.linspace(0.0, n - 1, n)
    dst = np.linspace(0.0, n - 1, target_n)

    features = np.empty((target_n, FEATURE_DIM), dtype=np.float32)
    for d in range(FEATURE_DIM):
        features[:, d] = np.interp(dst, src, sequence.features[:, d])

    # Presence is boolean: take nearest neighbour, never interpolate.
    idx = np.clip(np.round(dst).astype(int), 0, n - 1)
    return Sequence(
        features,
        sequence.left_present[idx],
        sequence.right_present[idx],
        target_fps,
    )


def save(path, sequence: Sequence, **meta) -> None:
    np.savez_compressed(
        path,
        features=sequence.features,
        left_present=sequence.left_present,
        right_present=sequence.right_present,
        fps=np.float32(sequence.fps),
        extractor_version=EXTRACTOR_VERSION,
        **{k: np.array(v) for k, v in meta.items()},
    )


def load(path) -> tuple[Sequence, dict]:
    data = np.load(path, allow_pickle=False)
    version = str(data["extractor_version"])
    if version != EXTRACTOR_VERSION:
        raise ValueError(
            f"Reference was extracted with '{version}' but this build uses "
            f"'{EXTRACTOR_VERSION}'. Re-extract before trusting it - mismatched "
            "features produce silently wrong distances."
        )
    sequence = Sequence(
        data["features"].astype(np.float32),
        data["left_present"].astype(bool),
        data["right_present"].astype(bool),
        float(data["fps"]),
    )
    meta = {k: data[k].item() if data[k].ndim == 0 else data[k]
            for k in data.files
            if k not in {"features", "left_present", "right_present", "fps"}}
    return sequence, meta
