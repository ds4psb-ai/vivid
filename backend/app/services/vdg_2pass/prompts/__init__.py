"""
VDG 2-Pass Prompts Package.
"""
from .semantic_prompt import SEMANTIC_SYSTEM_PROMPT, SEMANTIC_USER_PROMPT
from .visual_prompt import VISUAL_SYSTEM_PROMPT, VISUAL_USER_PROMPT, get_metric_registry_json

__all__ = [
    "SEMANTIC_SYSTEM_PROMPT",
    "SEMANTIC_USER_PROMPT",
    "VISUAL_SYSTEM_PROMPT",
    "VISUAL_USER_PROMPT",
    "get_metric_registry_json",
]
