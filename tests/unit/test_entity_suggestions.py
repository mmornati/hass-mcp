"""Unit tests for app.api.entity_suggestions module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api.entity_suggestions import (
    _build_suggestion_explanation,
    _find_entities_by_area,
    _find_entities_by_device,
    _find_entities_by_domain,
    _find_entities_by_similar_name,
    _find_entities_by_vector_similarity,
    _rank_and_deduplicate,
    get_entity_suggestions,
)


class TestFindEntitiesByArea:
    """Test _find_entities_by_area function."""

    @pytest.mark.asyncio
    async def test_find_entities_same_area(self):
        """Test finding entities in the same area."""
        mock_entities = [
            {
                "entity_id": "light.living_room_1",
                "attributes": {"area_id": "living_room", "friendly_name": "Light 1"},
            },
            {
                "entity_id": "light.living_room_2",
                "attributes": {"area_id": "living_room", "friendly_name": "Light 2"},
            },
            {
                "entity_id": "light.kitchen",
                "attributes": {"area_id": "kitchen", "friendly_name": "Kitchen Light"},
            },
        ]

        with patch("app.api.entity_suggestions.get_entities", return_value=mock_entities):
            results = await _find_entities_by_area("living_room", "light.living_room_1")

            assert len(results) == 1
            assert results[0]["entity_id"] == "light.living_room_2"
            assert results[0]["relationship_type"] == "same_area"
            assert results[0]["relationship_score"] == 1.0

    @pytest.mark.asyncio
    async def test_find_entities_no_area(self):
        """Test finding entities with no area."""
        results = await _find_entities_by_area(None, "light.test")
        assert results == []

    @pytest.mark.asyncio
    async def test_find_entities_empty_result(self):
        """Test finding entities when no matches."""
        mock_entities = [
            {
                "entity_id": "light.kitchen",
                "attributes": {"area_id": "kitchen", "friendly_name": "Kitchen Light"},
            },
        ]

        with patch("app.api.entity_suggestions.get_entities", return_value=mock_entities):
            results = await _find_entities_by_area("living_room", "light.test")
            assert results == []


class TestFindEntitiesByDevice:
    """Test _find_entities_by_device function."""

    @pytest.mark.asyncio
    async def test_find_entities_same_device(self):
        """Test finding entities from the same device."""
        mock_device = {
            "id": "device_123",
            "entities": ["light.bulb_1", "light.bulb_2", "light.bulb_3"],
        }

        mock_entity_1 = {
            "entity_id": "light.bulb_2",
            "attributes": {"friendly_name": "Bulb 2"},
        }
        mock_entity_2 = {
            "entity_id": "light.bulb_3",
            "attributes": {"friendly_name": "Bulb 3"},
        }

        with (
            patch("app.api.entity_suggestions.get_device_details", return_value=mock_device),
            patch(
                "app.api.entity_suggestions.get_entity_state",
                side_effect=[mock_entity_1, mock_entity_2],
            ),
        ):
            results = await _find_entities_by_device("device_123", "light.bulb_1")

            assert len(results) == 2
            assert results[0]["entity_id"] == "light.bulb_2"
            assert results[1]["entity_id"] == "light.bulb_3"
            assert all(r["relationship_type"] == "same_device" for r in results)

    @pytest.mark.asyncio
    async def test_find_entities_no_device(self):
        """Test finding entities with no device."""
        results = await _find_entities_by_device(None, "light.test")
        assert results == []


class TestFindEntitiesByDomain:
    """Test _find_entities_by_domain function."""

    @pytest.mark.asyncio
    async def test_find_entities_same_domain(self):
        """Test finding entities of the same domain."""
        mock_entities = [
            {"entity_id": "light.living_room", "attributes": {"friendly_name": "Living Room"}},
            {"entity_id": "light.kitchen", "attributes": {"friendly_name": "Kitchen"}},
            {"entity_id": "light.bedroom", "attributes": {"friendly_name": "Bedroom"}},
        ]

        with patch("app.api.entity_suggestions.get_entities", return_value=mock_entities):
            results = await _find_entities_by_domain("light", "light.living_room", limit=10)

            assert len(results) == 2
            assert all(r["relationship_type"] == "same_domain" for r in results)
            assert all(r["relationship_score"] == 0.8 for r in results)

    @pytest.mark.asyncio
    async def test_find_entities_no_domain(self):
        """Test finding entities with no domain."""
        results = await _find_entities_by_domain(None, "light.test")
        assert results == []


class TestFindEntitiesBySimilarName:
    """Test _find_entities_by_similar_name function."""

    @pytest.mark.asyncio
    async def test_find_entities_similar_name(self):
        """Test finding entities with similar names."""
        mock_entities = [
            {
                "entity_id": "light.living_room_main",
                "attributes": {"friendly_name": "Living Room Main Light"},
            },
            {
                "entity_id": "light.living_room_spot",
                "attributes": {"friendly_name": "Living Room Spot Light"},
            },
            {
                "entity_id": "light.kitchen",
                "attributes": {"friendly_name": "Kitchen Light"},
            },
        ]

        with patch("app.api.entity_suggestions.get_entities", return_value=mock_entities):
            results = await _find_entities_by_similar_name(
                "light.living_room", "Living Room Light", limit=10
            )

            assert len(results) > 0
            assert results[0]["relationship_type"] == "similar_name"
            # Should find entities with "Living Room" in the name
            assert "living_room" in results[0]["entity_id"]

    @pytest.mark.asyncio
    async def test_find_entities_no_friendly_name(self):
        """Test finding entities with no friendly name."""
        results = await _find_entities_by_similar_name("light.test", None, limit=10)
        assert results == []


class TestFindEntitiesByVectorSimilarity:
    """Test _find_entities_by_vector_similarity function."""

    @pytest.mark.asyncio
    async def test_find_entities_vector_similarity(self):
        """Test finding entities using vector similarity."""
        mock_entity = {
            "entity_id": "light.living_room",
            "attributes": {"friendly_name": "Living Room Light"},
        }

        mock_similar_entity = {
            "entity_id": "light.kitchen",
            "attributes": {"friendly_name": "Kitchen Light"},
        }

        mock_manager = AsyncMock()
        mock_manager._initialized = True
        mock_manager.search_vectors = AsyncMock(
            return_value=[
                {"id": "light.living_room", "distance": 0.0},  # Should be excluded
                {"id": "light.kitchen", "distance": 0.2},
            ]
        )

        mock_config = MagicMock()
        mock_config.is_enabled = MagicMock(return_value=True)

        with (
            patch("app.api.entity_suggestions.get_vectordb_config", return_value=mock_config),
            patch("app.api.entity_suggestions.get_vectordb_manager", return_value=mock_manager),
            patch(
                "app.api.entity_suggestions.get_entity_state",
                side_effect=[mock_entity, mock_similar_entity],
            ),
        ):
            results = await _find_entities_by_vector_similarity("light.living_room", limit=10)

            assert len(results) == 1
            assert results[0]["entity_id"] == "light.kitchen"
            assert results[0]["relationship_type"] == "similar_capabilities"

    @pytest.mark.asyncio
    async def test_find_entities_vector_disabled(self):
        """Test finding entities when vector DB is disabled."""
        mock_config = MagicMock()
        mock_config.is_enabled = MagicMock(return_value=False)

        with patch("app.api.entity_suggestions.get_vectordb_config", return_value=mock_config):
            results = await _find_entities_by_vector_similarity("light.test", limit=10)
            assert results == []


class TestRankAndDeduplicate:
    """Test _rank_and_deduplicate function."""

    def test_rank_and_deduplicate(self):
        """Test ranking and deduplication."""
        suggestions = [
            {
                "entity_id": "light.1",
                "relationship_score": 0.8,
                "relationship_type": "same_area",
            },
            {
                "entity_id": "light.2",
                "relationship_score": 0.9,
                "relationship_type": "same_device",
            },
            {
                "entity_id": "light.1",
                "relationship_score": 0.7,
                "relationship_type": "same_domain",
            },  # Duplicate
            {
                "entity_id": "light.3",
                "relationship_score": 0.95,
                "relationship_type": "similar_name",
            },
        ]

        results = _rank_and_deduplicate(suggestions, limit=10)

        # Should have 3 unique entities
        assert len(results) == 3
        # Should be sorted by score (descending)
        assert results[0]["entity_id"] == "light.3"  # 0.95
        assert results[1]["entity_id"] == "light.2"  # 0.9
        assert results[2]["entity_id"] == "light.1"  # 0.8 (higher of duplicates)

    def test_rank_with_limit(self):
        """Test ranking with limit."""
        suggestions = [
            {"entity_id": f"light.{i}", "relationship_score": 1.0 - (i * 0.1)}
            for i in range(10)
        ]

        results = _rank_and_deduplicate(suggestions, limit=3)
        assert len(results) == 3


class TestBuildSuggestionExplanation:
    """Test _build_suggestion_explanation function."""

    def test_explanation_same_area(self):
        """Test explanation for same_area relationship."""
        suggestion = {
            "entity_id": "light.kitchen",
            "entity": {
                "entity_id": "light.kitchen",
                "attributes": {"friendly_name": "Kitchen Light"},
            },
            "relationship_type": "same_area",
            "relationship_score": 1.0,
            "metadata": {"area_id": "kitchen"},
        }

        explanation = _build_suggestion_explanation(suggestion)
        assert "Kitchen Light" in explanation
        assert "light" in explanation
        assert "same area" in explanation
        assert "kitchen" in explanation

    def test_explanation_same_device(self):
        """Test explanation for same_device relationship."""
        suggestion = {
            "entity_id": "light.bulb_2",
            "entity": {
                "entity_id": "light.bulb_2",
                "attributes": {"friendly_name": "Bulb 2"},
            },
            "relationship_type": "same_device",
            "relationship_score": 1.0,
            "metadata": {},
        }

        explanation = _build_suggestion_explanation(suggestion)
        assert "Bulb 2" in explanation
        assert "same device" in explanation

    def test_explanation_similar_capabilities(self):
        """Test explanation for similar_capabilities relationship."""
        suggestion = {
            "entity_id": "sensor.temp_2",
            "entity": {
                "entity_id": "sensor.temp_2",
                "attributes": {"friendly_name": "Temperature 2"},
            },
            "relationship_type": "similar_capabilities",
            "relationship_score": 0.85,
            "metadata": {"vector_similarity": 0.85},
        }

        explanation = _build_suggestion_explanation(suggestion)
        assert "Temperature 2" in explanation
        assert "similar capabilities" in explanation
        assert "85" in explanation  # Similarity percentage


class TestGetEntitySuggestions:
    """Test get_entity_suggestions function."""

    @pytest.mark.asyncio
    async def test_get_suggestions_all_types(self):
        """Test getting suggestions with all relationship types."""
        mock_entity = {
            "entity_id": "light.living_room",
            "attributes": {
                "friendly_name": "Living Room Light",
                "area_id": "living_room",
                "device_id": "device_123",
            },
        }

        mock_area_entity = {
            "entity_id": "sensor.living_room_temp",
            "attributes": {
                "friendly_name": "Living Room Temperature",
                "area_id": "living_room",
            },
        }

        with (
            patch("app.core.decorators.HA_TOKEN", "fake_token"),
            patch(
                "app.api.entity_suggestions.get_entity_state",
                AsyncMock(return_value=mock_entity),
            ),
            patch(
                "app.api.entity_suggestions._find_entities_by_area",
                return_value=[
                    {
                        "entity_id": "sensor.living_room_temp",
                        "entity": mock_area_entity,
                        "relationship_type": "same_area",
                        "relationship_score": 1.0,
                        "metadata": {},
                    }
                ],
            ),
            patch("app.api.entity_suggestions._find_entities_by_device", return_value=[]),
            patch("app.api.entity_suggestions._find_entities_by_domain", return_value=[]),
            patch("app.api.entity_suggestions._find_entities_by_similar_name", return_value=[]),
            patch(
                "app.api.entity_suggestions._find_entities_by_vector_similarity", return_value=[]
            ),
        ):
            results = await get_entity_suggestions("light.living_room")

            assert len(results) > 0
            assert "explanation" in results[0]
            assert results[0]["entity_id"] == "sensor.living_room_temp"

    @pytest.mark.asyncio
    async def test_get_suggestions_specific_types(self):
        """Test getting suggestions with specific relationship types."""
        mock_entity = {
            "entity_id": "light.living_room",
            "attributes": {
                "friendly_name": "Living Room Light",
                "area_id": "living_room",
            },
        }

        with (
            patch("app.core.decorators.HA_TOKEN", "fake_token"),
            patch("app.api.entity_suggestions.get_entity_state", AsyncMock(return_value=mock_entity)),
            patch("app.api.entity_suggestions._find_entities_by_area", return_value=[]) as mock_area,
            patch("app.api.entity_suggestions._find_entities_by_device") as mock_device,
            patch("app.api.entity_suggestions._find_entities_by_domain") as mock_domain,
        ):
            await get_entity_suggestions(
                "light.living_room", relationship_types=["same_area"], limit=5
            )

            # Should only call _find_entities_by_area
            mock_area.assert_called_once()
            mock_device.assert_not_called()
            mock_domain.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_suggestions_entity_not_found(self):
        """Test getting suggestions for non-existent entity."""
        with patch(
            "app.api.entity_suggestions.get_entity_state", return_value={"error": "Not found"}
        ):
            results = await get_entity_suggestions("light.nonexistent")

            assert isinstance(results, list)
            assert len(results) == 1
            assert "error" in results[0]

    @pytest.mark.asyncio
    async def test_get_suggestions_limit(self):
        """Test getting suggestions with limit."""
        mock_entity = {
            "entity_id": "light.test",
            "attributes": {"friendly_name": "Test"},
        }

        mock_suggestions = [
            {
                "entity_id": f"light.{i}",
                "entity": {"entity_id": f"light.{i}", "attributes": {}},
                "relationship_type": "same_domain",
                "relationship_score": 1.0 - (i * 0.1),
                "metadata": {},
            }
            for i in range(20)
        ]

        with (
            patch("app.api.entity_suggestions.get_entity_state", return_value=mock_entity),
            patch(
                "app.api.entity_suggestions._find_entities_by_domain",
                return_value=mock_suggestions,
            ),
            patch("app.api.entity_suggestions._find_entities_by_area", return_value=[]),
            patch("app.api.entity_suggestions._find_entities_by_device", return_value=[]),
            patch("app.api.entity_suggestions._find_entities_by_similar_name", return_value=[]),
            patch(
                "app.api.entity_suggestions._find_entities_by_vector_similarity", return_value=[]
            ),
        ):
            results = await get_entity_suggestions("light.test", limit=5)

            # Should respect limit
            assert len(results) <= 5
