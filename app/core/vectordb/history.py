"""Query history and learning module for hass-mcp.

This module provides query history storage, pattern analysis, personalized ranking,
and learning from user query patterns.
"""

import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from app.core.vectordb.classification import process_query
from app.core.vectordb.config import VectorDBConfig, get_vectordb_config
from app.core.vectordb.manager import VectorDBManager, get_vectordb_manager

logger = logging.getLogger(__name__)

# Collection name for query history
QUERY_HISTORY_COLLECTION = "query_history"

# Collection name for entity popularity
ENTITY_POPULARITY_COLLECTION = "entity_popularity"


async def store_query_history(
    query: str,
    results: list[dict[str, Any]] | None = None,
    selected_entity_id: str | None = None,
    user_id: str | None = None,
    manager: VectorDBManager | None = None,
    config: VectorDBConfig | None = None,
) -> dict[str, Any]:
    """
    Store a query in the history.

    Args:
        query: The query text
        results: List of search results returned
        selected_entity_id: Entity ID that was selected/used (if any)
        user_id: Optional user identifier
        manager: Optional VectorDBManager instance
        config: Optional VectorDBConfig instance

    Returns:
        Dictionary with stored query information:
        - query_id: Unique query ID
        - query_text: Original query text
        - timestamp: When the query was stored
        - success: Whether storage was successful
    """
    manager = manager or get_vectordb_manager()
    config = config or get_vectordb_config()

    if not config.is_enabled():
        logger.debug("Vector DB is disabled, skipping query history storage")
        return {
            "query_id": str(uuid.uuid4()),
            "query_text": query,
            "timestamp": datetime.now(UTC).isoformat(),
            "success": False,
            "reason": "Vector DB disabled",
        }

    try:
        # Initialize if needed
        if not manager._initialized:
            await manager.initialize()

        if not manager.backend:
            raise RuntimeError("Vector DB backend not initialized")

        if not manager.embedding_model:
            raise RuntimeError("Embedding model not initialized")

        # Generate query ID
        query_id = str(uuid.uuid4())

        # Generate query embedding
        query_embeddings = await manager.embed_texts([query])
        query_embedding = query_embeddings[0]

        # Classify query to get intent and metadata
        classification = await process_query(query, manager, config)

        # Build metadata
        metadata: dict[str, Any] = {
            "query_id": query_id,
            "query_text": query,
            "timestamp": datetime.now(UTC).isoformat(),
            "intent": classification.get("intent", "SEARCH"),
            "domain": classification.get("domain"),
            "result_count": len(results) if results else 0,
            "selected_entity_id": selected_entity_id,
            "success": True,
        }

        if user_id:
            metadata["user_id"] = user_id

        # Add context information
        context: dict[str, Any] = {}
        hour = datetime.now(UTC).hour
        if 6 <= hour < 12:
            context["time_of_day"] = "morning"
        elif 12 <= hour < 18:
            context["time_of_day"] = "afternoon"
        elif 18 <= hour < 22:
            context["time_of_day"] = "evening"
        else:
            context["time_of_day"] = "night"

        if classification.get("entity_filters", {}).get("area_id"):
            context["area"] = classification["entity_filters"]["area_id"]

        if context:
            metadata["context"] = context

        # Store results summary
        if results:
            results_summary = []
            for i, result in enumerate(results[:10]):  # Store top 10 results
                result_info = {
                    "entity_id": result.get("entity_id"),
                    "rank": i + 1,
                    "similarity_score": result.get("similarity_score"),
                    "selected": result.get("entity_id") == selected_entity_id,
                }
                results_summary.append(result_info)
            metadata["results"] = results_summary

        # Ensure collection exists
        if not await manager.backend.collection_exists(QUERY_HISTORY_COLLECTION):
            await manager.backend.create_collection(QUERY_HISTORY_COLLECTION)

        # Store query in vector DB
        await manager.backend.add_vectors(
            collection_name=QUERY_HISTORY_COLLECTION,
            vectors=[query_embedding],
            ids=[query_id],
            metadata=[metadata],
        )

        # Learn from query if entity was selected
        if selected_entity_id:
            await _learn_from_query(query, selected_entity_id, manager, config)

        return {
            "query_id": query_id,
            "query_text": query,
            "timestamp": metadata["timestamp"],
            "success": True,
        }

    except Exception as e:
        logger.error(f"Failed to store query history: {e}")
        return {
            "query_id": str(uuid.uuid4()),
            "query_text": query,
            "timestamp": datetime.now(UTC).isoformat(),
            "success": False,
            "error": str(e),
        }


