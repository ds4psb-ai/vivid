"""Seed script to register 4 dimension tools in ToolManifest table.

This enables the telemetry pipeline to track tool usage.

Run with: python -m scripts.seed_dimension_tools
"""
import asyncio
import logging
from uuid import uuid4

from app.database import AsyncSessionLocal
from app.models_telemetry import ToolManifest, ToolTier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the 4 core dimension tools
DIMENSION_TOOLS = [
    {
        "tool_key": "generate_veo_prompt",
        "display_name": "1D Origin - Veo 프롬프트 생성기",
        "description": "영상 주제/스타일/분위기로 Veo 비디오 생성 프롬프트를 만듭니다",
        "category": "dimension",
        "credit_cost": 1,
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "영상 주제 또는 컨셉 (필수)"},
                "style": {
                    "type": "string",
                    "enum": ["cinematic", "documentary", "commercial", "artistic", "vlog"],
                    "description": "영상 스타일",
                },
                "mood": {
                    "type": "string",
                    "enum": ["neutral", "dramatic", "calm", "energetic", "melancholic"],
                    "description": "분위기/톤",
                },
                "duration": {"type": "string", "description": "영상 길이"},
            },
            "required": ["topic"],
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string"},
                "negative_prompt": {"type": "string"},
                "technical_params": {"type": "object"},
            },
        },
    },
    {
        "tool_key": "create_storyboard",
        "display_name": "2D Blueprint - 스토리보드 생성기",
        "description": "스토리 컨셉으로 씬 단위 스토리보드를 생성합니다",
        "category": "dimension",
        "credit_cost": 1,
        "input_schema": {
            "type": "object",
            "properties": {
                "concept": {"type": "string", "description": "스토리 컨셉 또는 시나리오"},
                "scene_count": {"type": "integer", "description": "생성할 씬 개수 (3~20)"},
            },
            "required": ["concept"],
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "scenes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "scene_number": {"type": "integer"},
                            "description": {"type": "string"},
                            "camera": {"type": "string"},
                        },
                    },
                },
            },
        },
    },
    {
        "tool_key": "generate_image_prompt",
        "display_name": "3D Ambience - 이미지 프롬프트 생성기",
        "description": "이미지 설명으로 AI 이미지 생성 프롬프트를 만듭니다",
        "category": "dimension",
        "credit_cost": 1,
        "input_schema": {
            "type": "object",
            "properties": {
                "description": {"type": "string", "description": "이미지 설명"},
                "style": {
                    "type": "string",
                    "enum": ["photorealistic", "cinematic", "anime", "illustration", "3d-render"],
                    "description": "이미지 스타일",
                },
                "aspect_ratio": {
                    "type": "string",
                    "enum": ["16:9", "9:16", "1:1", "4:3"],
                    "description": "종횡비",
                },
            },
            "required": ["description"],
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string"},
                "parameters": {"type": "object"},
            },
        },
    },
    {
        "tool_key": "analyze_reference",
        "display_name": "4D Moment - 레퍼런스 분석기",
        "description": "영상 레퍼런스의 시네마틱 요소를 분석합니다",
        "category": "dimension",
        "credit_cost": 1,
        "input_schema": {
            "type": "object",
            "properties": {
                "video_description": {"type": "string", "description": "분석할 영상의 특징 설명"},
                "focus_areas": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "분석 초점: composition, lighting, color, movement, narrative",
                },
            },
            "required": ["video_description"],
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "analysis": {"type": "object"},
                "recommendations": {"type": "array"},
            },
        },
    },
]


async def seed_dimension_tools():
    """Register 4 dimension tools in ToolManifest table."""
    async with AsyncSessionLocal() as db:
        created_count = 0
        updated_count = 0
        
        for tool_data in DIMENSION_TOOLS:
            # Check if tool already exists
            from sqlalchemy import select
            result = await db.execute(
                select(ToolManifest).where(ToolManifest.tool_key == tool_data["tool_key"])
            )
            existing = result.scalars().first()
            
            if existing:
                # Update existing tool
                existing.display_name = tool_data["display_name"]
                existing.description = tool_data["description"]
                existing.input_schema = tool_data["input_schema"]
                existing.output_schema = tool_data["output_schema"]
                existing.credit_cost = tool_data["credit_cost"]
                updated_count += 1
                logger.info(f"Updated: {tool_data['tool_key']}")
            else:
                # Create new tool
                tool = ToolManifest(
                    id=uuid4(),
                    tool_key=tool_data["tool_key"],
                    display_name=tool_data["display_name"],
                    description=tool_data["description"],
                    version="1.0.0",  # String format
                    category=tool_data["category"],
                    tier=ToolTier.VERIFIED.value,  # Use .value for enum
                    input_schema=tool_data["input_schema"],
                    output_schema=tool_data["output_schema"],
                    credit_cost=tool_data["credit_cost"],
                    fork_count=0,
                    usage_count=0,
                    total_revenue=0,
                    parent_tool_id=None,
                    fork_depth=0,
                    created_by="system",
                    safety_rating="safe",
                    sandbox_required=False,
                    is_active=True,
                )
                db.add(tool)
                created_count += 1
                logger.info(f"Created: {tool_data['tool_key']}")
        
        await db.commit()
        
        logger.info(f"\n✅ Seeding complete: {created_count} created, {updated_count} updated")


if __name__ == "__main__":
    asyncio.run(seed_dimension_tools())
