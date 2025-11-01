"""Unit tests for app.api.services module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api.services import call_service


class TestServicesAPI:
    """Test the Services API functions."""

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
    async def test_call_service_success(self, mock_httpx_client):
        """Test successfully calling a service."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value=[])
        mock_response.raise_for_status = MagicMock()

        mock_httpx_client.post = AsyncMock(return_value=mock_response)

        # Test function
        result = await call_service("light", "turn_on", {"entity_id": "light.living_room"})

        # Assertions
        assert result == []
        mock_httpx_client.post.assert_called_once()

        # Verify correct URL and payload
        call_args = mock_httpx_client.post.call_args
        assert call_args[0][0] == "http://localhost:8123/api/services/light/turn_on"
        assert call_args[1]["json"] == {"entity_id": "light.living_room"}

    @pytest.mark.asyncio
    async def test_call_service_no_data(self, mock_httpx_client):
        """Test calling a service without data."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value=[])
        mock_response.raise_for_status = MagicMock()

        mock_httpx_client.post = AsyncMock(return_value=mock_response)

        # Test function
        result = await call_service("automation", "reload")

        # Assertions
        assert result == []
        mock_httpx_client.post.assert_called_once()

        # Verify correct URL and payload (empty dict)
        call_args = mock_httpx_client.post.call_args
        assert call_args[0][0] == "http://localhost:8123/api/services/automation/reload"
        assert call_args[1]["json"] == {}

    @pytest.mark.asyncio
    async def test_call_service_with_complex_data(self, mock_httpx_client):
        """Test calling a service with complex data."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value=[])
        mock_response.raise_for_status = MagicMock()

        mock_httpx_client.post = AsyncMock(return_value=mock_response)

        # Complex data with brightness, color, etc.
        data = {
            "entity_id": "light.bedroom",
            "brightness": 128,
            "color_temp": 370,
            "transition": 5,
        }

        # Test function
        result = await call_service("light", "turn_on", data)

        # Assertions
        assert result == []
        mock_httpx_client.post.assert_called_once()

        # Verify correct URL and payload
        call_args = mock_httpx_client.post.call_args
        assert call_args[0][0] == "http://localhost:8123/api/services/light/turn_on"
        assert call_args[1]["json"] == data

    @pytest.mark.asyncio
    async def test_call_service_http_error(self, mock_httpx_client):
        """Test calling a service with HTTP error."""
        # Mock response with error
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.reason_phrase = "Internal Server Error"
        mock_response.raise_for_status = MagicMock(side_effect=Exception("HTTP error: 500"))

        mock_httpx_client.post = AsyncMock(return_value=mock_response)

        # Test function
        result = await call_service("light", "turn_on", {"entity_id": "light.invalid"})

        # Assertions
        assert isinstance(result, dict)
        assert "error" in result
        assert "HTTP error: 500" in result["error"]

    @pytest.mark.asyncio
    async def test_call_service_network_error(self, mock_httpx_client):
        """Test calling a service with network error."""
        # Mock network error
        mock_httpx_client.post = AsyncMock(side_effect=Exception("Connection error"))

        # Test function
        result = await call_service("light", "turn_on", {"entity_id": "light.living_room"})

        # Assertions
        assert isinstance(result, dict)
        assert "error" in result
        assert "Connection error" in result["error"]

    @pytest.mark.asyncio
    async def test_call_service_different_domains(self, mock_httpx_client):
        """Test calling services from different domains."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value=[])
        mock_response.raise_for_status = MagicMock()

        mock_httpx_client.post = AsyncMock(return_value=mock_response)

        # Test various domains
        domains_and_services = [
            ("switch", "toggle"),
            ("fan", "set_percentage"),
            ("climate", "set_temperature"),
            ("cover", "set_position"),
        ]

        for domain, service in domains_and_services:
            data = {"entity_id": f"{domain}.test"}
            result = await call_service(domain, service, data)

            # Verify correct URL
            call_args = mock_httpx_client.post.call_args
            assert call_args[0][0] == f"http://localhost:8123/api/services/{domain}/{service}"

            mock_response.json.reset_mock()
            mock_response.raise_for_status.reset_mock()
