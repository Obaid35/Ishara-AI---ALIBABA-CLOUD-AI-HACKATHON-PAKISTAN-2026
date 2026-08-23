# Technology Stack — FROZEN

**Status:** frozen on 2026-08-23.
**Rule:** do not substitute a technology without either a **measured failure** or a **documented reason** recorded in [Decision Log](DECISIONS_LOG.md). "I found something newer" is not a reason.

## Frozen stack

| Function | Final choice | Priority |
|---|---|---|
| Live camera | Browser webcam (`getUserMedia`) | P0 |
| Hands / body / face tracking | **MediaPipe Holistic** (Python side) | P0 |
| Day-1 sign recognition | **DTW / reference matching** | P0 |
| Later recognition if more data collected | Small temporal classifier | Only if needed |
| Sign start/end | Motion-based start/end + short reset | P0 |
| Unknown sign | Similarity threshold + separation from 2nd-best | P0 |
| PSL → Urdu sentence | **Local fixed templates** | P0 |
| Urdu speech | **Kokoro-82M Hindi, local** | P0 |
| English speech | **Kokoro-82M English, local** | Optional |
| Doctor → Patient | **Fixed verified PSL videos / buttons** | P0 |
| Doctor Urdu voice input | **Groq `whisper-large-v3-turbo`** | P1 |
| Doctor STT accuracy fallback | Groq `whisper-large-v3` | P1 |
| Offline doctor STT fallback | **faster-whisper `small`, CPU INT8** | P1 fallback |
| LLM sentence generation | **Not used in P0** (future: Groq `openai/gpt-oss-20b`, structured output) | P2 |
| Backend | **Python + FastAPI** | P0 |
| Web UI | **Next.js + React + TypeScript** | P0 |
| Database | **PostgreSQL** | P0 |
| Staff authentication | JWT access token + revocable refresh session | P1 |
| Password hashing | Argon2id (bcrypt acceptable) | P1 |
| Public signup | **None — accounts created by admin** | — |
| Patient authentication | **None — instant access** | Mandatory |
| Main demo internet requirement | **None** | Mandatory |

Scope tiers, roles and routes: [Application Scope](APPLICATION_SCOPE.md). Admin console: [Admin Specification](ADMIN_SPEC.md).

## Runtime topology

Everything below runs on the **single demo laptop**. There is no remote server.

```text
┌─ Browser (Next.js + React + TS) ──────────────────────────┐
│  webcam capture · one-screen UI · Urdu message card       │
│  audio playback · PSL video playback                      │
└──────────────┬────────────────────────────────────────────┘
               │  WebSocket (localhost) — video frames
               │  HTTP    (localhost) — messages, phrases, assets
┌──────────────▼────────────────────────────────────────────┐
│  FastAPI (Python)                                         │
│   MediaPipe Holistic → landmarks                          │
│   segmentation (motion start/end)                         │
│   DTW matching + unknown gate                             │
│   message template lookup                                 │
│   Kokoro (live generation fallback)                       │
│   faster-whisper (offline STT fallback)                   │
└──────────────┬────────────────────────────────────────────┘
               │
     ┌─────────▼─────────┐        ┌──────────────────────┐
     │  PostgreSQL       │        │  Local filesystem    │
     │  metadata only    │        │  assets/audio/*.wav  │
     │                   │        │  assets/psl-videos/  │
     └───────────────────┘        │  models/             │
                                  └──────────────────────┘
```

**Blobs never go in the database.** PostgreSQL stores metadata and references (path + checksum); WAV, MP4 and model files stay on disk. See [Data Model](DATA_MODEL.md).

## Internet dependency map

| Component | Needs internet? |
|---|---|
| Camera | No |
| MediaPipe Holistic | No |
| DTW recognition | No |
| Unknown gate | No |
| Urdu sentence templates | No |
| Urdu speech (pre-generated WAV) | No |
| Urdu speech (live Kokoro fallback) | No |
| Doctor phrase buttons | No |
| Verified PSL video playback | No |
| PostgreSQL | No |
| Doctor voice input via Groq (P1) | **Yes** |
| Doctor voice input via faster-whisper (P1 fallback) | No |

**The entire P0 demo runs with the network adapter disabled.** This must be verified as a QA step, not assumed.

## Layer notes

### 1. Tracking — MediaPipe Holistic

Runs on the Python side per the frozen stack. Extracts left hand (21), right hand (21), pose (33) and face landmarks.

- **Pin the MediaPipe version** in `requirements.txt` and record it in this file once installed. The legacy `mp.solutions.*` Solutions API is deprecated in favour of MediaPipe Tasks; whichever API is used on Day 1 is the one used for the rest of the project, because reference clips and live input **must be processed by the identical extraction path**.
- Landmark indices, ordering and normalisation must be identical for offline reference extraction and live capture. A mismatch here produces silently wrong DTW distances with no error message.

