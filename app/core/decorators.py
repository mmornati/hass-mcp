"""Decorators for hass-mcp.

This module provides decorators for async handlers and error handling.
"""

import functools
import inspect
import logging
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar, cast

import httpx

from app.config import HA_TOKEN, HA_URL

logger = logging.getLogger(__name__)

# Generic type variables
F = TypeVar("F", bound=Callable[..., Awaitable[Any]])
T = TypeVar("T")


def handle_api_errors(func: F) -> F:
    """
    Decorator to handle common error cases for Home Assistant API calls.

    This decorator wraps async functions and handles various HTTP errors,
    connection errors, and other exceptions that might occur during API calls.
    It formats errors based on the return type of the decorated function.

    Args:
        func: The async function to decorate

    Returns:
        Wrapped function that handles errors gracefully

    Examples:
        @handle_api_errors
        async def get_entity_state(entity_id: str) -> dict[str, Any]:
            # Function implementation
            pass
    """

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Determine return type from function annotation
        return_type = inspect.signature(func).return_annotation
        return_type_str = str(return_type).lower()
        is_list_return = "list" in return_type_str and "dict" not in return_type_str.split("[")[0]
        is_dict_return = "dict" in return_type_str and not is_list_return

        # Prepare error formatters based on return type
        def format_error(msg: str) -> Any:
            if is_dict_return:
                return {"error": msg}
            if is_list_return:
                return [{"error": msg}]
            return msg

        try:
            # Check if token is available
            if not HA_TOKEN:
                return format_error(
                    "No Home Assistant token provided. Please set HA_TOKEN in .env file."
                )

            # Call the original function
            return await func(*args, **kwargs)
        except httpx.ConnectError:
            return format_error(f"Connection error: Cannot connect to Home Assistant at {HA_URL}")
        except httpx.TimeoutException:
            return format_error(
                f"Timeout error: Home Assistant at {HA_URL} did not respond in time"
            )
        except httpx.HTTPStatusError as e:
            return format_error(
                f"HTTP error: {e.response.status_code} - {e.response.reason_phrase}"
            )
        except httpx.RequestError as e:
            return format_error(f"Error connecting to Home Assistant: {str(e)}")
        except Exception as e:
            return format_error(f"Unexpected error: {str(e)}")

    return cast(F, wrapper)


def async_handler(command_type: str):
    """
    Simple decorator that logs command execution.

    This decorator adds logging to async functions, typically MCP tools,
    to track when commands are executed.

    Args:
        command_type: The type of command (for logging)

    Returns:
        Decorator function

    Examples:
        @async_handler("get_entity")
        async def get_entity_tool(entity_id: str) -> dict[str, Any]:
            # Function implementation
            pass
    """

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            logger.info(f"Executing command: {command_type}")
            return await func(*args, **kwargs)

        return cast(Callable[..., Awaitable[T]], wrapper)

    return decorator
