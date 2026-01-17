"""MCP Database Models (P0 Phase 4 - 2026).

MCP Gateway 감사 로그 및 정책 저장.

Tables:
    - mcp_audit_logs: 모든 MCP 호출 기록 (compliance)
    - mcp_policies: 사용자/그룹별 접근 정책
    - mcp_user_policies: 사용자-정책 매핑
    - mcp_rate_limits: Rate limit 상태 (Redis 백업)

2026 Best Practices:
    - Partitioned table for audit logs (날짜별)
    - JSONB for flexible schema
    - Optimized indexes for common queries
    - Soft delete for policies
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    String,
    DateTime,
    Integer,
    Float,
    Text,
    Boolean,
    Index,
    Enum,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.database import Base


# =============================================================================
# Enums
# =============================================================================

class MCPActionType(str, enum.Enum):
    """MCP 액션 유형."""
    TOOL_CALL = "tool_call"
    TOOL_LIST = "tool_list"
    RESOURCE_READ = "resource_read"
    RESOURCE_LIST = "resource_list"
    PROMPT_GET = "prompt_get"
    HEALTH_CHECK = "health_check"


class MCPAuditLevel(str, enum.Enum):
    """감사 수준."""
    NONE = "none"
    BASIC = "basic"
    FULL = "full"


class MCPPolicyStatus(str, enum.Enum):
    """정책 상태."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


# =============================================================================
# MCP Audit Log
# =============================================================================

class MCPAuditLog(Base):
    """MCP 감사 로그.

    모든 MCP 호출을 기록합니다 (compliance-ready).

    Indexes:
        - (user_id, timestamp): 사용자별 최근 로그
        - (server_id, timestamp): 서버별 호출 통계
        - (success, timestamp): 에러 분석
        - (request_id): 요청 추적
    """
    __tablename__ = "mcp_audit_logs"
    __table_args__ = (
        Index("ix_mcp_audit_user_time", "user_id", "timestamp"),
        Index("ix_mcp_audit_server_time", "server_id", "timestamp"),
        Index("ix_mcp_audit_success_time", "success", "timestamp"),
        Index("ix_mcp_audit_request_id", "request_id"),
        Index("ix_mcp_audit_action", "action"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )

    # Request identification
    request_id: Mapped[str] = mapped_column(String(32), nullable=False)
    user_id: Mapped[str] = mapped_column(String(160), nullable=False)

    # MCP call details
    server_id: Mapped[str] = mapped_column(String(64), nullable=False)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    tool_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    # Security (hashed arguments for compliance)
    arguments_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    arguments_preview: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True
    )  # 민감 정보 제거된 일부

    # Result
    success: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    result_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Performance
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)

    # Economics
    credit_cost: Mapped[int] = mapped_column(Integer, default=0)
    run_token: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Context
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)  # IPv6 지원
    user_agent: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    policy_applied: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Extra metadata (named 'extra' to avoid SQLAlchemy reserved word 'metadata')
    extra: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)


# =============================================================================
# MCP Policy
# =============================================================================

class MCPPolicyModel(Base):
    """MCP 접근 정책.

    사용자/그룹별 MCP 접근 권한을 정의합니다.
    """
    __tablename__ = "mcp_policies"
    __table_args__ = (
        Index("ix_mcp_policies_status", "status"),
        Index("ix_mcp_policies_priority", "priority"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    policy_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Access Control (stored as JSON arrays)
    allowed_servers: Mapped[list] = mapped_column(ARRAY(String), default=list)
    denied_servers: Mapped[list] = mapped_column(ARRAY(String), default=list)
    allowed_tools: Mapped[list] = mapped_column(ARRAY(String), default=list)
    denied_tools: Mapped[list] = mapped_column(ARRAY(String), default=list)

    # Rate Limits
    max_calls_per_minute: Mapped[int] = mapped_column(Integer, default=30)
    max_calls_per_hour: Mapped[int] = mapped_column(Integer, default=500)
    max_calls_per_day: Mapped[int] = mapped_column(Integer, default=5000)

    # Credit Limits
    max_credit_per_call: Mapped[int] = mapped_column(Integer, default=100)
    max_credit_per_day: Mapped[int] = mapped_column(Integer, default=10000)

    # Time Restrictions (0-24 hours)
    allowed_hours_start: Mapped[int] = mapped_column(Integer, default=0)
    allowed_hours_end: Mapped[int] = mapped_column(Integer, default=24)

    # Security
    require_run_token: Mapped[bool] = mapped_column(Boolean, default=False)
    audit_level: Mapped[str] = mapped_column(
        String(16), default=MCPAuditLevel.BASIC.value
    )

    # Status and Priority
    status: Mapped[str] = mapped_column(
        String(16), default=MCPPolicyStatus.ACTIVE.value
    )
    priority: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    created_by: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)


# =============================================================================
# User Policy Mapping
# =============================================================================

class MCPUserPolicy(Base):
    """사용자-정책 매핑.

    하나의 사용자에게 하나의 정책만 할당 가능.
    """
    __tablename__ = "mcp_user_policies"
    __table_args__ = (
        Index("ix_mcp_user_policies_user", "user_id", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)
    policy_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("mcp_policies.policy_id", ondelete="CASCADE"),
        nullable=False,
    )
    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    assigned_by: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)


