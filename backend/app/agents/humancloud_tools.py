"""HumanCloud Tools for VividAgent.

초끼가 휴먼클라우드 마켓플레이스에서 요청/크리에이터 검색을 도와주는 도구들.
"""
from __future__ import annotations

from typing import Dict, Any, List

from sqlalchemy import select

from app.agents.agent_types import (
    ToolCall,
    ToolContext,
    ToolRegistry,
    ToolResult,
    ToolSpec,
)
from app.agents.tool_utils import success_result, error_result
from app.database import AsyncSessionLocal
from app.models_humancloud import CreativeRequest, CreatorProfile
from app.logging_config import get_logger

logger = get_logger("humancloud_tools")

# =============================================================================
# Tool Specs
# =============================================================================

SEARCH_REQUESTS_SPEC = ToolSpec(
    name="search_requests",
    description="휴먼클라우드에서 열린 요청(크리에이티브 의뢰)을 검색합니다. 카테고리나 예산으로 필터링 가능.",
    input_schema={
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "enum": ["video_creative", "design", "writing", "marketing", "development"],
                "description": "카테고리 필터",
            },
            "max_budget": {
                "type": "integer",
                "description": "최대 예산 (크레딧)",
            },
            "limit": {
                "type": "integer",
                "description": "최대 결과 수 (기본: 5)",
                "default": 5,
            },
        },
        "required": [],
    },
)

SEARCH_CREATORS_SPEC = ToolSpec(
    name="search_creators",
    description="휴먼클라우드에서 크리에이터를 검색합니다. 스킬이나 카테고리로 필터링 가능.",
    input_schema={
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "enum": ["video_creative", "design", "writing", "marketing", "development"],
                "description": "카테고리 필터",
            },
            "skill": {
                "type": "string",
                "enum": ["video_editing", "motion_graphics", "graphic_design", "copywriting", "web_development"],
                "description": "스킬 필터",
            },
            "limit": {
                "type": "integer",
                "description": "최대 결과 수 (기본: 5)",
                "default": 5,
            },
        },
        "required": [],
    },
)


# =============================================================================
# Handlers
# =============================================================================

async def _search_requests_handler(context: ToolContext, call: ToolCall) -> ToolResult:
    """요청 검색 핸들러."""
    category = call.arguments.get("category")
    max_budget = call.arguments.get("max_budget")
    limit = call.arguments.get("limit", 5)
    
    try:
        async with AsyncSessionLocal() as db:
            stmt = select(CreativeRequest).where(CreativeRequest.status == "open")
            
            if category:
                stmt = stmt.where(CreativeRequest.category == category)
            
            if max_budget:
                stmt = stmt.where(CreativeRequest.budget_credits <= max_budget)
            
            stmt = stmt.order_by(CreativeRequest.created_at.desc()).limit(limit)
            
            result = await db.execute(stmt)
            requests = result.scalars().all()
            
            if not requests:
                return success_result(call, {"requests": [], "count": 0, "message": "열린 요청이 없습니다."})
            
            request_list = []
            for r in requests:
                request_list.append({
                    "id": str(r.id),
                    "title": r.title,
                    "description": r.description[:100] + "..." if len(r.description) > 100 else r.description,
                    "category": r.category,
                    "budget_credits": r.budget_credits,
                    "status": r.status,
                    "deadline": r.deadline.isoformat() if r.deadline else None,
                })
            
            logger.info(
                "Requests searched",
                extra={"category": category, "count": len(request_list)},
            )
            
            return success_result(call, {"requests": request_list, "count": len(request_list)})
            
    except Exception as e:
        logger.error(f"Request search failed: {e}")
        return error_result(call, f"요청 검색 중 오류: {str(e)}")


async def _search_creators_handler(context: ToolContext, call: ToolCall) -> ToolResult:
    """크리에이터 검색 핸들러."""
    category = call.arguments.get("category", "video_creative")
    skill = call.arguments.get("skill")
    limit = call.arguments.get("limit", 5)
    
    try:
        async with AsyncSessionLocal() as db:
            stmt = select(CreatorProfile).where(CreatorProfile.is_available == True)
            
            # 카테고리 필터 (JSON 배열 내 포함 여부)
            if category:
                stmt = stmt.where(CreatorProfile.categories.contains([category]))
            
            # 스킬 필터
            if skill:
                stmt = stmt.where(CreatorProfile.skills.contains([skill]))
            
            stmt = stmt.order_by(CreatorProfile.completed_count.desc()).limit(limit)
            
            result = await db.execute(stmt)
            creators = result.scalars().all()
            
            if not creators:
                return success_result(call, {"creators": [], "count": 0, "message": "해당 조건의 크리에이터를 찾지 못했습니다."})
            
            creator_list = []
            for c in creators:
                creator_list.append({
                    "id": str(c.id),
                    "display_name": c.display_name,
                    "bio": c.bio[:100] + "..." if c.bio and len(c.bio) > 100 else c.bio,
                    "categories": c.categories or [],
                    "skills": c.skills or [],
                    "completed_count": c.completed_count,
                    "avg_rating": float(c.avg_rating) if c.avg_rating else None,
                    "is_verified": c.is_verified,
                })
            
            logger.info(
                "Creators searched",
                extra={"category": category, "skill": skill, "count": len(creator_list)},
            )
            
            return success_result(call, {"creators": creator_list, "count": len(creator_list)})
            
    except Exception as e:
        logger.error(f"Creator search failed: {e}")
        return error_result(call, f"크리에이터 검색 중 오류: {str(e)}")


# =============================================================================
# Registration
# =============================================================================

def get_humancloud_tool_specs() -> List[ToolSpec]:
    """휴먼클라우드 도구 스펙 목록 반환."""
    return [SEARCH_REQUESTS_SPEC, SEARCH_CREATORS_SPEC]


def register_humancloud_tools(registry: ToolRegistry) -> None:
    """휴먼클라우드 도구 등록."""
    registry.register(SEARCH_REQUESTS_SPEC, _search_requests_handler)
    registry.register(SEARCH_CREATORS_SPEC, _search_creators_handler)
    logger.info("HumanCloud tools registered", extra={"count": 2})
