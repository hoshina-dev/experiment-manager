"""Application configuration loaded from environment variables or a .env file."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the Experiment Manager application.

    Attributes:
        db_path: Filesystem path to the SQLite database file.
        cors_origin: Single allowed CORS origin for the API.
    """

    db_path: str = "data.db"
    cors_origin: str = "http://localhost:3000"

    model_config = SettingsConfigDict(env_prefix="APP_", env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
