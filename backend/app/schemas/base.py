"""Base Pydantic models with strict configuration.

Provides StrictBaseModel for external-facing API schemas that require
strict type validation to prevent type coercion attacks.

Usage:
    from app.schemas.base import StrictBaseModel

    class UserCreateRequest(StrictBaseModel):
        email: str
        age: int  # "123" -> ValidationError (no coercion)

Benefits:
    - Prevents type coercion attacks ("123" -> 123)
    - Runtime type safety enforcement
    - Validates on attribute assignment
"""
from pydantic import BaseModel, ConfigDict


class StrictBaseModel(BaseModel):
    """Base model with strict type validation for external API inputs.

    Features:
        - strict=True: Disables automatic type coercion
        - validate_assignment=True: Validates on attribute changes
        - extra="forbid": Rejects unknown fields

    Use for:
        - API request models (POST/PUT/PATCH bodies)
        - User-facing input validation
        - Security-sensitive data

    Do NOT use for:
        - ORM response models (use ConfigDict(from_attributes=True))
        - Internal DTOs where coercion is acceptable
    """

    model_config = ConfigDict(
        strict=True,
        validate_assignment=True,
        extra="forbid",
    )


class StrictInputModel(StrictBaseModel):
    """Alias for StrictBaseModel with explicit naming."""

    pass
