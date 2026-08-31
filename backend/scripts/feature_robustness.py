"""Does the feature representation survive a different signer?

    python scripts/feature_robustness.py

The live test showed a real person scoring 2-3x worse against the dictionary
references than the references score against each other. The suspicion is that
absolute hand positions are too brittle: hold the hand slightly lower on the
chest and every one of the 21 points contributes error, even though the sign is
performed correctly.

This applies synthetic perturbations that imitate what actually differs between
two people performing the same sign, and reports how much the distance grows:

    placement   the hand sits a little higher / lower / further out
    hand size   larger or smaller hands making the same shape
    speed       the same sign performed faster or slower
    jitter      landmark detection noise

A representation that generalises should barely move under placement and hand
size, because neither changes the sign. Distances are reported as a multiple of
the unperturbed self-distance, so lower is better.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402

from app.services import landmarks as lm  # noqa: E402
from app.services.dtw import cost_matrix, dtw_distance  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
SEQ_DIR = REPO / "experiments" / "day1" / "references"

P_ABSENT = 0.35
BAND = 25.0


def score(a: lm.Sequence, b: lm.Sequence) -> float:
    return dtw_distance(cost_matrix(a, b, P_ABSENT), BAND)


def shift_placement(seq: lm.Sequence, dx: float, dy: float) -> lm.Sequence:
    """Move where the hand sits on the body, leaving the handshape alone."""
    out = seq.features.copy()
    for anchor in (lm.LEFT_ANCHOR, lm.RIGHT_ANCHOR):
        out[:, anchor.start] += dx
        out[:, anchor.start + 1] += dy
    return lm.Sequence(out, seq.left_present.copy(), seq.right_present.copy(), seq.fps)


def resize_hand(seq: lm.Sequence, factor: float) -> lm.Sequence:
    """A bigger or smaller hand making the same shape."""
    out = seq.features.copy()
    for shape in (lm.LEFT_SHAPE, lm.RIGHT_SHAPE):
        out[:, shape] *= factor
    return lm.Sequence(out, seq.left_present.copy(), seq.right_present.copy(), seq.fps)


def change_speed(seq: lm.Sequence, factor: float) -> lm.Sequence:
    """The same sign performed faster or slower."""
    n = len(seq)
    target = max(4, int(round(n * factor)))
    src = np.linspace(0, n - 1, n)
    dst = np.linspace(0, n - 1, target)
    features = np.empty((target, lm.FEATURE_DIM), dtype=np.float32)
    for d in range(lm.FEATURE_DIM):
        features[:, d] = np.interp(dst, src, seq.features[:, d])
    idx = np.clip(np.round(dst).astype(int), 0, n - 1)
    return lm.Sequence(features, seq.left_present[idx], seq.right_present[idx], seq.fps)


def add_jitter(seq: lm.Sequence, sigma: float, rng: np.random.Generator) -> lm.Sequence:
    out = seq.features + rng.normal(0.0, sigma, seq.features.shape).astype(np.float32)
    return lm.Sequence(out.astype(np.float32), seq.left_present.copy(),
                       seq.right_present.copy(), seq.fps)


def main() -> None:
    paths = sorted(SEQ_DIR.glob("*.npz"))
    if not paths:
        raise SystemExit("No references found. Run scripts/extract_references.py first.")

    sequences: dict[str, lm.Sequence] = {}
    for path in paths:
        try:
            sequences[path.stem], _ = lm.load(path)
        except ValueError as exc:
            raise SystemExit(f"{path.name}: {exc}")

    print(f"\n  extractor: {lm.EXTRACTOR_VERSION}")
    print(f"  {len(sequences)} references\n")

    rng = np.random.default_rng(7)
    perturbations = [
        ("hand 0.10 lower",      lambda s: shift_placement(s, 0.0, 0.10)),
        ("hand 0.20 lower",      lambda s: shift_placement(s, 0.0, 0.20)),
        ("hand 0.15 out",        lambda s: shift_placement(s, 0.15, 0.0)),
        ("hand 25% bigger",      lambda s: resize_hand(s, 1.25)),
        ("hand 25% smaller",     lambda s: resize_hand(s, 0.80)),
        ("30% faster",           lambda s: change_speed(s, 0.70)),
        ("40% slower",           lambda s: change_speed(s, 1.40)),
        ("landmark jitter",      lambda s: add_jitter(s, 0.02, rng)),
    ]

    print(f"  {'perturbation':22} {'mean distance':>14} {'worst':>8}")
    print(f"  {'-' * 22} {'-' * 14} {'-' * 8}")

    for label, fn in perturbations:
        values = []
        for seq in sequences.values():
            values.append(score(fn(seq), seq))
        values = [v for v in values if np.isfinite(v)]
        if values:
            print(f"  {label:22} {np.mean(values):14.4f} {max(values):8.4f}")

    # For scale: how far apart are genuinely different signs?
    codes = {name: name.rsplit("_ref_", 1)[0] for name in sequences}
    same, diff = [], []
    names = list(sequences)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            d = score(sequences[a], sequences[b])
            if not np.isfinite(d):
                continue
            (same if codes[a] == codes[b] else diff).append(d)

    print()
    if same:
        print(f"  same sign, different take   mean {np.mean(same):.4f}  max {max(same):.4f}")
    if diff:
        print(f"  genuinely different signs   mean {np.mean(diff):.4f}  min {min(diff):.4f}")
    print()
    print("  A perturbation that stays well below the different-sign minimum is")
    print("  survivable. One that reaches it will be rejected or confused, and")
    print("  that is what a new signer runs into.")


if __name__ == "__main__":
    main()
