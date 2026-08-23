# File Manifest

Total Markdown files: **43**

Navigation lives in [`docs/INDEX.md`](docs/INDEX.md). This file is a flat inventory only.

## Root

- `README.md`
- `MANIFEST.md`

## Documentation

### Foundation
- `docs/PROJECT_CHARTER.md`
- `docs/PRODUCT_SPEC.md`
- `docs/APPLICATION_SCOPE.md`
- `docs/REQUIREMENTS.md`
- `docs/ACCEPTANCE_CRITERIA.md`

### UX and design
- `docs/USER_FLOWS.md`
- `docs/UI_SPEC.md`
- `docs/DESIGN_SYSTEM.md`
- `docs/COLOR_THEME.md`
- `docs/CONTENT_GUIDELINES.md`

### Recognition and data
- `docs/DAY1_EXPERIMENT.md`
- `docs/RECOGNITION_SPEC.md`
- `docs/DATA_STRATEGY.md`
- `docs/VOCABULARY_STRATEGY.md`
- `docs/CANDIDATE_VOCABULARY.md`
- `docs/MESSAGE_MAP.md`
- `docs/MEDICAL_MESSAGE_LIBRARY.md`
- `docs/DOCTOR_RESPONSE_LIBRARY.md`

### Architecture and engineering
- `docs/TECH_STACK.md`
- `docs/SYSTEM_ARCHITECTURE.md`
- `docs/APPLICATION_ARCHITECTURE.md`
- `docs/DATA_MODEL.md`
- `docs/ADMIN_SPEC.md`
- `docs/OFFLINE_FALLBACK.md`

### Testing and quality
- `docs/TESTING_PLAN.md`
- `docs/QA_CHECKLIST.md`
- `docs/RISK_REGISTER.md`
- `docs/KNOWN_LIMITATIONS.md`

### Execution and demo
- `docs/SIX_DAY_PLAN.md`
- `docs/TEAM_ROLES.md`
- `docs/DECISIONS_LOG.md`
- `docs/PROJECT_STATUS.md`
- `docs/DEMO_PLAN.md`
- `docs/JUDGE_QA.md`
- `docs/ROADMAP.md`

### Ethics, permissions and references
- `docs/PRIVACY_ETHICS_PERMISSIONS.md`
- `docs/CONTENT_PERMISSION_REQUEST.md`
- `docs/REFERENCES.md`
- `docs/CONTRIBUTING.md`
- `docs/CHANGELOG.md`
- `docs/INDEX.md`

## Non-Markdown project files

### Configuration
- `.env.example` — configuration template (committed)
- `.env` — local values (**gitignored**, never committed)
- `.gitignore`

### Scripts
- `setup.bat` — one-time setup
- `run.bat` — start the app
- `dev.bat` — start with hot reload
- `stop.bat` — stop both servers
- `snapshot.bat` — export the offline demo snapshot

### Database
- `db/migrations/001_init.sql` — schema
- `db/migrations/002_invariants_and_views.sql` — content-safety invariants and views

### Backend (`backend/`)
- `requirements.txt`
- `app/` — `main.py`, `config.py`, `db.py`, `models.py`, `schemas.py`,
  `security.py`, `deps.py`, `audit.py`, `content_data.py`, `seed.py`, `migrate.py`
- `app/routers/` — `auth.py`, `content.py`, `speech.py`, `stt_router.py`,
  `recognize.py`, `admin.py`, `health.py`
- `app/services/` — `recognition.py`, `tts.py`, `stt.py`, `snapshot.py`
- `scripts/generate_audio.py`
- `scripts/preflight.py` — startup readiness checks

### Frontend (`frontend/`)
- `package.json`, `tsconfig.json`, `next.config.mjs`, `tailwind.config.ts`, `postcss.config.mjs`
- `app/` — `layout.tsx`, `globals.css`, `page.tsx`, `login/`, `settings/`, `admin/*`
- `components/` — `Header`, `CameraPanel`, `StatusBar`, `MessageCard`,
  `SessionHistory`, `DoctorMode`, `admin/ui`
- `lib/` — `api.ts`, `auth.tsx`, `types.ts`, `useRecognition.ts`

### Generated / local (gitignored)
- `data/*.json` — exported offline snapshot
- `assets/audio/*.wav` — pre-generated Urdu audio
- `assets/psl-videos/*` — verified PSL videos
