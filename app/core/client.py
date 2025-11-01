"""HTTP client management for hass-mcp.

This module provides a persistent HTTP client for Home Assistant API calls.
"""

import logging

import httpx

logger = logging.getLogger(__name__)

# HTTP client instance
_client: httpx.AsyncClient | None = None


async def get_client() -> httpx.AsyncClient:
    """
    Get a persistent httpx client for Home Assistant API calls.

    The client is created on first call and reused for subsequent calls.
    This ensures connection pooling and efficient resource usage.

    Returns:
        An httpx.AsyncClient instance

    Examples:
        client = await get_client()
        response = await client.get(url, headers=headers)
    """
    global _client
    if _client is None:
        logger.debug("Creating new HTTP client")
        _client = httpx.AsyncClient(timeout=10.0)
    return _client


async def cleanup_client() -> None:
    """
    Close the HTTP client when shutting down.

    This should be called during application shutdown to properly clean up
    the HTTP client and close any open connections.

    Examples:
        await cleanup_client()
    """
    global _client
    if _client:
        logger.debug("Closing HTTP client")
        await _client.aclose()
        _client = None
