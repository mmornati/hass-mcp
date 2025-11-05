"""Unit tests for app.core.vectordb.config module."""

import os
from unittest.mock import patch

from app.core.vectordb.config import VectorDBConfig, get_vectordb_config


class TestVectorDBConfig:
    """Test the VectorDBConfig class."""

    def test_default_config(self):
        """Test default configuration values."""
        with patch.dict(os.environ, {}, clear=True):
            config = VectorDBConfig()

            assert config.get_backend() == "chroma"
            assert config.get_embedding_model() == "sentence-transformers"
            assert config.get_embedding_model_name() == "all-MiniLM-L6-v2"
            assert config.get_embedding_dimensions() == 384
            assert config.get_chroma_path() == ".vectordb"
            assert config.is_enabled() is True

    def test_custom_backend(self):
        """Test custom backend configuration."""
        with patch.dict(os.environ, {"HASS_MCP_VECTOR_DB_BACKEND": "qdrant"}, clear=False):
            config = VectorDBConfig()
            assert config.get_backend() == "qdrant"

    def test_custom_embedding_model(self):
        """Test custom embedding model configuration."""
        with patch.dict(
            os.environ,
            {
                "HASS_MCP_EMBEDDING_MODEL": "openai",
                "HASS_MCP_EMBEDDING_MODEL_NAME": "text-embedding-3-small",
            },
            clear=False,
        ):
            config = VectorDBConfig()
            assert config.get_embedding_model() == "openai"
            assert config.get_embedding_model_name() == "text-embedding-3-small"

    def test_chroma_path(self):
        """Test Chroma path configuration."""
        with patch.dict(os.environ, {"HASS_MCP_VECTOR_DB_PATH": "/custom/path"}, clear=False):
            config = VectorDBConfig()
            assert config.get_chroma_path() == "/custom/path"

    def test_qdrant_config(self):
        """Test Qdrant configuration."""
        with patch.dict(
            os.environ,
            {
                "HASS_MCP_QDRANT_URL": "http://localhost:6333",
                "HASS_MCP_QDRANT_API_KEY": "test_key",
            },
            clear=False,
        ):
            config = VectorDBConfig()
            assert config.get_qdrant_url() == "http://localhost:6333"
            assert config.get_qdrant_api_key() == "test_key"

    def test_weaviate_config(self):
        """Test Weaviate configuration."""
        with patch.dict(
            os.environ,
            {
                "HASS_MCP_WEAVIATE_URL": "http://localhost:8080",
                "HASS_MCP_WEAVIATE_API_KEY": "test_key",
            },
            clear=False,
        ):
            config = VectorDBConfig()
            assert config.get_weaviate_url() == "http://localhost:8080"
            assert config.get_weaviate_api_key() == "test_key"

    def test_pinecone_config(self):
        """Test Pinecone configuration."""
        with patch.dict(
            os.environ,
            {
                "HASS_MCP_PINECONE_API_KEY": "test_key",
                "HASS_MCP_PINECONE_ENVIRONMENT": "us-east-1",
            },
            clear=False,
        ):
            config = VectorDBConfig()
            assert config.get_pinecone_api_key() == "test_key"
            assert config.get_pinecone_environment() == "us-east-1"

    def test_openai_config(self):
        """Test OpenAI configuration."""
        with patch.dict(os.environ, {"HASS_MCP_OPENAI_API_KEY": "sk-test"}, clear=False):
            config = VectorDBConfig()
            assert config.get_openai_api_key() == "sk-test"

    def test_cohere_config(self):
        """Test Cohere configuration."""
        with patch.dict(os.environ, {"HASS_MCP_COHERE_API_KEY": "test_key"}, clear=False):
            config = VectorDBConfig()
            assert config.get_cohere_api_key() == "test_key"

    def test_disabled(self):
        """Test disabled configuration."""
        with patch.dict(os.environ, {"HASS_MCP_VECTOR_DB_ENABLED": "false"}, clear=False):
            config = VectorDBConfig()
            assert config.is_enabled() is False

    def test_get_all_config(self):
        """Test getting all configuration."""
        config = VectorDBConfig()
        all_config = config.get_all_config()
        assert isinstance(all_config, dict)
        assert "backend" in all_config
        assert "embedding_model" in all_config


class TestGetVectorDBConfig:
    """Test the get_vectordb_config function."""

    def test_singleton_pattern(self):
        """Test that get_vectordb_config returns a singleton."""

        # Reset singleton
        import app.core.vectordb.config as config_module

        config_module._vectordb_config = None

        config1 = get_vectordb_config()
        config2 = get_vectordb_config()

        assert config1 is config2
