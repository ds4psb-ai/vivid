"""Singularity Tools for VividAgent.

초끼가 템플릿 검색 및 적용을 도와주는 도구들.
"""
from __future__ import annotations

from typing import Dict, Any, List
from uuid import UUID

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
from app.models_singularity import BlackholeTemplate
from app.logging_config import get_logger

logger = get_logger("singularity_tools")

# =============================================================================
# Tool Specs
# =============================================================================

SEARCH_TEMPLATES_SPEC = ToolSpec(
    name="search_templates",
    description="싱귤래리티 템플릿 갤러리에서 템플릿을 검색합니다. 태그, 차원, 카테고리로 필터링 가능.",
    input_schema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "검색 키워드 (제목, 설명에서 검색)",
            },
            "dimension": {
                "type": "string",
                "enum": ["1D", "2D", "3D", "4D"],
                "description": "차원 필터 (1D=프롬프트, 2D=스토리보드, 3D=이미지, 4D=레퍼런스)",
            },
            "category": {
                "type": "string",
                "enum": ["marketing", "education", "entertainment", "business", "creative"],
                "description": "카테고리 필터",
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

APPLY_TEMPLATE_SPEC = ToolSpec(
    name="apply_template",
    description="템플릿을 적용합니다. 템플릿 ID 또는 이름으로 지정.",
    input_schema={
        "type": "object",
        "properties": {
            "template_id": {
                "type": "string",
                "description": "템플릿 UUID",
            },
            "template_name": {
                "type": "string",
                "description": "템플릿 이름 (ID 없을 때 검색)",
            },
        },
        "required": [],
    },
)

GET_TEMPLATE_DETAIL_SPEC = ToolSpec(
    name="get_template_detail",
    description="템플릿 상세 정보를 조회합니다.",
    input_schema={
        "type": "object",
        "properties": {
            "template_id": {
                "type": "string",
                "description": "템플릿 UUID",
            },
        },
        "required": ["template_id"],
    },
)


# =============================================================================
# Handlers
# =============================================================================

async def _search_templates_handler(context: ToolContext, call: ToolCall) -> ToolResult:
    """템플릿 검색 핸들러."""
    query = call.arguments.get("query", "")
    dimension = call.arguments.get("dimension")
    category = call.arguments.get("category")
    limit = call.arguments.get("limit", 5)
    
    try:
        async with AsyncSessionLocal() as db:
            stmt = select(BlackholeTemplate).where(
                BlackholeTemplate.is_public == True,
                BlackholeTemplate.is_approved == True
            )
            
            # 키워드 검색
            if query:
                search_term = f"%{query}%"
                stmt = stmt.where(
                    (BlackholeTemplate.title.ilike(search_term)) |
                    (BlackholeTemplate.description.ilike(search_term))
                )
            
            # 차원 필터
            if dimension:
                stmt = stmt.where(BlackholeTemplate.dimension_source == dimension)
            
            # 카테고리 필터
            if category:
                stmt = stmt.where(BlackholeTemplate.category == category)
            
            # 정렬 및 제한
            stmt = stmt.order_by(BlackholeTemplate.use_count.desc()).limit(limit)
            
            result = await db.execute(stmt)
            templates = result.scalars().all()
            
            if not templates:
                return success_result(call, {"templates": [], "count": 0, "message": "검색 결과가 없습니다."})
            
            template_list = []
            for t in templates:
                template_list.append({
                    "id": str(t.id),
                    "title": t.title,
                    "description": t.description[:100] + "..." if len(t.description) > 100 else t.description,
                    "dimension": t.dimension_source,
                    "category": t.category,
                    "use_count": t.use_count,
                    "rating_avg": float(t.rating_avg) if t.rating_avg else 0.0,
                    "is_featured": t.is_featured,
                })
            
            logger.info(
                "Templates searched",
                extra={"query": query, "dimension": dimension, "count": len(template_list)},
            )
            
            return success_result(call, {"templates": template_list, "count": len(template_list)})
            
    except Exception as e:
        logger.error(f"Template search failed: {e}")
        return error_result(call, f"템플릿 검색 중 오류: {str(e)}")


async def _apply_template_handler(context: ToolContext, call: ToolCall) -> ToolResult:
    """템플릿 적용 핸들러.
    
    Phase 3: Intent-based 템플릿은 input_preset에서 intent를 추출하여
    downstream tool 호출에서 활용할 수 있도록 반환합니다.
    """
    template_id = call.arguments.get("template_id")
    template_name = call.arguments.get("template_name")
    
    if not template_id and not template_name:
        return error_result(call, "template_id 또는 template_name 중 하나를 지정하세요.")
    
    try:
        async with AsyncSessionLocal() as db:
            if template_id:
                try:
                    uuid_id = UUID(template_id)
                except ValueError:
                    return error_result(call, "유효하지 않은 템플릿 ID입니다.")
                stmt = select(BlackholeTemplate).where(BlackholeTemplate.id == uuid_id)
            else:
                stmt = select(BlackholeTemplate).where(
                    BlackholeTemplate.title.ilike(f"%{template_name}%")
                ).limit(1)
            
            result = await db.execute(stmt)
            template = result.scalars().first()
            
            if not template:
                return error_result(call, "템플릿을 찾을 수 없습니다.")
            
            # 사용 횟수 증가
            template.use_count = (template.use_count or 0) + 1
            await db.commit()
            
            # === Phase 3: Intent Extraction ===
            input_preset = template.input_preset or {}
            extracted_intent = None
            
            try:
                from app.resolvers.integration import extract_intent_from_preset
                intent, legacy_params = extract_intent_from_preset(input_preset)
                if intent:
                    extracted_intent = intent.model_dump()
                    logger.debug(
                        "Intent extracted from template",
                        extra={"template_id": str(template.id), "mood": intent.mood.value},
                    )
            except ImportError:
                logger.debug("Resolver integration not available")
            except Exception as e:
                logger.warning(f"Intent extraction failed: {e}")
            
            # 네비게이션 이벤트 전송 (Flow 페이지로)
            if context.emit_event:
                context.emit_event("agent.navigation", {"path": "/flow"})
            
            logger.info(
                "Template applied",
                extra={
                    "template_id": str(template.id), 
                    "title": template.title,
                    "has_intent": extracted_intent is not None,
                },
            )
            
            return success_result(call, {
                "template_id": str(template.id),
                "title": template.title,
                "tool_sequence": template.tool_sequence or [],
                "input_preset": input_preset,
                # Phase 3: Intent 정보 추가 (downstream tool에서 활용)
                "_extracted_intent": extracted_intent,
                "_template_preset": input_preset,  # dimension_tools에서 사용
                "applied": True,
                "message": f"'{template.title}' 템플릿이 적용되었습니다. Flow 페이지로 이동합니다.",
            })
            
    except Exception as e:
        logger.error(f"Template apply failed: {e}")
        return error_result(call, f"템플릿 적용 중 오류: {str(e)}")


async def _get_template_detail_handler(context: ToolContext, call: ToolCall) -> ToolResult:
    """템플릿 상세 조회 핸들러."""
    template_id = call.arguments.get("template_id")
    
    if not template_id:
        return error_result(call, "template_id가 필요합니다.")
    
    try:
        uuid_id = UUID(template_id)
    except ValueError:
        return error_result(call, "유효하지 않은 템플릿 ID입니다.")
    
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(BlackholeTemplate).where(BlackholeTemplate.id == uuid_id)
            )
            template = result.scalars().first()
            
            if not template:
                return error_result(call, "템플릿을 찾을 수 없습니다.")
            
            return success_result(call, {
                "id": str(template.id),
                "title": template.title,
                "description": template.description,
                "dimension_source": template.dimension_source,
                "tool_sequence": template.tool_sequence or [],
                "input_preset": template.input_preset or {},
                "output_example": template.output_example or {},
                "category": template.category,
                "tags": template.tags or [],
                "use_count": template.use_count,
                "rating_avg": float(template.rating_avg) if template.rating_avg else 0.0,
                "is_featured": template.is_featured,
            })
            
    except Exception as e:
        logger.error(f"Template detail failed: {e}")
        return error_result(call, f"템플릿 조회 중 오류: {str(e)}")


# =============================================================================
# Registration
# =============================================================================

def get_singularity_tool_specs() -> List[ToolSpec]:
    """싱귤래리티 도구 스펙 목록 반환."""
    return [SEARCH_TEMPLATES_SPEC, APPLY_TEMPLATE_SPEC, GET_TEMPLATE_DETAIL_SPEC]


def register_singularity_tools(registry: ToolRegistry) -> None:
    """싱귤래리티 도구 등록."""
    registry.register(SEARCH_TEMPLATES_SPEC, _search_templates_handler)
    registry.register(APPLY_TEMPLATE_SPEC, _apply_template_handler)
    registry.register(GET_TEMPLATE_DETAIL_SPEC, _get_template_detail_handler)
    logger.info("Singularity tools registered", extra={"count": 3})
