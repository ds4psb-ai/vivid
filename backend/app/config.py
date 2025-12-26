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
    VIDEO_SCHEMA_VERSIONS: str = "gemini-video-v1"
    VIDEO_KEYFRAME_PATTERN: str = r"^[A-Za-z0-9][A-Za-z0-9_-]{1,63}$"
    VIDEO_EVIDENCE_REF_PATTERN: str = r"^[a-z][a-z0-9_-]*:.+"

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

    @property
    def ALLOWED_VIDEO_SCHEMA_VERSIONS(self) -> List[str]:
        if not self.VIDEO_SCHEMA_VERSIONS or self.VIDEO_SCHEMA_VERSIONS == "*":
            return []
        return [
            version.strip()
            for version in self.VIDEO_SCHEMA_VERSIONS.split(",")
            if version.strip()
        ]

    @property
    def VIDEO_KEYFRAME_REGEX(self) -> str:
        return self.VIDEO_KEYFRAME_PATTERN

    @property
    def VIDEO_EVIDENCE_REF_REGEX(self) -> str:
        return self.VIDEO_EVIDENCE_REF_PATTERN

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
