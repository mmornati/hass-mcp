"""Base API class for hass-mcp.

This module provides a base class that implements common patterns for
interacting with the Home Assistant REST API, reducing code duplication.
"""

import logging
from typing import Any, cast

import httpx

from app.config import HA_URL, get_ha_headers
from app.core import get_client

logger = logging.getLogger(__name__)


class BaseAPI:
    """
    Base class for Home Assistant API interactions.

    This class provides common HTTP methods and patterns that are reused
    across different domains (entities, automations, scripts, etc.).

    Example:
        class EntitiesAPI(BaseAPI):
            async def get_state(self, entity_id: str) -> dict[str, Any]:
                return await self.get(f"/api/states/{entity_id}")
    """

    def __init__(self):
        """Initialize the BaseAPI instance."""
        self._client = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = await get_client()
        return self._client

    async def get(
        self, endpoint: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """
        Perform a GET request to the Home Assistant API.

        Args:
            endpoint: API endpoint path (e.g., "/api/states")
            params: Optional query parameters

        Returns:
            Response JSON data (dict or list)

        Raises:
            httpx.HTTPStatusError: If the request fails
            httpx.RequestError: If the request cannot be completed
        """
        client = await self._get_client()
        url = f"{HA_URL}{endpoint}"
        response = await client.get(url, headers=get_ha_headers(), params=params)
        response.raise_for_status()
        return cast(dict[str, Any], response.json())

    async def post(self, endpoint: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Perform a POST request to the Home Assistant API.

        Args:
            endpoint: API endpoint path (e.g., "/api/services/light/turn_on")
            data: Optional JSON payload

        Returns:
            Response JSON data

        Raises:
            httpx.HTTPStatusError: If the request fails
            httpx.RequestError: If the request cannot be completed
        """
        client = await self._get_client()
        url = f"{HA_URL}{endpoint}"
        response = await client.post(url, headers=get_ha_headers(), json=data or {})
        response.raise_for_status()
        return cast(dict[str, Any], response.json())

    async def put(self, endpoint: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Perform a PUT request to the Home Assistant API.

        Args:
            endpoint: API endpoint path
            data: Optional JSON payload

        Returns:
            Response JSON data

        Raises:
            httpx.HTTPStatusError: If the request fails
            httpx.RequestError: If the request cannot be completed
        """
        client = await self._get_client()
        url = f"{HA_URL}{endpoint}"
        response = await client.put(url, headers=get_ha_headers(), json=data or {})
        response.raise_for_status()
        return cast(dict[str, Any], response.json())

    async def delete(self, endpoint: str) -> dict[str, Any]:
        """
        Perform a DELETE request to the Home Assistant API.

        Args:
            endpoint: API endpoint path

        Returns:
            Response JSON data

        Raises:
            httpx.HTTPStatusError: If the request fails
            httpx.RequestError: If the request cannot be completed
        """
        client = await self._get_client()
        url = f"{HA_URL}{endpoint}"
        response = await client.delete(url, headers=get_ha_headers())
        response.raise_for_status()
        return cast(dict[str, Any], response.json())

    async def patch(self, endpoint: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Perform a PATCH request to the Home Assistant API.

        Args:
            endpoint: API endpoint path
            data: Optional JSON payload

        Returns:
            Response JSON data

        Raises:
            httpx.HTTPStatusError: If the request fails
            httpx.RequestError: If the request cannot be completed
        """
        client = await self._get_client()
        url = f"{HA_URL}{endpoint}"
        response = await client.patch(url, headers=get_ha_headers(), json=data or {})
        response.raise_for_status()
        return cast(dict[str, Any], response.json())
