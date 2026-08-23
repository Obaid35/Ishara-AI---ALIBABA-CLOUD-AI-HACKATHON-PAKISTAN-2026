# Application Architecture

Implementation-level structure. Stack: [Technology Stack](TECH_STACK.md). Scope, roles and routes: [Application Scope](APPLICATION_SCOPE.md).

## Processes

Three processes on one laptop. No remote server.

| Process | Port | Owns |
|---|---|---|
| Next.js frontend | 3000 | UI, webcam capture, playback |
| FastAPI backend | 8000 | MediaPipe, DTW, unknown gate, templates, TTS, STT, content API |
| PostgreSQL | 5432 | content, users, rights, tests, audit |

## Routes

```text
/login                  staff login
/                       PSL communication screen  ← one screen, no scroll
/settings               application settings (admin)
/admin                  dashboard
/admin/signs
/admin/messages
/admin/doctor-phrases
/admin/testing
/admin/assets
/admin/users
```

`/` is reachable **without authentication**. Everything under `/admin` and `/settings` requires an admin role, checked server-side on every request — never only in the UI.

## Backend surface

| Group | Purpose |
|---|---|
| `/api/auth/*` | login, logout, refresh, forgot/reset password |
| `/ws/recognize` | localhost WebSocket — frames in, recognition events out |
| `/api/messages` | enabled messages and their audio references |
| `/api/doctor-phrases` | enabled phrases by category, with PSL video references |
| `/api/speech/*` | audio file resolution; live TTS fallback |
| `/api/stt` | P1 doctor voice → transcription → phrase match candidates |
| `/api/admin/*` | content CRUD, testing records, assets, users, audit |
| `/api/health` | process, database and snapshot-mode status |

Recognition events emitted on the socket: `ready`, `capturing`, `recognized`, `unknown_ambiguous`, `unknown_no_match`, `aborted`.

## Communication-screen state

### Patient mode
- camera ready / unavailable / permission denied
- recognition state: ready / capturing / analyzing / recognized / unknown
- current recognized concept and its Urdu meaning
- accumulated message concepts
- resolved Urdu sentence (or "concepts only" when no template matches)
- speech ready / speaking
- undo / clear / retry availability
- session history (in memory)

### Doctor mode
- phrase categories and search query
- selected phrase
- verified PSL video, play / pause / replay / full-screen
- P1: microphone state, transcription, matched phrase awaiting confirmation
- return to Patient mode

### Shell
- authenticated user and role, or anonymous
- settings
- `+ New Conversation`

## Layout

### Shared header
Brand · mode switch · signed-in staff name · New Conversation · logout. When nobody is signed in, brand and mode switch only — the patient experience does not change with login state.

### Main body — Patient
Left: camera. Right: status, recognized sign, Urdu message, controls.

### Main body — Doctor
Left: PSL video. Right: phrase library with categories and search.

### Footer
Small communication-assistance / non-diagnostic statement.

## Why the communication screen is one screen

- faster to build;
- lower cognitive load;
- suited to clinic/kiosk usage;
- safer live demo;
- all critical controls remain visible.

## No-scroll rule

Header + body + footer fit the demo viewport on `/`. If the doctor phrase library is long, the list scrolls internally — the page does not.

**Admin pages are exempt.** Forcing a data grid into one viewport would be pointless; admin tables scroll and paginate normally.

## Required error recovery

Each needs a clear next action:

- camera permission denied;
- camera unavailable;
- unknown sign;
- landmark tracking lost mid-sign;
- recognition backend unreachable — Speak disabled, doctor mode still works;
- no reference clips loaded — explicit startup failure, never a silent empty vocabulary;
- speech unavailable — fall back to live TTS, then to text only;
- missing or stale doctor video;
- **stale audio** — screen text and audio disagree; playback blocked;
- **database unreachable** — boot read-only from the JSON snapshot and show a persistent snapshot-mode indicator;
- STT unavailable — fall back to manual phrase buttons silently.

## Degraded-mode indicator

When the app is running on the JSON snapshot, or live TTS instead of pre-generated audio, or local STT instead of Groq, the header shows a small persistent indicator. Silent degradation during a judged demo is worse than a visible one — the team must know which path is live without guessing.
