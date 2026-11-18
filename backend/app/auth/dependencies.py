from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.tokens import read_session_token
from app.database import get_db
from app.models import User

SESSION_COOKIE = "owl_session"

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(db: DbSession, owl_session: Annotated[str | None, Cookie()] = None) -> User:
    """The logged-in user, or a 401 if the cookie is missing, forged, expired or from before a password reset."""
    claims = read_session_token(owl_session) if owl_session else None
    user = db.get(User, claims.user_id) if claims else None
    if user is None or user.token_version != claims.token_version:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Please log in.")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
