"""
Authentication primitives: password hashing (Argon2) and JWT issuance.

No plaintext credentials are ever stored or logged. Only Argon2 password
hashes are persisted for user accounts. This module has nothing to do
with the digital twin's "assets" — asset credentials are never collected
or stored anywhere in this application (see app/models/models.py).
"""
from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def normalize_email(email: str) -> str:
    """Canonical form used for every lookup, comparison, and stored
    value: trimmed and lowercased. Applied consistently at registration,
    login, demo-user seeding, and lookup so " Demo@DigitalTwin.Local "
    and "demo@digitaltwin.local" always resolve to the same account.
    Never applied to passwords."""
    return email.strip().lower()


def create_access_token(subject: str, expires_minutes: int | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
