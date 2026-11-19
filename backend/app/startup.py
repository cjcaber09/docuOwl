import shutil
from pathlib import Path

from sqlalchemy import text, update
from sqlalchemy.orm import Session

from app.database import tables_without_row_level_security
from app.documents.validation import UPLOAD_DIR
from app.models import Document

INTERRUPTED_REASON = "Processing was interrupted, please upload again."


class StartupCheckError(RuntimeError):
    """Something is wrong enough that Owl must not start."""


def check_database(session: Session) -> None:
    try:
        session.execute(text("SELECT 1"))
    except Exception as error:
        raise StartupCheckError("Can't reach the database. Check DATABASE_URL in backend/.env.") from error

    vector_installed = session.execute(text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")).first()
    if vector_installed is None:
        raise StartupCheckError("The pgvector extension is missing. Run: uv run alembic upgrade head")

    unprotected = tables_without_row_level_security(session)
    if unprotected:
        raise StartupCheckError(
            "Row Level Security is off for: " + ", ".join(unprotected) + ". Add a migration that enables it."
        )


def mark_interrupted_documents(session: Session) -> int:
    """Only one backend runs, so after a restart nothing can still be processing these."""
    result = session.execute(
        update(Document)
        .where(Document.status == "processing")
        .values(status="failed", failure_reason=INTERRUPTED_REASON)
    )
    session.commit()
    return result.rowcount


def clear_upload_folder(folder: Path = UPLOAD_DIR) -> int:
    """Temporary uploads left by a previous run belong to documents just marked failed."""
    if not folder.exists():
        return 0
    leftovers = list(folder.iterdir())
    for path in leftovers:
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        else:
            path.unlink(missing_ok=True)
    return len(leftovers)
