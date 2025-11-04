"""Unit tests for app.api.system module."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.api.system import (
    get_core_config,
    get_hass_error_log,
    get_hass_version,
    get_system_health,
    get_system_overview,
    restart_home_assistant,
)
from app.core.cache.manager import get_cache_manager


class TestGetHassVersion:
    """Test the get_hass_version function."""

    @pytest.fixture(autouse=True)
    def mock_config(self):
        """Mock HA_URL and HA_TOKEN for all tests in this class."""
        with (
            patch("app.config.HA_URL", "http://localhost:8123"),
            patch("app.config.HA_TOKEN", "test_token"),
            patch("app.core.decorators.HA_TOKEN", "test_token"),
        ):
            yield

    @pytest.fixture(autouse=True)
    async def clear_cache(self):
        """Clear cache before each test to ensure isolation."""
        cache = await get_cache_manager()
        await cache.clear()
        yield
        await cache.clear()

    @pytest.mark.asyncio
    async def test_get_hass_version_success(self):
        """Test successful retrieval of Home Assistant version."""
        mock_config = {"version": "2025.3.0", "location_name": "Home"}

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = mock_config
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("app.api.system.get_client", return_value=mock_client):
            result = await get_hass_version()

            assert result == "2025.3.0"
            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert call_args[0][0] == "http://localhost:8123/api/config"

    @pytest.mark.asyncio
    async def test_get_hass_version_unknown(self):
        """Test version retrieval when version is not in response."""
        mock_config = {"location_name": "Home"}

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = mock_config
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("app.api.system.get_client", return_value=mock_client):
            result = await get_hass_version()
            assert result == "unknown"

    @pytest.mark.asyncio
    async def test_get_hass_version_http_error(self):
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

        with patch("app.api.system.get_client", return_value=mock_client):
            result = await get_hass_version()
            # Error handler may return dict or string depending on error type
            if isinstance(result, dict):
                assert "error" in result
                assert "HTTP error: 500" in result["error"]
            else:
                assert isinstance(result, str)
                assert "error" in result.lower() or "500" in result


class TestGetHassErrorLog:
    """Test the get_hass_error_log function."""

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
    async def test_get_hass_error_log_success(self):
        """Test successful retrieval of error log."""
        mock_log_text = (
            "2025-01-01 ERROR [mqtt] Connection failed\n2025-01-01 WARNING [zwave] Device timeout"
        )

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = mock_log_text
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("app.api.system.get_client", return_value=mock_client):
            result = await get_hass_error_log()

            assert isinstance(result, dict)
            assert result["error_count"] == 1
            assert result["warning_count"] == 1
            assert "mqtt" in result["integration_mentions"]
            assert "zwave" in result["integration_mentions"]
            assert result["log_text"] == mock_log_text

    @pytest.mark.asyncio
    async def test_get_hass_error_log_http_error(self):
        """Test handling of HTTP error during log retrieval."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.reason_phrase = "Internal Server Error"
        mock_response.text = "Error"
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("app.api.system.get_client", return_value=mock_client):
            result = await get_hass_error_log()

            assert "error" in result
            assert "Error retrieving error log: 500" in result["error"]
            assert result["error_count"] == 0
            assert result["warning_count"] == 0

    @pytest.mark.asyncio
    async def test_get_hass_error_log_exception(self):
        """Test handling of exception during log retrieval."""
        mock_client = AsyncMock()
        mock_client.get.side_effect = Exception("Connection failed")

        with patch("app.api.system.get_client", return_value=mock_client):
            result = await get_hass_error_log()

            assert "error" in result
            assert "Error retrieving error log: Connection failed" in result["error"]


