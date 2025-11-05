"""Chroma vector DB backend for hass-mcp.

This module provides Chroma implementation of the vector DB backend interface.
"""

import logging
from typing import Any

from app.core.vectordb.backend import VectorDBBackend
from app.core.vectordb.config import VectorDBConfig, get_vectordb_config

logger = logging.getLogger(__name__)


class ChromaBackend(VectorDBBackend):
    """
    Chroma vector DB backend implementation.

    Chroma is a local, embedded vector database that requires no external setup.
    """

    def __init__(self, config: VectorDBConfig | None = None):
        """
        Initialize Chroma backend.

        Args:
            config: Optional VectorDBConfig instance. If None, uses global config.
        """
        self.config = config or get_vectordb_config()
        self.client: Any = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the Chroma backend."""
        if self._initialized:
            return

        try:
            import chromadb  # type: ignore[import-untyped]  # noqa: PLC0415

            # Create persistent client
            persist_directory = self.config.get_chroma_path()
            self.client = chromadb.PersistentClient(path=persist_directory)
            self._initialized = True
            logger.info(f"Initialized Chroma backend at {persist_directory}")
        except ImportError as e:
            raise ImportError("chromadb not installed. Install with: pip install chromadb") from e
        except Exception as e:
            logger.error(f"Failed to initialize Chroma backend: {e}")
            raise

    async def health_check(self) -> bool:
        """Check if Chroma backend is healthy."""
        try:
            if not self._initialized:
                await self.initialize()
            # Try to list collections as a health check
            self.client.list_collections()
            return True
        except Exception as e:
            logger.error(f"Chroma health check failed: {e}")
            return False

    async def create_collection(
        self, collection_name: str, metadata: dict[str, Any] | None = None
    ) -> None:
        """Create a new collection in Chroma."""
        if not self._initialized:
            await self.initialize()

        try:
            # Check if collection already exists
            if await self.collection_exists(collection_name):
                logger.warning(f"Collection {collection_name} already exists")
                return

            # Create collection with metadata
            collection_metadata = metadata or {}
            self.client.create_collection(
                name=collection_name,
                metadata=collection_metadata,
            )
            logger.info(f"Created Chroma collection: {collection_name}")
        except Exception as e:
            logger.error(f"Failed to create Chroma collection: {e}")
            raise

    async def delete_collection(self, collection_name: str) -> None:
        """Delete a collection from Chroma."""
        if not self._initialized:
            await self.initialize()

        try:
            self.client.delete_collection(name=collection_name)
            logger.info(f"Deleted Chroma collection: {collection_name}")
        except Exception as e:
            logger.error(f"Failed to delete Chroma collection: {e}")
            raise

    async def collection_exists(self, collection_name: str) -> bool:
        """Check if a collection exists in Chroma."""
        if not self._initialized:
            await self.initialize()

        try:
            collections = self.client.list_collections()
            return any(col.name == collection_name for col in collections)
        except Exception as e:
            logger.error(f"Failed to check collection existence: {e}")
            return False

    async def add_vectors(
        self,
        collection_name: str,
        vectors: list[list[float]],
        ids: list[str],
        metadata: list[dict[str, Any]] | None = None,
    ) -> None:
        """Add vectors to a Chroma collection."""
        if not self._initialized:
            await self.initialize()

        try:
            collection = self.client.get_collection(name=collection_name)

            # Convert metadata format
            metadatas = metadata or [{}] * len(vectors)
            if len(metadatas) != len(vectors):
                metadatas = [{}] * len(vectors)

            # Add vectors
            collection.add(
                embeddings=vectors,
                ids=ids,
                metadatas=metadatas,
            )
            logger.debug(f"Added {len(vectors)} vectors to collection {collection_name}")
        except Exception as e:
            logger.error(f"Failed to add vectors to Chroma: {e}")
            raise

    async def search_vectors(
        self,
        collection_name: str,
        query_vector: list[float],
        limit: int = 10,
        filter_metadata: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Search for similar vectors in a Chroma collection."""
        if not self._initialized:
            await self.initialize()

        try:
            collection = self.client.get_collection(name=collection_name)

            # Build where clause from filter_metadata
            where = filter_metadata or {}

            # Search
            results = collection.query(
                query_embeddings=[query_vector],
                n_results=limit,
                where=where if where else None,
            )

            # Format results
            formatted_results = []
            if results["ids"] and len(results["ids"]) > 0:
                for i in range(len(results["ids"][0])):
                    formatted_results.append(
                        {
                            "id": results["ids"][0][i],
                            "distance": (
                                results["distances"][0][i] if results.get("distances") else 0.0
                            ),
                            "metadata": (
                                results["metadatas"][0][i] if results.get("metadatas") else {}
                            ),
                        }
                    )

            return formatted_results
        except Exception as e:
            logger.error(f"Failed to search vectors in Chroma: {e}")
            raise

    async def update_vectors(
        self,
        collection_name: str,
        vectors: list[list[float]],
        ids: list[str],
        metadata: list[dict[str, Any]] | None = None,
    ) -> None:
        """Update existing vectors in a Chroma collection."""
        if not self._initialized:
            await self.initialize()

        try:
            collection = self.client.get_collection(name=collection_name)

            # Convert metadata format
            metadatas = metadata or [{}] * len(vectors)
            if len(metadatas) != len(vectors):
                metadatas = [{}] * len(vectors)

            # Update vectors (Chroma uses upsert for updates)
            collection.update(
                embeddings=vectors,
                ids=ids,
                metadatas=metadatas,
            )
            logger.debug(f"Updated {len(vectors)} vectors in collection {collection_name}")
        except Exception as e:
            logger.error(f"Failed to update vectors in Chroma: {e}")
            raise

    async def delete_vectors(self, collection_name: str, ids: list[str]) -> None:
        """Delete vectors from a Chroma collection."""
        if not self._initialized:
            await self.initialize()

        try:
            collection = self.client.get_collection(name=collection_name)
            collection.delete(ids=ids)
            logger.debug(f"Deleted {len(ids)} vectors from collection {collection_name}")
        except Exception as e:
            logger.error(f"Failed to delete vectors from Chroma: {e}")
            raise

    async def batch_operations(
        self, collection_name: str, operations: list[dict[str, Any]]
    ) -> None:
        """Perform batch operations on vectors in Chroma."""
        if not self._initialized:
            await self.initialize()

        try:
            collection = self.client.get_collection(name=collection_name)

            for operation in operations:
                op_type = operation.get("operation")
                if op_type == "add":
                    await self.add_vectors(
                        collection_name,
                        operation.get("vectors", []),
                        operation.get("ids", []),
                        operation.get("metadata"),
                    )
                elif op_type == "update":
                    await self.update_vectors(
                        collection_name,
                        operation.get("vectors", []),
                        operation.get("ids", []),
                        operation.get("metadata"),
                    )
                elif op_type == "delete":
                    await self.delete_vectors(collection_name, operation.get("ids", []))
                else:
                    logger.warning(f"Unknown operation type: {op_type}")

            logger.debug(
                f"Completed {len(operations)} batch operations on collection {collection_name}"
            )
        except Exception as e:
            logger.error(f"Failed to perform batch operations in Chroma: {e}")
            raise

    async def get_collection_stats(self, collection_name: str) -> dict[str, Any]:
        """Get statistics about a Chroma collection."""
        if not self._initialized:
            await self.initialize()

        try:
            collection = self.client.get_collection(name=collection_name)

            # Get collection count
            count = collection.count()

            # Get sample to determine dimensions
            sample = collection.peek(limit=1)
            dimensions = len(sample["embeddings"][0]) if sample.get("embeddings") else 0

            return {
                "count": count,
                "dimensions": dimensions,
                "metadata": collection.metadata or {},
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats from Chroma: {e}")
            raise

    async def close(self) -> None:
        """Close Chroma connections and cleanup resources."""
        self.client = None
        self._initialized = False
        logger.info("Closed Chroma backend")
