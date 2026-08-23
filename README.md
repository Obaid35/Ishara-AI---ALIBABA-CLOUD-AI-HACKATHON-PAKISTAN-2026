# PSL Bridge

**PSL Bridge** is a healthcare communication application for two-way communication between Pakistan Sign Language (PSL) users and Urdu-speaking medical staff.

## Core experience

- **Patient → Doctor:** a Deaf patient signs live in front of a normal camera; supported PSL signs are recognized and turned into Urdu text and Urdu speech.
- **Doctor → Patient:** the doctor selects a small set of verified medical questions/messages and the corresponding verified PSL video is shown to the patient.
- **Primary target:** reliability on a small, verified healthcare vocabulary.
- **Primary interface:** the communication screen is one screen with no required scrolling on the hackathon laptop.
- **Primary language:** Urdu.
- **Safety boundary:** communication assistance only; no diagnosis or medical advice.

## Project principle

> **Verified and reliable beats large and shaky.**

The initial goal is **15 rock-solid signs**, then expansion only when testing supports it. A 30–40-sign list is a stretch target, not a promise.

## Access model

**The patient never needs an account.** A Deaf patient arriving in pain opens the communication screen and starts signing.

Staff (doctor, nurse, admin) sign in so the application can offer settings, admin content management and an audit trail. There is **no public signup** — accounts are created internally by an admin. See [Application Scope](docs/APPLICATION_SCOPE.md).

## Technology

Frozen on 2026-08-23 — see [Technology Stack](docs/TECH_STACK.md).

| Layer | Choice |
|---|---|
| Web UI | Next.js + React + TypeScript |
| Backend | Python + FastAPI |
| Database | PostgreSQL |
| Tracking | MediaPipe Holistic |
| Recognition | DTW / reference matching + unknown gate |
| Urdu speech | Kokoro-82M (Hindi voices), pre-generated locally |
| Doctor → Patient | Fixed verified PSL videos |
| Doctor voice input (P1) | Groq `whisper-large-v3-turbo`, local faster-whisper fallback |
| Main demo internet requirement | **None** |

**Do not substitute a technology without a measured failure or a documented reason** recorded in the [Decision Log](docs/DECISIONS_LOG.md).

## Day-1 experiment

1. Pick 5 visually distinct, standalone verified signs **that the product actually uses**.
2. Use existing PSL dictionary videos first.
3. Extract the actual complete sign movements.
4. Treat repeated performances in one dictionary clip as separate references.
5. Try direct/reference matching first and an augmented-reference experiment second.
6. Test live with **2 people × 10 attempts × 5 signs = 100 trials**.
7. Decide from evidence whether existing videos are sufficient or additional recordings are required.

Start with [`docs/INDEX.md`](docs/INDEX.md).

## Running it

Windows, from the project folder:

| Script | What it does |
|---|---|
| `setup.bat` | One-time: installs dependencies, creates the database, applies migrations, seeds content, builds the frontend |
| `run.bat` | Checks everything is ready, starts the app, opens the browser |
| `dev.bat` | Same, with hot reload and visible logs |
| `stop.bat` | Stops both servers |
| `snapshot.bat` | Exports the offline demo snapshot to `data/*.json` |

`run.bat` will not start a half-working app. It verifies Python and Node are on
PATH, `.env` exists, `node_modules` and the production build are present
(offering to install or build if not), then runs `backend/scripts/preflight.py`
to check Python packages, database reachability, pending migrations, seeded
content, and stale or missing audio. Each failure names the exact command that
fixes it. It then waits for **both** the API and the web server to answer before
reporting ready, and prints any degraded modes it detects.

Then:

| | |
|---|---|
| Communication screen | http://localhost:3000 |
| Staff sign in | http://localhost:3000/login |
| Admin console | http://localhost:3000/admin |
| API docs | http://localhost:8000/docs |

Sign in with the `SEED_ADMIN_EMAIL` / `SEED_ADMIN_PASSWORD` from your `.env`.
**The patient never signs in** — the communication screen is open to everyone.

Manual equivalent:

```bash
cp .env.example .env                          # .env is gitignored
createdb psl_bridge
cd backend && python -m app.migrate && python -m app.seed --dev-content
cd ../frontend && npm install && npm run build && npm run start
```

Never commit `.env`. See [Technology Stack](docs/TECH_STACK.md) for the full setup and credential rules.

## What is real and what is stubbed

The application, database and safety architecture are built and working. The
three model-backed pieces are **stubs behind adapter interfaces**, clearly
labelled everywhere they appear:

- **Recognition** — the segmentation state machine and the unknown gate are
  real; the DTW scoring is simulated. Every event carries `engine: "stub"` and
  the UI shows a *Simulated engine* badge.
- **Urdu speech** — the pipeline, the staleness guard and playback are real;
  the audio files are placeholder tones until Kokoro is installed.
- **Doctor voice input** — phrase matching is real; transcription is not wired
  up. The phrase buttons are fully functional.

Nothing simulated can be mistaken for recognition. See
[Technology Stack](docs/TECH_STACK.md) for what landing the real models requires.

## Non-goals

The product does **not** claim to translate all PSL, understand every regional variant, replace interpreters, diagnose patients, or provide a full hospital-management system. It does not store patient records or consultation transcripts.
