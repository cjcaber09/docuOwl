from pwdlib import PasswordHash

MIN_PASSWORD_LENGTH = 10
MAX_PASSWORD_LENGTH = 128

# pwdlib's recommended settings use Argon2: deliberately slow, so guessing passwords is expensive.
_hasher = PasswordHash.recommended()

# Checked against when an email doesn't exist, so "unknown email" takes as long as "wrong password".
DUMMY_HASH = _hasher.hash("owl-dummy-password-used-only-for-timing")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _hasher.verify(password, password_hash)
