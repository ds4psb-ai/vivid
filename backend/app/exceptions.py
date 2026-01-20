"""
Custom Exceptions with RFC 9457 Problem Details Support (H3.3)

This module provides:
- VividException: Base exception with RFC 9457 problem details
- Domain-specific exception classes
- Helper functions for exception handling

Usage:
    from app.exceptions import InsufficientCreditsError, TokenExpiredError

    # In router
    raise InsufficientCreditsError(required=100, available=50)

    # In service
    if not has_enough_credits:
        raise InsufficientCreditsError(required=credits_needed, available=user_credits)
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import HTTPException

from app.schemas.problem_details import ProblemDetail, ProblemTypes


class VividException(HTTPException):
    """
    Base exception with RFC 9457 problem details.

    All Vivid exceptions should inherit from this class to ensure
    consistent error responses with proper problem details formatting.
    """

    def __init__(
        self,
        status_code: int,
        problem_type: str,
        title: str,
        detail: Optional[str] = None,
        error_code: Optional[str] = None,
        **extensions: Any,
    ):
        """
        Initialize a Vivid exception.

        Args:
            status_code: HTTP status code
            problem_type: RFC 9457 problem type URI
            title: Short human-readable title
            detail: Detailed error message
            error_code: Machine-readable error code
            **extensions: Additional extension fields
        """
        self.problem = ProblemDetail(
            type=problem_type,
            title=title,
            status=status_code,
            detail=detail,
            error_code=error_code,
            **extensions,
        )
        super().__init__(
            status_code=status_code,
            detail=self.problem.model_dump(mode="json", exclude_none=True),
        )


# =============================================================================
# Credit/Billing Exceptions
# =============================================================================

class InsufficientCreditsError(VividException):
    """Raised when user doesn't have enough credits for an operation."""

    def __init__(self, required: int, available: int):
        super().__init__(
            status_code=402,
            problem_type=ProblemTypes.INSUFFICIENT_CREDITS,
            title="Insufficient Credits",
            detail=f"This operation requires {required} credits, but you only have {available}",
            error_code="INSUFFICIENT_CREDITS",
            required_credits=required,
            available_credits=available,
            title_i18n_key="errors.INSUFFICIENT_CREDITS.title",
            detail_i18n_key="errors.INSUFFICIENT_CREDITS.detail",
        )
        self.required = required
        self.available = available


class TokenExpiredError(VividException):
    """Raised when run token has expired."""

    def __init__(self, token_id: str):
        super().__init__(
            status_code=400,
            problem_type=ProblemTypes.TOKEN_EXPIRED,
            title="Token Expired",
            detail=f"Run token '{token_id}' has expired",
            error_code="TOKEN_EXPIRED",
            token_id=token_id,
            title_i18n_key="errors.TOKEN_EXPIRED.title",
        )
        self.token_id = token_id


class SubscriptionRequiredError(VividException):
    """Raised when a subscription is required for an operation."""

    def __init__(self, feature: str):
        super().__init__(
            status_code=402,
            problem_type=ProblemTypes.SUBSCRIPTION_REQUIRED,
            title="Subscription Required",
            detail=f"A subscription is required to access '{feature}'",
            error_code="SUBSCRIPTION_REQUIRED",
            required_feature=feature,
            title_i18n_key="errors.SUBSCRIPTION_REQUIRED.title",
        )
        self.feature = feature


# =============================================================================
# Rate Limiting Exception
# =============================================================================

class RateLimitedError(VividException):
    """Raised when rate limit is exceeded."""

    def __init__(self, retry_after: int, limit_type: str = "requests"):
        super().__init__(
            status_code=429,
            problem_type=ProblemTypes.RATE_LIMITED,
            title="Rate Limit Exceeded",
            detail=f"Too many {limit_type}. Please retry after {retry_after} seconds",
            error_code="RATE_LIMITED",
            retry_after=retry_after,
            limit_type=limit_type,
            title_i18n_key="errors.RATE_LIMITED.title",
        )
        self.retry_after = retry_after
        self.limit_type = limit_type


# =============================================================================
# Authentication/Authorization Exceptions
# =============================================================================

class AuthenticationRequiredError(VividException):
    """Raised when authentication is required but not provided."""

    def __init__(self, detail: str = "Authentication is required"):
        super().__init__(
            status_code=401,
            problem_type=ProblemTypes.AUTHENTICATION_REQUIRED,
            title="Authentication Required",
            detail=detail,
            error_code="AUTHENTICATION_REQUIRED",
            title_i18n_key="errors.AUTHENTICATION_REQUIRED.title",
        )


class PermissionDeniedError(VividException):
    """Raised when user lacks permission for an operation."""

    def __init__(self, resource: str = None, action: str = None):
        detail = "You don't have permission to perform this action"
        if resource and action:
            detail = f"You don't have permission to {action} on {resource}"

        super().__init__(
            status_code=403,
            problem_type=ProblemTypes.PERMISSION_DENIED,
            title="Permission Denied",
            detail=detail,
            error_code="PERMISSION_DENIED",
            resource=resource,
            action=action,
            title_i18n_key="errors.PERMISSION_DENIED.title",
        )
        self.resource = resource
        self.action = action


