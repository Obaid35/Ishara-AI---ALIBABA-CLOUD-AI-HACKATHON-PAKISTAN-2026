"""Auth dependencies.

The communication screen is deliberately reachable without authentication
(D018) — only /admin and /settings endpoints require a role, and that check
happens here on the server, never only in the UI.
"""

from __future__ import annotations

import uuid

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from .db import get_db
from .models import User
from .security import decode_access_token


def _bearer_token(request: Request) -> str | None:
    header = request.headers.get("Authorization", "")
    if header.lower().startswith("bearer "):
        return header[7:].strip()
    return None


def current_user_optional(request: Request, db: Session = Depends(get_db)) -> User | None:
    token = _bearer_token(request)
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload:
        return None
    try:
        user_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError):
        return None
    user = db.get(User, user_id)
    # Deactivation takes effect immediately, not at token expiry.
    if user is None or not user.is_active:
        return None
    return user


def require_user(user: User | None = Depends(current_user_optional)) -> User:
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authentication required")
    return user


def require_admin(user: User = Depends(require_user)) -> User:
    if user.role_code != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Administrator role required")
    return user


def require_staff(user: User = Depends(require_user)) -> User:
    if user.role_code not in ("admin", "doctor", "staff"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Staff role required")
    return user
