"""Vector DB module for hass-mcp.

This module provides vector database infrastructure for semantic search capabilities.
"""

from app.core.vectordb.classification import (
    classify_intent,
    extract_action,
    extract_entities,
    extract_parameters,
    predict_domain,
    process_query,
    refine_query,
)
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
from app.core.vectordb.search import semantic_search

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
    "semantic_search",
    "classify_intent",
    "predict_domain",
    "extract_action",
    "extract_entities",
    "extract_parameters",
    "refine_query",
    "process_query",
]
