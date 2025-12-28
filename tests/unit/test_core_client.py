"""Unit tests for app.core.client module."""

from unittest.mock import AsyncMock, patch
import os

import pytest

from app.core.client import cleanup_client, get_client


class TestCoreClient:
    """Test the core client module."""

    @pytest.mark.asyncio
    async def test_get_client_creates_client_on_first_call(self):
        """Test that get_client creates a new client on first call with default SSL verify."""
        # Reset the global client
        import app.core.client

        app.core.client._client = None

        # Mock httpx.AsyncClient
        mock_client = AsyncMock()

        with patch("httpx.AsyncClient", return_value=mock_client):
            client = await get_client()

            assert client is mock_client
            # Verify AsyncClient was called with correct timeout and default SSL verify (True)
            import httpx

            httpx.AsyncClient.assert_called_once_with(timeout=10.0, verify=True)

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

    @pytest.mark.asyncio
    async def test_get_client_with_ssl_verify_disabled(self):
        """Test client creation with SSL verification disabled."""
        import app.core.client

        app.core.client._client = None

        mock_client = AsyncMock()

        with (
            patch.dict(os.environ, {"HA_SSL_VERIFY": "false"}),
            patch("httpx.AsyncClient", return_value=mock_client),
        ):
            # Need to reload config to pick up new env var
            import importlib
            import app.config

            importlib.reload(app.config)

            # Re-import after reload
            from app.core.client import get_client as reloaded_get_client

            client = await reloaded_get_client()

            import httpx

            httpx.AsyncClient.assert_called_once_with(timeout=10.0, verify=False)

    @pytest.mark.asyncio
    async def test_get_client_with_custom_ca_cert(self, tmp_path):
        """Test client creation with custom CA certificate."""
        import app.core.client

        app.core.client._client = None

        # Create a temporary CA file
        ca_file = tmp_path / "ca.pem"
        ca_file.write_text("FAKE CA CERTIFICATE")

        mock_client = AsyncMock()

        with (
            patch.dict(os.environ, {"HA_SSL_VERIFY": str(ca_file)}),
            patch("httpx.AsyncClient", return_value=mock_client),
        ):
            import importlib
            import app.config

            importlib.reload(app.config)

            from app.core.client import get_client as reloaded_get_client

            client = await reloaded_get_client()

            import httpx

            httpx.AsyncClient.assert_called_once_with(timeout=10.0, verify=str(ca_file))

    @pytest.mark.asyncio
    async def test_get_client_with_invalid_ca_path_falls_back(self):
        """Test that invalid CA path falls back to system CAs."""
        import app.core.client

        app.core.client._client = None

        mock_client = AsyncMock()

        with (
            patch.dict(os.environ, {"HA_SSL_VERIFY": "/nonexistent/ca.pem"}),
            patch("httpx.AsyncClient", return_value=mock_client),
        ):
            import importlib
            import app.config

            importlib.reload(app.config)

            from app.core.client import get_client as reloaded_get_client

            client = await reloaded_get_client()

            # Should fall back to True (system CAs)
            import httpx

            httpx.AsyncClient.assert_called_once_with(timeout=10.0, verify=True)
