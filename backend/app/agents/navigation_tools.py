"""Navigation Tools for VividAgent.

초끼가 사용자를 페이지로 이동시키는 도구.
Frontend에서 'agent.navigation' 이벤트를 수신하여 router.push() 실행.
"""
from __future__ import annotations

from typing import Dict, Any, List

from app.agents.agent_types import (
    ToolCall,
    ToolContext,
    ToolRegistry,
    ToolResult,
    ToolSpec,
)
from app.agents.tool_utils import success_result, error_result
from app.logging_config import get_logger

logger = get_logger("navigation_tools")

# 허용된 페이지 목록 (화이트리스트)
PAGES: Dict[str, str] = {
    # Core
    "dimension": "/dimension",
    "singularity": "/singularity",
    "flow": "/flow",
    
    # Tools
    "tools": "/tools",
    "tools_create": "/tools/create",
    
    # HumanCloud
    "humancloud": "/humancloud",
    "humancloud_requests": "/humancloud/requests",
    "humancloud_requests_create": "/humancloud/requests/create",
    "humancloud_creator": "/humancloud/creator",
    
    # Settings
    "settings": "/settings",
    "credits": "/credits",
    
    # Crebit
    "crebit": "/crebit",
    
    # Admin
    "admin": "/admin",
}

# 페이지 별칭 (자연어 → 페이지 키)
PAGE_ALIASES: Dict[str, str] = {
    "스토리보드": "dimension",
    "미니앱": "dimension",
    "차원문": "dimension",
    "템플릿": "singularity",
    "싱귤래리티": "singularity",
    "특이점": "singularity",
    "도구": "tools",
    "도구 만들기": "tools_create",
    "도구 생성": "tools_create",
    "휴먼클라우드": "humancloud",
    "마켓플레이스": "humancloud",
    "요청": "humancloud_requests",
    "요청 만들기": "humancloud_requests_create",
    "크리에이터": "humancloud_creator",
    "설정": "settings",
    "크레딧": "credits",
    "crebit": "crebit",
    "관리자": "admin",
}

NAVIGATE_PAGE_SPEC = ToolSpec(
    name="navigate_page",
    description="사용자를 특정 페이지로 이동시킵니다. 예: '스토리보드 페이지로 이동해줘', '템플릿 갤러리 보여줘'",
    input_schema={
        "type": "object",
        "properties": {
            "page_name": {
                "type": "string",
                "enum": ["dimension", "singularity", "flow", "tools", "tools_create", "humancloud", "humancloud_requests", "humancloud_requests_create", "humancloud_creator", "settings", "credits", "crebit", "admin"],
                "description": "이동할 페이지 이름",
            },
        },
        "required": ["page_name"],
    },
)


async def _navigate_handler(context: ToolContext, call: ToolCall) -> ToolResult:
    """페이지 이동 핸들러."""
    page_name = call.arguments.get("page_name", "").lower().strip()
    
    # 별칭 해결
    if page_name in PAGE_ALIASES:
        page_key = PAGE_ALIASES[page_name]
    elif page_name in PAGES:
        page_key = page_name
    else:
        # 부분 매칭 시도
        matched = None
        for alias, key in PAGE_ALIASES.items():
            if page_name in alias or alias in page_name:
                matched = key
                break
        if matched:
            page_key = matched
        else:
            return error_result(call, f"'{page_name}' 페이지를 찾을 수 없습니다. 이용 가능: {', '.join(PAGES.keys())}")
    
    target_path = PAGES[page_key]
    
    # Frontend로 네비게이션 이벤트 전송
    if context.emit_event:
        context.emit_event("agent.navigation", {"path": target_path})
    
    logger.info(
        "Navigation requested",
        extra={"page_name": page_name, "resolved": page_key, "path": target_path},
    )
    
    return success_result(call, {"navigated_to": target_path, "page_key": page_key})


def get_navigation_tool_specs() -> List[ToolSpec]:
    """네비게이션 도구 스펙 목록 반환."""
    return [NAVIGATE_PAGE_SPEC]


def register_navigation_tools(registry: ToolRegistry) -> None:
    """네비게이션 도구 등록."""
    registry.register(NAVIGATE_PAGE_SPEC, _navigate_handler)
    logger.info("Navigation tools registered", extra={"count": 1})
