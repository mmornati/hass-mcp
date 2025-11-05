"""Abstract vector DB backend interface for hass-mcp.

This module defines the abstract interface that all vector DB backends must implement.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class VectorDBBackend(ABC):
    """
    Abstract base class for vector DB backends.

    All vector DB backends must implement this interface to ensure consistent
    behavior across different vector databases (Chroma, Qdrant, Weaviate, Pinecone).
    """

    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the vector DB backend.

        This method should set up connections, create collections if needed,
        and perform any necessary initialization.
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the vector DB backend is healthy and available.

        Returns:
            True if the backend is healthy, False otherwise
        """
        pass

    @abstractmethod
    async def create_collection(
        self, collection_name: str, metadata: dict[str, Any] | None = None
    ) -> None:
        """
        Create a new collection in the vector DB.

        Args:
            collection_name: Name of the collection to create
            metadata: Optional metadata for the collection
        """
        pass

    @abstractmethod
    async def delete_collection(self, collection_name: str) -> None:
        """
        Delete a collection from the vector DB.

        Args:
            collection_name: Name of the collection to delete
        """
        pass

    @abstractmethod
    async def collection_exists(self, collection_name: str) -> bool:
        """
        Check if a collection exists.

        Args:
            collection_name: Name of the collection to check

        Returns:
            True if the collection exists, False otherwise
        """
        pass

    @abstractmethod
    async def add_vectors(
        self,
        collection_name: str,
        vectors: list[list[float]],
        ids: list[str],
        metadata: list[dict[str, Any]] | None = None,
    ) -> None:
        """
        Add vectors to a collection.

        Args:
            collection_name: Name of the collection
            vectors: List of vector embeddings
            ids: List of unique IDs for each vector
            metadata: Optional list of metadata dictionaries for each vector
        """
        pass

    @abstractmethod
    async def search_vectors(
        self,
        collection_name: str,
        query_vector: list[float],
        limit: int = 10,
        filter_metadata: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search for similar vectors in a collection.

        Args:
            collection_name: Name of the collection to search
            query_vector: Query vector to search for
            limit: Maximum number of results to return
            filter_metadata: Optional metadata filters to apply

        Returns:
            List of search results, each containing:
            - id: Vector ID
            - distance: Similarity distance
            - metadata: Associated metadata
        """
        pass

    @abstractmethod
    async def update_vectors(
        self,
        collection_name: str,
        vectors: list[list[float]],
        ids: list[str],
        metadata: list[dict[str, Any]] | None = None,
    ) -> None:
        """
        Update existing vectors in a collection.

        Args:
            collection_name: Name of the collection
            vectors: List of vector embeddings to update
            ids: List of IDs of vectors to update
            metadata: Optional list of metadata dictionaries to update
        """
        pass

    @abstractmethod
    async def delete_vectors(self, collection_name: str, ids: list[str]) -> None:
        """
        Delete vectors from a collection.

        Args:
            collection_name: Name of the collection
            ids: List of IDs of vectors to delete
        """
        pass

    @abstractmethod
    async def batch_operations(
        self, collection_name: str, operations: list[dict[str, Any]]
    ) -> None:
        """
        Perform batch operations on vectors.

        Args:
            collection_name: Name of the collection
            operations: List of operation dictionaries, each containing:
                - operation: 'add', 'update', or 'delete'
                - vectors: List of vectors (for add/update)
                - ids: List of IDs
                - metadata: Optional metadata (for add/update)
        """
        pass

    @abstractmethod
    async def get_collection_stats(self, collection_name: str) -> dict[str, Any]:
        """
        Get statistics about a collection.

        Args:
            collection_name: Name of the collection

        Returns:
            Dictionary containing collection statistics:
            - count: Number of vectors
            - dimensions: Vector dimensions
            - metadata: Collection metadata
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close connections and cleanup resources."""
        pass
