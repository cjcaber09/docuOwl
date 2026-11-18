import pytest
from pydantic import ValidationError

from app.config import Settings


def test_plain_postgres_url_gets_the_psycopg_driver():
    settings = Settings(_env_file=None, database_url="postgresql://user:pw@host:5432/postgres")

    assert settings.database_url == "postgresql+psycopg://user:pw@host:5432/postgres"


def test_short_postgres_url_gets_the_psycopg_driver():
    settings = Settings(_env_file=None, database_url="postgres://user:pw@host:5432/postgres")

    assert settings.database_url == "postgresql+psycopg://user:pw@host:5432/postgres"


def test_url_with_driver_is_left_alone():
    url = "postgresql+psycopg://user:pw@host:5432/postgres"

    assert Settings(_env_file=None, database_url=url).database_url == url


def test_missing_database_url_is_an_error(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_short_jwt_secret_is_an_error():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, database_url="postgresql://u:p@h/db", jwt_secret="too-short")


def test_frontend_url_trailing_slash_is_removed():
    settings = Settings(_env_file=None, database_url="postgresql://u:p@h/db", frontend_url="https://owl.app/")

    assert settings.frontend_url == "https://owl.app"


def test_cookies_are_secure_only_for_https():
    local = Settings(_env_file=None, database_url="postgresql://u:p@h/db", frontend_url="http://localhost:5173")
    online = Settings(_env_file=None, database_url="postgresql://u:p@h/db", frontend_url="https://owl.app")

    assert local.cookie_secure is False
    assert online.cookie_secure is True
