"""Natural language query processing MCP tool for hass-mcp.

This module provides a tool for processing natural language queries to extract
entities, actions, and parameters for executing user commands.
"""

import logging
from typing import Any

from app.core.vectordb.classification import process_query  # noqa: PLC0415
from app.core.vectordb.search import semantic_search  # noqa: PLC0415

logger = logging.getLogger(__name__)


async def process_natural_language_query(query: str) -> dict[str, Any]:
    """
    Process natural language query to extract entities, actions, and parameters.

    This tool processes natural language queries to automatically extract:
    - Intent (CONTROL, STATUS, SEARCH, etc.)
    - Entities (resolved to actual entity IDs)
    - Actions (on, off, set, etc.)
    - Parameters (temperature, brightness, etc.)
    - Execution plan (structured plan for executing the query)

    Args:
        query: Natural language query (e.g., "Turn on the living room lights",
               "Set kitchen temperature to 22 degrees")

    Returns:
        A dictionary containing:
        - intent: Query intent (CONTROL, STATUS, SEARCH, etc.)
        - confidence: Intent confidence score (0.0-1.0)
        - entities: List of resolved entities with confidence scores
        - action: Extracted action (on, off, set, etc.)
        - action_params: Action parameters
        - parameters: Extracted parameters (temperature, brightness, etc.)
        - execution_plan: Structured execution plan
        - domain: Predicted domain (light, sensor, climate, etc.)
        - refined_query: Refined/normalized query

    Examples:
        query="Turn on the living room lights"
        Returns:
        {
            "intent": "CONTROL",
            "confidence": 0.95,
            "entities": [
                {"entity_id": "light.living_room", "confidence": 0.92},
                {"entity_id": "light.salon_spot_01", "confidence": 0.85}
            ],
            "action": "on",
            "action_params": {},
            "parameters": {},
            "execution_plan": [
                {"entity": "light.living_room", "action": "on"},
                {"entity": "light.salon_spot_01", "action": "on"}
            ],
            "domain": "light",
            "refined_query": "turn on the living room lights"
        }

        query="Set kitchen temperature to 22 degrees"
        Returns:
        {
            "intent": "CONTROL",
            "confidence": 0.90,
            "entities": [
                {"entity_id": "climate.kitchen", "confidence": 0.95}
            ],
            "action": "set",
            "action_params": {"temperature": 22},
            "parameters": {"temperature": 22, "unit": "celsius"},
            "execution_plan": [
                {
                    "entity": "climate.kitchen",
                    "action": "set_temperature",
                    "parameters": {"temperature": 22}
                }
            ],
            "domain": "climate",
            "refined_query": "set kitchen temperature to 22 degrees"
        }
    """
    logger.info(f"Processing natural language query: '{query}'")

    if not query or not query.strip():
        return {
            "error": "Empty query provided",
            "intent": None,
            "confidence": 0.0,
            "entities": [],
            "action": None,
            "action_params": {},
            "parameters": {},
            "execution_plan": [],
            "domain": None,
            "refined_query": query,
        }

    try:
        # Process query using classification module
        classification_result = await process_query(query)

        # Extract classification results
        intent = classification_result.get("intent", "SEARCH")
        confidence = classification_result.get("confidence", 0.0)
        domain = classification_result.get("domain")
        action = classification_result.get("action")
        action_params = classification_result.get("action_params", {})
        parameters = classification_result.get("parameters", {})
        refined_query = classification_result.get("refined_query", query)
        entity_filters = classification_result.get("entity_filters", {})

        # Resolve entities using semantic search
        entities = await _resolve_entities(
            query=refined_query,
            domain=domain,
            entity_filters=entity_filters,
            intent=intent,
        )

        # Build execution plan
        execution_plan = await _build_execution_plan(
            entities=entities,
            action=action,
            action_params=action_params,
            parameters=parameters,
            intent=intent,
        )

        return {
            "intent": intent,
            "confidence": confidence,
            "entities": entities,
            "action": action,
            "action_params": action_params,
            "parameters": {**action_params, **parameters},
            "execution_plan": execution_plan,
            "domain": domain,
            "refined_query": refined_query,
        }

    except Exception as e:
        logger.error(f"Failed to process natural language query: {e}")
        return {
            "error": f"Failed to process query: {str(e)}",
            "intent": None,
            "confidence": 0.0,
            "entities": [],
            "action": None,
            "action_params": {},
            "parameters": {},
            "execution_plan": [],
            "domain": None,
            "refined_query": query,
        }


