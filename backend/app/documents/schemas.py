import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class DocumentOut(BaseModel):
    """What the Documents page sees. Python names (file_type) leave as camelCase JSON (fileType)."""

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, validate_by_name=True, serialize_by_alias=True)

    id: uuid.UUID
    filename: str
    file_type: str
    status: str
    failure_reason: str | None
    page_count: int | None
    created_at: datetime
