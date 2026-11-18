from sqlalchemy import select

from app.models import User

PASSWORD = "correct horse battery"


def signup(client, email="reader@example.com", password=PASSWORD):
    return client.post("/api/auth/signup", json={"email": email, "password": password})


def login(client, email="reader@example.com", password=PASSWORD):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def test_signup_creates_the_account_and_logs_in(client):
    response = signup(client)

    assert response.status_code == 201
    assert response.json()["email"] == "reader@example.com"
    assert client.get("/api/auth/me").json()["email"] == "reader@example.com"


def test_signup_stores_the_email_trimmed_and_lowercase(client):
    assert signup(client, email="  Reader@Example.COM ").json()["email"] == "reader@example.com"


def test_signup_never_stores_the_plain_password(client, db):
    signup(client)

    user = db.scalar(select(User))
    assert user.password_hash != PASSWORD
    assert user.password_hash.startswith("$argon2")


def test_signup_rejects_a_short_password(client):
    assert signup(client, password="short").status_code == 422


def test_signup_rejects_an_email_that_already_has_an_account(client):
    signup(client)

    response = signup(client)

    assert response.status_code == 409
    assert response.json() == {"detail": "An account with this email already exists."}


def test_session_cookie_is_hidden_from_page_scripts(client):
    set_cookie = signup(client).headers["set-cookie"].lower()

    assert "owl_session=" in set_cookie
    assert "httponly" in set_cookie
    assert "samesite=lax" in set_cookie


def test_login_with_the_right_password(client):
    signup(client)
    client.cookies.clear()

    assert login(client).status_code == 200
    assert client.get("/api/auth/me").status_code == 200


def test_unknown_email_and_wrong_password_get_the_same_answer(client):
    signup(client)
    client.cookies.clear()

    wrong_password = login(client, password="not the password")
    unknown_email = login(client, email="nobody@example.com")

    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json() == {"detail": "Wrong email or password."}


def test_me_without_a_login_is_401(client):
    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json() == {"detail": "Please log in."}


def test_logout_ends_the_session(client):
    signup(client)

    assert client.post("/api/auth/logout").status_code == 204
    assert client.get("/api/auth/me").status_code == 401


def test_old_logins_stop_working_when_token_version_changes(client, db):
    signup(client)
    user = db.scalar(select(User))
    user.token_version += 1
    db.commit()

    assert client.get("/api/auth/me").status_code == 401


def test_too_many_login_attempts_are_slowed_down(client):
    signup(client)
    client.cookies.clear()

    answers = [login(client, password="not the password").status_code for _ in range(11)]

    assert answers[:10] == [401] * 10
    assert answers[10] == 429
