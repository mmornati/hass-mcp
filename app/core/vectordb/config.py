"""Vector DB configuration management for hass-mcp.

This module provides configuration management for the vector database system, including
support for environment variables and multiple backend configurations.
"""

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


class VectorDBConfig:
    """
    Vector DB configuration manager.

    This class manages vector DB configuration from environment variables.
    """

    def __init__(self):
        """Initialize vector DB configuration."""
        self._config_data: dict[str, Any] = {}
        self._load_configuration()

    def _load_configuration(self) -> None:
        """Load configuration from environment variables."""
        # Default values
        self._config_data = {
            "backend": os.environ.get("HASS_MCP_VECTOR_DB_BACKEND", "chroma").lower(),
            "embedding_model": os.environ.get(
                "HASS_MCP_EMBEDDING_MODEL", "sentence-transformers"
            ).lower(),
            "embedding_model_name": os.environ.get(
                "HASS_MCP_EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2"
            ),
            "embedding_dimensions": int(os.environ.get("HASS_MCP_EMBEDDING_DIMENSIONS", "384")),
            # Chroma configuration
            "chroma_path": os.environ.get("HASS_MCP_VECTOR_DB_PATH", ".vectordb"),
            # Qdrant configuration
            "qdrant_url": os.environ.get("HASS_MCP_QDRANT_URL", "http://localhost:6333"),
            "qdrant_api_key": os.environ.get("HASS_MCP_QDRANT_API_KEY"),
            # Weaviate configuration
            "weaviate_url": os.environ.get("HASS_MCP_WEAVIATE_URL", "http://localhost:8080"),
            "weaviate_api_key": os.environ.get("HASS_MCP_WEAVIATE_API_KEY"),
            # Pinecone configuration
            "pinecone_api_key": os.environ.get("HASS_MCP_PINECONE_API_KEY"),
            "pinecone_environment": os.environ.get("HASS_MCP_PINECONE_ENVIRONMENT"),
            # OpenAI configuration
            "openai_api_key": os.environ.get("HASS_MCP_OPENAI_API_KEY"),
            # Cohere configuration
            "cohere_api_key": os.environ.get("HASS_MCP_COHERE_API_KEY"),
            # Enable/disable
            "enabled": os.environ.get("HASS_MCP_VECTOR_DB_ENABLED", "true").lower()
            in ("true", "1", "yes"),
        }

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