async def _learn_from_query(
    query: str,
    selected_entity_id: str,
    manager: VectorDBManager,
    config: VectorDBConfig,
) -> None:
    """
    Learn from user query and selection.

    Args:
        query: The query text
        selected_entity_id: Entity ID that was selected
        manager: VectorDBManager instance
        config: VectorDBConfig instance
    """
    try:
        # Update entity popularity
        await _increment_entity_popularity(selected_entity_id, manager, config)

        # Update query patterns (could be extended in future)
        logger.debug(f"Learning from query: {query} -> {selected_entity_id}")

    except Exception as e:
        logger.debug(f"Failed to learn from query: {e}")


async def _increment_entity_popularity(
    entity_id: str,
    manager: VectorDBManager,
    config: VectorDBConfig,
) -> None:
    """
    Increment entity popularity counter.

    Args:
        entity_id: Entity ID to increment popularity for
        manager: VectorDBManager instance
        config: VectorDBConfig instance
    """
    try:
        if not manager.backend:
            return

        # Ensure collection exists
        if not await manager.backend.collection_exists(ENTITY_POPULARITY_COLLECTION):
            await manager.backend.create_collection(ENTITY_POPULARITY_COLLECTION)

        # Check if entity popularity already exists
        # For simplicity, we'll use a simple counter approach
        # In a real implementation, you might want to use a separate storage
        # or update the existing vector with new popularity count
        popularity_id = f"popularity_{entity_id}"

        # Get current popularity (if exists)
        # Note: This is a simplified implementation
        # A full implementation would need to track and update popularity counts
        current_popularity = 1  # Default to 1

        # Store popularity (simplified - in production, you'd update existing)
        popularity_embedding = await manager.embed_texts([entity_id])
        popularity_metadata = {
            "entity_id": entity_id,
            "popularity_count": current_popularity,
            "last_updated": datetime.now(UTC).isoformat(),
        }

        await manager.backend.add_vectors(
            collection_name=ENTITY_POPULARITY_COLLECTION,
            vectors=[popularity_embedding[0]],
            ids=[popularity_id],
            metadata=[popularity_metadata],
        )

    except Exception as e:
        logger.debug(f"Failed to increment entity popularity: {e}")


async def get_entity_popularity(
    entity_id: str,
    manager: VectorDBManager | None = None,
    config: VectorDBConfig | None = None,
) -> int:
    """
    Get entity popularity count.

    Args:
        entity_id: Entity ID to get popularity for
        manager: Optional VectorDBManager instance
        config: Optional VectorDBConfig instance

    Returns:
        Popularity count (0 if not found)
    """
    manager = manager or get_vectordb_manager()
    config = config or get_vectordb_config()

    if not config.is_enabled():
        return 0

    try:
        if not manager._initialized:
            await manager.initialize()

        if not manager.backend:
            return 0

        if not await manager.backend.collection_exists(ENTITY_POPULARITY_COLLECTION):
            return 0

        # Search for entity popularity
        popularity_id = f"popularity_{entity_id}"
        entity_embedding = await manager.embed_texts([entity_id])

        # Search for the entity in popularity collection
        results = await manager.backend.search_vectors(
            collection_name=ENTITY_POPULARITY_COLLECTION,
            query_vector=entity_embedding[0],
            limit=1,
        )

        if results and len(results) > 0:
            metadata = results[0].get("metadata", {})
            if metadata.get("entity_id") == entity_id:
                return metadata.get("popularity_count", 0)

        return 0

    except Exception as e:
        logger.debug(f"Failed to get entity popularity: {e}")
        return 0


