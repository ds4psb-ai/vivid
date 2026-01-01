"""
Structured Logging Configuration

Provides JSON-formatted logging with request context, timing, and error tracking.
Uses Python's structlog for structured logging output.
"""
import logging
import sys
import time
from contextvars import ContextVar
from functools import wraps
from typing import Any, Callable, Optional
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Context variables for request tracking
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")
user_id_ctx: ContextVar[str] = ContextVar("user_id", default="")


class StructuredFormatter(logging.Formatter):
    """JSON-style structured log formatter."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add request context if available
        if request_id := request_id_ctx.get():
            log_data["request_id"] = request_id
        if user_id := user_id_ctx.get():
            log_data["user_id"] = user_id
            
        # Add extra fields
        if hasattr(record, "extra"):
            log_data.update(record.extra)
            
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
            
        import json
        return json.dumps(log_data, ensure_ascii=False, default=str)


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Configure structured logging for the application."""
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Add structured handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(handler)
    
    # Silence noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name."""
    return logging.getLogger(name)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request logging with timing."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid4())[:8]
        request_id_ctx.set(request_id)
        
        # Get user ID from header
        user_id = request.headers.get("X-User-Id", "")
        user_id_ctx.set(user_id)
        
        # Start timing
        start_time = time.perf_counter()
        
        # Get logger
        logger = get_logger("http")
        
        # Log request
        logger.info(
            f"{request.method} {request.url.path}",
            extra={
                "type": "request",
                "method": request.method,
                "path": request.url.path,
                "query": str(request.query_params),
            }
        )
        
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            
            # Log response
            log_level = logging.WARNING if response.status_code >= 400 else logging.INFO
            logger.log(
                log_level,
                f"{request.method} {request.url.path} → {response.status_code}",
                extra={
                    "type": "response",
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                    "duration_ms": duration_ms,
                }
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as exc:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            logger.error(
                f"{request.method} {request.url.path} → Error",
                extra={
                    "type": "error",
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(exc),
                    "duration_ms": duration_ms,
                },
                exc_info=True,
            )
            raise


def log_function(logger_name: str = "app"):
    """Decorator for logging function calls with timing."""
    def decorator(func: Callable) -> Callable:
        logger = get_logger(logger_name)
        
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                duration_ms = int((time.perf_counter() - start_time) * 1000)
                logger.debug(
                    f"{func.__name__} completed",
                    extra={
                        "type": "function",
                        "function": func.__name__,
                        "duration_ms": duration_ms,
                    }
                )
                return result
            except Exception as exc:
                duration_ms = int((time.perf_counter() - start_time) * 1000)
                logger.error(
                    f"{func.__name__} failed",
                    extra={
                        "type": "function_error",
                        "function": func.__name__,
                        "error": str(exc),
                        "duration_ms": duration_ms,
                    },
                    exc_info=True,
                )
                raise
                
        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                duration_ms = int((time.perf_counter() - start_time) * 1000)
                logger.debug(
                    f"{func.__name__} completed",
                    extra={
                        "type": "function",
                        "function": func.__name__,
                        "duration_ms": duration_ms,
                    }
                )
                return result
            except Exception as exc:
                duration_ms = int((time.perf_counter() - start_time) * 1000)
                logger.error(
                    f"{func.__name__} failed",
                    extra={
                        "type": "function_error",
                        "function": func.__name__,
                        "error": str(exc),
                        "duration_ms": duration_ms,
                    },
                    exc_info=True,
                )
                raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator
