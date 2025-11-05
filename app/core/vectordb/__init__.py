"""Vector DB module for hass-mcp.

This module provides vector database infrastructure for semantic search capabilities.
"""

from app.core.vectordb.config import VectorDBConfig, get_vectordb_config
from app.core.vectordb.indexing import (
    generate_entity_description,
    generate_entity_metadata,
    get_indexing_status,
    index_entities,
    index_entity,
    remove_entity_from_index,
    update_entity_index,
)
from app.core.vectordb.manager import VectorDBManager, get_vectordb_manager

__all__ = [
    "VectorDBConfig",
    "get_vectordb_config",
    "VectorDBManager",
    "get_vectordb_manager",
    "generate_entity_description",
    "generate_entity_metadata",
    "index_entity",
    "index_entities",
    "update_entity_index",
    "remove_entity_from_index",
    "get_indexing_status",
]
