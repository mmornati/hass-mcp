"""Unit tests for app.core.vectordb.indexing module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.vectordb.indexing import (
    generate_entity_description,
    generate_entity_metadata,
    get_indexing_status,
    index_entities,
    index_entity,
    remove_entity_from_index,
    update_entity_index,
)
from app.core.vectordb.manager import VectorDBManager


class TestGenerateEntityDescription:
    """Test the generate_entity_description function."""

    def test_basic_description(self):
        """Test basic entity description generation."""
        entity = {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {
                "friendly_name": "Living Room Light",
            },
        }

        description = generate_entity_description(entity)
        assert "Living Room Light" in description
        assert "light entity" in description.lower()

    def test_description_with_area(self):
        """Test description generation with area."""
        entity = {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {
                "friendly_name": "Living Room Light",
            },
        }

        description = generate_entity_description(entity, area_name="Living Room")
        assert "Living Room Light" in description
        assert "in the Living Room area" in description

    def test_description_with_device(self):
        """Test description generation with device info."""
        entity = {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {
                "friendly_name": "Living Room Light",
            },
        }

        device_info = {"manufacturer": "Philips", "model": "Hue"}

        description = generate_entity_description(entity, device_info=device_info)
        assert "Living Room Light" in description
        assert "Philips" in description
        assert "Hue" in description

    def test_light_capabilities(self):
        """Test description generation for light with capabilities."""
        entity = {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {
                "friendly_name": "Living Room Light",
                "supported_color_modes": ["brightness", "color_temp"],
                "brightness": 255,
            },
        }

        description = generate_entity_description(entity)
        assert "Supports brightness, color_temp" in description
        assert "brightness control" in description

    def test_sensor_description(self):
        """Test description generation for sensor."""
        entity = {
            "entity_id": "sensor.temperature",
            "state": "21.5",
            "attributes": {
                "friendly_name": "Temperature",
                "device_class": "temperature",
                "unit_of_measurement": "°C",
            },
        }

        description = generate_entity_description(entity)
        assert "Temperature" in description
        assert "temperature sensor" in description.lower()
        assert "measured in °C" in description

    def test_climate_description(self):
        """Test description generation for climate entity."""
        entity = {
            "entity_id": "climate.living_room",
            "state": "heat",
            "attributes": {
                "friendly_name": "Living Room Thermostat",
                "current_temperature": 21.5,
                "temperature": 22.0,
                "hvac_mode": "heat",
            },
        }

        description = generate_entity_description(entity)
        assert "Living Room Thermostat" in description
        assert "current temperature 21.5" in description
        assert "target temperature 22.0" in description
        assert "mode heat" in description

    def test_fallback_to_entity_id(self):
        """Test description generation when no friendly name."""
        entity = {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {},
        }

        description = generate_entity_description(entity)
        assert "light entity" in description.lower()
        assert "Currently on" in description


class TestGenerateEntityMetadata:
    """Test the generate_entity_metadata function."""

    @pytest.mark.asyncio
    async def test_basic_metadata(self):
        """Test basic metadata generation."""
        entity = {
            "entity_id": "light.living_room",
            "state": "on",
            "last_updated": "2025-01-01T12:00:00Z",
            "attributes": {
                "friendly_name": "Living Room Light",
                "area_id": "living_room",
            },
        }

        metadata = await generate_entity_metadata(entity)
        assert metadata["entity_id"] == "light.living_room"
        assert metadata["domain"] == "light"
        assert metadata["friendly_name"] == "Living Room Light"
        assert metadata["area_id"] == "living_room"
        assert "indexed_at" in metadata

    @pytest.mark.asyncio
    async def test_metadata_with_device(self):
        """Test metadata generation with device info."""
        entity = {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {
                "friendly_name": "Living Room Light",
                "device_id": "device_123",
            },
        }

        mock_device = {"manufacturer": "Philips", "model": "Hue"}

        with patch("app.core.vectordb.indexing.get_device_details", return_value=mock_device):
            metadata = await generate_entity_metadata(entity)
            assert metadata["manufacturer"] == "Philips"
            assert metadata["model"] == "Hue"

    @pytest.mark.asyncio
    async def test_metadata_device_error(self):
        """Test metadata generation when device info fails."""
        entity = {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {
                "friendly_name": "Living Room Light",
                "device_id": "device_123",
            },
        }

        with patch(
            "app.core.vectordb.indexing.get_device_details",
            side_effect=Exception("Device not found"),
        ):
            metadata = await generate_entity_metadata(entity)
            assert "manufacturer" not in metadata
            assert "model" not in metadata


class TestIndexEntity:
    """Test the index_entity function."""

    @pytest.fixture
    def mock_manager(self):
        """Create a mock VectorDBManager."""
        manager = MagicMock(spec=VectorDBManager)
        manager.config = MagicMock()
        manager.config.is_enabled = MagicMock(return_value=True)
        manager.collection_exists = AsyncMock(return_value=True)
        manager.add_vectors = AsyncMock()
        manager.create_collection = AsyncMock()
        return manager

    @pytest.mark.asyncio
    async def test_index_entity_success(self, mock_manager):
        """Test successful entity indexing."""
        entity = {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {
                "friendly_name": "Living Room Light",
            },
        }

        with (
            patch("app.core.vectordb.indexing.get_entity_state", return_value=entity),
            patch("app.core.vectordb.indexing.get_area_name", return_value=None),
            patch("app.core.vectordb.indexing.get_device_details", return_value=None),
        ):
            result = await index_entity("light.living_room", mock_manager)
            assert result["success"] is True
            assert result["entity_id"] == "light.living_room"
            assert "description" in result
            mock_manager.add_vectors.assert_called_once()

    @pytest.mark.asyncio
    async def test_index_entity_not_found(self, mock_manager):
        """Test indexing when entity not found."""
        with patch(
            "app.core.vectordb.indexing.get_entity_state",
            return_value={"error": "Entity not found"},
        ):
            result = await index_entity("light.nonexistent", mock_manager)
            assert result["success"] is False
            assert "error" in result

    @pytest.mark.asyncio
    async def test_index_entity_vectordb_disabled(self):
        """Test indexing when vector DB is disabled."""
        manager = MagicMock(spec=VectorDBManager)
        manager.config = MagicMock()
        manager.config.is_enabled = MagicMock(return_value=False)

        result = await index_entity("light.living_room", manager)
        assert result["success"] is False
        assert "disabled" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_index_entity_creates_collection(self, mock_manager):
        """Test that indexing creates collection if it doesn't exist."""
        entity = {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {
                "friendly_name": "Living Room Light",
            },
        }

        mock_manager.collection_exists = AsyncMock(return_value=False)
        mock_manager.create_collection = AsyncMock()

        with (
            patch("app.core.vectordb.indexing.get_entity_state", return_value=entity),
            patch("app.core.vectordb.indexing.get_area_name", return_value=None),
            patch("app.core.vectordb.indexing.get_device_details", return_value=None),
        ):
            await index_entity("light.living_room", mock_manager)
            mock_manager.create_collection.assert_called_once()


