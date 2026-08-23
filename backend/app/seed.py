"""Database seeding.

    python -m app.seed              # schema content, everything DISABLED
    python -m app.seed --dev-content  # additionally enable a working dev set

Content is seeded disabled because enabling is a human decision that must be
recorded (D032). --dev-content marks the freeze-list signs Reliable and
enables their messages so the UI can be developed and demonstrated before any
real PSL verification exists. It creates PLACEHOLDER assets which are our own
files, so their rights are recorded truthfully as `own_recording`.

Real PSL videos replacing those placeholders must have their rights re-entered.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import uuid

from sqlalchemy import select, text

from .config import settings
from .content_data import (
    CATEGORIES,
    DEFAULT_SETTINGS,
    DOCTOR_PHRASES,
    INITIAL_RECOGNITION_CONFIG,
    MESSAGES,
    SIGNS,
)
from .db import SessionLocal
from .models import (
    Asset,
    AssetRights,
    DoctorPhrase,
    DoctorPhraseCategory,
    MessageConcept,
    PatientMessage,
    RecognitionConfig,
    Role,
    Setting,
    Sign,
    User,
)
from .security import hash_password

ROLES = [
    ("admin", "Administrator", "Manages content, users and settings."),
    ("doctor", "Doctor", "Uses the communication screen; records test results."),
    ("staff", "Nurse / Staff", "Uses the communication screen."),
]

# The 15-sign freeze list from docs/MESSAGE_MAP.md §1.
FREEZE_LIST = {
    "HEADACHE", "CHEST_PAIN", "STOMACH_PAIN", "FEVER", "COUGH", "VOMITING",
    "DIZZINESS", "BREATHING_PROBLEM", "BLEEDING", "HELP", "YES", "NO",
    "TWO", "DAY", "INJURY",
}


def text_checksum(urdu: str, kokoro: str) -> str:
    return hashlib.md5(f"{urdu}||{kokoro}".encode("utf-8")).hexdigest()


def seed(dev_content: bool = False) -> None:
    db = SessionLocal()
    try:
        # ---------------------------------------------------------- roles
        for code, name, desc in ROLES:
            if not db.get(Role, code):
                db.add(Role(code=code, name=name, description=desc))
        db.flush()

        # ---------------------------------------------------------- admin user
        admin = db.scalar(select(User).where(User.email == settings.seed_admin_email))
        if not admin:
            if settings.seed_admin_password in ("", "change_me"):
                print(
                    "  ! SEED_ADMIN_PASSWORD is unset or still 'change_me'.\n"
                    "    Set it in .env before seeding a real environment.",
                    file=sys.stderr,
                )
            admin = User(
                email=settings.seed_admin_email,
                full_name="Administrator",
                password_hash=hash_password(settings.seed_admin_password or "change_me"),
                role_code="admin",
                is_active=True,
                must_change_password=True,
            )
            db.add(admin)
            db.flush()
            print(f"  + admin user: {settings.seed_admin_email} (must change password)")

        # ---------------------------------------------------------- settings
        for key, value in DEFAULT_SETTINGS.items():
            if not db.get(Setting, key):
                db.add(Setting(key=key, value=value))

        # ---------------------------------------------------------- recognition config
        if not db.scalar(select(RecognitionConfig).limit(1)):
            db.add(RecognitionConfig(is_active=True, **INITIAL_RECOGNITION_CONFIG))

        # ---------------------------------------------------------- signs
        signs: dict[str, Sign] = {
            s.code: s for s in db.scalars(select(Sign)).all()
        }
        for code, urdu, english, demo_critical, notes in SIGNS:
            if code in signs:
                continue
            sign = Sign(
                code=code,
                urdu_meaning=urdu,
                english_meaning=english,
                is_demo_critical=demo_critical,
                notes=notes,
                verification_status="draft",
                reliability_status="candidate",
                is_enabled=False,
            )
            db.add(sign)
            signs[code] = sign
        db.flush()

        # ---------------------------------------------------------- categories
        categories: dict[str, DoctorPhraseCategory] = {
            c.code: c for c in db.scalars(select(DoctorPhraseCategory)).all()
        }
        for code, name_en, name_ur, order in CATEGORIES:
            if code in categories:
                continue
            cat = DoctorPhraseCategory(code=code, name_en=name_en, name_ur=name_ur, sort_order=order)
            db.add(cat)
            categories[code] = cat
        db.flush()

        # ---------------------------------------------------------- messages
        existing_messages = {m.code for m in db.scalars(select(PatientMessage)).all()}
        for code, concepts, urdu, english, kokoro, priority, demo_critical in MESSAGES:
            if code in existing_messages:
                continue
            msg = PatientMessage(
                code=code,
                urdu_text=urdu,
                english_text=english,
                kokoro_input=kokoro,
                priority=priority,
                is_demo_critical=demo_critical,
                is_enabled=False,
            )
            db.add(msg)
            db.flush()
            for position, sign_code in enumerate(concepts, start=1):
                db.add(
                    MessageConcept(
                        message_id=msg.id, position=position, sign_id=signs[sign_code].id
                    )
                )

        # ---------------------------------------------------------- doctor phrases
        existing_phrases = {p.code for p in db.scalars(select(DoctorPhrase)).all()}
        for code, cat_code, urdu, english, priority, demo_critical, order, aliases in DOCTOR_PHRASES:
            if code in existing_phrases:
                continue
            db.add(
                DoctorPhrase(
                    code=code,
                    category_id=categories[cat_code].id,
                    urdu_text=urdu,
                    english_text=english,
                    priority=priority,
                    is_demo_critical=demo_critical,
                    sort_order=order,
                    stt_aliases=list(aliases),
                    verification_status="draft",
                    is_enabled=False,
                )
            )

        db.commit()
        print("  + base content seeded (all disabled)")

        if dev_content:
            _enable_dev_content(db)

    finally:
        db.close()


def _placeholder_asset(db, kind: str, path: str, source: str) -> Asset:
    asset = db.scalar(select(Asset).where(Asset.path == path))
    if asset:
        return asset
    asset = Asset(kind=kind, path=path, checksum="", bytes=0)
    db.add(asset)
    db.flush()
    # Truthful rights: a placeholder we generate ourselves is our own file.
    db.add(
        AssetRights(
            asset_id=asset.id,
            source_name=source,
            permission_status="own_recording",
            permitted_development=True,
            permitted_internal_testing=True,
            permitted_demo_playback=True,
            permitted_public_release=False,
            license_notes="PLACEHOLDER generated by the project. Replace with verified "
                          "PSL content and re-enter rights before any real demo.",
        )
    )
    db.flush()
    return asset


def _enable_dev_content(db) -> None:
    """Development convenience: make the app demonstrable before verification exists."""
    print("  --dev-content: enabling a working development set")

    # 1. Freeze-list signs become reliable + enabled.
    for sign in db.scalars(select(Sign)).all():
        if sign.code in FREEZE_LIST:
            sign.verification_status = "psl_verified"
            sign.reliability_status = "reliable"
            sign.is_enabled = True
            sign.verified_by = "DEV PLACEHOLDER — not a real verification"
    db.commit()

    # 2. P0 messages get placeholder audio and are enabled.
    enabled_messages = 0
    for msg in db.scalars(select(PatientMessage).where(PatientMessage.priority == "p0")).all():
        concept_ids = [
            mc.sign_id
            for mc in db.scalars(
                select(MessageConcept).where(MessageConcept.message_id == msg.id)
            ).all()
        ]
        concept_signs = [db.get(Sign, sid) for sid in concept_ids]
        if not concept_signs or not all(
            s and s.reliability_status == "reliable" and s.is_enabled for s in concept_signs
        ):
            continue
        asset = _placeholder_asset(
            db, "audio_wav", f"assets/audio/{msg.code.lower()}.wav", "PLACEHOLDER audio"
        )
        msg.audio_asset_id = asset.id
        msg.audio_source_checksum = text_checksum(msg.urdu_text, msg.kokoro_input)
        msg.is_enabled = True
        enabled_messages += 1
    db.commit()
    print(f"  + {enabled_messages} messages enabled with placeholder audio")

    # 3. P0 doctor phrases get placeholder videos and are enabled.
    enabled_phrases = 0
    for phrase in db.scalars(select(DoctorPhrase).where(DoctorPhrase.priority == "p0")).all():
        asset = _placeholder_asset(
            db, "psl_video", f"assets/psl-videos/{phrase.code.lower()}.mp4", "PLACEHOLDER video"
        )
        phrase.psl_asset_id = asset.id
        phrase.verification_status = "psl_verified"
        phrase.verified_by = "DEV PLACEHOLDER — not a real verification"
        phrase.is_enabled = True
        enabled_phrases += 1
    db.commit()
    print(f"  + {enabled_phrases} doctor phrases enabled with placeholder videos")
    print(
        "\n  NOTE: dev content is marked 'DEV PLACEHOLDER'. It is not verified PSL\n"
        "        and must not be presented as such. Replace before any real demo."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the PSL Bridge database.")
    parser.add_argument(
        "--dev-content",
        action="store_true",
        help="Enable a working development set so the UI can be demonstrated.",
    )
    args = parser.parse_args()
    print("Seeding PSL Bridge database...")
    seed(dev_content=args.dev_content)
    print("Done.")


if __name__ == "__main__":
    main()
