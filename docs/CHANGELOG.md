# Changelog

## 2026-08-23 — Stack freeze and application scope

### Added
- **Technology stack frozen** (D017): MediaPipe Holistic, DTW, local templates, Kokoro, fixed PSL videos, FastAPI, Next.js, PostgreSQL. Substitution requires a measured failure or a documented reason.
- **Recognition specification**: feature representation with shoulder-width normalisation, motion-energy segmentation with hysteresis, DTW parameters, and the two-condition unknown gate with a calibration procedure and operating point.
- **Data model**: PostgreSQL schema covering signs, variants, references, messages, doctor phrases, assets, rights, participants, consent, test results, per-trial distances, thresholds, users, settings and audit logs — with eight enforced content invariants.
- **Message map**: sign → message → demo traceability, the 15-sign freeze list, the P0 ten for both libraries, and a demo coverage check.
- **Application scope**: scope tiers A/B/C, roles and permissions, routes, settings, session history.
- **Admin specification**: dashboard, content management, sign verification workflow, testing records, assets and permissions, users, audit log.
- Staff authentication with roles; **no public signup**; patient requires no account (D018, D019).
- PostgreSQL as system of record (D020), with a read-only JSON snapshot fallback (D021).
- Pre-generated Kokoro audio as the P0 speech path (D023), with a by-ear verification step and a checksum staleness guard.
- Pain-free fallback P0 message set (D024), so the demo survives unresolved pain-concept verification.
- Doctor voice input as P1 with confirm-before-play (D029) and a four-level fallback chain (D030).
- `.env.example` and `.gitignore`; configuration via environment variables (D034).
- Degraded-mode indicator so fallback paths are never silent.
- Offline dry run with networking disabled as an acceptance criterion.

### Changed
- D002 amended by D019 — the application may have login and admin pages; the communication screen stays one screen.
- Vocabulary freeze moved to end of Day 5 so rehearsal is not competing with sign removal.
- Day-1 sign set now drawn from the freeze list (`YES` `NO` `HELP` `FEVER` `COUGH`); `DOCTOR` dropped as unused by any P0 message.
- Both content libraries now mark which ten items are P0 — previously both listed fifteen against a requirement of ten.
- Duration combinations bounded to demo-critical pairs to avoid a 60-message content explosion.
- Urdu speech risk downgraded from "test the browser voice early" to a solved problem; audio **staleness** identified as the real remaining risk.
- Risk register restructured, with admin/auth work displacing recognition work added as a critical schedule risk.
- Project status rewritten as a fillable tier-based tracker rather than an empty template.

### Corrected
- The unknown gate's runner-up must carry a **different sign code** (D025). Comparing against a sign's own other reference clips would have made the margin test silently useless.
- Missing hands are masked with a penalty rather than filled with zeros, which would place a phantom hand at the shoulder midpoint.
- Per-sign threshold overrides may only be **stricter** (D028).
- Reference clips and live input must share an identical extraction path; `extractor_version` is recorded so a mismatch is detectable rather than silently wrong.
- Augmented references are explicitly flagged and never counted as signer diversity.

## Planning baseline

### Added
- healthcare-only scope;
- one-screen communication interface;
- Patient → Doctor live recognition;
- Doctor → Patient verified PSL playback;
- Urdu-first output;
- `#017A3A` + white theme;
- unknown/retry;
- confirm-before-speak;
- existing-video-first experiment;
- 100-trial denominator;
- early volunteer recruitment;
- 15-reliable-sign-first philosophy;
- unseen-person testing;
- 9/10 demo target;
- backup demo video;
- privacy/permission and PSL verification requirements.

### Corrected
- one video per sign is not treated as a normal diverse training dataset;
- `PAIN` composition is not assumed without PSL verification;
- large custom recording dataset is Plan B, not the automatic first step;
- vocabulary count no longer outranks reliability.
