"""Embedding model wrapper for hass-mcp.

This module provides a unified interface for different embedding models.
"""

import asyncio
import logging
from typing import Any

from app.core.vectordb.config import VectorDBConfig, get_vectordb_config

logger = logging.getLogger(__name__)


class EmbeddingModel:
    """
    Wrapper for embedding models.

    Supports multiple embedding providers:
    - sentence-transformers (local)
    - OpenAI (cloud)
    - Cohere (cloud)
    """

    def __init__(self, config: VectorDBConfig | None = None):
        """
        Initialize the embedding model.

        Args:
            config: Optional VectorDBConfig instance. If None, uses global config.
        """
        self.config = config or get_vectordb_config()
        self.model_type = self.config.get_embedding_model()
        self.model_name = self.config.get_embedding_model_name()
        self._model: Any = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the embedding model."""
        if self._initialized:
            return

        try:
            if self.model_type == "sentence-transformers":
                await self._initialize_sentence_transformers()
            elif self.model_type == "openai":
                await self._initialize_openai()
            elif self.model_type == "cohere":
                await self._initialize_cohere()
            else:
                raise ValueError(
                    f"Unsupported embedding model type: {self.model_type}. "
                    "Supported types: sentence-transformers, openai, cohere"
                )

            self._initialized = True
            logger.info(f"Initialized embedding model: {self.model_type}/{self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {e}")
            raise

    async def _initialize_sentence_transformers(self) -> None:
        """Initialize sentence-transformers model."""
        try:
            import sentence_transformers  # type: ignore[import-untyped]  # noqa: PLC0415

            # Load model (this is synchronous but we wrap it)
            self._model = sentence_transformers.SentenceTransformer(self.model_name)
            logger.info(f"Loaded sentence-transformers model: {self.model_name}")
        except ImportError as e:
            raise ImportError(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            ) from e

    async def _initialize_openai(self) -> None:
        """Initialize OpenAI embedding model."""
        api_key = self.config.get_openai_api_key()
        if not api_key:
            raise ValueError("OpenAI API key not configured. Set HASS_MCP_OPENAI_API_KEY")

        try:
            from openai import OpenAI  # type: ignore[import-untyped]  # noqa: PLC0415

            self._model = OpenAI(api_key=api_key)
            logger.info("Initialized OpenAI embedding client")
        except ImportError as e:
            raise ImportError("openai not installed. Install with: pip install openai") from e

    async def _initialize_cohere(self) -> None:
        """Initialize Cohere embedding model."""
        api_key = self.config.get_cohere_api_key()
        if not api_key:
            raise ValueError("Cohere API key not configured. Set HASS_MCP_COHERE_API_KEY")

        try:
            import cohere  # type: ignore[import-untyped]  # noqa: PLC0415

            self._model = cohere.Client(api_key=api_key)
            logger.info("Initialized Cohere embedding client")
        except ImportError as e:
            raise ImportError("cohere not installed. Install with: pip install cohere") from e

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors (each is a list of floats)
        """
        if not self._initialized:
            await self.initialize()

        if not texts:
            return []

        try:
            if self.model_type == "sentence-transformers":
                return await self._embed_sentence_transformers(texts)
            if self.model_type == "openai":
                return await self._embed_openai(texts)
            if self.model_type == "cohere":
                return await self._embed_cohere(texts)
            raise ValueError(f"Unsupported embedding model type: {self.model_type}")
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise

    async def _embed_sentence_transformers(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using sentence-transformers."""
        # Sentence transformers is synchronous, but we can run it in executor
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(None, self._model.encode, texts)
        # Convert numpy array to list of lists
        return [emb.tolist() for emb in embeddings]

    async def _embed_openai(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using OpenAI."""
        try:
            response = self._model.embeddings.create(
                model="text-embedding-3-small",
                input=texts,
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}")
            raise

    async def _embed_cohere(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using Cohere."""
        try:
            response = self._model.embed(
                texts=texts,
                model="embed-english-v3.0",
                input_type="search_document",
            )
            return response.embeddings
        except Exception as e:
            logger.error(f"Cohere embedding error: {e}")
            raise

    def get_dimensions(self) -> int:
        """
        Get the embedding dimensions for this model.

        Returns:
            Number of dimensions in embeddings
        """
        # Model-specific dimensions
        if self.model_type == "sentence-transformers":
            # all-MiniLM-L6-v2 has 384 dimensions
            if "MiniLM-L6" in self.model_name:
                return 384
            # Default to config value
            return self.config.get_embedding_dimensions()
        if self.model_type == "openai":
            # text-embedding-3-small has 1536 dimensions
            return 1536
        if self.model_type == "cohere":
            # embed-english-v3.0 has 1024 dimensions
            return 1024
        return self.config.get_embedding_dimensions()

    async def close(self) -> None:
        """Close the embedding model and cleanup resources."""
        self._model = None
        self._initialized = False
