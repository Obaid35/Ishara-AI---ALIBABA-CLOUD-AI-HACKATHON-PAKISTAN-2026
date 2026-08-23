"""Admin console API.

Admin-only, checked server-side on every route — never only in the UI.

The most important behaviour here is refusing impossible operations with an
explanation. The database enforces the content invariants; this layer turns
those refusals into messages a human can act on.
"""

from __future__ import annotations

import datetime as dt
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from psycopg2.errors import CheckViolation
from pydantic import BaseModel
from sqlalchemy import func, select, text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session

from .. import audit
from ..db import get_db
from ..schemas import AccountEmail
from ..deps import require_admin, require_staff
from ..models import (
    Asset,
    AssetRights,
    AuditLog,
    AuthSession,
    Consent,
    DoctorPhrase,
    DoctorPhraseCategory,
    MessageConcept,
    PatientMessage,
    RecognitionConfig,
    RecognitionTest,
    RecognitionTrial,
    Sign,
    TestParticipant,
    User,
    Setting,
)
from ..security import hash_password
from ..services import snapshot, tts

router = APIRouter(prefix="/api/admin", tags=["admin"])


def _invariant_error(exc: Exception) -> HTTPException:
    """Turn a database invariant refusal into an explanation."""
    orig = getattr(exc, "orig", None)
    if isinstance(orig, CheckViolation) or "I1:" in str(orig) or "I2:" in str(orig):
        message = str(orig).split("\n")[0].strip()
        for prefix in ("I1: ", "I2: ", "I4: ", "I6: "):
            message = message.replace(prefix, "")
        return HTTPException(status.HTTP_409_CONFLICT, message)
    return HTTPException(status.HTTP_400_BAD_REQUEST, str(orig or exc).split("\n")[0])


# ================================================================ dashboard

@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    def scalar(sql: str) -> int:
        return db.execute(text(sql)).scalar() or 0

    by_status = {
        r[0]: r[1]
        for r in db.execute(
            text("SELECT reliability_status::text, count(*) FROM signs GROUP BY 1")
        )
    }
    readiness = [dict(r._mapping) for r in db.execute(text("SELECT * FROM v_demo_readiness"))]
    gaps = [dict(r._mapping) for r in db.execute(text("SELECT * FROM v_permission_gaps"))]
    config = db.execute(
        text(
            "SELECT tau_accept, delta_margin, sigma, frozen_on, notes "
            "FROM recognition_config WHERE is_active LIMIT 1"
        )
    ).first()
    recent = [
        dict(r._mapping)
        for r in db.execute(
            text(
                "SELECT rt.run_on, rt.test_level::text AS test_level, s.code AS sign_code, "
                "       rt.attempts, rt.correct, rt.wrong, rt.unknown "
                "FROM recognition_tests rt JOIN signs s ON s.id = rt.sign_id "
                "ORDER BY rt.created_at DESC LIMIT 8"
            )
        )
    ]

    return {
        "counts": {
            "reliable_signs": scalar("SELECT count(*) FROM v_production_vocabulary"),
            "total_signs": scalar("SELECT count(*) FROM signs"),
            "verified_signs": scalar(
                "SELECT count(*) FROM signs WHERE verification_status = 'psl_verified'"
            ),
            "demoable_messages": scalar("SELECT count(*) FROM v_demoable_messages"),
            "total_messages": scalar("SELECT count(*) FROM patient_messages"),
            "demoable_phrases": scalar("SELECT count(*) FROM v_demoable_doctor_phrases"),
            "total_phrases": scalar("SELECT count(*) FROM doctor_phrases"),
            "stale_audio": scalar(
                "SELECT count(*) FROM patient_messages pm WHERE pm.audio_asset_id IS NOT NULL "
                "AND pm.audio_source_checksum IS DISTINCT FROM "
                "message_text_checksum(pm.urdu_text, pm.kokoro_input)"
            ),
            "users": scalar("SELECT count(*) FROM users WHERE is_active"),
        },
        "signs_by_status": by_status,
        "demo_readiness": readiness,
        "permission_gaps": gaps,
        "recognition_config": dict(config._mapping) if config else None,
        "recent_tests": recent,
        "snapshot": snapshot.info(),
    }


