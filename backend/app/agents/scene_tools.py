"""Scene tool handlers for VividAgent."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.agents.agent_types import (
    ToolCall,
    ToolContext,
    ToolRegistry,
    ToolResult,
    ToolSpec,
    ToolTaskState,
)
from app.config import settings

SCENE_STORE_KEY = "scenes"
DEFAULT_VIDEO_PROVIDER = "veo-3.1"
DEFAULT_IMAGE_MODEL = settings.GEMINI_IMAGE_MODEL


def register_scene_tools(registry: ToolRegistry) -> None:
    registry.register(
        ToolSpec(
            name="create_scene",
            description="Create a new scene draft and return its snapshot.",
            input_schema={
                "type": "object",
                "properties": {
                    "scene_id": {"type": "string"},
                    "title": {"type": "string"},
                    "summary": {"type": "string"},
                    "style": {"type": "object"},
                },
                "required": ["title", "summary"],
            },
            output_schema={
                "type": "object",
                "properties": {
                    "scene_id": {"type": "string"},
                    "title": {"type": "string"},
                    "summary": {"type": "string"},
                    "style": {"type": "object"},
                    "created_at": {"type": "string"},
                },
            },
        ),
        _create_scene,
    )
    registry.register(
        ToolSpec(
            name="modify_scene",
            description="Modify fields of an existing scene draft.",
            input_schema={
                "type": "object",
                "properties": {
                    "scene_id": {"type": "string"},
                    "patch": {"type": "object"},
                },
                "required": ["scene_id", "patch"],
            },
        ),
        _modify_scene,
    )
    registry.register(
        ToolSpec(
            name="split_scene",
            description="Split a scene into multiple drafts.",
            input_schema={
                "type": "object",
                "properties": {
                    "scene_id": {"type": "string"},
                    "parts": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "summary": {"type": "string"},
                            },
                            "required": ["summary"],
                        },
                    },
                },
                "required": ["scene_id", "parts"],
            },
        ),
        _split_scene,
    )
    registry.register(
        ToolSpec(
            name="merge_scenes",
            description="Merge multiple scenes into a new draft.",
            input_schema={
                "type": "object",
                "properties": {
                    "scene_ids": {"type": "array", "items": {"type": "string"}},
                    "title": {"type": "string"},
                    "summary": {"type": "string"},
                },
                "required": ["scene_ids"],
            },
        ),
        _merge_scenes,
    )
    registry.register(
        ToolSpec(
            name="apply_style",
            description="Apply a style override to a scene.",
            input_schema={
                "type": "object",
                "properties": {
                    "scene_id": {"type": "string"},
                    "style": {"type": "object"},
                },
                "required": ["scene_id", "style"],
            },
        ),
        _apply_style,
    )
    registry.register(
        ToolSpec(
            name="generate_video",
            description="Start a video generation task for a scene.",
            input_schema={
                "type": "object",
                "properties": {
                    "scene_id": {"type": "string"},
                    "provider": {"type": "string"},
                    "quality": {"type": "string"},
                    "length_sec": {"type": "number"},
                },
                "required": ["scene_id"],
            },
        ),
        _generate_video,
    )
    registry.register(
        ToolSpec(
            name="generate_image",
            description="Start an image generation task for a scene.",
            input_schema={
                "type": "object",
                "properties": {
                    "scene_id": {"type": "string"},
                    "prompt": {"type": "string"},
                    "model": {"type": "string"},
                    "aspect_ratio": {"type": "string"},
                    "size": {"type": "string"},
                },
                "required": ["scene_id"],
            },
        ),
        _generate_image,
    )


def _scene_store(context: ToolContext) -> Dict[str, Dict[str, Any]]:
    return context.state.artifacts.setdefault(SCENE_STORE_KEY, {})


def _build_scene_id(scene_id: Optional[str]) -> str:
    return scene_id or f"scene_{uuid4().hex[:8]}"


async def _create_scene(context: ToolContext, call: ToolCall) -> ToolResult:
    args = call.arguments or {}
    title = (args.get("title") or "").strip()
    summary = (args.get("summary") or "").strip()
    if not title or not summary:
        return ToolResult(
            tool_call_id=call.id,
            name=call.name,
            status=ToolTaskState.FAILED,
            error="title and summary are required",
        )
    scene_id_input = (args.get("scene_id") or "").strip()
    scene_id = _build_scene_id(scene_id_input or None)
    style = args.get("style") or {}
    scene = {
        "scene_id": scene_id,
        "title": title,
        "summary": summary,
        "style": style,
        "created_at": f"{datetime.utcnow().isoformat()}Z",
    }
    store = _scene_store(context)
    store[scene_id] = scene
    return ToolResult(
        tool_call_id=call.id,
        name=call.name,
        output=scene,
    )


def _merge_dict(base: Dict[str, Any], patch: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(base)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = {**merged[key], **value}
        else:
            merged[key] = value
    return merged


async def _modify_scene(context: ToolContext, call: ToolCall) -> ToolResult:
    args = call.arguments or {}
    scene_id = (args.get("scene_id") or "").strip()
    patch = args.get("patch") or {}
    if not scene_id or not isinstance(patch, dict):
        return ToolResult(
            tool_call_id=call.id,
            name=call.name,
            status=ToolTaskState.FAILED,
            error="scene_id and patch are required",
        )
    store = _scene_store(context)
    scene = store.get(scene_id)
    if not scene:
        return ToolResult(
            tool_call_id=call.id,
            name=call.name,
            status=ToolTaskState.FAILED,
            error=f"scene_id not found: {scene_id}",
        )
    scene = _merge_dict(scene, patch)
    scene["updated_at"] = f"{datetime.utcnow().isoformat()}Z"
    store[scene_id] = scene
    return ToolResult(
        tool_call_id=call.id,
        name=call.name,
        output=scene,
    )


async def _split_scene(context: ToolContext, call: ToolCall) -> ToolResult:
    args = call.arguments or {}
    scene_id = (args.get("scene_id") or "").strip()
    parts = args.get("parts") or []
    if not scene_id or not isinstance(parts, list) or not parts:
        return ToolResult(
            tool_call_id=call.id,
            name=call.name,
            status=ToolTaskState.FAILED,
            error="scene_id and parts are required",
        )
    store = _scene_store(context)
    source_scene = store.get(scene_id)
    if not source_scene:
        return ToolResult(
            tool_call_id=call.id,
            name=call.name,
            status=ToolTaskState.FAILED,
            error=f"scene_id not found: {scene_id}",
        )
    created: List[Dict[str, Any]] = []
    for idx, part in enumerate(parts, start=1):
        if not isinstance(part, dict):
            continue
        summary = (part.get("summary") or "").strip()
        if not summary:
            continue
        title = (part.get("title") or f"{source_scene.get('title', 'Scene')} Part {idx}").strip()
        new_id = _build_scene_id(None)
        scene = {
            "scene_id": new_id,
            "title": title,
            "summary": summary,
            "style": source_scene.get("style", {}),
            "split_from": scene_id,
            "created_at": f"{datetime.utcnow().isoformat()}Z",
        }
        store[new_id] = scene
        created.append(scene)
    return ToolResult(
        tool_call_id=call.id,
        name=call.name,
        output={"created": created},
    )


async def _merge_scenes(context: ToolContext, call: ToolCall) -> ToolResult:
    args = call.arguments or {}
    scene_ids = args.get("scene_ids") or []
    if not isinstance(scene_ids, list) or not scene_ids:
        return ToolResult(
            tool_call_id=call.id,
            name=call.name,
            status=ToolTaskState.FAILED,
            error="scene_ids is required",
        )
    store = _scene_store(context)
    scenes = [store.get(scene_id) for scene_id in scene_ids if store.get(scene_id)]
    if not scenes:
        return ToolResult(
            tool_call_id=call.id,
            name=call.name,
            status=ToolTaskState.FAILED,
            error="no valid scene_ids found",
        )
    title = (args.get("title") or "Merged Scene").strip()
    summary = (args.get("summary") or " ".join((scene.get("summary") or "") for scene in scenes)).strip()
    merged_id = _build_scene_id(None)
    scene = {
        "scene_id": merged_id,
        "title": title,
        "summary": summary,
        "style": scenes[0].get("style", {}),
        "merged_from": scene_ids,
        "created_at": f"{datetime.utcnow().isoformat()}Z",
    }
    store[merged_id] = scene
    return ToolResult(
        tool_call_id=call.id,
        name=call.name,
        output=scene,
    )


async def _apply_style(context: ToolContext, call: ToolCall) -> ToolResult:
    args = call.arguments or {}
    scene_id = (args.get("scene_id") or "").strip()
    style = args.get("style") or {}
    if not scene_id or not isinstance(style, dict):
        return ToolResult(
            tool_call_id=call.id,
            name=call.name,
            status=ToolTaskState.FAILED,
            error="scene_id and style are required",
        )
    store = _scene_store(context)
    scene = store.get(scene_id)
    if not scene:
        return ToolResult(
            tool_call_id=call.id,
            name=call.name,
            status=ToolTaskState.FAILED,
            error=f"scene_id not found: {scene_id}",
        )
    scene["style"] = _merge_dict(scene.get("style", {}), style)
    scene["updated_at"] = f"{datetime.utcnow().isoformat()}Z"
    store[scene_id] = scene
    return ToolResult(
        tool_call_id=call.id,
        name=call.name,
        output=scene,
    )


async def _generate_video(context: ToolContext, call: ToolCall) -> ToolResult:
    args = call.arguments or {}
    scene_id = (args.get("scene_id") or "").strip()
    if not scene_id:
        return ToolResult(
            tool_call_id=call.id,
            name=call.name,
            status=ToolTaskState.FAILED,
            error="scene_id is required",
        )
    task_id = f"task_{uuid4().hex[:8]}"
    provider = (args.get("provider") or DEFAULT_VIDEO_PROVIDER).strip()
    return ToolResult(
        tool_call_id=call.id,
        name=call.name,
        status=ToolTaskState.WORKING,
        task_id=task_id,
        output={
            "scene_id": scene_id,
            "provider": provider,
            "quality": args.get("quality"),
            "length_sec": args.get("length_sec"),
            "task_id": task_id,
        },
    )


async def _generate_image(context: ToolContext, call: ToolCall) -> ToolResult:
    args = call.arguments or {}
    scene_id = (args.get("scene_id") or "").strip()
    if not scene_id:
        return ToolResult(
            tool_call_id=call.id,
            name=call.name,
            status=ToolTaskState.FAILED,
            error="scene_id is required",
        )
    task_id = f"task_{uuid4().hex[:8]}"
    model = (args.get("model") or DEFAULT_IMAGE_MODEL).strip()
    return ToolResult(
        tool_call_id=call.id,
        name=call.name,
        status=ToolTaskState.WORKING,
        task_id=task_id,
        output={
            "scene_id": scene_id,
            "prompt": args.get("prompt"),
            "model": model,
            "aspect_ratio": args.get("aspect_ratio"),
            "size": args.get("size"),
            "task_id": task_id,
        },
    )
