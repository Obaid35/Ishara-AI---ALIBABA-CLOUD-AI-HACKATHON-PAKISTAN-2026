"""Shared field types.

`AccountEmail` is deliberately more permissive than pydantic's EmailStr:
hospital staff accounts legitimately use internal domains such as
`admin@isharaai.local` or `nurse@hospital.internal`, which strict RFC
validators reject as special-use names. We validate shape, not deliverability.
"""

from __future__ import annotations

import re
from typing import Annotated

from pydantic import AfterValidator

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validate_account_email(value: str) -> str:
    value = (value or "").strip()
    if not _EMAIL_RE.match(value):
        raise ValueError("Enter a valid email address, for example name@hospital.local")
    if len(value) > 254:
        raise ValueError("Email address is too long")
    return value.lower()


AccountEmail = Annotated[str, AfterValidator(_validate_account_email)]
