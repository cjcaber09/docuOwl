"""Reset a user's password from the command line.

    uv run python -m scripts.reset_password reader@example.com
"""

import sys
from getpass import getpass

from app.auth.admin import UnknownUserError, reset_password
from app.database import SessionLocal


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: uv run python -m scripts.reset_password <email>")
        return 2
    password = getpass("New password: ")
    if getpass("Repeat new password: ") != password:
        print("Passwords don't match.")
        return 1
    try:
        with SessionLocal() as session:
            reset_password(session, sys.argv[1], password)
    except (UnknownUserError, ValueError) as error:
        print(error)
        return 1
    print("Password changed. The user is now logged out on every device.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