class TokenInvalidError(VividException):
    """Raised when authentication token is invalid."""

    def __init__(self, reason: str = "Token is invalid or malformed"):
        super().__init__(
            status_code=401,
            problem_type=ProblemTypes.TOKEN_INVALID,
            title="Invalid Token",
            detail=reason,
            error_code="TOKEN_INVALID",
            title_i18n_key="errors.TOKEN_INVALID.title",
        )


# =============================================================================
# Resource Exceptions
# =============================================================================

class ResourceNotFoundError(VividException):
    """Raised when a requested resource is not found."""

    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            status_code=404,
            problem_type=ProblemTypes.RESOURCE_NOT_FOUND,
            title="Resource Not Found",
            detail=f"{resource_type} with id '{resource_id}' not found",
            error_code="RESOURCE_NOT_FOUND",
            resource_type=resource_type,
            resource_id=resource_id,
            title_i18n_key="errors.RESOURCE_NOT_FOUND.title",
        )
        self.resource_type = resource_type
        self.resource_id = resource_id


class ResourceConflictError(VividException):
    """Raised when there's a conflict with the current resource state."""

    def __init__(self, resource_type: str, detail: str):
        super().__init__(
            status_code=409,
            problem_type=ProblemTypes.RESOURCE_CONFLICT,
            title="Resource Conflict",
            detail=detail,
            error_code="RESOURCE_CONFLICT",
            resource_type=resource_type,
            title_i18n_key="errors.RESOURCE_CONFLICT.title",
        )
        self.resource_type = resource_type


# =============================================================================
# Capsule/Execution Exceptions
# =============================================================================

class CapsuleExecutionError(VividException):
    """Raised when capsule execution fails."""

    def __init__(self, capsule_id: str, reason: str):
        super().__init__(
            status_code=500,
            problem_type=ProblemTypes.CAPSULE_EXECUTION_FAILED,
            title="Capsule Execution Failed",
            detail=f"Failed to execute capsule: {reason}",
            error_code="CAPSULE_EXECUTION_FAILED",
            capsule_id=capsule_id,
            title_i18n_key="errors.CAPSULE_EXECUTION_FAILED.title",
        )
        self.capsule_id = capsule_id
        self.reason = reason


class GenerationError(VividException):
    """Raised when content generation fails."""

    def __init__(self, provider: str, reason: str):
        super().__init__(
            status_code=500,
            problem_type=ProblemTypes.GENERATION_FAILED,
            title="Generation Failed",
            detail=f"Content generation failed: {reason}",
            error_code="GENERATION_FAILED",
            provider=provider,
            title_i18n_key="errors.GENERATION_FAILED.title",
        )
        self.provider = provider
        self.reason = reason


class RAGQueryError(VividException):
    """Raised when RAG query fails."""

    def __init__(self, reason: str, dimension: str = None):
        super().__init__(
            status_code=500,
            problem_type=ProblemTypes.RAG_QUERY_FAILED,
            title="RAG Query Failed",
            detail=f"RAG query failed: {reason}",
            error_code="RAG_QUERY_FAILED",
            dimension=dimension,
            title_i18n_key="errors.RAG_QUERY_FAILED.title",
        )
        self.reason = reason
        self.dimension = dimension


# =============================================================================
# External Service Exceptions
# =============================================================================

class ServiceUnavailableError(VividException):
    """Raised when a required service is unavailable."""

    def __init__(self, service: str, retry_after: int = None):
        detail = f"Service '{service}' is currently unavailable"
        if retry_after:
            detail += f". Please retry after {retry_after} seconds"

        super().__init__(
            status_code=503,
            problem_type=ProblemTypes.SERVICE_UNAVAILABLE,
            title="Service Unavailable",
            detail=detail,
            error_code="SERVICE_UNAVAILABLE",
            service=service,
            retry_after=retry_after,
            title_i18n_key="errors.SERVICE_UNAVAILABLE.title",
        )
        self.service = service
        self.retry_after = retry_after


class UpstreamError(VividException):
    """Raised when an upstream service returns an error."""

    def __init__(self, service: str, upstream_status: int = None):
        super().__init__(
            status_code=502,
            problem_type=ProblemTypes.UPSTREAM_ERROR,
            title="Upstream Error",
            detail=f"Upstream service '{service}' returned an error",
            error_code="UPSTREAM_ERROR",
            service=service,
            upstream_status=upstream_status,
            title_i18n_key="errors.UPSTREAM_ERROR.title",
        )
        self.service = service
        self.upstream_status = upstream_status


class TimeoutError(VividException):
    """Raised when an operation times out."""

    def __init__(self, operation: str, timeout_seconds: int):
        super().__init__(
            status_code=504,
            problem_type=ProblemTypes.TIMEOUT,
            title="Operation Timeout",
            detail=f"Operation '{operation}' timed out after {timeout_seconds} seconds",
            error_code="TIMEOUT",
            operation=operation,
            timeout_seconds=timeout_seconds,
            title_i18n_key="errors.TIMEOUT.title",
        )
        self.operation = operation
        self.timeout_seconds = timeout_seconds


# =============================================================================
# Validation Exception
# =============================================================================

class ValidationError(VividException):
    """Raised when request validation fails."""

    def __init__(self, errors: list, detail: str = "Request validation failed"):
        super().__init__(
            status_code=422,
            problem_type=ProblemTypes.VALIDATION_ERROR,
            title="Validation Error",
            detail=detail,
            error_code="VALIDATION_ERROR",
            errors=errors,
            title_i18n_key="errors.VALIDATION_ERROR.title",
        )
        self.errors = errors
