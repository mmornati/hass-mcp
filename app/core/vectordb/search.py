"""Semantic search module for hass-mcp.

This module provides semantic search functionality for entities using
natural language queries and vector similarity.
"""

import logging
from typing import Any

from app.api.entities import get_entities, get_entity_state
from app.core.vectordb.config import VectorDBConfig, get_vectordb_config
from app.core.vectordb.indexing import ENTITY_COLLECTION
from app.core.vectordb.manager import VectorDBManager, get_vectordb_manager

logger = logging.getLogger(__name__)


async def semantic_search(
    query: str,
    domain: str | None = None,
    area_id: str | None = None,
    device_manufacturer: str | None = None,
    entity_state: str | None = None,
    limit: int = 10,
    similarity_threshold: float | None = None,
    hybrid_search: bool | None = None,
    manager: VectorDBManager | None = None,
    config: VectorDBConfig | None = None,
) -> list[dict[str, Any]]:
    """
    Perform semantic search for entities using natural language queries.

    Args:
        query: Natural language search query
        domain: Optional domain filter (e.g., "light", "sensor")
        area_id: Optional area/room filter
        device_manufacturer: Optional device manufacturer filter
        entity_state: Optional entity state filter (e.g., "on", "off")
        limit: Maximum number of results to return
        similarity_threshold: Minimum similarity score (0.0-1.0)
        hybrid_search: Whether to use hybrid search (combines semantic + keyword)
        manager: Optional VectorDBManager instance
        config: Optional VectorDBConfig instance

    Returns:
        List of entities with similarity scores and metadata:
        - entity_id: Entity ID
        - similarity_score: Similarity score (0.0-1.0)
        - entity: Entity state dictionary
        - explanation: Explanation for why entity matched
        - metadata: Entity metadata from vector DB
    """
    manager = manager or get_vectordb_manager()
    config = config or get_vectordb_config()

    if not config.is_enabled():
        logger.debug("Vector DB is disabled, falling back to keyword search")
        return await _keyword_search(query, domain, area_id, limit)

    # Get configuration values
    if similarity_threshold is None:
        similarity_threshold = config.get_search_similarity_threshold()
    if hybrid_search is None:
        hybrid_search = config.get_search_hybrid_search()
    if limit is None:
        limit = config.get_search_default_limit()

    try:
        # Initialize if needed
        if not manager._initialized:
            await manager.initialize()

        # Build metadata filters
        filter_metadata: dict[str, Any] = {}
        if domain:
            filter_metadata["domain"] = domain
        if area_id:
            filter_metadata["area_id"] = area_id
        if device_manufacturer:
            filter_metadata["manufacturer"] = device_manufacturer

        # Perform semantic search
        vector_results = await manager.search_vectors(
            collection_name=ENTITY_COLLECTION,
            query_text=query,
            limit=limit * 2,  # Get more results for ranking
            filter_metadata=filter_metadata if filter_metadata else None,
        )

        # Process and rank results
        results = await _process_search_results(
            vector_results, query, similarity_threshold, entity_state, limit
        )

        # Hybrid search: combine with keyword search if enabled
        if hybrid_search:
            keyword_results = await _keyword_search(query, domain, area_id, limit)
            results = _merge_and_rank_results(results, keyword_results, limit)

        return results[:limit]

    except Exception as e:
        logger.error(f"Semantic search failed: {e}, falling back to keyword search")
        return await _keyword_search(query, domain, area_id, limit)


async def _process_search_results(
    vector_results: list[dict[str, Any]],
    query: str,
    similarity_threshold: float,
    entity_state: str | None,
    limit: int,
) -> list[dict[str, Any]]:
    """
    Process and rank vector search results.

    Args:
        vector_results: Raw vector search results
        query: Original query string
        similarity_threshold: Minimum similarity score
        entity_state: Optional entity state filter
        limit: Maximum results

    Returns:
        Processed and ranked results
    """
    processed_results = []

    for result in vector_results:
        entity_id = result.get("id") or result.get("entity_id")
        if not entity_id:
            continue

        similarity_score = result.get("distance") or result.get("similarity")
        if similarity_score is None:
            continue

        # Convert distance to similarity
        # Chroma uses cosine distance (0 = identical, 2 = opposite)
        # Convert to similarity (1.0 = identical, 0.0 = opposite)
        if "distance" in result:
            # Chroma returns cosine distance (0-2 range)
            # Convert to similarity: similarity = 1 - (distance / 2)
            distance = float(similarity_score)
            similarity_score = max(0.0, min(1.0, 1.0 - (distance / 2.0)))
        elif isinstance(similarity_score, (int, float)):
            if similarity_score <= 0:
                similarity_score = 0.0
            elif similarity_score > 1.0:
                # Likely a distance metric, convert to similarity
                similarity_score = 1.0 / (1.0 + similarity_score)
            else:
                # Already in 0-1 range, just ensure it's a float
                similarity_score = float(similarity_score)

        # Apply similarity threshold
        if similarity_score < similarity_threshold:
            continue

        # Get entity state
        try:
            entity = await get_entity_state(entity_id, lean=True)
            if isinstance(entity, dict) and "error" in entity:
                continue

            # Filter by state if specified
            if entity_state and entity.get("state", "").lower() != entity_state.lower():
                continue

            # Build explanation
            explanation = _build_explanation(entity, query, similarity_score)

            # Boost score for exact matches
            boosted_score = _boost_score(
                entity, query, similarity_score, result.get("metadata", {})
            )

            processed_results.append(
                {
                    "entity_id": entity_id,
                    "similarity_score": boosted_score,
                    "entity": entity,
                    "explanation": explanation,
                    "metadata": result.get("metadata", {}),
                }
            )
        except Exception as e:
            logger.debug(f"Failed to get entity {entity_id}: {e}")
            continue

    # Sort by similarity score (descending)
    processed_results.sort(key=lambda x: x["similarity_score"], reverse=True)

    return processed_results


