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

## Local setup

```bash
cp .env.example .env      # fill in local values; .env is gitignored
createdb psl_bridge       # then apply db/migrations and seed
```

Never commit `.env`. See [Technology Stack](docs/TECH_STACK.md) for the full setup and credential rules.

## Non-goals

The product does **not** claim to translate all PSL, understand every regional variant, replace interpreters, diagnose patients, or provide a full hospital-management system. It does not store patient records or consultation transcripts.
