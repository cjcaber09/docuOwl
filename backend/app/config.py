from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Every setting Owl needs, read from environment variables or the .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    # Signs login tokens. Anyone who knows it could forge a login, so it is long, random and secret.
    jwt_secret: str = Field(min_length=32)
    # Where the frontend runs. Used for the CSRF check and to decide if cookies need HTTPS.
    frontend_url: str = "http://localhost:5173"
    # Voyage AI turns text into embeddings (lists of numbers) so Owl can search by meaning.
    voyage_api_key: str = Field(min_length=1)
    embedding_model: str = "voyage-4"
    # Upload limits.
    max_upload_mb: int = Field(default=20, gt=0)
    max_pdf_pages: int = Field(default=500, gt=0)
    max_documents_per_user: int = Field(default=50, gt=0)
    # Claude writes the answers. Create a key at https://platform.claude.com/
    anthropic_api_key: str = Field(min_length=1)
    max_questions_per_day: int = Field(default=100, gt=0)

    @field_validator("database_url")
    @classmethod
    def use_psycopg_driver(cls, value: str) -> str:
        # Supabase gives "postgresql://..."; SQLAlchemy needs to know which driver to use.
        for prefix in ("postgresql://", "postgres://"):
            if value.startswith(prefix):
                return "postgresql+psycopg://" + value.removeprefix(prefix)
        return value

    @field_validator("frontend_url")
    @classmethod
    def remove_trailing_slash(cls, value: str) -> str:
        return value.rstrip("/")

    @property
    def cookie_secure(self) -> bool:
        return self.frontend_url.startswith("https://")


@lru_cache
def get_settings() -> Settings:
    return Settings()
