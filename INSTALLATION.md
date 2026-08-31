# Ishara AI — Installation Guide

> **For team members:** Open this file in your AI agent (Antigravity, Cursor, Copilot, etc.) and say:
> *"Read INSTALLATION.md and set up this project on my machine so it runs exactly like production."*
> The agent will follow every step below.

---

## ⚡ Short version (read this first)

```
Pehli baar:   setup.bat  →  phir  run.bat
Dobara:       sirf  run.bat
```

`run.bat` smart hai — woh khud detect karta hai ke kya installed hai aur kya nahi.
Agar setup nahi hua, woh pehle setup karega, phir app start karega.
**Sab packages install hone ke baad hamesha sirf `run.bat` chalao — bas.**

---

## What this project is

Ishara AI is a healthcare communication bridge for Deaf patients. It runs as two local servers:

| Server | URL | What it does |
|--------|-----|--------------|
| Backend (FastAPI) | `http://localhost:8000` | Recognition, speech, database, API |
| Frontend (Next.js) | `http://localhost:3000` | Camera UI, doctor mode, admin panel |

Everything runs **offline** — no internet required during the demo except optional doctor voice input.

---

## Prerequisites — install these first

The agent should verify each one is present before continuing. If missing, install it.

### 1. Python 3.11 or newer
```
python --version
```
Must show `3.11.x` or higher. Download from: https://www.python.org/downloads/
> During installation tick **"Add python.exe to PATH"**.

### 2. Node.js 20 or newer + npm
```
node --version
npm --version
```
Download from: https://nodejs.org/ (choose the LTS version)

### 3. PostgreSQL 15 or newer
```
psql --version
```
Download from: https://www.postgresql.org/download/windows/
> During installation, remember the password you set for the `postgres` user — you will need it in Step 3.
> After install, make sure the PostgreSQL `bin` folder is on PATH (the installer offers this as a checkbox).

---

## Step 1 — Get the code

```bash
git clone <repo-url> psl-bridge-project
cd psl-bridge-project
```

If you already have the folder, just pull:
```bash
git pull origin main
```

**Verify:** `experiments/day1/references/FEVER_ref_01.npz` should exist after the pull. These are the DTW reference files — they are committed to git and must be present for recognition to work.

---

## Step 2 — Download the MediaPipe model file

This file is **not** in git (13.7 MB, gitignored). Download it manually:

**File to download:**
https://storage.googleapis.com/mediapipe-models/holistic_landmarker/holistic_landmarker/float16/latest/holistic_landmarker.task

**Where to put it:**
`models/holistic_landmarker.task`
(the `models/` folder already exists in the repo, just drop the file inside)

**Agent: verify with this command:**
```powershell
Test-Path models\holistic_landmarker.task
```
Must print `True` before continuing.

---

## Step 3 — Create the `.env` file

Copy the example file:
```powershell
Copy-Item .env.example .env
```

Now open `.env` and fill in these values:

```env
# Your PostgreSQL password (the one you set when installing Postgres)
POSTGRES_PASSWORD=your_postgres_password_here
DATABASE_URL=postgresql://postgres:your_postgres_password_here@localhost:5432/ishara_ai

# Generate a random secret with the command below and paste the output here
JWT_SECRET=paste_random_secret_here

# Admin login for the staff panel (you can change these)
SEED_ADMIN_EMAIL=admin@isharaai.local
SEED_ADMIN_PASSWORD=admin123
```

**Agent: generate `JWT_SECRET` by running:**
```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```
Copy the output and replace `paste_random_secret_here` in `.env`.

Leave all other lines as-is. Do **not** commit `.env` — it is gitignored.

---

## Step 4 — Run the automated setup

This single script does everything: installs Python packages, creates the database, runs migrations, seeds content, installs frontend packages, and builds the frontend.

```powershell
.\setup.bat
```

When prompted:
- **"PostgreSQL password"** → enter the same password you put in `.env`
- **"Admin password"** → press Enter to use `admin123`, or type your own
- **"Include development content? [Y/N]"** → press **Y**

The script prints `[ok]` for each step. If any step prints `[X]`, stop and fix that issue (see Troubleshooting below) before continuing.

Expected last lines:
```
Setup complete.
Start it with:  run.bat
Staff sign in:  admin@isharaai.local / admin123
```

---

## Step 5 — Start the app

```powershell
.\run.bat
```

This starts both servers in background windows and opens the browser automatically.

Wait until you see:
```
[ok] API is answering
[ok] Web is answering
```

| URL | Purpose |
|-----|---------|
| http://localhost:3000 | Patient communication screen |
| http://localhost:3000/login | Staff login |
| http://localhost:3000/admin | Admin panel |
| http://localhost:8000/docs | API documentation |

