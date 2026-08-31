"""DTW reference matching.

This is the real recognition engine. It replaces StubEngine once references
exist. There is no training and no model file -- a live sign is compared
directly against stored reference sequences, and the closest one wins only if
the unknown gate accepts it.

Specification: docs/RECOGNITION_SPEC.md §3.
  * per-frame cost   Euclidean over the hand/pose blocks present in BOTH
                     frames, plus a penalty per mismatched hand block
  * path constraint  Sakoe-Chiba band, 15% of the longer sequence
  * normalisation    accumulated cost / path length, so short and long signs
                     are comparable against one shared threshold
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np

from . import landmarks as lm

log = logging.getLogger("ishara.dtw")

INF = float("inf")

# Relative importance of hand trajectory vs handshape. A sign is described
# by where the hand travels AND what the fingers do; neither alone is
# enough. Tunable -- validated by the perturbation test in
# scripts/feature_robustness.py.
W_ANCHOR = 1.0
W_SHAPE = 0.6


# --------------------------------------------------------------- cost matrix

def _block_distances(q: np.ndarray, r: np.ndarray, sl: slice) -> np.ndarray:
    """Mean per-point Euclidean distance between every frame pair, for one block.

    q: (T1, 98)  r: (T2, 98)  ->  (T1, T2)
    """
    qp = q[:, sl].reshape(q.shape[0], -1, 2)          # (T1, P, 2)
    rp = r[:, sl].reshape(r.shape[0], -1, 2)          # (T2, P, 2)
    diff = qp[:, None, :, :] - rp[None, :, :, :]      # (T1, T2, P, 2)
    return np.linalg.norm(diff, axis=3).mean(axis=2).astype(np.float32)


def cost_matrix(query: lm.Sequence, reference: lm.Sequence, p_absent: float) -> np.ndarray:
    """Frame-to-frame cost, honouring hand presence.

    A hand that is missing from one frame and present in the other must not be
    compared numerically -- the absent hand's coordinates are zeros, which sit
    at the shoulder midpoint and would read as a real (and very wrong) hand
    position. Those pairs take a fixed penalty instead.
    """
    q, r = query.features, reference.features
    t1, t2 = q.shape[0], r.shape[0]

    pose = _block_distances(q, r, lm.POSE_SLICE)      # always present
    total = pose.copy()
    counted = np.ones((t1, t2), dtype=np.float32)
    penalty = np.zeros((t1, t2), dtype=np.float32)

    for anchor_sl, shape_sl, q_present, r_present in (
        (lm.LEFT_ANCHOR, lm.LEFT_SHAPE, query.left_present, reference.left_present),
        (lm.RIGHT_ANCHOR, lm.RIGHT_SHAPE, query.right_present, reference.right_present),
    ):
        both = q_present[:, None] & r_present[None, :]
        either = q_present[:, None] ^ r_present[None, :]
        if both.any():
            # WHERE the hand is, and WHAT the fingers do, scored separately.
            # Scoring them together let a small placement difference swamp a
            # correct handshape, which is what made a different signer fail.
            travel = _block_distances(q, r, anchor_sl)
            shape = _block_distances(q, r, shape_sl)
            block = W_ANCHOR * travel + W_SHAPE * shape
            total += np.where(both, block, 0.0)
            counted += (both.astype(np.float32) * (W_ANCHOR + W_SHAPE))
        penalty += either.astype(np.float32) * p_absent

    return (total / counted) + penalty


# --------------------------------------------------------------- DTW

def dtw_distance(cost: np.ndarray, band_pct: float = 15.0) -> float:
    """Length-normalised DTW distance over a Sakoe-Chiba band.

    Returns the accumulated cost divided by the warping path length, so a long
    sign is not penalised for being long.
    """
    t1, t2 = cost.shape
    if t1 == 0 or t2 == 0:
        return INF

    band = max(2, int(round(max(t1, t2) * band_pct / 100.0)))

    acc = np.full((t1 + 1, t2 + 1), INF, dtype=np.float64)
    steps = np.zeros((t1 + 1, t2 + 1), dtype=np.int32)
    acc[0, 0] = 0.0

    for i in range(1, t1 + 1):
        # Only visit cells inside the band around the diagonal.
        centre = (i - 1) * t2 / t1
        lo = max(1, int(centre - band) + 1)
        hi = min(t2, int(centre + band) + 1)
        for j in range(lo, hi + 1):
            best, best_steps = INF, 0
            for pi, pj in ((i - 1, j - 1), (i - 1, j), (i, j - 1)):
                if acc[pi, pj] < best:
                    best, best_steps = acc[pi, pj], steps[pi, pj]
            if best == INF:
                continue
            acc[i, j] = best + cost[i - 1, j - 1]
            steps[i, j] = best_steps + 1

    if acc[t1, t2] == INF or steps[t1, t2] == 0:
        return INF
    return float(acc[t1, t2] / steps[t1, t2])


def subsequence_distance(cost: np.ndarray) -> float:
    """Match the reference against the BEST-FITTING PART of the query.

    Standard DTW forces the whole query to align to the whole reference. A live
    capture is not the whole sign: it also contains the hand rising into
    position and dropping afterwards, because segmentation starts on the first
    movement and ends on the first rest. A reference recorded with manual
    start/stop contains only the sign.

    Comparing those end to end makes DURATION dominate the score -- a 4.1s
    capture of a 0.6s sign matched a long reference of a DIFFERENT sign purely
    because the lengths were alike.

    Here the reference must be matched in full, while the query is free to
    begin and end anywhere: the alignment may start at any query frame
    (acc[i][0] = 0) and finish at any query frame (min over acc[i][T2]). That
    finds the sign inside the capture and ignores what surrounds it.
    """
    t1, t2 = cost.shape
    if t1 == 0 or t2 == 0:
        return INF

    acc = np.full((t1 + 1, t2 + 1), INF, dtype=np.float64)
    steps = np.zeros((t1 + 1, t2 + 1), dtype=np.int32)
    # Free start along the query axis.
    acc[:, 0] = 0.0

    for i in range(1, t1 + 1):
        for j in range(1, t2 + 1):
            best, best_steps = INF, 0
            for pi, pj in ((i - 1, j - 1), (i - 1, j), (i, j - 1)):
                if acc[pi, pj] < best:
                    best, best_steps = acc[pi, pj], steps[pi, pj]
            if best == INF:
                continue
            acc[i, j] = best + cost[i - 1, j - 1]
            steps[i, j] = best_steps + 1

    # Free end along the query axis: take the cheapest full-reference match.
    best = INF
    for i in range(1, t1 + 1):
        if steps[i, t2] > 0:
            value = acc[i, t2] / steps[i, t2]
            if value < best:
                best = value
    return best


# --------------------------------------------------------------- library

class Reference:
    __slots__ = ("name", "sign_code", "sequence", "meta")

    def __init__(self, name: str, sign_code: str, sequence: lm.Sequence, meta: dict):
        self.name = name
        self.sign_code = sign_code
        self.sequence = sequence
        self.meta = meta

    def __repr__(self) -> str:
        return f"<Reference {self.name} {self.sign_code} {len(self.sequence)}f>"


class ReferenceLibrary:
    """Every stored reference sequence, loaded once at startup."""

    def __init__(self, subsequence: bool = True) -> None:
        self.references: list[Reference] = []
        # Find the reference inside the capture rather than end to end.
        self.subsequence = subsequence

    @property
    def sign_codes(self) -> list[str]:
        return sorted({r.sign_code for r in self.references})

    def load_dir(self, directory: Path, allowed: set[str] | None = None) -> int:
        """Load every reference on disk, optionally restricted to `allowed`.

        The database decides which signs are live (v_production_vocabulary).
        Without this filter a sign disabled for being unreliable would still
        compete for every match, and could win one.
        """
        directory = Path(directory)
        if not directory.exists():
            log.warning("Reference directory missing: %s", directory)
            return 0

        loaded = skipped = 0
        for path in sorted(directory.glob("*.npz")):
            try:
                sequence, meta = lm.load(path)
            except ValueError as exc:
                # Extractor version mismatch: refuse rather than score wrongly.
                log.error("Skipping %s - %s", path.name, exc)
                continue
            except Exception as exc:  # noqa: BLE001
                log.error("Could not load %s: %s", path.name, exc)
                continue

            code = str(meta.get("sign_code") or path.stem.rsplit("_ref_", 1)[0])
            if allowed is not None and code not in allowed:
                skipped += 1
                continue
            self.references.append(Reference(path.stem, code, sequence, meta))
            loaded += 1

        if skipped:
            log.info("Ignored %d reference(s) for signs not in the live vocabulary", skipped)
        log.info("Loaded %d reference(s) covering %d sign(s)", loaded, len(self.sign_codes))
        return loaded

    def score(self, query: lm.Sequence, *, p_absent: float = 0.35,
              band_pct: float = 15.0) -> list[tuple[str, float, str]]:
        """Compare a live sequence against every reference.

        Returns (sign_code, distance, reference_name), nearest first.
        """
        if not self.references or len(query) < 2:
            return []

        results: list[tuple[str, float, str]] = []
        for reference in self.references:
            cost = cost_matrix(query, reference.sequence, p_absent)
            distance = (
                subsequence_distance(cost) if self.subsequence
                else dtw_distance(cost, band_pct)
            )
            if distance != INF:
                results.append((reference.sign_code, distance, reference.name))

        results.sort(key=lambda item: item[1])
        return results


# --------------------------------------------------------------- engine adapter

class DtwEngine:
    """Drop-in replacement for StubEngine.

    Implements the same `score(sequence) -> list[Candidate]` contract, so the
    recognition socket and the unknown gate are untouched.
    """

    name = "dtw"

    def __init__(self, library: ReferenceLibrary, p_absent: float = 0.35,
                 band_pct: float = 15.0):
        self.library = library
        self.p_absent = p_absent
        self.band_pct = band_pct
        self.vocabulary: list[str] = library.sign_codes

    def set_vocabulary(self, codes: list[str]) -> None:
        # The enabled vocabulary can be narrower than what is on disk; a sign
        # that is not Reliable + Enabled must never be returned.
        self.vocabulary = codes

    def arm(self, sign_code: str | None, outcome: str | None = None) -> None:
        """No-op. The real engine cannot be told what to see."""

    def score(self, sequence):
        from .recognition import Candidate

        if not isinstance(sequence, lm.Sequence):
            return []

        allowed = set(self.vocabulary) if self.vocabulary else None
        ranked = self.library.score(sequence, p_absent=self.p_absent, band_pct=self.band_pct)

        candidates: list[Candidate] = []
        for code, distance, _name in ranked:
            if allowed is not None and code not in allowed:
                continue
            candidates.append(Candidate(code, float(distance)))
        return candidates
