"""Finds the passages most likely to answer a question, among the user's own ready documents."""

import uuid
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Chunk, Document

PASSAGE_LIMIT = 8


@dataclass(frozen=True)
class Passage:
    document_id: uuid.UUID
    filename: str
    text: str
    location: str  # "p. 4", a heading, or "part 3 of 12"


def location_label(page_number: int | None, heading: str | None, position: int, chunk_count: int) -> str:
    if page_number is not None:
        return f"p. {page_number}"
    if heading:
        return heading
    return f"part {position + 1} of {chunk_count}"


def has_ready_documents(db: Session, user_id: uuid.UUID) -> bool:
    found = db.scalar(select(Document.id).where(Document.user_id == user_id, Document.status == "ready").limit(1))
    return found is not None


def find_passages(
    db: Session, user_id: uuid.UUID, query_embedding: list[float], limit: int = PASSAGE_LIMIT
) -> list[Passage]:
    """Exact search: every chunk of the user's ready documents is compared, closest first."""
    chunk_counts = (
        select(Chunk.document_id, func.count().label("chunk_count"))
        .where(Chunk.user_id == user_id)
        .group_by(Chunk.document_id)
        .subquery()
    )
    rows = db.execute(
        select(
            Chunk.text,
            Chunk.page_number,
            Chunk.heading,
            Chunk.position,
            Document.id.label("document_id"),
            Document.filename,
            chunk_counts.c.chunk_count,
        )
        .join(Document, Document.id == Chunk.document_id)
        .join(chunk_counts, chunk_counts.c.document_id == Chunk.document_id)
        .where(Chunk.user_id == user_id, Document.user_id == user_id, Document.status == "ready")
        .order_by(Chunk.embedding.cosine_distance(query_embedding))
        .limit(limit)
    )
    return [
        Passage(
            document_id=row.document_id,
            filename=row.filename,
            text=row.text,
            location=location_label(row.page_number, row.heading, row.position, row.chunk_count),
        )
        for row in rows
    ]
