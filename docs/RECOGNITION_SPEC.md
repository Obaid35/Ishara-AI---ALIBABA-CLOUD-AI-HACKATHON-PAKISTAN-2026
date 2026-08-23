# Recognition Specification

Operational specification for the three safety-critical behaviours that every other document refers to but none previously defined: **sign segmentation**, **DTW matching**, and the **unknown gate**.

Stack context: [Technology Stack](TECH_STACK.md). Every parameter below has an initial value and a Day-1 calibration procedure. Initial values are starting points, not measurements.

## Governing principle

> **Unknown is better than confidently wrong.**

Every threshold decision in this document resolves ties in favour of refusing to classify. A wrong medical sentence spoken aloud is the worst outcome this system can produce; an unnecessary "please repeat" is a minor inconvenience.

## 1. Feature representation

### Landmarks used

| Source | Points | Values | Dims |
|---|---|---|---|
| Left hand | 21 | x, y | 42 |
| Right hand | 21 | x, y | 42 |
| Pose subset: nose, both shoulders, both elbows, both wrists | 7 | x, y | 14 |
| **Total per frame** | | | **98** |

MediaPipe `z` is not used in P0 — it is unreliable from a single camera and adds noise to the distance function. Face landmarks beyond the nose are not used in P0; if a verified sign turns out to require a non-manual marker, that sign is documented as needing face features before it can be added.

### Normalisation — the part that decides unseen-person transfer

Raw landmark coordinates encode the signer's body size, position and distance from the camera. Matching on raw coordinates will match the *person*, not the *sign*. Every frame is therefore normalised:

1. **Translate:** origin = midpoint between the two shoulders.
2. **Scale:** divide by shoulder width, so shoulder width = 1.0 unit.
3. Retain the sign of coordinates; do not mirror (see below).

This removes camera distance, body size and frame position. It is the single highest-leverage step for T4 unseen-person performance.

### Missing hands

A one-handed sign leaves 42 dims undetected. Do **not** fill them with zeros — zero is a valid coordinate and creates a phantom hand at the shoulder midpoint.

- Each hand carries a `present` flag.
- Distance is computed only over dimension blocks present in **both** frames being compared.
- A fixed penalty `P_absent` is added when one frame has a hand and the other does not, so that a one-handed performance does not match a two-handed reference for free.

| Parameter | Initial value | Calibrate |
|---|---|---|
| `P_absent` | 0.35 per absent hand block | Day 1 |

### Mirroring

Mirroring is **not** applied automatically. Left- and right-handed performances of the same sign are treated as separate reference clips unless a PSL reviewer confirms the sign is handedness-neutral. Automatic mirroring can change meaning and is a linguistic decision, not a data-augmentation decision (see D006, D015).

## 2. Segmentation — one motion, one decision

```text
READY
  ↓  motion energy rises above θ_start for k_start frames
CAPTURING
  ↓  motion energy falls below θ_end for k_end frames
ANALYZE
  ↓
RECOGNIZED / UNKNOWN
  ↓  refractory period
READY
```

**Motion energy** for frame *t*:

```text
m_t = mean over present hand landmarks of || p_t − p_(t−1) ||
```

measured in normalised units (shoulder widths), so it is body-size independent like the features.

| Parameter | Initial value | Meaning |
|---|---|---|
| `θ_start` | 0.020 / frame | motion energy to begin capture |
| `k_start` | 3 frames | consecutive frames above `θ_start` |
| `θ_end` | 0.010 / frame | motion energy to end capture |
| `k_end` | 8 frames (~250 ms @ 30 fps) | consecutive frames below `θ_end` |
| `T_min` | 400 ms | shorter capture is discarded, not classified |
| `T_max` | 3000 ms | longer capture aborts → "please sign again" |
| `T_refractory` | 600 ms | after a decision, before returning to READY |

`θ_end < θ_start` deliberately — hysteresis prevents flicker at the threshold boundary.

### Hard rules

- **One completed motion produces at most one sign decision.** The system must never emit a label per frame. `PAIN PAIN PAIN PAIN` is a defect, not a confidence signal.
- A capture shorter than `T_min` is **discarded silently** — it is incidental movement, not a sign, and must not produce an "unknown" prompt for every scratch of the nose.
- A capture longer than `T_max` aborts with an explicit retry instruction rather than being truncated and classified.
- If no hand is detected at any point during the capture, the segment is discarded, not classified.

## 3. DTW matching

For a captured sequence *Q* and each stored reference *R*:

- **Per-frame cost:** Euclidean distance over the shared present dimension blocks, plus `P_absent` per mismatched hand block.
- **Path constraint:** Sakoe–Chiba band, width = 15% of `max(|Q|, |R|)`. This prevents pathological warps that align a short gesture to a long one.
- **Length normalisation:** the accumulated cost is divided by the warping path length, giving a mean per-step distance `d`. Without this, longer signs are systematically penalised and the thresholds cannot be shared across the vocabulary.

Result: a ranked list of `(reference_id, sign_code, d)`, lowest `d` first.

| Parameter | Initial value | Calibrate |
|---|---|---|
| Sakoe–Chiba band width | 15% | Day 1 |
| Frame rate normalisation | resample to 30 fps | Day 1 |

### Similarity for display

The gate decides on `d` (lower is better). The UI shows a similarity value for human readability:

```text
s = exp(−d / σ)
```