class TestGetSystemOverview:
    """Test the get_system_overview function."""

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
    async def test_get_system_overview_success(self):
        """Test successful retrieval of system overview."""
        mock_entities = [
            {
                "entity_id": "light.living_room",
                "state": "on",
                "attributes": {"friendly_name": "Living Room", "area_id": "living_room"},
            },
            {
                "entity_id": "switch.kitchen",
                "state": "off",
                "attributes": {"friendly_name": "Kitchen", "area_id": "kitchen"},
            },
        ]

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = mock_entities
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("app.api.system.get_client", return_value=mock_client):
            result = await get_system_overview()

            assert isinstance(result, dict)
            assert result["total_entities"] == 2
            assert "domains" in result
            assert "light" in result["domains"]
            assert "switch" in result["domains"]
            assert result["domains"]["light"]["count"] == 1
            assert result["domains"]["switch"]["count"] == 1

    @pytest.mark.asyncio
    async def test_get_system_overview_exception(self):
        """Test handling of exception during overview generation."""
        mock_client = AsyncMock()
        mock_client.get.side_effect = Exception("Connection failed")

        with patch("app.api.system.get_client", return_value=mock_client):
            result = await get_system_overview()
            assert "error" in result
            assert "Error generating system overview" in result["error"]


class TestGetSystemHealth:
    """Test the get_system_health function."""

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
    async def test_get_system_health_success(self):
        """Test successful retrieval of system health."""
        mock_health = {
            "homeassistant": {"healthy": True, "version": "2025.3.0"},
            "supervisor": {"healthy": True, "version": "2025.03.1"},
        }

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = mock_health
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("app.api.system.get_client", return_value=mock_client):
            result = await get_system_health()

            assert isinstance(result, dict)
            assert "homeassistant" in result
            assert result["homeassistant"]["healthy"] is True
            assert result["homeassistant"]["version"] == "2025.3.0"
            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert call_args[0][0] == "http://localhost:8123/api/system_health"

    @pytest.mark.asyncio
    async def test_get_system_health_http_error(self):
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

        with patch("app.api.system.get_client", return_value=mock_client):
            result = await get_system_health()
            assert "error" in result
            assert "HTTP error: 500" in result["error"]


class TestGetCoreConfig:
    """Test the get_core_config function."""

    @pytest.fixture(autouse=True)
    def mock_config(self):
        """Mock HA_URL and HA_TOKEN for all tests in this class."""
        with (
            patch("app.config.HA_URL", "http://localhost:8123"),
            patch("app.config.HA_TOKEN", "test_token"),
            patch("app.core.decorators.HA_TOKEN", "test_token"),
        ):
            yield

    @pytest.fixture(autouse=True)
    async def clear_cache(self):
        """Clear cache before each test to ensure isolation."""
        cache = await get_cache_manager()
        await cache.clear()
        yield
        await cache.clear()

    @pytest.mark.asyncio
    async def test_get_core_config_success(self):
        """Test successful retrieval of core configuration."""
        mock_config = {
            "location_name": "Home",
            "time_zone": "America/New_York",
            "unit_system": {"length": "km", "temperature": "°C"},
            "version": "2025.3.0",
            "components": ["mqtt", "hue"],
        }

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = mock_config
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("app.api.system.get_client", return_value=mock_client):
            result = await get_core_config()

            assert isinstance(result, dict)
            assert result["location_name"] == "Home"
            assert result["time_zone"] == "America/New_York"
            assert result["version"] == "2025.3.0"
            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert call_args[0][0] == "http://localhost:8123/api/config"

    @pytest.mark.asyncio
    async def test_get_core_config_http_error(self):
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

        with patch("app.api.system.get_client", return_value=mock_client):
            result = await get_core_config()
            assert "error" in result
            assert "HTTP error: 500" in result["error"]


class TestRestartHomeAssistant:
    """Test the restart_home_assistant function."""

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
    async def test_restart_home_assistant_success(self):
        """Test successful restart of Home Assistant."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.api.system.get_client", return_value=mock_client):
            result = await restart_home_assistant()

            assert isinstance(result, list)
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[0][0] == "http://localhost:8123/api/services/homeassistant/restart"
            assert call_args[1]["json"] == {}

    @pytest.mark.asyncio
    async def test_restart_home_assistant_http_error(self):
        """Test handling of HTTP error during restart."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Internal Server Error",
            request=httpx.Request("POST", "url"),
            response=mock_response,
        )
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.api.system.get_client", return_value=mock_client):
            result = await restart_home_assistant()
            assert "error" in result
            assert "HTTP error: 500" in result["error"]
