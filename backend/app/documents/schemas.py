import uuid
from datetime import datetime

from app.schemas import CamelModel


class DocumentOut(CamelModel):
    """What the Documents page sees."""

    id: uuid.UUID
    filename: str
    file_type: str
    status: str
    failure_reason: str | None
    page_count: int | None
    created_at: datetime
