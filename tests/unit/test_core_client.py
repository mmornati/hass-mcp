"""Unit tests for app.core.client module."""

from unittest.mock import AsyncMock, patch

import pytest

from app.core.client import cleanup_client, get_client


class TestCoreClient:
    """Test the core client module."""

    @pytest.mark.asyncio
    async def test_get_client_creates_client_on_first_call(self):
        """Test that get_client creates a new client on first call."""
        # Reset the global client
        import app.core.client

        app.core.client._client = None

        # Mock httpx.AsyncClient
        mock_client = AsyncMock()

        with patch("httpx.AsyncClient", return_value=mock_client):
            client = await get_client()

            assert client is mock_client
            # Verify AsyncClient was called with correct timeout
            import httpx

            httpx.AsyncClient.assert_called_once_with(timeout=10.0)

    @pytest.mark.asyncio
    async def test_get_client_reuses_existing_client(self):
        """Test that get_client reuses existing client."""
        import app.core.client

        # Create a mock client
        mock_client = AsyncMock()
        app.core.client._client = mock_client

        # Call get_client
        client = await get_client()

        # Should return the same client
        assert client is mock_client

    @pytest.mark.asyncio
    async def test_cleanup_client_closes_existing_client(self):
        """Test that cleanup_client closes the client."""
        import app.core.client

        # Create a mock client
        mock_client = AsyncMock()
        app.core.client._client = mock_client

        # Call cleanup_client
        await cleanup_client()

        # Verify client was closed
        mock_client.aclose.assert_called_once()

        # Verify client was set to None
        assert app.core.client._client is None

    @pytest.mark.asyncio
    async def test_cleanup_client_handles_none_client(self):
        """Test that cleanup_client handles None client gracefully."""
        import app.core.client

        # Set client to None
        app.core.client._client = None

        # Should not raise an error
        await cleanup_client()

        # Client should still be None
        assert app.core.client._client is None
