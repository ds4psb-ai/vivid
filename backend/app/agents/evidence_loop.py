"""Evidence Loop for Vivid AI Learning (Hardened v2).

Collects explicit metrics for AI model improvement.
Based on Evidence Loop philosophy: explicit metrics over implicit signals.

Hardening v2 includes:
- Thread safety with RLock
- Bounded event buffer (memory protection)
- Input validation and sanitization
- Rate limiting per session
- Configurable sampling
- Graceful degradation
"""
from __future__ import annotations

import re
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Deque, Dict, FrozenSet, List, Optional, Tuple
from uuid import uuid4

from app.logging_config import get_logger

logger = get_logger("evidence_loop")


# =============================================================================
# Configuration
# =============================================================================

@dataclass(frozen=True)
class EvidenceConfig:
    """Configuration for evidence collection."""
    max_events: int = 10_000              # Maximum events in buffer
    max_events_per_session: int = 500      # Max events per session
    max_pending_starts: int = 1_000        # Max pending tool starts
    max_string_length: int = 500           # Max string field length
    sampling_rate: float = 1.0             # 1.0 = 100% sampling
    rate_limit_per_minute: int = 100       # Max events per session per minute


DEFAULT_CONFIG = EvidenceConfig()


# =============================================================================
# Allowed Values (Whitelist)
# =============================================================================

ALLOWED_DIMENSIONS: FrozenSet[str] = frozenset({"1D", "2D", "3D", "4D"})
ALLOWED_TOOLS: FrozenSet[str] = frozenset({
    "generate_veo_prompt",
    "create_storyboard", 
    "generate_image_prompt",
    "analyze_reference",
    "analyze_sources",
})
ALLOWED_ACTIONS: FrozenSet[str] = frozenset({"accept", "reject", "edit"})


# =============================================================================
# Event Types
# =============================================================================

class EvidenceEventType(Enum):
    """Types of evidence events."""
    TOOL_START = "tool_start"
    TOOL_SUCCESS = "tool_success"
    TOOL_FAILURE = "tool_failure"
    TOOL_RETRY = "tool_retry"
    QUALITY_SCORE = "quality_score"
    USER_EDIT = "user_edit"
    USER_ACCEPT = "user_accept"
    USER_REJECT = "user_reject"
    WORKFLOW_START = "workflow_start"
    WORKFLOW_COMPLETE = "workflow_complete"
    WORKFLOW_ABANDON = "workflow_abandon"
    SESSION_START = "session_start"
    SESSION_END = "session_end"


