"""Unit tests for app.api.devices module."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.api.devices import (
    get_device_details,
    get_device_entities,
    get_device_statistics,
    get_devices,
)
from app.core.cache.manager import get_cache_manager


class TestGetDevices:
    """Test the get_devices function."""

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
    async def test_get_devices_success(self):
        """Test successful retrieval of all devices."""
        mock_devices = [
            {
                "id": "device1",
                "name": "Device 1",
                "manufacturer": "Philips",
                "model": "Hue Bridge",
                "identifiers": [["hue", "bridge1"]],
                "entities": ["light.living_room"],
            },
            {
                "id": "device2",
                "name": "Device 2",
                "manufacturer": "Samsung",
                "model": "Smart TV",
                "identifiers": [["samsung", "tv1"]],
                "entities": ["media_player.tv"],
            },
        ]

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = mock_devices
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("app.api.devices.get_client", return_value=mock_client):
            result = await get_devices()

            assert isinstance(result, list)
            assert len(result) == 2
            assert result[0]["id"] == "device1"
            assert result[0]["name"] == "Device 1"
            assert result[1]["id"] == "device2"
            assert result[1]["manufacturer"] == "Samsung"

    @pytest.mark.asyncio
    async def test_get_devices_filtered_by_domain(self):
        """Test filtering devices by integration domain."""
        mock_devices = [
            {
                "id": "device1",
                "name": "Device 1",
                "manufacturer": "Philips",
                "model": "Hue Bridge",
                "identifiers": [["hue", "bridge1"]],
                "entities": ["light.living_room"],
            },
            {
                "id": "device2",
                "name": "Device 2",
                "manufacturer": "Samsung",
                "model": "Smart TV",
                "identifiers": [["samsung", "tv1"]],
                "entities": ["media_player.tv"],
            },
        ]

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = mock_devices
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("app.api.devices.get_client", return_value=mock_client):
            result = await get_devices(domain="hue")

            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["id"] == "device1"
            assert result[0]["manufacturer"] == "Philips"

    @pytest.mark.asyncio
    async def test_get_devices_no_matching_domain(self):
        """Test filtering with no matching domain."""
        mock_devices = [
            {
                "id": "device1",
                "name": "Device 1",
                "identifiers": [["hue", "bridge1"]],
            }
        ]

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = mock_devices
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("app.api.devices.get_client", return_value=mock_client):
            result = await get_devices(domain="zwave")

            assert isinstance(result, list)
            assert len(result) == 0

    @pytest.mark.asyncio
    async def test_get_devices_http_error(self):
        """Test handling of HTTP error."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not found", request=MagicMock(), response=mock_response
        )
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("app.api.devices.get_client", return_value=mock_client):
            result = await get_devices()

            # handle_api_errors returns a list with error dict for list-returning functions
            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], dict)
            assert "error" in result[0]


class TestGetDeviceDetails:
    """Test the get_device_details function."""

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
    async def test_get_device_details_success(self):
        """Test successful retrieval of device details."""
        device_id = "device1"
        mock_device = {
            "id": "device1",
            "name": "Device 1",
            "manufacturer": "Philips",
            "model": "Hue Bridge",
            "identifiers": [["hue", "bridge1"]],
            "entities": ["light.living_room"],
        }

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = mock_device
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("app.api.devices.get_client", return_value=mock_client):
            result = await get_device_details(device_id)

            assert isinstance(result, dict)
            assert result["id"] == "device1"
            assert result["name"] == "Device 1"
            assert result["manufacturer"] == "Philips"
            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert call_args[0][0] == f"http://localhost:8123/api/config/devices/{device_id}"

    @pytest.mark.asyncio
    async def test_get_device_details_http_error(self):
        """Test handling of HTTP error."""
        device_id = "nonexistent"
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not found", request=MagicMock(), response=mock_response
        )
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("app.api.devices.get_client", return_value=mock_client):
            result = await get_device_details(device_id)

            assert isinstance(result, dict)
            assert "error" in result


