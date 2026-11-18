import pytest

from app.auth.admin import UnknownUserError, reset_password
from app.auth.passwords import hash_password, verify_password
from app.models import User


def make_user(db):
    user = User(email="reader@example.com", password_hash=hash_password("old password 123"))
    db.add(user)
    db.commit()
    return user


def test_reset_changes_the_password_and_logs_out_everywhere(db):
    user = make_user(db)
    old_version = user.token_version

    reset_password(db, "  Reader@Example.com ", "new password 456")

    db.refresh(user)
    assert verify_password("new password 456", user.password_hash)
    assert user.token_version == old_version + 1


def test_reset_for_an_unknown_email_fails(db):
    with pytest.raises(UnknownUserError):
        reset_password(db, "nobody@example.com", "new password 456")


def test_reset_rejects_a_short_password(db):
    make_user(db)

    with pytest.raises(ValueError):
        reset_password(db, "reader@example.com", "short")
