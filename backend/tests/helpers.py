"""Small helpers several test files share."""

from app.models import User


def make_user(db, email: str = "reader@example.com") -> User:
    user = User(email=email, password_hash="not-a-real-hash")
    db.add(user)
    db.commit()
    return user


def sign_up(client, email: str = "reader@example.com"):
    return client.post("/api/auth/signup", json={"email": email, "password": "correct horse battery"})


def upload(client, filename: str, content: bytes):
    return client.post("/api/documents", files={"file": (filename, content)})
