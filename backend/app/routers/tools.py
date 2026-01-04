"""
Tool Registry API Router

Provides endpoints for tool discovery and metadata.
Used by the Chokki agent and frontend for dynamic tool loading.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.registry import (
    TOOL_REGISTRY,
    get_tool_by_id,
    get_tools_by_dimension,
    get_chainable_tools,
    get_all_tools_for_agent,
    get_tool_registry_summary,
    DimensionLevel,
)

router = APIRouter(prefix="/api/v1/tools", tags=["tools"])


# =============================================================================
# Response Models
# =============================================================================

class ToolSummary(BaseModel):
    """Summary of a tool for list views."""
    tool_id: str
    dimension: str
    name_ko: str
    name_en: str
    credit_cost: int
    color: str
    icon: str
    route: str


class ToolDetail(BaseModel):
    """Full tool details."""
    tool_id: str
    dimension: str
    name_ko: str
    name_en: str
    description_ko: str
    description_en: str
    input_schema: dict
    output_schema: dict
    endpoint: str
    credit_cost: int
    supports_byok: bool
    auto_executable: bool
    color: str
    icon: str
    route: str
    can_chain_from: List[str]
    can_chain_to: List[str]
    output_mapping: dict


class ChainableToolsResponse(BaseModel):
    """Response for chainable tools query."""
    from_tool_id: str
    chainable_tools: List[ToolSummary]


class AgentToolsResponse(BaseModel):
    """Tools formatted for LLM function calling."""
    tools: List[dict]


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/", response_model=List[ToolSummary])
async def list_tools():
    """
    List all available dimension tools.
    
    Returns a summary of each tool suitable for display.
    """
    return get_tool_registry_summary()


@router.get("/for-agent", response_model=AgentToolsResponse)
async def get_tools_for_agent():
    """
    Get tools formatted for LLM function calling.
    
    Returns tools in OpenAI/Gemini function calling schema format.
    """
    return AgentToolsResponse(tools=get_all_tools_for_agent())


@router.get("/dimension/{dimension}", response_model=List[ToolSummary])
async def list_tools_by_dimension(dimension: str):
    """
    List tools in a specific dimension.
    
    Args:
        dimension: Dimension level (1D, 2D, 3D, 4D, 5D)
    """
    try:
        dim_level = DimensionLevel(dimension)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid dimension: {dimension}. Valid values: 1D, 2D, 3D, 4D, 5D"
        )
    
    tools = get_tools_by_dimension(dim_level)
    return [
        ToolSummary(
            tool_id=t.tool_id,
            dimension=t.dimension,
            name_ko=t.name_ko,
            name_en=t.name_en,
            credit_cost=t.credit_cost,
            color=t.color,
            icon=t.icon,
            route=t.route,
        )
        for t in tools
    ]


@router.get("/{tool_id}", response_model=ToolDetail)
async def get_tool(tool_id: str):
    """
    Get detailed information about a specific tool.
    
    Args:
        tool_id: The tool's unique identifier
    """
    tool = get_tool_by_id(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_id}")
    
    return ToolDetail(
        tool_id=tool.tool_id,
        dimension=tool.dimension,
        name_ko=tool.name_ko,
        name_en=tool.name_en,
        description_ko=tool.description_ko,
        description_en=tool.description_en,
        input_schema=tool.input_schema,
        output_schema=tool.output_schema,
        endpoint=tool.endpoint,
        credit_cost=tool.credit_cost,
        supports_byok=tool.supports_byok,
        auto_executable=tool.auto_executable,
        color=tool.color,
        icon=tool.icon,
        route=tool.route,
        can_chain_from=tool.can_chain_from,
        can_chain_to=tool.can_chain_to,
        output_mapping=tool.output_mapping,
    )


@router.get("/{tool_id}/chainable", response_model=ChainableToolsResponse)
async def get_chainable(tool_id: str):
    """
    Get tools that can be chained after a specific tool.
    
    Args:
        tool_id: The source tool's unique identifier
    """
    tool = get_tool_by_id(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_id}")
    
    chainable = get_chainable_tools(tool_id)
    return ChainableToolsResponse(
        from_tool_id=tool_id,
        chainable_tools=[
            ToolSummary(
                tool_id=t.tool_id,
                dimension=t.dimension,
                name_ko=t.name_ko,
                name_en=t.name_en,
                credit_cost=t.credit_cost,
                color=t.color,
                icon=t.icon,
                route=t.route,
            )
            for t in chainable if t
        ]
    )