with `σ` chosen on Day 1 so that a typical correct match lands near 0.85–0.90. `s` is a **display convenience only**. No decision is ever made on `s`.

## 4. The unknown gate

Two independent conditions. **Both** must pass for a sign to be accepted.

### Condition A — absolute quality

```text
d₁ ≤ τ_accept
```

The best match must be good in absolute terms. Without this, a completely unrelated movement is still "closest to" something and would be accepted.

### Condition B — separation from the runner-up

```text
(d₂ − d₁) / d₁  ≥  δ_margin
```

where **`d₂` is the best-scoring reference carrying a *different* sign code than `d₁`.**

This detail is mandatory. A sign with three reference clips will usually have its own other clips ranked second, third and fourth. Comparing against the raw second-place entry would compare a sign to itself, the margin would always look excellent, and Condition B would silently do nothing. The runner-up must be a genuine competing *label*.

| Parameter | Initial value | Calibrate |
|---|---|---|
| `τ_accept` | TBD from Day-1 data | Day 1, before T4 |
| `δ_margin` | 0.15 (15% relative separation) | Day 1, before T4 |

### Outcomes

| Condition A | Condition B | Result | UI |
|---|---|---|---|
| pass | pass | **Recognised** | green + concept + Urdu |
| pass | fail | **Unknown — ambiguous** | amber, "please repeat the sign" |
| fail | — | **Unknown — no match** | red, "sign not recognised" |

Worked example, using the shape from the frozen decisions:

```text
Best:    FEVER  0.84      Second (different label):  HELP  0.51   → accept
Best:    FEVER  0.61      Second (different label):  HELP  0.59   → do not guess
```

The second case is exactly the situation where a naive top-1 classifier speaks a wrong medical sentence.

### Never

- Never accept the top-1 result merely because it is top-1.
- Never lower a threshold to make a live demo look better. Thresholds are frozen (below).
- Never let an unrecognised movement add a concept to the message.
- Never speak anything as a result of recognition alone — speech requires the patient's explicit confirmation regardless of confidence (D010).

## 5. Calibration procedure

Run after the Day-1 100-trial experiment ([Day-1 Experiment](DAY1_EXPERIMENT.md)), using the recorded distances from those trials.

1. For every trial, store `d₁`, the top-1 label, `d₂` (best different label), and the ground-truth label.
2. Split trials into **correct top-1** and **incorrect top-1**.
3. Plot the `d₁` distributions for both groups, and the margin distributions for both.
4. Choose `τ_accept` and `δ_margin` to **minimise wrong-accepts first**, then maximise correct-accepts.

### Operating point

The objective is asymmetric on purpose:

| Metric | Target |
|---|---|
| Wrong sign accepted | **≤ 2%** of trials — hard constraint |
| Correct sign accepted | as high as possible subject to the above |
| Unknown / retry rate | up to ~20% is acceptable |

A system that says "please repeat" one time in five and is almost never wrong is the correct product. A system that is right 90% of the time and confidently wrong 10% of the time is not acceptable for medical communication.

Report unknowns and wrongs as **separate numbers**, never merged into one accuracy figure ([Testing Plan](TESTING_PLAN.md)).

## 6. Threshold freeze rule

> **`τ_accept` and `δ_margin` are frozen before the T4 unseen-person test begins.**

Tuning thresholds on the unseen person's data destroys the only strong validation result the project has — the person is no longer unseen. If a threshold is changed after T4 for any reason:

1. the previous T4 result is void;
2. the change is recorded in [Decision Log](DECISIONS_LOG.md);
3. T4 is re-run with a different person, or the result is reported as tuned-on-test and labelled as such.

Frozen values, once set, are recorded here and mirrored into the `recognition_config` table ([Data Model](DATA_MODEL.md)):

```text
tau_accept:   <TBD>
delta_margin: <TBD>
frozen_on:    <TBD>
frozen_by:    <TBD>
```

## 7. Per-sign overrides

Some signs are intrinsically harder to separate (see the high-risk confusion list in [Vocabulary Strategy](VOCABULARY_STRATEGY.md): YES/NO, one/two/three, body locations, mild/severe).

A sign may carry a stricter `delta_margin_override`. A sign may **never** carry a looser one — loosening is how a weak sign sneaks into the demo. A sign that only passes with a loosened threshold is a **Weak** sign and is removed (D009).

## 8. Error and degraded states

Each needs a defined next action ([Application Architecture](APPLICATION_ARCHITECTURE.md)):

| Condition | Behaviour |
|---|---|
| No camera permission | explain, offer retry, do not proceed silently |
| Camera unavailable | explain, offer device selection |
| No hands detected during capture | discard segment, stay READY |
| Landmark tracking drops mid-sign | abort segment, "please sign again" |
| Capture exceeds `T_max` | abort, "please sign again" |
| Recognition backend unreachable | explicit status, disable Speak, doctor mode still works |
| No reference clips loaded | explicit startup failure, never an empty vocabulary that silently returns unknown for everything |

## 9. What this specification does not cover

- Continuous multi-sign segmentation without pauses — out of scope, see [Roadmap](ROADMAP.md) Phase 2.
- Any temporal classifier. If Day-1 evidence justifies one, it is specified in a new document and this file records the handover.
- Non-manual markers (facial grammar). Noted as a limitation, not implemented in P0.