async def get_query_history(
    limit: int = 50,
    user_id: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    manager: VectorDBManager | None = None,
    config: VectorDBConfig | None = None,
) -> list[dict[str, Any]]:
    """
    Get query history.

    Args:
        limit: Maximum number of queries to return
        user_id: Optional user ID to filter by
        start_date: Optional start date filter
        end_date: Optional end date filter
        manager: Optional VectorDBManager instance
        config: Optional VectorDBConfig instance

    Returns:
        List of query history entries
    """
    manager = manager or get_vectordb_manager()
    config = config or get_vectordb_config()

    if not config.is_enabled():
        return []

    try:
        if not manager._initialized:
            await manager.initialize()

        if not manager.backend:
            return []

        if not await manager.backend.collection_exists(QUERY_HISTORY_COLLECTION):
            return []

        # Get all queries (simplified - in production, you'd want better filtering)
        # For now, we'll get recent queries by searching with a generic query
        recent_query_embedding = await manager.embed_texts(["recent queries"])
        results = await manager.backend.search_vectors(
            collection_name=QUERY_HISTORY_COLLECTION,
            query_vector=recent_query_embedding[0],
            limit=limit * 2,  # Get more to filter
        )

        # Filter and sort results
        history_entries = []
        for result in results:
            metadata = result.get("metadata", {})
            if not metadata:
                continue

            # Filter by user_id if specified
            if user_id and metadata.get("user_id") != user_id:
                continue

            # Filter by date range if specified
            timestamp_str = metadata.get("timestamp")
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                    if start_date and timestamp < start_date:
                        continue
                    if end_date and timestamp > end_date:
                        continue
                except (ValueError, AttributeError):
                    pass

            history_entries.append(metadata)

        # Sort by timestamp (most recent first)
        history_entries.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        return history_entries[:limit]

    except Exception as e:
        logger.error(f"Failed to get query history: {e}")
        return []


async def clear_query_history(
    user_id: str | None = None,
    before_date: datetime | None = None,
    manager: VectorDBManager | None = None,
    config: VectorDBConfig | None = None,
) -> dict[str, Any]:
    """
    Clear query history.

    Args:
        user_id: Optional user ID to clear history for (if None, clears all)
        before_date: Optional date to clear history before
        manager: Optional VectorDBManager instance
        config: Optional VectorDBConfig instance

    Returns:
        Dictionary with deletion results:
        - deleted_count: Number of queries deleted
        - success: Whether deletion was successful
    """
    manager = manager or get_vectordb_manager()
    config = config or get_vectordb_config()

    if not config.is_enabled():
        return {"deleted_count": 0, "success": False, "reason": "Vector DB disabled"}

    try:
        if not manager._initialized:
            await manager.initialize()

        if not manager.backend:
            return {"deleted_count": 0, "success": False, "reason": "Backend not initialized"}

        if not await manager.backend.collection_exists(QUERY_HISTORY_COLLECTION):
            return {"deleted_count": 0, "success": True}

        # Get queries to delete
        history_entries = await get_query_history(
            limit=10000,  # Get a large number
            user_id=user_id,
            end_date=before_date,
            manager=manager,
            config=config,
        )

        # Delete queries
        query_ids = [entry.get("query_id") for entry in history_entries if entry.get("query_id")]
        if query_ids:
            await manager.backend.delete_vectors(QUERY_HISTORY_COLLECTION, query_ids)

        return {
            "deleted_count": len(query_ids),
            "success": True,
        }

    except Exception as e:
        logger.error(f"Failed to clear query history: {e}")
        return {"deleted_count": 0, "success": False, "error": str(e)}


