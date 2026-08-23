# Changelog

## 2026-08-23 — Application built

Frontend, backend and database implemented against the frozen stack. Model-backed
pieces (MediaPipe, Kokoro, Whisper) deliberately left as labelled stubs.

### Added
- **PostgreSQL schema** — 20 tables, 8 enums, migrations in `db/migrations`, with
  a minimal runner (`python -m app.migrate`).
- **Content-safety invariants enforced in the database** — I1 (message needs
  reliable signs), I1 cascade (demoting a sign auto-disables dependent messages),
  I2 (phrase needs verification + demo permission), I4 (stricter overrides only),
  I5 (correct + wrong + unknown = attempts), I6 (reference needs dev permission),
  I7 (one active config). All verified by live test.
- **Reporting views** — `v_production_vocabulary`, `v_demoable_messages`,
  `v_demoable_doctor_phrases`, `v_permission_gaps`, `v_demo_readiness`.
- **FastAPI backend** — auth with revocable sessions, unauthenticated content
  endpoints, speech resolution, STT phrase matching, recognition WebSocket, and
  the full admin API.
- **Next.js frontend** — one-screen communication interface, doctor mode with
  categories and search, staff login, settings, and a seven-page admin console.
- **Recognition socket** — segmentation state machine and the two-condition
  unknown gate, both real and verified against all three outcomes.
- **Audio staleness guard** — editing a message's text blocks playback until the
  audio is regenerated; verified end to end.
- **Snapshot fallback** — the backend boots read-only from `data/*.json` when
  PostgreSQL is unavailable.
- **Launcher scripts** — `setup.bat`, `run.bat`, `dev.bat`, `stop.bat`, `snapshot.bat`.
- `backend/scripts/generate_audio.py` with a `--placeholder` mode so the speech
  pipeline is exercisable before Kokoro is installed.

### Deliberately stubbed
- MediaPipe landmark extraction, DTW scoring, Kokoro generation, Whisper
  transcription. Each sits behind an adapter interface and labels itself: the
  socket sends `engine: "stub"`, the UI shows a *Simulated engine* badge, and
  `/api/health` lists every degradation.

### Fixed during the build
- Migration runner now uses a raw DBAPI cursor — SQLAlchemy passed psycopg2 an
  empty parameter set, which made it treat the `%` format specifiers in the
  PL/pgSQL `RAISE` statements as placeholders.
- Account email validation relaxed from strict RFC checking; hospital staff
  accounts legitimately use internal domains such as `admin@isharaai.local`,
  which `email-validator` rejects as special-use names.
- Next pinned to 15.5.23 with `postcss` and `sharp` forced to patched builds via
  npm `overrides`, clearing all advisories without a major upgrade.

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
