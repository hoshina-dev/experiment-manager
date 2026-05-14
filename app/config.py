from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    db_path: str = "data.db"
    cors_origin: str = "http://localhost:3000"
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()