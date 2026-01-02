"""Seed Tool Manifests from Legacy Capsule Registry.

This script migrates the 8 capsules from capsule_registry.py
into the new ToolManifest database table.

Run: python -m scripts.seed_tool_manifests
"""
import asyncio
import logging
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker
from app.models_telemetry import ToolManifest, ToolTier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# Capsule Definitions (from capsule_registry.py)
# =============================================================================

LEGACY_CAPSULES = [
    # NotebookLM RAG (4)
    {
        "tool_key": "nlm_notebook_create",
        "display_name": "📓 노트북 생성",
        "category": "notebooklm",
        "description": "NotebookLM Enterprise에서 새 노트북을 생성합니다",
        "credit_cost": 1,
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "노트북 제목"}
            },
            "required": ["title"]
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "notebook_id": {"type": "string", "description": "노트북 ID"}
            }
        },
        "legacy_endpoint": "/api/v1/agent/tool/create_notebook",
    },
    {
        "tool_key": "nlm_sources_add",
        "display_name": "📎 소스 추가",
        "category": "notebooklm",
        "description": "노트북에 텍스트, URL, Drive 문서를 추가합니다",
        "credit_cost": 2,
        "input_schema": {
            "type": "object",
            "properties": {
                "notebook_id": {"type": "string", "description": "노트북 ID"},
                "sources": {"type": "array", "description": "소스 배열"}
            },
            "required": ["notebook_id", "sources"]
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "source_ids": {"type": "array", "description": "소스 ID 목록"},
                "source_content": {"type": "string", "description": "소스 내용 요약"}
            }
        },
        "legacy_endpoint": "/api/v1/agent/tool/add_sources",
    },
    {
        "tool_key": "nlm_audio_generate",
        "display_name": "🎙️ 오디오 오버뷰",
        "category": "notebooklm",
        "description": "AI 오디오 오버뷰(팟캐스트 스타일)를 생성합니다",
        "credit_cost": 5,
        "input_schema": {
            "type": "object",
            "properties": {
                "notebook_id": {"type": "string", "description": "노트북 ID"},
                "focus": {"type": "string", "description": "강조 주제"}
            },
            "required": ["notebook_id"]
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "audio_url": {"type": "string", "description": "오디오 URL"},
                "status": {"type": "string", "description": "상태"}
            }
        },
        "legacy_endpoint": "/api/v1/agent/tool/generate_audio_overview",
    },
    {
        "tool_key": "nlm_notebooks_list",
        "display_name": "📋 노트북 목록",
        "category": "notebooklm",
        "description": "최근 노트북 목록을 조회합니다",
        "credit_cost": 0,
        "input_schema": {
            "type": "object",
            "properties": {
                "page_size": {"type": "integer", "description": "페이지 크기"}
            }
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "notebooks": {"type": "array", "description": "노트북 목록"}
            }
        },
        "legacy_endpoint": "/api/v1/agent/tool/list_notebooks",
    },
    
    # Teaching Capsules (4)
    {
        "tool_key": "teaching_prompt_generate",
        "display_name": "✨ Veo 프롬프트",
        "category": "teaching",
        "description": "영상 주제/스타일로 Veo 비디오 생성 프롬프트를 만듭니다",
        "credit_cost": 2,
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "주제"},
                "style": {"type": "string", "description": "스타일"},
                "mood": {"type": "string", "description": "분위기"},
                "duration": {"type": "string", "description": "길이"}
            },
            "required": ["topic"]
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "프롬프트"},
                "negative_prompt": {"type": "string", "description": "네거티브 프롬프트"},
                "technical": {"type": "object", "description": "기술 설정"}
            }
        },
        "legacy_endpoint": "/api/v1/teaching/prompt/generate",
    },
    {
        "tool_key": "teaching_storyboard_create",
        "display_name": "🎬 스토리보드",
        "category": "teaching",
        "description": "스토리 컨셉으로 씬 단위 스토리보드를 생성합니다",
        "credit_cost": 3,
        "input_schema": {
            "type": "object",
            "properties": {
                "concept": {"type": "string", "description": "컨셉"},
                "scene_count": {"type": "integer", "description": "씬 개수"}
            },
            "required": ["concept"]
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "scenes": {"type": "array", "description": "씬 목록"}
            }
        },
        "legacy_endpoint": "/api/v1/teaching/storyboard/create",
    },
    {
        "tool_key": "teaching_image_generate",
        "display_name": "🖼️ 이미지 프롬프트",
        "category": "teaching",
        "description": "이미지 설명으로 AI 이미지 생성 프롬프트를 만듭니다",
        "credit_cost": 2,
        "input_schema": {
            "type": "object",
            "properties": {
                "description": {"type": "string", "description": "설명"},
                "style": {"type": "string", "description": "스타일"},
                "aspect_ratio": {"type": "string", "description": "종횡비"}
            },
            "required": ["description"]
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "프롬프트"},
                "parameters": {"type": "object", "description": "파라미터"}
            }
        },
        "legacy_endpoint": "/api/v1/teaching/image/generate",
    },
    {
        "tool_key": "teaching_reference_analyze",
        "display_name": "🔍 레퍼런스 분석",
        "category": "teaching",
        "description": "영상 레퍼런스의 시네마틱 요소를 분석합니다",
        "credit_cost": 3,
        "input_schema": {
            "type": "object",
            "properties": {
                "video_description": {"type": "string", "description": "영상 설명"},
                "focus_areas": {"type": "array", "description": "분석 초점"}
            },
            "required": ["video_description"]
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "analysis": {"type": "object", "description": "분석 결과"},
                "recommendations": {"type": "array", "description": "추천사항"},
                "insights": {"type": "string", "description": "인사이트 요약"}
            }
        },
        "legacy_endpoint": "/api/v1/teaching/reference/analyze",
    },
]


