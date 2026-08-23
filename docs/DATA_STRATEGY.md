# Data Strategy

## Principle

> **Existing PSL videos first. Additional recordings only when evidence says they are needed.**

# Source 1 — Existing dictionary videos

Use for:
- sign discovery and verification/reference;
- Day-1 bootstrap experiment;
- doctor-side playback only where permission allows.

Limitations:
- one/few signers;
- one/few performances;
- controlled conditions;
- no guarantee of generalization.

# Source 2 — Augmented variants

Purpose: create small variation around a reference performance.

Examples: speed change; scale; position shift; small noise; safe mirroring only.

**Limitation: this does not replace different people.** Augmented references are stored with `is_augmented = true` and are **never counted as signer diversity** (D006). Mirroring is a linguistic decision, not a data one — apply it only where a reviewer confirms the sign is handedness-neutral.

# Source 3 — Targeted new recordings

Trigger:
- live generalization is weak;
- specific signs confuse;
- new-person testing is poor.

Improve weak signs first instead of automatically recording everything.

# Full fallback dataset

If dictionary bootstrap clearly fails:
- 5 people;
- 15–30 signs;
- roughly 10 repetitions each.

Approximate scale:
- 15 signs ≈ 750 performances;
- 30 signs ≈ 1,500 performances.

# Recording principles

- verify the sign first;
- capture full movement, start through completion;
- keep face when relevant;
- upper body and hands visible;
- allow normal indoor variation;
- reject wrong/partial attempts.

# Participant split

Keep at least one person **unseen** for final testing. Marked `is_unseen` on the participant record — the T4 population must be identifiable, not remembered.

# Landmark artefacts

Every reference clip produces an extracted landmark sequence stored alongside it, with:

- `landmark_path` and checksum;
- **`extractor_version`** — MediaPipe version and API;
- frame count and source fps;
- participant (null for dictionary sources);
- `is_augmented`.

`extractor_version` matters more than it looks. Reference clips and live input must be processed by the **identical** extraction path; a mismatch produces silently wrong distances with no error. If the extractor changes, every reference must be re-extracted, and this column is what makes that detectable.

# Naming convention

`SIGNCODE_P03_R07` — sign, participant, repetition. Participant codes match the `test_participants` table.

# Rights

Tracked per asset as four **independent** permissions, not one flag:

- development;
- internal testing;
- demo playback;
- public release.

They are separate because they are genuinely separate. Helping the project does not imply consent to public release, and viewing a public video does not imply the right to redistribute it.

A reference clip may be used in development only if `permitted_development = true` (invariant I6). A doctor video may be shown only if `permitted_demo_playback = true` (I2). This is enforced by the database, not by memory.

# What is never collected

- Patient identity — there is no patient record.
- Patient camera footage — frames and landmarks are processed in memory and discarded.
- Consultation transcripts — session history is temporary and never written to disk.
- Participant names or contact details — participants are codes.
