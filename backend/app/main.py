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
from app.routers.dimension import router as dimension_router
from app.routers.agent import router as agent_router
from app.routers.mcp import router as mcp_router
from app.routers.mcp_v2 import router as mcp_v2_router
from app.routers.health import router as health_router
from app.routers.user_settings import router as user_settings_router
from app.routers.dashboard import router as dashboard_router
from app.routers.feedback import router as feedback_router

# Crebit (강의 판매 + 결제)
from app.routers.crebit import router as crebit_router
from app.routers.payment import router as payment_router

# Telemetry (4-Layer Ecosystem)
from app.routers.telemetry import router as telemetry_router

# RAG Feedback (P6: Feedback Collection)
from app.routers.rag_feedback import router as rag_feedback_router

# UQSL (Universal Quality Selection Layer)
from app.routers.uqsl import router as uqsl_router

# Feature Flags (Self-hosted, Redis-backed)
from app.features.router import router as feature_flags_router

# A/B Testing (Experimentation Infrastructure)
from app.experiments.router import router as experiments_router

# Settlements (Revenue Distribution)
from app.routers.settlements import router as settlements_router

# Fork (Version Control & Fork Creation)
from app.routers.fork import router as fork_router

# Reviews (Approval Workflow)
from app.routers.reviews import router as reviews_router

# Sandbox (Isolated Execution)
from app.routers.sandbox import router as sandbox_router

# Human Cloud (Creative Marketplace)
from app.routers.humancloud import router as humancloud_router

# RAG (Vector Search)
from app.routers.rag import router as rag_router

# RAG Pipeline (3-Tier RAG Administration)
from app.routers.rag_admin import router as rag_pipeline_router

# Workflow (Tool Chain Orchestration)
from app.routers.workflow import router as workflow_router

# Singularity (Template Gallery - 차원의 특이점)
from app.routers.singularity import router as singularity_router

# Constellation (Multi-scene Projects - 별자리)
from app.routers.constellation import router as constellation_router

# Tool Registry (MCP-compatible tool discovery)
from app.routers.tools import router as tools_router

# Batch (Async Processing with 50% cost reduction)
from app.routers.batch import router as batch_router

# Content Metrics (Viral/Engagement Tracking)
from app.routers.content_metrics import router as content_metrics_router

# Affiliate (Referral System)
from app.routers.affiliate import router as affiliate_router

# Monitor (API Cost and Performance Tracking)
from app.routers.monitor import router as monitor_router

# Admin (Internal Staff App Management)
from app.routers.admin import router as admin_router

# Ops Audit (Admin Ops Logs)
from app.routers.ops_audit import router as ops_audit_router

# Run Token (App Execution Tokens)
from app.routers.run_token import router as run_token_router

# Internal S2S (mTLS Protected)
from app.routers.internal import router as internal_router

# MiniApps (Dimension Portal Submissions)
from app.routers.miniapps import router as miniapps_router

# Context Library (Expert Workflow - Context Injection)
from app.routers.context import router as context_router

# Intent Presets (Creative Intent API)
from app.routers.intent import router as intent_router

# Capsules (Direct Capsule Execution - P5)
from app.routers.capsules import router as capsules_router

# IP (Intellectual Property) - IP-First UX
from app.routers.ip import router as ip_router
from app.routers.ip_generation import router as ip_generation_router
from app.routers.dmca import router as dmca_router
from app.routers.ip_payout import router as ip_payout_router

# Tool Recommendation (IP-First Coordination Phase 2.5)
from app.routers.tool_recommendation import router as tool_recommendation_router

# Phase 7: HITL Enhancement
from app.routers.approval_gate import router as approval_gate_router
from app.routers.creator_dashboard import router as creator_dashboard_router

# Phase 9: Monetization & Analytics
from app.routers.analytics_dashboard import router as analytics_dashboard_router

# GraphQL Gateway (2026 Best Practices - P3.3)
from app.graphql import graphql_router

from app.middleware.rate_limit import setup_rate_limiting
from app.middleware.mtls import MTLSMiddleware
from app.middleware.security import setup_security_middleware
from app.logging_config import setup_logging, LoggingMiddleware
from app.monitoring import setup_monitoring


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Validate production configuration (fail fast)
    if settings.ENVIRONMENT.lower() in {"production", "prod", "staging"}:
        warnings = settings.validate_production_config()
        if warnings:
            import logging
            logger = logging.getLogger("startup")
            for warning in warnings:
                logger.warning(f"[PROD CONFIG] {warning}")

    # Initialize database
    await init_db(drop_all=False)
    
    # Initialize Redis client
    from app.redis_client import init_redis, close_redis
    await init_redis()
    
    # Initialize Arq Redis Pool
    app.state.arq_pool = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
    
    yield
    
    # Close Arq Redis Pool
    await app.state.arq_pool.close()
    
    # Close Redis client
    await close_redis()


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

# Add secure logging middleware (PII Redaction)
# LoggingMiddleware는 제거하고 SecureLoggingMiddleware 사용
from app.middleware.secure_logging import SecureLoggingMiddleware
app.add_middleware(SecureLoggingMiddleware)

# Add mTLS middleware (for internal S2S routes)
app.add_middleware(MTLSMiddleware)

# Setup security middleware (2026 Best Practices)
# Order: Security Headers → Request ID → Timing → Suspicious Detection
if settings.SECURITY_HEADERS_ENABLED:
    setup_security_middleware(
        app,
        enable_security_headers=settings.SECURITY_HEADERS_ENABLED,
        enable_request_id=settings.SECURITY_REQUEST_ID_ENABLED,
        enable_timing=True,
        enable_suspicious_detection=settings.SECURITY_SUSPICIOUS_DETECTION,
    )

