"""
Request Tracker Middleware

Tracks in-flight requests for graceful shutdown.
Returns 503 Service Unavailable during shutdown.

Usage:
    from app.middleware.request_tracker import RequestTrackerMiddleware

    app.add_middleware(RequestTrackerMiddleware)
"""
from __future__ import annotations

import logging
import uuid
from typing import Callable

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.schemas.problem_details import ProblemDetail, ProblemTypes
from app.services.shutdown_manager import get_shutdown_manager

logger = logging.getLogger(__name__)


class RequestTrackerMiddleware(BaseHTTPMiddleware):
    """
    Middleware that tracks requests for graceful shutdown.

    Features:
    - Generates request ID if not present
    - Tracks in-flight requests
    - Returns 503 during shutdown
    - Untracks requests on completion
    """

    def __init__(self, app):
        super().__init__(app)
        self._shutdown_manager = get_shutdown_manager()

    async def dispatch(self, request: Request, call_next: Callable):
        """Process request with tracking."""
        # Get or generate request ID
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())

        # Check if shutting down
        if self._shutdown_manager.is_shutting_down:
            logger.info(f"[SHUTDOWN] Rejecting request during shutdown: {request_id}")

            problem = ProblemDetail(
                type=ProblemTypes.SERVICE_UNAVAILABLE,
                title="Service Unavailable",
                status=503,
                detail="Server is shutting down. Please retry later.",
                error_code="SHUTDOWN_IN_PROGRESS",
            )

            return JSONResponse(
                status_code=503,
                content=problem.model_dump(mode="json", exclude_none=True),
                media_type="application/problem+json",
                headers={
                    "Retry-After": "30",
                    "X-Request-ID": request_id,
                },
            )

        # Track the request
        tracked = self._shutdown_manager.track_request(
            request_id=request_id,
            path=str(request.url.path),
            method=request.method,
        )

        if not tracked:
            # Failed to track (shouldn't happen, but handle gracefully)
            problem = ProblemDetail(
                type=ProblemTypes.SERVICE_UNAVAILABLE,
                title="Service Unavailable",
                status=503,
                detail="Server is not accepting requests.",
                error_code="REQUEST_REJECTED",
            )

            return JSONResponse(
                status_code=503,
                content=problem.model_dump(mode="json", exclude_none=True),
                media_type="application/problem+json",
            )

        try:
            # Process the request
            response = await call_next(request)

            # Add request ID to response
            response.headers["X-Request-ID"] = request_id

            return response

        finally:
            # Always untrack the request
            self._shutdown_manager.untrack_request(request_id)