# =============================================================================
# MCP Server Config (DB-based, optional)
# =============================================================================

class MCPServerConfigModel(Base):
    """MCP 서버 설정 (DB 저장).

    환경변수 대신 DB에서 서버 설정을 관리할 때 사용.
    """
    __tablename__ = "mcp_server_configs"
    __table_args__ = (
        Index("ix_mcp_server_configs_enabled", "enabled"),
        Index("ix_mcp_server_configs_tier", "tier"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    server_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Transport
    transport: Mapped[str] = mapped_column(String(32), default="streamable_http")
    url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    command: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    args: Mapped[list] = mapped_column(ARRAY(String), default=list)
    env: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Authentication (encrypted)
    auth_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    auth_config_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timeouts and Limits
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=30)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    retry_delay_ms: Mapped[int] = mapped_column(Integer, default=1000)
    circuit_breaker_threshold: Mapped[int] = mapped_column(Integer, default=5)
    rate_limit_rpm: Mapped[int] = mapped_column(Integer, default=60)

    # Tier and Economics
    tier: Mapped[str] = mapped_column(String(16), default="core")
    credit_cost: Mapped[int] = mapped_column(Integer, default=1)

    # Status
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # Extra metadata (named 'extra' to avoid SQLAlchemy reserved word 'metadata')
    extra: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


# =============================================================================
# MCP Rate Limit State (Redis backup)
# =============================================================================

class MCPRateLimitState(Base):
    """Rate limit 상태 (Redis 백업용).

    Redis 장애 시 복구를 위한 백업 테이블.
    실시간 처리는 Redis, 백업은 주기적으로 DB 동기화.
    """
    __tablename__ = "mcp_rate_limit_states"
    __table_args__ = (
        Index("ix_mcp_rate_limit_user", "user_id", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)

    # Counters
    minute_count: Mapped[int] = mapped_column(Integer, default=0)
    hour_count: Mapped[int] = mapped_column(Integer, default=0)
    day_count: Mapped[int] = mapped_column(Integer, default=0)
    day_credit: Mapped[int] = mapped_column(Integer, default=0)

    # Reset timestamps
    minute_reset: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    hour_reset: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    day_reset: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Sync timestamp
    synced_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# =============================================================================
# MCP Tool Usage Stats (Aggregated)
# =============================================================================

class MCPToolUsageStats(Base):
    """MCP 도구 사용 통계 (집계 테이블).

    일별/주별/월별 집계 통계.
    """
    __tablename__ = "mcp_tool_usage_stats"
    __table_args__ = (
        Index("ix_mcp_tool_usage_server_tool_date", "server_id", "tool_name", "date"),
        Index("ix_mcp_tool_usage_date", "date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False)  # 날짜 (시간 제거)
    server_id: Mapped[str] = mapped_column(String(64), nullable=False)
    tool_name: Mapped[str] = mapped_column(String(128), nullable=False)

    # Counts
    total_calls: Mapped[int] = mapped_column(Integer, default=0)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)

    # Performance
    avg_latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    p50_latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    p95_latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    p99_latency_ms: Mapped[float] = mapped_column(Float, default=0.0)

    # Economics
    total_credits: Mapped[int] = mapped_column(Integer, default=0)

    # Unique users
    unique_users: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
