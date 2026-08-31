"""SQLAlchemy models mirroring db/migrations/001_init.sql."""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Optional

from sqlalchemy import (
    ARRAY,
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ENUM, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base

# Enums are created by the migration; create_type=False stops SQLAlchemy
# from trying to create them again.
VerificationStatus = ENUM(
    "draft", "psl_verified", "rejected", name="verification_status", create_type=False
)
ReliabilityStatus = ENUM(
    "candidate", "experimenting", "testing", "reliable", "weak", "dropped",
    name="reliability_status", create_type=False,
)
PriorityLevel = ENUM("p0", "p1", "p2", name="priority_level", create_type=False)
AssetKind = ENUM("psl_video", "audio_wav", "reference_clip", name="asset_kind", create_type=False)
PermissionStatus = ENUM(
    "unknown", "requested", "granted", "denied", "own_recording",
    name="permission_status", create_type=False,
)
ConsentPurpose = ENUM(
    "development", "internal_testing", "demo_playback", "public_release",
    name="consent_purpose", create_type=False,
)
TestLevel = ENUM(
    "t1_source", "t2_live_team", "t3_second_person", "t4_unseen", "t5_room_variation",
    name="test_level", create_type=False,
)
TrialOutcome = ENUM(
    "correct", "wrong", "unknown_ambiguous", "unknown_no_match",
    name="trial_outcome", create_type=False,
)


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())


class Role(Base):
    __tablename__ = "roles"
    code: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text, default="")


class Setting(Base):
    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(Text, primary_key=True)
    value: Mapped[dict] = mapped_column(JSONB)
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = _uuid_pk()
    email: Mapped[str] = mapped_column(Text, unique=True)
    username: Mapped[Optional[str]] = mapped_column(Text, unique=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(Text)
    full_name: Mapped[str] = mapped_column(Text, default="")
    role_code: Mapped[str] = mapped_column(Text, ForeignKey("roles.code"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuthSession(Base):
    __tablename__ = "auth_sessions"
    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    refresh_token_hash: Mapped[str] = mapped_column(Text)
    issued_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ip: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class PasswordReset(Base):
    __tablename__ = "password_resets"
    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    token_hash: Mapped[str] = mapped_column(Text)
    expires_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    action: Mapped[str] = mapped_column(Text)
    entity_type: Mapped[str] = mapped_column(Text)
    entity_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    before: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    after: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    ip: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Asset(Base):
    __tablename__ = "assets"
    id: Mapped[uuid.UUID] = _uuid_pk()
    kind: Mapped[str] = mapped_column(AssetKind)
    path: Mapped[str] = mapped_column(Text, unique=True)
    checksum: Mapped[str] = mapped_column(Text, default="")
    bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    rights: Mapped[Optional["AssetRights"]] = relationship(back_populates="asset", uselist=False)


class AssetRights(Base):
    __tablename__ = "asset_rights"
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), primary_key=True
    )
    source_name: Mapped[str] = mapped_column(Text, default="")
    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    permission_status: Mapped[str] = mapped_column(PermissionStatus, default="unknown")
    permitted_development: Mapped[bool] = mapped_column(Boolean, default=False)
    permitted_internal_testing: Mapped[bool] = mapped_column(Boolean, default=False)
    permitted_demo_playback: Mapped[bool] = mapped_column(Boolean, default=False)
    permitted_public_release: Mapped[bool] = mapped_column(Boolean, default=False)
    requested_on: Mapped[Optional[dt.date]] = mapped_column(Date, nullable=True)
    responded_on: Mapped[Optional[dt.date]] = mapped_column(Date, nullable=True)
    license_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence_ref: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    asset: Mapped[Asset] = relationship(back_populates="rights")


class TestParticipant(Base):
    __tablename__ = "test_participants"
    id: Mapped[uuid.UUID] = _uuid_pk()
    participant_code: Mapped[str] = mapped_column(Text, unique=True)
    is_unseen: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str] = mapped_column(Text, default="")


