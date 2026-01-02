#!/usr/bin/env python3
"""Seed Tool Versions with Actual Code.

Creates ToolVersion records for existing tools with their actual
prompt templates/code content. This makes Fork system fully functional.

Run: python -m backend.scripts.seed_tool_versions
"""
import asyncio
import sys
from datetime import datetime
from pathlib import Path
from uuid import uuid4

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models_telemetry import ToolManifest
from app.models_versioning import ToolVersion, VersionStatus, CodeType


# =============================================================================
# Actual Tool Prompts/Code
# =============================================================================

TOOL_CODE_CONTENT = {
    "teaching_prompt_generate": {
        "code_type": CodeType.PROMPT_TEMPLATE.value,
        "system_prompt": """You are an expert video prompt engineer specializing in Veo 3.1.
Create cinematic, detailed prompts that capture the essence of the topic with rich visual language.""",
        "code_content": """# Veo 프롬프트 생성기 v1.0

## 입력 변수
- {{topic}}: 영상 주제
- {{style}}: 시각적 스타일 (default: cinematic)
- {{mood}}: 감정적 톤 (default: neutral)
- {{duration}}: 목표 길이 (default: 15 seconds)
- {{language}}: 출력 언어 (ko/en)

## 프롬프트 템플릿

Create a Veo 3.1 video prompt for the following concept:

**Topic:** {{topic}}
**Style:** {{style}}
**Mood:** {{mood}}
**Duration:** {{duration}}

Generate a detailed video prompt with:
1. Opening shot description
2. Main action/subject
3. Camera movement (dolly, pan, crane, etc.)
4. Lighting setup (natural, dramatic, soft, etc.)
5. Color grading reference
6. Closing shot

Output Format:
{
  "prompt": "<detailed veo prompt>",
  "negative_prompt": "<what to avoid>",
  "style": {
    "cinematography": "<camera style>",
    "lighting": "<lighting style>",
    "color_grade": "<color reference>"
  },
  "technical": {
    "aspect_ratio": "16:9",
    "duration": "{{duration}}",
    "fps": 24
  }
}
""",
    },
    
    "teaching_storyboard_create": {
        "code_type": CodeType.PROMPT_TEMPLATE.value,
        "system_prompt": """You are a professional storyboard artist and film director.
Create compelling visual sequences with clear shot descriptions.""",
        "code_content": """# 스토리보드 생성기 v1.0

## 입력 변수
- {{concept}}: 스토리 컨셉
- {{prompt}}: Veo 프롬프트 (선택)
- {{scene_count}}: 씬 개수 (default: 5)
- {{language}}: 출력 언어

## 프롬프트 템플릿

Create a {{scene_count}}-scene storyboard for:

**Concept:** {{concept}}
{% if prompt %}**Base Prompt:** {{prompt}}{% endif %}

For each scene, provide:
1. Scene number
2. Shot type (wide, medium, close-up, etc.)
3. Visual description
4. Camera movement
5. Duration (in seconds)
6. Key action/emotion
7. Audio notes (ambient, music, dialogue)

Output Format:
{
  "scenes": [
    {
      "scene_number": 1,
      "shot_type": "<shot type>",
      "description": "<visual description>",
      "camera": "<camera movement>",
      "duration_seconds": 3,
      "action": "<key action>",
      "audio": "<audio notes>",
      "veo_prompt": "<individual scene prompt>"
    }
  ]
}
""",
    },
    
    "teaching_image_generate": {
        "code_type": CodeType.PROMPT_TEMPLATE.value,
        "system_prompt": """You are an expert AI image prompt engineer.
Create detailed prompts optimized for Imagen 3 and similar models.""",
        "code_content": """# 이미지 프롬프트 생성기 v1.0

## 입력 변수
- {{description}}: 이미지 설명
- {{style}}: 아트 스타일 (default: photorealistic)
- {{aspect_ratio}}: 비율 (default: 16:9)

## 프롬프트 템플릿

Generate an optimized AI image prompt for:

**Description:** {{description}}
**Style:** {{style}}
**Aspect Ratio:** {{aspect_ratio}}

Create a detailed prompt including:
1. Subject description with specific details
2. Environment/background
3. Lighting conditions
4. Art style references
5. Technical quality markers (8k, detailed, etc.)
6. Negative prompts to avoid common issues

Output Format:
{
  "prompt": "<optimized image prompt>",
  "parameters": {
    "style": "{{style}}",
    "aspect_ratio": "{{aspect_ratio}}",
    "quality": "hd",
    "cfg_scale": 7.5
  },
  "tags": ["tag1", "tag2"],
  "negative": "<what to avoid>"
}
""",
    },
    
    "teaching_reference_analyze": {
        "code_type": CodeType.PROMPT_TEMPLATE.value,
        "system_prompt": """You are a cinematographer and film analyst.
Analyze videos for their visual techniques and provide actionable insights.""",
        "code_content": """# 레퍼런스 분석기 v1.0

## 입력 변수
- {{video_description}}: 분석할 영상 설명
- {{focus_areas}}: 분석 영역 (composition, lighting, color, movement)

## 프롬프트 템플릿

Analyze the following video reference:

**Video Description:** {{video_description}}
**Focus Areas:** {{focus_areas}}

Provide detailed analysis on:

1. **Composition**
   - Rule of thirds usage
   - Leading lines
   - Framing techniques
   - Depth layers

2. **Lighting**
   - Key light direction
   - Fill ratio
   - Rim/accent lights
   - Practical lights
   - Time of day simulation

3. **Color**
   - Color palette (3-5 main colors)
   - Color temperature
   - Saturation levels
   - Contrast type (high/low/mid)
   - LUT/grade reference

4. **Movement**
   - Camera movement type
   - Speed and rhythm
   - Subject movement
   - Transitions

Output Format:
{
  "analysis": {
    "composition": {...},
    "lighting": {...},
    "color": {...},
    "movement": {...}
  },
  "recommendations": [...],
  "similar_references": [...]
}
""",
    },
}


