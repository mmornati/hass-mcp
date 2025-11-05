"""Vector DB configuration management for hass-mcp.

This module provides configuration management for the vector database system, including
support for environment variables, configuration files (JSON/YAML), and multiple backend configurations.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Try to import yaml, but make it optional
try:
    import yaml  # type: ignore[import-untyped]

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


class VectorDBConfig:
    """
    Vector DB configuration manager.

    This class manages vector DB configuration from:
    - Configuration files (JSON/YAML)
    - Environment variables (override config files)
    - Default values
    """

    def __init__(self, config_file: str | None = None):
        """
        Initialize vector DB configuration.

        Args:
            config_file: Optional path to configuration file. If None, will search for
                        config files in common locations.
        """
        self._config_data: dict[str, Any] = {}
        self._config_file_path: str | None = None
        self._load_configuration(config_file)

    def _find_config_file(self) -> str | None:
        """
        Find configuration file in common locations.

        Returns:
            Path to configuration file if found, None otherwise
        """
        # Possible config file names
        config_names = [
            "vectordb.json",
            "vectordb.yaml",
            "vectordb.yml",
            ".vectordb.json",
            ".vectordb.yaml",
        ]

        # Possible locations
        locations = [
            Path.cwd(),
            Path.home(),
            Path(os.environ.get("HASS_MCP_CONFIG_DIR", "")),
            Path("/etc/hass-mcp"),
        ]

        for location in locations:
            if not location.exists():
                continue
            for name in config_names:
                config_path = location / name
                if config_path.exists():
                    return str(config_path)

        return None

    def _load_config_file(self, config_file: str | None) -> dict[str, Any]:
        """
        Load configuration from file.

        Args:
            config_file: Path to configuration file

        Returns:
            Configuration dictionary from file
        """
        if config_file is None:
            config_file = self._find_config_file()

        if config_file is None:
            return {}

        config_path = Path(config_file)
        if not config_path.exists():
            logger.warning(f"Configuration file not found: {config_file}")
            return {}

        self._config_file_path = str(config_path)

        try:
            with config_path.open() as f:
                if config_path.suffix in (".yaml", ".yml"):
                    if not YAML_AVAILABLE:
                        logger.warning(
                            "YAML support not available. Install pyyaml for YAML config support."
                        )
                        return {}
                    config_data = yaml.safe_load(f) or {}
                else:
                    config_data = json.load(f)

            # Extract vector_db section if present
            if "vector_db" in config_data:
                return config_data.get("vector_db", {})
            return config_data
        except Exception as e:
            logger.error(f"Failed to load configuration file {config_file}: {e}")
            return {}

    def _load_configuration(self, config_file: str | None = None) -> None:
        """
        Load configuration from files and environment variables.

        Environment variables override configuration file values.

        Args:
            config_file: Optional path to configuration file
        """
        # Start with defaults
        defaults = {
            "backend": "chroma",
            "embedding_model": "sentence-transformers",
            "embedding_model_name": "all-MiniLM-L6-v2",
            "embedding_dimensions": 384,
            "embedding_device": "cpu",
            # Chroma configuration
            "chroma_path": ".vectordb",
            "collection_name": "entities",
            # Qdrant configuration
            "qdrant_url": "http://localhost:6333",
            "qdrant_api_key": None,
            # Weaviate configuration
            "weaviate_url": "http://localhost:8080",
            "weaviate_api_key": None,
            # Pinecone configuration
            "pinecone_api_key": None,
            "pinecone_environment": None,
            "pinecone_index_name": "entities",
            # OpenAI configuration
            "openai_api_key": None,
            "openai_model": "text-embedding-3-small",
            # Cohere configuration
            "cohere_api_key": None,
            "cohere_model": "embed-english-v3.0",
            # Performance configuration
            "indexing_batch_size": 100,
            "indexing_auto_index": False,
            "indexing_update_on_change": True,
            "search_default_limit": 10,
            "search_similarity_threshold": 0.7,
            "search_hybrid_search": False,
            # Enable/disable
            "enabled": True,
        }

        # Load from config file
        file_config = self._load_config_file(config_file)

        # Merge defaults, file config, and environment variables
        # Environment variables take precedence
        self._config_data = defaults.copy()

        # Merge file config
        if file_config:
            # Handle nested structure
            if "embeddings" in file_config:
                embeddings = file_config.pop("embeddings")
                # Map common aliases
                if "model" in embeddings:
                    embeddings["embedding_model"] = embeddings.pop("model")
                if "model_name" in embeddings:
                    embeddings["embedding_model_name"] = embeddings.pop("model_name")
                if "dimensions" in embeddings:
                    embeddings["embedding_dimensions"] = embeddings.pop("dimensions")
                if "device" in embeddings:
                    embeddings["embedding_device"] = embeddings.pop("device")
                self._config_data.update(embeddings)
            if "indexing" in file_config:
                indexing = file_config.pop("indexing")
                for key, value in indexing.items():
                    self._config_data[f"indexing_{key}"] = value
            if "search" in file_config:
                search = file_config.pop("search")
                for key, value in search.items():
                    self._config_data[f"search_{key}"] = value
            self._config_data.update(file_config)

        # Override with environment variables
        env_mappings = {
            "HASS_MCP_VECTOR_DB_BACKEND": "backend",
            "HASS_MCP_EMBEDDING_MODEL": "embedding_model",
            "HASS_MCP_EMBEDDING_MODEL_NAME": "embedding_model_name",
            "HASS_MCP_EMBEDDING_DIMENSIONS": "embedding_dimensions",
            "HASS_MCP_EMBEDDING_DEVICE": "embedding_device",
            "HASS_MCP_VECTOR_DB_PATH": "chroma_path",
            "HASS_MCP_VECTOR_DB_COLLECTION": "collection_name",
            "HASS_MCP_QDRANT_URL": "qdrant_url",
            "HASS_MCP_QDRANT_API_KEY": "qdrant_api_key",
            "HASS_MCP_WEAVIATE_URL": "weaviate_url",
            "HASS_MCP_WEAVIATE_API_KEY": "weaviate_api_key",
            "HASS_MCP_PINECONE_API_KEY": "pinecone_api_key",
            "HASS_MCP_PINECONE_ENVIRONMENT": "pinecone_environment",
            "HASS_MCP_PINECONE_INDEX_NAME": "pinecone_index_name",
            "HASS_MCP_OPENAI_API_KEY": "openai_api_key",
            "HASS_MCP_OPENAI_MODEL": "openai_model",
            "HASS_MCP_COHERE_API_KEY": "cohere_api_key",
            "HASS_MCP_COHERE_MODEL": "cohere_model",
            "HASS_MCP_INDEXING_BATCH_SIZE": "indexing_batch_size",
            "HASS_MCP_INDEXING_AUTO_INDEX": "indexing_auto_index",
            "HASS_MCP_INDEXING_UPDATE_ON_CHANGE": "indexing_update_on_change",
            "HASS_MCP_SEARCH_DEFAULT_LIMIT": "search_default_limit",
            "HASS_MCP_SEARCH_SIMILARITY_THRESHOLD": "search_similarity_threshold",
            "HASS_MCP_SEARCH_HYBRID_SEARCH": "search_hybrid_search",
            "HASS_MCP_VECTOR_DB_ENABLED": "enabled",
        }

        for env_var, config_key in env_mappings.items():
            value = os.environ.get(env_var)
            if value is not None:
                # Convert to appropriate type
                if config_key in (
                    "embedding_dimensions",
                    "indexing_batch_size",
                    "search_default_limit",
                ):
                    self._config_data[config_key] = int(value)
                elif config_key in ("search_similarity_threshold",):
                    self._config_data[config_key] = float(value)
                elif config_key in (
                    "enabled",
                    "indexing_auto_index",
                    "indexing_update_on_change",
                    "search_hybrid_search",
                ):
                    self._config_data[config_key] = value.lower() in ("true", "1", "yes")
                elif config_key == "backend" or config_key == "embedding_model":
                    self._config_data[config_key] = value.lower()
                else:
                    self._config_data[config_key] = value

    def get_backend(self) -> str:
        """Get the configured vector DB backend."""
        return str(self._config_data.get("backend", "chroma"))

    def get_embedding_model(self) -> str:
        """Get the configured embedding model type."""
        return str(self._config_data.get("embedding_model", "sentence-transformers"))

    def get_embedding_model_name(self) -> str:
        """Get the embedding model name."""
        return str(self._config_data.get("embedding_model_name", "all-MiniLM-L6-v2"))

    def get_embedding_dimensions(self) -> int:
        """Get the embedding dimensions."""
        return int(self._config_data.get("embedding_dimensions", 384))

    def get_chroma_path(self) -> str:
        """Get the Chroma database path."""
        return str(self._config_data.get("chroma_path", ".vectordb"))

    def get_qdrant_url(self) -> str:
        """Get the Qdrant URL."""
        return str(self._config_data.get("qdrant_url", "http://localhost:6333"))

    def get_qdrant_api_key(self) -> str | None:
        """Get the Qdrant API key."""
        return self._config_data.get("qdrant_api_key")

    def get_weaviate_url(self) -> str:
        """Get the Weaviate URL."""
        return str(self._config_data.get("weaviate_url", "http://localhost:8080"))

    def get_weaviate_api_key(self) -> str | None:
        """Get the Weaviate API key."""
        return self._config_data.get("weaviate_api_key")

    def get_pinecone_api_key(self) -> str | None:
        """Get the Pinecone API key."""
        return self._config_data.get("pinecone_api_key")

    def get_pinecone_environment(self) -> str | None:
        """Get the Pinecone environment."""
        return self._config_data.get("pinecone_environment")

    def get_openai_api_key(self) -> str | None:
        """Get the OpenAI API key."""
        return self._config_data.get("openai_api_key")

    def get_cohere_api_key(self) -> str | None:
        """Get the Cohere API key."""
        return self._config_data.get("cohere_api_key")

    def is_enabled(self) -> bool:
        """Check if vector DB is enabled."""
        return bool(self._config_data.get("enabled", True))

    def get_all_config(self) -> dict[str, Any]:
        """Get the complete configuration dictionary."""
        return self._config_data.copy()

    def get_config_file_path(self) -> str | None:
        """Get the path to the loaded configuration file."""
        return self._config_file_path

    def get_embedding_device(self) -> str:
        """Get the embedding device (cpu/gpu)."""
        return str(self._config_data.get("embedding_device", "cpu"))

    def get_collection_name(self) -> str:
        """Get the default collection name."""
        return str(self._config_data.get("collection_name", "entities"))

    def get_pinecone_index_name(self) -> str:
        """Get the Pinecone index name."""
        return str(self._config_data.get("pinecone_index_name", "entities"))

    def get_openai_model(self) -> str:
        """Get the OpenAI model name."""
        return str(self._config_data.get("openai_model", "text-embedding-3-small"))

    def get_cohere_model(self) -> str:
        """Get the Cohere model name."""
        return str(self._config_data.get("cohere_model", "embed-english-v3.0"))

    def get_indexing_batch_size(self) -> int:
        """Get the batch size for indexing."""
        return int(self._config_data.get("indexing_batch_size", 100))

    def get_indexing_auto_index(self) -> bool:
        """Get whether to auto-index on startup."""
        return bool(self._config_data.get("indexing_auto_index", False))

    def get_indexing_update_on_change(self) -> bool:
        """Get whether to update index on entity changes."""
        return bool(self._config_data.get("indexing_update_on_change", True))

    def get_search_default_limit(self) -> int:
        """Get the default search result limit."""
        return int(self._config_data.get("search_default_limit", 10))

    def get_search_similarity_threshold(self) -> float:
        """Get the similarity threshold for search."""
        return float(self._config_data.get("search_similarity_threshold", 0.7))

    def get_search_hybrid_search(self) -> bool:
        """Get whether to use hybrid search."""
        return bool(self._config_data.get("search_hybrid_search", False))

    def validate(self) -> tuple[bool, list[str]]:
        """
        Validate the configuration.

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors: list[str] = []

        # Validate backend
        backend = self.get_backend()
        valid_backends = ["chroma", "qdrant", "weaviate", "pinecone"]
        if backend not in valid_backends:
            errors.append(f"Invalid backend: {backend}. Must be one of {valid_backends}")

        # Validate embedding model
        embedding_model = self.get_embedding_model()
        valid_models = ["sentence-transformers", "openai", "cohere"]
        if embedding_model not in valid_models:
            errors.append(
                f"Invalid embedding model: {embedding_model}. Must be one of {valid_models}"
            )

        # Validate backend-specific requirements
        if backend == "qdrant":
            if not self.get_qdrant_url():
                errors.append("Qdrant URL is required when using Qdrant backend")

        if backend == "weaviate":
            if not self.get_weaviate_url():
                errors.append("Weaviate URL is required when using Weaviate backend")

        if backend == "pinecone":
            if not self.get_pinecone_api_key():
                errors.append("Pinecone API key is required when using Pinecone backend")
            if not self.get_pinecone_environment():
                errors.append("Pinecone environment is required when using Pinecone backend")

        # Validate embedding model-specific requirements
        if embedding_model == "openai":
            if not self.get_openai_api_key():
                errors.append("OpenAI API key is required when using OpenAI embeddings")

        if embedding_model == "cohere":
            if not self.get_cohere_api_key():
                errors.append("Cohere API key is required when using Cohere embeddings")

        # Validate performance settings
        if self.get_indexing_batch_size() < 1:
            errors.append("Indexing batch size must be at least 1")

        if self.get_search_default_limit() < 1:
            errors.append("Search default limit must be at least 1")

        threshold = self.get_search_similarity_threshold()
        if threshold < 0.0 or threshold > 1.0:
            errors.append("Search similarity threshold must be between 0.0 and 1.0")

        # Validate embedding dimensions
        dimensions = self.get_embedding_dimensions()
        if dimensions < 1:
            errors.append("Embedding dimensions must be at least 1")

        # Validate device
        device = self.get_embedding_device()
        if device not in ("cpu", "gpu", "cuda"):
            errors.append(f"Invalid embedding device: {device}. Must be one of: cpu, gpu, cuda")

        is_valid = len(errors) == 0
        return (is_valid, errors)


# Global vector DB config instance
_vectordb_config: VectorDBConfig | None = None


def get_vectordb_config() -> VectorDBConfig:
    """
    Get the global vector DB configuration instance (singleton pattern).

    Returns:
        The VectorDBConfig instance
    """
    global _vectordb_config
    if _vectordb_config is None:
        _vectordb_config = VectorDBConfig()
        logger.info("Vector DB configuration loaded")
    return _vectordb_config
