"""Test setup. pytest runs this file before any test file."""

import os
from pathlib import Path

from dotenv import dotenv_values

BACKEND_DIR = Path(__file__).resolve().parent.parent

test_env = dotenv_values(BACKEND_DIR / ".env.test")
real_env = dotenv_values(BACKEND_DIR / ".env")

if not test_env.get("DATABASE_URL"):
    raise RuntimeError("Create backend/.env.test with DATABASE_URL pointing at your owl-test Supabase project.")
if test_env["DATABASE_URL"] == real_env.get("DATABASE_URL"):
    raise RuntimeError("Refusing to run: .env.test and .env point at the same database. Tests would wipe your real data.")

# Environment variables win over the .env file, so the app now uses the test database.
os.environ["DATABASE_URL"] = test_env["DATABASE_URL"]
