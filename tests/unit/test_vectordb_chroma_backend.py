"""Unit tests for app.core.vectordb.chroma_backend module."""

from unittest.mock import MagicMock, patch

import pytest

from app.core.vectordb.chroma_backend import ChromaBackend
from app.core.vectordb.config import VectorDBConfig


class TestChromaBackend:
    """Test the ChromaBackend class."""

    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        return VectorDBConfig()

    @pytest.fixture
    def backend(self, config):
        """Create a ChromaBackend instance."""
        return ChromaBackend(config)

    @pytest.mark.asyncio
    async def test_initialize_success(self, backend):
        """Test successful initialization."""
        mock_client = MagicMock()
        mock_client.list_collections.return_value = []

        mock_chromadb = MagicMock()
        mock_chromadb.PersistentClient = MagicMock(return_value=mock_client)

        with patch(
            "builtins.__import__",
            side_effect=lambda name, *args, **kwargs: mock_chromadb
            if name == "chromadb"
            else __import__(name, *args, **kwargs),
        ):
            await backend.initialize()
            assert backend._initialized is True
            assert backend.client is not None

    @pytest.mark.asyncio
    async def test_initialize_import_error(self, backend):
        """Test initialization with missing chromadb."""

        def mock_import(name, *args, **kwargs):
            if name == "chromadb":
                raise ImportError("No module named 'chromadb'")
            return __import__(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            with pytest.raises(ImportError, match="chromadb not installed"):
                await backend.initialize()

    @pytest.mark.asyncio
    async def test_health_check_success(self, backend):
        """Test successful health check."""
        mock_client = MagicMock()
        mock_client.list_collections.return_value = []

        mock_chromadb = MagicMock()
        mock_chromadb.PersistentClient = MagicMock(return_value=mock_client)

        with patch(
            "builtins.__import__",
            side_effect=lambda name, *args, **kwargs: mock_chromadb
            if name == "chromadb"
            else __import__(name, *args, **kwargs),
        ):
            await backend.initialize()
            result = await backend.health_check()
            assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self, backend):
        """Test health check failure."""
        mock_client = MagicMock()
        mock_client.list_collections.side_effect = Exception("Connection error")

        mock_chromadb = MagicMock()
        mock_chromadb.PersistentClient = MagicMock(return_value=mock_client)

        with patch(
            "builtins.__import__",
            side_effect=lambda name, *args, **kwargs: mock_chromadb
            if name == "chromadb"
            else __import__(name, *args, **kwargs),
        ):
            await backend.initialize()
            result = await backend.health_check()
            assert result is False

    @pytest.mark.asyncio
    async def test_create_collection(self, backend):
        """Test creating a collection."""
        mock_client = MagicMock()
        mock_client.list_collections.return_value = []

        mock_chromadb = MagicMock()
        mock_chromadb.PersistentClient = MagicMock(return_value=mock_client)

        with patch(
            "builtins.__import__",
            side_effect=lambda name, *args, **kwargs: mock_chromadb
            if name == "chromadb"
            else __import__(name, *args, **kwargs),
        ):
            await backend.initialize()
            await backend.create_collection("test_collection", {"test": "metadata"})
            mock_client.create_collection.assert_called_once()

    @pytest.mark.asyncio
    async def test_collection_exists(self, backend):
        """Test checking if collection exists."""
        mock_collection = MagicMock()
        mock_collection.name = "test_collection"
        mock_client = MagicMock()
        mock_client.list_collections.return_value = [mock_collection]

        mock_chromadb = MagicMock()
        mock_chromadb.PersistentClient = MagicMock(return_value=mock_client)

        with patch(
            "builtins.__import__",
            side_effect=lambda name, *args, **kwargs: mock_chromadb
            if name == "chromadb"
            else __import__(name, *args, **kwargs),
        ):
            await backend.initialize()
            exists = await backend.collection_exists("test_collection")
            assert exists is True

    @pytest.mark.asyncio
    async def test_add_vectors(self, backend):
        """Test adding vectors."""
        mock_collection = MagicMock()
        mock_client = MagicMock()
        mock_client.get_collection.return_value = mock_collection

        mock_chromadb = MagicMock()
        mock_chromadb.PersistentClient = MagicMock(return_value=mock_client)

        with patch(
            "builtins.__import__",
            side_effect=lambda name, *args, **kwargs: mock_chromadb
            if name == "chromadb"
            else __import__(name, *args, **kwargs),
        ):
            await backend.initialize()
            await backend.add_vectors(
                "test_collection",
                [[0.1, 0.2, 0.3]],
                ["id1"],
                [{"test": "metadata"}],
            )
            mock_collection.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_vectors(self, backend):
        """Test searching vectors."""
        mock_collection = MagicMock()
        mock_collection.query.return_value = {
            "ids": [["id1", "id2"]],
            "distances": [[0.1, 0.2]],
            "metadatas": [[{"test": "data1"}, {"test": "data2"}]],
        }
        mock_client = MagicMock()
        mock_client.get_collection.return_value = mock_collection

        mock_chromadb = MagicMock()
        mock_chromadb.PersistentClient = MagicMock(return_value=mock_client)

        with patch(
            "builtins.__import__",
            side_effect=lambda name, *args, **kwargs: mock_chromadb
            if name == "chromadb"
            else __import__(name, *args, **kwargs),
        ):
            await backend.initialize()
            results = await backend.search_vectors("test_collection", [0.1, 0.2, 0.3], limit=10)
            assert len(results) == 2
            assert results[0]["id"] == "id1"

    @pytest.mark.asyncio
    async def test_update_vectors(self, backend):
        """Test updating vectors."""
        mock_collection = MagicMock()
        mock_client = MagicMock()
        mock_client.get_collection.return_value = mock_collection

        mock_chromadb = MagicMock()
        mock_chromadb.PersistentClient = MagicMock(return_value=mock_client)

        with patch(
            "builtins.__import__",
            side_effect=lambda name, *args, **kwargs: mock_chromadb
            if name == "chromadb"
            else __import__(name, *args, **kwargs),
        ):
            await backend.initialize()
            await backend.update_vectors(
                "test_collection",
                [[0.1, 0.2, 0.3]],
                ["id1"],
                [{"test": "metadata"}],
            )
            mock_collection.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_vectors(self, backend):
        """Test deleting vectors."""
        mock_collection = MagicMock()
        mock_client = MagicMock()
        mock_client.get_collection.return_value = mock_collection

        mock_chromadb = MagicMock()
        mock_chromadb.PersistentClient = MagicMock(return_value=mock_client)

        with patch(
            "builtins.__import__",
            side_effect=lambda name, *args, **kwargs: mock_chromadb
            if name == "chromadb"
            else __import__(name, *args, **kwargs),
        ):
            await backend.initialize()
            await backend.delete_vectors("test_collection", ["id1"])
            mock_collection.delete.assert_called_once_with(ids=["id1"])

    @pytest.mark.asyncio
    async def test_get_collection_stats(self, backend):
        """Test getting collection statistics."""
        mock_collection = MagicMock()
        mock_collection.count.return_value = 10
        mock_collection.peek.return_value = {
            "embeddings": [[0.1, 0.2, 0.3]],
        }
        mock_collection.metadata = {"test": "metadata"}
        mock_client = MagicMock()
        mock_client.get_collection.return_value = mock_collection

        mock_chromadb = MagicMock()
        mock_chromadb.PersistentClient = MagicMock(return_value=mock_client)

        with patch(
            "builtins.__import__",
            side_effect=lambda name, *args, **kwargs: mock_chromadb
            if name == "chromadb"
            else __import__(name, *args, **kwargs),
        ):
            await backend.initialize()
            stats = await backend.get_collection_stats("test_collection")
            assert stats["count"] == 10
            assert stats["dimensions"] == 3

    @pytest.mark.asyncio
    async def test_close(self, backend):
        """Test closing the backend."""
        mock_client = MagicMock()
        mock_chromadb = MagicMock()
        mock_chromadb.PersistentClient = MagicMock(return_value=mock_client)

        with patch(
            "builtins.__import__",
            side_effect=lambda name, *args, **kwargs: mock_chromadb
            if name == "chromadb"
            else __import__(name, *args, **kwargs),
        ):
            await backend.initialize()
            await backend.close()
            assert backend.client is None
            assert backend._initialized is False
