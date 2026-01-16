"""Versioning API Schemas.

Request/response models for fork creation and version management.
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# =============================================================================
# Version Schemas
# =============================================================================

class VersionBase(BaseModel):
    """Base version info."""
    id: UUID
    tool_id: UUID
    version: str
    version_number: int
    code_type: str
    status: str
    is_live: bool
    created_by: str
    created_at: datetime


class VersionResponse(VersionBase):
    """Full version response."""
    code_content: str
    system_prompt: Optional[str] = None
    input_schema: Optional[dict] = None
    output_schema: Optional[dict] = None
    dependencies: dict = {}
    config: dict = {}
    changelog: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class VersionCreate(BaseModel):
    """Create version request."""
    code_type: str = Field("prompt_template")
    code_content: str = Field(..., min_length=1, max_length=50000)
    system_prompt: Optional[str] = Field(None, max_length=10000)
    input_schema: Optional[dict] = None
    output_schema: Optional[dict] = None
    dependencies: Optional[dict] = None
    config: Optional[dict] = None
    changelog: Optional[str] = Field(None, max_length=1000)


# =============================================================================
# Diff Schemas
# =============================================================================

class DiffStats(BaseModel):
    """Diff statistics."""
    lines_added: int
    lines_removed: int
    lines_modified: int
    similarity_ratio: float
    diff_score: int
    is_trivial: bool


class DiffPreview(BaseModel):
    """Preview a diff before creating fork."""
    diff_content: str
    stats: DiffStats
    semantic_changes: dict
    sybil_warning: Optional[str] = None


class DiffResponse(BaseModel):
    """Full diff response."""
    id: UUID
    fork_event_id: Optional[UUID]
    original_version_id: UUID
    forked_version_id: UUID
    diff_content: str
    lines_added: int
    lines_removed: int
    lines_modified: int
    similarity_ratio: float
    diff_score: int
    is_trivial_change: bool
    semantic_changes: dict
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# Fork Schemas
# =============================================================================

class ForkCreate(BaseModel):
    """Create fork request."""
    new_tool_key: str = Field(..., min_length=3, max_length=64, pattern=r'^[a-z][a-z0-9_]*$')
    new_display_name: str = Field(..., min_length=3, max_length=100)
    code_content: str = Field(..., min_length=1, max_length=50000)
    code_type: Optional[str] = None
    changelog: Optional[str] = Field(None, max_length=1000)


class ForkPreviewRequest(BaseModel):
    """Preview fork changes request."""
    code_content: str = Field(..., min_length=1, max_length=50000)


class ForkResult(BaseModel):
    """Fork creation result."""
    tool_id: UUID
    tool_key: str
    version_id: UUID
    fork_event_id: UUID
    diff: DiffStats
    needs_review: bool
    sybil_flagged: bool


# =============================================================================
# Test Case Schemas
# =============================================================================

class TestCaseCreate(BaseModel):
    """Create test case request."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    input_data: dict
    expected_output: Optional[dict] = None
    validation_rules: Optional[dict] = None
    is_required: bool = True


class TestCaseResponse(BaseModel):
    """Test case response."""
    id: UUID
    tool_id: UUID
    name: str
    description: Optional[str]
    input_data: dict
    expected_output: Optional[dict]
    validation_rules: dict
    is_required: bool
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TestRunResult(BaseModel):
    """Result of running a test case."""
    test_id: UUID
    test_name: str
    passed: bool
    latency_ms: int
    output: Optional[dict] = None
    error: Optional[str] = None
