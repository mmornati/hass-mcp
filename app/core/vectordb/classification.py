"""Query intent classification module for hass-mcp.

This module provides query intent classification, domain prediction, action extraction,
entity extraction, parameter extraction, and query refinement for natural language queries.
"""

import contextlib
import logging
import re
from typing import Any

from app.api.areas import get_areas
from app.core.vectordb.config import VectorDBConfig, get_vectordb_config
from app.core.vectordb.manager import VectorDBManager, get_vectordb_manager

logger = logging.getLogger(__name__)

# Intent classification patterns
INTENT_PATTERNS = {
    "SEARCH": [
        r"\b(find|search|show|list|get|what|which|where)\b",
        r"\b(all|every|any)\b",
        r"\b(are|is|exist)\b",
    ],
    "CONTROL": [
        r"\b(turn|switch|set|change|adjust|control|activate|deactivate)\b",
        r"\b(on|off|up|down|open|close)\b",
        r"\b(dim|brighten|increase|decrease|raise|lower)\b",
    ],
    "STATUS": [
        r"\b(what|how|status|state|current|check|is|are)\b",
        r"\b(temperature|brightness|level|value)\b",
        r"\b(on|off|active|inactive)\b",
    ],
    "CONFIGURE": [
        r"\b(configure|setup|set up|install|add|remove|delete|update|modify)\b",
        r"\b(settings|config|preferences)\b",
    ],
    "DISCOVER": [
        r"\b(discover|explore|find|show|what|other|similar|related)\b",
        r"\b(in|from|of|this|that|same)\b",
    ],
    "ANALYZE": [
        r"\b(analyze|analysis|report|statistics|stats|history|trend|pattern)\b",
        r"\b(usage|consumption|efficiency|performance)\b",
    ],
}

# Domain prediction patterns
DOMAIN_PATTERNS = {
    "light": [r"\b(light|lights|lamp|lamps|bulb|bulbs|illumination|brightness)\b"],
    "sensor": [
        r"\b(sensor|sensors|temperature|humidity|motion|presence|detector)\b",
        r"\b(reading|measurement|value|data)\b",
    ],
    "switch": [r"\b(switch|switches|toggle|outlet|outlets|plug|plugs)\b"],
    "climate": [
        r"\b(climate|thermostat|heating|cooling|ac|air conditioning|temperature control)\b",
    ],
    "cover": [r"\b(cover|covers|blind|blinds|curtain|curtains|shade|shades|garage)\b"],
    "fan": [r"\b(fan|fans|ventilation|vent)\b"],
    "lock": [r"\b(lock|locks|door lock|security)\b"],
    "media_player": [
        r"\b(media|player|music|audio|speaker|speakers|tv|television|stream)\b",
    ],
    "camera": [r"\b(camera|cameras|video|stream|feed)\b"],
    "alarm_control_panel": [r"\b(alarm|security|alert|siren)\b"],
}

# Action extraction patterns
ACTION_PATTERNS = {
    "on": [r"\b(turn on|switch on|activate|enable|open)\b"],
    "off": [r"\b(turn off|switch off|deactivate|disable|close)\b"],
    "set": [r"\b(set|set to|configure to|adjust to)\b"],
    "increase": [r"\b(increase|raise|up|higher|more|brighten|dim up)\b"],
    "decrease": [r"\b(decrease|lower|down|less|dim|dim down)\b"],
    "toggle": [r"\b(toggle|switch|flip)\b"],
}

# Attribute extraction patterns
ATTRIBUTE_PATTERNS = {
    "brightness": [r"\b(brightness|bright|dim|illumination)\b"],
    "color": [r"\b(color|colour|hue|rgb)\b"],
    "color_temp": [r"\b(color temperature|color temp|colour temperature|kelvin|k)\b"],
    "temperature": [r"\b(temperature|temp|heat|cool)\b"],
    "humidity": [r"\b(humidity|moisture)\b"],
    "position": [r"\b(position|level|open|closed)\b"],
}


async def classify_intent(query: str) -> tuple[str, float]:
    """
    Classify query intent.

    Args:
        query: Natural language query

    Returns:
        Tuple of (intent, confidence) where intent is one of:
        SEARCH, CONTROL, STATUS, CONFIGURE, DISCOVER, ANALYZE
    """
    query_lower = query.lower()
    intent_scores: dict[str, float] = {}

    # Score each intent based on pattern matches
    for intent, patterns in INTENT_PATTERNS.items():
        score = 0.0
        for pattern in patterns:
            matches = len(re.findall(pattern, query_lower, re.IGNORECASE))
            score += matches * 0.3  # Weight each match

        # Boost score for multiple matches
        if score > 0:
            intent_scores[intent] = score

    # If no intent found, default to SEARCH
    if not intent_scores:
        return ("SEARCH", 0.5)

    # Get the highest scoring intent
    best_intent = max(intent_scores.items(), key=lambda x: x[1])[0]
    best_score = intent_scores[best_intent]

    # Normalize confidence to 0.0-1.0 range
    confidence = min(1.0, best_score / 2.0)
    confidence = max(confidence, 0.5)  # Minimum confidence

    return (best_intent, confidence)


