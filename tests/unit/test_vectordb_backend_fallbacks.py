"""Unit tests for vector DB backend fallback behavior."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.vectordb.config import VectorDBConfig
from app.core.vectordb.manager import VectorDBManager


class TestBackendFallbacks:
    """Test fallback behavior for unsupported backends."""

    @pytest.mark.asyncio
    async def test_qdrant_backend_not_implemented(self):
        """Test that Qdrant backend is not yet implemented."""
        config = VectorDBConfig()
        config._config_data["backend"] = "qdrant"

        manager = VectorDBManager(config)
        with pytest.raises(NotImplementedError, match="not yet implemented"):
            await manager.initialize()

    @pytest.mark.asyncio
    async def test_weaviate_backend_not_implemented(self):
        """Test that Weaviate backend is not yet implemented."""
        config = VectorDBConfig()
        config._config_data["backend"] = "weaviate"

        manager = VectorDBManager(config)
        with pytest.raises(NotImplementedError, match="not yet implemented"):
            await manager.initialize()

    @pytest.mark.asyncio
    async def test_pinecone_backend_not_implemented(self):
        """Test that Pinecone backend is not yet implemented."""
        config = VectorDBConfig()
        config._config_data["backend"] = "pinecone"

        manager = VectorDBManager(config)
        with pytest.raises(NotImplementedError, match="not yet implemented"):
            await manager.initialize()

    @pytest.mark.asyncio
    async def test_invalid_backend_fallback(self):
        """Test fallback behavior for invalid backend."""
        config = VectorDBConfig()
        config._config_data["backend"] = "invalid_backend"

        manager = VectorDBManager(config)
        with pytest.raises(ValueError, match="Unsupported"):
            await manager.initialize()

    @pytest.mark.asyncio
    async def test_chroma_backend_import_error(self):
        """Test fallback when Chroma backend import fails."""
        config = VectorDBConfig()
        config._config_data["backend"] = "chroma"

        def mock_import(name, *args, **kwargs):
            if name == "chromadb":
                raise ImportError("chromadb not available")
            return __import__(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            manager = VectorDBManager(config)
            with pytest.raises((ImportError, Exception)):
                await manager.initialize()

    @pytest.mark.asyncio
    async def test_chroma_backend_initialization_error(self):
        """Test fallback when Chroma backend initialization fails."""
        config = VectorDBConfig()

        mock_chroma_backend = MagicMock()
        mock_chroma_backend.initialize = AsyncMock(side_effect=Exception("Initialization error"))
        mock_chroma_backend.health_check = AsyncMock(return_value=True)

        with patch(
            "app.core.vectordb.manager.ChromaBackend",
            return_value=mock_chroma_backend,
        ):
            manager = VectorDBManager(config)
            with pytest.raises(Exception, match="Initialization error"):
                await manager.initialize()

    @pytest.mark.asyncio
    async def test_embedding_model_fallback(self):
        """Test fallback when embedding model is not available."""
        config = VectorDBConfig()
        config._config_data["embedding_model"] = "invalid_model"

        manager = VectorDBManager(config)
        with pytest.raises((ValueError, NotImplementedError, ImportError)):
            await manager.initialize()

    @pytest.mark.asyncio
    async def test_sentence_transformers_import_error(self):
        """Test fallback when sentence-transformers import fails."""
        config = VectorDBConfig()
        config._config_data["embedding_model"] = "sentence-transformers"

        def mock_import(name, *args, **kwargs):
            if name == "sentence_transformers":
                raise ImportError("sentence_transformers not available")
            return __import__(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            manager = VectorDBManager(config)
            with pytest.raises((ImportError, Exception)):
                await manager.initialize()

    @pytest.mark.asyncio
    async def test_openai_embedding_api_key_missing(self):
        """Test fallback when OpenAI API key is missing."""
        config = VectorDBConfig()
        config._config_data["embedding_model"] = "openai"
        config._config_data["openai_api_key"] = None

        manager = VectorDBManager(config)
        with pytest.raises((ValueError, Exception)):
            await manager.initialize()

    @pytest.mark.asyncio
    async def test_cohere_embedding_api_key_missing(self):
        """Test fallback when Cohere API key is missing."""
        config = VectorDBConfig()
        config._config_data["embedding_model"] = "cohere"
        config._config_data["cohere_api_key"] = None

        manager = VectorDBManager(config)
        with pytest.raises((ValueError, Exception)):
            await manager.initialize()
