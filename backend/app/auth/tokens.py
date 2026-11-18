import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt

from app.config import get_settings

SESSION_LIFETIME = timedelta(days=7)
ALGORITHM = "HS256"


@dataclass(frozen=True)
class SessionClaims:
    """What a valid login token tells us: who it is, and which login 'generation' it belongs to."""

    user_id: uuid.UUID
    token_version: int


def create_session_token(user_id: uuid.UUID, token_version: int, now: datetime | None = None) -> str:
    issued_at = now or datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "ver": token_version,
        "iat": issued_at,
        "exp": issued_at + SESSION_LIFETIME,
    }
    return jwt.encode(payload, get_settings().jwt_secret, algorithm=ALGORITHM)


def read_session_token(token: str) -> SessionClaims | None:
    """The claims if the token is genuine and not expired, otherwise None."""
    try:
        payload = jwt.decode(token, get_settings().jwt_secret, algorithms=[ALGORITHM])
        return SessionClaims(user_id=uuid.UUID(payload["sub"]), token_version=int(payload["ver"]))
    except (jwt.InvalidTokenError, KeyError, ValueError):
        return None
