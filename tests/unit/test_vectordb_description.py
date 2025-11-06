"""Unit tests for app.core.vectordb.description module."""

from unittest.mock import AsyncMock, patch

import pytest

from app.core.vectordb.description import (
    extract_capabilities,
    generate_entity_description_batch,
    generate_entity_description_enhanced,
    get_area_name,
    get_device_info,
)


class TestGetAreaName:
    """Test the get_area_name function."""

    @pytest.fixture
    def mock_get_areas(self):
        """Create a mock get_areas function."""
        return AsyncMock(
            return_value=[
                {"area_id": "living_room", "name": "Living Room"},
                {"area_id": "kitchen", "name": "Kitchen"},
            ]
        )

    @pytest.mark.asyncio
    async def test_get_area_name_success(self, mock_get_areas):
        """Test successful area name retrieval."""
        with patch("app.core.vectordb.description.get_areas", mock_get_areas):
            area_name = await get_area_name("living_room")

            assert area_name == "Living Room"

    @pytest.mark.asyncio
    async def test_get_area_name_not_found(self, mock_get_areas):
        """Test area name retrieval when area not found."""
        with patch("app.core.vectordb.description.get_areas", mock_get_areas):
            area_name = await get_area_name("bedroom")

            assert area_name is None

    @pytest.mark.asyncio
    async def test_get_area_name_error(self):
        """Test area name retrieval with error."""
        mock_get_areas = AsyncMock(side_effect=Exception("Failed to get areas"))

        with patch("app.core.vectordb.description.get_areas", mock_get_areas):
            area_name = await get_area_name("living_room")

            assert area_name is None


class TestGetDeviceInfo:
    """Test the get_device_info function."""

    @pytest.fixture
    def mock_get_device_details(self):
        """Create a mock get_device_details function."""
        return AsyncMock(
            return_value={
                "id": "device1",
                "name": "Philips Hue Bridge",
                "manufacturer": "Philips",
                "model": "Hue Bridge",
            }
        )

    @pytest.mark.asyncio
    async def test_get_device_info_success(self, mock_get_device_details):
        """Test successful device info retrieval."""
        with patch("app.core.vectordb.description.get_device_details", mock_get_device_details):
            device_info = await get_device_info("device1")

            assert device_info is not None
            assert device_info["id"] == "device1"
            assert device_info["name"] == "Philips Hue Bridge"

    @pytest.mark.asyncio
    async def test_get_device_info_none(self):
        """Test device info retrieval with None device_id."""
        device_info = await get_device_info(None)

        assert device_info is None

    @pytest.mark.asyncio
    async def test_get_device_info_error(self):
        """Test device info retrieval with error."""
        mock_get_device_details = AsyncMock(side_effect=Exception("Failed to get device"))

        with patch("app.core.vectordb.description.get_device_details", mock_get_device_details):
            device_info = await get_device_info("device1")

            assert device_info is None


class TestExtractCapabilities:
    """Test the extract_capabilities function."""

    def test_extract_capabilities_light(self):
        """Test capability extraction for light entity."""
        entity = {
            "entity_id": "light.living_room",
            "attributes": {
                "supported_color_modes": ["brightness", "color_temp"],
                "brightness": 255,
                "color_temp": 370,
            },
        }

        capabilities = extract_capabilities(entity)

        assert "color modes" in capabilities
        assert "brightness control" in capabilities
        assert "color temperature control" in capabilities

    def test_extract_capabilities_sensor(self):
        """Test capability extraction for sensor entity."""
        entity = {
            "entity_id": "sensor.temperature",
            "attributes": {"device_class": "temperature"},
        }

        capabilities = extract_capabilities(entity)

        assert "temperature sensor" in capabilities

    def test_extract_capabilities_climate(self):
        """Test capability extraction for climate entity."""
        entity = {
            "entity_id": "climate.kitchen",
            "attributes": {
                "hvac_modes": ["heat", "cool", "off"],
                "temperature": 22,
            },
        }

        capabilities = extract_capabilities(entity)

        assert "HVAC modes" in capabilities
        assert "temperature control" in capabilities

    def test_extract_capabilities_default(self):
        """Test capability extraction for unknown entity."""
        entity = {
            "entity_id": "unknown.entity",
            "attributes": {},
        }

        capabilities = extract_capabilities(entity)

        assert capabilities == "basic control"


