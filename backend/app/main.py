"""FastAPI entrypoint for 3-Layer Ecosystem."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from arq import create_pool
from arq.connections import RedisSettings

from app.config import settings
from app.database import init_db

# Core Routers (3-Layer Ecosystem)
from app.routers.auth import router as auth_router
from app.routers.credits import router as credits_router
from app.routers.teaching import router as teaching_router
from app.routers.agent import router as agent_router
from app.routers.mcp import router as mcp_router
from app.routers.health import router as health_router
from app.routers.user_settings import router as user_settings_router
from app.routers.dashboard import router as dashboard_router
from app.routers.feedback import router as feedback_router

# Crebit (강의 판매 + 결제)
from app.routers.crebit import router as crebit_router
from app.routers.payment import router as payment_router

# Telemetry (4-Layer Ecosystem)
from app.routers.telemetry import router as telemetry_router

from app.middleware.rate_limit import setup_rate_limiting
from app.logging_config import setup_logging, LoggingMiddleware
from app.monitoring import setup_monitoring


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database
    await init_db(drop_all=False)
    
    # Initialize Arq Redis Pool
    app.state.arq_pool = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
    yield
    # Close Arq Redis Pool
    await app.state.arq_pool.close()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="2.0.0",  # 3-Layer Ecosystem
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
    max_age=settings.CORS_MAX_AGE,
)

# Add logging middleware
app.add_middleware(LoggingMiddleware)

# Setup rate limiting
setup_rate_limiting(app)

# Initialize structured logging
setup_logging(settings.LOG_LEVEL if hasattr(settings, 'LOG_LEVEL') else "INFO")

# Setup Sentry and Prometheus monitoring
setup_monitoring(app)

# =============================================================================
# 3-Layer Ecosystem Routers
# =============================================================================

# Layer 1: Teaching Tools (핵심)
app.include_router(teaching_router, prefix="/api/teaching", tags=["teaching"])

# Layer 2: Agent Chat
app.include_router(agent_router, prefix="/api/v1", tags=["agent"])

# Layer 3: MCP (Model Context Protocol)
app.include_router(mcp_router, prefix="/api/v1", tags=["mcp"])

# Auth & Credits
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(credits_router, prefix="/api/v1/credits", tags=["credits"])
app.include_router(user_settings_router, prefix="")

# Dashboard & Feedback
app.include_router(dashboard_router, prefix="/api/v1", tags=["dashboard"])
app.include_router(feedback_router, prefix="/api/v1", tags=["feedback"])

# Crebit (강의 판매 + 결제)
app.include_router(crebit_router, prefix="/api/v1/crebit", tags=["crebit"])
app.include_router(payment_router, prefix="/api/v1/payment", tags=["payment"])

# Telemetry (4-Layer Ecosystem: Tool tracking, Forks, Attribution)
app.include_router(telemetry_router, prefix="/api/v1/telemetry", tags=["telemetry"])

# Infrastructure
app.include_router(health_router, prefix="", tags=["health"])


@app.get("/")
async def root():
    return {
        "message": f"{settings.PROJECT_NAME} API",
        "version": "2.0.0",
        "architecture": "3-Layer Ecosystem",
        "layers": {
            "1": "Teaching Tools (도구 Fork)",
            "2": "Human Cloud (콘텐츠)",
            "3": "RAG Knowledge (지식)"
        }
    }