def _build_explanation(entity: dict[str, Any], query: str, similarity_score: float) -> str:
    """
    Build explanation for why entity matched.

    Args:
        entity: Entity state dictionary
        query: Original query string
        similarity_score: Similarity score

    Returns:
        Explanation string
    """
    parts = []
    entity_id = entity.get("entity_id", "")
    friendly_name = entity.get("attributes", {}).get("friendly_name", "")
    domain = entity_id.split(".")[0] if "." in entity_id else "unknown"
    area_id = entity.get("attributes", {}).get("area_id")

    if friendly_name:
        parts.append(f'Entity "{friendly_name}"')
    else:
        parts.append(f'Entity "{entity_id}"')

    parts.append(f"({domain})")

    if area_id:
        parts.append(f'in area "{area_id}"')

    parts.append(f"matched with {similarity_score:.2%} similarity")

    return " ".join(parts)


def _boost_score(
    entity: dict[str, Any],
    query: str,
    base_score: float,
    metadata: dict[str, Any],
) -> float:
    """
    Boost similarity score for exact matches.

    Args:
        entity: Entity state dictionary
        query: Original query string
        base_score: Base similarity score
        metadata: Entity metadata

    Returns:
        Boosted similarity score
    """
    boosted_score = base_score
    query_lower = query.lower()
    entity_id = entity.get("entity_id", "").lower()
    friendly_name = entity.get("attributes", {}).get("friendly_name", "").lower()
    domain = entity_id.split(".")[0] if "." in entity_id else ""
    area_id = entity.get("attributes", {}).get("area_id", "").lower()

    # Boost for exact entity_id match
    if query_lower in entity_id:
        boosted_score = min(1.0, boosted_score + 0.2)

    # Boost for exact friendly_name match
    if friendly_name and query_lower in friendly_name:
        boosted_score = min(1.0, boosted_score + 0.15)

    # Boost for domain match
    if domain and domain in query_lower:
        boosted_score = min(1.0, boosted_score + 0.1)

    # Boost for area match
    if area_id and area_id in query_lower:
        boosted_score = min(1.0, boosted_score + 0.1)

    return boosted_score


async def _keyword_search(
    query: str,
    domain: str | None = None,
    area_id: str | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """
    Perform keyword-based search for entities.

    Args:
        query: Search query string
        domain: Optional domain filter
        area_id: Optional area filter
        limit: Maximum results

    Returns:
        List of entities with keyword match scores
    """
    try:
        entities = await get_entities(domain=domain, search_query=query, limit=limit * 2, lean=True)
        if isinstance(entities, dict) and "error" in entities:
            return []

        results = []
        query_lower = query.lower()
        query_words = set(query_lower.split())

        for entity in entities:
            if not isinstance(entity, dict):
                continue

            entity_id = entity.get("entity_id", "").lower()
            friendly_name = entity.get("attributes", {}).get("friendly_name", "").lower()
            entity_area_id = entity.get("attributes", {}).get("area_id", "").lower()

            # Filter by area if specified
            if area_id and entity_area_id != area_id.lower():
                continue

            # Calculate keyword match score
            score = 0.0
            matches = []

            # Check entity_id
            if query_lower in entity_id:
                score += 0.5
                matches.append("entity_id")

            # Check friendly_name
            if friendly_name:
                if query_lower in friendly_name:
                    score += 0.4
                    matches.append("friendly_name")
                # Check word matches
                name_words = set(friendly_name.split())
                common_words = query_words.intersection(name_words)
                if common_words:
                    score += 0.1 * len(common_words)
                    matches.append("name_words")

            if score > 0:
                results.append(
                    {
                        "entity_id": entity.get("entity_id"),
                        "similarity_score": score,
                        "entity": entity,
                        "explanation": f"Keyword match in {', '.join(matches)}",
                        "metadata": {},
                    }
                )

        # Sort by score (descending)
        results.sort(key=lambda x: x["similarity_score"], reverse=True)

        return results[:limit]

    except Exception as e:
        logger.error(f"Keyword search failed: {e}")
        return []


def _merge_and_rank_results(
    semantic_results: list[dict[str, Any]],
    keyword_results: list[dict[str, Any]],
    limit: int,
) -> list[dict[str, Any]]:
    """
    Merge and rank semantic and keyword search results.

    Args:
        semantic_results: Semantic search results
        keyword_results: Keyword search results
        limit: Maximum results

    Returns:
        Merged and ranked results
    """
    # Create a map of entity_id to best result
    result_map: dict[str, dict[str, Any]] = {}

    # Add semantic results (weighted higher)
    for result in semantic_results:
        entity_id = result.get("entity_id")
        if entity_id:
            # Boost semantic results
            result["similarity_score"] = result.get("similarity_score", 0.0) * 1.2
            result["source"] = "semantic"
            result_map[entity_id] = result

    # Add keyword results (merge or add)
    for result in keyword_results:
        entity_id = result.get("entity_id")
        if entity_id:
            if entity_id in result_map:
                # Merge: use higher score
                existing_score = result_map[entity_id].get("similarity_score", 0.0)
                keyword_score = result.get("similarity_score", 0.0)
                if keyword_score > existing_score:
                    result["similarity_score"] = keyword_score
                    result["source"] = "hybrid"
                    result_map[entity_id] = result
            else:
                # Add new result
                result["source"] = "keyword"
                result_map[entity_id] = result

    # Convert to list and sort
    merged_results = list(result_map.values())
    merged_results.sort(key=lambda x: x.get("similarity_score", 0.0), reverse=True)

    return merged_results[:limit]
