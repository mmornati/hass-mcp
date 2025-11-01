"""Unit tests for app.api.integrations module."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.api.integrations import (
    get_integration_config,
    get_integrations,
    reload_integration,
)


class TestGetIntegrations:
    """Test the get_integrations function."""

    @pytest.fixture(autouse=True)
    def mock_config(self):
        """Mock HA_URL and HA_TOKEN for all tests in this class."""
        with (
            patch("app.config.HA_URL", "http://localhost:8123"),
            patch("app.config.HA_TOKEN", "test_token"),
            patch("app.core.decorators.HA_TOKEN", "test_token"),
        ):
            yield

    @pytest.mark.asyncio
    async def test_get_integrations_success(self):
        """Test successful retrieval of all integrations."""
        mock_integrations = [
            {
                "entry_id": "abc123",
                "domain": "mqtt",
                "title": "MQTT",
                "source": "user",
                "state": "loaded",
            },
            {
                "entry_id": "def456",
                "domain": "zwave",
                "title": "Z-Wave",
                "source": "user",
                "state": "loaded",
            },
        ]

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = mock_integrations
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("app.api.integrations.get_client", return_value=mock_client):
            result = await get_integrations()

            assert isinstance(result, list)
            assert len(result) == 2
            assert result[0]["domain"] == "mqtt"
            assert result[1]["domain"] == "zwave"
            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert call_args[0][0] == "http://localhost:8123/api/config/config_entries/entry"

    @pytest.mark.asyncio
    async def test_get_integrations_with_domain_filter(self):
        """Test retrieval of integrations filtered by domain."""
        mock_all_integrations = [
            {
                "entry_id": "abc123",
                "domain": "mqtt",
                "title": "MQTT",
                "source": "user",
                "state": "loaded",
            },
            {
                "entry_id": "def456",
                "domain": "zwave",
                "title": "Z-Wave",
                "source": "user",
                "state": "loaded",
            },
        ]

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = mock_all_integrations
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("app.api.integrations.get_client", return_value=mock_client):
            result = await get_integrations(domain="mqtt")

            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["domain"] == "mqtt"
            assert result[0]["entry_id"] == "abc123"

    @pytest.mark.asyncio
    async def test_get_integrations_empty(self):
        """Test retrieval when no integrations are found."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("app.api.integrations.get_client", return_value=mock_client):
            result = await get_integrations()
            assert result == []

    @pytest.mark.asyncio
    async def test_get_integrations_http_error(self):
        """Test handling of HTTP error."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Internal Server Error",
            request=httpx.Request("GET", "url"),
            response=mock_response,
        )
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("app.api.integrations.get_client", return_value=mock_client):
            result = await get_integrations()
            # Error handler returns list for list return types: [{"error": msg}]
            assert isinstance(result, list)
            assert len(result) == 1
            assert "error" in result[0]
            assert "HTTP error: 500" in result[0]["error"]


class TestGetIntegrationConfig:
    """Test the get_integration_config function."""

    @pytest.fixture(autouse=True)
    def mock_config(self):
        """Mock HA_URL and HA_TOKEN for all tests in this class."""
        with (
            patch("app.config.HA_URL", "http://localhost:8123"),
            patch("app.config.HA_TOKEN", "test_token"),
            patch("app.core.decorators.HA_TOKEN", "test_token"),
        ):
            yield

    @pytest.mark.asyncio
    async def test_get_integration_config_success(self):
        """Test successful retrieval of integration configuration."""
        mock_config = {
            "entry_id": "abc123",
            "domain": "mqtt",
            "title": "MQTT",
            "source": "user",
            "state": "loaded",
            "options": {"broker": "localhost", "port": 1883},
        }

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = mock_config
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("app.api.integrations.get_client", return_value=mock_client):
            result = await get_integration_config("abc123")

            assert isinstance(result, dict)
            assert result["entry_id"] == "abc123"
            assert result["domain"] == "mqtt"
            assert result["options"] == {"broker": "localhost", "port": 1883}
            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert call_args[0][0] == "http://localhost:8123/api/config/config_entries/entry/abc123"

    @pytest.mark.asyncio
    async def test_get_integration_config_not_found(self):
        """Test handling of integration not found."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not Found",
            request=httpx.Request("GET", "url"),
            response=mock_response,
        )
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("app.api.integrations.get_client", return_value=mock_client):
            result = await get_integration_config("nonexistent")
            assert "error" in result
            assert "HTTP error: 404" in result["error"]


class TestReloadIntegration:
    """Test the reload_integration function."""

    @pytest.fixture(autouse=True)
    def mock_config(self):
        """Mock HA_URL and HA_TOKEN for all tests in this class."""
        with (
            patch("app.config.HA_URL", "http://localhost:8123"),
            patch("app.config.HA_TOKEN", "test_token"),
            patch("app.core.decorators.HA_TOKEN", "test_token"),
        ):
            yield

    @pytest.mark.asyncio
    async def test_reload_integration_success(self):
        """Test successful reload of an integration."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.api.integrations.get_client", return_value=mock_client):
            result = await reload_integration("abc123")

            assert isinstance(result, list)
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[0][0] == "http://localhost:8123/api/services/config/reload_entry"
            assert call_args[1]["json"] == {"entry_id": "abc123"}

    @pytest.mark.asyncio
    async def test_reload_integration_http_error(self):
        """Test handling of HTTP error during reload."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Internal Server Error",
            request=httpx.Request("POST", "url"),
            response=mock_response,
        )
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.api.integrations.get_client", return_value=mock_client):
            result = await reload_integration("abc123")
            assert "error" in result
            assert "HTTP error: 500" in result["error"]
