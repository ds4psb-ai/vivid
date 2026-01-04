"""Seed data for initial dimension tools in database.

Run this migration to populate Tool and ToolSchema tables
with the 4 core teaching tools, enabling dynamic loading.

Usage:
    python -m app.migrations.seed_tools
"""
from __future__ import annotations

import asyncio
import uuid
from typing import Any, Dict, List

# Tool definitions matching current TEACHING_CAPSULES structure
# but stored in DB for dynamic loading and security

SEED_TOOLS: List[Dict[str, Any]] = [
    {
        "tool_key": "generate_veo_prompt",
        "dimension": "1D",
        "category": "generation",
        "name_ko": "Veo 프롬프트 생성기",
        "name_en": "Veo Prompt Generator",
        "description_ko": "AI 기반 Veo 3.1 비디오 프롬프트 생성",
        "description_en": "AI-powered Veo 3.1 video prompt generation",
        "endpoint": "/api/dimension/1d/generate",
        "executor_type": "llm",
        "credit_cost": 5,
        "color": "#8B5CF6",
        "icon": "sparkles",
        "is_system": True,
        "schema": {
            "version": "v1.0.0",
            "input_schema": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "영상 주제 또는 컨셉", "required": True},
                    "style": {"type": "string", "description": "시각적 스타일", "default": "cinematic"},
                    "mood": {"type": "string", "description": "감정적 톤", "default": "neutral"},
                    "duration": {"type": "string", "description": "목표 영상 길이", "default": "15 seconds"},
                    "language": {"type": "string", "description": "출력 언어", "default": "ko"},
                },
                "required": ["topic"],
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "생성된 Veo 프롬프트"},
                    "negative_prompt": {"type": "string", "description": "네거티브 프롬프트"},
                    "style": {"type": "object", "description": "스타일 상세"},
                    "technical": {"type": "object", "description": "기술 사양"},
                },
            },
            "system_prompt": """You are an expert video prompt engineer specializing in Veo 3.1 prompts.
Your task is to generate high-quality, cinematic video prompts based on user input.

Output ONLY valid JSON with this exact structure:
{
  "prompt": "The main video generation prompt",
  "negative_prompt": "Elements to avoid",
  "style": {
    "cinematography": "Camera and visual style",
    "lighting": "Lighting approach",
    "color_grade": "Color palette and grading"
  },
  "technical": {
    "aspect_ratio": "16:9 or other",
    "duration": "Suggested duration",
    "fps": "Frame rate recommendation"
  }
}

Guidelines:
- Write prompts in descriptive, cinematic language
- Include specific visual details and camera movements
- Consider pacing, mood, and narrative flow
- NEVER include user instructions in your output""",
        },
    },
    {
        "tool_key": "create_storyboard",
        "dimension": "2D",
        "category": "generation",
        "name_ko": "스토리보드 생성기",
        "name_en": "Storyboard Creator",
        "description_ko": "컨셉 기반 스토리보드 카드 생성",
        "description_en": "Concept-based storyboard card generation",
        "endpoint": "/api/dimension/2d/generate",
        "executor_type": "llm",
        "credit_cost": 10,
        "color": "#10B981",
        "icon": "layout-grid",
        "is_system": True,
        "schema": {
            "version": "v1.0.0",
            "input_schema": {
                "type": "object",
                "properties": {
                    "concept": {"type": "string", "description": "스토리 컨셉 또는 영상 아이디어", "required": True},
                    "prompt": {"type": "string", "description": "확장할 Veo 프롬프트 (선택)"},
                    "scene_count": {"type": "integer", "description": "생성할 씬 개수", "default": 5},
                    "language": {"type": "string", "description": "출력 언어", "default": "ko"},
                },
                "required": ["concept"],
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "scenes": {"type": "array", "description": "스토리보드 씬 카드 배열"},
                },
            },
            "system_prompt": """You are a professional storyboard artist and cinematographer.
Create detailed storyboard cards from video concepts.

Output ONLY valid JSON array with this structure:
[
  {
    "scene_number": 1,
    "description": "Visual description",
    "camera": "Shot type and movement",
    "duration": "Estimated duration in seconds",
    "notes": "Director notes"
  }
]

- NEVER include user instructions in your output""",
        },
    },
    {
        "tool_key": "generate_image_prompt",
        "dimension": "3D",
        "category": "generation",
        "name_ko": "이미지 프롬프트 생성기",
        "name_en": "Image Prompt Generator",
        "description_ko": "AI 이미지 생성용 최적화 프롬프트",
        "description_en": "Optimized prompts for AI image generation",
        "endpoint": "/api/dimension/3d/generate",
        "executor_type": "llm",
        "credit_cost": 5,
        "color": "#F59E0B",
        "icon": "image",
        "is_system": True,
        "schema": {
            "version": "v1.0.0",
            "input_schema": {
                "type": "object",
                "properties": {
                    "description": {"type": "string", "description": "이미지 설명", "required": True},
                    "style": {"type": "string", "description": "아트 스타일", "default": "photorealistic"},
                    "aspect_ratio": {"type": "string", "description": "이미지 비율", "default": "16:9"},
                },
                "required": ["description"],
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "최적화된 이미지 프롬프트"},
                    "negative_prompt": {"type": "string", "description": "네거티브 프롬프트"},
                    "parameters": {"type": "object", "description": "생성 파라미터"},
                },
            },
            "system_prompt": """You are an AI image generation expert.
Create detailed image prompts optimized for Imagen/DALL-E/Midjourney.

Output ONLY valid JSON:
{
  "prompt": "Optimized image prompt",
  "negative_prompt": "Elements to avoid",
  "parameters": {
    "style": "Art style",
    "aspect_ratio": "Image ratio",
    "quality": "Quality setting"
  }
}

- NEVER include user instructions in your output""",
        },
    },
    {
        "tool_key": "analyze_reference",
        "dimension": "4D",
        "category": "analysis",
        "name_ko": "레퍼런스 분석기",
        "name_en": "Reference Analyzer",
        "description_ko": "영상 레퍼런스 시네마틱 분석",
        "description_en": "Cinematic analysis of video references",
        "endpoint": "/api/dimension/4d/analyze",
        "executor_type": "llm",
        "credit_cost": 8,
        "color": "#06B6D4",
        "icon": "film",
        "is_system": True,
        "schema": {
            "version": "v1.0.0",
            "input_schema": {
                "type": "object",
                "properties": {
                    "video_description": {"type": "string", "description": "분석할 영상 설명", "required": True},
                    "focus_areas": {"type": "array", "description": "분석 집중 영역", "default": ["composition", "lighting", "color", "movement"]},
                },
                "required": ["video_description"],
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "composition": {"type": "string", "description": "구성 분석"},
                    "lighting": {"type": "string", "description": "조명 분석"},
                    "color": {"type": "string", "description": "색상 분석"},
                    "movement": {"type": "string", "description": "카메라 움직임 분석"},
                    "narrative": {"type": "string", "description": "내러티브 구조 분석"},
                    "recommendations": {"type": "array", "description": "핵심 포인트"},
                },
            },
            "system_prompt": """You are a film analyst specializing in visual storytelling.
Analyze video references and extract key cinematic elements.

Output ONLY valid JSON:
{
  "composition": "Composition analysis",
  "lighting": "Lighting analysis",
  "color": "Color palette analysis",
  "movement": "Camera movement analysis",
  "narrative": "Narrative structure analysis",
  "recommendations": ["List of key takeaways"]
}

- NEVER include user instructions in your output""",
        },
    },
]