# Setup rate limiting
setup_rate_limiting(app)

# Initialize structured logging
setup_logging(settings.LOG_LEVEL if hasattr(settings, 'LOG_LEVEL') else "INFO")

# Setup Sentry, Prometheus, and OpenTelemetry monitoring
setup_monitoring(app)

# =============================================================================
# 3-Layer Ecosystem Routers
# =============================================================================

# Layer 1: Dimension Apps (차원 앱 - 신규 API)
app.include_router(dimension_router, prefix="/api/dimension", tags=["dimension"])

# Layer 1: Teaching Tools (레거시 호환용 - deprecated)
# [DEPRECATED] teaching API - use /api/dimension/* instead

# Layer 2: Agent Chat
app.include_router(agent_router, prefix="/api/v1", tags=["agent"])

# Layer 3: MCP (Model Context Protocol)
app.include_router(mcp_router, prefix="/api/v1", tags=["mcp"])
app.include_router(mcp_v2_router, prefix="/api/v1", tags=["mcp-v2"])

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

# RAG Feedback (P6: Feedback Collection for P7/P8)
app.include_router(rag_feedback_router, prefix="/api/v1", tags=["rag-feedback"])

# Settlements (Revenue Distribution)
app.include_router(settlements_router, prefix="/api/v1", tags=["settlements"])

# Fork (Version Control & Fork Creation)
app.include_router(fork_router, prefix="/api/v1", tags=["fork"])

# Reviews (Approval Workflow)
app.include_router(reviews_router, prefix="/api/v1", tags=["reviews"])

# Sandbox (Isolated Execution)
app.include_router(sandbox_router, prefix="/api/v1", tags=["sandbox"])

# Human Cloud (Creative Marketplace)
app.include_router(humancloud_router, prefix="/api/v1", tags=["humancloud"])

# RAG (Vector Search & Recommendations)
app.include_router(rag_router, prefix="/api/v1", tags=["rag"])

# RAG Pipeline (3-Tier Administration)
app.include_router(rag_pipeline_router, prefix="/api/v1", tags=["rag-pipeline"])

# UQSL (Universal Quality Selection Layer) - prefix already in router
app.include_router(uqsl_router, tags=["uqsl"])

# Feature Flags (Self-hosted Feature Management) - prefix already in router
app.include_router(feature_flags_router, tags=["feature-flags"])

# A/B Testing (Experimentation Infrastructure) - prefix already in router
app.include_router(experiments_router, tags=["ab-testing"])

# Workflow (Tool Chain Orchestration)
app.include_router(workflow_router, prefix="/api/v1", tags=["workflow"])

# Singularity (Template Gallery - 차원의 특이점)
app.include_router(singularity_router, prefix="/api/v1", tags=["singularity"])

# Constellation (Multi-scene Projects - 별자리)
app.include_router(constellation_router, prefix="/api/v1", tags=["constellation"])

# Intent Presets (Creative Intent API)
app.include_router(intent_router, prefix="/api/v1", tags=["intent"])

# IP (Intellectual Property) - IP-First UX
app.include_router(ip_router, prefix="/api/v1/ip", tags=["ip"])
app.include_router(ip_generation_router, prefix="/api/v1/ip", tags=["ip-generation"])
app.include_router(dmca_router, prefix="/api/v1/dmca", tags=["dmca"])
app.include_router(ip_payout_router, prefix="/api/v1/ip", tags=["ip-payout"])

# Tool Recommendation (IP-First Coordination Phase 2.5)
app.include_router(tool_recommendation_router, prefix="/api/v1", tags=["tool-recommendation"])

# Capsules (Direct Capsule Execution - P5)
app.include_router(capsules_router, tags=["capsules"])

# Content Metrics (Viral/Engagement Tracking)
app.include_router(content_metrics_router, prefix="/api/v1", tags=["content-metrics"])

# Affiliate (Referral System)
app.include_router(affiliate_router, prefix="/api/v1", tags=["affiliate"])

# Tool Registry (MCP-compatible tool discovery)
app.include_router(tools_router, tags=["tools"])

# Batch (Async Processing with 50% cost reduction)
app.include_router(batch_router, tags=["batch"])

# Monitor (API Cost and Performance Tracking)
app.include_router(monitor_router, tags=["monitor"])

# Admin (Internal Staff App Management)
app.include_router(admin_router, prefix="/api/v1", tags=["admin"])

# Ops Audit (Admin Logs)
app.include_router(ops_audit_router, prefix="/api/v1", tags=["ops"])

# Run Token (App Execution Tokens)
app.include_router(run_token_router, prefix="/api/v1", tags=["run-token"])

# Internal S2S (mTLS Protected)
app.include_router(internal_router, prefix="/api/v1", tags=["internal"])

# MiniApps (Dimension Portal Submissions)
app.include_router(miniapps_router, prefix="/api/v1", tags=["miniapps"])

# Context Library (Expert Workflow - Context Injection)
app.include_router(context_router, prefix="/api/v1", tags=["context"])

# Phase 7: HITL Enhancement (Approval Gate, Creator Dashboard)
app.include_router(approval_gate_router, prefix="/api/v1", tags=["approval-gate"])
app.include_router(creator_dashboard_router, prefix="/api/v1", tags=["creator-dashboard"])

# Phase 9: Monetization & Analytics
app.include_router(analytics_dashboard_router, tags=["analytics"])

# GraphQL Gateway (2026 Best Practices - P3.3)
if settings.ENVIRONMENT.lower() in {"production", "prod", "staging"}:
    if settings.GRAPHQL_ENABLED:
        app.include_router(graphql_router, prefix="/graphql", tags=["graphql"])
else:
    app.include_router(graphql_router, prefix="/graphql", tags=["graphql"])

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