**Contingency (not a substitution):** if localhost frame streaming proves too slow on Day 1 — measured, not assumed — move landmark extraction into the browser using MediaPipe Tasks (JS) and send landmark arrays to FastAPI instead of frames. Landmark indices are the same, so the DTW code does not change. Trigger only on a measured latency failure and log it as a decision.

**Frame transport budget:** downscale to 640×480, JPEG quality ~70, 15–20 fps. Over localhost, bandwidth is not the constraint — Python-side JPEG decode plus MediaPipe inference is. Measure end-to-end latency on Day 1 and record it here.

### 2. Recognition — DTW

Reference/template matching against verified reference clips. Full specification, including the unknown gate, in [Recognition Specification](RECOGNITION_SPEC.md).

We are **not** committing to a temporal classifier before we know our data situation. That change requires evidence from the Day-1 experiment.

### 3. Sentence generation — local templates only

No LLM in P0. A recognised concept sequence maps to a pre-written Urdu string through a lookup table. Deterministic, offline, no hallucination. See [Message Map](MESSAGE_MAP.md).

If a signed sequence has no template, show the recognised concepts — do not invent a sentence.

### 4. Urdu speech — Kokoro-82M, Hindi voices

Kokoro does not officially list Urdu. We use its **Hindi** capability (language code `h`) because spoken medical Urdu and everyday Hindi are phonologically very close. This is a deliberate, disclosed choice — see [Known Limitations](KNOWN_LIMITATIONS.md). We must never claim "Kokoro supports Urdu."

Available Hindi voices: `hf_alpha`, `hf_beta` (female); `hm_omega`, `hm_psi` (male).

**Input is Devanagari, not Urdu script.** Every message therefore carries two text fields:

| Field | Purpose | Shown to user? |
|---|---|---|
| `urdu_text` | displayed on screen | Yes |
| `kokoro_input` | Devanagari pronunciation string fed to Kokoro | No |

Example:

```text
urdu_text     مجھے سینے میں درد ہے۔
kokoro_input  मुझे सीने में दर्द है।
sounds like   Mujhe seenay mein dard hai.
```

`kokoro_input` is authored by hand and **verified by ear** by an Urdu speaker listening to the generated audio. It is not verified by reading the Devanagari. See [Content Guidelines](CONTENT_GUIDELINES.md).

**Day-1 install check:** the Hindi G2P path must actually work. Install and run it on Day 1 — do not discover on Day 4 that a phonemiser dependency (for example `espeak-ng`) is missing. Record the working install steps in this file.

### 5. Urdu speech delivery — pre-generated WAV is P0

The P0 message set is small and closed, so audio is generated **before** the demo and played from disk.

```text
assets/audio/
  headache.wav
  chest_pain.wav
  fever.wav
  cough.wav
  ...
  yes.wav
  no.wav
```

Demo path: PSL recognised → Urdu sentence appears → patient presses **Speak** → **local WAV plays**.

No generation delay. No internet. No missing voice. No pronunciation drifting mid-presentation.

- **Pre-generated Kokoro = P0.**
- **Live Kokoro generation = fallback / stretch**, used only for a sentence with no pre-generated file.

**Regeneration rule:** if `urdu_text` or `kokoro_input` changes, the WAV is stale and must be regenerated and re-checked before the demo. This is enforced by a checksum column — see [Data Model](DATA_MODEL.md).

### 6. Voice selection — decided by blind listening test, not by name

On Day 1, generate the same five Urdu medical sentences with all four Hindi voices, then have 2–3 Urdu speakers listen **blind** and pick the most natural. Kokoro's own model card rates its Hindi voices around grade C, so our own test matters more than the label.

Record the winner here once chosen: `selected_voice: <TBD>`.

### 7. English speech — Kokoro English

If an `اردو | English` toggle is added, English uses Kokoro too. **One TTS system for the whole application.** No second engine.

### 8. Doctor → Patient — buttons are P0, voice is P1

P0 is a grid of verified phrase buttons. Doctor clicks → verified PSL video plays. Reliable, offline, fast, easy to demonstrate.

P1 adds a microphone: doctor speaks Urdu → STT → the text is **matched against the existing approved phrase list** → the verified PSL video plays.

The AI never generates PSL. Voice only *selects* one of our verified questions. That is the whole safety argument.

**Confirm-before-play:** the matched phrase is displayed for the doctor to confirm before the video plays, mirroring confirm-before-speak on the patient side. A misheard question must not silently play the wrong PSL video.

### 9. Doctor STT — Groq primary, local fallback, buttons underneath

