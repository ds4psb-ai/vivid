"""Sandbox Execution Models.

Models for isolated tool execution:
- SandboxConfig: Execution constraints
- SandboxExecution: Execution record
- SandboxResult: Execution output
"""
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, String, Text, Integer, Boolean, DateTime, Float
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


# =============================================================================
# Enums
# =============================================================================

class ExecutionStatus(str, Enum):
    """Sandbox execution status."""
    PENDING = "pending"           # Queued
    RUNNING = "running"           # Currently executing
    SUCCESS = "success"           # Completed successfully
    FAILED = "failed"             # Execution error
    TIMEOUT = "timeout"           # Exceeded time limit
    OOM = "oom"                   # Out of memory
    KILLED = "killed"             # Manually terminated
    REJECTED = "rejected"         # Failed safety check


class SandboxTier(str, Enum):
    """Sandbox restriction levels."""
    STRICT = "strict"       # No network, readonly fs, minimal resources
    STANDARD = "standard"   # Limited network (allowlist), restricted fs
    TRUSTED = "trusted"     # Full network, limited fs writes


# =============================================================================
# Sandbox Config
# =============================================================================

class SandboxConfig(Base):
    """Configuration for sandbox execution environment.
    
    Defines resource limits and restrictions for tool execution.
    """
    __tablename__ = "sandbox_configs"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    tier: Mapped[str] = mapped_column(String(20), default=SandboxTier.STRICT.value)
    
    # Resource limits
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=30)
    memory_mb: Mapped[int] = mapped_column(Integer, default=512)
    cpu_limit: Mapped[float] = mapped_column(Float, default=1.0)  # CPU cores
    
    # Network restrictions
    network_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    allowed_hosts: Mapped[list] = mapped_column(JSONB, default=list)
    
    # Filesystem restrictions
    filesystem_readonly: Mapped[bool] = mapped_column(Boolean, default=True)
    allowed_paths: Mapped[list] = mapped_column(JSONB, default=list)
    
    # Execution limits
    max_output_bytes: Mapped[int] = mapped_column(Integer, default=1024 * 1024)  # 1MB
    max_input_bytes: Mapped[int] = mapped_column(Integer, default=1024 * 100)    # 100KB
    
    # Metadata
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


# =============================================================================
# Sandbox Execution
# =============================================================================

class SandboxExecution(Base):
    """Record of a sandboxed tool execution.
    
    Tracks execution from queuing to completion with resource usage.
    """
    __tablename__ = "sandbox_executions"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    
    # What was executed
    tool_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("tool_manifests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("tool_versions.id", ondelete="SET NULL"),
        nullable=True,
    )
    config_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sandbox_configs.id", ondelete="RESTRICT"),
        nullable=False,
    )
    
    # Who triggered it
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    
    # Input/Output
    input_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    output_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # Status
    status: Mapped[str] = mapped_column(
        String(20), 
        default=ExecutionStatus.PENDING.value,
        index=True,
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Resource usage
    execution_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    memory_used_mb: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cpu_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Container info
    container_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    exit_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Logs
    stdout: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    stderr: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    queued_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Credits
    credits_charged: Mapped[int] = mapped_column(Integer, default=0)
    credits_refunded: Mapped[int] = mapped_column(Integer, default=0)


# =============================================================================
# Default Configs
# =============================================================================

DEFAULT_SANDBOX_CONFIGS = [
    {
        "name": "strict",
        "tier": SandboxTier.STRICT.value,
        "description": "Maximum isolation - no network, readonly filesystem",
        "timeout_seconds": 30,
        "memory_mb": 256,
        "cpu_limit": 0.5,
        "network_enabled": False,
        "filesystem_readonly": True,
    },
    {
        "name": "standard",
        "tier": SandboxTier.STANDARD.value,
        "description": "Standard isolation for verified tools",
        "timeout_seconds": 60,
        "memory_mb": 512,
        "cpu_limit": 1.0,
        "network_enabled": True,
        "allowed_hosts": ["api.openai.com", "generativelanguage.googleapis.com"],
        "filesystem_readonly": True,
    },
    {
        "name": "trusted",
        "tier": SandboxTier.TRUSTED.value,
        "description": "Minimal isolation for certified tools",
        "timeout_seconds": 120,
        "memory_mb": 1024,
        "cpu_limit": 2.0,
        "network_enabled": True,
        "filesystem_readonly": False,
        "allowed_paths": ["/tmp", "/app/data"],
    },
]
