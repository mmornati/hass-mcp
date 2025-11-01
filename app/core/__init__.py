"""Core infrastructure module for hass-mcp.

This module provides shared utilities including:
- HTTP client management
- Decorators for async handlers and error handling
- Type definitions
- Error handling utilities
"""

from app.core.client import cleanup_client, get_client
from app.core.decorators import async_handler, handle_api_errors
from app.core.types import (
    DEFAULT_LEAN_FIELDS,
    DEFAULT_STANDARD_FIELDS,
    DOMAIN_IMPORTANT_ATTRIBUTES,
    F,
    T,
)

__all__ = [
    "cleanup_client",
    "get_client",
    "async_handler",
    "handle_api_errors",
    "DEFAULT_LEAN_FIELDS",
    "DEFAULT_STANDARD_FIELDS",
    "DOMAIN_IMPORTANT_ATTRIBUTES",
    "F",
    "T",
]
