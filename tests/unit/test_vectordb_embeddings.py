"""Unit tests for app.core.vectordb.embeddings module."""

from unittest.mock import MagicMock, patch

import pytest

from app.core.vectordb.config import VectorDBConfig
from app.core.vectordb.embeddings import EmbeddingModel


class TestEmbeddingModel:
    """Test the EmbeddingModel class."""

    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        return VectorDBConfig()

    @pytest.mark.asyncio
    async def test_initialize_sentence_transformers(self, config):
        """Test initializing sentence-transformers model."""
        mock_model = MagicMock()
        mock_model.encode.return_value = [[0.1, 0.2, 0.3]]

        mock_sentence_transformers = MagicMock()
        mock_sentence_transformers.SentenceTransformer = MagicMock(return_value=mock_model)

        def mock_import(name, *args, **kwargs):
            if name == "sentence_transformers":
                return mock_sentence_transformers
            return __import__(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            model = EmbeddingModel(config)
            await model.initialize()
            assert model._initialized is True
            assert model._model is not None

    @pytest.mark.asyncio
    async def test_initialize_sentence_transformers_import_error(self, config):
        """Test initialization with missing sentence-transformers."""

        def mock_import(name, *args, **kwargs):
            if name == "sentence_transformers":
                raise ImportError("No module named 'sentence_transformers'")
            return __import__(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            model = EmbeddingModel(config)
            with pytest.raises(ImportError, match="sentence-transformers not installed"):
                await model.initialize()

    @pytest.mark.asyncio
    async def test_initialize_openai(self, config):
        """Test initializing OpenAI model."""
        with patch.dict(
            "os.environ",
            {
                "HASS_MCP_EMBEDDING_MODEL": "openai",
                "HASS_MCP_OPENAI_API_KEY": "sk-test",
            },
            clear=False,
        ):
            config = VectorDBConfig()
            mock_client = MagicMock()
            mock_openai_module = MagicMock()
            mock_openai_module.OpenAI = MagicMock(return_value=mock_client)

            def mock_import(name, *args, **kwargs):
                if name == "openai":
                    return mock_openai_module
                return __import__(name, *args, **kwargs)

            with patch("builtins.__import__", side_effect=mock_import):
                model = EmbeddingModel(config)
                await model.initialize()
                assert model._initialized is True

    @pytest.mark.asyncio
    async def test_initialize_openai_missing_key(self, config):
        """Test OpenAI initialization without API key."""
        with patch.dict(
            "os.environ",
            {"HASS_MCP_EMBEDDING_MODEL": "openai"},
            clear=False,
        ):
            config = VectorDBConfig()
            model = EmbeddingModel(config)
            with pytest.raises(ValueError, match="OpenAI API key not configured"):
                await model.initialize()

    @pytest.mark.asyncio
    async def test_embed_sentence_transformers(self, config):
        """Test embedding with sentence-transformers."""
        mock_model = MagicMock()
        # Mock numpy array-like return value
        mock_emb1 = MagicMock()
        mock_emb1.tolist.return_value = [0.1, 0.2, 0.3]
        mock_emb2 = MagicMock()
        mock_emb2.tolist.return_value = [0.4, 0.5, 0.6]
        mock_embeddings_array = [mock_emb1, mock_emb2]
        mock_model.encode.return_value = mock_embeddings_array

        mock_sentence_transformers = MagicMock()
        mock_sentence_transformers.SentenceTransformer = MagicMock(return_value=mock_model)

        original_import = __import__

        def mock_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "sentence_transformers":
                return mock_sentence_transformers
            return original_import(name, globals, locals, fromlist, level)

        with patch("builtins.__import__", side_effect=mock_import):
            model = EmbeddingModel(config)
            await model.initialize()
            # Mock the encode method to return the embeddings directly (no executor needed)
            model._model.encode = MagicMock(return_value=mock_embeddings_array)
            embeddings = await model.embed(["text1", "text2"])
            assert len(embeddings) == 2
            assert embeddings[0] == [0.1, 0.2, 0.3]

    @pytest.mark.asyncio
    async def test_embed_openai(self, config):
        """Test embedding with OpenAI."""
        with patch.dict(
            "os.environ",
            {
                "HASS_MCP_EMBEDDING_MODEL": "openai",
                "HASS_MCP_OPENAI_API_KEY": "sk-test",
            },
            clear=False,
        ):
            config = VectorDBConfig()
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.data = [
                MagicMock(embedding=[0.1, 0.2, 0.3]),
                MagicMock(embedding=[0.4, 0.5, 0.6]),
            ]
            mock_client.embeddings.create.return_value = mock_response
            mock_openai_module = MagicMock()
            mock_openai_module.OpenAI = MagicMock(return_value=mock_client)

            def mock_import(name, *args, **kwargs):
                if name == "openai":
                    return mock_openai_module
                return __import__(name, *args, **kwargs)

            with patch("builtins.__import__", side_effect=mock_import):
                model = EmbeddingModel(config)
                await model.initialize()
                embeddings = await model.embed(["text1", "text2"])
                assert len(embeddings) == 2
                assert embeddings[0] == [0.1, 0.2, 0.3]

    @pytest.mark.asyncio
    async def test_get_dimensions(self, config):
        """Test getting embedding dimensions."""
        model = EmbeddingModel(config)
        dimensions = model.get_dimensions()
        assert dimensions == 384  # Default for all-MiniLM-L6-v2

    @pytest.mark.asyncio
    async def test_close(self, config):
        """Test closing the model."""
        mock_model = MagicMock()
        mock_sentence_transformers = MagicMock()
        mock_sentence_transformers.SentenceTransformer = MagicMock(return_value=mock_model)

        def mock_import(name, *args, **kwargs):
            if name == "sentence_transformers":
                return mock_sentence_transformers
            return __import__(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            model = EmbeddingModel(config)
            await model.initialize()
            await model.close()
            assert model._model is None
            assert model._initialized is False
