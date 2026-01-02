"""
MCP API Router (Hardened)

MCP 서버 통합 API 엔드포인트.
Streamable HTTP 프로토콜 지원.

Hardening:
- 상세 로깅
- 에러 핸들링 강화
- DB 연동 엔드포인트
- 입력 검증
"""
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field, validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.mcp_servers.pattern_truth_mcp import pattern_truth_mcp
from app.database import get_db
from app.models_telemetry import ToolManifest, ToolTier

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mcp", tags=["MCP"])


# =========================================================================
# Request/Response Models (Hardened)
# =========================================================================

class ToolCallRequest(BaseModel):
    """MCP Tool 호출 요청"""
    tool_name: str = Field(..., min_length=1, max_length=100)
    arguments: Dict[str, Any] = Field(default_factory=dict)
    
    @validator("tool_name")
    def validate_tool_name(cls, v):
        allowed = ["compute_stpf", "analyze_sensitivity", "update_confidence", "calculate_kelly"]
        if v not in allowed:
            raise ValueError(f"Unknown tool: {v}. Allowed: {allowed}")
        return v


class ToolCallResponse(BaseModel):
    """MCP Tool 호출 응답"""
    tool_name: str
    result: Any
    success: bool
    error: Optional[str] = None
    execution_time_ms: Optional[float] = None


class STFPRequest(BaseModel):
    """STPF 계산 요청 (검증 강화)"""
    trust: float = Field(5.0, ge=1.0, le=10.0)
    legality: float = Field(8.0, ge=1.0, le=10.0)
    hygiene: float = Field(6.0, ge=1.0, le=10.0)
    essence: float = Field(5.0, ge=1.0, le=10.0)
    capability: float = Field(5.0, ge=1.0, le=10.0)
    novelty: float = Field(5.0, ge=1.0, le=10.0)
    connection: float = Field(5.0, ge=1.0, le=10.0)
    proof: float = Field(5.0, ge=1.0, le=10.0)
    cost: float = Field(5.0, ge=1.0, le=10.0)
    risk: float = Field(5.0, ge=1.0, le=10.0)
    threat: float = Field(5.0, ge=1.0, le=10.0)
    pressure: float = Field(5.0, ge=1.0, le=10.0)
    lag: float = Field(5.0, ge=1.0, le=10.0)
    uncertainty: float = Field(5.0, ge=1.0, le=10.0)


class BayesianRequest(BaseModel):
    """베이지안 갱신 요청 (검증 강화)"""
    rule_id: str = Field(..., min_length=1, max_length=255)
    supports_rule: bool = True
    strength: float = Field(0.8, ge=0.0, le=1.0)
    prior_confidence: float = Field(0.5, ge=0.0, le=1.0)
    prior_strength: float = Field(1.0, ge=0.1, le=5.0)


class KellyRequest(BaseModel):
    """Kelly 배분 요청 (검증 강화)"""
    balance: int = Field(1000, ge=0)
    cost_per_run: int = Field(10, ge=1)
    success_probability: float = Field(0.6, ge=0.01, le=0.99)
    reward_ratio: float = Field(2.0, ge=0.1, le=100.0)


# =========================================================================
# Server Info
# =========================================================================

@router.get("/servers")
async def list_servers():
    """사용 가능한 MCP 서버 목록"""
    logger.info("MCP: listing servers")
    return {
        "servers": [
            pattern_truth_mcp.get_server_info(),
        ]
    }


@router.get("/servers/pattern-truth")
async def get_pattern_truth_info():
    """Pattern Truth MCP 서버 정보"""
    return pattern_truth_mcp.get_server_info()


# =========================================================================
# Tools (Hardened)
# =========================================================================

@router.get("/servers/pattern-truth/tools")
async def list_pattern_truth_tools():
    """Pattern Truth MCP 도구 목록"""
    tools = pattern_truth_mcp.list_tools()
    return {
        "tools": [t.model_dump() for t in tools]
    }


