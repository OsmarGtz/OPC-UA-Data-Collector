import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt as _bcrypt
from jose import JWTError, jwt

from app.config import settings


def hash_password(plain: str) -> str:
    return _bcrypt.hashpw(plain.encode(), _bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return _bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(user_id: int, role: str) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "exp": expire,
        "jti": str(uuid.uuid4()),
    }
    return str(jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM))


def create_refresh_token(user_id: int) -> str:
    expire = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": expire,
        "jti": str(uuid.uuid4()),
    }
    return str(jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM))


def decode_token(token: str) -> dict[str, Any]:
    """Decode and verify a JWT.  Raises JWTError on failure."""
    return dict(jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]))


__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "JWTError",
]
