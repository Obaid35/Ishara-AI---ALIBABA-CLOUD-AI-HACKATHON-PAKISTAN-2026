"""Turn PSL dictionary videos into reference samples.

    python scripts/extract_references.py --inspect          # report only, writes nothing
    python scripts/extract_references.py                    # extract all configured videos
    python scripts/extract_references.py --only FEVER

For each source video it:
  1. runs MediaPipe Holistic over every frame,
  2. computes motion energy in shoulder-width units,
  3. finds the distinct sign performances and drops idle / intro / outro,
  4. keeps the COMPLETE movement with a small pad either side,
  5. saves each performance as its own landmark sequence + trimmed clip.

A dictionary clip usually contains the same sign performed two or three times.
Each performance is saved separately -- they are separate references, not one
long sample (docs/DATA_STRATEGY.md).

Nothing here trains anything. These sequences are templates that live signing
is compared against.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import cv2  # noqa: E402
import numpy as np  # noqa: E402

from app.services import landmarks as lm  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
SOURCE_DIR = REPO / "assets" / "psl-videos"
OUT_DIR = REPO / "experiments" / "day1"
SEQ_DIR = OUT_DIR / "references"
CLIP_DIR = OUT_DIR / "clips"

# --------------------------------------------------------------- the 5 Day-1 signs
# Deliberately kept to five. Expand only after live testing (D009).
# Some signs pause mid-performance (a compound sign such as "pain in eye"
# points, pauses, then signs pain). Without a wider merge gap those halves
# are stored as two separate references, which is wrong.
MERGE_GAP_OVERRIDE: dict[str, float] = {
    # Both confirmed by the distance matrix: halves of one performance sit
    # far apart (HELP 01<->02 = 1.04) while matching halves sit very close
    # (HELP 01<->03 = 0.11). That is a compound sign, not repetitions.
    "PAIN_IN_EYE": 1.60,
    "HELP": 1.00,
    # Split into 5 fragments at the default gap; the real performances are two,
    # separated by a 1.18s rest while the fragments within each sit adjacent.
    "HERE_I_AM": 1.00,
    "I_HAVE_A_QUESTION": 0.80,
    "I_HAVE_A_COMPLAINT": 0.60,
}

SOURCES: dict[str, str] = {
    "PAIN_IN_EYE": "pain_in_eye_1680111205_15959.mp4",
    "DOCTOR": "doctor_1622524762_18002.mp4",
    "FEVER": "fever_1621355818_82670.mp4",
    "HELP": "help_1623253688_82961.mp4",
    # Needed for the first real sentence: FEVER + TWO + DAY.
    "TWO": "two_1680119661_32772.mp4",
    "DAY": "day_1619868722_79149.mp4",
    # A whole medical statement in a single sign - the highest-value item in
    # the set, because it needs no sequence to say something useful.
    "I_AM_SICK": "i_am_sick_1669962334_53967.mp4",
    "HERE_I_AM": "Here_I_am_1687445175_26162.mp4",
    "I_HAVE_A_QUESTION": "I_have_a_question_1622731954_64380.mp4",
    "I_HAVE_A_COMPLAINT": "I_have_a_complaint_1666698120_32698.mp4",
    # COUGH removed from the current experiment: its three samples disagreed
    # with each other (0.32-0.83 apart) and ref_03 matched DOCTOR at a +0.1%
    # margin. Revisit with a different source clip after the live 4-sign test.
    # "COUGH": "cough_1621343677_67000.mp4",
}

# Samples excluded by hand after review. FEVER_ref_02 sat 1.2 away from both
# its siblings, which were 0.146 apart -- it is not the same movement.
EXCLUDED_SAMPLES = {"FEVER_ref_02"}

# --------------------------------------------------------------- segmentation
# Offline segmentation is more permissive than the live gate: a dictionary
# signer moves deliberately and pauses between repetitions, so we look for
# sustained activity separated by clear rests.

ACTIVE_QUANTILE = 0.55      # motion above this quantile of non-zero motion = active
ABS_FLOOR = 0.004           # ignore camera noise below this, whatever the quantile says
SMOOTH_WINDOW = 5           # frames, centred moving average
MIN_DURATION_S = 0.45       # shorter than this is not a sign
MAX_DURATION_S = 4.00       # longer is probably two merged performances
MERGE_GAP_S = 0.28          # rests shorter than this belong to one performance
PAD_S = 0.18                # keep a little before the start and after the end


@dataclass
class Segment:
    start: int
    end: int
    fps: float

    @property
    def start_s(self) -> float:
        return self.start / self.fps

    @property
    def end_s(self) -> float:
        return self.end / self.fps

    @property
    def duration_s(self) -> float:
        return (self.end - self.start) / self.fps


def smooth(values: np.ndarray, window: int) -> np.ndarray:
    if window < 2 or values.size < window:
        return values
    kernel = np.ones(window, dtype=np.float32) / window
    return np.convolve(values, kernel, mode="same")


def find_segments(energy: np.ndarray, fps: float,
                  merge_gap_s: float = MERGE_GAP_S) -> list[Segment]:
    """Locate each genuine sign performance in the motion-energy curve."""
    if energy.size == 0:
        return []

    curve = smooth(energy, SMOOTH_WINDOW)
    moving = curve[curve > ABS_FLOOR]
    if moving.size == 0:
        return []

    threshold = max(float(np.quantile(moving, ACTIVE_QUANTILE)) * 0.55, ABS_FLOOR)
    active = curve > threshold

    # contiguous active runs
    runs: list[list[int]] = []
    start = None
    for i, flag in enumerate(active):
        if flag and start is None:
            start = i
        elif not flag and start is not None:
            runs.append([start, i])
            start = None
    if start is not None:
        runs.append([start, len(active)])

    # join runs separated by only a short rest -- one performance often dips
    # briefly mid-sign
    merge_gap = int(round(merge_gap_s * fps))
    merged: list[list[int]] = []
    for run in runs:
        if merged and run[0] - merged[-1][1] <= merge_gap:
            merged[-1][1] = run[1]
        else:
            merged.append(run)

    pad = int(round(PAD_S * fps))
    min_len = int(round(MIN_DURATION_S * fps))
    max_len = int(round(MAX_DURATION_S * fps))

    segments: list[Segment] = []
    for begin, finish in merged:
        if finish - begin < min_len:
            continue
        # Pad outward so the movement's true start and end are inside the clip,
        # never only the final hand pose (D016).
        begin = max(0, begin - pad)
        finish = min(len(energy), finish + pad)
        if finish - begin > max_len:
            finish = begin + max_len
        segments.append(Segment(begin, finish, fps))

    return segments


# --------------------------------------------------------------- video pass

def read_video(path: Path, holistic) -> tuple[lm.Sequence, list[np.ndarray], float]:
    """One pass: decode, run Holistic, keep frames for later clip writing."""
    import mediapipe as mp

    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise SystemExit(f"  [X] Could not open {path.name}")

    fps = capture.get(cv2.CAP_PROP_FPS) or 25.0
    frames: list[lm.Frame] = []
    images: list[np.ndarray] = []
    index = 0

    while True:
        ok, image = capture.read()
        if not ok:
            break
        images.append(image)
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        # VIDEO mode wants a monotonically increasing timestamp in milliseconds.
        timestamp_ms = int(index * 1000 / fps)
        frames.append(lm.process_results(holistic.detect_for_video(mp_image, timestamp_ms)))
        index += 1

    capture.release()
    return lm.build_sequence(frames, fps), images, fps


def write_clip(images: list[np.ndarray], segment: Segment, path: Path, fps: float) -> None:
    if not images:
        return
    height, width = images[0].shape[:2]
    path.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
    for image in images[segment.start:segment.end]:
        writer.write(image)
    writer.release()


# --------------------------------------------------------------- main

def process(code: str, filename: str, make_landmarker, inspect_only: bool,
            merge_gap_s: float = MERGE_GAP_S) -> dict:
    source = SOURCE_DIR / filename
    if not source.exists():
        print(f"  [X] {code}: missing {filename}")
        return {"code": code, "error": "missing source"}

    # A fresh landmarker per video: VIDEO mode requires timestamps to increase
    # monotonically for the lifetime of the instance, and reusing one across
    # clips also lets tracking state bleed between unrelated recordings.
    with make_landmarker() as holistic:
        sequence, images, fps = read_video(source, holistic)

    energy = lm.motion_energy(sequence)
    tracked = int((sequence.left_present | sequence.right_present).sum())
    segments = find_segments(energy, fps, merge_gap_s)

    print(f"\n  {code}  ({filename})")
    print(f"    {len(sequence)} frames @ {fps:.1f} fps, "
          f"hands visible in {tracked} ({tracked / max(1, len(sequence)):.0%})")

    if not segments:
        print("    [!] no sign performance detected - check the video manually")
        return {"code": code, "error": "no segments"}

    print(f"    {len(segments)} performance(s) detected:")
    saved = []
    for index, segment in enumerate(segments, start=1):
        name = f"{code}_ref_{index:02d}"
        peak = float(energy[segment.start:segment.end].max())
        print(f"      {name}   {segment.start_s:5.2f}s - {segment.end_s:5.2f}s  "
              f"({segment.duration_s:.2f}s, peak motion {peak:.4f})")

        if inspect_only:
            saved.append({"name": name, "start_s": round(segment.start_s, 2),
                          "end_s": round(segment.end_s, 2),
                          "duration_s": round(segment.duration_s, 2)})
            continue

        clean = lm.resample(sequence.slice(segment.start, segment.end), target_fps=30.0)
        SEQ_DIR.mkdir(parents=True, exist_ok=True)
        lm.save(
            SEQ_DIR / f"{name}.npz",
            clean,
            sign_code=code,
            source_video=filename,
            start_s=round(segment.start_s, 3),
            end_s=round(segment.end_s, 3),
            source_fps=round(fps, 3),
        )
        write_clip(images, segment, CLIP_DIR / f"{name}.mp4", fps)
        saved.append({
            "name": name,
            "start_s": round(segment.start_s, 2),
            "end_s": round(segment.end_s, 2),
            "duration_s": round(segment.duration_s, 2),
            "frames": len(clean),
            "sequence": f"experiments/day1/references/{name}.npz",
            "clip": f"experiments/day1/clips/{name}.mp4",
        })

    return {
        "code": code,
        "source": filename,
        "source_fps": round(fps, 2),
        "total_frames": len(sequence),
        "hand_visibility": round(tracked / max(1, len(sequence)), 3),
        "samples": saved,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract PSL reference samples.")
    parser.add_argument("--inspect", action="store_true",
                        help="Report detected segments without writing anything.")
    parser.add_argument("--only", help="Process a single sign code.")
    parser.add_argument("--merge-gap", type=float,
                        help="Override the merge gap in seconds, for all signs.")
    args = parser.parse_args()

    import mediapipe as mp
    from mediapipe.tasks.python import BaseOptions
    from mediapipe.tasks.python.vision import (
        HolisticLandmarker,
        HolisticLandmarkerOptions,
        RunningMode,
    )

    targets = {args.only: SOURCES[args.only]} if args.only else SOURCES
    if args.only and args.only not in SOURCES:
        raise SystemExit(f"Unknown sign '{args.only}'. Known: {', '.join(SOURCES)}")

    model = lm.model_path()
    if not model.exists():
        raise SystemExit(
            f"Model bundle missing: {model}\n"
            f"Download it once:\n  curl -L -o \"{model}\" {lm.MODEL_URL}"
        )

    print("Extracting PSL reference samples")
    print(f"  extractor: {lm.EXTRACTOR_VERSION}")
    print(f"  mediapipe: {mp.__version__}")
    print(f"  model:     {model.name} ({model.stat().st_size / 1e6:.1f} MB)")
    if args.inspect:
        print("  MODE: inspect only - nothing will be written")

    options = HolisticLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(model)),
        running_mode=RunningMode.VIDEO,
        min_pose_detection_confidence=0.5,
        min_pose_landmarks_confidence=0.5,
        min_hand_landmarks_confidence=0.5,
    )

    def make_landmarker():
        return HolisticLandmarker.create_from_options(options)

    report = []
    for code, filename in targets.items():
        gap = args.merge_gap if args.merge_gap is not None else             MERGE_GAP_OVERRIDE.get(code, MERGE_GAP_S)
        report.append(process(code, filename, make_landmarker, args.inspect, gap))

    total = sum(len(r.get("samples", [])) for r in report)
    print(f"\n  {total} reference sample(s) across {len(report)} sign(s)")

    if not args.inspect:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        meta = {"extractor_version": lm.EXTRACTOR_VERSION, "mediapipe": mp.__version__,
                "signs": report}
        (OUT_DIR / "extraction_report.json").write_text(
            json.dumps(meta, indent=2), encoding="utf-8")
        print(f"  report: experiments/day1/extraction_report.json")


if __name__ == "__main__":
    main()
