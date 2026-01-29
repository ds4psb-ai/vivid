"""
Schemas package for Crebit Backend.

Provides Pydantic models for API request/response validation.
"""
from app.schemas.base import StrictBaseModel, StrictInputModel

__all__ = ["StrictBaseModel", "StrictInputModel"]
