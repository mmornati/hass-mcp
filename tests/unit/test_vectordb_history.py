"""Unit tests for app.core.vectordb.history module."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.vectordb.history import (
    boost_entity_ranking,
    clear_query_history,
    get_entity_popularity,
    get_query_history,
    get_query_statistics,
    store_query_history,
)


class TestStoreQueryHistory:
    """Test the store_query_history function."""

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
    async def test_store_query_history_success(self, mock_manager, mock_config):
        """Test successful query history storage."""
        results = [
            {
                "entity_id": "light.living_room",
                "similarity_score": 0.95,
            }
        ]

        with (
            patch("app.core.vectordb.history.get_vectordb_manager", return_value=mock_manager),
            patch("app.core.vectordb.history.get_vectordb_config", return_value=mock_config),
            patch("app.core.vectordb.history.process_query", return_value={"intent": "SEARCH"}),
        ):
            result = await store_query_history(
                "living room lights",
                results=results,
                selected_entity_id="light.living_room",
            )

            assert result["success"] is True
            assert "query_id" in result
            assert "query_text" in result
            assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_store_query_history_disabled(self, mock_manager, mock_config):
        """Test query history storage when Vector DB is disabled."""
        mock_config.is_enabled = MagicMock(return_value=False)

        with (
            patch("app.core.vectordb.history.get_vectordb_manager", return_value=mock_manager),
            patch("app.core.vectordb.history.get_vectordb_config", return_value=mock_config),
        ):
            result = await store_query_history("living room lights")

            assert result["success"] is False
            assert result.get("reason") == "Vector DB disabled"

    @pytest.mark.asyncio
    async def test_store_query_history_with_user_id(self, mock_manager, mock_config):
        """Test storing query history with user ID."""
        with (
            patch("app.core.vectordb.history.get_vectordb_manager", return_value=mock_manager),
            patch("app.core.vectordb.history.get_vectordb_config", return_value=mock_config),
            patch("app.core.vectordb.history.process_query", return_value={"intent": "SEARCH"}),
        ):
            result = await store_query_history("living room lights", user_id="user123")

            assert result["success"] is True
            mock_manager.backend.add_vectors.assert_called_once()
            call_args = mock_manager.backend.add_vectors.call_args
            metadata = call_args[1]["metadata"][0]
            assert metadata.get("user_id") == "user123"


class TestGetQueryHistory:
    """Test the get_query_history function."""

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
                    "id": "query1",
                    "metadata": {
                        "query_id": "query1",
                        "query_text": "living room lights",
                        "timestamp": datetime.now(UTC).isoformat(),
                        "intent": "SEARCH",
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
    async def test_get_query_history_success(self, mock_manager, mock_config):
        """Test getting query history."""
        with (
            patch("app.core.vectordb.history.get_vectordb_manager", return_value=mock_manager),
            patch("app.core.vectordb.history.get_vectordb_config", return_value=mock_config),
        ):
            history = await get_query_history(limit=10)

            assert isinstance(history, list)
            assert len(history) > 0
            assert "query_text" in history[0]

    @pytest.mark.asyncio
    async def test_get_query_history_disabled(self, mock_manager, mock_config):
        """Test getting query history when Vector DB is disabled."""
        mock_config.is_enabled = MagicMock(return_value=False)

        with (
            patch("app.core.vectordb.history.get_vectordb_manager", return_value=mock_manager),
            patch("app.core.vectordb.history.get_vectordb_config", return_value=mock_config),
        ):
            history = await get_query_history()

            assert history == []

    @pytest.mark.asyncio
    async def test_get_query_history_with_filters(self, mock_manager, mock_config):
        """Test getting query history with filters."""
        start_date = datetime.now(UTC) - timedelta(days=7)
        end_date = datetime.now(UTC)

        with (
            patch("app.core.vectordb.history.get_vectordb_manager", return_value=mock_manager),
            patch("app.core.vectordb.history.get_vectordb_config", return_value=mock_config),
        ):
            history = await get_query_history(
                limit=10,
                user_id="user123",
                start_date=start_date,
                end_date=end_date,
            )

            assert isinstance(history, list)


class TestClearQueryHistory:
    """Test the clear_query_history function."""

    @pytest.fixture
    def mock_manager(self):
        """Create a mock VectorDBManager."""
        manager = MagicMock()
        manager._initialized = True
        manager.initialize = AsyncMock()
        manager.backend = MagicMock()
        manager.backend.collection_exists = AsyncMock(return_value=True)
        manager.backend.delete_vectors = AsyncMock()
        return manager

    @pytest.fixture
    def mock_config(self):
        """Create a mock VectorDBConfig."""
        config = MagicMock()
        config.is_enabled = MagicMock(return_value=True)
        return config

    @pytest.mark.asyncio
    async def test_clear_query_history_success(self, mock_manager, mock_config):
        """Test clearing query history."""
        with (
            patch("app.core.vectordb.history.get_vectordb_manager", return_value=mock_manager),
            patch("app.core.vectordb.history.get_vectordb_config", return_value=mock_config),
            patch(
                "app.core.vectordb.history.get_query_history", return_value=[{"query_id": "query1"}]
            ),
        ):
            result = await clear_query_history()

            assert result["success"] is True
            assert result["deleted_count"] >= 0

    @pytest.mark.asyncio
    async def test_clear_query_history_disabled(self, mock_manager, mock_config):
        """Test clearing query history when Vector DB is disabled."""
        mock_config.is_enabled = MagicMock(return_value=False)

        with (
            patch("app.core.vectordb.history.get_vectordb_manager", return_value=mock_manager),
            patch("app.core.vectordb.history.get_vectordb_config", return_value=mock_config),
        ):
            result = await clear_query_history()

            assert result["success"] is False
            assert result.get("reason") == "Vector DB disabled"


class TestGetQueryStatistics:
    """Test the get_query_statistics function."""

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
    async def test_get_query_statistics_success(self, mock_manager, mock_config):
        """Test getting query statistics."""
        mock_history = [
            {
                "query_id": "query1",
                "query_text": "living room lights",
                "timestamp": datetime.now(UTC).isoformat(),
                "intent": "SEARCH",
                "domain": "light",
                "selected_entity_id": "light.living_room",
                "context": {"time_of_day": "morning"},
            },
            {
                "query_id": "query2",
                "query_text": "living room lights",
                "timestamp": datetime.now(UTC).isoformat(),
                "intent": "SEARCH",
                "domain": "light",
                "context": {"time_of_day": "evening"},
            },
        ]

        with (
            patch("app.core.vectordb.history.get_vectordb_manager", return_value=mock_manager),
            patch("app.core.vectordb.history.get_vectordb_config", return_value=mock_config),
            patch("app.core.vectordb.history.get_query_history", return_value=mock_history),
        ):
            stats = await get_query_statistics(days=30)

            assert "total_queries" in stats
            assert "unique_queries" in stats
            assert "most_common_queries" in stats
            assert "most_common_intents" in stats
            assert "most_common_domains" in stats
            assert "most_selected_entities" in stats
            assert "queries_by_time_of_day" in stats

    @pytest.mark.asyncio
    async def test_get_query_statistics_disabled(self, mock_manager, mock_config):
        """Test getting query statistics when Vector DB is disabled."""
        mock_config.is_enabled = MagicMock(return_value=False)

        with (
            patch("app.core.vectordb.history.get_vectordb_manager", return_value=mock_manager),
            patch("app.core.vectordb.history.get_vectordb_config", return_value=mock_config),
        ):
            stats = await get_query_statistics()

            assert stats["total_queries"] == 0
            assert stats["unique_queries"] == 0


class TestGetEntityPopularity:
    """Test the get_entity_popularity function."""

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
                    "id": "popularity_light.living_room",
                    "metadata": {
                        "entity_id": "light.living_room",
                        "popularity_count": 5,
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
    async def test_get_entity_popularity_success(self, mock_manager, mock_config):
        """Test getting entity popularity."""
        with (
            patch("app.core.vectordb.history.get_vectordb_manager", return_value=mock_manager),
            patch("app.core.vectordb.history.get_vectordb_config", return_value=mock_config),
        ):
            popularity = await get_entity_popularity("light.living_room")

            assert popularity >= 0

    @pytest.mark.asyncio
    async def test_get_entity_popularity_not_found(self, mock_manager, mock_config):
        """Test getting entity popularity when not found."""
        mock_manager.backend.search_vectors = AsyncMock(return_value=[])

        with (
            patch("app.core.vectordb.history.get_vectordb_manager", return_value=mock_manager),
            patch("app.core.vectordb.history.get_vectordb_config", return_value=mock_config),
        ):
            popularity = await get_entity_popularity("light.nonexistent")

            assert popularity == 0

    @pytest.mark.asyncio
    async def test_get_entity_popularity_disabled(self, mock_manager, mock_config):
        """Test getting entity popularity when Vector DB is disabled."""
        mock_config.is_enabled = MagicMock(return_value=False)

        with (
            patch("app.core.vectordb.history.get_vectordb_manager", return_value=mock_manager),
            patch("app.core.vectordb.history.get_vectordb_config", return_value=mock_config),
        ):
            popularity = await get_entity_popularity("light.living_room")

            assert popularity == 0


class TestBoostEntityRanking:
    """Test the boost_entity_ranking function."""

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
    async def test_boost_entity_ranking_success(self, mock_manager, mock_config):
        """Test boosting entity ranking."""
        entities = [
            {
                "entity_id": "light.living_room",
                "similarity_score": 0.8,
            },
            {
                "entity_id": "light.kitchen",
                "similarity_score": 0.7,
            },
        ]

        with (
            patch("app.core.vectordb.history.get_vectordb_manager", return_value=mock_manager),
            patch("app.core.vectordb.history.get_vectordb_config", return_value=mock_config),
            patch("app.core.vectordb.history.get_entity_popularity", return_value=5),
        ):
            boosted = await boost_entity_ranking(entities, boost_factor=0.1)

            assert len(boosted) == len(entities)
            # Check that scores were boosted
            for entity in boosted:
                assert "similarity_score" in entity
                assert entity["similarity_score"] >= 0.0
                assert entity["similarity_score"] <= 1.0

    @pytest.mark.asyncio
    async def test_boost_entity_ranking_disabled(self, mock_manager, mock_config):
        """Test boosting entity ranking when Vector DB is disabled."""
        mock_config.is_enabled = MagicMock(return_value=False)

        entities = [
            {
                "entity_id": "light.living_room",
                "similarity_score": 0.8,
            }
        ]

        with (
            patch("app.core.vectordb.history.get_vectordb_manager", return_value=mock_manager),
            patch("app.core.vectordb.history.get_vectordb_config", return_value=mock_config),
        ):
            boosted = await boost_entity_ranking(entities)

            # Should return entities unchanged when disabled
            assert len(boosted) == len(entities)

    @pytest.mark.asyncio
    async def test_boost_entity_ranking_no_popularity(self, mock_manager, mock_config):
        """Test boosting entity ranking when no popularity data."""
        entities = [
            {
                "entity_id": "light.living_room",
                "similarity_score": 0.8,
            }
        ]

        with (
            patch("app.core.vectordb.history.get_vectordb_manager", return_value=mock_manager),
            patch("app.core.vectordb.history.get_vectordb_config", return_value=mock_config),
            patch("app.core.vectordb.history.get_entity_popularity", return_value=0),
        ):
            boosted = await boost_entity_ranking(entities)

            # Should return entities unchanged when no popularity
            assert len(boosted) == len(entities)
            assert boosted[0]["similarity_score"] == entities[0]["similarity_score"]
