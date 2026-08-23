"""Ishara AI API.

Run:  uvicorn app.main:app --reload --port 8000

The communication endpoints are deliberately unauthenticated — a Deaf patient
must be able to use the screen without an account (D018). Only /api/admin
requires a role, and that is enforced here on the server.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .db import db_state
from .routers import admin, auth, content, health, recognize, speech, stt_router
from .services.recognition import is_stub

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("ishara")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if db_state.probe():
        log.info("PostgreSQL connected — live mode")
    else:
        log.warning("PostgreSQL unavailable — snapshot mode (read-only)")
    if is_stub():
        log.warning("Recognition engine is a STUB — results are simulated, not recognition")

    settings.audio_dir.mkdir(parents=True, exist_ok=True)
    settings.video_dir.mkdir(parents=True, exist_ok=True)
    settings.snapshot_dir.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title="Ishara AI API",
    version="0.1.0",
    description=(
        "Healthcare communication between Pakistan Sign Language users and "
        "Urdu-speaking medical staff. Communication assistance only — not diagnostic."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(content.router)
app.include_router(speech.router)
app.include_router(stt_router.router)
app.include_router(admin.router)
app.include_router(recognize.router)

# Verified PSL videos are served from disk; the database stores paths only.
app.mount(
    "/media/psl-videos",
    StaticFiles(directory=settings.video_dir, check_dir=False),
    name="psl-videos",
)


@app.get("/")
def root():
    return {
        "name": "Ishara AI API",
        "docs": "/docs",
        "health": "/api/health",
        "boundary": "Communication assistance only. No diagnosis, no treatment advice.",
    }
