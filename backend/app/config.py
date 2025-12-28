"""
Crebit Node Canvas settings
"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Crebit Node Canvas"
    ENVIRONMENT: str = "development"

    POSTGRES_USER: str = "crebit_user"
    POSTGRES_PASSWORD: str = "crebit_password"
    POSTGRES_DB: str = "crebit_canvas"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5433

    CORS_ORIGINS: str = "http://localhost:3100,http://127.0.0.1:3100"
    SEED_AUTEUR_DATA: bool = False
    ALLOW_INPUT_FALLBACKS: bool = True
    VIDEO_SCHEMA_VERSIONS: str = "gemini-video-v1"
    VIDEO_KEYFRAME_PATTERN: str = r"^[A-Za-z0-9][A-Za-z0-9_-]{1,63}$"
    VIDEO_EVIDENCE_REF_PATTERN: str = r"^[a-z][a-z0-9_-]*:.+"

    # Gemini API
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"  # Default for text/general tasks
    GEMINI_VIDEO_MODEL: str = "gemini-2.0-pro-exp"  # For video file interpretation
    GEMINI_ENABLED: bool = True

    # Tavily API (Exa alternative for web search)
    # Get free key at https://tavily.com (1,000 credits/month)
    TAVILY_API_KEY: str = "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"

    # Qdrant Vector Database
    # Local: docker-compose up qdrant (port 6333)
    # Cloud: https://cloud.qdrant.io
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str = ""
    
    # Redis (Added Phase 3)
    REDIS_URL: str = "redis://localhost:6379"

    # Auth / OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = ""
    GOOGLE_OAUTH_SCOPES: str = "openid email profile"
    GOOGLE_AUTH_URL: str = "https://accounts.google.com/o/oauth2/v2/auth"
    GOOGLE_TOKEN_URL: str = "https://oauth2.googleapis.com/token"
    GOOGLE_TOKEN_INFO_URL: str = "https://oauth2.googleapis.com/tokeninfo"

    SESSION_SECRET: str = ""
    SESSION_TTL_SECONDS: int = 60 * 60 * 24 * 7
    OAUTH_STATE_TTL_SECONDS: int = 600
    SESSION_COOKIE_NAME: str = "crebit_session"
    OAUTH_STATE_COOKIE_NAME: str = "crebit_oauth_state"
    AUTH_SUCCESS_REDIRECT: str = "http://localhost:3100"
    AUTH_ERROR_REDIRECT: str = "http://localhost:3100/login?error=auth_failed"
    MASTER_ADMIN_EMAILS: str = ""

    # NICE Payments (나이스페이)
    # Sandbox: S2_af4543a0be4d49a98122e01ec2059a56
    # Production: Get from NICE admin console
    NICEPAY_CLIENT_ID: str = "S2_af4543a0be4d49a98122e01ec2059a56"
    NICEPAY_SECRET_KEY: str = "9eb85607103646da9f9c02b128f2e5ee"
    NICEPAY_API_URL: str = "https://sandbox-api.nicepay.co.kr"
    NICEPAY_MODE: str = "sandbox"  # sandbox | production

    # NotebookLM Enterprise API
    # License: arkain.info@gmail.com (Gemini Enterprise)
    # Project: vivid-canvas-482303
    # Docs: https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs
    NOTEBOOKLM_PROJECT_NUMBER: str = "239259013228"  # vivid-canvas project
    NOTEBOOKLM_LOCATION: str = "global"  # global, us, eu
    NOTEBOOKLM_ENDPOINT: str = "global"  # API endpoint region
    NOTEBOOKLM_CREDENTIALS_PATH: str = ""  # Service account JSON path (optional, uses ADC if empty)

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

    @property
    def MASTER_ADMIN_EMAIL_SET(self) -> set[str]:
        return {email.strip().lower() for email in self.MASTER_ADMIN_EMAILS.split(",") if email.strip()}

    @property
    def COOKIE_SECURE(self) -> bool:
        return self.ENVIRONMENT not in {"development", "local", "dev"}

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