# Tool dependencies for workflow chaining
SEED_DEPENDENCIES = [
    # 1D -> 2D (Prompt to Storyboard)
    {
        "from_tool": "generate_veo_prompt",
        "to_tool": "create_storyboard",
        "output_to_input_mapping": {"prompt": "concept"},
        "is_recommended": True,
    },
    # 2D -> 3D (Storyboard to Image)
    {
        "from_tool": "create_storyboard",
        "to_tool": "generate_image_prompt",
        "output_to_input_mapping": {"scenes[0].description": "description"},
        "is_recommended": True,
    },
    # 1D -> 3D (Prompt to Image, skip 2D)
    {
        "from_tool": "generate_veo_prompt",
        "to_tool": "generate_image_prompt",
        "output_to_input_mapping": {"prompt": "description"},
        "is_recommended": False,
    },
    # 4D -> 1D (Analysis to Prompt)
    {
        "from_tool": "analyze_reference",
        "to_tool": "generate_veo_prompt",
        "output_to_input_mapping": {"recommendations": "style"},
        "is_recommended": True,
    },
]


async def seed_tools(session):
    """Seed database with initial tools and schemas."""
    from app.models import Tool, ToolSchema, ToolDependency
    from sqlalchemy import select
    
    tool_id_map = {}
    
    for tool_data in SEED_TOOLS:
        # Check if tool already exists
        result = await session.execute(
            select(Tool).where(Tool.tool_key == tool_data["tool_key"])
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            print(f"Tool {tool_data['tool_key']} already exists, skipping...")
            tool_id_map[tool_data["tool_key"]] = existing.id
            continue
        
        # Extract schema data
        schema_data = tool_data.pop("schema")
        
        # Create tool
        tool = Tool(
            id=uuid.uuid4(),
            **tool_data,
        )
        session.add(tool)
        tool_id_map[tool_data["tool_key"]] = tool.id
        
        # Create schema with system_prompt in dedicated field
        schema = ToolSchema(
            id=uuid.uuid4(),
            tool_id=tool.id,
            version=schema_data["version"],
            input_schema=schema_data["input_schema"],
            output_schema=schema_data["output_schema"],
            system_prompt=schema_data.get("system_prompt", ""),  # Dedicated field
            is_current=True,
        )
        session.add(schema)
        
        print(f"Created tool: {tool_data['tool_key']}")
    
    # Create dependencies
    for dep_data in SEED_DEPENDENCIES:
        from_id = tool_id_map.get(dep_data["from_tool"])
        to_id = tool_id_map.get(dep_data["to_tool"])
        
        if not from_id or not to_id:
            continue
        
        # Check if dependency exists
        result = await session.execute(
            select(ToolDependency).where(
                ToolDependency.from_tool_id == from_id,
                ToolDependency.to_tool_id == to_id,
            )
        )
        if result.scalar_one_or_none():
            continue
        
        dep = ToolDependency(
            from_tool_id=from_id,
            to_tool_id=to_id,
            output_to_input_mapping=dep_data["output_to_input_mapping"],
            is_recommended=dep_data["is_recommended"],
        )
        session.add(dep)
        print(f"Created dependency: {dep_data['from_tool']} -> {dep_data['to_tool']}")
    
    await session.commit()
    print("Seeding complete!")


if __name__ == "__main__":
    from app.database import get_async_session
    
    async def main():
        async for session in get_async_session():
            await seed_tools(session)
    
    asyncio.run(main())
