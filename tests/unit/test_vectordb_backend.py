"""Unit tests for app.core.vectordb.backend module."""

import pytest

from app.core.vectordb.backend import VectorDBBackend


class TestVectorDBBackend:
    """Test the VectorDBBackend abstract class."""

    def test_abstract_methods(self):
        """Test that VectorDBBackend is abstract and cannot be instantiated."""
        with pytest.raises(TypeError):
            VectorDBBackend()  # type: ignore[abstract]

    def test_abstract_methods_exist(self):
        """Test that all abstract methods are defined."""
        abstract_methods = {
            "initialize",
            "health_check",
            "create_collection",
            "delete_collection",
            "collection_exists",
            "add_vectors",
            "search_vectors",
            "update_vectors",
            "delete_vectors",
            "batch_operations",
            "get_collection_stats",
            "close",
        }

        for method_name in abstract_methods:
            assert hasattr(VectorDBBackend, method_name)
            method = getattr(VectorDBBackend, method_name)
            assert hasattr(method, "__isabstractmethod__")
