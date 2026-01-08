"""
Tool Registry Module - MCP Compatible Tool Definitions

This module provides a standardized registry of all dimension tools (mini-apps)
following the Model Context Protocol (MCP) patterns for tool discovery and invocation.

References:
- Anthropic MCP: https://modelcontextprotocol.io
- OpenAI Function Calling: https://platform.openai.com/docs/guides/function-calling
"""

from functools import lru_cache
from typing import Any, Dict, List, Optional, Literal, Tuple
from pydantic import BaseModel, Field
from enum import Enum


class DimensionLevel(str, Enum):
    """Dimension levels representing abstraction/complexity."""
    D1_ORIGIN = "1D"      # Text/concept generation
    D2_BLUEPRINT = "2D"   # Structure/planning
    D3_AMBIENCE = "3D"    # Visual/spatial
    D4_MOMENT = "4D"      # Time/motion
    D5_SOUL = "5D"        # Style/personality


class ThemeColor(str, Enum):
    """Theme colors for UI consistency."""
    VIOLET = "violet"
    CYAN = "cyan"
    EMERALD = "emerald"
    AMBER = "amber"
    LIME = "lime"


class ToolDefinition(BaseModel):
    """
    MCP-compatible tool definition schema.
    
    Each tool represents a dimension "mini-app" that can be:
    - Discovered by the agent
    - Invoked programmatically
    - Chained with other tools
    """
    
    # === Identity ===
    tool_id: str = Field(..., description="Unique identifier (snake_case)")
    dimension: DimensionLevel = Field(..., description="Dimension level")
    
    # === Localized Names ===
    name_ko: str = Field(..., description="Korean display name")
    name_en: str = Field(..., description="English display name")
    description_ko: str = Field(..., description="Korean description")
    description_en: str = Field(..., description="English description")
    
    # === Schemas (JSON Schema format) ===
    input_schema: Dict[str, Any] = Field(..., description="Input parameters JSON Schema")
    output_schema: Dict[str, Any] = Field(..., description="Output structure JSON Schema")
    
    # === Execution ===
    endpoint: str = Field(..., description="API endpoint path")
    credit_cost: int = Field(..., ge=0, description="Credit cost per invocation")
    supports_byok: bool = Field(default=True, description="Supports Bring Your Own Key")
    auto_executable: bool = Field(default=True, description="Can be auto-executed by agent")
    
    # === UI ===
    color: ThemeColor = Field(..., description="Theme color")
    icon: str = Field(..., description="Lucide icon name")
    route: str = Field(..., description="Frontend route path")
    
    # === Chaining ===
    can_chain_from: List[str] = Field(default=[], description="Tools that can precede this")
    can_chain_to: List[str] = Field(default=[], description="Tools that can follow this")
    output_mapping: Dict[str, str] = Field(
        default={}, 
        description="Map output fields to next tool's input fields"
    )

    class Config:
        use_enum_values = True


# =============================================================================
# Tool Registry - All Dimension Tools
# =============================================================================

