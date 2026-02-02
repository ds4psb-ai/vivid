"""Provider Adapters - LogicVector → Provider Native Format Translation.

This package provides the translation layer between:
1. LogicVector (VPE/VDG output) - Semantic analysis results
2. PromptCards (IR - Intermediate Representation) - Structured shot grammar
3. Provider Native Format - Veo/Kling/Sora specific prompts

Architecture:
    LogicVector (VPE output)
           ↓
    PromptCards (IR - 중간 표현)
           ↓
    ProviderAdapter.compile()
           ↓
    Veo/Kling/Sora Native Format

Usage:
    from app.routers.production.providers.adapters import (
        get_adapter,
        VeoAdapter,
        KlingAdapter,
    )

    # Get adapter by provider name
    adapter = get_adapter("veo")

    # Translate LogicVector → Provider prompt
    result = adapter.translate_logic_vector(logic_vector)

    # Or compile PromptCards → Provider prompt
    result = adapter.compile_prompt_cards(prompt_cards)
"""
from .base_adapter import (
    BaseProviderAdapter,
    AdapterResult,
    ProviderPromptConfig,
)
from .veo_adapter import VeoAdapter
from .kling_adapter import KlingAdapter
from .sora_adapter import SoraAdapter

# Adapter registry
_ADAPTERS = {
    "veo": VeoAdapter,
    "kling": KlingAdapter,
    "sora": SoraAdapter,
}


def get_adapter(provider_name: str) -> BaseProviderAdapter:
    """Get adapter instance by provider name.

    Args:
        provider_name: Provider name (veo, kling, sora)

    Returns:
        Provider adapter instance

    Raises:
        ValueError: If provider is not supported
    """
    adapter_cls = _ADAPTERS.get(provider_name.lower())
    if not adapter_cls:
        supported = ", ".join(_ADAPTERS.keys())
        raise ValueError(f"Unsupported provider: {provider_name}. Supported: {supported}")
    return adapter_cls()


def list_adapters() -> list[str]:
    """List all supported provider adapters."""
    return list(_ADAPTERS.keys())


__all__ = [
    "BaseProviderAdapter",
    "AdapterResult",
    "ProviderPromptConfig",
    "VeoAdapter",
    "KlingAdapter",
    "SoraAdapter",
    "get_adapter",
    "list_adapters",
]
