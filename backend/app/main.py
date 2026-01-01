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
from app.routers.affiliate import router as affiliate_router
from app.routers.auth import router as auth_router
from app.routers.ingest import router as ingest_router
from app.routers.ops import router as ops_router
from app.routers.realtime import router as realtime_router
from app.routers.runs import router as runs_router
from app.routers.templates import router as templates_router
from app.routers.spec import router as spec_router
from app.routers.analytics import router as analytics_router
from app.routers.crebit import router as crebit_router
from app.routers.payment import router as payment_router
from app.routers.events import router as events_router
from app.routers.jobs import router as jobs_router
from app.routers.director_packs import router as director_packs_router
from app.routers.content_metrics import router as content_metrics_router
from app.routers.health import router as health_router
from app.routers.data_deletion import router as data_deletion_router
from app.routers.director import router as director_router
from app.routers.agent import router as agent_router
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

app.include_router(canvases_router, prefix="/api/v1/canvases", tags=["canvases"])
app.include_router(templates_router, prefix="/api/v1/templates", tags=["templates"])
app.include_router(capsules_router, prefix="/api/v1/capsules", tags=["capsules"])
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(credits_router, prefix="/api/v1/credits", tags=["credits"])
app.include_router(affiliate_router, prefix="/api/v1/affiliate", tags=["affiliate"])
app.include_router(ingest_router, prefix="/api/v1/ingest", tags=["ingest"])
app.include_router(runs_router, prefix="/api/v1/runs", tags=["runs"])
app.include_router(spec_router, prefix="/api/v1/spec", tags=["spec"])
app.include_router(ops_router, prefix="/api/v1/ops", tags=["ops"])
app.include_router(analytics_router, prefix="/api/v1/analytics", tags=["analytics"])
app.include_router(crebit_router, prefix="/api/v1", tags=["crebit"])
app.include_router(payment_router, prefix="/api/v1", tags=["payment"])
app.include_router(events_router, prefix="/api/v1", tags=["events"])
app.include_router(jobs_router, prefix="/api/v1", tags=["jobs"])
app.include_router(director_packs_router, prefix="/api/v1", tags=["director-packs"])
app.include_router(content_metrics_router, prefix="/api/v1", tags=["content-metrics"])
app.include_router(director_router, prefix="/api/v1", tags=["director"])  # AI Director vibe coding
app.include_router(agent_router, prefix="/api/v1", tags=["agent"])  # Agent chat endpoints
app.include_router(data_deletion_router, prefix="/api/v1", tags=["compliance"])  # GDPR data deletion
app.include_router(health_router, prefix="", tags=["health"])  # Health endpoints at root
app.include_router(realtime_router, prefix="/ws", tags=["realtime"])


@app.get("/")
async def root():
    return {"message": f"{settings.PROJECT_NAME} API"}
