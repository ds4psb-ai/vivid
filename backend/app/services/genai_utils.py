"""Shared utilities for Google GenAI client usage."""
from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

from app.config import settings


def get_genai_client(api_key: Optional[str] = None):
    """Return google.genai client.

    Lazily imports the library to avoid import errors when not needed.

    H1.3: Uses SecretStr.get_secret_value() for API key security.
    """
    try:
        from google import genai  # type: ignore
    except Exception as exc:  # pragma: no cover - handled in tests via mocks
        raise ImportError("google-genai is not installed") from exc

    # H1.3: Use get_secret_value() for SecretStr
    key = api_key or settings.GEMINI_API_KEY.get_secret_value()
    if not key:
        raise ValueError("GEMINI_API_KEY not set")
    return genai.Client(api_key=key)


def with_model_prefix(model_name: str) -> str:
    """Ensure model name has 'models/' prefix for google-genai APIs."""
    if model_name.startswith("models/"):
        return model_name
    return f"models/{model_name}"


def normalize_model_name(model_name: str) -> str:
    """Strip 'models/' prefix if present."""
    if model_name.startswith("models/"):
        return model_name[len("models/") :]
    return model_name


def build_generate_config(
    base_config: Optional[Dict[str, Any]] = None,
    *,
    system_instruction: Optional[str] = None,
    response_schema: Optional[Any] = None,
) -> Dict[str, Any]:
    """Build generation config dict for google-genai calls."""
    config: Dict[str, Any] = dict(base_config or {})
    if system_instruction:
        config["system_instruction"] = system_instruction
    if response_schema is not None:
        config["response_schema"] = response_schema
    return config


class GenaiModelAdapter:
    """Lightweight adapter around google-genai client models API."""

    def __init__(
        self,
        client: Any,
        model: str,
        system_instruction: Optional[str] = None,
        generation_config: Optional[Dict[str, Any]] = None,
        cached_content: Optional[str] = None,
    ) -> None:
        self._client = client
        self._model = model
        self._system_instruction = system_instruction
        self._generation_config = generation_config or {}
        self._cached_content = cached_content

    def _build_config(self, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        config = dict(self._generation_config)
        if self._system_instruction:
            config.setdefault("system_instruction", self._system_instruction)
        if self._cached_content:
            config.setdefault("cached_content", self._cached_content)
        if extra:
            config.update(extra)
        return config

    def generate_content(self, contents: Any, **kwargs):
        config = self._build_config(kwargs.get("config"))
        return self._client.models.generate_content(
            model=self._model,
            contents=contents,
            config=config,
        )

    async def generate_content_async(self, contents: Any, **kwargs):
        config = self._build_config(kwargs.get("config"))
        if hasattr(self._client, "aio") and hasattr(self._client.aio, "models"):
            return await self._client.aio.models.generate_content(
                model=self._model,
                contents=contents,
                config=config,
            )
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.generate_content(contents, config=config),
        )