async def _resolve_entities(
    query: str,
    domain: str | None = None,
    entity_filters: dict[str, Any] | None = None,
    intent: str = "SEARCH",
    limit: int = 10,
) -> list[dict[str, Any]]:
    """
    Resolve entity references to actual entity IDs using semantic search.

    Args:
        query: Natural language query
        domain: Predicted domain filter
        entity_filters: Entity filters (area_id, etc.)
        intent: Query intent
        limit: Maximum number of entities to return

    Returns:
        List of resolved entities with confidence scores
    """
    if intent == "SEARCH":
        # For search queries, use semantic search to find entities
        try:
            area_id = entity_filters.get("area_id") if entity_filters else None
            semantic_results = await semantic_search(
                query=query,
                domain=domain,
                area_id=area_id,
                limit=limit,
                similarity_threshold=0.5,  # Lower threshold for entity resolution
            )

            entities = []
            for result in semantic_results:
                entity_id = result.get("entity_id")
                if not entity_id:
                    continue

                entities.append(
                    {
                        "entity_id": entity_id,
                        "confidence": round(result.get("similarity_score", 0.0), 3),
                        "match_reason": result.get("explanation", "Semantic match"),
                    }
                )

            return entities
        except Exception as e:
            logger.warning(f"Semantic search failed for entity resolution: {e}")
            return []

    # For control/status queries, also use semantic search
    try:
        area_id = entity_filters.get("area_id") if entity_filters else None
        semantic_results = await semantic_search(
            query=query,
            domain=domain,
            area_id=area_id,
            limit=limit,
            similarity_threshold=0.6,  # Higher threshold for control queries
        )

        entities = []
        for result in semantic_results:
            entity_id = result.get("entity_id")
            if not entity_id:
                continue

            entities.append(
                {
                    "entity_id": entity_id,
                    "confidence": round(result.get("similarity_score", 0.0), 3),
                    "match_reason": result.get("explanation", "Semantic match"),
                }
            )

        return entities
    except Exception as e:
        logger.warning(f"Semantic search failed for entity resolution: {e}")
        return []


async def _build_execution_plan(
    entities: list[dict[str, Any]],
    action: str | None = None,
    action_params: dict[str, Any] | None = None,
    parameters: dict[str, Any] | None = None,
    intent: str = "SEARCH",
) -> list[dict[str, Any]]:
    """
    Build execution plan from entities, action, and parameters.

    Args:
        entities: List of resolved entities
        action: Extracted action
        action_params: Action parameters
        parameters: Extracted parameters
        intent: Query intent

    Returns:
        List of execution plan steps
    """
    if intent == "SEARCH" or not entities:
        # For search queries, return empty execution plan
        return []

    execution_plan = []
    action_params = action_params or {}
    parameters = parameters or {}

    # Merge action_params and parameters
    merged_params = {**action_params, **parameters}

    for entity_info in entities:
        entity_id = entity_info.get("entity_id")
        if not entity_id:
            continue

        # Build execution step
        step = {
            "entity": entity_id,
            "action": action,
        }

        # Add parameters if available
        if merged_params:
            step["parameters"] = merged_params

        # Map action to service call for specific domains
        entity_domain = entity_id.split(".")[0]
        if entity_domain == "climate" and action == "set" and "temperature" in merged_params:
            step["action"] = "set_temperature"
            step["parameters"] = {"temperature": merged_params.get("temperature")}
        elif entity_domain == "light" and action == "on" and "brightness" in merged_params:
            step["parameters"] = {"brightness": merged_params.get("brightness")}
        elif entity_domain == "cover" and action in ["on", "off"]:
            step["action"] = "open" if action == "on" else "close"

        execution_plan.append(step)

    return execution_plan
