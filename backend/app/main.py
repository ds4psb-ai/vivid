"""FastAPI entrypoint for the canvas MVP."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from arq import create_pool
from arq.connections import RedisSettings

from app.config import settings
from app.database import init_db
from app.routers.canvases import router as canvases_router
from app.routers.capsules import router as capsules_router
from app.routers.credits import router as credits_router
from app.routers.auth import router as auth_router
from app.routers.runs import router as runs_router
from app.routers.director_packs import router as director_packs_router
from app.routers.health import router as health_router
from app.routers.director import router as director_router
from app.routers.agent import router as agent_router
from app.routers.nodes import router as nodes_router
from app.routers.user_settings import router as user_settings_router
from app.routers.teaching import router as teaching_router
from app.routers.stpf import router as stpf_router
from app.routers.bayesian import router as bayesian_router
from app.routers.kelly import router as kelly_router
from app.routers.mcp import router as mcp_router
from app.routers.tot import router as tot_router
from app.routers.feedback import router as feedback_router
from app.routers.dashboard import router as dashboard_router
from app.routers.intent import router as intent_router
from app.seed import seed_auteur_data
from app.middleware.rate_limit import setup_rate_limiting
from app.logging_config import setup_logging, LoggingMiddleware
from app.monitoring import setup_monitoring


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Drop and recreate tables if seeding (development only)
    await init_db(drop_all=settings.SEED_AUTEUR_DATA)
    if settings.SEED_AUTEUR_DATA:
        await seed_auteur_data()
    
    # Initialize Arq Redis Pool
    app.state.arq_pool = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
    yield
    # Close Arq Redis Pool
    await app.state.arq_pool.close()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
    max_age=settings.CORS_MAX_AGE,  # Cache preflight requests
)

# Add logging middleware for structured request/response logging
app.add_middleware(LoggingMiddleware)

# Setup rate limiting (100/min default, see rate_limit.py for details)
setup_rate_limiting(app)

# Initialize structured logging
setup_logging(settings.LOG_LEVEL if hasattr(settings, 'LOG_LEVEL') else "INFO")

# Setup Sentry and Prometheus monitoring
setup_monitoring(app)

# =============================================================================
# CORE Routers - Agent + Canvas + Teaching Architecture
# =============================================================================

# Canvas & Node Management
app.include_router(canvases_router, prefix="/api/v1/canvases", tags=["canvases"])
app.include_router(nodes_router, prefix="/api/v1", tags=["nodes"])

# Agent Chat System
app.include_router(agent_router, prefix="/api/v1", tags=["agent"])

# Teaching Tools
app.include_router(teaching_router, prefix="/api/teaching", tags=["teaching"])

# Capsule Execution
app.include_router(capsules_router, prefix="/api/v1/capsules", tags=["capsules"])
app.include_router(runs_router, prefix="/api/v1/runs", tags=["runs"])

# Director (Coaching)
app.include_router(director_router, prefix="/api/v1", tags=["director"])
app.include_router(director_packs_router, prefix="/api/v1", tags=["director-packs"])

# Auth & User
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(credits_router, prefix="/api/v1/credits", tags=["credits"])
app.include_router(user_settings_router, prefix="")

# STPF (Computational Truth Engine)
app.include_router(stpf_router, prefix="/api/v1", tags=["stpf"])

# Bayesian (Confidence Updates)
app.include_router(bayesian_router, prefix="/api/v1", tags=["bayesian"])

# Kelly (Credit Allocation)
app.include_router(kelly_router, prefix="/api/v1", tags=["kelly"])

# MCP (Model Context Protocol)
app.include_router(mcp_router, prefix="/api/v1", tags=["mcp"])

# ToT (Tree of Thoughts)
app.include_router(tot_router, prefix="/api/v1", tags=["tot"])

# Feedback Loop
app.include_router(feedback_router, prefix="/api/v1", tags=["feedback"])

# Dashboard (Frontend API)
app.include_router(dashboard_router, prefix="/api/v1", tags=["dashboard"])

# Intent Parser (Node Chat Integration)
app.include_router(intent_router, prefix="/api/v1", tags=["intent"])

# Infrastructure
app.include_router(health_router, prefix="", tags=["health"])


@app.get("/")
async def root():
    return {"message": f"{settings.PROJECT_NAME} API"}
