from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt

from app.config import settings

JWT_ALGORITHM = "HS256"


def encode_token(user_id: UUID) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(seconds=settings.jwt_lifetime_seconds),
        "jti": str(uuid4()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> UUID | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[JWT_ALGORITHM])
        return UUID(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        return None
