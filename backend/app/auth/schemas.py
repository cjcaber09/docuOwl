import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.auth.passwords import MAX_PASSWORD_LENGTH, MIN_PASSWORD_LENGTH


def normalize_email(value: str) -> str:
    return value.strip().lower()


class Credentials(BaseModel):
    email: EmailStr

    @field_validator("email", mode="before")
    @classmethod
    def clean_email(cls, value: object) -> object:
        return normalize_email(value) if isinstance(value, str) else value


class SignupRequest(Credentials):
    password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH)


class LoginRequest(Credentials):
    password: str = Field(min_length=1, max_length=MAX_PASSWORD_LENGTH)


class UserOut(BaseModel):
    """What the frontend may see about a user. Never the password hash."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
