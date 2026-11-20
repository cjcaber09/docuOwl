from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """Python names (file_type) leave as camelCase JSON (fileType) for the frontend."""

    model_config = ConfigDict(from_attributes=True, alias_generator=to_camel, validate_by_name=True, serialize_by_alias=True)
