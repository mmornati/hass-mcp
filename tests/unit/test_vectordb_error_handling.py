"""Unit tests for vector DB error handling and fallbacks."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.vectordb.config import VectorDBConfig
from app.core.vectordb.manager import VectorDBManager
from app.core.vectordb.search import semantic_search


class TestErrorHandling:
    """Test error handling and fallback behavior."""

    @pytest.mark.asyncio
    async def test_manager_initialization_error(self):
        """Test manager initialization with backend error."""
        config = VectorDBConfig()
        config._config_data["backend"] = "invalid_backend"

        manager = VectorDBManager(config)
        with pytest.raises((ValueError, NotImplementedError)):
            await manager.initialize()

    @pytest.mark.asyncio
    async def test_manager_embedding_error(self):
        """Test manager initialization with embedding model error."""
        config = VectorDBConfig()
        config._config_data["embedding_model"] = "invalid_model"

        manager = VectorDBManager(config)
        with pytest.raises((ValueError, NotImplementedError, ImportError)):
            await manager.initialize()

    @pytest.mark.asyncio
    async def test_backend_health_check_failure(self):
        """Test manager with failing health check."""
        mock_backend = MagicMock()
        mock_backend.health_check = AsyncMock(return_value=False)
        mock_backend.initialize = AsyncMock()

        mock_embedding = MagicMock()
        mock_embedding.initialize = AsyncMock()

        config = VectorDBConfig()

        with (
            patch(
                "app.core.vectordb.manager.ChromaBackend",
                return_value=mock_backend,
            ),
            patch(
                "app.core.vectordb.manager.EmbeddingModel",
                return_value=mock_embedding,
            ),
        ):
            manager = VectorDBManager(config)
            with pytest.raises(RuntimeError, match="health check"):
                await manager.initialize()

    @pytest.mark.asyncio
    async def test_search_fallback_to_keyword(self):
        """Test semantic search fallback to keyword search."""
        with (
            patch("app.core.vectordb.search.get_vectordb_manager") as mock_manager_getter,
            patch("app.core.vectordb.search.get_entities") as mock_get_entities,
        ):
            mock_manager = MagicMock()
            mock_manager.config.is_enabled = MagicMock(return_value=True)
            mock_manager.embed_texts = AsyncMock(side_effect=Exception("Embedding error"))
            mock_manager_getter.return_value = mock_manager

            mock_get_entities.return_value = [
                {"entity_id": "light.living_room", "friendly_name": "Living Room Light"},
            ]

            results = await semantic_search("light", limit=10)

            assert isinstance(results, list)
            assert len(results) > 0
            mock_get_entities.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_disabled_vectordb(self):
        """Test semantic search when vector DB is disabled."""
        with (
            patch("app.core.vectordb.search.get_vectordb_manager") as mock_manager_getter,
            patch("app.core.vectordb.search.get_entities") as mock_get_entities,
        ):
            mock_manager = MagicMock()
            mock_manager.config.is_enabled = MagicMock(return_value=False)
            mock_manager_getter.return_value = mock_manager

            mock_get_entities.return_value = [
                {"entity_id": "light.living_room", "friendly_name": "Living Room Light"},
            ]

            results = await semantic_search("light", limit=10)

            assert isinstance(results, list)
            mock_get_entities.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_empty_results(self):
        """Test semantic search with empty results."""
        with (
            patch("app.core.vectordb.search.get_vectordb_manager") as mock_manager_getter,
            patch("app.core.vectordb.search.get_entities") as mock_get_entities,
        ):
            mock_manager = MagicMock()
            mock_manager.config.is_enabled = MagicMock(return_value=True)
            mock_manager.embed_texts = AsyncMock(return_value=[[0.1] * 384])
            mock_manager.search_vectors = AsyncMock(return_value=[])
            mock_manager_getter.return_value = mock_manager

            mock_get_entities.return_value = []

            results = await semantic_search("nonexistent", limit=10)

            assert isinstance(results, list)
            assert len(results) == 0

    @pytest.mark.asyncio
    async def test_manager_embed_texts_error(self):
        """Test manager embed_texts with error."""
        config = VectorDBConfig()
        manager = VectorDBManager(config)

        # Manager not initialized
        with pytest.raises(RuntimeError, match="not initialized"):
            await manager.embed_texts(["test"])

    @pytest.mark.asyncio
    async def test_manager_search_vectors_error(self):
        """Test manager search_vectors with error."""
        config = VectorDBConfig()
        manager = VectorDBManager(config)

        # Manager not initialized
        with pytest.raises(RuntimeError, match="not initialized"):
            await manager.search_vectors("collection", [0.1] * 384, limit=10)

    @pytest.mark.asyncio
    async def test_manager_add_vectors_error(self):
        """Test manager add_vectors with error."""
        config = VectorDBConfig()
        manager = VectorDBManager(config)

        # Manager not initialized
        with pytest.raises(RuntimeError, match="not initialized"):
            await manager.add_vectors("collection", ["id"], [[0.1] * 384], [{}])

    @pytest.mark.asyncio
    async def test_manager_update_vectors_error(self):
        """Test manager update_vectors with error."""
        config = VectorDBConfig()
        manager = VectorDBManager(config)

        # Manager not initialized
        with pytest.raises(RuntimeError, match="not initialized"):
            await manager.update_vectors("collection", ["id"], [[0.1] * 384], [{}])

    @pytest.mark.asyncio
    async def test_manager_delete_vectors_error(self):
        """Test manager delete_vectors with error."""
        config = VectorDBConfig()
        manager = VectorDBManager(config)

        # Manager not initialized
        with pytest.raises(RuntimeError, match="not initialized"):
            await manager.delete_vectors("collection", ["id"])

    @pytest.mark.asyncio
    async def test_manager_close_not_initialized(self):
        """Test manager close when not initialized."""
        config = VectorDBConfig()
        manager = VectorDBManager(config)

        # Should not raise error
        await manager.close()

    @pytest.mark.asyncio
    async def test_manager_health_check_not_initialized(self):
        """Test manager health_check when not initialized."""
        config = VectorDBConfig()
        manager = VectorDBManager(config)

        result = await manager.health_check()
        assert result is False  # health_check returns bool, not dict