TOOL_REGISTRY: List[ToolDefinition] = [
    # -------------------------------------------------------------------------
    # 1D - ORIGIN: Prompt Generator
    # -------------------------------------------------------------------------
    ToolDefinition(
        tool_id="prompt_generator",
        dimension=DimensionLevel.D1_ORIGIN,
        name_ko="Veo 프롬프트 생성기",
        name_en="Veo Prompt Generator",
        description_ko="주제, 스타일, 분위기를 입력하면 Veo 영상 생성에 최적화된 프롬프트를 생성합니다.",
        description_en="Generate optimized prompts for Veo video generation from topic, style, and mood.",
        input_schema={
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "Video topic or concept",
                    "minLength": 1,
                    "maxLength": 500
                },
                "style": {
                    "type": "string",
                    "enum": ["cinematic", "documentary", "commercial", "artistic", "vlog"],
                    "default": "cinematic"
                },
                "mood": {
                    "type": "string",
                    "enum": ["neutral", "dramatic", "calm", "energetic", "melancholic"],
                    "default": "neutral"
                },
                "duration": {
                    "type": "string",
                    "enum": ["5 seconds", "10 seconds", "15 seconds", "30 seconds", "60 seconds"],
                    "default": "15 seconds"
                },
                "language": {
                    "type": "string",
                    "enum": ["ko", "en"],
                    "default": "ko"
                }
            },
            "required": ["topic"]
        },
        output_schema={
            "type": "object",
            "properties": {
                "prompt": {"type": "string"},
                "negative_prompt": {"type": "string"},
                "style": {
                    "type": "object",
                    "properties": {
                        "cinematography": {"type": "string"},
                        "lighting": {"type": "string"},
                        "color_grade": {"type": "string"}
                    }
                },
                "technical": {
                    "type": "object",
                    "properties": {
                        "aspect_ratio": {"type": "string"},
                        "duration": {"type": "string"},
                        "fps": {"type": "string"}
                    }
                }
            },
            "required": ["prompt"]
        },
        endpoint="/api/dimension/1d/generate",
        credit_cost=5,
        color=ThemeColor.VIOLET,
        icon="Sparkles",
        route="/dimension/prompt",
        can_chain_to=["storyboard_architect", "image_generator"],
        output_mapping={
            "prompt": "concept",  # prompt → storyboard's concept
        }
    ),
    
    # -------------------------------------------------------------------------
    # 2D - BLUEPRINT: Storyboard Architect
    # -------------------------------------------------------------------------
    ToolDefinition(
        tool_id="storyboard_architect",
        dimension=DimensionLevel.D2_BLUEPRINT,
        name_ko="스토리보드 아키텍트",
        name_en="Storyboard Architect",
        description_ko="스토리 개요를 입력하면 장면별 시각적 스토리보드를 생성합니다.",
        description_en="Create scene-by-scene visual storyboards from story concepts.",
        input_schema={
            "type": "object",
            "properties": {
                "script": {
                    "type": "string",
                    "description": "Story script or concept",
                    "minLength": 1,
                    "maxLength": 2000
                },
                "scene_count": {
                    "type": "integer",
                    "enum": [3, 5, 7, 10, 15, 20],
                    "default": 5
                },
                "language": {
                    "type": "string",
                    "enum": ["ko", "en"],
                    "default": "ko"
                }
            },
            "required": ["script"]
        },
        output_schema={
            "type": "object",
            "properties": {
                "scenes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "scene_number": {"type": "integer"},
                            "description": {"type": "string"},
                            "visual_prompt": {"type": "string"},
                            "camera": {"type": "string"},
                            "duration": {"type": "string"},
                            "shot_type": {"type": "string"},
                            "camera_movement": {"type": "string"},
                            "notes": {"type": "string"}
                        }
                    }
                }
            },
            "required": ["scenes"]
        },
        endpoint="/api/dimension/2d/create",
        credit_cost=10,
        color=ThemeColor.EMERALD,
        icon="LayoutGrid",
        route="/dimension/storyboard",
        can_chain_from=["prompt_generator"],
        can_chain_to=["image_generator"],
        output_mapping={
            "scenes[0].visual_prompt": "description",  # First scene → image description
        }
    ),
    
    # -------------------------------------------------------------------------
    # 3D - AMBIENCE: Image Generator
    # -------------------------------------------------------------------------
    ToolDefinition(
        tool_id="image_generator",
        dimension=DimensionLevel.D3_AMBIENCE,
        name_ko="비주얼 스튜디오",
        name_en="Visual Studio",
        description_ko="설명을 입력하면 이미지 생성에 최적화된 프롬프트를 생성합니다.",
        description_en="Generate optimized image prompts from descriptions.",
        input_schema={
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "Image description",
                    "minLength": 1,
                    "maxLength": 1000
                },
                "style": {
                    "type": "string",
                    "default": "photorealistic"
                },
                "aspect_ratio": {
                    "type": "string",
                    "enum": ["1:1", "16:9", "9:16", "4:3", "3:4"],
                    "default": "16:9"
                }
            },
            "required": ["description"]
        },
        output_schema={
            "type": "object",
            "properties": {
                "image_prompt": {"type": "string"},
                "negative_prompt": {"type": "string"},
                "style_tags": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["image_prompt"]
        },
        endpoint="/api/dimension/3d/generate",
        credit_cost=5,
        color=ThemeColor.AMBER,
        icon="Image",
        route="/dimension/image-tool",
        can_chain_from=["prompt_generator", "storyboard_architect"],
        can_chain_to=["reference_analyzer"],
        output_mapping={}
    ),
    
    # -------------------------------------------------------------------------
    # 4D - MOMENT: Reference Analyzer / Frame Catcher
    # -------------------------------------------------------------------------
    ToolDefinition(
        tool_id="reference_analyzer",
        dimension=DimensionLevel.D4_MOMENT,
        name_ko="프레임 캐쳐",
        name_en="Frame Catcher",
        description_ko="영상 설명을 분석하여 구도, 조명, 색감 등의 레퍼런스 분석 결과를 제공합니다.",
        description_en="Analyze video descriptions for composition, lighting, and color references.",
        input_schema={
            "type": "object",
            "properties": {
                "video_description": {
                    "type": "string",
                    "description": "Video or scene description to analyze",
                    "minLength": 1,
                    "maxLength": 2000
                },
                "focus_areas": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["composition", "lighting", "color", "movement", "framing"]
                    },
                    "default": ["composition", "lighting", "color", "movement"]
                }
            },
            "required": ["video_description"]
        },
        output_schema={
            "type": "object",
            "properties": {
                "analysis": {
                    "type": "object",
                    "properties": {
                        "composition": {"type": "string"},
                        "lighting": {"type": "string"},
                        "color": {"type": "string"},
                        "movement": {"type": "string"}
                    }
                },
                "recommendations": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        },
        endpoint="/api/dimension/4d/analyze",
        credit_cost=8,
        color=ThemeColor.CYAN,
        icon="Eye",
        route="/dimension/shot-catch",
        can_chain_from=["image_generator", "storyboard_architect"],
        can_chain_to=[],
        output_mapping={}
    ),
]


