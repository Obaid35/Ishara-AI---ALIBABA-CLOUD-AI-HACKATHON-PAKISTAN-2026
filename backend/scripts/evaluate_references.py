"""Leave-one-out sanity check over the extracted references.

    python scripts/evaluate_references.py

Takes each reference in turn, hides it from the library, and asks: does the
remaining set identify it correctly?

This is test level T1 in docs/TESTING_PLAN.md -- PIPELINE SANITY ONLY. It says
whether extraction, normalisation and DTW are wired up correctly. It says
NOTHING about real-world accuracy, because every sample here comes from the
same signer in the same recording. Do not quote these numbers as accuracy.

The number that matters comes later, from a different person signing live.
"""

from __future__ import annotations

import sys
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402

from app.services import landmarks as lm  # noqa: E402
from app.services.dtw import ReferenceLibrary, cost_matrix, dtw_distance  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
SEQ_DIR = REPO / "experiments" / "day1" / "references"

P_ABSENT = 0.35
BAND_PCT = 15.0


def main() -> None:
    library = ReferenceLibrary()
    count = library.load_dir(SEQ_DIR)
    if count == 0:
        raise SystemExit(
            "No references found. Run scripts/extract_references.py first."
        )

    refs = library.references
    print(f"\n  {count} references covering {len(library.sign_codes)} signs: "
          f"{', '.join(library.sign_codes)}\n")

    # ---------------------------------------------------------- full distance matrix
    n = len(refs)
    matrix = np.full((n, n), np.nan, dtype=np.float64)
    for i, j in combinations(range(n), 2):
        d = dtw_distance(cost_matrix(refs[i].sequence, refs[j].sequence, P_ABSENT), BAND_PCT)
        matrix[i, j] = matrix[j, i] = d

    names = [r.name for r in refs]
    width = max(len(x) for x in names) + 2

    print("  Pairwise DTW distance (lower = more similar)")
    print("  " + " " * width + "".join(f"{k:>8}" for k in range(n)))
    for i, name in enumerate(names):
        row = "".join(
            "     -  " if i == j else f"{matrix[i, j]:8.3f}"
            for j in range(n)
        )
        print(f"  {name:<{width}}{row}   [{i}]")

    # ---------------------------------------------------------- leave-one-out
    print("\n  Leave-one-out identification")
    correct = 0
    evaluated = 0
    margins = []

    for i, ref in enumerate(refs):
        others = [(j, refs[j]) for j in range(n) if j != i]
        if not others:
            continue
        # Only signs that still have a representative can possibly be matched.
        available = {r.sign_code for _, r in others}
        if ref.sign_code not in available:
            print(f"    {ref.name:<{width}} skipped - only sample of this sign")
            continue

        evaluated += 1
        ranked = sorted(((matrix[i, j], r.sign_code, r.name) for j, r in others),
                        key=lambda t: t[0])
        best_d, best_code, best_name = ranked[0]
        rival = next((t for t in ranked[1:] if t[1] != best_code), None)

        hit = best_code == ref.sign_code
        correct += hit

        if rival:
            margin = (rival[0] - best_d) / best_d if best_d > 0 else float("inf")
            margins.append((margin, hit))
            detail = f"d1={best_d:.3f}  d2={rival[0]:.3f} ({rival[1]})  margin={margin:+.1%}"
        else:
            detail = f"d1={best_d:.3f}  (no rival label)"

        mark = "OK " if hit else "MISS"
        print(f"    [{mark}] {ref.name:<{width}} -> {best_code:<14} {detail}")

    # ---------------------------------------------------------- summary
    print()
    if evaluated:
        print(f"  {correct}/{evaluated} identified correctly "
              f"({correct / evaluated:.0%}) -- source-clip sanity only")
    else:
        print("  Nothing evaluated: every sign has only one sample.")

    if margins:
        good = [m for m, hit in margins if hit]
        if good:
            print(f"  Correct-match margin: min {min(good):+.1%}  median "
                  f"{float(np.median(good)):+.1%}  max {max(good):+.1%}")
        bad = [m for m, hit in margins if not hit]
        if bad:
            print(f"  Wrong-match margin:   {', '.join(f'{m:+.1%}' for m in bad)}")

    # ---------------------------------------------------------- separation
    same, diff = [], []
    for i, j in combinations(range(n), 2):
        (same if refs[i].sign_code == refs[j].sign_code else diff).append(matrix[i, j])

    print()
    if same:
        print(f"  Same-sign distance    n={len(same):3}  "
              f"min {min(same):.3f}  mean {float(np.mean(same)):.3f}  max {max(same):.3f}")
    if diff:
        print(f"  Different-sign dist.  n={len(diff):3}  "
              f"min {min(diff):.3f}  mean {float(np.mean(diff)):.3f}  max {max(diff):.3f}")
    if same and diff:
        gap = min(diff) - max(same)
        print(f"\n  Separation gap: {gap:+.3f}  "
              f"(closest different-sign pair minus furthest same-sign pair)")
        if gap > 0:
            suggested = (max(same) + min(diff)) / 2
            print(f"  Every same-sign pair is closer than every different-sign pair.")
            print(f"  A threshold near tau_accept ~ {suggested:.2f} separates them here.")
            print(f"  This is a starting point ONLY. Calibrate from live trials.")
        else:
            print("  Overlap: some different-sign pairs are closer than same-sign pairs.")
            print("  Expect confusions. The unknown gate should refuse these rather")
            print("  than guess -- check which pairs overlap above.")

    print("\n  Reminder: T1 is pipeline sanity, not accuracy. The real test is a")
    print("  different person signing live (T3/T4).")


if __name__ == "__main__":
    main()