# ================================================================ signs

class SignUpdate(BaseModel):
    urdu_meaning: str | None = None
    english_meaning: str | None = None
    verification_status: str | None = None
    reliability_status: str | None = None
    is_enabled: bool | None = None
    verified_by: str | None = None
    regional_variant_note: str | None = None
    delta_margin_override: float | None = None
    is_demo_critical: bool | None = None
    notes: str | None = None


@router.get("/signs")
def list_signs(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    rows = db.execute(
        text(
            "SELECT s.id, s.code, s.urdu_meaning, s.english_meaning, "
            "       s.verification_status::text, s.reliability_status::text, s.is_enabled, "
            "       s.verified_by, s.verified_on, s.is_demo_critical, s.notes, "
            "       s.delta_margin_override, s.regional_variant_note, "
            "       (SELECT count(*) FROM sign_references sr WHERE sr.sign_id = s.id) AS reference_count, "
            "       (SELECT count(*) FROM message_concepts mc WHERE mc.sign_id = s.id) AS used_by_messages "
            "FROM signs s ORDER BY s.is_demo_critical DESC, s.code"
        )
    )
    return {"signs": [dict(r._mapping) for r in rows]}


@router.get("/signs/{sign_id}/impact")
def sign_impact(sign_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    """Which messages would be disabled if this sign were demoted (I1 cascade)."""
    rows = db.execute(
        text(
            "SELECT pm.code, pm.urdu_text, pm.is_enabled, pm.is_demo_critical "
            "FROM patient_messages pm JOIN message_concepts mc ON mc.message_id = pm.id "
            "WHERE mc.sign_id = :sid ORDER BY pm.code"
        ),
        {"sid": str(sign_id)},
    )
    messages = [dict(r._mapping) for r in rows]
    return {
        "messages": messages,
        "enabled_count": sum(1 for m in messages if m["is_enabled"]),
        "warning": "Demoting this sign will automatically disable every enabled "
                   "message listed here.",
    }


@router.patch("/signs/{sign_id}")
def update_sign(sign_id: uuid.UUID, payload: SignUpdate, request: Request,
                db: Session = Depends(get_db), user: User = Depends(require_admin)):
    sign = db.get(Sign, sign_id)
    if not sign:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sign not found")

    before = {
        "verification_status": sign.verification_status,
        "reliability_status": sign.reliability_status,
        "is_enabled": sign.is_enabled,
    }
    data = payload.model_dump(exclude_unset=True)

    if data.get("is_enabled") and (
        data.get("reliability_status", sign.reliability_status) != "reliable"
    ):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"{sign.code} cannot be enabled — it is not Reliable. "
            "Only Reliable signs enter the production vocabulary.",
        )

    for key, value in data.items():
        setattr(sign, key, value)
    if data.get("verification_status") == "psl_verified" and not sign.verified_on:
        sign.verified_on = dt.date.today()
    sign.updated_at = dt.datetime.now(dt.timezone.utc)

    audit.record(db, action="update", entity_type="sign", entity_id=str(sign.id),
                 user_id=user.id, before=before, after=data, request=request)
    try:
        db.commit()
    except (IntegrityError, DBAPIError) as exc:
        db.rollback()
        raise _invariant_error(exc) from exc

    return {"ok": True}


# ================================================================ messages

class MessageUpdate(BaseModel):
    urdu_text: str | None = None
    english_text: str | None = None
    kokoro_input: str | None = None
    priority: str | None = None
    is_demo_critical: bool | None = None
    is_enabled: bool | None = None
    reviewed_by: str | None = None


@router.get("/messages")
def list_messages(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    rows = db.execute(
        text(
            "SELECT pm.id, pm.code, pm.urdu_text, pm.english_text, pm.kokoro_input, "
            "       pm.priority::text, pm.is_demo_critical, pm.is_enabled, pm.reviewed_by, "
            "       a.path AS audio_path, "
            "       (pm.audio_asset_id IS NOT NULL AND pm.audio_source_checksum "
            "        = message_text_checksum(pm.urdu_text, pm.kokoro_input)) AS audio_ok, "
            "       (pm.audio_asset_id IS NOT NULL AND pm.audio_source_checksum IS DISTINCT FROM "
            "        message_text_checksum(pm.urdu_text, pm.kokoro_input)) AS audio_stale, "
            "       (SELECT string_agg(s.code, ' + ' ORDER BY mc.position) "
            "          FROM message_concepts mc JOIN signs s ON s.id = mc.sign_id "
            "         WHERE mc.message_id = pm.id) AS concept_sequence, "
            "       (SELECT string_agg(s.code, ', ') FROM message_concepts mc "
            "          JOIN signs s ON s.id = mc.sign_id "
            "         WHERE mc.message_id = pm.id "
            "           AND (s.reliability_status <> 'reliable' OR NOT s.is_enabled)) AS blocking_signs "
            "FROM patient_messages pm LEFT JOIN assets a ON a.id = pm.audio_asset_id "
            "ORDER BY pm.priority, pm.code"
        )
    )
    return {"messages": [dict(r._mapping) for r in rows]}


@router.patch("/messages/{message_id}")
def update_message(message_id: uuid.UUID, payload: MessageUpdate, request: Request,
                   db: Session = Depends(get_db), user: User = Depends(require_admin)):
    msg = db.get(PatientMessage, message_id)
    if not msg:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Message not found")

    before = {"urdu_text": msg.urdu_text, "kokoro_input": msg.kokoro_input,
              "is_enabled": msg.is_enabled}
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(msg, key, value)
    msg.updated_at = dt.datetime.now(dt.timezone.utc)

    text_changed = "urdu_text" in data or "kokoro_input" in data
    audit.record(db, action="update", entity_type="patient_message", entity_id=str(msg.id),
                 user_id=user.id, before=before, after=data, request=request)
    try:
        db.commit()
    except (IntegrityError, DBAPIError) as exc:
        db.rollback()
        raise _invariant_error(exc) from exc

    stale = (
        msg.audio_asset_id is not None
        and msg.audio_source_checksum != tts.text_checksum(msg.urdu_text, msg.kokoro_input)
    )
    return {
        "ok": True,
        "audio_stale": stale,
        "warning": (
            "Audio is now stale. The text changed after this audio was generated — "
            "regenerate before the demo, or the screen and the speaker will disagree."
        )
        if (text_changed and stale)
        else None,
    }


# ================================================================ doctor phrases

class PhraseUpdate(BaseModel):
    urdu_text: str | None = None
    english_text: str | None = None
    verification_status: str | None = None
    verified_by: str | None = None
    priority: str | None = None
    is_demo_critical: bool | None = None
    is_enabled: bool | None = None
    sort_order: int | None = None
    stt_aliases: list[str] | None = None


@router.get("/doctor-phrases")
def list_phrases(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    rows = db.execute(
        text(
            "SELECT dp.id, dp.code, dp.urdu_text, dp.english_text, dp.priority::text, "
            "       dp.verification_status::text, dp.verified_by, dp.is_enabled, "
            "       dp.is_demo_critical, dp.sort_order, dp.stt_aliases, "
            "       c.code AS category_code, c.name_en AS category_name, "
            "       a.path AS video_path, ar.permission_status::text, "
            "       ar.permitted_demo_playback "
            "FROM doctor_phrases dp "
            "LEFT JOIN doctor_phrase_categories c ON c.id = dp.category_id "
            "LEFT JOIN assets a ON a.id = dp.psl_asset_id "
            "LEFT JOIN asset_rights ar ON ar.asset_id = a.id "
            "ORDER BY c.sort_order, dp.sort_order"
        )
    )
    return {"phrases": [dict(r._mapping) for r in rows]}


@router.patch("/doctor-phrases/{phrase_id}")
def update_phrase(phrase_id: uuid.UUID, payload: PhraseUpdate, request: Request,
                  db: Session = Depends(get_db), user: User = Depends(require_admin)):
    phrase = db.get(DoctorPhrase, phrase_id)
    if not phrase:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Phrase not found")

    before = {"verification_status": phrase.verification_status, "is_enabled": phrase.is_enabled}
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(phrase, key, value)
    if data.get("verification_status") == "psl_verified" and not phrase.verified_on:
        phrase.verified_on = dt.date.today()
    phrase.updated_at = dt.datetime.now(dt.timezone.utc)

    audit.record(db, action="update", entity_type="doctor_phrase", entity_id=str(phrase.id),
                 user_id=user.id, before=before, after=data, request=request)
    try:
        db.commit()
    except (IntegrityError, DBAPIError) as exc:
        db.rollback()
        raise _invariant_error(exc) from exc
    return {"ok": True}


# ================================================================ testing

class TestCreate(BaseModel):
    test_level: str
    sign_code: str
    participant_code: str | None = None
    attempts: int
    correct: int
    wrong: int
    unknown: int
    top_confusion_sign_code: str | None = None
    notes: str = ""


@router.get("/testing")
def list_tests(db: Session = Depends(get_db), _: User = Depends(require_staff)):
    rows = db.execute(
        text(
            "SELECT rt.id, rt.run_on, rt.test_level::text, s.code AS sign_code, "
            "       p.participant_code, p.is_unseen, rt.attempts, rt.correct, rt.wrong, "
            "       rt.unknown, cs.code AS confusion_code, rt.notes "
            "FROM recognition_tests rt "
            "JOIN signs s ON s.id = rt.sign_id "
            "LEFT JOIN test_participants p ON p.id = rt.participant_id "
            "LEFT JOIN signs cs ON cs.id = rt.top_confusion_sign_id "
            "ORDER BY rt.created_at DESC"
        )
    )
    tests = [dict(r._mapping) for r in rows]

    totals = db.execute(
        text("SELECT coalesce(sum(attempts),0), coalesce(sum(correct),0), "
             "coalesce(sum(wrong),0), coalesce(sum(unknown),0) FROM recognition_tests")
    ).first()

    return {
        "tests": tests,
        "totals": {
            "attempts": totals[0], "correct": totals[1],
            "wrong": totals[2], "unknown": totals[3],
        },
        "note": "Unknown is tracked separately from wrong. Never merge them, and "
                "never quote a percentage without its denominator.",
    }


@router.post("/testing")
def create_test(payload: TestCreate, request: Request, db: Session = Depends(get_db),
                user: User = Depends(require_staff)):
    if payload.correct + payload.wrong + payload.unknown != payload.attempts:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"correct + wrong + unknown ({payload.correct + payload.wrong + payload.unknown}) "
            f"must equal attempts ({payload.attempts})",
        )

    sign = db.scalar(select(Sign).where(Sign.code == payload.sign_code))
    if not sign:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Unknown sign '{payload.sign_code}'")

    participant = None
    if payload.participant_code:
        participant = db.scalar(
            select(TestParticipant).where(
                TestParticipant.participant_code == payload.participant_code
            )
        )
        if not participant:
            participant = TestParticipant(participant_code=payload.participant_code)
            db.add(participant)
            db.flush()

    confusion = None
    if payload.top_confusion_sign_code:
        confusion = db.scalar(select(Sign).where(Sign.code == payload.top_confusion_sign_code))

    config = db.scalar(select(RecognitionConfig).where(RecognitionConfig.is_active))

    record = RecognitionTest(
        test_level=payload.test_level,
        sign_id=sign.id,
        participant_id=participant.id if participant else None,
        attempts=payload.attempts,
        correct=payload.correct,
        wrong=payload.wrong,
        unknown=payload.unknown,
        top_confusion_sign_id=confusion.id if confusion else None,
        config_id=config.id if config else None,
        notes=payload.notes,
    )
    db.add(record)
    audit.record(db, action="create", entity_type="recognition_test",
                 user_id=user.id, after=payload.model_dump(), request=request)
    try:
        db.commit()
    except (IntegrityError, DBAPIError) as exc:
        db.rollback()
        raise _invariant_error(exc) from exc
    return {"ok": True, "id": str(record.id)}


# ================================================================ thresholds

class ThresholdUpdate(BaseModel):
    tau_accept: float
    delta_margin: float
    notes: str = ""


@router.get("/thresholds")
def get_thresholds(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    row = db.execute(
        text(
            "SELECT id, tau_accept, delta_margin, sigma, band_width_pct, p_absent, "
            "       frozen_on, notes FROM recognition_config WHERE is_active LIMIT 1"
        )
    ).first()
    t4 = db.execute(
        text("SELECT max(run_on) FROM recognition_tests WHERE test_level = 't4_unseen'")
    ).scalar()
    return {
        "config": dict(row._mapping) if row else None,
        "last_t4_run": t4,
        "warning": (
            f"Changing frozen thresholds voids the T4 unseen-person result recorded on {t4}."
            if t4 and row and row._mapping["frozen_on"]
            else None
        ),
    }


@router.patch("/thresholds")
def update_thresholds(payload: ThresholdUpdate, request: Request,
                      db: Session = Depends(get_db), user: User = Depends(require_admin)):
    config = db.scalar(select(RecognitionConfig).where(RecognitionConfig.is_active))
    if not config:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No active recognition config")
    before = {"tau_accept": float(config.tau_accept), "delta_margin": float(config.delta_margin),
              "frozen_on": config.frozen_on}
    config.tau_accept = payload.tau_accept
    config.delta_margin = payload.delta_margin
    config.notes = payload.notes or config.notes
    audit.record(db, action="update", entity_type="recognition_config", entity_id=str(config.id),
                 user_id=user.id, before=before, after=payload.model_dump(), request=request)
    db.commit()
    return {"ok": True}


@router.post("/thresholds/freeze")
def freeze_thresholds(request: Request, db: Session = Depends(get_db),
                      user: User = Depends(require_admin)):
    config = db.scalar(select(RecognitionConfig).where(RecognitionConfig.is_active))
    if not config:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No active recognition config")
    config.frozen_on = dt.datetime.now(dt.timezone.utc)
    config.frozen_by = user.id
    audit.record(db, action="freeze_thresholds", entity_type="recognition_config",
                 entity_id=str(config.id), user_id=user.id,
                 after={"tau_accept": float(config.tau_accept),
                        "delta_margin": float(config.delta_margin)}, request=request)
    db.commit()
    return {"ok": True, "frozen_on": config.frozen_on,
            "note": "Thresholds are frozen. Run the T4 unseen-person test now. "
                    "Changing them afterwards voids that result."}


# ================================================================ assets

class RightsUpdate(BaseModel):
    source_name: str | None = None
    source_url: str | None = None
    permission_status: str | None = None
    permitted_development: bool | None = None
    permitted_internal_testing: bool | None = None
    permitted_demo_playback: bool | None = None
    permitted_public_release: bool | None = None
    license_notes: str | None = None
    evidence_ref: str | None = None


@router.get("/assets")
def list_assets(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    rows = db.execute(
        text(
            "SELECT a.id, a.kind::text, a.path, a.bytes, a.duration_ms, "
            "       ar.source_name, ar.source_url, ar.permission_status::text, "
            "       ar.permitted_development, ar.permitted_internal_testing, "
            "       ar.permitted_demo_playback, ar.permitted_public_release, "
            "       ar.license_notes, ar.evidence_ref, "
            "       (SELECT string_agg(dp.code, ', ') FROM doctor_phrases dp "
            "         WHERE dp.psl_asset_id = a.id) AS used_by_phrases, "
            "       (SELECT string_agg(pm.code, ', ') FROM patient_messages pm "
            "         WHERE pm.audio_asset_id = a.id) AS used_by_messages "
            "FROM assets a LEFT JOIN asset_rights ar ON ar.asset_id = a.id "
            "ORDER BY a.kind, a.path"
        )
    )
    return {"assets": [dict(r._mapping) for r in rows]}


@router.patch("/assets/{asset_id}/rights")
def update_rights(asset_id: uuid.UUID, payload: RightsUpdate, request: Request,
                  db: Session = Depends(get_db), user: User = Depends(require_admin)):
    rights = db.get(AssetRights, asset_id)
    if not rights:
        if not db.get(Asset, asset_id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Asset not found")
        rights = AssetRights(asset_id=asset_id)
        db.add(rights)

    before = {"permission_status": rights.permission_status,
              "permitted_demo_playback": rights.permitted_demo_playback}
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(rights, key, value)
    if payload.permission_status in ("granted", "denied") and not rights.responded_on:
        rights.responded_on = dt.date.today()

    audit.record(db, action="update", entity_type="asset_rights", entity_id=str(asset_id),
                 user_id=user.id, before=before,
                 after=payload.model_dump(exclude_unset=True), request=request)
    db.commit()
    return {"ok": True}


@router.get("/participants")
def list_participants(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    rows = db.execute(
        text(
            "SELECT p.id, p.participant_code, p.is_unseen, p.notes, "
            "       (SELECT string_agg(c.purpose::text, ', ') FROM consents c "
            "         WHERE c.participant_id = p.id AND c.granted) AS granted_purposes "
            "FROM test_participants p ORDER BY p.participant_code"
        )
    )
    return {"participants": [dict(r._mapping) for r in rows]}


# ================================================================ users

class UserCreate(BaseModel):
    email: AccountEmail
    full_name: str
    role_code: str
    password: str


class UserUpdate(BaseModel):
    full_name: str | None = None
    role_code: str | None = None
    is_active: bool | None = None


@router.get("/users")
def list_users(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    rows = db.execute(
        text(
            "SELECT u.id, u.email, u.full_name, u.role_code, u.is_active, "
            "       u.must_change_password, u.last_login_at, u.created_at "
            "FROM users u ORDER BY u.created_at"
        )
    )
    return {"users": [dict(r._mapping) for r in rows]}


@router.post("/users")
def create_user(payload: UserCreate, request: Request, db: Session = Depends(get_db),
                admin: User = Depends(require_admin)):
    if payload.role_code not in ("admin", "doctor", "staff"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown role")
    if len(payload.password) < 8:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Password must be at least 8 characters")
    if db.scalar(select(User).where(User.email == payload.email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with that email already exists")

    user = User(
        email=payload.email,
        full_name=payload.full_name,
        role_code=payload.role_code,
        password_hash=hash_password(payload.password),
        created_by=admin.id,
        must_change_password=True,
    )
    db.add(user)
    db.flush()
    # The password is never written to the audit log.
    audit.record(db, action="create", entity_type="user", entity_id=str(user.id),
                 user_id=admin.id,
                 after={"email": payload.email, "role_code": payload.role_code}, request=request)
    db.commit()
    return {"ok": True, "id": str(user.id)}


@router.patch("/users/{user_id}")
def update_user(user_id: uuid.UUID, payload: UserUpdate, request: Request,
                db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    data = payload.model_dump(exclude_unset=True)
    # An admin cannot lock the system out of administration through their own account.
    if user.id == admin.id:
        if data.get("is_active") is False:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "You cannot deactivate your own account")
        if data.get("role_code") and data["role_code"] != "admin":
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "You cannot remove your own admin role")

    before = {"role_code": user.role_code, "is_active": user.is_active}
    for key, value in data.items():
        setattr(user, key, value)

    if data.get("is_active") is False:
        # Deactivation takes effect immediately.
        for session in db.scalars(select(AuthSession).where(AuthSession.user_id == user.id)).all():
            if session.revoked_at is None:
                session.revoked_at = dt.datetime.now(dt.timezone.utc)

    audit.record(db, action="update", entity_type="user", entity_id=str(user.id),
                 user_id=admin.id, before=before, after=data, request=request)
    db.commit()
    return {"ok": True}


@router.post("/users/{user_id}/reset-password")
def admin_reset_password(user_id: uuid.UUID, request: Request, db: Session = Depends(get_db),
                         admin: User = Depends(require_admin)):
    import secrets

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    temporary = secrets.token_urlsafe(12)
    user.password_hash = hash_password(temporary)
    user.must_change_password = True
    for session in db.scalars(select(AuthSession).where(AuthSession.user_id == user.id)).all():
        if session.revoked_at is None:
            session.revoked_at = dt.datetime.now(dt.timezone.utc)
    audit.record(db, action="reset_password", entity_type="user", entity_id=str(user.id),
                 user_id=admin.id, request=request)
    db.commit()
    # Shown once, to be handed over directly. Never stored, never logged.
    return {"ok": True, "temporary_password": temporary}


# ================================================================ audit

@router.get("/audit")
def list_audit(limit: int = 100, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    rows = db.execute(
        text(
            "SELECT al.id, al.created_at, al.action, al.entity_type, al.entity_id, "
            "       al.before, al.after, u.email AS user_email "
            "FROM audit_logs al LEFT JOIN users u ON u.id = al.user_id "
            "ORDER BY al.id DESC LIMIT :lim"
        ),
        {"lim": min(limit, 500)},
    )
    return {"entries": [dict(r._mapping) for r in rows]}


# ================================================================ settings

class SettingUpdate(BaseModel):
    value: object


@router.get("/settings")
def get_settings_endpoint(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    rows = db.execute(text("SELECT key, value FROM settings ORDER BY key"))
    return {"settings": {r[0]: r[1] for r in rows}}


@router.put("/settings/{key}")
def update_setting(key: str, payload: SettingUpdate, request: Request,
                   db: Session = Depends(get_db), user: User = Depends(require_admin)):
    setting = db.get(Setting, key)
    if not setting:
        setting = Setting(key=key, value=payload.value)
        db.add(setting)
    else:
        before = {"value": setting.value}
        setting.value = payload.value
        audit.record(db, action="update", entity_type="setting", entity_id=key,
                     user_id=user.id, before=before, after={"value": payload.value},
                     request=request)
    setting.updated_by = user.id
    setting.updated_at = dt.datetime.now(dt.timezone.utc)
    db.commit()

    warning = None
    if key == "tts_voice":
        count = db.execute(
            text("SELECT count(*) FROM patient_messages WHERE audio_asset_id IS NOT NULL")
        ).scalar()
        warning = (
            f"Changing the voice makes all {count} pre-generated audio files stale — "
            "every one was produced by the previous voice and must be regenerated."
        )
    return {"ok": True, "warning": warning}


# ================================================================ snapshot

@router.post("/snapshot/export")
def export_snapshot(request: Request, db: Session = Depends(get_db),
                    user: User = Depends(require_admin)):
    counts = snapshot.export(db)
    audit.record(db, action="export_snapshot", entity_type="snapshot",
                 user_id=user.id, after=counts, request=request)
    db.commit()
    return {"ok": True, "counts": counts, "info": snapshot.info()}


@router.get("/snapshot")
def snapshot_status(_: User = Depends(require_admin)):
    return snapshot.info()
