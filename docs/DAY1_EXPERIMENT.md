# Day-1 Experiment

## Purpose

Answer one question early:

> **Can existing PSL dictionary videos bootstrap live recognition well enough to continue without immediately collecting a large custom dataset?**

Do not judge the approach from source-video accuracy. The real test is a different person performing the sign live.

Method and parameters are frozen: MediaPipe Holistic → normalised landmarks → DTW → two-condition unknown gate. See [Recognition Specification](RECOGNITION_SPEC.md).

# Step 0 — Environment (do this first, it blocks everything)

- [ ] Python, FastAPI, MediaPipe installed; **version pinned and recorded** in [Technology Stack](TECH_STACK.md).
- [ ] Kokoro installed and the **Hindi G2P path actually runs** — this is the dependency that bites on Day 4 if skipped now.
- [ ] Camera → backend frame streaming works; **end-to-end latency measured and recorded**. If it is unacceptable, take the pre-approved contingency (D035) and move extraction to the browser.
- [ ] `.env` created from `.env.example`.

# Step 1 — Choose 5 signs

Rules:

- standalone verified concepts;
- visually distinct;
- easy to locate;
- no unresolved linguistic ambiguity;
- **used by an actual P0 message or the demo script** — Day-1 work should advance Day-3 work;
- avoid `PAIN` until its exact PSL representation is verified.

Selected set, from [Message Map](MESSAGE_MAP.md) §6:

| Sign | Used by |
|---|---|
| `YES` | demo answer |
| `NO` | demo answer |
| `HELP` | message 10 |
| `FEVER` | message 4, demo symptom fallback |
| `COUGH` | message 5 |

`YES` and `NO` are included **deliberately** despite being the highest-risk confusion pair. If they cannot be separated, the team must know on Day 1, not Day 5.

`DOCTOR` is excluded — visually distinct, but used by no P0 message.

# Step 2 — Prepare reference clips

For each dictionary video:

- remove intro/outro idle time;
- remove tutorial/movie/spelling footage;
- keep the **entire sign movement**;
- if repeated twice, save each full performance separately;
- keep face + upper body + hands when relevant.

Rule: start just before intentional movement begins and end after it finishes. Do not keep only the final hand pose.

Record `extractor_version` for every extraction. Reference clips and live input **must** be processed by the identical extraction path — a mismatch produces silently wrong distances with no error message.

# Step 3 — Two experiment paths

## A. DTW / reference matching
Compare live movement directly to reference sequences. This is the fastest honest one/few-example test and is the frozen P0 method.

## B. Augmented reference experiment
Create small variants from the motion representation:

- slight speed changes;
- slight scale;
- small position shifts;
- small noise;
- mirroring **only when linguistically safe** — handedness is a language question, not a data question.

**Important:** augmentation does not create new signer diversity. Augmented references are marked as such and never counted as people.

# Step 4 — Live test

Required denominator:

**5 signs × 10 attempts × 2 people = 100 trials**

Person A may help with setup. Person B should not be the person used to tune every threshold.

Log every trial: ground-truth sign, top-1 label, `d₁`, `d₂` for the best **different** label, and the outcome. Without per-trial distances there is nothing to calibrate thresholds against.

# Step 5 — Results

| Sign | Person A /10 | Person B /10 | Total /20 | Unknown | Main confusions |
|---|---:|---:|---:|---:|---|
| YES | | | | | |
| NO | | | | | |
| HELP | | | | | |
| FEVER | | | | | |
| COUGH | | | | | |
| **Total** | | | **/100** | | |

Record **correct, wrong and unknown separately.** Unknown is a designed behaviour, not a failure, and merging it into "wrong" hides the thing the gate is for.

# Step 6 — Internal decision guide

These are project-management thresholds, not scientific claims.

- **~80%+ live:** continue existing-video-first, then test 10–15 signs.
- **~50–80%:** promising; add targeted recordings for weak signs.
- **<~50%:** move rapidly to verified custom recordings.

# Step 7 — Threshold calibration

From the logged trials, choose `τ_accept` and `δ_margin` at the required operating point: **wrong-accepts ≤ 2% first**, then maximise correct-accepts. Up to ~20% unknown is acceptable. Procedure in [Recognition Specification](RECOGNITION_SPEC.md) §5.

# Step 8 — Parallel actions

Run these alongside the experiment so Day 2 is not spent waiting:

- recruit 5–6 possible volunteers **before** results are known;
- send the content permission request;
- **start pain-concept PSL verification** — it is due end of Day 2 and gates the flagship message;
- generate the same five Urdu sentences with all four Kokoro Hindi voices and run the **blind listening test**.

If existing videos work, cancel or reduce recording. If not, people are ready.

## Day-1 success

Day 1 succeeds when the team has an evidence-based data strategy, a measured latency number, a chosen voice, and calibrated thresholds — **even if the answer is "dictionary examples alone are not enough."**

Day 1 does **not** succeed because a login page or a database schema exists. Tier A first (D036).
