"""Audit logging.

Append-only. Exists to answer one question: who changed this verified
medical phrase, and when. Credentials are never written here.
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import Request
from sqlalchemy.orm import Session

from .models import AuditLog

_REDACTED = {"password", "password_hash", "token", "refresh_token", "jwt_secret", "secret"}


def _clean(data: dict[str, Any] | None) -> dict[str, Any] | None:
    if not data:
        return None
    return {
        k: ("***" if any(s in k.lower() for s in _REDACTED) else _jsonable(v))
        for k, v in data.items()
    }


def _jsonable(value: Any) -> Any:
    if isinstance(value, uuid.UUID):
        return str(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    return value


def record(
    db: Session,
    *,
    action: str,
    entity_type: str,
    entity_id: str | uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
    request: Request | None = None,
) -> None:
    entry = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id else None,
        before=_clean(before),
        after=_clean(after),
        ip=request.client.host if request and request.client else None,
    )
    db.add(entry)
