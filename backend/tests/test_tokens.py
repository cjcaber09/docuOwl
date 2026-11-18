import uuid
from datetime import UTC, datetime, timedelta

import jwt

from app.auth.tokens import create_session_token, read_session_token


def test_token_round_trip():
    user_id = uuid.uuid4()

    claims = read_session_token(create_session_token(user_id, token_version=3))

    assert claims is not None
    assert claims.user_id == user_id
    assert claims.token_version == 3


def test_expired_token_is_rejected():
    eight_days_ago = datetime.now(UTC) - timedelta(days=8)

    assert read_session_token(create_session_token(uuid.uuid4(), 0, now=eight_days_ago)) is None


def test_tampered_token_is_rejected():
    token = create_session_token(uuid.uuid4(), 0)
    tampered = token[:-2] + ("aa" if not token.endswith("aa") else "bb")

    assert read_session_token(tampered) is None


def test_token_signed_with_another_secret_is_rejected():
    forged = jwt.encode({"sub": str(uuid.uuid4()), "ver": 0}, "some-other-secret-" * 4, algorithm="HS256")

    assert read_session_token(forged) is None
