# Decision Log

## Planning decisions

### D001 — Healthcare only
Focus the product on basic healthcare communication.

### D002 — One-screen communication interface
The communication screen has no sidebar, no nested navigation and no required scroll. **Amended by D019:** the application may have login and admin pages; the communication screen itself stays one-screen.

### D003 — Urdu primary
Urdu text and speech first; English optional.

### D004 — Theme
Primary `#017A3A` with white and soft neutral green.

### D005 — Existing PSL videos first
Day 1 tests the cheapest bootstrap path before a large custom recording effort.

### D006 — One/few examples are not a normal training dataset
Use reference matching and augmented-reference testing rather than pretending one clip provides real signer diversity. Augmented references are never counted as signer diversity.

### D007 — Day-1 denominator
5 signs × 10 attempts × 2 people = 100 live trials.

### D008 — Recruit volunteers before failure
Avoid losing Day 2 waiting for people.

### D009 — Reliability over count
15 reliable signs first. Expand only after validation. Only `Reliable + Enabled` signs are counted publicly.

### D010 — Confirm before speak
The patient controls outbound speech, regardless of recognition confidence.

### D011 — Unknown is mandatory
The system can refuse to classify.

### D012 — Doctor direction uses fixed verified PSL
No unrestricted doctor → PSL generation.

### D013 — No unverified team-created medical PSL
Remove a doctor phrase if it cannot be verified.

### D014 — Backup demo video
Record full successful consultation before final day.

### D015 — Pain concepts need language verification
Do not assume a universal standalone `PAIN` sign or an English-style `HEAD + PAIN` composition.
**Follow-up:** owned by the PSL/Data lead, due end of Day 2. A pain-free fallback P0 message set exists — see D024.

### D016 — Full sign movement
Reference clips include movement start through completion, not only the final hand pose.

## Stack freeze — 2026-08-23

### D017 — Technology stack frozen
The stack in [Technology Stack](TECH_STACK.md) is frozen: MediaPipe Holistic, DTW, local templates, Kokoro, fixed PSL videos, FastAPI, Next.js, PostgreSQL.

**No substitution without a measured failure or a documented reason recorded here.** "I found something newer" is not a reason.

### D018 — Patient requires no account
The communication screen is usable without authentication. A Deaf patient arriving in pain must not face account → email → password → OTP. This is an accessibility and emergency-use decision, not a deferral.

### D019 — The application has staff login and an admin console
Amends D002. Doctor, nurse/staff and admin roles authenticate; an admin console manages verified content. **No public signup** — accounts are created internally.

The communication interface remains one clean single-screen experience. Admin pages are conventional data screens and may scroll.

### D020 — PostgreSQL is the system of record
Replaces the earlier "no database for the hackathon" position. Stores signs, messages, doctor phrases, asset and permission tracking, test results, participants and consent, users, settings and audit logs.

**No patient records. No stored consultation transcripts. No stored camera sessions.**

### D021 — JSON snapshot fallback for the database
Because PostgreSQL is now a demo dependency, the backend must boot read-only from an exported `data/*.json` snapshot if the database is unreachable. Same pattern as the doctor buttons sitting under the STT: no single dependency can kill the demo.

### D022 — No LLM in P0 sentence generation
Recognized concepts map to pre-written, reviewed Urdu strings through a lookup table. Deterministic, offline, no hallucination. An LLM is P2 only, constrained to communication output, and never given diagnostic freedom.

### D023 — Urdu speech uses Kokoro Hindi voices, pre-generated
Kokoro does not officially support Urdu. We use its Hindi capability because spoken medical Urdu and everyday Hindi are phonologically close. **We never claim "Kokoro supports Urdu"** — it is disclosed as a limitation.

P0 audio is **generated before the demo and played from local WAV files**. Live generation is the fallback. This removes generation delay, internet dependency, missing-voice failure and mid-demo pronunciation drift.

Voice is chosen by **blind listening test** on Day 1 across `hf_alpha`, `hf_beta`, `hm_omega`, `hm_psi` — not by name.

### D024 — A pain-free P0 message set exists
Because D015 is unresolved, the ten P0 messages have an alternative set containing no pain concept (fever, cough, vomiting, dizziness, weakness, breathing, bleeding, injury, allergy, help). The demo's symptom step swaps `CHEST_PAIN` → `FEVER`. **The demo survives the pain concepts failing verification.**

### D025 — The unknown gate has two conditions
Absolute quality (`d₁ ≤ τ_accept`) **and** separation from the best **different-label** candidate (`(d₂−d₁)/d₁ ≥ δ_margin`).

The runner-up must carry a different sign code. Comparing a sign against its own other reference clips would make the margin test silently useless.

### D026 — Thresholds are frozen before the unseen-person test
Tuning on the unseen person's data destroys the only strong validation the project has. Changing them afterwards voids that T4 result and must be logged here.

### D027 — One completed motion, at most one decision
The recognizer never emits a label per frame.

### D028 — Per-sign threshold overrides may only be stricter
A sign that passes only with a loosened threshold is Weak and is removed.

### D029 — Confirm-before-play on the doctor side
When doctor voice input is used, the matched phrase is shown for confirmation before the PSL video plays — mirroring confirm-before-speak. A misheard question must not silently play the wrong verified video.

### D030 — Doctor STT can never break the demo
Groq Turbo primary → Groq Large V3 for accuracy → local faster-whisper offline → manual phrase buttons. The buttons always remain on screen.

### D031 — The 15-sign freeze list is derived from the P0 messages and the demo script
Not chosen by convenience. `DOCTOR` and `HOSPITAL` are excluded because no P0 message uses them. Seven signs are demo-critical. See [Message Map](MESSAGE_MAP.md).

### D032 — Content safety is enforced in the schema
A message cannot be enabled unless every sign it needs is `Reliable + Enabled`; a doctor phrase cannot be enabled without PSL verification and demo permission; audio with a stale checksum cannot be played. Encoded as database invariants so they survive deadline pressure.

### D033 — Session history is temporary
Shown during a consultation, cleared at session end. No `conversations` table. Persisting transcripts would require a retention policy, a consent flow and a fresh privacy review.

### D034 — Configuration lives in environment variables
`.env.example` is committed with placeholders; `.env` holds real values and is gitignored. No credential is written into documentation, migrations or source.

### D035 — Landmark extraction runs on the Python side
Frames are streamed to FastAPI over a localhost WebSocket.

**Documented contingency:** if Day-1 measurement shows the latency is unacceptable, extraction moves to the browser via MediaPipe Tasks (JS) and landmark arrays are sent instead. Landmark indices are identical, so DTW is unchanged. This is a pre-approved contingency, and taking it must be recorded here with the measurement that triggered it.

### D036 — Build order is Tier A first
Communication core end-to-end and stable on a second person **before** login, admin or polish. A polished admin console attached to an unreliable recognizer is a failed project.

## How to add a decision

New entries are appended with the next `D0xx` number, a one-line title, and the reason. A decision that reverses an earlier one **amends it in place** with a pointer, as D019 does to D002 — never silently contradicts it.