```text
Internet available   → Groq whisper-large-v3-turbo
Urdu accuracy poor   → Groq whisper-large-v3
No internet          → faster-whisper small, CPU int8 (~1.5 GB RAM)
Both fail            → doctor clicks the phrase button
```

Turbo is primary because this feature is short, interactive and latency-sensitive. Because the manual buttons always remain on screen, **speech recognition can never kill the demo**.

Matching is against a closed set of ~15 phrases, which is far more forgiving than open transcription. Use normalised fuzzy matching over the phrase list and reject below a match threshold rather than picking the nearest phrase regardless of distance.

### 10. Backend — FastAPI + Python

Recognition, DTW, MediaPipe, Kokoro, faster-whisper and message mapping are all Python work already. There is no reason to force them into Node.

### 11. Frontend — Next.js + React + TypeScript

Webcam, one-screen UI, camera preview, optional tracking overlay, recognised sign, Urdu output, controls, doctor mode, video playback.

### 12. Database — PostgreSQL

Stores: sign metadata and verification status, Urdu/English message mappings, doctor phrase library, PSL video references, audio file references, test results and accuracy records, participant IDs and consent status, and asset/permission tracking. Full schema: [Data Model](DATA_MODEL.md).

**We do not store patient camera or video sessions by default.** There is no table for them.

**Demo-day resilience rule.** PostgreSQL is now a demo dependency, and this project's design principle is that no single dependency can kill the demo. Therefore the backend must be able to boot from a **read-only JSON snapshot** exported from the database:

```text
data/
  signs.json
  messages.json
  doctor_phrases.json
```

The snapshot is exported at feature freeze and re-exported after any content change. If PostgreSQL is unreachable at demo time, the backend loads the snapshot and the demo proceeds read-only. Recording new test results still requires the live database. This is the same pattern as the doctor buttons sitting underneath the STT.

## Local development setup

### Configuration

All configuration is read from environment variables. **No credential is written into any documentation, migration or source file.**

- `.env.example` — committed, placeholders only.
- `.env` — real local values, **gitignored**.

```bash
cp .env.example .env       # then fill in local values
```

Keys: `DATABASE_URL`, `POSTGRES_*`, `JWT_SECRET`, `SEED_ADMIN_EMAIL`, `SEED_ADMIN_PASSWORD`, `KOKORO_VOICE`, `GROQ_API_KEY` (optional — P1 only).

### Database

```bash
createdb psl_bridge
# apply migrations from db/migrations, then seed:
#   roles, initial admin, phrase categories, candidate vocabulary (all disabled)
```

The seeded admin account starts with `must_change_password = true`.

### Credential rules

- The local development password is a **throwaway for a local database on a laptop**. It is not a production credential and must not be reused for anything reachable from a network.
- `JWT_SECRET` and `SEED_ADMIN_PASSWORD` must be changed from their example values before the application is exposed beyond localhost.
- If this project is ever pushed to a public repository, confirm `.env` is not in the history.
- Never commit `.env`, never paste credentials into docs, issues, or the audit log.

### Running

```text
PostgreSQL   localhost:5432
FastAPI      localhost:8000
Next.js      localhost:3000
```

All three on the demo laptop. The P0 demo must work with the network adapter disabled — verify this, do not assume it.

## Version pinning

Fill in on Day 1 and do not change afterwards without a decision entry.

| Component | Version | Recorded on |
|---|---|---|
| Python | | |
| mediapipe | | |
| MediaPipe API used (`solutions` / `tasks`) | | |
| kokoro | | |
| G2P dependency (for example espeak-ng) | | |
| faster-whisper | | |
| fastapi / uvicorn | | |
| Node | | |
| next / react | | |
| PostgreSQL | | |

## Repository structure

```text
PSL-BRIDGE/
├── frontend/          Next.js + React + TypeScript
├── backend/           FastAPI, MediaPipe, DTW, Kokoro, faster-whisper
├── models/            Kokoro + whisper model files (not committed)
├── data/              exported JSON snapshot (demo fallback)
├── assets/
│   ├── audio/         pre-generated Urdu WAV files
│   └── psl-videos/    verified doctor PSL videos
├── db/                migrations + seed
├── experiments/day1/  reference extraction, DTW trials, results
├── tests/
└── docs/
```

## Related documents

- [Application Scope](APPLICATION_SCOPE.md) — scope tiers, roles, routes, settings
- [Admin Specification](ADMIN_SPEC.md) — admin console and verification workflow
- [Recognition Specification](RECOGNITION_SPEC.md) — segmentation and unknown-gate parameters
- [Message Map](MESSAGE_MAP.md) — sign → message → demo traceability
- [Data Model](DATA_MODEL.md) — PostgreSQL schema
- [Offline & Fallback Strategy](OFFLINE_FALLBACK.md)
- [System Architecture](SYSTEM_ARCHITECTURE.md)
