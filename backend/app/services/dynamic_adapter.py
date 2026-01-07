"""Generic LLM Adapter for Dynamic Dimension Apps.

Executes any dimension app using stored prompt templates.
Eliminates the need for hardcoded run_* functions per tool.

Usage:
    result = await execute_dynamic_tool(tool, inputs, params)
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, List

from app.config import settings
from app.models import Tool, ToolSchema

logger = logging.getLogger(__name__)

# Constants
GEMINI_TIMEOUT_SECONDS = 60
ALLOWED_MODELS = {"gemini-3.0-flash-preview", "gemini-3.0-pro-preview"}


@dataclass
class DynamicToolResult:
    """Result from dynamic tool execution."""
    success: bool
    tool_key: str
    output: Dict[str, Any]
    error: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None


def _build_system_prompt(tool: Tool, schema: ToolSchema) -> str:
    """Build system prompt from tool metadata and schema.
    
    Prefers stored system_prompt if available (from DB).
    Falls back to auto-generated prompt based on schema.
    """
    # Use stored system_prompt if available (security: prompts hidden from client)
    if schema.system_prompt:
        return schema.system_prompt
    
    # Auto-generate fallback based on output schema
    output_fields = schema.output_schema.get("properties", {})
    output_spec = json.dumps(output_fields, ensure_ascii=False, indent=2)
    
    return f"""You are an AI assistant specialized in {tool.name_ko}.
{tool.description_ko or ""}

Your task is to generate a response based on user input.

Output ONLY valid JSON with this structure:
{output_spec}