async def seed_tool_versions():
    """Create ToolVersion records for existing tools."""
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        # Get all tools
        result = await db.execute(select(ToolManifest))
        tools = result.scalars().all()
        
        print(f"Found {len(tools)} tools in database")
        
        created = 0
        skipped = 0
        
        for tool in tools:
            # Check if version exists
            existing = await db.execute(
                select(ToolVersion)
                .where(ToolVersion.tool_id == tool.id)
                .where(ToolVersion.is_live == True)
            )
            if existing.scalars().first():
                print(f"  ⏭️  {tool.tool_key}: Already has live version")
                skipped += 1
                continue
            
            # Get code content
            code_data = TOOL_CODE_CONTENT.get(tool.tool_key)
            
            if not code_data:
                # Create placeholder version
                code_data = {
                    "code_type": CodeType.PROMPT_TEMPLATE.value,
                    "system_prompt": f"You are an AI assistant for {tool.display_name}.",
                    "code_content": f"# {tool.display_name}\n\n## Description\n{tool.description or 'No description'}\n\n## Input Schema\n{tool.input_schema}\n\n## Output Schema\n{tool.output_schema}",
                }
            
            version = ToolVersion(
                id=uuid4(),
                tool_id=tool.id,
                version="1.0.0",
                version_number=1,
                code_type=code_data["code_type"],
                code_content=code_data["code_content"],
                system_prompt=code_data.get("system_prompt"),
                input_schema=tool.input_schema,
                output_schema=tool.output_schema,
                dependencies={},
                config={"timeout_seconds": 30, "max_tokens": 4000},
                status=VersionStatus.APPROVED.value,
                is_live=True,
                created_by=tool.created_by or "system",
                reviewed_by="system",
                reviewed_at=datetime.utcnow(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                changelog="Initial version created from fixture",
            )
            
            db.add(version)
            created += 1
            print(f"  ✅ {tool.tool_key}: Created v1.0.0")
        
        await db.commit()
        print(f"\n✅ Done! Created {created} versions, skipped {skipped}")


if __name__ == "__main__":
    asyncio.run(seed_tool_versions())
