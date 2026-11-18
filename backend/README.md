# Owl backend

Python + FastAPI. Uses Postgres (Supabase, as plain Postgres) with the pgvector extension.
Every table has Row Level Security turned on, so Supabase's public Data API can't read it.

## First-time setup

1. Install uv: `winget install --id=astral-sh.uv -e`
2. Copy `.env.example` to `.env` (your **owl** Supabase project) and to `.env.test` (your separate **owl-test** project).
3. From this folder:

```bash
uv sync                      # install the libraries
uv run alembic upgrade head  # create or update the tables
```

## Everyday commands

| Command | What it does |
|---|---|
| `uv run fastapi dev app/main.py` | Start the API at http://localhost:8000 (docs at /docs) |
| `uv run pytest` | Run the tests (uses `.env.test`, never your real database) |
| `uv run alembic revision --autogenerate -m "describe the change"` | Create a migration after changing `app/models.py` (always read it before applying) |
| `uv run alembic upgrade head` | Apply new migrations to the database in `.env` |
| `uv run alembic downgrade -1` | Undo the most recent migration |
| `uv run python -m scripts.reset_password <email>` | Set a new password for a user and log them out everywhere (run it in PowerShell, which can hide the typed password) |

## When the server refuses to start

At startup the backend checks that the database is reachable, that the `vector` extension is installed,
and that every table has Row Level Security on. If one fails it stops with `StartupCheckError` and a message
saying what to fix. New tables need a migration that runs `ALTER TABLE "<name>" ENABLE ROW LEVEL SECURITY`.
