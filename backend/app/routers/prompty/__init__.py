"""Prompty Router Package.

AI-free workflow guide platform.
"""
from fastapi import APIRouter

from .projects import router as projects_router
from .templates import router as templates_router
from .critique import router as critique_router
from .guide import router as guide_router

router = APIRouter(prefix="/prompty", tags=["prompty"])

router.include_router(projects_router)
router.include_router(templates_router)
router.include_router(critique_router)
router.include_router(guide_router)

__all__ = ["router"]
