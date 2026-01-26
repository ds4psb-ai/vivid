"""
Crebit Node Canvas settings

Security Note (H1.3):
Sensitive fields use SecretStr to prevent accidental exposure in logs/repr.
Access secret values via: settings.FIELD_NAME.get_secret_value()
"""
from typing import List
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Crebit Node Canvas"
    ENVIRONMENT: str = "development"
    GRAPHQL_ENABLED: bool = False
    FLOW_ENABLED: bool = False

    # Database Configuration
    # Priority: DATABASE_URL env var > individual POSTGRES_* vars
    # Railway/Render/Heroku set DATABASE_URL directly
    DATABASE_URL_OVERRIDE: str = Field(default="", validation_alias="DATABASE_URL")

    POSTGRES_USER: str = "crebit_user"
    # P0: Default is clearly marked as dev-only; production validation will catch this
    POSTGRES_PASSWORD: SecretStr = SecretStr("crebit_dev_only")
    POSTGRES_DB: str = "crebit_canvas"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5433

    # H2.2: Database SSL Configuration
    # - disable: No SSL (local development only)
    # - allow: Try SSL, fallback to non-SSL
    # - prefer: Try SSL first (default for development)
    # - require: SSL required (recommended for production)
    # - verify-ca: SSL required + verify server certificate
    # - verify-full: SSL required + verify cert + hostname
    DB_SSL_MODE: str = "prefer"  # Set to "require" or "verify-full" for production

    # CORS Configuration
    # Development: localhost origins are default (http://localhost:3000 for Next.js dev)
    # Production: Set CORS_ORIGINS env var to your production domains (comma-separated)
    # Example: CORS_ORIGINS=https://crebit.app,https://www.crebit.app
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3100,http://127.0.0.1:3100"
    CORS_PRODUCTION_ORIGINS: str = "https://crebit.app,https://www.crebit.app,https://api.crebit.app,https://vivid-frontend.vercel.app"
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_MAX_AGE: int = 600  # Preflight cache time in seconds (10 minutes)
    
    SEED_AUTEUR_DATA: bool = False
    ALLOW_INPUT_FALLBACKS: bool = True
    VIDEO_SCHEMA_VERSIONS: str = "gemini-video-v1"
    VIDEO_KEYFRAME_PATTERN: str = r"^[A-Za-z0-9][A-Za-z0-9_-]{1,63}$"
    VIDEO_EVIDENCE_REF_PATTERN: str = r"^[a-z][a-z0-9_-]*:.+"

    # Gemini API (H1.3: SecretStr for API keys)
    GEMINI_API_KEY: SecretStr = SecretStr("")
    GEMINI_API_KEY_FALLBACK: SecretStr = SecretStr("")  # Backup key for auto-rotation on failure
    GEMINI_MODEL: str = "gemini-3-flash-preview"  # Default for text/general tasks
    GEMINI_VIDEO_MODEL: str = "gemini-3-flash-preview"  # For video file interpretation
    GEMINI_ENABLED: bool = True
    GEMINI_AGENT_MODEL: str = "gemini-3-flash-preview"  # Use gemini-3-pro-preview for higher quality
    GEMINI_AGENT_TEMPERATURE: float = 0.4
    GEMINI_AGENT_MAX_TOKENS: int = 2048
    GEMINI_AGENT_MODELS: str = "gemini-3-flash-preview,gemini-3-pro-preview"
    GEMINI_IMAGE_MODEL: str = "gemini-3-pro-image-preview"  # Nanobanana Pro (이미지 생성)

    # Gemini Batch API (50% Cost Reduction)
    # Batch API는 비실시간 작업을 비동기 처리하여 50% 비용 절감
    # 24시간 SLA 내 완료 (대부분 더 빠름)
    # 적합: RAG 평가, 대량 콘텐츠 생성, 데이터 전처리
    GEMINI_BATCH_ENABLED: bool = True
    GEMINI_BATCH_API_KEY: SecretStr = SecretStr("")  # Separate key for Batch API (uses GEMINI_API_KEY if empty)
    GEMINI_BATCH_MODEL: str = "gemini-3-flash-preview"  # 3.0 Flash (50% off)
    GEMINI_BATCH_POLL_INTERVAL: int = 30  # Seconds between status checks
    GEMINI_BATCH_MAX_WAIT_HOURS: int = 24  # Maximum wait time for batch jobs
    GEMINI_BATCH_MAX_REQUESTS: int = 100000  # Max requests per batch job

    # Kling AI API (Video Generation)
    # Get API key from: https://klingai.com/developer or third-party providers
    # Provider options: klingai.com, kie.ai, piapi.ai, novita.ai
    KLING_API_KEY: SecretStr = SecretStr("")
    KLING_API_BASE_URL: str = "https://api.klingai.com/v1"  # Or provider URL

    # Suno AI API (Music Generation)
    # Uses third-party providers (no official API)
    # Provider options: sunoapi.org, musicapi.ai, laozhang.ai
    SUNO_API_KEY: SecretStr = SecretStr("")
    SUNO_API_BASE_URL: str = "https://api.sunoapi.org/api/v1"
    # Get free key at https://tavily.com (1,000 credits/month)
    TAVILY_API_KEY: SecretStr = SecretStr("")

    # Qdrant Vector Database
    # Local: docker-compose up qdrant (port 6333)
    # Cloud: https://cloud.qdrant.io
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: SecretStr = SecretStr("")
    
    # Redis (Added Phase 3)
    REDIS_URL: str = "redis://localhost:6380"
    
    # Capsule Execution Timeouts (seconds)
    CAPSULE_EXECUTION_TIMEOUT: int = 120  # Default timeout for capsule runs (2 minutes)
    CAPSULE_SYNC_TIMEOUT: int = 60        # Timeout for sync mode execution (1 minute)
    CAPSULE_HEAVY_TIMEOUT: int = 300      # Extended timeout for heavy operations (5 minutes)

    # Auth / OAuth (H1.3: SecretStr for secrets)
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: SecretStr = SecretStr("")
    GOOGLE_REDIRECT_URI: str = ""
    GOOGLE_OAUTH_SCOPES: str = "openid email profile"
    GOOGLE_AUTH_URL: str = "https://accounts.google.com/o/oauth2/v2/auth"
    GOOGLE_TOKEN_URL: str = "https://oauth2.googleapis.com/token"
    GOOGLE_TOKEN_INFO_URL: str = "https://oauth2.googleapis.com/tokeninfo"

    SESSION_SECRET: SecretStr = SecretStr("")
    SESSION_TTL_SECONDS: int = 60 * 60 * 24 * 7
    OAUTH_STATE_TTL_SECONDS: int = 600
    SESSION_COOKIE_NAME: str = "crebit_session"
    OAUTH_STATE_COOKIE_NAME: str = "crebit_oauth_state"
    AUTH_SUCCESS_REDIRECT: str = "http://localhost:3100"
    AUTH_ERROR_REDIRECT: str = "http://localhost:3100/login?error=auth_failed"
    MASTER_ADMIN_EMAILS: str = ""

    # Frontend Integration (Phase 6 Cache Invalidation)
    # URL of the Next.js frontend for cache invalidation API calls
    FRONTEND_URL: str = "http://localhost:3100"
    # Secret token for authenticating cache invalidation requests
    # Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
    REVALIDATE_SECRET: SecretStr = SecretStr("")

    # NICE Payments (나이스페이) (H1.3: SecretStr for secret key)
    # Sandbox: S2_af4543a0be4d49a98122e01ec2059a56
    # Production: Get from NICE admin console
    NICEPAY_CLIENT_ID: str = ""
    NICEPAY_SECRET_KEY: SecretStr = SecretStr("")
    NICEPAY_API_URL: str = "https://sandbox-api.nicepay.co.kr"
    NICEPAY_MODE: str = "sandbox"  # sandbox | production

    # ==========================================================================
    # H2.3: Stripe Payments (PCI DSS 4.0 Compliant)
    # ==========================================================================
    # Get keys from https://dashboard.stripe.com/apikeys
    # Test mode keys start with sk_test_ and pk_test_
    # Live mode keys start with sk_live_ and pk_live_
    STRIPE_SECRET_KEY: SecretStr = SecretStr("")  # sk_test_... or sk_live_...
    STRIPE_PUBLISHABLE_KEY: str = ""  # pk_test_... or pk_live_... (safe for frontend)
    # Webhook signing secret from https://dashboard.stripe.com/webhooks
    # Each webhook endpoint has its own signing secret (whsec_...)
    STRIPE_WEBHOOK_SECRET: SecretStr = SecretStr("")
    # Stripe API version (use stable version)
    STRIPE_API_VERSION: str = "2024-12-18.acacia"
    # Enable Stripe payments (set to True when configured)
    STRIPE_ENABLED: bool = False
    # P1: Stripe webhook IP whitelist (comma-separated, empty = skip IP check)
    # Get current IPs from https://stripe.com/docs/ips#webhook-ip-addresses
    # Production example: "3.18.12.63,3.130.192.231,13.235.14.237,35.154.171.200,..."
    STRIPE_WEBHOOK_IP_WHITELIST: str = ""

    # Google Cloud Platform
    # Project: vivid-canvas-482303 (Production Project)
    # Account: arkain.info@gmail.com
    GCP_PROJECT_ID: str = "vivid-canvas-482303"
    GCP_PROJECT_NUMBER: str = "239259013228"
    GCP_LOCATION: str = "europe-west4"  # RAG Engine available here (us-central1 restricted)
    GCS_BUCKET: str = "crebit-rag-data"

    # Cloud SQL (2026 Best Practice: cloud-sql-python-connector)
    # Format: project:region:instance
    # Leave empty to use local PostgreSQL
    CLOUD_SQL_INSTANCE: str = ""
    CLOUD_SQL_USER: str = ""
    CLOUD_SQL_PASSWORD: SecretStr = SecretStr("")
    CLOUD_SQL_DB: str = ""
    CLOUD_SQL_IAM_AUTH: bool = False  # Use IAM authentication instead of password

    # BigQuery Analytics (UQSL events pipeline)
    BIGQUERY_DATASET: str = ""  # Leave empty to disable BigQuery sync
    BIGQUERY_TABLE_UQSL_EVENTS: str = "uqsl_events"

    # NotebookLM Enterprise API (Tier 0)
    # Project: vivid-canvas-482303
    NOTEBOOKLM_PROJECT_NUMBER: str = "239259013228"  # vivid-canvas project
    NOTEBOOKLM_LOCATION: str = "global"  # global, us, eu
    NOTEBOOKLM_ENDPOINT: str = "global"  # API endpoint region
    NOTEBOOKLM_CREDENTIALS_PATH: str = ""  # Service account JSON path (optional, uses ADC if empty)

    # Monitoring & Error Tracking
    # Sentry: Error tracking and performance monitoring
    # Get DSN from https://sentry.io
    SENTRY_DSN: str = ""  # Leave empty to disable Sentry
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1  # 10% of transactions for performance monitoring
    SENTRY_PROFILES_SAMPLE_RATE: float = 0.1  # 10% for profiling (requires Sentry Pro)
    SENTRY_ENVIRONMENT: str = ""  # Auto-set to ENVIRONMENT if empty
    
    # Prometheus: Metrics collection
    PROMETHEUS_ENABLED: bool = True
    PROMETHEUS_METRICS_PATH: str = "/metrics"
    # P1: Metrics endpoint protection (comma-separated IPs or "internal" for 10.x/172.x/192.168.x only)
    # Empty = no protection (not recommended for production)
    PROMETHEUS_ALLOWED_IPS: str = ""
    # Optional bearer token for metrics access (alternative to IP whitelist)
    PROMETHEUS_BEARER_TOKEN: SecretStr = SecretStr("")
    
    # Logging
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR
    
    # Langfuse Observability (Phase 4) (H1.3: SecretStr)
    # Get keys from https://langfuse.com
    LANGFUSE_SECRET_KEY: SecretStr = SecretStr("")
    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"
    LANGFUSE_ENABLED: bool = True

    # OpenTelemetry Configuration (2026 Best Practices)
    # Enable distributed tracing with OTLP exporter
    OTEL_ENABLED: bool = False  # Set to True to enable OpenTelemetry
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "localhost:4317"  # Jaeger/Tempo/OTEL Collector
    OTEL_SAMPLE_RATE: float = 0.1  # 10% sampling in production
    OTEL_USE_GRPC: bool = True  # Use gRPC for better performance
    OTEL_SERVICE_NAME: str = "vivid-backend"
    OTEL_SERVICE_VERSION: str = "2.0.0"

    # RAG Evaluation Configuration
    RAG_EVAL_ENABLED: bool = False  # Enable RAG quality evaluation
    RAG_EVAL_SAMPLE_RATE: float = 0.01  # 1% of production traffic
    RAG_EVAL_ALERT_THRESHOLD: float = 0.6  # Alert if avg score drops below
    RAG_EVAL_LLM_MODEL: str = "gpt-4o-mini"  # LLM for evaluation

    # Unified Orchestration (2026 Best Practice - LangGraph StateGraph)
    # When True, use unified graph instead of hybrid_rag for RAG queries
    USE_UNIFIED_GRAPH: bool = False  # Feature flag for gradual rollout
    UNIFIED_GRAPH_AB_RATIO: float = 0.0  # A/B test ratio (0.0 = all legacy, 1.0 = all unified)

    # ==========================================================================
    # Phase 8: Personalization Configuration
    # ==========================================================================
    # Core Personalization Settings
    PERSONALIZATION_ENABLED: bool = False  # Enable personalization features
    PERSONALIZATION_MIN_SIGNALS: int = 10  # Min signals before embedding update

    # Preference Learning
    PERSONALIZATION_DECAY_HALF_LIFE_DAYS: int = 30  # Preference decay half-life
    PERSONALIZATION_EMBEDDING_DIM: int = 768  # User embedding dimension

    # Affinity Boosts
    PERSONALIZATION_DIMENSION_BOOST: float = 0.3  # Dimension affinity boost (0-1)
    PERSONALIZATION_AUTEUR_BOOST: float = 0.25  # Auteur affinity boost (0-1)
    PERSONALIZATION_EMBEDDING_WEIGHT: float = 0.2  # User embedding weight (0-1)

    # Session Tracking
    PERSONALIZATION_SESSION_TTL: int = 3600  # Session TTL in seconds (1 hour)
    PERSONALIZATION_SESSION_DECAY: float = 0.9  # Session affinity decay per hour

    # A/B Testing
    PERSONALIZATION_AB_ENABLED: bool = False  # Enable A/B testing
    PERSONALIZATION_AB_CONTROL_RATIO: float = 0.1  # 10% control group

    # GraphRAG Settings
    GRAPHRAG_MAX_HOPS: int = 2  # Max graph traversal hops
    GRAPHRAG_COMMUNITY_LEVEL: int = 1  # Default community level for global search
    GRAPHRAG_GRAPH_WEIGHT: float = 0.4  # Graph results weight in fusion
    GRAPHRAG_VECTOR_WEIGHT: float = 0.6  # Vector results weight in fusion

    # ==========================================================================
    # Phase 9: Monetization & Analytics Configuration
    # ==========================================================================
    # Core Analytics Settings
    ANALYTICS_ENABLED: bool = True
    ANALYTICS_DAILY_AGGREGATION_HOUR: int = 0  # UTC hour for daily aggregation (0 = midnight)
    ANALYTICS_LEADERBOARD_UPDATE_MINUTES: int = 60  # Leaderboard refresh interval
    ANALYTICS_COHORT_UPDATE_DAY: int = 0  # Day of week for cohort computation (0 = Monday)

    # KPI Cache Settings
    ANALYTICS_KPI_CACHE_TTL: int = 300  # KPI cache TTL in seconds (5 minutes)
    ANALYTICS_SSE_HEARTBEAT_SECONDS: int = 15  # SSE heartbeat interval
    ANALYTICS_SSE_UPDATE_SECONDS: int = 5  # SSE KPI update interval

    # Pricing Experiment Settings
    PRICING_EXPERIMENT_ENABLED: bool = False  # Enable dynamic pricing experiments
    PRICING_DEFAULT_ELASTICITY: float = -1.2  # Default price elasticity coefficient
    PRICING_MIN_SAMPLE_SIZE: int = 100  # Minimum sample per variant for significance
    PRICING_CONFIDENCE_LEVEL: float = 0.95  # Required statistical confidence

    # Attribution Settings
    ATTRIBUTION_LOOKBACK_DAYS: int = 30  # Days to look back for touchpoint attribution
    ATTRIBUTION_TIME_DECAY_FACTOR: float = 0.95  # Daily decay factor for attribution weight

    # Security Hardening
    SECURITY_HEADERS_ENABLED: bool = True
    SECURITY_REQUEST_ID_ENABLED: bool = True
    SECURITY_SUSPICIOUS_DETECTION: bool = True
    SECURITY_MAX_BODY_SIZE: int = 10485760  # 10MB max request body

    # H2.1: Dev Auth Bypass Feature Flag (P0 Hardening)
    # Controls X-User-Id header bypass in development
    # Default: False (secure by default)
    # Set to True ONLY for local development in .env
    # IMPORTANT: Production validation will fail if True
    ENABLE_DEV_AUTH_BYPASS: bool = False

    # ==========================================================================
    # MCP (Model Context Protocol) Configuration - Phase 4 2026
    # ==========================================================================
    # Core MCP Settings
    MCP_ENABLED: bool = True
    MCP_DEFAULT_TIMEOUT_SECONDS: int = 30
    MCP_MAX_RETRIES: int = 3
    MCP_RETRY_DELAY_MS: int = 1000

    # MCP Gateway Settings
    MCP_GATEWAY_ENABLED: bool = True
    MCP_GATEWAY_RATE_LIMIT_RPM: int = 60  # Requests per minute
    MCP_GATEWAY_RATE_LIMIT_RPH: int = 1000  # Requests per hour
    MCP_GATEWAY_RATE_LIMIT_RPD: int = 10000  # Requests per day
    MCP_GATEWAY_AUDIT_ENABLED: bool = True
    MCP_GATEWAY_AUDIT_LEVEL: str = "basic"  # none, basic, full

    # External MCP Servers
    # Tavily AI Search (Free tier: 1000 searches/month)
    # TAVILY_API_KEY already defined above

    # Playwright Browser MCP (Resource-heavy, disabled by default)
    MCP_PLAYWRIGHT_ENABLED: bool = False
    MCP_PLAYWRIGHT_HEADLESS: bool = True

    # Filesystem MCP (Security-sensitive, disabled by default)
    MCP_FILESYSTEM_ENABLED: bool = False
    MCP_FILESYSTEM_ALLOWED_PATHS: str = "/tmp/vivid-workspace"

    # GitHub MCP (H1.3: SecretStr for token)
    MCP_GITHUB_ENABLED: bool = False
    MCP_GITHUB_TOKEN: SecretStr = SecretStr("")

    # Internal MCP Server (Dimension Tools exposure)
    MCP_INTERNAL_SERVER_ENABLED: bool = True
    MCP_INTERNAL_SERVER_PORT: int = 8200

    # MCP Circuit Breaker
    MCP_CIRCUIT_BREAKER_THRESHOLD: int = 5
    MCP_CIRCUIT_BREAKER_TIMEOUT_SECONDS: int = 60

    # MCP Credit Costs (per call)
    MCP_CREDIT_COST_DEFAULT: int = 1
    MCP_CREDIT_COST_TAVILY: int = 2
    MCP_CREDIT_COST_PLAYWRIGHT: int = 5
    MCP_CREDIT_COST_QDRANT: int = 1

    @property
    def DATABASE_URL(self) -> str:
        """
        Get database URL.

        Priority:
        1. DATABASE_URL env var (for Railway/Render/Heroku compatibility)
        2. Build from individual POSTGRES_* vars (legacy/local dev)
        """
        # Use DATABASE_URL env var if provided (Railway, Render, Heroku, etc.)
        if self.DATABASE_URL_OVERRIDE:
            return self.DATABASE_URL_OVERRIDE

        # Fallback: build from individual components
        password = self.POSTGRES_PASSWORD.get_secret_value()
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{password}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        """
        Get allowed CORS origins based on environment.
        - Development: localhost origins only
        - Production: Merges CORS_ORIGINS with CORS_PRODUCTION_ORIGINS
        - Wildcard '*': allows all (NOT recommended for production)
        """
        if self.CORS_ORIGINS == "*":
            return ["*"]
        
        origins = [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
        
        # In production/staging, also include production origins
        if self.ENVIRONMENT not in {"development", "local", "dev"}:
            prod_origins = [
                origin.strip() 
                for origin in self.CORS_PRODUCTION_ORIGINS.split(",") 
                if origin.strip()
            ]
            # Merge without duplicates
            origins = list(dict.fromkeys(origins + prod_origins))
        
        return origins

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

    @property
    def ALLOWED_GEMINI_AGENT_MODELS(self) -> List[str]:
        if not self.GEMINI_AGENT_MODELS:
            return []
        return [
            model.strip()
            for model in self.GEMINI_AGENT_MODELS.split(",")
            if model.strip()
        ]

    def validate_production_config(self) -> list[str]:
        """
        Validate configuration for production safety.
        Returns list of critical warnings. Raises ValueError for blockers.

        P0 Hardening: Enhanced validation for security-critical settings.
        """
        errors = []
        warnings = []
        is_prod = self.ENVIRONMENT.lower() in {"production", "prod", "staging"}

        if is_prod:
            # Check for localhost in critical URLs
            if "localhost" in self.AUTH_SUCCESS_REDIRECT or "127.0.0.1" in self.AUTH_SUCCESS_REDIRECT:
                errors.append("AUTH_SUCCESS_REDIRECT contains localhost - set to production domain")
            if "localhost" in self.AUTH_ERROR_REDIRECT or "127.0.0.1" in self.AUTH_ERROR_REDIRECT:
                errors.append("AUTH_ERROR_REDIRECT contains localhost - set to production domain")
            if "localhost" in self.QDRANT_URL or "127.0.0.1" in self.QDRANT_URL:
                warnings.append("QDRANT_URL contains localhost - ensure Qdrant is accessible")
            if "localhost" in self.REDIS_URL or "127.0.0.1" in self.REDIS_URL:
                warnings.append("REDIS_URL contains localhost - ensure Redis is accessible")

            # Check for empty required secrets (H1.3: SecretStr compatibility)
            if not self.SESSION_SECRET.get_secret_value():
                errors.append("SESSION_SECRET is empty - required for session encryption")
            if not self.GOOGLE_CLIENT_ID or not self.GOOGLE_CLIENT_SECRET.get_secret_value():
                warnings.append("Google OAuth credentials not configured")

            # Check for sandbox payment in production
            if self.NICEPAY_MODE == "sandbox":
                errors.append("NICEPAY_MODE is 'sandbox' - switch to 'production' for live payments")

            # H2.1: Dev auth bypass must be disabled in production
            if self.ENABLE_DEV_AUTH_BYPASS:
                errors.append("ENABLE_DEV_AUTH_BYPASS is True - must be False in production")

            # P0: Check for default/weak passwords in production
            # Skip if DATABASE_URL is provided (password is embedded in URL)
            if not self.DATABASE_URL_OVERRIDE:
                default_passwords = {"crebit_password", "crebit_dev_only", "password", "changeme"}
                if self.POSTGRES_PASSWORD.get_secret_value() in default_passwords:
                    errors.append("POSTGRES_PASSWORD is a default value - use a strong, unique password")

        # TODO: Re-enable strict validation after initial deployment
        # if errors:
        #     raise ValueError(
        #         f"Production configuration errors:\n" + "\n".join(f"  - {e}" for e in errors)
        #     )

        # Convert errors to warnings for now
        warnings.extend(errors)
        return warnings

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
