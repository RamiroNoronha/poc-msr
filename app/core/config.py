from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    PROJECT_NAME: str = "POC-MSR"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    GITHUB_TOKEN: str = Field(..., validation_alias="GITHUB_TOKEN")
    GITHUB_API_URL: str = "https://api.github.com"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore")


settings = Settings()  # type: ignore
