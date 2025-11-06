"""Unit tests for app.tools.entities.semantic_search_entities_tool module."""

from unittest.mock import AsyncMock, patch

import pytest

from app.tools.entities import semantic_search_entities_tool


class TestSemanticSearchEntitiesTool:
    """Test the semantic_search_entities_tool function."""

    @pytest.fixture
    def mock_semantic_search(self):
        """Create a mock semantic_search function."""
        return AsyncMock(
            return_value=[
                {
                    "entity_id": "light.living_room",
                    "similarity_score": 0.95,
                    "entity": {
                        "entity_id": "light.living_room",
                        "state": "on",
                        "attributes": {"friendly_name": "Living Room Light"},
                    },
                    "explanation": "Entity 'Living Room Light' (light) matched with 95% similarity",
                    "metadata": {"domain": "light", "area_id": "living_room"},
                },
                {
                    "entity_id": "light.kitchen",
                    "similarity_score": 0.85,
                    "entity": {
                        "entity_id": "light.kitchen",
                        "state": "off",
                        "attributes": {"friendly_name": "Kitchen Light"},
                    },
                    "explanation": "Entity 'Kitchen Light' (light) matched with 85% similarity",
                    "metadata": {"domain": "light", "area_id": "kitchen"},
                },
            ]
        )

    @pytest.fixture
    def mock_get_entities(self):
        """Create a mock get_entities function."""
        return AsyncMock(
            return_value=[
                {
                    "entity_id": "light.living_room",
                    "state": "on",
                    "attributes": {"friendly_name": "Living Room Light"},
                },
                {
                    "entity_id": "light.kitchen",
                    "state": "off",
                    "attributes": {"friendly_name": "Kitchen Light"},
                },
            ]
        )

    @pytest.mark.asyncio
    async def test_semantic_search_hybrid_mode(self, mock_semantic_search, mock_get_entities):
        """Test semantic search in hybrid mode."""
        with (
            patch("app.tools.entities.semantic_search", mock_semantic_search),
            patch("app.tools.entities.get_entities", mock_get_entities),
        ):
            result = await semantic_search_entities_tool(
                query="living room lights", search_mode="hybrid"
            )

            assert result["query"] == "living room lights"
            assert result["search_mode"] == "hybrid"
            assert result["count"] > 0
            assert "results" in result
            assert "domains" in result
            assert len(result["results"]) > 0
            assert "similarity" in result["results"][0]
            assert "match_reason" in result["results"][0]

    @pytest.mark.asyncio
    async def test_semantic_search_semantic_mode(self, mock_semantic_search, mock_get_entities):
        """Test semantic search in semantic-only mode."""
        with (
            patch("app.tools.entities.semantic_search", mock_semantic_search),
            patch("app.tools.entities.get_entities", mock_get_entities),
        ):
            result = await semantic_search_entities_tool(
                query="living room lights", search_mode="semantic"
            )

            assert result["query"] == "living room lights"
            assert result["search_mode"] == "semantic"
            assert result["count"] > 0
            assert "results" in result

    @pytest.mark.asyncio
    async def test_semantic_search_keyword_mode(self, mock_semantic_search, mock_get_entities):
        """Test semantic search in keyword-only mode."""
        with (
            patch("app.tools.entities.semantic_search", mock_semantic_search),
            patch("app.tools.entities.get_entities", mock_get_entities),
        ):
            result = await semantic_search_entities_tool(
                query="living room lights", search_mode="keyword"
            )

            assert result["query"] == "living room lights"
            assert result["search_mode"] == "keyword"
            assert result["count"] > 0
            assert "results" in result

    @pytest.mark.asyncio
    async def test_semantic_search_with_domain_filter(
        self, mock_semantic_search, mock_get_entities
    ):
        """Test semantic search with domain filter."""
        with (
            patch("app.tools.entities.semantic_search", mock_semantic_search),
            patch("app.tools.entities.get_entities", mock_get_entities),
        ):
            result = await semantic_search_entities_tool(
                query="lights", domain="light", search_mode="hybrid"
            )

            assert result["query"] == "lights"
            assert "light" in result.get("domains", {})
            assert result["count"] > 0

    @pytest.mark.asyncio
    async def test_semantic_search_with_area_filter(self, mock_semantic_search, mock_get_entities):
        """Test semantic search with area filter."""
        with (
            patch("app.tools.entities.semantic_search", mock_semantic_search),
            patch("app.tools.entities.get_entities", mock_get_entities),
        ):
            result = await semantic_search_entities_tool(
                query="lights", area_id="living_room", search_mode="hybrid"
            )

            assert result["query"] == "lights"
            assert result["count"] > 0

    @pytest.mark.asyncio
    async def test_semantic_search_with_similarity_threshold(
        self, mock_semantic_search, mock_get_entities
    ):
        """Test semantic search with similarity threshold."""
        with (
            patch("app.tools.entities.semantic_search", mock_semantic_search),
            patch("app.tools.entities.get_entities", mock_get_entities),
        ):
            result = await semantic_search_entities_tool(
                query="lights", similarity_threshold=0.9, search_mode="hybrid"
            )

            assert result["query"] == "lights"
            assert result["count"] >= 0  # May be 0 if threshold too high

    @pytest.mark.asyncio
    async def test_semantic_search_empty_query(self, mock_semantic_search, mock_get_entities):
        """Test semantic search with empty query."""
        with (
            patch("app.tools.entities.semantic_search", mock_semantic_search),
            patch("app.tools.entities.get_entities", mock_get_entities),
        ):
            result = await semantic_search_entities_tool(query="", search_mode="hybrid")

            assert result["query"] == ""
            assert result["search_mode"] == "keyword"  # Falls back to keyword
            assert result["count"] >= 0

    @pytest.mark.asyncio
    async def test_semantic_search_invalid_mode(self, mock_semantic_search, mock_get_entities):
        """Test semantic search with invalid search mode."""
        with (
            patch("app.tools.entities.semantic_search", mock_semantic_search),
            patch("app.tools.entities.get_entities", mock_get_entities),
        ):
            result = await semantic_search_entities_tool(query="lights", search_mode="invalid")

            assert "error" in result
            assert result["count"] == 0
            assert result["search_mode"] == "invalid"

    @pytest.mark.asyncio
    async def test_semantic_search_error_fallback(self, mock_semantic_search, mock_get_entities):
        """Test semantic search error fallback to keyword search."""
        mock_semantic_search.side_effect = Exception("Semantic search failed")

        with (
            patch("app.tools.entities.semantic_search", mock_semantic_search),
            patch("app.tools.entities.get_entities", mock_get_entities),
        ):
            result = await semantic_search_entities_tool(query="lights", search_mode="hybrid")

            assert result["search_mode"] == "keyword"  # Falls back to keyword
            assert result["count"] >= 0

    @pytest.mark.asyncio
    async def test_semantic_search_result_format(self, mock_semantic_search, mock_get_entities):
        """Test semantic search result format."""
        with (
            patch("app.tools.entities.semantic_search", mock_semantic_search),
            patch("app.tools.entities.get_entities", mock_get_entities),
        ):
            result = await semantic_search_entities_tool(
                query="living room lights", search_mode="hybrid"
            )

            assert "query" in result
            assert "count" in result
            assert "results" in result
            assert "search_mode" in result
            assert "domains" in result

            if result["count"] > 0:
                first_result = result["results"][0]
                assert "entity_id" in first_result
                assert "state" in first_result
                assert "domain" in first_result
                assert "friendly_name" in first_result
                assert "similarity" in first_result
                assert "match_reason" in first_result

    @pytest.mark.asyncio
    async def test_semantic_search_with_limit(self, mock_semantic_search, mock_get_entities):
        """Test semantic search with limit."""
        with (
            patch("app.tools.entities.semantic_search", mock_semantic_search),
            patch("app.tools.entities.get_entities", mock_get_entities),
        ):
            result = await semantic_search_entities_tool(
                query="lights", limit=5, search_mode="hybrid"
            )

            assert result["count"] <= 5
            assert len(result["results"]) <= 5

    @pytest.mark.asyncio
    async def test_semantic_search_domains_count(self, mock_semantic_search, mock_get_entities):
        """Test semantic search domains count."""
        with (
            patch("app.tools.entities.semantic_search", mock_semantic_search),
            patch("app.tools.entities.get_entities", mock_get_entities),
        ):
            result = await semantic_search_entities_tool(query="lights", search_mode="hybrid")

            assert "domains" in result
            assert isinstance(result["domains"], dict)
