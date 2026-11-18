from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.passwords import MAX_PASSWORD_LENGTH, MIN_PASSWORD_LENGTH, hash_password
from app.auth.schemas import normalize_email
from app.models import User


class UnknownUserError(LookupError):
    """No account has that email."""


def reset_password(session: Session, email: str, new_password: str) -> None:
    """Set a new password and log the user out on every device."""
    if not MIN_PASSWORD_LENGTH <= len(new_password) <= MAX_PASSWORD_LENGTH:
        raise ValueError(f"Passwords must be {MIN_PASSWORD_LENGTH}–{MAX_PASSWORD_LENGTH} characters.")
    user = session.scalar(select(User).where(User.email == normalize_email(email)))
    if user is None:
        raise UnknownUserError(f"No account with the email {email.strip()}.")
    user.password_hash = hash_password(new_password)
    user.token_version += 1
    session.commit()
