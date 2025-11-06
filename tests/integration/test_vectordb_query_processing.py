"""Integration tests for query processing."""

import pytest

from app.core.vectordb.classification import (
    classify_intent,
    extract_action,
    extract_entities,
    extract_parameters,
    predict_domain,
    process_query,
    refine_query,
)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_classify_intent():
    """Test intent classification."""
    # Test various intents
    assert classify_intent("turn on the light") == "CONTROL"
    assert classify_intent("what is the temperature") == "STATUS"
    assert classify_intent("find lights") == "SEARCH"
    assert classify_intent("show me all sensors") == "DISCOVER"
    assert classify_intent("set temperature to 22") == "CONFIGURE"
    assert classify_intent("analyze energy usage") == "ANALYZE"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_predict_domain():
    """Test domain prediction."""
    assert predict_domain("turn on the light") == "light"
    assert predict_domain("what is the temperature") == "sensor"
    assert predict_domain("open the garage door") == "cover"
    assert predict_domain("set the thermostat") == "climate"
    assert predict_domain("play music") == "media_player"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_extract_action():
    """Test action extraction."""
    action = extract_action("turn on the light")
    assert action["action"] == "turn_on"
    assert action["confidence"] > 0.5

    action = extract_action("set temperature to 22 degrees")
    assert action["action"] == "set"
    assert "value" in action["params"]
    assert action["params"]["value"] == 22


@pytest.mark.integration
@pytest.mark.asyncio
async def test_extract_entities():
    """Test entity extraction."""
    entities = extract_entities("turn on light.living_room")
    assert "light.living_room" in entities["entity_ids"]

    entities = extract_entities("show me all lights in the living room")
    assert entities["filters"]["domain"] == "light"
    assert "living room" in entities["filters"].get("area", "").lower()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_extract_parameters():
    """Test parameter extraction."""
    params = extract_parameters("set temperature to 22 degrees")
    assert params["numeric_values"][0]["value"] == 22
    assert params["numeric_values"][0]["unit"] == "degrees"

    params = extract_parameters("set brightness to 50 percent")
    assert params["numeric_values"][0]["value"] == 50
    assert params["numeric_values"][0]["unit"] == "percent"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_refine_query():
    """Test query refinement."""
    refined = refine_query("turn on  the  light")
    assert "  " not in refined  # No double spaces

    refined = refine_query("turn on the lights")
    assert "light" in refined.lower()  # Synonym expansion


@pytest.mark.integration
@pytest.mark.asyncio
async def test_process_query_full():
    """Test full query processing pipeline."""
    result = await process_query("turn on the living room light")

    assert "intent" in result
    assert result["intent"] == "CONTROL"
    assert "domain" in result
    assert result["domain"] == "light"
    assert "action" in result
    assert result["action"]["action"] == "turn_on"
    assert "entities" in result
    assert "refined_query" in result
