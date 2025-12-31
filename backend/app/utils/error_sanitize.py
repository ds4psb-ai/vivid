"""
Error Message Sanitization Utilities
====================================
Prevents sensitive information from being exposed in API error responses.

Usage:
    from app.utils.error_sanitize import sanitize_error_message

    raise HTTPException(status_code=500, detail=sanitize_error_message(e, "Operation failed"))
"""
import re
from typing import Optional


# Patterns that indicate sensitive information
SENSITIVE_PATTERNS = [
    r"password",
    r"secret",
    r"token",
    r"api[_-]?key",
    r"credential",
    r"auth",
    r"/[a-zA-Z0-9_-]+/\.[a-zA-Z]+",  # File paths
    r"@[\w.-]+\.[a-zA-Z]{2,}",  # Email addresses
    r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",  # IP addresses
    r"postgres(ql)?://",  # Database URLs
    r"redis://",  # Redis URLs
    r"mongodb://",  # MongoDB URLs
    r"traceback",
    r"File \"",  # Python traceback
    r"line \d+",  # Python traceback line numbers
]

# Compile patterns for efficiency
_SENSITIVE_RE = re.compile("|".join(SENSITIVE_PATTERNS), re.IGNORECASE)


def sanitize_error_message(
    error: Exception,
    fallback_message: str = "An error occurred. Please try again.",
    include_type: bool = False,
) -> str:
    """
    Sanitize an exception message for safe exposure in API responses.
    
    Args:
        error: The exception that was caught
        fallback_message: Message to use if original is sensitive
        include_type: If True, includes exception type name
    
    Returns:
        A safe error message that doesn't expose sensitive information
    """
    error_str = str(error)
    
    # Check for sensitive patterns
    if _SENSITIVE_RE.search(error_str):
        # Log the real error internally (would go to structured logging)
        return fallback_message
    
    # If error message is too long, it might contain stack traces
    if len(error_str) > 500:
        return fallback_message
    
    # If error contains newlines, it might be a multi-line traceback
    if "\n" in error_str:
        return fallback_message
    
    # Safe to include, optionally with type
    if include_type:
        return f"{type(error).__name__}: {error_str}"
    
    return error_str


def safe_error_detail(
    error: Exception,
    operation: str = "Operation",
    generic_only: bool = False,
) -> str:
    """
    Create a safe HTTP detail message for an operation failure.
    
    Args:
        error: The exception that was caught
        operation: Name of the operation that failed (e.g., "Search", "Upload")
        generic_only: If True, always returns generic message
    
    Returns:
        A safe detail string for HTTPException
    """
    if generic_only:
        return f"{operation} failed. Please try again or contact support."
    
    safe_msg = sanitize_error_message(error)
    return f"{operation} failed: {safe_msg}"


# Pre-defined safe messages for common operations
SAFE_MESSAGES = {
    "search": "Search failed. Please try again.",
    "seeding": "Data seeding failed. Please contact support.",
    "database": "Database operation failed. Please try again.",
    "auth": "Authentication failed. Please log in again.",
    "payment": "Payment processing failed. Please try again.",
    "upload": "Upload failed. Please check your file and try again.",
    "generation": "Generation failed. Please try again.",
}
