"""FastAPI entrypoint for the canvas MVP."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.routers.canvases import router as canvases_router
from app.routers.capsules import router as capsules_router
from app.routers.credits import router as credits_router
from app.routers.affiliate import router as affiliate_router
from app.routers.ingest import router as ingest_router
from app.routers.ops import router as ops_router
from app.routers.realtime import router as realtime_router
from app.routers.runs import router as runs_router
from app.routers.templates import router as templates_router
from app.routers.spec import router as spec_router
from app.seed import seed_auteur_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Drop and recreate tables if seeding (development only)
    await init_db(drop_all=settings.SEED_AUTEUR_DATA)
    if settings.SEED_AUTEUR_DATA:
        await seed_auteur_data()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(canvases_router, prefix="/api/v1/canvases", tags=["canvases"])
app.include_router(templates_router, prefix="/api/v1/templates", tags=["templates"])
app.include_router(capsules_router, prefix="/api/v1/capsules", tags=["capsules"])
app.include_router(credits_router, prefix="/api/v1/credits", tags=["credits"])
app.include_router(affiliate_router, prefix="/api/v1/affiliate", tags=["affiliate"])
app.include_router(ingest_router, prefix="/api/v1/ingest", tags=["ingest"])
app.include_router(runs_router, prefix="/api/v1/runs", tags=["runs"])
app.include_router(spec_router, prefix="/api/v1/spec", tags=["spec"])
app.include_router(ops_router, prefix="/api/v1/ops", tags=["ops"])
app.include_router(realtime_router, prefix="/ws", tags=["realtime"])


@app.get("/health")
async def health_check():
    return {"status": "ok", "environment": settings.ENVIRONMENT}


@app.get("/")
async def root():
    return {"message": f"{settings.PROJECT_NAME} API"}