class TestGetDeviceEntities:
    """Test the get_device_entities function."""

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
    async def test_get_device_entities_success(self):
        """Test successful retrieval of device entities."""
        device_id = "device1"
        mock_device = {
            "id": "device1",
            "entities": ["light.living_room", "light.kitchen"],
        }
        mock_entities = [
            {"entity_id": "light.living_room", "state": "on"},
            {"entity_id": "light.kitchen", "state": "off"},
        ]

        with patch("app.api.devices.get_device_details", return_value=mock_device):
            with patch("app.api.devices.get_entity_state") as mock_get_entity:
                mock_get_entity.side_effect = [
                    mock_entities[0],
                    mock_entities[1],
                ]
                result = await get_device_entities(device_id)

                assert isinstance(result, list)
                assert len(result) == 2
                assert result[0]["entity_id"] == "light.living_room"
                assert result[1]["entity_id"] == "light.kitchen"

    @pytest.mark.asyncio
    async def test_get_device_entities_no_entities(self):
        """Test device with no entities."""
        device_id = "device1"
        mock_device = {"id": "device1", "entities": []}

        with patch("app.api.devices.get_device_details", return_value=mock_device):
            result = await get_device_entities(device_id)

            assert isinstance(result, list)
            assert len(result) == 0

    @pytest.mark.asyncio
    async def test_get_device_entities_error(self):
        """Test handling of error when getting device details."""
        device_id = "nonexistent"
        error_response = {"error": "Device not found"}

        with patch("app.api.devices.get_device_details", return_value=error_response):
            result = await get_device_entities(device_id)

            # Should propagate the error from get_device_details as a list
            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], dict)
            assert "error" in result[0]


class TestGetDeviceStatistics:
    """Test the get_device_statistics function."""

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
    async def test_get_device_statistics_success(self):
        """Test successful calculation of device statistics."""
        mock_devices = [
            {
                "id": "device1",
                "manufacturer": "Philips",
                "model": "Hue Bridge",
                "identifiers": [["hue", "bridge1"]],
                "disabled_by": None,
            },
            {
                "id": "device2",
                "manufacturer": "Philips",
                "model": "Hue Light",
                "identifiers": [["hue", "light1"]],
                "disabled_by": None,
            },
            {
                "id": "device3",
                "manufacturer": "Samsung",
                "model": "Smart TV",
                "identifiers": [["samsung", "tv1"]],
                "disabled_by": "user",
            },
            {
                "id": "device4",
                "manufacturer": None,  # Unknown manufacturer
                "model": None,  # Unknown model
                "identifiers": [["mqtt", "sensor1"]],
                "disabled_by": None,
            },
        ]

        with patch("app.api.devices.get_devices", return_value=mock_devices):
            result = await get_device_statistics()

            assert isinstance(result, dict)
            assert result["total_devices"] == 4
            assert result["by_manufacturer"]["Philips"] == 2
            assert result["by_manufacturer"]["Samsung"] == 1
            assert result["by_manufacturer"]["Unknown"] == 1
            assert result["by_model"]["Hue Bridge"] == 1
            assert result["by_model"]["Hue Light"] == 1
            assert result["by_model"]["Smart TV"] == 1
            assert result["by_model"]["Unknown"] == 1
            assert result["by_integration"]["hue"] == 2
            assert result["by_integration"]["samsung"] == 1
            assert result["by_integration"]["mqtt"] == 1
            assert result["disabled_devices"] == 1

    @pytest.mark.asyncio
    async def test_get_device_statistics_empty(self):
        """Test statistics with no devices."""
        with patch("app.api.devices.get_devices", return_value=[]):
            result = await get_device_statistics()

            assert isinstance(result, dict)
            assert result["total_devices"] == 0
            assert result["disabled_devices"] == 0
            assert len(result["by_manufacturer"]) == 0
            assert len(result["by_model"]) == 0
            assert len(result["by_integration"]) == 0

    @pytest.mark.asyncio
    async def test_get_device_statistics_error(self):
        """Test handling of error when getting devices."""
        error_response = {"error": "Connection error"}

        with patch("app.api.devices.get_devices", return_value=error_response):
            result = await get_device_statistics()

            # Should propagate the error from get_devices
            assert isinstance(result, dict)
            assert "error" in result
