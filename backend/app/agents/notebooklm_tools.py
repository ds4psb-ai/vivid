"""NotebookLM Enterprise API tools for VividAgent.

Wraps NotebookLM Enterprise API functionality as callable agent tools,
enabling notebook creation, source management, and audio overview generation.

Refactored to use shared utilities from tool_utils.py.
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict

from app.agents.agent_types import (
    ToolCall,
    ToolContext,
    ToolRegistry,
    ToolResult,
    ToolSpec,
)
from app.agents.tool_utils import (
    create_emitter,
    error_result,
    get_enterprise_client,
    success_result,
    validation_error,
)
from app.logging_config import get_logger

logger = get_logger("notebooklm_tools")


# =============================================================================
# Tool Handlers
# =============================================================================

async def _create_notebook_handler(
    context: ToolContext,
    call: ToolCall,
) -> ToolResult:
    """새 NotebookLM Enterprise 노트북을 생성합니다."""
    title = call.arguments.get("title", "Untitled Notebook")
    
    try:
        client = get_enterprise_client()
        notebook = await client.create_notebook(title)
        
        logger.info("Notebook created", extra={
            "session_id": context.session_id,
            "notebook_id": notebook.notebook_id,
            "title": title,
        })
        
        return success_result(call, {
            "notebook_id": notebook.notebook_id,
            "title": notebook.title,
            "name": notebook.name,
            "user_role": notebook.user_role,
        })
        
    except Exception as e:
        logger.exception("Failed to create notebook", extra={
            "session_id": context.session_id, "error": str(e)
        })
        return error_result(call, f"Notebook creation failed: {e}")


async def _add_sources_handler(
    context: ToolContext,
    call: ToolCall,
) -> ToolResult:
    """노트북에 소스를 추가합니다 (텍스트, 웹 URL, 또는 Drive 문서)."""
    args = call.arguments
    notebook_id = args.get("notebook_id")
    sources = args.get("sources", [])
    
    if not notebook_id:
        return validation_error(call, "notebook_id")
    if not sources:
        return validation_error(call, "sources", "sources array is required")
    
    try:
        client = get_enterprise_client()
        added = await _process_sources(client, notebook_id, sources)
        
        logger.info("Sources added", extra={
            "session_id": context.session_id,
            "notebook_id": notebook_id,
            "sources_count": len(added),
        })
        
        return success_result(call, {
            "notebook_id": notebook_id,
            "added_sources": added,
            "total_added": len(added),
        })
        
    except Exception as e:
        logger.exception("Failed to add sources", extra={
            "session_id": context.session_id, "error": str(e)
        })
        return error_result(call, f"Source addition failed: {e}")


async def _process_sources(
    client: Any,
    notebook_id: str,
    sources: list,
) -> list:
    """Process and add sources to notebook. Extracted for testability."""
    added = []
    
    SOURCE_HANDLERS = {
        "text": lambda c, nid, src: c.add_text_source(
            nid, src.get("name", "Unnamed"), src.get("content", "")
        ),
        "web": lambda c, nid, src: c.add_web_source(
            nid, src.get("name", "Unnamed"), src.get("url", "")
        ),
        "drive": lambda c, nid, src: c.add_drive_source(
            nid,
            src.get("name", "Unnamed"),
            src.get("document_id", ""),
            src.get("mime_type", "application/vnd.google-apps.document"),
        ),
    }
    
    for src in sources:
        src_type = src.get("type", "text")
        handler = SOURCE_HANDLERS.get(src_type)
        
        if handler:
            result = await handler(client, notebook_id, src)
            added.append({
                "source_id": result.source_id,
                "name": src.get("name", "Unnamed"),
                "type": src_type,
            })
    
    return added


async def _generate_audio_overview_handler(
    context: ToolContext,
    call: ToolCall,
) -> ToolResult:
    """AI 오디오 오버뷰를 생성합니다."""
    args = call.arguments
    notebook_id = args.get("notebook_id")
    focus = args.get("focus", "")
    language_code = args.get("language_code", "ko")
    source_ids = args.get("source_ids")
    
    if not notebook_id:
        return validation_error(call, "notebook_id")
    
    emitter = create_emitter(context, call)
    
    try:
        client = get_enterprise_client()
        
        emitter.emit("agent.audio_overview_start", {
            "notebook_id": notebook_id,
            "status": "creating",
        })
        
        overview = await client.create_audio_overview(
            notebook_id=notebook_id,
            source_ids=source_ids,
            focus=focus,
            language_code=language_code,
        )
        
        # Poll until ready (max 60 seconds)
        overview = await _poll_audio_overview(
            client, notebook_id, overview, emitter
        )
        
        logger.info("Audio overview generated", extra={
            "session_id": context.session_id,
            "notebook_id": notebook_id,
            "audio_overview_id": overview.audio_overview_id,
            "status": overview.status,
        })
        
        return success_result(call, {
            "notebook_id": notebook_id,
            "audio_overview_id": overview.audio_overview_id,
            "status": overview.status,
            "name": overview.name,
            "focus": focus,
            "language_code": language_code,
        })
        
    except Exception as e:
        logger.exception("Failed to generate audio overview", extra={
            "session_id": context.session_id, "error": str(e)
        })
        return error_result(call, f"Audio overview generation failed: {e}")


async def _poll_audio_overview(
    client: Any,
    notebook_id: str,
    overview: Any,
    emitter: Any,
    max_attempts: int = 12,
    poll_interval: int = 5,
) -> Any:
    """Poll for audio overview completion. Extracted for testability."""
    READY_STATES = ("READY", "COMPLETED", "DONE")
    
    for attempt in range(max_attempts):
        if overview.status in READY_STATES:
            break
        
        await asyncio.sleep(poll_interval)
        overview = await client.get_audio_overview(
            notebook_id, overview.audio_overview_id
        )
        
        progress = min(95, (attempt + 1) * 8)
        emitter.emit("agent.audio_overview_progress", {
            "notebook_id": notebook_id,
            "audio_overview_id": overview.audio_overview_id,
            "status": overview.status,
            "progress": progress,
        })
    
    return overview


async def _list_notebooks_handler(
    context: ToolContext,
    call: ToolCall,
) -> ToolResult:
    """최근 노트북 목록을 조회합니다."""
    page_size = call.arguments.get("page_size", 10)
    
    try:
        client = get_enterprise_client()
        notebooks = await client.list_notebooks(page_size=page_size)
        
        notebook_list = [
            {
                "notebook_id": nb.notebook_id,
                "title": nb.title,
                "user_role": nb.user_role,
                "is_shared": nb.is_shared,
            }
            for nb in notebooks
        ]
        
        logger.info("Notebooks listed", extra={
            "session_id": context.session_id,
            "count": len(notebook_list),
        })
        
        return success_result(call, {
            "notebooks": notebook_list,
            "count": len(notebook_list),
        })
        
    except Exception as e:
        logger.exception("Failed to list notebooks", extra={
            "session_id": context.session_id, "error": str(e)
        })
        return error_result(call, f"Notebook listing failed: {e}")


# =============================================================================
# Tool Specifications
# =============================================================================

_SPECS = [
    ToolSpec(
        name="create_notebook",
        description="NotebookLM Enterprise에서 새 노트북을 생성합니다. 노트북은 소스 분석 및 오디오 오버뷰 생성의 컨테이너입니다.",
        input_schema={
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "노트북 제목 (예: '봉준호 HOOK 분석')",
                },
            },
            "required": ["title"],
        },
    ),
    ToolSpec(
        name="add_sources",
        description="노트북에 소스를 추가합니다. 텍스트, 웹 URL, 또는 Google Drive 문서를 추가할 수 있습니다.",
        input_schema={
            "type": "object",
            "properties": {
                "notebook_id": {
                    "type": "string",
                    "description": "소스를 추가할 노트북 ID",
                },
                "sources": {
                    "type": "array",
                    "description": "추가할 소스 배열",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string", "enum": ["text", "web", "drive"]},
                            "name": {"type": "string"},
                            "content": {"type": "string"},
                            "url": {"type": "string"},
                            "document_id": {"type": "string"},
                        },
                        "required": ["type", "name"],
                    },
                },
            },
            "required": ["notebook_id", "sources"],
        },
    ),
    ToolSpec(
        name="generate_audio_overview",
        description="AI 오디오 오버뷰를 생성합니다. 노트북의 소스들을 기반으로 AI가 생성한 오디오 요약(팟캐스트 스타일)을 만듭니다.",
        input_schema={
            "type": "object",
            "properties": {
                "notebook_id": {"type": "string", "description": "오디오 오버뷰를 생성할 노트북 ID"},
                "focus": {"type": "string", "description": "강조할 주제 또는 콘텐츠 설명"},
                "language_code": {"type": "string", "default": "ko"},
                "source_ids": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["notebook_id"],
        },
    ),
    ToolSpec(
        name="list_notebooks",
        description="최근 NotebookLM Enterprise 노트북 목록을 조회합니다.",
        input_schema={
            "type": "object",
            "properties": {
                "page_size": {"type": "integer", "default": 10},
            },
        },
    ),
]

_HANDLERS = {
    "create_notebook": _create_notebook_handler,
    "add_sources": _add_sources_handler,
    "generate_audio_overview": _generate_audio_overview_handler,
    "list_notebooks": _list_notebooks_handler,
}


def register_notebooklm_tools(registry: ToolRegistry) -> None:
    """Register NotebookLM Enterprise tools with the given registry."""
    for spec in _SPECS:
        handler = _HANDLERS.get(spec.name)
        if handler:
            registry.register(spec, handler)
    
    logger.info(f"Registered {len(_SPECS)} NotebookLM tools")
