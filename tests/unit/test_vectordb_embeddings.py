"""Unit tests for app.core.vectordb.embeddings module."""

from unittest.mock import MagicMock, patch

import pytest

# Mock sentence_transformers module for testing
mock_sentence_transformers = MagicMock()
mock_sentence_transformers.SentenceTransformer = MagicMock

# Mock openai module for testing
mock_openai = MagicMock()
mock_openai.OpenAI = MagicMock

# Mock cohere module for testing
mock_cohere = MagicMock()
mock_cohere.Client = MagicMock

# Patch modules before importing
with patch.dict(
    "sys.modules",
    {
        "sentence_transformers": mock_sentence_transformers,
        "openai": mock_openai,
        "cohere": mock_cohere,
    },
):
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

        mock_sentence_transformers.SentenceTransformer.return_value = mock_model
        model = EmbeddingModel(config)
        await model.initialize()
        assert model._initialized is True
        assert model._model is not None

    @pytest.mark.asyncio
    async def test_initialize_sentence_transformers_import_error(self, config):
        """Test initialization with missing sentence-transformers."""
        import app.core.vectordb.embeddings as embeddings_module

        original_st = embeddings_module.sentence_transformers
        try:
            embeddings_module.sentence_transformers = None
            model = EmbeddingModel(config)
            with pytest.raises(ImportError, match="sentence-transformers not installed"):
                await model.initialize()
        finally:
            embeddings_module.sentence_transformers = original_st

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
            mock_openai.OpenAI.return_value = mock_client
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
        mock_embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        # Create mock objects with tolist method
        mock_emb1 = MagicMock()
        mock_emb1.tolist.return_value = [0.1, 0.2, 0.3]
        mock_emb2 = MagicMock()
        mock_emb2.tolist.return_value = [0.4, 0.5, 0.6]
        mock_embeddings_array = [mock_emb1, mock_emb2]
        mock_model.encode.return_value = mock_embeddings_array

        mock_sentence_transformers.SentenceTransformer.return_value = mock_model
        model = EmbeddingModel(config)
        await model.initialize()
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
            mock_openai.OpenAI.return_value = mock_client

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
        mock_sentence_transformers.SentenceTransformer.return_value = mock_model
        model = EmbeddingModel(config)
        await model.initialize()
        await model.close()
        assert model._model is None
        assert model._initialized is False
