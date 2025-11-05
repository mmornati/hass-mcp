"""Unit tests for app.core.vectordb.manager module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.vectordb.config import VectorDBConfig
from app.core.vectordb.manager import VectorDBManager, get_vectordb_manager


class TestVectorDBManager:
    """Test the VectorDBManager class."""

    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        return VectorDBConfig()

    @pytest.mark.asyncio
    async def test_initialize_success(self, config):
        """Test successful initialization."""
        mock_backend = MagicMock()
        mock_backend.health_check = AsyncMock(return_value=True)
        mock_backend.initialize = AsyncMock()

        mock_embedding = MagicMock()
        mock_embedding.initialize = AsyncMock()

        mock_sentence_transformers = MagicMock()
        mock_sentence_transformers.SentenceTransformer = MagicMock(return_value=MagicMock())

        def mock_import(name, *args, **kwargs):
            if name == "sentence_transformers":
                return mock_sentence_transformers
            return __import__(name, *args, **kwargs)

        with (
            patch("builtins.__import__", side_effect=mock_import),
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
            await manager.initialize()
            assert manager._initialized is True
            assert manager.backend is not None
            assert manager.embedding_model is not None

    @pytest.mark.asyncio
    async def test_initialize_disabled(self, config):
        """Test initialization when vector DB is disabled."""
        with patch.dict("os.environ", {"HASS_MCP_VECTOR_DB_ENABLED": "false"}, clear=False):
            config = VectorDBConfig()
            manager = VectorDBManager(config)
            await manager.initialize()
            assert manager._initialized is False
            assert manager.backend is None

    @pytest.mark.asyncio
    async def test_initialize_unsupported_backend(self, config):
        """Test initialization with unsupported backend."""
        with patch.dict("os.environ", {"HASS_MCP_VECTOR_DB_BACKEND": "invalid"}, clear=False):
            config = VectorDBConfig()
            manager = VectorDBManager(config)
            # The error should be raised before trying to initialize embedding model
            # but we need to mock it just in case
            mock_sentence_transformers = MagicMock()
            mock_sentence_transformers.SentenceTransformer = MagicMock(return_value=MagicMock())

            original_import = __import__

            def mock_import(name, globals=None, locals=None, fromlist=(), level=0):
                if name == "sentence_transformers":
                    return mock_sentence_transformers
                return original_import(name, globals, locals, fromlist, level)

            with patch("builtins.__import__", side_effect=mock_import):
                with pytest.raises(ValueError, match="Unsupported vector DB backend"):
                    await manager.initialize()

    @pytest.mark.asyncio
    async def test_health_check_success(self, config):
        """Test successful health check."""
        mock_backend = MagicMock()
        mock_backend.health_check = AsyncMock(return_value=True)
        mock_backend.initialize = AsyncMock()

        mock_embedding = MagicMock()
        mock_embedding.initialize = AsyncMock()

        mock_sentence_transformers = MagicMock()
        mock_sentence_transformers.SentenceTransformer = MagicMock(return_value=MagicMock())

        def mock_import(name, *args, **kwargs):
            if name == "sentence_transformers":
                return mock_sentence_transformers
            return __import__(name, *args, **kwargs)

        with (
            patch("builtins.__import__", side_effect=mock_import),
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
            result = await manager.health_check()
            assert result is True

    @pytest.mark.asyncio
    async def test_embed_texts(self, config):
        """Test embedding texts."""
        mock_backend = MagicMock()
        mock_backend.health_check = AsyncMock(return_value=True)
        mock_backend.initialize = AsyncMock()

        mock_embedding = MagicMock()
        mock_embedding.initialize = AsyncMock()
        mock_embedding.embed = AsyncMock(return_value=[[0.1, 0.2, 0.3]])

        mock_sentence_transformers = MagicMock()
        mock_sentence_transformers.SentenceTransformer = MagicMock(return_value=MagicMock())

        def mock_import(name, *args, **kwargs):
            if name == "sentence_transformers":
                return mock_sentence_transformers
            return __import__(name, *args, **kwargs)

        with (
            patch("builtins.__import__", side_effect=mock_import),
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
            await manager.initialize()
            embeddings = await manager.embed_texts(["text1"])
            assert embeddings == [[0.1, 0.2, 0.3]]

    @pytest.mark.asyncio
    async def test_add_vectors(self, config):
        """Test adding vectors."""
        mock_backend = MagicMock()
        mock_backend.health_check = AsyncMock(return_value=True)
        mock_backend.initialize = AsyncMock()
        mock_backend.collection_exists = AsyncMock(return_value=True)
        mock_backend.add_vectors = AsyncMock()

        mock_embedding = MagicMock()
        mock_embedding.initialize = AsyncMock()
        mock_embedding.embed = AsyncMock(return_value=[[0.1, 0.2, 0.3]])

        mock_sentence_transformers = MagicMock()
        mock_sentence_transformers.SentenceTransformer = MagicMock(return_value=MagicMock())

        def mock_import(name, *args, **kwargs):
            if name == "sentence_transformers":
                return mock_sentence_transformers
            return __import__(name, *args, **kwargs)

        with (
            patch("builtins.__import__", side_effect=mock_import),
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
            await manager.initialize()
            await manager.add_vectors("test_collection", ["text1"], ["id1"])
            mock_backend.add_vectors.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_vectors(self, config):
        """Test searching vectors."""
        mock_backend = MagicMock()
        mock_backend.health_check = AsyncMock(return_value=True)
        mock_backend.initialize = AsyncMock()
        mock_backend.search_vectors = AsyncMock(
            return_value=[{"id": "id1", "distance": 0.1, "metadata": {}}]
        )

        mock_embedding = MagicMock()
        mock_embedding.initialize = AsyncMock()
        mock_embedding.embed = AsyncMock(return_value=[[0.1, 0.2, 0.3]])

        mock_sentence_transformers = MagicMock()
        mock_sentence_transformers.SentenceTransformer = MagicMock(return_value=MagicMock())

        def mock_import(name, *args, **kwargs):
            if name == "sentence_transformers":
                return mock_sentence_transformers
            return __import__(name, *args, **kwargs)

        with (
            patch("builtins.__import__", side_effect=mock_import),
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
            await manager.initialize()
            results = await manager.search_vectors("test_collection", "query text")
            assert len(results) == 1
            assert results[0]["id"] == "id1"

    @pytest.mark.asyncio
    async def test_close(self, config):
        """Test closing the manager."""
        mock_backend = MagicMock()
        mock_backend.health_check = AsyncMock(return_value=True)
        mock_backend.initialize = AsyncMock()
        mock_backend.close = AsyncMock()

        mock_embedding = MagicMock()
        mock_embedding.initialize = AsyncMock()
        mock_embedding.close = AsyncMock()

        mock_sentence_transformers = MagicMock()
        mock_sentence_transformers.SentenceTransformer = MagicMock(return_value=MagicMock())

        def mock_import(name, *args, **kwargs):
            if name == "sentence_transformers":
                return mock_sentence_transformers
            return __import__(name, *args, **kwargs)

        with (
            patch("builtins.__import__", side_effect=mock_import),
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
            await manager.initialize()
            await manager.close()
            assert manager._initialized is False
            mock_backend.close.assert_called_once()
            mock_embedding.close.assert_called_once()


class TestGetVectorDBManager:
    """Test the get_vectordb_manager function."""

    def test_singleton_pattern(self):
        """Test that get_vectordb_manager returns a singleton."""

        # Reset singleton
        import app.core.vectordb.manager as manager_module

        manager_module._vectordb_manager = None

        manager1 = get_vectordb_manager()
        manager2 = get_vectordb_manager()

        assert manager1 is manager2
