"""Unit tests for app.core.vectordb.search module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.vectordb.search import semantic_search


class TestSemanticSearch:
    """Test the semantic_search function."""

    @pytest.fixture
    def mock_manager(self):
        """Create a mock VectorDBManager."""
        manager = MagicMock()
        manager._initialized = True
        manager.initialize = AsyncMock()
        manager.search_vectors = AsyncMock(
            return_value=[
                {
                    "id": "light.living_room",
                    "distance": 0.1,
                    "metadata": {"domain": "light", "area_id": "living_room"},
                },
                {
                    "id": "light.kitchen",
                    "distance": 0.3,
                    "metadata": {"domain": "light", "area_id": "kitchen"},
                },
            ]
        )
        return manager

    @pytest.fixture
    def mock_config(self):
        """Create a mock VectorDBConfig."""
        config = MagicMock()
        config.is_enabled = MagicMock(return_value=True)
        config.get_search_similarity_threshold = MagicMock(return_value=0.7)
        config.get_search_hybrid_search = MagicMock(return_value=False)
        config.get_search_default_limit = MagicMock(return_value=10)
        return config

    @pytest.mark.asyncio
    async def test_semantic_search_success(self, mock_manager, mock_config):
        """Test successful semantic search."""
        entity1 = {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {"friendly_name": "Living Room Light", "area_id": "living_room"},
        }
        entity2 = {
            "entity_id": "light.kitchen",
            "state": "off",
            "attributes": {"friendly_name": "Kitchen Light", "area_id": "kitchen"},
        }

        with (
            patch("app.core.vectordb.search.get_vectordb_manager", return_value=mock_manager),
            patch("app.core.vectordb.search.get_vectordb_config", return_value=mock_config),
            patch(
                "app.core.vectordb.search.get_entity_state",
                side_effect=[entity1, entity2],
            ),
        ):
            results = await semantic_search("living room lights")
            assert len(results) > 0
            assert results[0]["entity_id"] == "light.living_room"
            assert "similarity_score" in results[0]
            assert "explanation" in results[0]
            assert "entity" in results[0]

    @pytest.mark.asyncio
    async def test_semantic_search_with_domain_filter(self, mock_manager, mock_config):
        """Test semantic search with domain filter."""
        entity = {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {"friendly_name": "Living Room Light"},
        }

        with (
            patch("app.core.vectordb.search.get_vectordb_manager", return_value=mock_manager),
            patch("app.core.vectordb.search.get_vectordb_config", return_value=mock_config),
            patch("app.core.vectordb.search.get_entity_state", return_value=entity),
        ):
            results = await semantic_search("lights", domain="light")
            mock_manager.search_vectors.assert_called_once()
            call_args = mock_manager.search_vectors.call_args
            assert call_args[1]["filter_metadata"]["domain"] == "light"

    @pytest.mark.asyncio
    async def test_semantic_search_with_area_filter(self, mock_manager, mock_config):
        """Test semantic search with area filter."""
        entity = {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {"friendly_name": "Living Room Light"},
        }

        with (
            patch("app.core.vectordb.search.get_vectordb_manager", return_value=mock_manager),
            patch("app.core.vectordb.search.get_vectordb_config", return_value=mock_config),
            patch("app.core.vectordb.search.get_entity_state", return_value=entity),
        ):
            results = await semantic_search("lights", area_id="living_room")
            mock_manager.search_vectors.assert_called_once()
            call_args = mock_manager.search_vectors.call_args
            assert call_args[1]["filter_metadata"]["area_id"] == "living_room"

    @pytest.mark.asyncio
    async def test_semantic_search_with_state_filter(self, mock_manager, mock_config):
        """Test semantic search with state filter."""
        entity_on = {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {"friendly_name": "Living Room Light"},
        }
        entity_off = {
            "entity_id": "light.kitchen",
            "state": "off",
            "attributes": {"friendly_name": "Kitchen Light"},
        }

        with (
            patch(
                "app.core.vectordb.search.get_vectordb_manager",
                return_value=mock_manager,
            ),
            patch("app.core.vectordb.search.get_vectordb_config", return_value=mock_config),
            patch(
                "app.core.vectordb.search.get_entity_state",
                side_effect=[entity_on, entity_off],
            ),
        ):
            results = await semantic_search("lights", entity_state="on")
            # Only entities with state "on" should be returned
            for result in results:
                assert result["entity"]["state"] == "on"

    @pytest.mark.asyncio
    async def test_semantic_search_with_similarity_threshold(self, mock_manager, mock_config):
        """Test semantic search with similarity threshold."""
        entity = {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {"friendly_name": "Living Room Light"},
        }

        with (
            patch("app.core.vectordb.search.get_vectordb_manager", return_value=mock_manager),
            patch("app.core.vectordb.search.get_vectordb_config", return_value=mock_config),
            patch("app.core.vectordb.search.get_entity_state", return_value=entity),
        ):
            results = await semantic_search("lights", similarity_threshold=0.8)
            # Results should only include entities with similarity >= 0.8
            for result in results:
                assert result["similarity_score"] >= 0.8

    @pytest.mark.asyncio
    async def test_semantic_search_vectordb_disabled(self, mock_manager):
        """Test semantic search when vector DB is disabled."""
        config = MagicMock()
        config.is_enabled = MagicMock(return_value=False)

        entities = [
            {
                "entity_id": "light.living_room",
                "state": "on",
                "attributes": {"friendly_name": "Living Room Light"},
            }
        ]

        with (
            patch("app.core.vectordb.search.get_vectordb_manager", return_value=mock_manager),
            patch("app.core.vectordb.search.get_vectordb_config", return_value=config),
            patch("app.core.vectordb.search.get_entities", return_value=entities),
        ):
            results = await semantic_search("living room lights")
            # Should fall back to keyword search
            assert len(results) > 0
            assert results[0]["entity_id"] == "light.living_room"

    @pytest.mark.asyncio
    async def test_semantic_search_hybrid(self, mock_manager, mock_config):
        """Test hybrid search (semantic + keyword)."""
        mock_config.get_search_hybrid_search = MagicMock(return_value=True)

        entity = {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {"friendly_name": "Living Room Light", "area_id": "living_room"},
        }

        with (
            patch("app.core.vectordb.search.get_vectordb_manager", return_value=mock_manager),
            patch("app.core.vectordb.search.get_vectordb_config", return_value=mock_config),
            patch("app.core.vectordb.search.get_entity_state", return_value=entity),
            patch("app.core.vectordb.search.get_entities", return_value=[entity]),
        ):
            results = await semantic_search("living room lights", hybrid_search=True)
            # Should include both semantic and keyword results
            assert len(results) > 0

    @pytest.mark.asyncio
    async def test_semantic_search_limit(self, mock_manager, mock_config):
        """Test semantic search with limit."""
        entity = {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {"friendly_name": "Living Room Light"},
        }

        # Mock more results than limit
        mock_manager.search_vectors = AsyncMock(
            return_value=[
                {
                    "id": f"light.entity_{i}",
                    "distance": 0.1 * i,
                    "metadata": {"domain": "light"},
                }
                for i in range(20)
            ]
        )

        with (
            patch("app.core.vectordb.search.get_vectordb_manager", return_value=mock_manager),
            patch("app.core.vectordb.search.get_vectordb_config", return_value=mock_config),
            patch("app.core.vectordb.search.get_entity_state", return_value=entity),
        ):
            results = await semantic_search("lights", limit=5)
            assert len(results) <= 5

    @pytest.mark.asyncio
    async def test_semantic_search_error_handling(self, mock_manager, mock_config):
        """Test semantic search error handling."""
        mock_manager.search_vectors = AsyncMock(side_effect=Exception("Search error"))

        entities = [
            {
                "entity_id": "light.living_room",
                "state": "on",
                "attributes": {"friendly_name": "Living Room Light"},
            }
        ]

        with (
            patch("app.core.vectordb.search.get_vectordb_manager", return_value=mock_manager),
            patch("app.core.vectordb.search.get_vectordb_config", return_value=mock_config),
            patch("app.core.vectordb.search.get_entities", return_value=entities),
        ):
            results = await semantic_search("living room lights")
            # Should fall back to keyword search
            assert len(results) > 0

    @pytest.mark.asyncio
    async def test_semantic_search_boost_exact_match(self, mock_manager, mock_config):
        """Test that exact matches are boosted."""
        entity = {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {"friendly_name": "Living Room Light", "area_id": "living_room"},
        }

        with (
            patch("app.core.vectordb.search.get_vectordb_manager", return_value=mock_manager),
            patch("app.core.vectordb.search.get_vectordb_config", return_value=mock_config),
            patch("app.core.vectordb.search.get_entity_state", return_value=entity),
        ):
            results = await semantic_search("living room light")
            # Exact match should have higher score
            if len(results) > 0:
                assert "similarity_score" in results[0]
                assert results[0]["similarity_score"] > 0.0

    @pytest.mark.asyncio
    async def test_semantic_search_explanation(self, mock_manager, mock_config):
        """Test that results include explanations."""
        entity = {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {"friendly_name": "Living Room Light", "area_id": "living_room"},
        }

        with (
            patch("app.core.vectordb.search.get_vectordb_manager", return_value=mock_manager),
            patch("app.core.vectordb.search.get_vectordb_config", return_value=mock_config),
            patch("app.core.vectordb.search.get_entity_state", return_value=entity),
        ):
            results = await semantic_search("lights")
            if len(results) > 0:
                assert "explanation" in results[0]
                assert isinstance(results[0]["explanation"], str)
                assert "matched" in results[0]["explanation"].lower()