async def get_query_statistics(
    user_id: str | None = None,
    days: int = 30,
    manager: VectorDBManager | None = None,
    config: VectorDBConfig | None = None,
) -> dict[str, Any]:
    """
    Get query statistics.

    Args:
        user_id: Optional user ID to filter by
        days: Number of days to analyze
        manager: Optional VectorDBManager instance
        config: Optional VectorDBConfig instance

    Returns:
        Dictionary with statistics:
        - total_queries: Total number of queries
        - unique_queries: Number of unique queries
        - most_common_queries: List of most common queries
        - most_common_intents: List of most common intents
        - most_common_domains: List of most common domains
        - most_selected_entities: List of most selected entities
        - queries_by_time_of_day: Distribution by time of day
    """
    manager = manager or get_vectordb_manager()
    config = config or get_vectordb_config()

    if not config.is_enabled():
        return {
            "total_queries": 0,
            "unique_queries": 0,
            "most_common_queries": [],
            "most_common_intents": [],
            "most_common_domains": [],
            "most_selected_entities": [],
            "queries_by_time_of_day": {},
        }

    try:
        # Get query history for the specified period
        end_date = datetime.now(UTC)
        start_date = end_date - timedelta(days=days)

        history = await get_query_history(
            limit=10000,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            manager=manager,
            config=config,
        )

        # Calculate statistics
        total_queries = len(history)
        unique_queries = len({entry.get("query_text", "") for entry in history})

        # Count queries by text
        query_counts: dict[str, int] = {}
        intent_counts: dict[str, int] = {}
        domain_counts: dict[str, int] = {}
        entity_counts: dict[str, int] = {}
        time_of_day_counts: dict[str, int] = {}

        for entry in history:
            query_text = entry.get("query_text", "")
            if query_text:
                query_counts[query_text] = query_counts.get(query_text, 0) + 1

            intent = entry.get("intent")
            if intent:
                intent_counts[intent] = intent_counts.get(intent, 0) + 1

            domain = entry.get("domain")
            if domain:
                domain_counts[domain] = domain_counts.get(domain, 0) + 1

            selected_entity = entry.get("selected_entity_id")
            if selected_entity:
                entity_counts[selected_entity] = entity_counts.get(selected_entity, 0) + 1

            context = entry.get("context", {})
            time_of_day = context.get("time_of_day")
            if time_of_day:
                time_of_day_counts[time_of_day] = time_of_day_counts.get(time_of_day, 0) + 1

        # Get top items
        most_common_queries = sorted(query_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        most_common_intents = sorted(intent_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        most_common_domains = sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        most_selected_entities = sorted(entity_counts.items(), key=lambda x: x[1], reverse=True)[
            :10
        ]

        return {
            "total_queries": total_queries,
            "unique_queries": unique_queries,
            "most_common_queries": [{"query": q, "count": c} for q, c in most_common_queries],
            "most_common_intents": [{"intent": i, "count": c} for i, c in most_common_intents],
            "most_common_domains": [{"domain": d, "count": c} for d, c in most_common_domains],
            "most_selected_entities": [
                {"entity_id": e, "count": c} for e, c in most_selected_entities
            ],
            "queries_by_time_of_day": time_of_day_counts,
        }

    except Exception as e:
        logger.error(f"Failed to get query statistics: {e}")
        return {
            "total_queries": 0,
            "unique_queries": 0,
            "most_common_queries": [],
            "most_common_intents": [],
            "most_common_domains": [],
            "most_selected_entities": [],
            "queries_by_time_of_day": {},
        }


async def boost_entity_ranking(
    entities: list[dict[str, Any]],
    boost_factor: float = 0.1,
    manager: VectorDBManager | None = None,
    config: VectorDBConfig | None = None,
) -> list[dict[str, Any]]:
    """
    Boost entity ranking based on popularity.

    Args:
        entities: List of entities with similarity scores
        boost_factor: Factor to boost popular entities (0.0-1.0)
        manager: Optional VectorDBManager instance
        config: Optional VectorDBConfig instance

    Returns:
        List of entities with boosted scores
    """
    manager = manager or get_vectordb_manager()
    config = config or get_vectordb_config()

    if not config.is_enabled():
        return entities

    try:
        # Get popularity for each entity
        for entity in entities:
            entity_id = entity.get("entity_id")
            if not entity_id:
                continue

            popularity = await get_entity_popularity(entity_id, manager, config)
            if popularity > 0:
                # Boost score based on popularity
                # Simple linear boost: popularity * boost_factor
                boost = min(boost_factor, popularity * 0.01 * boost_factor)
                current_score = entity.get("similarity_score", 0.0)
                entity["similarity_score"] = min(1.0, current_score + boost)
                entity["popularity_boost"] = boost

        # Re-sort by boosted score
        entities.sort(key=lambda x: x.get("similarity_score", 0.0), reverse=True)

        return entities

    except Exception as e:
        logger.debug(f"Failed to boost entity ranking: {e}")
        return entities
