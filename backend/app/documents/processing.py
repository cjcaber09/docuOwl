"""The background half of an upload: read the file, split it, embed it, save the chunks."""

import logging
import uuid
from pathlib import Path

from app.config import get_settings
from app.database import SessionLocal
from app.documents.chunking import split_into_chunks
from app.documents.embeddings import Embedder, EmbeddingError
from app.documents.extraction import ExtractionError, extract_text
from app.models import Chunk, Document

logger = logging.getLogger("owl.documents")

EMBEDDING_FAILED = "Owl couldn't process this file right now. Please upload it again later."
UNEXPECTED_FAILURE = "Something went wrong while processing this file. Please upload it again."


def process_document(document_id: uuid.UUID, path: Path, embedder: Embedder) -> None:
    """Runs after the upload response is sent. Always deletes the temporary file."""
    try:
        _process(document_id, path, embedder)
    finally:
        path.unlink(missing_ok=True)


def _process(document_id: uuid.UUID, path: Path, embedder: Embedder) -> None:
    # 1. A quick read, then the database connection goes back to the pool during the slow work.
    with SessionLocal() as session:
        document = session.get(Document, document_id)
        if document is None:
            return  # deleted before we started
        file_type, user_id = document.file_type, document.user_id

    # 2. The slow part, outside any database transaction.
    failure_reason: str | None = None
    try:
        extracted = extract_text(path, file_type, get_settings().max_pdf_pages)
        drafts = split_into_chunks(extracted.sections)
        embeddings = embedder.embed([draft.text for draft in drafts], input_type="document")
        if len(embeddings) != len(drafts):
            raise EmbeddingError(f"expected {len(drafts)} embeddings, got {len(embeddings)}")
    except ExtractionError as error:
        failure_reason = str(error)
    except EmbeddingError:
        logger.exception("Embedding failed for document %s", document_id)
        failure_reason = EMBEDDING_FAILED
    except Exception:
        logger.exception("Processing failed for document %s", document_id)
        failure_reason = UNEXPECTED_FAILURE

    # 3. Save. The row lock means a delete waits until we finish (or we see that it already happened).
    with SessionLocal() as session:
        document = session.get(Document, document_id, with_for_update=True)
        if document is None:
            return  # deleted while we were working: stop quietly
        if failure_reason is None:
            session.add_all(
                Chunk(
                    user_id=user_id,
                    document_id=document_id,
                    text=draft.text,
                    page_number=draft.page_number,
                    heading=draft.heading,
                    position=draft.position,
                    embedding=embedding,
                    embedding_model=embedder.model,
                )
                for draft, embedding in zip(drafts, embeddings)
            )
            document.page_count = extracted.page_count
            document.status = "ready"
        else:
            document.status = "failed"
            document.failure_reason = failure_reason
        session.commit()
