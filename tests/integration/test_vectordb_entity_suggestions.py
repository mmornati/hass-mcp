"""Integration tests for entity suggestions."""

import pytest

from app.api.entity_suggestions import get_entity_suggestions


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_entity_suggestions_by_area():
    """Test getting entity suggestions by area."""
    from app.api.entities import get_entities

    entities = await get_entities(lean=True)
    if not entities:
        pytest.skip("No entities available")

    # Get an entity with an area
    entity_with_area = next((e for e in entities if e.get("area_id")), None)
    if not entity_with_area:
        pytest.skip("No entities with areas available")

    entity_id = entity_with_area["entity_id"]
    area_id = entity_with_area["area_id"]

    # Get suggestions
    suggestions = await get_entity_suggestions(entity_id, relationship_types=["area"])

    assert isinstance(suggestions, list)
    # All suggestions should be in the same area
    for suggestion in suggestions:
        assert suggestion.get("area_id") == area_id


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_entity_suggestions_by_device():
    """Test getting entity suggestions by device."""
    from app.api.entities import get_entities

    entities = await get_entities(lean=True)
    if not entities:
        pytest.skip("No entities available")

    # Get an entity with a device
    entity_with_device = next((e for e in entities if e.get("device_id")), None)
    if not entity_with_device:
        pytest.skip("No entities with devices available")

    entity_id = entity_with_device["entity_id"]
    device_id = entity_with_device["device_id"]

    # Get suggestions
    suggestions = await get_entity_suggestions(entity_id, relationship_types=["device"])

    assert isinstance(suggestions, list)
    # All suggestions should be from the same device
    for suggestion in suggestions:
        assert suggestion.get("device_id") == device_id


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_entity_suggestions_by_domain():
    """Test getting entity suggestions by domain."""
    from app.api.entities import get_entities

    entities = await get_entities(lean=True)
    if not entities:
        pytest.skip("No entities available")

    entity_id = entities[0]["entity_id"]
    domain = entities[0]["domain"]

    # Get suggestions
    suggestions = await get_entity_suggestions(entity_id, relationship_types=["domain"])

    assert isinstance(suggestions, list)
    # All suggestions should be from the same domain
    for suggestion in suggestions:
        assert suggestion["domain"] == domain


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_entity_suggestions_multiple_types():
    """Test getting entity suggestions with multiple relationship types."""
    from app.api.entities import get_entities

    entities = await get_entities(lean=True)
    if not entities:
        pytest.skip("No entities available")

    entity_id = entities[0]["entity_id"]

    # Get suggestions with multiple relationship types
    suggestions = await get_entity_suggestions(
        entity_id, relationship_types=["area", "domain", "device"], limit=20
    )

    assert isinstance(suggestions, list)
    assert len(suggestions) <= 20
