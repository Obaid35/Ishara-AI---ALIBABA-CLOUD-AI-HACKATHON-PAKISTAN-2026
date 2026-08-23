"""Staff authentication.

No public signup route exists — accounts are created by an admin (D019).
Login never gates the communication screen.
"""

from __future__ import annotations

import datetime as dt
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import audit
from ..db import get_db
from ..schemas import AccountEmail
from ..deps import require_user
from ..models import AuthSession, PasswordReset, User
from ..security import (
    create_access_token,
    hash_password,
    hash_token,
    new_refresh_token,
    refresh_expiry,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: AccountEmail
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class ForgotPasswordRequest(BaseModel):
    email: AccountEmail


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class RefreshRequest(BaseModel):
    refresh_token: str


def _user_payload(user: User) -> dict:
    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role_code,
        "must_change_password": user.must_change_password,
    }


@router.post("/login")
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email))

    if not user or not verify_password(payload.password, user.password_hash):
        audit.record(
            db,
            action="login_failed",
            entity_type="user",
            entity_id=payload.email,
            request=request,
        )
        db.commit()
        # Same message either way — do not reveal whether the account exists.
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")

    if not user.is_active:
        audit.record(
            db, action="login_blocked", entity_type="user", entity_id=str(user.id), request=request
        )
        db.commit()
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This account is deactivated")

    raw_refresh, refresh_hash = new_refresh_token()
    db.add(
        AuthSession(
            user_id=user.id,
            refresh_token_hash=refresh_hash,
            expires_at=refresh_expiry(),
            user_agent=request.headers.get("User-Agent"),
            ip=request.client.host if request.client else None,
        )
    )
    user.last_login_at = dt.datetime.now(dt.timezone.utc)
    audit.record(db, action="login", entity_type="user", entity_id=str(user.id),
                 user_id=user.id, request=request)
    db.commit()

    return {
        "access_token": create_access_token(user.id, user.role_code),
        "refresh_token": raw_refresh,
        "token_type": "bearer",
        "user": _user_payload(user),
    }


@router.post("/refresh")
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    session = db.scalar(
        select(AuthSession).where(AuthSession.refresh_token_hash == hash_token(payload.refresh_token))
    )
    now = dt.datetime.now(dt.timezone.utc)
    if not session or session.revoked_at is not None or session.expires_at <= now:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expired, please sign in again")

    user = db.get(User, session.user_id)
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This account is deactivated")

    return {
        "access_token": create_access_token(user.id, user.role_code),
        "token_type": "bearer",
        "user": _user_payload(user),
    }


@router.post("/logout")
def logout(payload: RefreshRequest, request: Request, db: Session = Depends(get_db),
           user: User = Depends(require_user)):
    session = db.scalar(
        select(AuthSession).where(AuthSession.refresh_token_hash == hash_token(payload.refresh_token))
    )
    if session:
        session.revoked_at = dt.datetime.now(dt.timezone.utc)
    audit.record(db, action="logout", entity_type="user", entity_id=str(user.id),
                 user_id=user.id, request=request)
    db.commit()
    return {"ok": True}


@router.get("/me")
def me(user: User = Depends(require_user)):
    return _user_payload(user)


@router.post("/change-password")
def change_password(payload: ChangePasswordRequest, request: Request,
                    db: Session = Depends(get_db), user: User = Depends(require_user)):
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Current password is incorrect")
    if len(payload.new_password) < 8:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "New password must be at least 8 characters")

    user.password_hash = hash_password(payload.new_password)
    user.must_change_password = False

    # Changing a password revokes every other session.
    for session in db.scalars(select(AuthSession).where(AuthSession.user_id == user.id)).all():
        if session.revoked_at is None:
            session.revoked_at = dt.datetime.now(dt.timezone.utc)

    audit.record(db, action="change_password", entity_type="user", entity_id=str(user.id),
                 user_id=user.id, request=request)
    db.commit()
    return {"ok": True}


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email))
    response = {
        "ok": True,
        "message": "If that account exists, a reset token has been created.",
    }

    if not user or not user.is_active:
        return response

    raw = secrets.token_urlsafe(32)
    db.add(
        PasswordReset(
            user_id=user.id,
            token_hash=hash_token(raw),
            expires_at=dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=1),
        )
    )
    audit.record(db, action="password_reset_requested", entity_type="user", entity_id=str(user.id))
    db.commit()

    # No mail transport in the hackathon build. The token is returned so an
    # admin can hand it over in person; wire this to email before deployment.
    response["dev_token"] = raw
    response["dev_note"] = "No mail transport configured — deliver this token manually."
    return response


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    reset = db.scalar(
        select(PasswordReset).where(PasswordReset.token_hash == hash_token(payload.token))
    )
    now = dt.datetime.now(dt.timezone.utc)
    if not reset or reset.used_at is not None or reset.expires_at <= now:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This reset link is invalid or expired")
    if len(payload.new_password) < 8:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "New password must be at least 8 characters")

    user = db.get(User, reset.user_id)
    if not user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This reset link is invalid")

    user.password_hash = hash_password(payload.new_password)
    user.must_change_password = False
    reset.used_at = now

    for session in db.scalars(select(AuthSession).where(AuthSession.user_id == user.id)).all():
        if session.revoked_at is None:
            session.revoked_at = now

    audit.record(db, action="password_reset", entity_type="user", entity_id=str(user.id))
    db.commit()
    return {"ok": True}
