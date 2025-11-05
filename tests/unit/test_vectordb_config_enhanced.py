"""Unit tests for enhanced VectorDBConfig functionality."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from app.core.vectordb.config import VectorDBConfig


class TestConfigFileLoading:
    """Test configuration file loading."""

    def test_load_json_config_file(self):
        """Test loading configuration from JSON file."""
        config_data = {
            "vector_db": {
                "backend": "qdrant",
                "embedding_model": "openai",
                "embedding_model_name": "text-embedding-3-small",
                "chroma_path": "/custom/path",
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name

        try:
            config = VectorDBConfig(config_file=config_file)
            assert config.get_backend() == "qdrant"
            assert config.get_embedding_model() == "openai"
            assert config.get_embedding_model_name() == "text-embedding-3-small"
            assert config.get_chroma_path() == "/custom/path"
            assert config.get_config_file_path() == config_file
        finally:
            os.unlink(config_file)

    def test_load_json_config_file_no_vector_db_section(self):
        """Test loading JSON config without vector_db section."""
        config_data = {
            "backend": "weaviate",
            "embedding_model": "cohere",
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name

        try:
            config = VectorDBConfig(config_file=config_file)
            assert config.get_backend() == "weaviate"
            assert config.get_embedding_model() == "cohere"
        finally:
            os.unlink(config_file)

    def test_load_yaml_config_file(self):
        """Test loading configuration from YAML file."""
        try:
            import yaml  # type: ignore[import-untyped]
        except ImportError:
            pytest.skip("PyYAML not available")

        config_data = {
            "vector_db": {
                "backend": "pinecone",
                "embedding_model": "sentence-transformers",
                "indexing": {"batch_size": 200},
                "search": {"default_limit": 20},
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            config_file = f.name

        try:
            config = VectorDBConfig(config_file=config_file)
            assert config.get_backend() == "pinecone"
            assert config.get_embedding_model() == "sentence-transformers"
            assert config.get_indexing_batch_size() == 200
            assert config.get_search_default_limit() == 20
        finally:
            os.unlink(config_file)

    def test_config_file_not_found(self):
        """Test handling when config file doesn't exist."""
        config = VectorDBConfig(config_file="/nonexistent/config.json")
        # Should fall back to defaults
        assert config.get_backend() == "chroma"
        assert config.get_config_file_path() is None

    def test_config_file_invalid_json(self):
        """Test handling invalid JSON config file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json {")
            config_file = f.name

        try:
            config = VectorDBConfig(config_file=config_file)
            # Should fall back to defaults
            assert config.get_backend() == "chroma"
        finally:
            os.unlink(config_file)

    def test_find_config_file(self):
        """Test automatic config file discovery."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "vectordb.json"
            config_data = {"backend": "qdrant"}
            with config_path.open("w") as f:
                json.dump(config_data, f)

            with patch("app.core.vectordb.config.Path.cwd", return_value=Path(tmpdir)):
                config = VectorDBConfig()
                assert config.get_backend() == "qdrant"
                assert config.get_config_file_path() == str(config_path)


