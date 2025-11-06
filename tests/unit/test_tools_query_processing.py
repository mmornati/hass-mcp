"""Unit tests for app.tools.query_processing module."""

from unittest.mock import AsyncMock, patch

import pytest

from app.tools.query_processing import process_natural_language_query


class TestProcessNaturalLanguageQuery:
    """Test the process_natural_language_query function."""

    @pytest.fixture
    def mock_process_query(self):
        """Create a mock process_query function."""
        return AsyncMock(
            return_value={
                "intent": "CONTROL",
                "confidence": 0.95,
                "domain": "light",
                "domain_confidence": 0.90,
                "action": "on",
                "action_params": {},
                "entities": [],
                "entity_filters": {"area_id": "living_room"},
                "parameters": {},
                "refined_query": "turn on the living room lights",
            }
        )

    @pytest.fixture
    def mock_semantic_search(self):
        """Create a mock semantic_search function."""
        return AsyncMock(
            return_value=[
                {
                    "entity_id": "light.living_room",
                    "similarity_score": 0.92,
                    "entity": {
                        "entity_id": "light.living_room",
                        "state": "off",
                        "attributes": {"friendly_name": "Living Room Light"},
                    },
                    "explanation": "Entity 'Living Room Light' (light) matched with 92% similarity",
                    "metadata": {"domain": "light", "area_id": "living_room"},
                },
                {
                    "entity_id": "light.salon_spot_01",
                    "similarity_score": 0.85,
                    "entity": {
                        "entity_id": "light.salon_spot_01",
                        "state": "off",
                        "attributes": {"friendly_name": "Living Room Spot"},
                    },
                    "explanation": "Entity 'Living Room Spot' (light) matched with 85% similarity",
                    "metadata": {"domain": "light", "area_id": "living_room"},
                },
            ]
        )

    @pytest.mark.asyncio
    async def test_process_query_control_intent(self, mock_process_query, mock_semantic_search):
        """Test processing a control query."""
        with (
            patch("app.tools.query_processing.process_query", mock_process_query),
            patch("app.tools.query_processing.semantic_search", mock_semantic_search),
        ):
            result = await process_natural_language_query("Turn on the living room lights")

            assert result["intent"] == "CONTROL"
            assert result["confidence"] == 0.95
            assert result["action"] == "on"
            assert result["domain"] == "light"
            assert len(result["entities"]) > 0
            assert len(result["execution_plan"]) > 0

    @pytest.mark.asyncio
    async def test_process_query_status_intent(self, mock_process_query, mock_semantic_search):
        """Test processing a status query."""
        mock_process_query.return_value = {
            "intent": "STATUS",
            "confidence": 0.90,
            "domain": "sensor",
            "domain_confidence": 0.85,
            "action": None,
            "action_params": {},
            "entities": [],
            "entity_filters": {},
            "parameters": {},
            "refined_query": "what is the temperature in the bedroom",
        }

        with (
            patch("app.tools.query_processing.process_query", mock_process_query),
            patch("app.tools.query_processing.semantic_search", mock_semantic_search),
        ):
            result = await process_natural_language_query("What's the temperature in the bedroom?")

            assert result["intent"] == "STATUS"
            assert result["confidence"] == 0.90
            assert result["domain"] == "sensor"
            assert result["action"] is None

    @pytest.mark.asyncio
    async def test_process_query_with_parameters(self, mock_process_query, mock_semantic_search):
        """Test processing a query with parameters."""
        mock_process_query.return_value = {
            "intent": "CONTROL",
            "confidence": 0.90,
            "domain": "climate",
            "domain_confidence": 0.95,
            "action": "set",
            "action_params": {"temperature": 22},
            "entities": [],
            "entity_filters": {"area_id": "kitchen"},
            "parameters": {"temperature": 22, "unit": "celsius"},
            "refined_query": "set kitchen temperature to 22 degrees",
        }

        mock_semantic_search.return_value = [
            {
                "entity_id": "climate.kitchen",
                "similarity_score": 0.95,
                "entity": {
                    "entity_id": "climate.kitchen",
                    "state": "heat",
                    "attributes": {"friendly_name": "Kitchen Thermostat"},
                },
                "explanation": "Entity 'Kitchen Thermostat' (climate) matched with 95% similarity",
                "metadata": {"domain": "climate", "area_id": "kitchen"},
            }
        ]

        with (
            patch("app.tools.query_processing.process_query", mock_process_query),
            patch("app.tools.query_processing.semantic_search", mock_semantic_search),
        ):
            result = await process_natural_language_query("Set kitchen temperature to 22 degrees")

            assert result["intent"] == "CONTROL"
            assert result["action"] == "set"
            assert "temperature" in result["parameters"]
            assert result["parameters"]["temperature"] == 22
            assert len(result["execution_plan"]) > 0
            assert result["execution_plan"][0]["action"] == "set_temperature"

    @pytest.mark.asyncio
    async def test_process_query_empty_query(self, mock_process_query, mock_semantic_search):
        """Test processing an empty query."""
        with (
            patch("app.tools.query_processing.process_query", mock_process_query),
            patch("app.tools.query_processing.semantic_search", mock_semantic_search),
        ):
            result = await process_natural_language_query("")

            assert "error" in result
            assert result["intent"] is None
            assert result["confidence"] == 0.0
            assert len(result["entities"]) == 0
            assert len(result["execution_plan"]) == 0

    @pytest.mark.asyncio
    async def test_process_query_search_intent(self, mock_process_query, mock_semantic_search):
        """Test processing a search query."""
        mock_process_query.return_value = {
            "intent": "SEARCH",
            "confidence": 0.85,
            "domain": "light",
            "domain_confidence": 0.80,
            "action": None,
            "action_params": {},
            "entities": [],
            "entity_filters": {},
            "parameters": {},
            "refined_query": "find all lights",
        }

        with (
            patch("app.tools.query_processing.process_query", mock_process_query),
            patch("app.tools.query_processing.semantic_search", mock_semantic_search),
        ):
            result = await process_natural_language_query("Find all lights")

            assert result["intent"] == "SEARCH"
            assert result["confidence"] == 0.85
            assert result["action"] is None
            assert len(result["execution_plan"]) == 0  # Search queries don't have execution plans

    @pytest.mark.asyncio
    async def test_process_query_error_handling(self, mock_process_query, mock_semantic_search):
        """Test error handling in query processing."""
        mock_process_query.side_effect = Exception("Processing failed")

        with (
            patch("app.tools.query_processing.process_query", mock_process_query),
            patch("app.tools.query_processing.semantic_search", mock_semantic_search),
        ):
            result = await process_natural_language_query("Turn on the lights")

            assert "error" in result
            assert result["intent"] is None
            assert result["confidence"] == 0.0

    @pytest.mark.asyncio
    async def test_process_query_entity_resolution(self, mock_process_query, mock_semantic_search):
        """Test entity resolution in query processing."""
        with (
            patch("app.tools.query_processing.process_query", mock_process_query),
            patch("app.tools.query_processing.semantic_search", mock_semantic_search),
        ):
            result = await process_natural_language_query("Turn on the living room lights")

            assert len(result["entities"]) > 0
            assert "entity_id" in result["entities"][0]
            assert "confidence" in result["entities"][0]
            assert "match_reason" in result["entities"][0]

    @pytest.mark.asyncio
    async def test_process_query_execution_plan(self, mock_process_query, mock_semantic_search):
        """Test execution plan building."""
        with (
            patch("app.tools.query_processing.process_query", mock_process_query),
            patch("app.tools.query_processing.semantic_search", mock_semantic_search),
        ):
            result = await process_natural_language_query("Turn on the living room lights")

            assert len(result["execution_plan"]) > 0
            assert "entity" in result["execution_plan"][0]
            assert "action" in result["execution_plan"][0]
            assert result["execution_plan"][0]["action"] == "on"

    @pytest.mark.asyncio
    async def test_process_query_climate_execution_plan(
        self, mock_process_query, mock_semantic_search
    ):
        """Test execution plan for climate control."""
        mock_process_query.return_value = {
            "intent": "CONTROL",
            "confidence": 0.90,
            "domain": "climate",
            "domain_confidence": 0.95,
            "action": "set",
            "action_params": {"temperature": 22},
            "entities": [],
            "entity_filters": {"area_id": "kitchen"},
            "parameters": {"temperature": 22, "unit": "celsius"},
            "refined_query": "set kitchen temperature to 22 degrees",
        }

        mock_semantic_search.return_value = [
            {
                "entity_id": "climate.kitchen",
                "similarity_score": 0.95,
                "entity": {
                    "entity_id": "climate.kitchen",
                    "state": "heat",
                    "attributes": {"friendly_name": "Kitchen Thermostat"},
                },
                "explanation": "Entity 'Kitchen Thermostat' (climate) matched with 95% similarity",
                "metadata": {"domain": "climate", "area_id": "kitchen"},
            }
        ]

        with (
            patch("app.tools.query_processing.process_query", mock_process_query),
            patch("app.tools.query_processing.semantic_search", mock_semantic_search),
        ):
            result = await process_natural_language_query("Set kitchen temperature to 22 degrees")

            assert len(result["execution_plan"]) > 0
            assert result["execution_plan"][0]["action"] == "set_temperature"
            assert "parameters" in result["execution_plan"][0]
            assert result["execution_plan"][0]["parameters"]["temperature"] == 22

    @pytest.mark.asyncio
    async def test_process_query_cover_execution_plan(
        self, mock_process_query, mock_semantic_search
    ):
        """Test execution plan for cover control."""
        mock_process_query.return_value = {
            "intent": "CONTROL",
            "confidence": 0.90,
            "domain": "cover",
            "domain_confidence": 0.85,
            "action": "on",
            "action_params": {},
            "entities": [],
            "entity_filters": {},
            "parameters": {},
            "refined_query": "open the garage door",
        }

        mock_semantic_search.return_value = [
            {
                "entity_id": "cover.garage_door",
                "similarity_score": 0.90,
                "entity": {
                    "entity_id": "cover.garage_door",
                    "state": "closed",
                    "attributes": {"friendly_name": "Garage Door"},
                },
                "explanation": "Entity 'Garage Door' (cover) matched with 90% similarity",
                "metadata": {"domain": "cover"},
            }
        ]

        with (
            patch("app.tools.query_processing.process_query", mock_process_query),
            patch("app.tools.query_processing.semantic_search", mock_semantic_search),
        ):
            result = await process_natural_language_query("Open the garage door")

            assert len(result["execution_plan"]) > 0
            assert result["execution_plan"][0]["action"] == "open"

    @pytest.mark.asyncio
    async def test_process_query_result_format(self, mock_process_query, mock_semantic_search):
        """Test result format."""
        with (
            patch("app.tools.query_processing.process_query", mock_process_query),
            patch("app.tools.query_processing.semantic_search", mock_semantic_search),
        ):
            result = await process_natural_language_query("Turn on the living room lights")

            assert "intent" in result
            assert "confidence" in result
            assert "entities" in result
            assert "action" in result
            assert "action_params" in result
            assert "parameters" in result
            assert "execution_plan" in result
            assert "domain" in result
            assert "refined_query" in result