---

## Step 6 — Verify it works

### Camera test
1. Go to http://localhost:3000
2. Allow camera permission when the browser asks
3. You should see a live camera feed in the left panel
4. The status bar should show **"Ready"** with a green indicator

### Recognition test
1. With the camera showing, slowly make a clear deliberate sign (wave your hand in an arc)
2. The system will either show a result card or say "Unknown — please try again"
3. Both outcomes are correct. "Unknown" means the gate is working, not that it broke

### Staff login test
1. Go to http://localhost:3000/login
2. Login: `admin@isharaai.local` / `admin123`
3. You should reach the staff dashboard

---

## Dobara start karna (after first setup)

Pehli baar `setup.bat` chal gayi — ab **sirf yahi ek command** yaad rakhni hai:

```powershell
.\run.bat
```

`run.bat` har baar ye check karta hai apne aap:

| Check | Kya karta hai |
|-------|---------------|
| `.env` maujood hai? | Agar nahi → setup offer karta hai |
| `frontend/node_modules` hai? | Agar nahi → `npm install` karta hai |
| Frontend build hai? | Agar nahi → `npm run build` karta hai |
| Backend packages hain? | Agar nahi → `pip install` karta hai |
| Ports 3000/8000 busy hain? | Puranie processes kill karta hai |

To dobara start karne ke liye `setup.bat` dobara mat chalao — woh pehli baar ka kaam hai.
`run.bat` sab sambhal leta hai.

---

## Stopping the app

```powershell
.\stop.bat
```

Or close the two minimised windows labelled **"Ishara AI API"** and **"Ishara AI Web"**.

---

## Troubleshooting

### `[X] Python was not found on PATH`
Python is installed but not on PATH.
Reinstall Python and tick "Add to PATH", or add `C:\Users\<you>\AppData\Local\Programs\Python\Python311\` to your system PATH manually.

### `[X] Could not connect to PostgreSQL`
Either the service is not running or the password in `.env` is wrong.
- Check service: Win+R → `services.msc` → find `postgresql-x64-XX` → Start
- Check password: open `.env`, confirm `POSTGRES_PASSWORD` matches what you set during PostgreSQL install

### `[X] Migrations failed`
```powershell
# Drop and recreate the database, then re-run setup
psql -U postgres -h localhost -c "DROP DATABASE IF EXISTS ishara_ai;"
.\setup.bat
```

### Camera shows black / no feed
- Make sure no other app is using the camera (Teams, Zoom, etc.)
- Use Chrome — it has the best MediaPipe compatibility
- Check browser camera permission: address bar → lock icon → permissions

### Recognition always returns Unknown
The `models/holistic_landmarker.task` file may be missing. Verify:
```powershell
Test-Path models\holistic_landmarker.task
```
If `False`, re-download from Step 2 and restart with `run.bat`.

### Port already in use (3000 or 8000)
`run.bat` kills old processes automatically. If it still fails:
```powershell
# Find what is on port 8000
netstat -ano | findstr :8000
# Kill it (replace 1234 with the PID from above)
taskkill /PID 1234 /F
```

---

## File layout — what matters for setup

```
psl-bridge-project/
├── .env                           ← YOU CREATE THIS  (gitignored)
├── .env.example                   ← template         (committed)
├── setup.bat                      ← one-time setup
├── run.bat                        ← start the app
├── stop.bat                       ← stop the app
├── dev.bat                        ← start with hot-reload (dev only)
├── models/
│   └── holistic_landmarker.task   ← YOU DOWNLOAD THIS (gitignored)
├── experiments/
│   └── day1/references/*.npz      ← DTW reference files (committed, already present after git pull)
├── backend/
│   ├── requirements.txt
│   └── app/
└── frontend/
    └── package.json
```

---

## What NOT to do

- Do **not** commit `.env`
- Do **not** modify anything in `experiments/day1/references/` — these are calibrated DTW files
- Do **not** run `npm run dev` for the demo — use `run.bat` which uses the production build
- Do **not** add your own recordings to `references/` without telling the lead

---

## Quick reference

| Task | Command |
|------|---------|
| First-time setup | `.\setup.bat` |
| Start the app | `.\run.bat` |
| Stop the app | `.\stop.bat` |
| Dev mode (hot reload) | `.\dev.bat` |
| Check API health | `curl http://localhost:8000/api/health` |
| Check DB connection | `psql -U postgres -h localhost -d ishara_ai -c "SELECT 1"` |

---

*Ishara AI — Alibaba Cloud AI Hackathon Pakistan 2026*
