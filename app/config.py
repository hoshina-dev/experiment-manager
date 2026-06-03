"""Application configuration loaded from environment variables or a .env file."""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _dsn_to_async_url(dsn: str) -> str:
    """Convert a PostgreSQL key=value DSN to a SQLAlchemy async URL.

    Input:  host=localhost user=postgres password=postgres dbname=expman port=5432 sslmode=disable
    Output: postgresql+psycopg://postgres:postgres@localhost:5432/expman?client_encoding=utf8
    """
    parts: dict[str, str] = {}
    for token in dsn.strip().split():
        key, _, val = token.partition("=")
        parts[key] = val
    user = parts.get("user", "")
    password = parts.get("password", "")
    host = parts.get("host", "localhost")
    port = parts.get("port", "5432")
    dbname = parts.get("dbname", "")
    base = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{dbname}"
    query = "client_encoding=utf8"
    sslmode = parts.get("sslmode")
    if sslmode:
        query = f"sslmode={sslmode}&{query}"
    return f"{base}?{query}"


class Settings(BaseSettings):
    port: int = 8000
    cors_origins: str = "http://localhost:3000"
    otel_endpoint: str | None = None
    data_source_name: str = Field(default="")
    test_data_source_name: str | None = None

    @field_validator("data_source_name", mode="after")
    @classmethod
    def require_data_source_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("DATA_SOURCE_NAME environment variable is required")
        return v

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    @property
    def database_url(self) -> str:
        return _dsn_to_async_url(self.data_source_name)

    @property
    def test_database_url(self) -> str | None:
        if self.test_data_source_name:
            return _dsn_to_async_url(self.test_data_source_name)
        return None

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


settings = Settings()
