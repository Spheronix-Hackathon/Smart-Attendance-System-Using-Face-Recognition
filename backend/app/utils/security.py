from __future__ import annotations

import hashlib
import os
import random
import string
from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext

from ..config import settings
from .time import now_ist


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    payload = data.copy()
    delta = expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    payload.update({"exp": datetime.now(timezone.utc) + delta})
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def generate_otp() -> str:
    return "".join(random.choices(string.digits, k=6))


def otp_salt() -> str:
    return os.getenv("OTP_SALT", settings.secret_key)


def otp_hash(otp: str, salt: str) -> str:
    return hashlib.sha256(f"{salt}:{otp}".encode("utf-8")).hexdigest()


def verify_otp(otp: str, salt: str, expected_hash: str) -> bool:
    return otp_hash(otp, salt) == expected_hash
