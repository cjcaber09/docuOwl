"""Test setup. pytest runs this file before any test file."""

import os
from pathlib import Path

import pytest
from dotenv import dotenv_values
from sqlalchemy import text

BACKEND_DIR = Path(__file__).resolve().parent.parent

test_env = dotenv_values(BACKEND_DIR / ".env.test")
real_env = dotenv_values(BACKEND_DIR / ".env")

if not test_env.get("DATABASE_URL"):
    raise RuntimeError("Create backend/.env.test with DATABASE_URL pointing at your owl-test Supabase project.")
if test_env["DATABASE_URL"] == real_env.get("DATABASE_URL"):
    raise RuntimeError("Refusing to run: .env.test and .env point at the same database. Tests would wipe your real data.")

# Environment variables win over the .env file, so the app now uses the test database.
os.environ["DATABASE_URL"] = test_env["DATABASE_URL"]

# A throwaway signing secret for tests only, and the frontend address the CSRF check expects.
os.environ["JWT_SECRET"] = test_env.get("JWT_SECRET") or "test-only-secret-never-used-outside-tests-0123456789"
os.environ["FRONTEND_URL"] = "http://localhost:5173"
# Tests never call Voyage (a fake embedder stands in), but the setting must exist.
os.environ["VOYAGE_API_KEY"] = "test-key-never-sent-to-voyage"


@pytest.fixture(scope="session", autouse=True)
def migrated_test_database():
    """Bring the test database up to the latest migration once, before any test runs."""
    from alembic import command
    from alembic.config import Config

    command.upgrade(Config(str(BACKEND_DIR / "alembic.ini")), "head")


@pytest.fixture
def db():
    """A database session for one test. Every table is emptied afterwards."""
    from app.database import SessionLocal, engine
    from app.models import Base

    with SessionLocal() as session:
        yield session

    table_names = ", ".join(table.name for table in Base.metadata.sorted_tables)
    with engine.begin() as connection:
        connection.execute(text(f"TRUNCATE {table_names} CASCADE"))


@pytest.fixture
def client(db):
    """A pretend browser on Owl's own page. Uses `db` so every table is emptied afterwards."""
    from fastapi.testclient import TestClient

    from app.auth.rate_limit import reset_all_limiters
    from app.config import get_settings
    from app.main import app

    reset_all_limiters()
    return TestClient(app, headers={"Origin": get_settings().frontend_url})