class TestIndexEntities:
    """Test the index_entities function."""

    @pytest.fixture
    def mock_manager(self):
        """Create a mock VectorDBManager."""
        manager = MagicMock(spec=VectorDBManager)
        manager.config = MagicMock()
        manager.config.is_enabled = MagicMock(return_value=True)
        manager.collection_exists = AsyncMock(return_value=True)
        manager.add_vectors = AsyncMock()
        manager.create_collection = AsyncMock()
        return manager

    @pytest.mark.asyncio
    async def test_index_entities_success(self, mock_manager):
        """Test successful batch indexing."""
        entity_ids = ["light.living_room", "sensor.temperature"]
        entity1 = {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {"friendly_name": "Living Room Light"},
        }
        entity2 = {
            "entity_id": "sensor.temperature",
            "state": "21.5",
            "attributes": {"friendly_name": "Temperature"},
        }

        with (
            patch("app.core.vectordb.indexing.get_entity_state", side_effect=[entity1, entity2]),
            patch("app.core.vectordb.indexing.get_area_name", return_value=None),
            patch("app.core.vectordb.indexing.get_device_details", return_value=None),
        ):
            result = await index_entities(entity_ids, batch_size=10, manager=mock_manager)
            assert result["total"] == 2
            assert result["succeeded"] == 2
            assert result["failed"] == 0
            assert len(result["results"]) == 2

    @pytest.mark.asyncio
    async def test_index_entities_all(self, mock_manager):
        """Test indexing all entities."""
        entities = [
            {"entity_id": "light.living_room"},
            {"entity_id": "sensor.temperature"},
        ]
        entity_data = {
            "light.living_room": {
                "entity_id": "light.living_room",
                "state": "on",
                "attributes": {"friendly_name": "Living Room Light"},
            },
            "sensor.temperature": {
                "entity_id": "sensor.temperature",
                "state": "21.5",
                "attributes": {"friendly_name": "Temperature"},
            },
        }

        def mock_get_entity_state(entity_id, **kwargs):
            return entity_data.get(entity_id)

        with (
            patch("app.core.vectordb.indexing.get_entities", return_value=entities),
            patch(
                "app.core.vectordb.indexing.get_entity_state",
                side_effect=mock_get_entity_state,
            ),
            patch("app.core.vectordb.indexing.get_area_name", return_value=None),
            patch("app.core.vectordb.indexing.get_device_details", return_value=None),
        ):
            result = await index_entities(manager=mock_manager)
            assert result["total"] == 2
            assert result["succeeded"] == 2

    @pytest.mark.asyncio
    async def test_index_entities_with_failures(self, mock_manager):
        """Test batch indexing with some failures."""
        entity_ids = ["light.living_room", "sensor.nonexistent"]
        entity1 = {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {"friendly_name": "Living Room Light"},
        }

        with (
            patch(
                "app.core.vectordb.indexing.get_entity_state",
                side_effect=[entity1, {"error": "Entity not found"}],
            ),
            patch("app.core.vectordb.indexing.get_area_name", return_value=None),
            patch("app.core.vectordb.indexing.get_device_details", return_value=None),
        ):
            result = await index_entities(entity_ids, manager=mock_manager)
            assert result["total"] == 2
            assert result["succeeded"] == 1
            assert result["failed"] == 1