class TestGenerateEntityDescriptionEnhanced:
    """Test the generate_entity_description_enhanced function."""

    @pytest.fixture
    def mock_get_area_name(self):
        """Create a mock get_area_name function."""
        return AsyncMock(return_value="Living Room")

    @pytest.fixture
    def mock_get_device_info(self):
        """Create a mock get_device_info function."""
        return AsyncMock(
            return_value={
                "manufacturer": "Philips",
                "model": "Hue Bridge",
                "name": "Philips Hue Bridge",
            }
        )

    @pytest.mark.asyncio
    async def test_generate_description_light(self, mock_get_area_name, mock_get_device_info):
        """Test description generation for light entity."""
        entity = {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {
                "friendly_name": "Living Room Light",
                "area_id": "living_room",
                "device_id": "device1",
                "supported_color_modes": ["brightness"],
                "brightness": 255,
            },
        }

        with (
            patch("app.core.vectordb.description.get_area_name", mock_get_area_name),
            patch("app.core.vectordb.description.get_device_info", mock_get_device_info),
        ):
            description = await generate_entity_description_enhanced(entity, use_template=True)

            assert "Living Room Light" in description
            assert "light entity" in description
            assert "Living Room" in description
            assert "on" in description

    @pytest.mark.asyncio
    async def test_generate_description_sensor(self, mock_get_area_name, mock_get_device_info):
        """Test description generation for sensor entity."""
        entity = {
            "entity_id": "sensor.temperature",
            "state": "22.5",
            "attributes": {
                "friendly_name": "Temperature Sensor",
                "area_id": "living_room",
                "device_class": "temperature",
                "unit_of_measurement": "°C",
            },
        }

        with (
            patch("app.core.vectordb.description.get_area_name", mock_get_area_name),
            patch("app.core.vectordb.description.get_device_info", mock_get_device_info),
        ):
            description = await generate_entity_description_enhanced(entity, use_template=True)

            assert "Temperature Sensor" in description
            assert "sensor entity" in description
            assert "temperature" in description
            assert "°C" in description

    @pytest.mark.asyncio
    async def test_generate_description_climate(self, mock_get_area_name, mock_get_device_info):
        """Test description generation for climate entity."""
        entity = {
            "entity_id": "climate.kitchen",
            "state": "heat",
            "attributes": {
                "friendly_name": "Kitchen Thermostat",
                "area_id": "kitchen",
                "current_temperature": 20,
                "temperature": 22,
                "hvac_mode": "heat",
            },
        }

        with (
            patch("app.core.vectordb.description.get_area_name", mock_get_area_name),
            patch("app.core.vectordb.description.get_device_info", mock_get_device_info),
        ):
            description = await generate_entity_description_enhanced(entity, use_template=True)

            assert "Kitchen Thermostat" in description
            assert "climate entity" in description
            assert "20" in description or "22" in description

    @pytest.mark.asyncio
    async def test_generate_description_without_template(self, mock_get_area_name):
        """Test description generation without template."""
        entity = {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {
                "friendly_name": "Living Room Light",
                "area_id": "living_room",
            },
        }

        with patch("app.core.vectordb.description.get_area_name", mock_get_area_name):
            description = await generate_entity_description_enhanced(entity, use_template=False)

            assert "Living Room Light" in description
            assert "light entity" in description
            assert "Living Room" in description

    @pytest.mark.asyncio
    async def test_generate_description_default_template(self, mock_get_area_name):
        """Test description generation with default template."""
        entity = {
            "entity_id": "unknown.entity",
            "state": "on",
            "attributes": {
                "friendly_name": "Unknown Entity",
                "area_id": "living_room",
            },
        }

        with patch("app.core.vectordb.description.get_area_name", mock_get_area_name):
            description = await generate_entity_description_enhanced(entity, use_template=True)

            assert "Unknown Entity" in description
            assert "unknown" in description.lower() or "N/A" in description


class TestGenerateEntityDescriptionBatch:
    """Test the generate_entity_description_batch function."""

    @pytest.fixture
    def mock_get_areas(self):
        """Create a mock get_areas function."""
        return AsyncMock(
            return_value=[
                {"area_id": "living_room", "name": "Living Room"},
                {"area_id": "kitchen", "name": "Kitchen"},
            ]
        )

    @pytest.mark.asyncio
    async def test_generate_descriptions_batch(self, mock_get_areas):
        """Test batch description generation."""
        entities = [
            {
                "entity_id": "light.living_room",
                "state": "on",
                "attributes": {
                    "friendly_name": "Living Room Light",
                    "area_id": "living_room",
                },
            },
            {
                "entity_id": "sensor.temperature",
                "state": "22.5",
                "attributes": {
                    "friendly_name": "Temperature Sensor",
                    "area_id": "living_room",
                },
            },
        ]

        with patch("app.core.vectordb.description.get_areas", mock_get_areas):
            descriptions = await generate_entity_description_batch(entities, use_template=True)

            assert len(descriptions) == 2
            assert "light.living_room" in descriptions
            assert "sensor.temperature" in descriptions
            assert "Living Room Light" in descriptions["light.living_room"]
            assert "Temperature Sensor" in descriptions["sensor.temperature"]