@router.post("/servers/pattern-truth/tools/call", response_model=ToolCallResponse)
async def call_pattern_truth_tool(request: ToolCallRequest):
    """Pattern Truth MCP 도구 호출 (Hardened)"""
    import time
    start = time.time()
    
    logger.info(f"MCP Tool call: {request.tool_name} with {len(request.arguments)} args")
    
    try:
        result = await pattern_truth_mcp.call_tool(request.tool_name, request.arguments)
        elapsed_ms = (time.time() - start) * 1000
        
        logger.info(f"MCP Tool success: {request.tool_name} in {elapsed_ms:.1f}ms")
        
        return ToolCallResponse(
            tool_name=request.tool_name,
            result=result,
            success=True,
            execution_time_ms=round(elapsed_ms, 2),
        )
    except ValueError as e:
        logger.warning(f"MCP Tool not found: {request.tool_name}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        elapsed_ms = (time.time() - start) * 1000
        logger.error(f"MCP Tool error: {request.tool_name} - {e}")
        
        return ToolCallResponse(
            tool_name=request.tool_name,
            result=None,
            success=False,
            error=str(e),
            execution_time_ms=round(elapsed_ms, 2),
        )


# =========================================================================
# Resources
# =========================================================================

@router.get("/servers/pattern-truth/resources")
async def list_pattern_truth_resources():
    """Pattern Truth MCP 리소스 목록"""
    resources = pattern_truth_mcp.list_resources()
    return {
        "resources": [r.model_dump() for r in resources]
    }


@router.get("/servers/pattern-truth/resources/{resource_path:path}")
async def read_pattern_truth_resource(resource_path: str):
    """Pattern Truth MCP 리소스 읽기"""
    uri = f"pattern://{resource_path}"
    logger.info(f"MCP Resource read: {uri}")
    
    try:
        result = await pattern_truth_mcp.read_resource(uri)
        return result
    except ValueError as e:
        logger.warning(f"MCP Resource not found: {uri}")
        raise HTTPException(status_code=404, detail=str(e))


# =========================================================================
# Direct Endpoints (Hardened with Validation)
# =========================================================================

@router.post("/compute-stpf")
async def compute_stpf_direct(request: STFPRequest):
    """STPF 점수 직접 계산 (입력 검증 강화)"""
    logger.info(f"STPF compute: trust={request.trust}, essence={request.essence}")
    
    return await pattern_truth_mcp.compute_stpf(**request.model_dump())


@router.post("/update-confidence")
async def update_confidence_direct(request: BayesianRequest):
    """베이지안 갱신 직접 호출 (입력 검증 강화)"""
    logger.info(f"Bayesian update: rule={request.rule_id}, supports={request.supports_rule}")
    
    return await pattern_truth_mcp.update_confidence(**request.model_dump())


@router.post("/calculate-kelly")
async def calculate_kelly_direct(request: KellyRequest):
    """Kelly 배분 직접 호출 (입력 검증 강화)"""
    logger.info(f"Kelly calculate: balance={request.balance}, prob={request.success_probability}")
    
    return await pattern_truth_mcp.calculate_kelly(**request.model_dump())


# =========================================================================
# Health
# =========================================================================

@router.get("/health")
async def mcp_health():
    """MCP 서버 상태 (상세)"""
    health = await pattern_truth_mcp.read_resource("pattern://health")
    config = await pattern_truth_mcp.read_resource("pattern://config")
    
    return {
        "status": health["status"],
        "server": health["server"],
        "version": health["version"],
        "tools_count": len(health.get("tools", [])),
        "config": config,
    }


@router.get("/stats")
async def mcp_stats():
    """MCP 서버 통계"""
    tools = pattern_truth_mcp.list_tools()
    resources = pattern_truth_mcp.list_resources()
    
    return {
        "server": pattern_truth_mcp.name,
        "version": pattern_truth_mcp.version,
        "tools": {
            "count": len(tools),
            "names": [t.name for t in tools],
        },
        "resources": {
            "count": len(resources),
            "uris": [r.uri for r in resources],
        },
    }


# =========================================================================
# Tool Manifests (DB-based)
# =========================================================================

@router.get("/tools")
async def list_db_tools(
    category: Optional[str] = None,
    tier: Optional[str] = None,
    is_active: bool = True,
    limit: int = Query(default=50, le=200),
    db: AsyncSession = Depends(get_db),
):
    """List all tool manifests from DB.
    
    This replaces the static capsule_registry.py with dynamic DB lookup.
    """
    query = select(ToolManifest).where(ToolManifest.is_active == is_active)
    
    if category:
        query = query.where(ToolManifest.category == category.lower())
    if tier:
        query = query.where(ToolManifest.tier == tier.lower())
    
    query = query.order_by(ToolManifest.usage_count.desc()).limit(limit)
    
    result = await db.execute(query)
    tools = result.scalars().all()
    
    return {
        "tools": [
            {
                "id": str(tool.id),
                "tool_key": tool.tool_key,
                "display_name": tool.display_name,
                "description": tool.description,
                "category": tool.category,
                "tier": tool.tier,
                "credit_cost": tool.credit_cost,
                "input_schema": tool.input_schema,
                "output_schema": tool.output_schema,
                "usage_count": tool.usage_count,
                "quality_rating": tool.quality_rating,
            }
            for tool in tools
        ],
        "total": len(tools),
    }


@router.get("/tools/{tool_key}")
async def get_db_tool(
    tool_key: str,
    include_code: bool = Query(default=False, description="Include live version code"),
    db: AsyncSession = Depends(get_db),
):
    """Get a single tool manifest by key.
    
    If include_code=true, also returns the live version's code content.
    """
    from app.models_versioning import ToolVersion
    
    result = await db.execute(
        select(ToolManifest).where(ToolManifest.tool_key == tool_key)
    )
    tool = result.scalars().first()
    
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_key}' not found")
    
    response = {
        "id": str(tool.id),
        "tool_key": tool.tool_key,
        "display_name": tool.display_name,
        "description": tool.description,
        "category": tool.category,
        "tier": tool.tier,
        "credit_cost": tool.credit_cost,
        "input_schema": tool.input_schema,
        "output_schema": tool.output_schema,
        "usage_count": tool.usage_count,
        "fork_count": tool.fork_count,
        "quality_rating": tool.quality_rating,
        "safety_rating": tool.safety_rating,
        "sandbox_required": tool.sandbox_required,
        "created_by": tool.created_by,
        "created_at": tool.created_at.isoformat() if tool.created_at else None,
        "parent_tool_id": str(tool.parent_tool_id) if tool.parent_tool_id else None,
    }
    
    # Include live version if requested
    if include_code:
        version_result = await db.execute(
            select(ToolVersion)
            .where(ToolVersion.tool_id == tool.id)
            .where(ToolVersion.is_live == True)
        )
        live_version = version_result.scalars().first()
        
        if live_version:
            response["live_version"] = {
                "id": str(live_version.id),
                "version": live_version.version,
                "code_type": live_version.code_type,
                "code_content": live_version.code_content,
                "system_prompt": live_version.system_prompt,
                "status": live_version.status,
            }
        else:
            response["live_version"] = None
    
    return response


@router.get("/tools/category/{category}")
async def list_tools_by_category(
    category: str,
    db: AsyncSession = Depends(get_db),
):
    """List tools by category (for frontend palette)."""
    result = await db.execute(
        select(ToolManifest)
        .where(ToolManifest.category == category.lower())
        .where(ToolManifest.is_active == True)
        .order_by(ToolManifest.display_name)
    )
    tools = result.scalars().all()
    
    return {
        "category": category,
        "tools": [
            {
                "tool_key": tool.tool_key,
                "display_name": tool.display_name,
                "description": tool.description,
                "tier": tool.tier,
                "credit_cost": tool.credit_cost,
                "input_schema": tool.input_schema,
                "output_schema": tool.output_schema,
            }
            for tool in tools
        ],
        "count": len(tools),
    }

