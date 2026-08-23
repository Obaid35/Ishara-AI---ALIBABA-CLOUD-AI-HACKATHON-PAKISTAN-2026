# Testing Plan

## Core philosophy

The important question is not "does the reference clip work?" but **"does a different person perform the sign live and get the right result?"**

Results are recorded in the `recognition_tests` and `recognition_trials` tables ([Data Model](DATA_MODEL.md)) and viewed at `/admin/testing`.

# Test levels

## T1 — Source sanity
Reference clip produces intended label. Pipeline sanity only; **do not report as real-world accuracy.**

## T2 — Live team member
One person performs every sign repeatedly.

## T3 — Second live person
A different person performs every sign.

## T4 — Unseen person
A person not used for tuning performs the sign set. This is the strongest hackathon validation.

**Thresholds must be frozen before T4 begins.** Tuning on this person's data destroys the only strong validation the project has, and voids the result (D026).

## T5 — Normal-room variation
Normal office/classroom light, sitting, standing, slight distance changes, different clothing.

# Per-person matrix

| Sign | P1 | P2 | P3 | Unseen P4 | Notes |
|---|---|---|---|---|---|
| YES | | | | | |
| NO | | | | | |
| HELP | | | | | |
| FEVER | | | | | |
| COUGH | | | | | |
| … | | | | | |

Use:
- ✅ correct
- ❌ wrong
- ? unknown/retry

**Track unknown separately from wrong.** They are different behaviours: one is the safety gate working, the other is the failure it exists to prevent. `correct + wrong + unknown = attempts` is enforced when recording results.

# What gets logged per trial

Ground-truth sign · top-1 label · `d₁` · `d₂` for the best **different** label · accepted or not · outcome.

Per-trial distances are what make threshold calibration possible. Recording only a tally makes the operating point unrecoverable.

# Confusion testing

Record the most common wrong prediction, especially for:

- YES vs NO;
- one vs two;
- body locations;
- severe vs mild;
- emergency/help;
- breathing problem;
- bleeding.

# Operating point

The objective is deliberately asymmetric:

| Metric | Target |
|---|---|
| Wrong sign accepted | **≤ 2%** — hard constraint |
| Correct sign accepted | as high as possible subject to the above |
| Unknown / retry rate | up to ~20% acceptable |

A system that says "please repeat" one time in five and is almost never wrong is the correct product for medical communication. A system that is right 90% of the time and confidently wrong 10% of the time is not.

# Non-recognition testing

Beyond sign accuracy, verify before the demo:

- **audio matches text** for every enabled message — no stale checksums;
- app boots and demos with PostgreSQL stopped;
- **full demo with networking disabled**;
- weak-sign removal auto-disables dependent messages;
- unverified or unpermitted content cannot be enabled;
- admin routes reject non-admin roles server-side;
- patient can use `/` with no login;
- session history clears at session end.

# Reliability rehearsal

Run the exact final demo **10 times**. Target: **9/10 successful without developer intervention**.

Rehearsal begins only after the vocabulary is frozen — you cannot rehearse a fixed demo while signs are still being removed. If below target, reduce vocabulary or simplify the demo; **do not add features**.

# Report honestly

Publish:

- the final denominator;
- reliable sign count from `v_production_vocabulary` only;
- number of people tested;
- the unseen-person result specifically;
- weak signs excluded;
- unknown behaviour as its own number;
- that Urdu speech uses Kokoro **Hindi** voices.

Never quote an unmeasured number, and never quote a percentage without its denominator.
