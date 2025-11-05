"""Vector DB manager for hass-mcp.

This module provides the main VectorDBManager singleton that coordinates
vector database operations and embedding generation.
"""

import logging
from typing import Any

from app.core.vectordb.backend import VectorDBBackend
from app.core.vectordb.chroma_backend import ChromaBackend
from app.core.vectordb.config import VectorDBConfig, get_vectordb_config
from app.core.vectordb.embeddings import EmbeddingModel

logger = logging.getLogger(__name__)


class VectorDBManager:
    """
    Vector DB manager singleton.

    This class manages vector database operations, embedding generation,
    and provides a unified interface for semantic search.
    """

    def __init__(self, config: VectorDBConfig | None = None):
        """
        Initialize Vector DB manager.

        Args:
            config: Optional VectorDBConfig instance. If None, uses global config.
        """
        self.config = config or get_vectordb_config()
        self.backend: VectorDBBackend | None = None
        self.embedding_model: EmbeddingModel | None = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the vector DB manager."""
        if self._initialized:
            return

        if not self.config.is_enabled():
            logger.info("Vector DB is disabled, skipping initialization")
            return

        try:
            # Initialize embedding model
            self.embedding_model = EmbeddingModel(self.config)
            await self.embedding_model.initialize()

            # Initialize backend
            backend_type = self.config.get_backend()
            if backend_type == "chroma":
                self.backend = ChromaBackend(self.config)
            elif backend_type == "qdrant":
                # Qdrant backend will be implemented in future
                raise NotImplementedError(
                    "Qdrant backend not yet implemented. Use 'chroma' backend for now."
                )
            elif backend_type == "weaviate":
                # Weaviate backend will be implemented in future
                raise NotImplementedError(
                    "Weaviate backend not yet implemented. Use 'chroma' backend for now."
                )
            elif backend_type == "pinecone":
                # Pinecone backend will be implemented in future
                raise NotImplementedError(
                    "Pinecone backend not yet implemented. Use 'chroma' backend for now."
                )
            else:
                raise ValueError(
                    f"Unsupported vector DB backend: {backend_type}. "
                    "Supported backends: chroma, qdrant, weaviate, pinecone"
                )

            await self.backend.initialize()

            # Health check
            if not await self.backend.health_check():
                logger.warning("Vector DB backend health check failed")
                raise RuntimeError("Vector DB backend health check failed")

            self._initialized = True
            logger.info(
                f"Initialized Vector DB manager with backend: {backend_type}, "
                f"embedding model: {self.config.get_embedding_model()}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Vector DB manager: {e}")
            raise

    async def health_check(self) -> bool:
        """
        Check if the vector DB manager is healthy.

        Returns:
            True if healthy, False otherwise
        """
        if not self.config.is_enabled():
            return False

        if not self._initialized:
            try:
                await self.initialize()
            except Exception:
                return False

        if not self.backend:
            return False

        return await self.backend.health_check()

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors
        """
        if not self._initialized:
            await self.initialize()

        if not self.embedding_model:
            raise RuntimeError("Embedding model not initialized")

        return await self.embedding_model.embed(texts)

    async def add_vectors(
        self,
        collection_name: str,
        texts: list[str],
        ids: list[str],
        metadata: list[dict[str, Any]] | None = None,
    ) -> None:
        """
        Add vectors to a collection.

        Args:
            collection_name: Name of the collection
            texts: List of text strings to embed and add
            ids: List of unique IDs for each vector
            metadata: Optional list of metadata dictionaries
        """
        if not self._initialized:
            await self.initialize()

        if not self.backend:
            raise RuntimeError("Vector DB backend not initialized")

        # Generate embeddings
        vectors = await self.embed_texts(texts)

        # Ensure collection exists
        if not await self.backend.collection_exists(collection_name):
            await self.backend.create_collection(collection_name)

        # Add vectors
        await self.backend.add_vectors(collection_name, vectors, ids, metadata)

    async def search_vectors(
        self,
        collection_name: str,
        query_text: str,
        limit: int = 10,
        filter_metadata: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search for similar vectors in a collection.

        Args:
            collection_name: Name of the collection to search
            query_text: Query text to search for
            limit: Maximum number of results to return
            filter_metadata: Optional metadata filters to apply

        Returns:
            List of search results with metadata
        """
        if not self._initialized:
            await self.initialize()

        if not self.backend:
            raise RuntimeError("Vector DB backend not initialized")

        if not self.embedding_model:
            raise RuntimeError("Embedding model not initialized")

        # Generate query embedding
        query_embeddings = await self.embed_texts([query_text])
        query_vector = query_embeddings[0]

        # Search
        results = await self.backend.search_vectors(
            collection_name, query_vector, limit, filter_metadata
        )

        return results

    async def update_vectors(
        self,
        collection_name: str,
        texts: list[str],
        ids: list[str],
        metadata: list[dict[str, Any]] | None = None,
    ) -> None:
        """
        Update existing vectors in a collection.

        Args:
            collection_name: Name of the collection
            texts: List of text strings to embed and update
            ids: List of IDs of vectors to update
            metadata: Optional list of metadata dictionaries to update
        """
        if not self._initialized:
            await self.initialize()

        if not self.backend:
            raise RuntimeError("Vector DB backend not initialized")

        # Generate embeddings
        vectors = await self.embed_texts(texts)

        # Update vectors
        await self.backend.update_vectors(collection_name, vectors, ids, metadata)

    async def delete_vectors(self, collection_name: str, ids: list[str]) -> None:
        """
        Delete vectors from a collection.

        Args:
            collection_name: Name of the collection
            ids: List of IDs of vectors to delete
        """
        if not self._initialized:
            await self.initialize()

        if not self.backend:
            raise RuntimeError("Vector DB backend not initialized")

        await self.backend.delete_vectors(collection_name, ids)

    async def create_collection(
        self, collection_name: str, metadata: dict[str, Any] | None = None
    ) -> None:
        """
        Create a new collection.

        Args:
            collection_name: Name of the collection to create
            metadata: Optional metadata for the collection
        """
        if not self._initialized:
            await self.initialize()

        if not self.backend:
            raise RuntimeError("Vector DB backend not initialized")

        await self.backend.create_collection(collection_name, metadata)

    async def delete_collection(self, collection_name: str) -> None:
        """
        Delete a collection.

        Args:
            collection_name: Name of the collection to delete
        """
        if not self._initialized:
            await self.initialize()

        if not self.backend:
            raise RuntimeError("Vector DB backend not initialized")

        await self.backend.delete_collection(collection_name)

    async def collection_exists(self, collection_name: str) -> bool:
        """
        Check if a collection exists.

        Args:
            collection_name: Name of the collection to check

        Returns:
            True if the collection exists, False otherwise
        """
        if not self._initialized:
            await self.initialize()

        if not self.backend:
            return False

        return await self.backend.collection_exists(collection_name)

    async def get_collection_stats(self, collection_name: str) -> dict[str, Any]:
        """
        Get statistics about a collection.

        Args:
            collection_name: Name of the collection

        Returns:
            Dictionary containing collection statistics
        """
        if not self._initialized:
            await self.initialize()

        if not self.backend:
            raise RuntimeError("Vector DB backend not initialized")

        return await self.backend.get_collection_stats(collection_name)

    async def close(self) -> None:
        """Close connections and cleanup resources."""
        if self.backend:
            await self.backend.close()
        if self.embedding_model:
            await self.embedding_model.close()
        self._initialized = False
        logger.info("Closed Vector DB manager")


# Global vector DB manager instance
_vectordb_manager: VectorDBManager | None = None


def get_vectordb_manager() -> VectorDBManager:
    """
    Get the global vector DB manager instance (singleton pattern).

    Returns:
        The VectorDBManager instance
    """
    global _vectordb_manager
    if _vectordb_manager is None:
        _vectordb_manager = VectorDBManager()
        logger.info("Vector DB manager instance created")
    return _vectordb_manager
