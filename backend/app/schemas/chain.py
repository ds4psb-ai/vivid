"""Pydantic schemas for Chain Session management.

Provides type-safe schemas for:
- Chain data output from dimension executions
- Chain session CRUD operations
- Optimistic locking support (version field)
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class ChainDataOutput(BaseModel):
    """Individual dimension execution result stored in chain.

    Represents the output from a single dimension panel execution
    that can be passed to downstream dimensions in the workflow.
    """

    dimension_key: str = Field(..., description="Dimension route key (e.g., 'reference-decoder')")
    output: dict[str, Any] = Field(default_factory=dict, description="Output data from dimension")
    title: str = Field(default="", description="Human-readable title/summary")
    evidence_refs: list[str] = Field(default_factory=list, description="Evidence references (List[str])")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When this output was created")

    @field_validator("evidence_refs", mode="before")
    @classmethod
    def validate_evidence_refs(cls, v: Any) -> list[str]:
        """Ensure evidence_refs is a list of strings (not dicts)."""
        if v is None:
            return []
        if isinstance(v, list):
            # Validate each item is a string
            return [str(item) for item in v]
        return []


class ChainSessionCreate(BaseModel):
    """Request schema for creating a new chain session."""

    mega_app: Optional[str] = Field(None, description="MegaApp context (e.g., 'dna-lab')")
    title: Optional[str] = Field(None, max_length=255, description="Session title")
    ip_slug: Optional[str] = Field(None, max_length=100, description="IP slug for project association")


class ChainSessionUpdate(BaseModel):
    """Request schema for updating a chain session.

    Requires version field for optimistic locking - prevents
    race conditions when multiple clients update the same session.
    """

    chain_data: Optional[dict[str, ChainDataOutput]] = Field(
        None, description="Updated chain data (keyed by dimension_key)"
    )
    accumulated_evidence_refs: Optional[list[str]] = Field(
        None, description="Accumulated evidence refs across all dimensions"
    )
    current_dimension: Optional[str] = Field(None, max_length=50, description="Currently active dimension")
    navigation_history: Optional[list[str]] = Field(None, description="Navigation history (dimension keys)")
    title: Optional[str] = Field(None, max_length=255, description="Session title")

    # Optimistic Locking - required for updates
    version: int = Field(..., ge=1, description="Current version for optimistic locking (required)")

    @field_validator("chain_data", mode="before")
    @classmethod
    def validate_chain_data(cls, v: Any) -> Optional[dict[str, ChainDataOutput]]:
        """Convert raw dict to ChainDataOutput objects."""
        if v is None:
            return None
        if isinstance(v, dict):
            result = {}
            for key, value in v.items():
                if isinstance(value, ChainDataOutput):
                    result[key] = value
                elif isinstance(value, dict):
                    result[key] = ChainDataOutput(**value)
                else:
                    raise ValueError(f"Invalid chain data value for key {key}")
            return result
        return v


class ChainSessionResponse(BaseModel):
    """Response schema for chain session queries."""

    id: uuid.UUID
    user_id: str
    chain_data: dict[str, ChainDataOutput] = Field(default_factory=dict)
    accumulated_evidence_refs: list[str] = Field(default_factory=list)
    current_dimension: Optional[str] = None
    navigation_history: list[str] = Field(default_factory=list)
    mega_app: Optional[str] = None
    title: Optional[str] = None
    ip_slug: Optional[str] = None
    version: int = Field(..., description="Current version for optimistic locking")
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChainSessionListItem(BaseModel):
    """Abbreviated response for session list queries."""

    id: uuid.UUID
    title: Optional[str]
    mega_app: Optional[str]
    ip_slug: Optional[str]
    version: int
    current_dimension: Optional[str]
    dimension_count: int = Field(default=0, description="Number of dimensions with data")
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChainConflictError(BaseModel):
    """Error response for version conflicts (409)."""

    error: str = Field(default="VERSION_CONFLICT")
    server_version: int
    your_version: int
    message: str = Field(default="Session was modified by another client")


class PreviousRunResponse(BaseModel):
    """Response for getting previous run output for a dimension."""

    run_id: Optional[uuid.UUID] = None
    dimension_key: str
    output: dict[str, Any] = Field(default_factory=dict)
    evidence_refs: list[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    found: bool = Field(default=False, description="Whether previous run data was found")
