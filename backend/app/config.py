"""
Vivid Node Canvas settings
"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Vivid Node Canvas"
    ENVIRONMENT: str = "development"

    POSTGRES_USER: str = "vivid_user"
    POSTGRES_PASSWORD: str = "vivid_password"
    POSTGRES_DB: str = "vivid_canvas"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5433

    CORS_ORIGINS: str = "http://localhost:3100,http://127.0.0.1:3100"
    SEED_AUTEUR_DATA: bool = False
    ALLOW_INPUT_FALLBACKS: bool = True

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