async def seed_tool_manifests() -> None:
    """Seed the database with legacy capsule definitions."""
    async with async_session_maker() as db:
        created = 0
        skipped = 0
        
        for capsule in LEGACY_CAPSULES:
            # Check if already exists
            result = await db.execute(
                select(ToolManifest).where(ToolManifest.tool_key == capsule["tool_key"])
            )
            if result.scalars().first():
                logger.info(f"Skipping existing tool: {capsule['tool_key']}")
                skipped += 1
                continue
            
            # Create new manifest
            manifest = ToolManifest(
                id=uuid4(),
                tool_key=capsule["tool_key"],
                display_name=capsule["display_name"],
                description=capsule["description"],
                category=capsule["category"],
                tier=ToolTier.VERIFIED.value,  # Legacy tools start as VERIFIED
                input_schema=capsule["input_schema"],
                output_schema=capsule["output_schema"],
                credit_cost=capsule["credit_cost"],
                created_by="system",
                is_active=True,
                safety_rating="safe",
                sandbox_required=False,
            )
            
            db.add(manifest)
            logger.info(f"Created tool: {capsule['tool_key']}")
            created += 1
        
        await db.commit()
        logger.info(f"Seed complete: {created} created, {skipped} skipped")


async def list_tool_manifests() -> None:
    """List all tool manifests in the database."""
    async with async_session_maker() as db:
        result = await db.execute(select(ToolManifest).order_by(ToolManifest.category))
        tools = result.scalars().all()
        
        print(f"\n{'='*60}")
        print(f" Tool Manifests ({len(tools)} total)")
        print(f"{'='*60}\n")
        
        for tool in tools:
            print(f"[{tool.tier.upper()}] {tool.display_name}")
            print(f"  Key: {tool.tool_key}")
            print(f"  Category: {tool.category}")
            print(f"  Credits: {tool.credit_cost}")
            print()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        asyncio.run(list_tool_manifests())
    else:
        asyncio.run(seed_tool_manifests())
