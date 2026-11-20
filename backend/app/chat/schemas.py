import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models import Message
from app.schemas import CamelModel


class QuestionIn(BaseModel):
    content: str = Field(min_length=1, max_length=4000)

    @field_validator("content", mode="before")
    @classmethod
    def strip_spaces(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class CitationOut(CamelModel):
    filename: str
    location: str
    quote: str
    deleted: bool = False


class MessageOut(CamelModel):
    id: uuid.UUID
    role: str
    content: str
    citations: list[CitationOut]
    created_at: datetime


class ConversationSummary(CamelModel):
    id: uuid.UUID
    title: str
    updated_at: datetime


class ConversationOut(CamelModel):
    id: uuid.UUID
    title: str
    messages: list[MessageOut]


def message_out(message: Message, existing_document_ids: set[str]) -> MessageOut:
    """A saved message for the frontend. A citation whose file is gone is marked deleted."""
    citations = [
        CitationOut(
            filename=snapshot["filename"],
            location=snapshot["location"],
            quote=snapshot["quote"],
            deleted=snapshot["documentId"] not in existing_document_ids,
        )
        for snapshot in message.citations
    ]
    return MessageOut(
        id=message.id, role=message.role, content=message.content, citations=citations, created_at=message.created_at
    )
