"""Application configuration loaded from environment variables or a .env file."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    cors_origin: str = "http://localhost:3000"
    otel_endpoint: str | None = None
    db_path: str = "experiments.db"

    model_config = SettingsConfigDict(env_prefix="APP_", env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
