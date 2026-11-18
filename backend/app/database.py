from collections.abc import Iterator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings

# The engine keeps a small pool of open connections to Postgres and reuses them.
engine = create_engine(get_settings().database_url, pool_pre_ping=True, pool_size=5, max_overflow=5)

# A session is one "conversation" with the database: reads, changes, then commit.
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """Give a route its own session and always close it afterwards."""
    with SessionLocal() as session:
        yield session


def database_is_reachable() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def tables_without_row_level_security(session: Session) -> list[str]:
    """Names of tables in the public schema that have Row Level Security turned off."""
    rows = session.scalars(
        text(
            "SELECT c.relname FROM pg_class c "
            "JOIN pg_namespace n ON n.oid = c.relnamespace "
            "WHERE n.nspname = 'public' AND c.relkind = 'r' AND NOT c.relrowsecurity "
            "ORDER BY c.relname"
        )
    )
    return list(rows)
