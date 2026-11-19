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


def test_upload_settings_have_the_spec_defaults():
    settings = Settings(_env_file=None, database_url="postgresql://u:p@h/db")

    assert settings.embedding_model == "voyage-4"
    assert settings.max_upload_mb == 20
    assert settings.max_pdf_pages == 500
    assert settings.max_documents_per_user == 50


def test_missing_voyage_key_is_an_error(monkeypatch):
    monkeypatch.delenv("VOYAGE_API_KEY", raising=False)

    with pytest.raises(ValidationError):
        Settings(_env_file=None, database_url="postgresql://u:p@h/db")


def test_daily_question_limit_defaults_to_100():
    assert Settings(_env_file=None, database_url="postgresql://u:p@h/db").max_questions_per_day == 100


def test_missing_anthropic_key_is_an_error(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    with pytest.raises(ValidationError):
        Settings(_env_file=None, database_url="postgresql://u:p@h/db")


def test_demo_mode_needs_no_anthropic_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    settings = Settings(_env_file=None, database_url="postgresql://u:p@h/db", chat_model="demo")

    assert settings.chat_model == "demo"