async def predict_domain(query: str) -> tuple[str | None, float]:
    """
    Predict entity domain from natural language query.

    Args:
        query: Natural language query

    Returns:
        Tuple of (domain, confidence) where domain is one of:
        light, sensor, switch, climate, cover, fan, lock, media_player, camera, etc.
    """
    query_lower = query.lower()
    domain_scores: dict[str, float] = {}

    # Score each domain based on pattern matches
    # Check climate first (more specific) before sensor (more general)
    domain_order = [
        "climate",
        "sensor",
        "light",
        "switch",
        "cover",
        "fan",
        "lock",
        "media_player",
        "camera",
        "alarm_control_panel",
    ]
    for domain in domain_order:
        if domain not in DOMAIN_PATTERNS:
            continue
        patterns = DOMAIN_PATTERNS[domain]
        score = 0.0
        for pattern in patterns:
            matches = len(re.findall(pattern, query_lower, re.IGNORECASE))
            score += matches * 0.4  # Weight each match

        if score > 0:
            domain_scores[domain] = score

    # If no domain found, return None
    if not domain_scores:
        return (None, 0.0)

    # Get the highest scoring domain
    best_domain = max(domain_scores.items(), key=lambda x: x[1])[0]
    best_score = domain_scores[best_domain]

    # Normalize confidence to 0.0-1.0 range
    confidence = min(1.0, best_score / 2.0)

    return (best_domain, confidence)


async def extract_action(query: str) -> tuple[str | None, dict[str, Any]]:
    """
    Extract action and action parameters from query.

    Args:
        query: Natural language query

    Returns:
        Tuple of (action, parameters) where:
        - action: One of "on", "off", "set", "increase", "decrease", "toggle", or None
        - parameters: Dictionary with action-specific parameters
    """
    query_lower = query.lower()
    action_params: dict[str, Any] = {}

    # Check each action pattern
    for action, patterns in ACTION_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, query_lower, re.IGNORECASE):
                # Extract numeric value if present
                value_match = re.search(r"\b(\d+)\b", query)
                if value_match:
                    with contextlib.suppress(ValueError):
                        action_params["value"] = int(value_match.group(1))

                # Extract percentage if present
                percent_match = re.search(r"(\d+)%", query)
                if percent_match:
                    with contextlib.suppress(ValueError):
                        action_params["value"] = int(percent_match.group(1))
                        action_params["unit"] = "percent"

                # Extract attribute if present
                for attr_name, attr_patterns in ATTRIBUTE_PATTERNS.items():
                    for attr_pattern in attr_patterns:
                        if re.search(attr_pattern, query_lower, re.IGNORECASE):
                            action_params["attribute"] = attr_name
                            break

                return (action, action_params)

    return (None, {})


async def extract_entities(
    query: str, manager: VectorDBManager | None = None, config: VectorDBConfig | None = None
) -> tuple[list[str], dict[str, Any]]:
    """
    Extract entity references and filters from query.

    Args:
        query: Natural language query
        manager: Optional VectorDBManager instance
        config: Optional VectorDBConfig instance

    Returns:
        Tuple of (entity_ids, filters) where:
        - entity_ids: List of explicit entity IDs found in query
        - filters: Dictionary with entity filters (area, domain, type, etc.)
    """
    entity_ids: list[str] = []
    filters: dict[str, Any] = {}

    # Extract explicit entity IDs (format: domain.entity_id)
    # Match domain.entity_id pattern (e.g., "light.living_room")
    entity_id_pattern = r"\b([a-z_]+)\.([a-z0-9_]+)\b"
    entity_matches = re.findall(entity_id_pattern, query, re.IGNORECASE)
    for domain, entity_name in entity_matches:
        entity_id = f"{domain}.{entity_name}"
        entity_ids.append(entity_id)

    # Extract area/room names
    try:
        areas = await get_areas()
        area_names: list[str] = []
        for area in areas:
            if isinstance(area, dict):
                area_name = area.get("name", "").lower()
                area_id = area.get("area_id", "")
                if area_name and area_name in query.lower():
                    area_names.append(area_id)
                    filters["area_id"] = area_id
                # Check aliases
                aliases = area.get("aliases", [])
                for alias in aliases:
                    if isinstance(alias, str) and alias.lower() in query.lower():
                        area_names.append(area_id)
                        filters["area_id"] = area_id
                        break
    except Exception as e:
        logger.debug(f"Failed to get areas for entity extraction: {e}")

    # Extract domain from query (already predicted, but also check here)
    domain, _ = await predict_domain(query)
    if domain:
        filters["domain"] = domain

    # Extract entity type hints (temperature, motion, etc.)
    type_hints = {
        "temperature": ["temperature", "temp", "heat", "cool"],
        "motion": ["motion", "movement", "presence"],
        "humidity": ["humidity", "moisture"],
        "brightness": ["brightness", "light level"],
    }

    for type_name, keywords in type_hints.items():
        for keyword in keywords:
            if keyword in query.lower():
                filters["type"] = type_name
                break

    return (entity_ids, filters)


