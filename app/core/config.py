from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    PROJECT_NAME: str = "POC-MSR"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    GITHUB_TOKEN: str = Field(..., validation_alias="GITHUB_TOKEN")
    GITHUB_API_URL: str = "https://api.github.com"
    CORS_ORIGINS: str = "http://localhost:5173"

    # Limites para expor o backend publicamente.
    MAX_REPO_SIZE_MB: int = 500
    GIT_TIMEOUT_SECONDS: int = 600

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore")


settings = Settings()  # type: ignore