# =============================================================================
# Registry Access Functions
# =============================================================================

def get_tool_by_id(tool_id: str) -> Optional[ToolDefinition]:
    """Get a tool definition by its ID."""
    for tool in TOOL_REGISTRY:
        if tool.tool_id == tool_id:
            return tool
    return None


def get_tools_by_dimension(dimension: DimensionLevel) -> List[ToolDefinition]:
    """Get all tools in a specific dimension."""
    return [t for t in TOOL_REGISTRY if t.dimension == dimension]


def get_chainable_tools(from_tool_id: str) -> List[ToolDefinition]:
    """Get tools that can be chained after a specific tool."""
    tool = get_tool_by_id(from_tool_id)
    if not tool:
        return []
    return [get_tool_by_id(tid) for tid in tool.can_chain_to if get_tool_by_id(tid)]


def get_all_tools_for_agent() -> List[Dict[str, Any]]:
    """
    Get all tools in a format suitable for LLM function calling.
    Compatible with OpenAI/Gemini function calling schema.
    """
    return [
        {
            "name": tool.tool_id,
            "description": tool.description_en,
            "parameters": tool.input_schema
        }
        for tool in TOOL_REGISTRY
    ]


def get_tool_registry_summary() -> List[Dict[str, Any]]:
    """Get a summary of all tools for display purposes."""
    return [
        {
            "tool_id": tool.tool_id,
            "dimension": tool.dimension,
            "name_ko": tool.name_ko,
            "name_en": tool.name_en,
            "credit_cost": tool.credit_cost,
            "color": tool.color,
            "icon": tool.icon,
            "route": tool.route,
        }
        for tool in TOOL_REGISTRY
    ]