async def extract_parameters(query: str) -> dict[str, Any]:
    """
    Extract numeric values, attribute names, and other parameters from query.

    Args:
        query: Natural language query

    Returns:
        Dictionary with extracted parameters:
        - value: Numeric value if found
        - unit: Unit of measurement if found
        - attribute: Attribute name if found
        - area: Area/room name if found
        - time: Time reference if found
    """
    parameters: dict[str, Any] = {}

    # Extract numeric values (check float first, then integer, then percentage)
    # Check for percentage first (most specific)
    percent_match = re.search(r"(\d+)%", query)
    if percent_match:
        with contextlib.suppress(ValueError, IndexError):
            parameters["value"] = int(percent_match.group(1))
            parameters["unit"] = "percent"
    else:
        # Check for float (more specific than integer)
        float_match = re.search(r"\b(\d+\.\d+)\b", query)
        if float_match:
            with contextlib.suppress(ValueError, IndexError):
                parameters["value"] = float(float_match.group(1))
        else:
            # Check for integer
            int_match = re.search(r"\b(\d+)\b", query)
            if int_match:
                with contextlib.suppress(ValueError, IndexError):
                    parameters["value"] = int(int_match.group(1))

    # Extract attribute names
    query_lower = query.lower()
    for attr_name, attr_patterns in ATTRIBUTE_PATTERNS.items():
        for attr_pattern in attr_patterns:
            if re.search(attr_pattern, query_lower, re.IGNORECASE):
                parameters["attribute"] = attr_name
                break

    # Extract time references
    time_patterns = [
        r"\b(\d+)\s*(minute|minutes|hour|hours|day|days|week|weeks)\b",
        r"\b(today|yesterday|now|recent|last)\b",
    ]

    for pattern in time_patterns:
        match = re.search(pattern, query_lower, re.IGNORECASE)
        if match:
            parameters["time"] = match.group(0)
            break

    return parameters


async def refine_query(query: str) -> str:
    """
    Refine query by expanding synonyms, correcting spelling, and normalizing text.

    Args:
        query: Original query

    Returns:
        Refined query string
    """
    refined = query.strip()

    # Common synonym expansions (only for phrases, not plurals)
    # Don't expand plurals to singulars as it changes meaning
    synonym_phrases = {
        "switch on": "turn on",
        "activate": "turn on",
        "deactivate": "turn off",
        "adjust temperature": "set temperature",
    }

    # Apply synonym phrase expansions
    for old_phrase, new_phrase in synonym_phrases.items():
        if old_phrase in refined.lower():
            refined = refined.replace(old_phrase, new_phrase)
            refined = refined.replace(old_phrase.capitalize(), new_phrase.capitalize())

    # Normalize whitespace
    refined = re.sub(r"\s+", " ", refined)

    return refined


async def process_query(
    query: str,
    manager: VectorDBManager | None = None,
    config: VectorDBConfig | None = None,
) -> dict[str, Any]:
    """
    Process natural language query to extract intent and parameters.

    This is the main entry point for query classification. It performs:
    1. Intent classification
    2. Domain prediction
    3. Action extraction
    4. Entity extraction
    5. Parameter extraction
    6. Query refinement

    Args:
        query: Natural language query
        manager: Optional VectorDBManager instance
        config: Optional VectorDBConfig instance

    Returns:
        Dictionary with classification results:
        - intent: Query intent (SEARCH, CONTROL, STATUS, etc.)
        - confidence: Confidence score (0.0-1.0)
        - domain: Predicted domain (light, sensor, etc.) or None
        - domain_confidence: Domain prediction confidence (0.0-1.0)
        - action: Extracted action (on, off, set, etc.) or None
        - action_params: Action-specific parameters
        - entities: List of explicit entity IDs found
        - entity_filters: Dictionary with entity filters (area, domain, type)
        - parameters: Dictionary with extracted parameters (value, unit, attribute, etc.)
        - refined_query: Refined query string

    Example:
        >>> result = await process_query("turn on the living room lights")
        >>> result["intent"]  # "CONTROL"
        >>> result["action"]  # "on"
        >>> result["entity_filters"]["area_id"]  # "living_room"
    """
    manager = manager or get_vectordb_manager()
    config = config or get_vectordb_config()

    # 1. Intent classification
    intent, intent_confidence = await classify_intent(query)

    # 2. Domain prediction
    domain, domain_confidence = await predict_domain(query)

    # 3. Action extraction
    action, action_params = await extract_action(query)

    # 4. Entity extraction
    entities, entity_filters = await extract_entities(query, manager, config)

    # 5. Parameter extraction
    parameters = await extract_parameters(query)

    # 6. Query refinement
    refined_query = await refine_query(query)

    return {
        "intent": intent,
        "confidence": intent_confidence,
        "domain": domain,
        "domain_confidence": domain_confidence,
        "action": action,
        "action_params": action_params,
        "entities": entities,
        "entity_filters": entity_filters,
        "parameters": parameters,
        "refined_query": refined_query,
    }
