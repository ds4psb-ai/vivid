"""
RFC 9457 Problem Details for HTTP APIs (H3.3)

Reference: https://datatracker.ietf.org/doc/rfc9457/
Supersedes: RFC 7807

This module provides:
- ProblemDetail: RFC 9457 compliant error response schema
- ProblemTypes: Standard problem type URIs for Vivid
- Helper functions for creating problem details
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ProblemDetail(BaseModel):
    """
    RFC 9457 compliant problem detail response.

    Standard Members:
    - type: URI reference identifying problem type
    - title: Short human-readable summary
    - status: HTTP status code
    - detail: Human-readable explanation specific to this occurrence
    - instance: URI reference identifying specific occurrence

    Vivid Extensions:
    - error_code: Machine-readable error code
    - request_id: Request tracking ID for support
    - timestamp: Error occurrence timestamp
    - title_i18n_key: i18n key for title localization
    - detail_i18n_key: i18n key for detail localization
    """

    # RFC 9457 Required fields
    type: str = Field(
        default="about:blank",
        description="URI reference identifying problem type"
    )
    title: str = Field(
        description="Short human-readable summary"
    )
    status: int = Field(
        description="HTTP status code"
    )

    # RFC 9457 Optional fields
    detail: Optional[str] = Field(
        default=None,
        description="Human-readable explanation specific to this occurrence"
    )
    instance: Optional[str] = Field(
        default=None,
        description="URI reference identifying specific occurrence"
    )

    # Vivid extensions
    error_code: Optional[str] = Field(
        default=None,
        description="Machine-readable error code (e.g., INSUFFICIENT_CREDITS)"
    )
    request_id: Optional[str] = Field(
        default=None,
        description="Request tracking ID for support"
    )
    timestamp: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        description="Error occurrence timestamp"
    )

    # i18n support
    title_i18n_key: Optional[str] = Field(
        default=None,
        description="i18n key for title localization"
    )
    detail_i18n_key: Optional[str] = Field(
        default=None,
        description="i18n key for detail localization"
    )

    # Additional extension fields (for domain-specific data)
    errors: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Validation errors array (for 422 responses)"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "type": "https://vivid.crebit.io/errors/insufficient-credits",
                "title": "Insufficient Credits",
                "status": 402,
                "detail": "This operation requires 100 credits, but you only have 50",
                "instance": "/api/v1/capsules/run/abc123",
                "error_code": "INSUFFICIENT_CREDITS",
                "request_id": "req_abc123",
                "timestamp": "2026-01-20T12:00:00Z"
            }
        }
    }


class ProblemTypes:
    """
    Standard problem type URIs for Vivid.

    All problem types are documented at: https://vivid.crebit.io/errors/
    """

    BASE = "https://vivid.crebit.io/errors"

    # Credit/Billing Errors (4xx)
    INSUFFICIENT_CREDITS = f"{BASE}/insufficient-credits"
    TOKEN_EXPIRED = f"{BASE}/token-expired"
    SUBSCRIPTION_REQUIRED = f"{BASE}/subscription-required"

    # Rate Limiting (429)
    RATE_LIMITED = f"{BASE}/rate-limited"

    # Validation Errors (422)
    VALIDATION_ERROR = f"{BASE}/validation-error"
    INVALID_INPUT = f"{BASE}/invalid-input"

    # Authentication/Authorization (401, 403)
    AUTHENTICATION_REQUIRED = f"{BASE}/authentication-required"
    PERMISSION_DENIED = f"{BASE}/permission-denied"
    TOKEN_INVALID = f"{BASE}/token-invalid"

    # Resource Errors (404, 409, 410)
    RESOURCE_NOT_FOUND = f"{BASE}/resource-not-found"
    RESOURCE_CONFLICT = f"{BASE}/resource-conflict"
    RESOURCE_GONE = f"{BASE}/resource-gone"

    # Capsule/Execution Errors (5xx)
    CAPSULE_EXECUTION_FAILED = f"{BASE}/capsule-execution-failed"
    GENERATION_FAILED = f"{BASE}/generation-failed"
    RAG_QUERY_FAILED = f"{BASE}/rag-query-failed"

    # External Service Errors (502, 503, 504)
    SERVICE_UNAVAILABLE = f"{BASE}/service-unavailable"
    UPSTREAM_ERROR = f"{BASE}/upstream-error"
    TIMEOUT = f"{BASE}/timeout"

    # Internal Errors (500)
    INTERNAL_ERROR = f"{BASE}/internal-error"


def create_problem_detail(
    status: int,
    title: str,
    detail: Optional[str] = None,
    problem_type: str = "about:blank",
    error_code: Optional[str] = None,
    request_id: Optional[str] = None,
    instance: Optional[str] = None,
    **extensions: Any,
) -> ProblemDetail:
    """
    Factory function to create a ProblemDetail instance.

    Args:
        status: HTTP status code
        title: Short error title
        detail: Detailed error message
        problem_type: Problem type URI
        error_code: Machine-readable error code
        request_id: Request ID for tracking
        instance: Request path/URI
        **extensions: Additional extension fields

    Returns:
        ProblemDetail instance
    """
    return ProblemDetail(
        type=problem_type,
        title=title,
        status=status,
        detail=detail,
        instance=instance,
        error_code=error_code,
        request_id=request_id,
        **extensions,
    )


# Common problem detail factories
def insufficient_credits(required: int, available: int, request_id: str = None) -> ProblemDetail:
    """Create problem detail for insufficient credits."""
    return ProblemDetail(
        type=ProblemTypes.INSUFFICIENT_CREDITS,
        title="Insufficient Credits",
        status=402,
        detail=f"This operation requires {required} credits, but you only have {available}",
        error_code="INSUFFICIENT_CREDITS",
        request_id=request_id,
        title_i18n_key="errors.INSUFFICIENT_CREDITS.title",
        detail_i18n_key="errors.INSUFFICIENT_CREDITS.detail",
    )


def rate_limited(retry_after: int, request_id: str = None) -> ProblemDetail:
    """Create problem detail for rate limiting."""
    return ProblemDetail(
        type=ProblemTypes.RATE_LIMITED,
        title="Rate Limit Exceeded",
        status=429,
        detail=f"Too many requests. Please retry after {retry_after} seconds",
        error_code="RATE_LIMITED",
        request_id=request_id,
        title_i18n_key="errors.RATE_LIMITED.title",
        detail_i18n_key="errors.RATE_LIMITED.detail",
    )


def validation_error(errors: List[Dict[str, Any]], request_id: str = None) -> ProblemDetail:
    """Create problem detail for validation errors."""
    return ProblemDetail(
        type=ProblemTypes.VALIDATION_ERROR,
        title="Validation Error",
        status=422,
        detail="Request validation failed",
        error_code="VALIDATION_ERROR",
        request_id=request_id,
        errors=errors,
        title_i18n_key="errors.VALIDATION_ERROR.title",
    )


def resource_not_found(resource_type: str, resource_id: str, request_id: str = None) -> ProblemDetail:
    """Create problem detail for not found errors."""
    return ProblemDetail(
        type=ProblemTypes.RESOURCE_NOT_FOUND,
        title="Resource Not Found",
        status=404,
        detail=f"{resource_type} with id '{resource_id}' not found",
        error_code="RESOURCE_NOT_FOUND",
        request_id=request_id,
        title_i18n_key="errors.RESOURCE_NOT_FOUND.title",
    )


def internal_error(request_id: str = None, detail: str = None) -> ProblemDetail:
    """Create problem detail for internal server errors."""
    return ProblemDetail(
        type=ProblemTypes.INTERNAL_ERROR,
        title="Internal Server Error",
        status=500,
        detail=detail or "An unexpected error occurred",
        error_code="INTERNAL_ERROR",
        request_id=request_id,
        title_i18n_key="errors.INTERNAL_ERROR.title",
    )
