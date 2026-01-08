"""HTTP client management for hass-mcp.

This module provides a persistent HTTP client for Home Assistant API calls.
"""

import logging

import httpx

from app.config import get_ssl_verify_value

logger = logging.getLogger(__name__)

# HTTP client instance
_client: httpx.AsyncClient | None = None


async def get_client() -> httpx.AsyncClient:
    """
    Get a persistent httpx client for Home Assistant API calls.

    The client is created on first call and reused for subsequent calls.
    This ensures connection pooling and efficient resource usage.

    SSL/TLS verification is configured via the HA_SSL_VERIFY environment variable:
    - "true" (default): Use system CA certificates
    - "false": Disable SSL verification (useful for self-signed certificates)
    - "/path/to/ca.pem": Use custom CA certificate bundle

    Returns:
        An httpx.AsyncClient instance

    Examples:
        client = await get_client()
        response = await client.get(url, headers=headers)
    """
    global _client
    if _client is None:
        ssl_verify = get_ssl_verify_value()
        logger.debug(f"Creating new HTTP client with SSL verify: {ssl_verify}")
        _client = httpx.AsyncClient(timeout=10.0, verify=ssl_verify)
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