class ToolStatus(Enum):
    """Tool execution status."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILURE = "failure"
    RETRIED = "retried"


# =============================================================================
# Evidence Event (Immutable)
# =============================================================================

@dataclass(frozen=True)
class EvidenceEvent:
    """An immutable evidence event."""
    event_id: str
    event_type: EvidenceEventType
    timestamp: datetime
    session_id: str
    user_id: Optional[str]
    tool_name: Optional[str] = None
    tool_status: Optional[ToolStatus] = None
    latency_ms: Optional[int] = None
    credit_cost: Optional[int] = None
    quality_score: Optional[float] = None
    dimension: Optional[str] = None
    intent: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Tuple[Tuple[str, Any], ...] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/storage."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
            "user_id": self.user_id,
            "tool_name": self.tool_name,
            "tool_status": self.tool_status.value if self.tool_status else None,
            "latency_ms": self.latency_ms,
            "credit_cost": self.credit_cost,
            "quality_score": self.quality_score,
            "dimension": self.dimension,
            "intent": self.intent,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "metadata": dict(self.metadata),
        }


# =============================================================================
# Input Validation
# =============================================================================

_SAFE_STRING_PATTERN = re.compile(r"^[\w\s\-._:/@#]+$", re.UNICODE)


def sanitize_string(value: str, max_length: int = 500) -> str:
    """Sanitize and truncate string input."""
    if not isinstance(value, str):
        return ""
    # Strip and truncate
    value = value.strip()[:max_length]
    return value


def validate_session_id(session_id: str) -> str:
    """Validate session ID format."""
    if not session_id or not isinstance(session_id, str):
        raise ValueError("session_id must be a non-empty string")
    return sanitize_string(session_id, 100)


def validate_tool_name(tool_name: str) -> str:
    """Validate tool name against whitelist."""
    if not tool_name:
        raise ValueError("tool_name must be provided")
    # Allow any tool name but sanitize
    return sanitize_string(tool_name, 50)


def validate_dimension(dimension: Optional[str]) -> Optional[str]:
    """Validate dimension value."""
    if dimension is None:
        return None
    if dimension not in ALLOWED_DIMENSIONS:
        return None  # Gracefully ignore invalid dimensions
    return dimension


def validate_quality_score(score: float) -> float:
    """Validate and clamp quality score."""
    if not isinstance(score, (int, float)):
        return 0.0
    return max(0.0, min(5.0, float(score)))


# =============================================================================
# Rate Limiter
# =============================================================================

class SessionRateLimiter:
    """Simple rate limiter per session."""
    
    def __init__(self, max_per_minute: int = 100) -> None:
        self._max_per_minute = max_per_minute
        self._lock = threading.Lock()
        self._sessions: Dict[str, Deque[float]] = {}
    
    def is_allowed(self, session_id: str) -> bool:
        """Check if session is allowed to record an event."""
        now = time.time()
        cutoff = now - 60.0
        
        with self._lock:
            if session_id not in self._sessions:
                self._sessions[session_id] = deque(maxlen=self._max_per_minute * 2)
            
            timestamps = self._sessions[session_id]
            
            # Remove old timestamps
            while timestamps and timestamps[0] < cutoff:
                timestamps.popleft()
            
            if len(timestamps) >= self._max_per_minute:
                return False
            
            timestamps.append(now)
            return True
    
    def cleanup_old_sessions(self, max_age_seconds: int = 3600) -> int:
        """Remove sessions older than max_age."""
        now = time.time()
        cutoff = now - max_age_seconds
        removed = 0
        
        with self._lock:
            sessions_to_remove = []
            for session_id, timestamps in self._sessions.items():
                if not timestamps or timestamps[-1] < cutoff:
                    sessions_to_remove.append(session_id)
            
            for session_id in sessions_to_remove:
                del self._sessions[session_id]
                removed += 1
        
        return removed


# =============================================================================
# Evidence Collector (Hardened)
# =============================================================================

class EvidenceCollector:
    """Thread-safe evidence collector with bounded buffer."""
    
    def __init__(self, config: EvidenceConfig = DEFAULT_CONFIG) -> None:
        self._config = config
        self._lock = threading.RLock()
        self._events: Deque[EvidenceEvent] = deque(maxlen=config.max_events)
        self._tool_starts: Dict[str, float] = {}
        self._session_event_counts: Dict[str, int] = {}
        self._rate_limiter = SessionRateLimiter(config.rate_limit_per_minute)
        self._dropped_count = 0
    
    def record_tool_start(
        self,
        session_id: str,
        tool_name: str,
        dimension: Optional[str] = None,
        intent: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Record tool execution start. Returns event_id."""
        try:
            # Validate inputs
            session_id = validate_session_id(session_id)
            tool_name = validate_tool_name(tool_name)
            dimension = validate_dimension(dimension)
            
            # Rate limit check
            if not self._rate_limiter.is_allowed(session_id):
                self._dropped_count += 1
                logger.warning("Rate limit exceeded", extra={"session_id": session_id})
                return ""
            
            event_id = str(uuid4())
            now = datetime.now(timezone.utc)
            
            event = EvidenceEvent(
                event_id=event_id,
                event_type=EvidenceEventType.TOOL_START,
                timestamp=now,
                session_id=session_id,
                user_id=sanitize_string(user_id, 100) if user_id else None,
                tool_name=tool_name,
                tool_status=ToolStatus.RUNNING,
                dimension=dimension,
                intent=sanitize_string(intent, 100) if intent else None,
                metadata=tuple((k, v) for k, v in (metadata or {}).items())[:10],
            )
            
            with self._lock:
                # Check session limit
                count = self._session_event_counts.get(session_id, 0)
                if count >= self._config.max_events_per_session:
                    self._dropped_count += 1
                    return ""
                
                # Check pending starts limit
                if len(self._tool_starts) >= self._config.max_pending_starts:
                    # Clean up old starts
                    self._cleanup_stale_starts()
                
                self._events.append(event)
                self._tool_starts[event_id] = time.perf_counter()
                self._session_event_counts[session_id] = count + 1
            
            logger.info(
                "evidence_tool_start",
                extra={"event_id": event_id, "session_id": session_id, "tool_name": tool_name},
            )
            return event_id
            
        except Exception as e:
            logger.exception("Failed to record tool start", extra={"error": str(e)})
            return ""
    
    def record_tool_success(
        self,
        event_id: str,
        session_id: str,
        tool_name: str,
        credit_cost: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record tool execution success."""
        try:
            if not event_id:
                return
            
            session_id = validate_session_id(session_id)
            tool_name = validate_tool_name(tool_name)
            credit_cost = max(0, min(1000, credit_cost))  # Clamp credits
            
            latency_ms = self._calculate_latency(event_id)
            now = datetime.now(timezone.utc)
            
            event = EvidenceEvent(
                event_id=event_id,
                event_type=EvidenceEventType.TOOL_SUCCESS,
                timestamp=now,
                session_id=session_id,
                user_id=None,
                tool_name=tool_name,
                tool_status=ToolStatus.SUCCESS,
                latency_ms=latency_ms,
                credit_cost=credit_cost,
                metadata=tuple((k, v) for k, v in (metadata or {}).items())[:10],
            )
            
            with self._lock:
                self._events.append(event)
            
            logger.info(
                "evidence_tool_success",
                extra={"event_id": event_id, "latency_ms": latency_ms, "credit_cost": credit_cost},
            )
            
        except Exception as e:
            logger.exception("Failed to record tool success", extra={"error": str(e)})
    
    def record_tool_failure(
        self,
        event_id: str,
        session_id: str,
        tool_name: str,
        error_code: str,
        error_message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record tool execution failure."""
        try:
            if not event_id:
                return
            
            session_id = validate_session_id(session_id)
            tool_name = validate_tool_name(tool_name)
            error_code = sanitize_string(error_code, 50)
            error_message = sanitize_string(error_message, 500)
            
            latency_ms = self._calculate_latency(event_id)
            now = datetime.now(timezone.utc)
            
            event = EvidenceEvent(
                event_id=event_id,
                event_type=EvidenceEventType.TOOL_FAILURE,
                timestamp=now,
                session_id=session_id,
                user_id=None,
                tool_name=tool_name,
                tool_status=ToolStatus.FAILURE,
                latency_ms=latency_ms,
                error_code=error_code,
                error_message=error_message,
                metadata=tuple((k, v) for k, v in (metadata or {}).items())[:10],
            )
            
            with self._lock:
                self._events.append(event)
            
            logger.warning(
                "evidence_tool_failure",
                extra={"event_id": event_id, "error_code": error_code},
            )
            
        except Exception as e:
            logger.exception("Failed to record tool failure", extra={"error": str(e)})
    
    def record_quality_score(
        self,
        session_id: str,
        tool_name: str,
        score: float,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record user quality feedback."""
        try:
            session_id = validate_session_id(session_id)
            tool_name = validate_tool_name(tool_name)
            score = validate_quality_score(score)
            
            if not self._rate_limiter.is_allowed(session_id):
                return
            
            event = EvidenceEvent(
                event_id=str(uuid4()),
                event_type=EvidenceEventType.QUALITY_SCORE,
                timestamp=datetime.now(timezone.utc),
                session_id=session_id,
                user_id=sanitize_string(user_id, 100) if user_id else None,
                tool_name=tool_name,
                quality_score=score,
                metadata=tuple((k, v) for k, v in (metadata or {}).items())[:10],
            )
            
            with self._lock:
                self._events.append(event)
            
            logger.info("evidence_quality_score", extra={"score": score, "tool_name": tool_name})
            
        except Exception as e:
            logger.exception("Failed to record quality score", extra={"error": str(e)})
    
    def record_user_action(
        self,
        session_id: str,
        action: str,
        tool_name: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record user action on tool output."""
        try:
            session_id = validate_session_id(session_id)
            
            if action not in ALLOWED_ACTIONS:
                action = "edit"
            
            event_type_map = {
                "accept": EvidenceEventType.USER_ACCEPT,
                "reject": EvidenceEventType.USER_REJECT,
                "edit": EvidenceEventType.USER_EDIT,
            }
            
            event = EvidenceEvent(
                event_id=str(uuid4()),
                event_type=event_type_map[action],
                timestamp=datetime.now(timezone.utc),
                session_id=session_id,
                user_id=sanitize_string(user_id, 100) if user_id else None,
                tool_name=validate_tool_name(tool_name) if tool_name else None,
                metadata=tuple((k, v) for k, v in (metadata or {}).items())[:10],
            )
            
            with self._lock:
                self._events.append(event)
            
            logger.info(f"evidence_user_{action}", extra={"session_id": session_id})
            
        except Exception as e:
            logger.exception("Failed to record user action", extra={"error": str(e)})
    
    def get_session_metrics(self, session_id: str) -> Dict[str, Any]:
        """Get aggregated metrics for a session (thread-safe)."""
        try:
            session_id = validate_session_id(session_id)
            
            with self._lock:
                events = [e for e in self._events if e.session_id == session_id]
            
            if not events:
                return {"session_id": session_id, "has_data": False}
            
            starts = [e for e in events if e.event_type == EvidenceEventType.TOOL_START]
            successes = [e for e in events if e.event_type == EvidenceEventType.TOOL_SUCCESS]
            failures = [e for e in events if e.event_type == EvidenceEventType.TOOL_FAILURE]
            
            total_runs = len(starts)
            completion_rate = len(successes) / total_runs if total_runs > 0 else 0.0
            failure_rate = len(failures) / total_runs if total_runs > 0 else 0.0
            
            latencies = [e.latency_ms for e in events if e.latency_ms is not None]
            avg_latency = sum(latencies) / len(latencies) if latencies else 0
            
            quality_events = [e for e in events if e.event_type == EvidenceEventType.QUALITY_SCORE]
            scores = [e.quality_score for e in quality_events if e.quality_score is not None]
            avg_quality = sum(scores) / len(scores) if scores else None
            
            total_credits = sum(e.credit_cost or 0 for e in events)
            
            return {
                "session_id": session_id,
                "has_data": True,
                "total_tool_runs": total_runs,
                "completion_rate": round(completion_rate, 3),
                "failure_rate": round(failure_rate, 3),
                "avg_latency_ms": round(avg_latency, 1),
                "avg_quality_score": round(avg_quality, 2) if avg_quality else None,
                "total_credits": total_credits,
                "event_count": len(events),
            }
            
        except Exception as e:
            logger.exception("Failed to get session metrics", extra={"error": str(e)})
            return {"session_id": session_id, "has_data": False, "error": str(e)}
    
    def get_tool_metrics(self, tool_name: str) -> Dict[str, Any]:
        """Get aggregated metrics for a tool (thread-safe)."""
        try:
            tool_name = validate_tool_name(tool_name)
            
            with self._lock:
                events = [e for e in self._events if e.tool_name == tool_name]
            
            if not events:
                return {"tool_name": tool_name, "has_data": False}
            
            starts = [e for e in events if e.event_type == EvidenceEventType.TOOL_START]
            successes = [e for e in events if e.event_type == EvidenceEventType.TOOL_SUCCESS]
            
            completion_rate = len(successes) / len(starts) if starts else 0.0
            
            latencies = [e.latency_ms for e in successes if e.latency_ms]
            avg_latency = sum(latencies) / len(latencies) if latencies else 0
            
            return {
                "tool_name": tool_name,
                "has_data": True,
                "total_runs": len(starts),
                "completion_rate": round(completion_rate, 3),
                "avg_latency_ms": round(avg_latency, 1),
            }
            
        except Exception as e:
            logger.exception("Failed to get tool metrics", extra={"error": str(e)})
            return {"tool_name": tool_name, "has_data": False, "error": str(e)}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get collector statistics."""
        with self._lock:
            return {
                "total_events": len(self._events),
                "pending_starts": len(self._tool_starts),
                "session_count": len(self._session_event_counts),
                "dropped_count": self._dropped_count,
                "max_events": self._config.max_events,
            }
    
    def _calculate_latency(self, event_id: str) -> Optional[int]:
        """Calculate latency from start time (thread-safe)."""
        with self._lock:
            start_time = self._tool_starts.pop(event_id, None)
        
        if start_time is None:
            return None
        return int((time.perf_counter() - start_time) * 1000)
    
    def _cleanup_stale_starts(self, max_age_seconds: float = 300.0) -> int:
        """Clean up stale pending starts (must hold lock)."""
        now = time.perf_counter()
        stale = [
            eid for eid, start_time in self._tool_starts.items()
            if now - start_time > max_age_seconds
        ]
        for eid in stale:
            del self._tool_starts[eid]
        return len(stale)
    
    def flush_events(self) -> List[EvidenceEvent]:
        """Flush and return all events (thread-safe)."""
        with self._lock:
            events = list(self._events)
            self._events.clear()
            self._session_event_counts.clear()
            return events


# =============================================================================
# Singleton Instance
# =============================================================================

_collector: Optional[EvidenceCollector] = None
_lock = threading.Lock()


def get_evidence_collector() -> EvidenceCollector:
    """Get or create the singleton evidence collector (thread-safe)."""
    global _collector
    if _collector is None:
        with _lock:
            if _collector is None:
                _collector = EvidenceCollector()
    return _collector


# =============================================================================
# Convenience Functions
# =============================================================================

def record_tool_start(session_id: str, tool_name: str, **kwargs) -> str:
    return get_evidence_collector().record_tool_start(session_id, tool_name, **kwargs)

def record_tool_success(event_id: str, session_id: str, tool_name: str, **kwargs) -> None:
    get_evidence_collector().record_tool_success(event_id, session_id, tool_name, **kwargs)

def record_tool_failure(
    event_id: str, session_id: str, tool_name: str, error_code: str, error_message: str, **kwargs
) -> None:
    get_evidence_collector().record_tool_failure(
        event_id, session_id, tool_name, error_code, error_message, **kwargs
    )

def record_quality_score(session_id: str, tool_name: str, score: float, **kwargs) -> None:
    get_evidence_collector().record_quality_score(session_id, tool_name, score, **kwargs)

def get_session_metrics(session_id: str) -> Dict[str, Any]:
    return get_evidence_collector().get_session_metrics(session_id)

def get_tool_metrics(tool_name: str) -> Dict[str, Any]:
    return get_evidence_collector().get_tool_metrics(tool_name)

def get_evidence_stats() -> Dict[str, Any]:
    return get_evidence_collector().get_stats()