class TestUpdateEntityIndex:
    """Test the update_entity_index function."""

    @pytest.fixture
    def mock_manager(self):
        """Create a mock VectorDBManager."""
        manager = MagicMock(spec=VectorDBManager)
        manager.config = MagicMock()
        manager.config.is_enabled = MagicMock(return_value=True)
        manager.collection_exists = AsyncMock(return_value=True)
        manager.add_vectors = AsyncMock()
        manager.create_collection = AsyncMock()
        return manager

    @pytest.mark.asyncio
    async def test_update_entity_index(self, mock_manager):
        """Test updating entity index."""
        entity = {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {
                "friendly_name": "Living Room Light",
            },
        }

        with (
            patch("app.core.vectordb.indexing.get_entity_state", return_value=entity),
            patch("app.core.vectordb.indexing.get_area_name", return_value=None),
            patch("app.core.vectordb.indexing.get_device_details", return_value=None),
        ):
            result = await update_entity_index("light.living_room", mock_manager)
            assert result["success"] is True
            mock_manager.add_vectors.assert_called_once()


class TestRemoveEntityFromIndex:
    """Test the remove_entity_from_index function."""

    @pytest.fixture
    def mock_manager(self):
        """Create a mock VectorDBManager."""
        manager = MagicMock(spec=VectorDBManager)
        manager.config = MagicMock()
        manager.config.is_enabled = MagicMock(return_value=True)
        manager.delete_vectors = AsyncMock()
        return manager

    @pytest.mark.asyncio
    async def test_remove_entity_success(self, mock_manager):
        """Test successful entity removal."""
        result = await remove_entity_from_index("light.living_room", mock_manager)
        assert result["success"] is True
        assert result["entity_id"] == "light.living_room"
        mock_manager.delete_vectors.assert_called_once_with("entities", ["light.living_room"])

    @pytest.mark.asyncio
    async def test_remove_entity_vectordb_disabled(self):
        """Test removal when vector DB is disabled."""
        manager = MagicMock(spec=VectorDBManager)
        manager.config = MagicMock()
        manager.config.is_enabled = MagicMock(return_value=False)

        result = await remove_entity_from_index("light.living_room", manager)
        assert result["success"] is False
        assert "disabled" in result["error"].lower()


class TestGetIndexingStatus:
    """Test the get_indexing_status function."""

    @pytest.fixture
    def mock_manager(self):
        """Create a mock VectorDBManager."""
        manager = MagicMock(spec=VectorDBManager)
        manager.config = MagicMock()
        manager.config.is_enabled = MagicMock(return_value=True)
        manager.collection_exists = AsyncMock(return_value=True)
        manager.get_collection_stats = AsyncMock(
            return_value={"count": 10, "dimensions": 384, "metadata": {}}
        )
        return manager

    @pytest.mark.asyncio
    async def test_get_indexing_status_success(self, mock_manager):
        """Test getting indexing status."""
        status = await get_indexing_status(mock_manager)
        assert status["collection_exists"] is True
        assert status["total_entities"] == 10
        assert status["dimensions"] == 384

    @pytest.mark.asyncio
    async def test_get_indexing_status_no_collection(self, mock_manager):
        """Test getting status when collection doesn't exist."""
        mock_manager.collection_exists = AsyncMock(return_value=False)

        status = await get_indexing_status(mock_manager)
        assert status["collection_exists"] is False
        assert status["total_entities"] == 0

    @pytest.mark.asyncio
    async def test_get_indexing_status_vectordb_disabled(self):
        """Test getting status when vector DB is disabled."""
        manager = MagicMock(spec=VectorDBManager)
        manager.config = MagicMock()
        manager.config.is_enabled = MagicMock(return_value=False)

        status = await get_indexing_status(manager)
        assert status["collection_exists"] is False
        assert "error" in status