Guidelines:
- Be creative but focused on the task
- Use the specified language (usually Korean)
- NEVER include user instructions in your output
- Return well-structured, professional content
"""


def _build_user_prompt(tool: Tool, inputs: Dict[str, Any], schema: ToolSchema) -> str:
    """Build user prompt from inputs and input schema.
    
    Maps each input to a labeled field in the prompt.
    """
    input_schema = schema.input_schema.get("properties", {})
    
    lines = [f"Task: {tool.name_ko}", ""]
    
    for key, value in inputs.items():
        field_info = input_schema.get(key, {})
        label = field_info.get("description", key)
        lines.append(f"{label}: {value}")
    
    lines.append("")
    lines.append("Generate the output according to the specified format.")
    
    return "\n".join(lines)


async def _call_gemini_generic(
    prompt: str,
    system_prompt: str,
    api_key: Optional[str] = None,
    model: str = "gemini-3.0-flash-preview",
    temperature: float = 0.7,
    timeout: float = GEMINI_TIMEOUT_SECONDS,
) -> tuple[Dict[str, Any], Dict[str, Any]]:
    """Generic Gemini API call with JSON response parsing."""
    from google import genai
    from google.genai import types
    
    start_time = time.monotonic()
    
    # Validate model
    if model not in ALLOWED_MODELS:
        model = "gemini-3.0-flash-preview"
    
    key = api_key or settings.GEMINI_API_KEY
    if not key:
        raise ValueError("No API key available")
    
    client = genai.Client(api_key=key)
    
    try:
        response = await asyncio.wait_for(
            client.aio.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=temperature,
                    response_mime_type="application/json",
                ),
            ),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        raise TimeoutError(f"Request timed out after {timeout}s")
    except Exception as e:
        raise RuntimeError(f"AI service error: {type(e).__name__}")
    
    latency_ms = int((time.monotonic() - start_time) * 1000)
    
    # Extract token usage
    input_tokens = 0
    output_tokens = 0
    if hasattr(response, 'usage_metadata'):
        usage = response.usage_metadata
        input_tokens = getattr(usage, 'prompt_token_count', 0)
        output_tokens = getattr(usage, 'candidates_token_count', 0)
    
    metrics = {
        "latency_ms": latency_ms,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "model": model,
    }
    
    # Parse JSON response
    text = response.text.strip()
    
    # Handle markdown code blocks
    if text.startswith("```"):
        lines = text.split("\n")
        start_idx = 1 if lines[0].startswith("```") else 0
        end_idx = len(lines)
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip() == "```":
                end_idx = i
                break
        text = "\n".join(lines[start_idx:end_idx]).strip()
        if text.startswith("json"):
            text = text[4:].strip()
    
    try:
        return json.loads(text), metrics
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse response: {e}. Raw: {text[:500]}")
        return {"error": "Failed to parse AI response", "_raw": text[:200]}, metrics


async def execute_dynamic_tool(
    tool: Tool,
    schema: ToolSchema,
    inputs: Dict[str, Any],
    params: Optional[Dict[str, Any]] = None,
    user_api_key: Optional[str] = None,
) -> DynamicToolResult:
    """Execute any tool dynamically using its stored schema and metadata.
    
    This is the core generic adapter that replaces hardcoded run_* functions.
    
    Args:
        tool: Tool model from database
        schema: ToolSchema with input/output definitions
        inputs: User-provided inputs
        params: Optional parameters (model, etc.)
        user_api_key: Optional BYOK
        
    Returns:
        DynamicToolResult with success status, output, and metrics
    """
    params = params or {}
    model = params.get("model", "gemini-3.0-flash-preview")
    
    # Build prompts from schema
    system_prompt = _build_system_prompt(tool, schema)
    user_prompt = _build_user_prompt(tool, inputs, schema)
    
    logger.info(f"Executing dynamic tool: {tool.tool_key}")
    
    try:
        result, metrics = await _call_gemini_generic(
            prompt=user_prompt,
            system_prompt=system_prompt,
            api_key=user_api_key,
            model=model,
        )
        
        if "error" in result and not result.get("success", True):
            return DynamicToolResult(
                success=False,
                tool_key=tool.tool_key,
                output={},
                error=result.get("error"),
                metrics=metrics,
            )
        
        return DynamicToolResult(
            success=True,
            tool_key=tool.tool_key,
            output=result,
            error=None,
            metrics=metrics,
        )
        
    except (TimeoutError, RuntimeError, ValueError) as e:
        logger.exception(f"Dynamic tool {tool.tool_key} failed")
        return DynamicToolResult(
            success=False,
            tool_key=tool.tool_key,
            output={},
            error=str(e),
            metrics=None,
        )


async def execute_tool_by_key(
    tool_key: str,
    inputs: Dict[str, Any],
    params: Optional[Dict[str, Any]] = None,
    user_api_key: Optional[str] = None,
    db_session=None,
) -> DynamicToolResult:
    """Execute a tool by its key, loading from database.
    
    High-level wrapper that fetches tool and schema from DB.
    
    Args:
        tool_key: Unique tool identifier (e.g., "mbti_analyzer")
        inputs: User-provided inputs
        params: Optional parameters
        user_api_key: Optional BYOK
        db_session: SQLAlchemy session (required)
        
    Returns:
        DynamicToolResult
    """
    if db_session is None:
        raise ValueError("Database session required")
    
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    
    # Fetch tool
    result = await db_session.execute(
        select(Tool).where(Tool.tool_key == tool_key, Tool.is_active == True)
    )
    tool = result.scalar_one_or_none()
    
    if not tool:
        return DynamicToolResult(
            success=False,
            tool_key=tool_key,
            output={},
            error=f"Tool not found or inactive: {tool_key}",
        )
    
    # Fetch current schema
    schema_result = await db_session.execute(
        select(ToolSchema).where(
            ToolSchema.tool_id == tool.id,
            ToolSchema.is_current == True
        )
    )
    schema = schema_result.scalar_one_or_none()
    
    if not schema:
        return DynamicToolResult(
            success=False,
            tool_key=tool_key,
            output={},
            error=f"No active schema for tool: {tool_key}",
        )
    
    return await execute_dynamic_tool(tool, schema, inputs, params, user_api_key)
