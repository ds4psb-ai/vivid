"""Tool Versioning and Diff Models.

Models for managing tool code versions and tracking changes:
- ToolVersion: Stores actual tool code/logic
- ToolDiff: Tracks changes between versions (for fork attribution)
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Index, String, Text, Integer, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# =============================================================================
# Enums
# =============================================================================

class CodeType(str, Enum):
    """Type of tool code/logic."""
    PROMPT_TEMPLATE = "prompt_template"     # LLM prompt with variables
    PYTHON_FUNCTION = "python_function"     # Python code (sandboxed)
    API_CALL = "api_call"                   # External API configuration
    COMPOSITE = "composite"                 # Combines multiple tools
    STATIC = "static"                       # No code, just schema


class VersionStatus(str, Enum):
    """Tool version status."""
    DRAFT = "draft"                   # Being edited
    PENDING_REVIEW = "pending_review" # Submitted for review
    APPROVED = "approved"             # Live version
    REJECTED = "rejected"             # Review rejected
    DEPRECATED = "deprecated"         # Old version


# =============================================================================
# Tool Version
# =============================================================================

class ToolVersion(Base):
    """Version-controlled tool code.
    
    Each ToolManifest can have multiple versions. Only one can be
    'approved' (live) at a time.
    """
    __tablename__ = "tool_versions"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    
    # Parent tool
    tool_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("tool_manifests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Version info
    version: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g. "1.0.0"
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)  # Auto-increment
    
    # Code type and content
    code_type: Mapped[str] = mapped_column(
        String(30), 
        default=CodeType.PROMPT_TEMPLATE.value
    )
    code_content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Input/Output schemas (overrides from manifest if specified)
    input_schema: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    output_schema: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # System prompt for LLM-based tools
    system_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Dependencies
    dependencies: Mapped[dict] = mapped_column(JSONB, default=dict)
    # e.g. {"pip": ["requests"], "tools": ["uuid-of-other-tool"]}
    
    # Configuration
    config: Mapped[dict] = mapped_column(JSONB, default=dict)
    # e.g. {"timeout_seconds": 30, "max_tokens": 1000}
    
    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        default=VersionStatus.DRAFT.value,
        index=True,
    )
    is_live: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Creator
    created_by: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    
    # Review
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    
    # Change log
    changelog: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_tool_version_tool_status", "tool_id", "status"),
        Index("ix_tool_version_tool_live", "tool_id", "is_live"),
    )


# =============================================================================
# Tool Diff
# =============================================================================

class ToolDiff(Base):
    """Diff between tool versions.
    
    Used for:
    1. Computing attribution score for forks
    2. Code review
    3. Version comparison
    """
    __tablename__ = "tool_diffs"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    
    # Fork event (if this is a fork diff)
    fork_event_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("fork_events.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # Versions being compared
    original_version_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("tool_versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    forked_version_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("tool_versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    # Raw diff
    diff_content: Mapped[str] = mapped_column(Text, nullable=False)  # Unified diff format
    
    # Statistics
    lines_added: Mapped[int] = mapped_column(Integer, default=0)
    lines_removed: Mapped[int] = mapped_column(Integer, default=0)
    lines_modified: Mapped[int] = mapped_column(Integer, default=0)
    
    # Semantic analysis
    semantic_changes: Mapped[dict] = mapped_column(JSONB, default=dict)
    # e.g. {"added_parameters": ["style"], "modified_prompt": true, "changed_model": false}
    
    # Attribution calculation
    diff_score: Mapped[int] = mapped_column(Integer, default=0)  # 0-100
    similarity_ratio: Mapped[float] = mapped_column(default=0.0)  # 0.0-1.0
    
    # Sybil detection
    is_trivial_change: Mapped[bool] = mapped_column(Boolean, default=False)
    sybil_flags: Mapped[dict] = mapped_column(JSONB, default=dict)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# =============================================================================
# Tool Test Case
# =============================================================================

class ToolTestCase(Base):
    """Test cases for tool validation.
    
    Forks inherit test cases from parent tool.
    """
    __tablename__ = "tool_test_cases"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    
    tool_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("tool_manifests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Test info
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Test data
    input_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    expected_output: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # Validation rules
    validation_rules: Mapped[dict] = mapped_column(JSONB, default=dict)
    # e.g. {"output_contains": "keyword", "max_latency_ms": 5000}
    
    # Status
    is_required: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    created_by: Mapped[str] = mapped_column(String(64), nullable=False)
