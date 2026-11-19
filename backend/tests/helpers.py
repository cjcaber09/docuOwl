"""Small helpers several test files share."""

from app.models import User


def make_user(db, email: str = "reader@example.com") -> User:
    user = User(email=email, password_hash="not-a-real-hash")
    db.add(user)
    db.commit()
    return user
