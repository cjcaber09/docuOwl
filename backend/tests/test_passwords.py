from app.auth.passwords import hash_password, verify_password


def test_hash_is_not_the_password_and_verifies():
    password_hash = hash_password("correct horse battery")

    assert password_hash != "correct horse battery"
    assert password_hash.startswith("$argon2")
    assert verify_password("correct horse battery", password_hash) is True


def test_wrong_password_does_not_verify():
    assert verify_password("wrong password!", hash_password("correct horse battery")) is False
