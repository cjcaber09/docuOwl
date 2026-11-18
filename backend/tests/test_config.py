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