class TestNestedConfigStructure:
    """Test nested configuration structure handling."""

    def test_nested_embeddings_section(self):
        """Test loading nested embeddings section."""
        config_data = {
            "vector_db": {
                "embeddings": {
                    "model": "openai",
                    "model_name": "text-embedding-3-large",
                    "dimensions": 3072,
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name

        try:
            config = VectorDBConfig(config_file=config_file)
            assert config.get_embedding_model() == "openai"
            assert config.get_embedding_model_name() == "text-embedding-3-large"
            assert config.get_embedding_dimensions() == 3072
        finally:
            os.unlink(config_file)

    def test_nested_indexing_section(self):
        """Test loading nested indexing section."""
        config_data = {
            "vector_db": {
                "indexing": {
                    "batch_size": 500,
                    "auto_index": True,
                    "update_on_change": False,
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name

        try:
            config = VectorDBConfig(config_file=config_file)
            assert config.get_indexing_batch_size() == 500
            assert config.get_indexing_auto_index() is True
            assert config.get_indexing_update_on_change() is False
        finally:
            os.unlink(config_file)

    def test_nested_search_section(self):
        """Test loading nested search section."""
        config_data = {
            "vector_db": {
                "search": {
                    "default_limit": 25,
                    "similarity_threshold": 0.8,
                    "hybrid_search": True,
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name

        try:
            config = VectorDBConfig(config_file=config_file)
            assert config.get_search_default_limit() == 25
            assert config.get_search_similarity_threshold() == 0.8
            assert config.get_search_hybrid_search() is True
        finally:
            os.unlink(config_file)


class TestEnvironmentVariableOverride:
    """Test environment variable override of config files."""

    def test_env_override_config_file(self):
        """Test environment variables override config file values."""
        config_data = {"backend": "qdrant", "embedding_model": "openai"}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name

        try:
            with patch.dict(os.environ, {"HASS_MCP_VECTOR_DB_BACKEND": "chroma"}):
                config = VectorDBConfig(config_file=config_file)
                # Environment variable should override config file
                assert config.get_backend() == "chroma"
                # Other values from config file should remain
                assert config.get_embedding_model() == "openai"
        finally:
            os.unlink(config_file)

    def test_env_override_nested_config(self):
        """Test environment variables override nested config values."""
        config_data = {
            "vector_db": {
                "indexing": {"batch_size": 500},
                "search": {"default_limit": 25},
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_file = f.name

        try:
            with patch.dict(os.environ, {"HASS_MCP_INDEXING_BATCH_SIZE": "100"}):
                config = VectorDBConfig(config_file=config_file)
                # Environment variable should override config file
                assert config.get_indexing_batch_size() == 100
                # Other values from config file should remain
                assert config.get_search_default_limit() == 25
        finally:
            os.unlink(config_file)


class TestNewConfigurationOptions:
    """Test new configuration options."""

    def test_embedding_device(self):
        """Test embedding device configuration."""
        with patch.dict(os.environ, {"HASS_MCP_EMBEDDING_DEVICE": "gpu"}):
            config = VectorDBConfig()
            assert config.get_embedding_device() == "gpu"

    def test_collection_name(self):
        """Test collection name configuration."""
        with patch.dict(os.environ, {"HASS_MCP_VECTOR_DB_COLLECTION": "custom_entities"}):
            config = VectorDBConfig()
            assert config.get_collection_name() == "custom_entities"

    def test_pinecone_index_name(self):
        """Test Pinecone index name configuration."""
        with patch.dict(os.environ, {"HASS_MCP_PINECONE_INDEX_NAME": "my_index"}):
            config = VectorDBConfig()
            assert config.get_pinecone_index_name() == "my_index"

    def test_openai_model(self):
        """Test OpenAI model configuration."""
        with patch.dict(os.environ, {"HASS_MCP_OPENAI_MODEL": "text-embedding-3-large"}):
            config = VectorDBConfig()
            assert config.get_openai_model() == "text-embedding-3-large"

    def test_cohere_model(self):
        """Test Cohere model configuration."""
        with patch.dict(os.environ, {"HASS_MCP_COHERE_MODEL": "embed-english-v3.0"}):
            config = VectorDBConfig()
            assert config.get_cohere_model() == "embed-english-v3.0"

    def test_indexing_batch_size(self):
        """Test indexing batch size configuration."""
        with patch.dict(os.environ, {"HASS_MCP_INDEXING_BATCH_SIZE": "200"}):
            config = VectorDBConfig()
            assert config.get_indexing_batch_size() == 200

    def test_indexing_auto_index(self):
        """Test indexing auto-index configuration."""
        with patch.dict(os.environ, {"HASS_MCP_INDEXING_AUTO_INDEX": "true"}):
            config = VectorDBConfig()
            assert config.get_indexing_auto_index() is True

    def test_indexing_update_on_change(self):
        """Test indexing update-on-change configuration."""
        with patch.dict(os.environ, {"HASS_MCP_INDEXING_UPDATE_ON_CHANGE": "false"}):
            config = VectorDBConfig()
            assert config.get_indexing_update_on_change() is False

    def test_search_default_limit(self):
        """Test search default limit configuration."""
        with patch.dict(os.environ, {"HASS_MCP_SEARCH_DEFAULT_LIMIT": "20"}):
            config = VectorDBConfig()
            assert config.get_search_default_limit() == 20

    def test_search_similarity_threshold(self):
        """Test search similarity threshold configuration."""
        with patch.dict(os.environ, {"HASS_MCP_SEARCH_SIMILARITY_THRESHOLD": "0.8"}):
            config = VectorDBConfig()
            assert config.get_search_similarity_threshold() == 0.8

    def test_search_hybrid_search(self):
        """Test search hybrid search configuration."""
        with patch.dict(os.environ, {"HASS_MCP_SEARCH_HYBRID_SEARCH": "true"}):
            config = VectorDBConfig()
            assert config.get_search_hybrid_search() is True


class TestConfigurationValidation:
    """Test configuration validation."""

    def test_validate_valid_config(self):
        """Test validation of valid configuration."""
        config = VectorDBConfig()
        is_valid, errors = config.validate()
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_invalid_backend(self):
        """Test validation with invalid backend."""
        with patch.dict(os.environ, {"HASS_MCP_VECTOR_DB_BACKEND": "invalid"}):
            config = VectorDBConfig()
            is_valid, errors = config.validate()
            assert is_valid is False
            assert any("Invalid backend" in error for error in errors)

    def test_validate_invalid_embedding_model(self):
        """Test validation with invalid embedding model."""
        with patch.dict(os.environ, {"HASS_MCP_EMBEDDING_MODEL": "invalid"}):
            config = VectorDBConfig()
            is_valid, errors = config.validate()
            assert is_valid is False
            assert any("Invalid embedding model" in error for error in errors)

    def test_validate_pinecone_missing_api_key(self):
        """Test validation with Pinecone backend missing API key."""
        with patch.dict(os.environ, {"HASS_MCP_VECTOR_DB_BACKEND": "pinecone"}):
            config = VectorDBConfig()
            is_valid, errors = config.validate()
            assert is_valid is False
            assert any("Pinecone API key" in error for error in errors)

    def test_validate_pinecone_missing_environment(self):
        """Test validation with Pinecone backend missing environment."""
        with patch.dict(
            os.environ,
            {
                "HASS_MCP_VECTOR_DB_BACKEND": "pinecone",
                "HASS_MCP_PINECONE_API_KEY": "test_key",
            },
        ):
            config = VectorDBConfig()
            is_valid, errors = config.validate()
            assert is_valid is False
            assert any("Pinecone environment" in error for error in errors)

    def test_validate_openai_missing_api_key(self):
        """Test validation with OpenAI embeddings missing API key."""
        with patch.dict(os.environ, {"HASS_MCP_EMBEDDING_MODEL": "openai"}):
            config = VectorDBConfig()
            is_valid, errors = config.validate()
            assert is_valid is False
            assert any("OpenAI API key" in error for error in errors)

    def test_validate_cohere_missing_api_key(self):
        """Test validation with Cohere embeddings missing API key."""
        with patch.dict(os.environ, {"HASS_MCP_EMBEDDING_MODEL": "cohere"}):
            config = VectorDBConfig()
            is_valid, errors = config.validate()
            assert is_valid is False
            assert any("Cohere API key" in error for error in errors)

    def test_validate_invalid_batch_size(self):
        """Test validation with invalid batch size."""
        with patch.dict(os.environ, {"HASS_MCP_INDEXING_BATCH_SIZE": "0"}):
            config = VectorDBConfig()
            is_valid, errors = config.validate()
            assert is_valid is False
            assert any("batch size" in error.lower() for error in errors)

    def test_validate_invalid_search_limit(self):
        """Test validation with invalid search limit."""
        with patch.dict(os.environ, {"HASS_MCP_SEARCH_DEFAULT_LIMIT": "0"}):
            config = VectorDBConfig()
            is_valid, errors = config.validate()
            assert is_valid is False
            assert any("default limit" in error.lower() for error in errors)

    def test_validate_invalid_similarity_threshold(self):
        """Test validation with invalid similarity threshold."""
        with patch.dict(os.environ, {"HASS_MCP_SEARCH_SIMILARITY_THRESHOLD": "1.5"}):
            config = VectorDBConfig()
            is_valid, errors = config.validate()
            assert is_valid is False
            assert any("similarity threshold" in error.lower() for error in errors)

    def test_validate_invalid_embedding_dimensions(self):
        """Test validation with invalid embedding dimensions."""
        with patch.dict(os.environ, {"HASS_MCP_EMBEDDING_DIMENSIONS": "0"}):
            config = VectorDBConfig()
            is_valid, errors = config.validate()
            assert is_valid is False
            assert any("dimensions" in error.lower() for error in errors)

    def test_validate_invalid_device(self):
        """Test validation with invalid device."""
        with patch.dict(os.environ, {"HASS_MCP_EMBEDDING_DEVICE": "invalid"}):
            config = VectorDBConfig()
            is_valid, errors = config.validate()
            assert is_valid is False
            assert any("device" in error.lower() for error in errors)

    def test_validate_multiple_errors(self):
        """Test validation with multiple errors."""
        with patch.dict(
            os.environ,
            {
                "HASS_MCP_VECTOR_DB_BACKEND": "invalid",
                "HASS_MCP_EMBEDDING_MODEL": "invalid",
                "HASS_MCP_INDEXING_BATCH_SIZE": "0",
            },
        ):
            config = VectorDBConfig()
            is_valid, errors = config.validate()
            assert is_valid is False
            assert len(errors) >= 3


class TestDefaultValues:
    """Test default configuration values."""

    def test_default_backend(self):
        """Test default backend."""
        config = VectorDBConfig()
        assert config.get_backend() == "chroma"

    def test_default_embedding_model(self):
        """Test default embedding model."""
        config = VectorDBConfig()
        assert config.get_embedding_model() == "sentence-transformers"

    def test_default_embedding_model_name(self):
        """Test default embedding model name."""
        config = VectorDBConfig()
        assert config.get_embedding_model_name() == "all-MiniLM-L6-v2"

    def test_default_embedding_dimensions(self):
        """Test default embedding dimensions."""
        config = VectorDBConfig()
        assert config.get_embedding_dimensions() == 384

    def test_default_embedding_device(self):
        """Test default embedding device."""
        config = VectorDBConfig()
        assert config.get_embedding_device() == "cpu"

    def test_default_collection_name(self):
        """Test default collection name."""
        config = VectorDBConfig()
        assert config.get_collection_name() == "entities"

    def test_default_indexing_batch_size(self):
        """Test default indexing batch size."""
        config = VectorDBConfig()
        assert config.get_indexing_batch_size() == 100

    def test_default_indexing_auto_index(self):
        """Test default indexing auto-index."""
        config = VectorDBConfig()
        assert config.get_indexing_auto_index() is False

    def test_default_indexing_update_on_change(self):
        """Test default indexing update-on-change."""
        config = VectorDBConfig()
        assert config.get_indexing_update_on_change() is True

    def test_default_search_default_limit(self):
        """Test default search limit."""
        config = VectorDBConfig()
        assert config.get_search_default_limit() == 10

    def test_default_search_similarity_threshold(self):
        """Test default similarity threshold."""
        config = VectorDBConfig()
        assert config.get_search_similarity_threshold() == 0.7

    def test_default_search_hybrid_search(self):
        """Test default hybrid search."""
        config = VectorDBConfig()
        assert config.get_search_hybrid_search() is False
