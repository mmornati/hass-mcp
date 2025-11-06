"""Unit tests for app.core.vectordb.relationships module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.vectordb.relationships import (
    build_relationship_graph,
    find_entities_by_relationship,
    get_entities_from_device,
    get_entities_in_area,
    get_related_entities,
    get_relationship_statistics,
)


class TestBuildRelationshipGraph:
    """Test the build_relationship_graph function."""

    @pytest.fixture
    def mock_manager(self):
        """Create a mock VectorDBManager."""
        manager = MagicMock()
        manager._initialized = True
        manager.initialize = AsyncMock()
        manager.embed_texts = AsyncMock(return_value=[[0.1, 0.2, 0.3]])
        manager.backend = MagicMock()
        manager.backend.collection_exists = AsyncMock(return_value=False)
        manager.backend.create_collection = AsyncMock()
        manager.backend.add_vectors = AsyncMock()
        return manager

    @pytest.fixture
    def mock_config(self):
        """Create a mock VectorDBConfig."""
        config = MagicMock()
        config.is_enabled = MagicMock(return_value=True)
        return config

    @pytest.mark.asyncio
    async def test_build_relationship_graph_success(self, mock_manager, mock_config):
        """Test successful relationship graph construction."""
        mock_entities = [
            {
                "entity_id": "light.living_room",
                "attributes": {"area_id": "living_room"},
            },
            {
                "entity_id": "sensor.temperature",
                "attributes": {"area_id": "living_room"},
            },
        ]

        mock_areas = [
            {"area_id": "living_room", "name": "Living Room"},
        ]

        mock_devices = [
            {
                "id": "device1",
                "entities": ["light.living_room"],
                "via_device_id": None,
            },
        ]

        mock_automations = [
            {"entity_id": "automation.morning_routine"},
        ]

        with (
            patch(
                "app.core.vectordb.relationships.get_vectordb_manager", return_value=mock_manager
            ),
            patch("app.core.vectordb.relationships.get_vectordb_config", return_value=mock_config),
            patch("app.core.vectordb.relationships.get_entities", return_value=mock_entities),
            patch("app.core.vectordb.relationships.get_areas", return_value=mock_areas),
            patch("app.core.vectordb.relationships.get_devices", return_value=mock_devices),
            patch("app.core.vectordb.relationships.get_automations", return_value=mock_automations),
            patch("app.core.vectordb.relationships.get_device_details", return_value={}),
        ):
            result = await build_relationship_graph()

            assert result["success"] is True
            assert "total_relationships" in result
            assert "relationships_by_type" in result
            assert result["total_relationships"] > 0

    @pytest.mark.asyncio
    async def test_build_relationship_graph_disabled(self, mock_manager, mock_config):
        """Test relationship graph construction when Vector DB is disabled."""
        mock_config.is_enabled = MagicMock(return_value=False)

        with (
            patch(
                "app.core.vectordb.relationships.get_vectordb_manager", return_value=mock_manager
            ),
            patch("app.core.vectordb.relationships.get_vectordb_config", return_value=mock_config),
        ):
            result = await build_relationship_graph()

            assert result["success"] is False
            assert result.get("reason") == "Vector DB disabled"


class TestFindEntitiesByRelationship:
    """Test the find_entities_by_relationship function."""

    @pytest.fixture
    def mock_manager(self):
        """Create a mock VectorDBManager."""
        manager = MagicMock()
        manager._initialized = True
        manager.initialize = AsyncMock()
        manager.embed_texts = AsyncMock(return_value=[[0.1, 0.2, 0.3]])
        manager.backend = MagicMock()
        manager.backend.collection_exists = AsyncMock(return_value=True)
        manager.backend.search_vectors = AsyncMock(
            return_value=[
                {
                    "id": "rel1",
                    "metadata": {
                        "source": "light.living_room",
                        "target": "living_room",
                        "relationship_type": "in_area",
                    },
                }
            ]
        )
        return manager

    @pytest.fixture
    def mock_config(self):
        """Create a mock VectorDBConfig."""
        config = MagicMock()
        config.is_enabled = MagicMock(return_value=True)
        return config

    @pytest.mark.asyncio
    async def test_find_entities_by_relationship_success(self, mock_manager, mock_config):
        """Test finding entities by relationship."""
        with (
            patch(
                "app.core.vectordb.relationships.get_vectordb_manager", return_value=mock_manager
            ),
            patch("app.core.vectordb.relationships.get_vectordb_config", return_value=mock_config),
        ):
            relationships = await find_entities_by_relationship(
                relationship_type="in_area", limit=10
            )

            assert isinstance(relationships, list)
            if relationships:
                assert "source" in relationships[0]
                assert "target" in relationships[0]
                assert "relationship_type" in relationships[0]

    @pytest.mark.asyncio
    async def test_find_entities_by_relationship_disabled(self, mock_manager, mock_config):
        """Test finding entities by relationship when Vector DB is disabled."""
        mock_config.is_enabled = MagicMock(return_value=False)

        with (
            patch(
                "app.core.vectordb.relationships.get_vectordb_manager", return_value=mock_manager
            ),
            patch("app.core.vectordb.relationships.get_vectordb_config", return_value=mock_config),
        ):
            relationships = await find_entities_by_relationship()

            assert relationships == []


class TestGetEntitiesInArea:
    """Test the get_entities_in_area function."""

    @pytest.fixture
    def mock_manager(self):
        """Create a mock VectorDBManager."""
        manager = MagicMock()
        manager._initialized = True
        manager.initialize = AsyncMock()
        return manager

    @pytest.fixture
    def mock_config(self):
        """Create a mock VectorDBConfig."""
        config = MagicMock()
        config.is_enabled = MagicMock(return_value=True)
        return config

    @pytest.mark.asyncio
    async def test_get_entities_in_area_success(self, mock_manager, mock_config):
        """Test getting entities in an area."""
        mock_relationships = [
            {
                "source": "light.living_room",
                "target": "living_room",
                "relationship_type": "in_area",
            },
            {
                "source": "sensor.temperature",
                "target": "living_room",
                "relationship_type": "in_area",
            },
        ]

        with (
            patch(
                "app.core.vectordb.relationships.get_vectordb_manager", return_value=mock_manager
            ),
            patch("app.core.vectordb.relationships.get_vectordb_config", return_value=mock_config),
            patch(
                "app.core.vectordb.relationships.find_entities_by_relationship",
                return_value=mock_relationships,
            ),
        ):
            entities = await get_entities_in_area("living_room")

            assert isinstance(entities, list)
            assert len(entities) > 0
            assert "light.living_room" in entities or "sensor.temperature" in entities


class TestGetEntitiesFromDevice:
    """Test the get_entities_from_device function."""

    @pytest.fixture
    def mock_manager(self):
        """Create a mock VectorDBManager."""
        manager = MagicMock()
        manager._initialized = True
        manager.initialize = AsyncMock()
        return manager

    @pytest.fixture
    def mock_config(self):
        """Create a mock VectorDBConfig."""
        config = MagicMock()
        config.is_enabled = MagicMock(return_value=True)
        return config

    @pytest.mark.asyncio
    async def test_get_entities_from_device_success(self, mock_manager, mock_config):
        """Test getting entities from a device."""
        mock_relationships = [
            {
                "source": "light.living_room",
                "target": "device1",
                "relationship_type": "from_device",
            },
            {
                "source": "light.kitchen",
                "target": "device1",
                "relationship_type": "from_device",
            },
        ]

        with (
            patch(
                "app.core.vectordb.relationships.get_vectordb_manager", return_value=mock_manager
            ),
            patch("app.core.vectordb.relationships.get_vectordb_config", return_value=mock_config),
            patch(
                "app.core.vectordb.relationships.find_entities_by_relationship",
                return_value=mock_relationships,
            ),
        ):
            entities = await get_entities_from_device("device1")

            assert isinstance(entities, list)
            assert len(entities) > 0
            assert "light.living_room" in entities or "light.kitchen" in entities


class TestGetRelatedEntities:
    """Test the get_related_entities function."""

    @pytest.fixture
    def mock_manager(self):
        """Create a mock VectorDBManager."""
        manager = MagicMock()
        manager._initialized = True
        manager.initialize = AsyncMock()
        return manager

    @pytest.fixture
    def mock_config(self):
        """Create a mock VectorDBConfig."""
        config = MagicMock()
        config.is_enabled = MagicMock(return_value=True)
        return config

    @pytest.mark.asyncio
    async def test_get_related_entities_success(self, mock_manager, mock_config):
        """Test getting related entities."""
        mock_relationships = [
            {
                "source": "light.living_room",
                "target": "sensor.temperature",
                "relationship_type": "same_area",
            },
        ]

        with (
            patch(
                "app.core.vectordb.relationships.get_vectordb_manager", return_value=mock_manager
            ),
            patch("app.core.vectordb.relationships.get_vectordb_config", return_value=mock_config),
            patch(
                "app.core.vectordb.relationships.find_entities_by_relationship",
                return_value=mock_relationships,
            ),
        ):
            related = await get_related_entities("light.living_room")

            assert isinstance(related, list)
            # May be empty if no relationships found, but should be a list

    @pytest.mark.asyncio
    async def test_get_related_entities_with_types(self, mock_manager, mock_config):
        """Test getting related entities with specific relationship types."""
        mock_relationships = [
            {
                "source": "light.living_room",
                "target": "sensor.temperature",
                "relationship_type": "same_area",
            },
        ]

        with (
            patch(
                "app.core.vectordb.relationships.get_vectordb_manager", return_value=mock_manager
            ),
            patch("app.core.vectordb.relationships.get_vectordb_config", return_value=mock_config),
            patch(
                "app.core.vectordb.relationships.find_entities_by_relationship",
                return_value=mock_relationships,
            ),
        ):
            related = await get_related_entities(
                "light.living_room", relationship_types=["same_area"]
            )

            assert isinstance(related, list)


class TestGetRelationshipStatistics:
    """Test the get_relationship_statistics function."""

    @pytest.fixture
    def mock_manager(self):
        """Create a mock VectorDBManager."""
        manager = MagicMock()
        manager._initialized = True
        manager.initialize = AsyncMock()
        manager.embed_texts = AsyncMock(return_value=[[0.1, 0.2, 0.3]])
        manager.backend = MagicMock()
        manager.backend.collection_exists = AsyncMock(return_value=True)
        manager.backend.search_vectors = AsyncMock(
            return_value=[
                {
                    "id": "rel1",
                    "metadata": {
                        "source": "light.living_room",
                        "target": "living_room",
                        "relationship_type": "in_area",
                        "source_type": "entity",
                        "target_type": "area",
                    },
                }
            ]
        )
        return manager

    @pytest.fixture
    def mock_config(self):
        """Create a mock VectorDBConfig."""
        config = MagicMock()
        config.is_enabled = MagicMock(return_value=True)
        return config

    @pytest.mark.asyncio
    async def test_get_relationship_statistics_success(self, mock_manager, mock_config):
        """Test getting relationship statistics."""
        with (
            patch(
                "app.core.vectordb.relationships.get_vectordb_manager", return_value=mock_manager
            ),
            patch("app.core.vectordb.relationships.get_vectordb_config", return_value=mock_config),
        ):
            stats = await get_relationship_statistics()

            assert "total_relationships" in stats
            assert "relationships_by_type" in stats
            assert "entities_with_relationships" in stats
            assert "areas_with_entities" in stats
            assert "devices_with_entities" in stats

    @pytest.mark.asyncio
    async def test_get_relationship_statistics_disabled(self, mock_manager, mock_config):
        """Test getting relationship statistics when Vector DB is disabled."""
        mock_config.is_enabled = MagicMock(return_value=False)

        with (
            patch(
                "app.core.vectordb.relationships.get_vectordb_manager", return_value=mock_manager
            ),
            patch("app.core.vectordb.relationships.get_vectordb_config", return_value=mock_config),
        ):
            stats = await get_relationship_statistics()

            assert stats["total_relationships"] == 0
            assert stats["entities_with_relationships"] == 0