class Consent(Base):
    __tablename__ = "consents"
    __table_args__ = (UniqueConstraint("participant_id", "purpose"),)
    id: Mapped[uuid.UUID] = _uuid_pk()
    participant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("test_participants.id", ondelete="CASCADE")
    )
    purpose: Mapped[str] = mapped_column(ConsentPurpose)
    granted: Mapped[bool] = mapped_column(Boolean, default=False)
    granted_on: Mapped[Optional[dt.date]] = mapped_column(Date, nullable=True)
    evidence_ref: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class Sign(Base):
    __tablename__ = "signs"
    id: Mapped[uuid.UUID] = _uuid_pk()
    code: Mapped[str] = mapped_column(Text, unique=True)
    urdu_meaning: Mapped[str] = mapped_column(Text, default="")
    english_meaning: Mapped[str] = mapped_column(Text, default="")
    verification_status: Mapped[str] = mapped_column(VerificationStatus, default="draft")
    reliability_status: Mapped[str] = mapped_column(ReliabilityStatus, default="candidate")
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    verified_by: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    verified_on: Mapped[Optional[dt.date]] = mapped_column(Date, nullable=True)
    regional_variant_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    delta_margin_override: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    is_demo_critical: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SignVariant(Base):
    __tablename__ = "sign_variants"
    id: Mapped[uuid.UUID] = _uuid_pk()
    sign_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("signs.id", ondelete="CASCADE"))
    label: Mapped[str] = mapped_column(Text)
    region_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class SignReference(Base):
    __tablename__ = "sign_references"
    id: Mapped[uuid.UUID] = _uuid_pk()
    sign_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("signs.id", ondelete="CASCADE"))
    variant_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sign_variants.id"), nullable=True
    )
    asset_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assets.id"), nullable=True
    )
    landmark_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    landmark_checksum: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extractor_version: Mapped[str] = mapped_column(Text, default="")
    frame_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source_fps: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    participant_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("test_participants.id"), nullable=True
    )
    is_augmented: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PatientMessage(Base):
    __tablename__ = "patient_messages"
    id: Mapped[uuid.UUID] = _uuid_pk()
    code: Mapped[str] = mapped_column(Text, unique=True)
    urdu_text: Mapped[str] = mapped_column(Text)
    english_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    kokoro_input: Mapped[str] = mapped_column(Text, default="")
    audio_asset_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assets.id"), nullable=True
    )
    audio_source_checksum: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    priority: Mapped[str] = mapped_column(PriorityLevel, default="p1")
    is_demo_critical: Mapped[bool] = mapped_column(Boolean, default=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    reviewed_by: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewed_on: Mapped[Optional[dt.date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MessageConcept(Base):
    __tablename__ = "message_concepts"
    message_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patient_messages.id", ondelete="CASCADE"), primary_key=True
    )
    position: Mapped[int] = mapped_column(Integer, primary_key=True)
    sign_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("signs.id"))


class DoctorPhraseCategory(Base):
    __tablename__ = "doctor_phrase_categories"
    id: Mapped[uuid.UUID] = _uuid_pk()
    code: Mapped[str] = mapped_column(Text, unique=True)
    name_en: Mapped[str] = mapped_column(Text)
    name_ur: Mapped[str] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class DoctorPhrase(Base):
    __tablename__ = "doctor_phrases"
    id: Mapped[uuid.UUID] = _uuid_pk()
    code: Mapped[str] = mapped_column(Text, unique=True)
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("doctor_phrase_categories.id"), nullable=True
    )
    urdu_text: Mapped[str] = mapped_column(Text)
    english_text: Mapped[str] = mapped_column(Text, default="")
    psl_asset_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assets.id"), nullable=True
    )
    verification_status: Mapped[str] = mapped_column(VerificationStatus, default="draft")
    verified_by: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    verified_on: Mapped[Optional[dt.date]] = mapped_column(Date, nullable=True)
    priority: Mapped[str] = mapped_column(PriorityLevel, default="p1")
    is_demo_critical: Mapped[bool] = mapped_column(Boolean, default=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    stt_aliases: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RecognitionConfig(Base):
    __tablename__ = "recognition_config"
    id: Mapped[uuid.UUID] = _uuid_pk()
    tau_accept: Mapped[float] = mapped_column(Numeric)
    delta_margin: Mapped[float] = mapped_column(Numeric)
    sigma: Mapped[float] = mapped_column(Numeric, default=0.35)
    band_width_pct: Mapped[float] = mapped_column(Numeric, default=15)
    p_absent: Mapped[float] = mapped_column(Numeric, default=0.35)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    frozen_on: Mapped[Optional[dt.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    frozen_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RecognitionTest(Base):
    __tablename__ = "recognition_tests"
    __table_args__ = (
        CheckConstraint("correct + wrong + unknown = attempts", name="chk_test_totals"),
    )
    id: Mapped[uuid.UUID] = _uuid_pk()
    test_level: Mapped[str] = mapped_column(TestLevel)
    sign_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("signs.id", ondelete="CASCADE"))
    participant_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("test_participants.id"), nullable=True
    )
    attempts: Mapped[int] = mapped_column(Integer)
    correct: Mapped[int] = mapped_column(Integer, default=0)
    wrong: Mapped[int] = mapped_column(Integer, default=0)
    unknown: Mapped[int] = mapped_column(Integer, default=0)
    top_confusion_sign_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("signs.id"), nullable=True
    )
    config_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recognition_config.id"), nullable=True
    )
    run_on: Mapped[dt.date] = mapped_column(Date, server_default=func.current_date())
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RecognitionTrial(Base):
    __tablename__ = "recognition_trials"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    test_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recognition_tests.id", ondelete="CASCADE")
    )
    trial_index: Mapped[int] = mapped_column(Integer)
    ground_truth_sign_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("signs.id"))
    top1_sign_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("signs.id"), nullable=True
    )
    d1: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    d2_diff_label: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    accepted: Mapped[bool] = mapped_column(Boolean, default=False)
    outcome: Mapped[str] = mapped_column(TrialOutcome)
    capture_frames: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    capture_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    hand_visibility: Mapped[Optional[float]] = mapped_column(Numeric, nullable=True)
    capture_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
