"""Unit tests for app.core.vectordb.classification module."""

from unittest.mock import MagicMock, patch

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


class TestClassifyIntent:
    """Test the classify_intent function."""

    @pytest.mark.asyncio
    async def test_classify_search_intent(self):
        """Test classifying SEARCH intent."""
        intent, confidence = await classify_intent("find all lights in the kitchen")
        assert intent == "SEARCH"
        assert 0.0 <= confidence <= 1.0

    @pytest.mark.asyncio
    async def test_classify_control_intent(self):
        """Test classifying CONTROL intent."""
        intent, confidence = await classify_intent("turn on the living room lights")
        assert intent == "CONTROL"
        assert 0.0 <= confidence <= 1.0

    @pytest.mark.asyncio
    async def test_classify_status_intent(self):
        """Test classifying STATUS intent."""
        intent, confidence = await classify_intent("what is the temperature in the kitchen")
        assert intent == "STATUS"
        assert 0.0 <= confidence <= 1.0

    @pytest.mark.asyncio
    async def test_classify_configure_intent(self):
        """Test classifying CONFIGURE intent."""
        intent, confidence = await classify_intent("configure the thermostat settings")
        assert intent == "CONFIGURE"
        assert 0.0 <= confidence <= 1.0

    @pytest.mark.asyncio
    async def test_classify_discover_intent(self):
        """Test classifying DISCOVER intent."""
        intent, confidence = await classify_intent("what other lights are in this room")
        assert intent == "DISCOVER"
        assert 0.0 <= confidence <= 1.0

    @pytest.mark.asyncio
    async def test_classify_analyze_intent(self):
        """Test classifying ANALYZE intent."""
        intent, confidence = await classify_intent("analyze the energy consumption")
        assert intent == "ANALYZE"
        assert 0.0 <= confidence <= 1.0

    @pytest.mark.asyncio
    async def test_classify_default_intent(self):
        """Test default intent when no pattern matches."""
        intent, confidence = await classify_intent("random text without patterns")
        assert intent == "SEARCH"
        assert confidence >= 0.5


class TestPredictDomain:
    """Test the predict_domain function."""

    @pytest.mark.asyncio
    async def test_predict_light_domain(self):
        """Test predicting light domain."""
        domain, confidence = await predict_domain("turn on the lights")
        assert domain == "light"
        assert 0.0 <= confidence <= 1.0

    @pytest.mark.asyncio
    async def test_predict_sensor_domain(self):
        """Test predicting sensor domain."""
        domain, confidence = await predict_domain("what is the temperature sensor reading")
        assert domain == "sensor"
        assert 0.0 <= confidence <= 1.0

    @pytest.mark.asyncio
    async def test_predict_switch_domain(self):
        """Test predicting switch domain."""
        domain, confidence = await predict_domain("toggle the switch")
        assert domain == "switch"
        assert 0.0 <= confidence <= 1.0

    @pytest.mark.asyncio
    async def test_predict_climate_domain(self):
        """Test predicting climate domain."""
        domain, confidence = await predict_domain("set the thermostat temperature")
        assert domain == "climate"
        assert 0.0 <= confidence <= 1.0

    @pytest.mark.asyncio
    async def test_predict_no_domain(self):
        """Test when no domain is found."""
        domain, confidence = await predict_domain("random text without domain")
        assert domain is None
        assert confidence == 0.0


class TestExtractAction:
    """Test the extract_action function."""

    @pytest.mark.asyncio
    async def test_extract_on_action(self):
        """Test extracting 'on' action."""
        action, params = await extract_action("turn on the lights")
        assert action == "on"
        assert isinstance(params, dict)

    @pytest.mark.asyncio
    async def test_extract_off_action(self):
        """Test extracting 'off' action."""
        action, params = await extract_action("turn off the lights")
        assert action == "off"
        assert isinstance(params, dict)

    @pytest.mark.asyncio
    async def test_extract_set_action(self):
        """Test extracting 'set' action."""
        action, params = await extract_action("set temperature to 22")
        assert action == "set"
        assert isinstance(params, dict)

    @pytest.mark.asyncio
    async def test_extract_increase_action(self):
        """Test extracting 'increase' action."""
        action, params = await extract_action("increase the brightness")
        assert action == "increase"
        assert isinstance(params, dict)

    @pytest.mark.asyncio
    async def test_extract_decrease_action(self):
        """Test extracting 'decrease' action."""
        action, params = await extract_action("decrease the brightness")
        assert action == "decrease"
        assert isinstance(params, dict)

    @pytest.mark.asyncio
    async def test_extract_action_with_value(self):
        """Test extracting action with numeric value."""
        action, params = await extract_action("set brightness to 50")
        assert action == "set"
        assert "value" in params
        assert params["value"] == 50

    @pytest.mark.asyncio
    async def test_extract_action_with_percentage(self):
        """Test extracting action with percentage value."""
        action, params = await extract_action("set brightness to 50%")
        assert action == "set"
        assert "value" in params
        assert params["value"] == 50
        assert params.get("unit") == "percent"

    @pytest.mark.asyncio
    async def test_extract_action_with_attribute(self):
        """Test extracting action with attribute."""
        action, params = await extract_action("increase brightness")
        assert action == "increase"
        assert "attribute" in params
        assert params["attribute"] == "brightness"

    @pytest.mark.asyncio
    async def test_extract_no_action(self):
        """Test when no action is found."""
        action, params = await extract_action("what is the temperature")
        assert action is None
        assert params == {}


class TestExtractEntities:
    """Test the extract_entities function."""

    @pytest.mark.asyncio
    async def test_extract_explicit_entity_ids(self):
        """Test extracting explicit entity IDs."""
        with patch("app.core.vectordb.classification.get_areas", return_value=[]):
            entities, filters = await extract_entities("turn on light.living_room")
            assert "light.living_room" in entities

    @pytest.mark.asyncio
    async def test_extract_area_from_query(self):
        """Test extracting area from query."""
        mock_areas = [
            {
                "area_id": "living_room",
                "name": "Living Room",
                "aliases": ["living room", "lounge"],
            }
        ]

        with patch("app.core.vectordb.classification.get_areas", return_value=mock_areas):
            entities, filters = await extract_entities("turn on lights in living room")
            assert "area_id" in filters
            assert filters["area_id"] == "living_room"

    @pytest.mark.asyncio
    async def test_extract_area_from_alias(self):
        """Test extracting area from alias."""
        mock_areas = [
            {
                "area_id": "living_room",
                "name": "Living Room",
                "aliases": ["lounge"],
            }
        ]

        with patch("app.core.vectordb.classification.get_areas", return_value=mock_areas):
            entities, filters = await extract_entities("turn on lights in lounge")
            assert "area_id" in filters
            assert filters["area_id"] == "living_room"

    @pytest.mark.asyncio
    async def test_extract_domain_filter(self):
        """Test extracting domain filter."""
        with patch("app.core.vectordb.classification.get_areas", return_value=[]):
            entities, filters = await extract_entities("turn on the lights")
            assert "domain" in filters
            assert filters["domain"] == "light"

    @pytest.mark.asyncio
    async def test_extract_type_hint(self):
        """Test extracting entity type hint."""
        with patch("app.core.vectordb.classification.get_areas", return_value=[]):
            entities, filters = await extract_entities("what is the temperature")
            assert "type" in filters
            assert filters["type"] == "temperature"

    @pytest.mark.asyncio
    async def test_extract_entities_error_handling(self):
        """Test error handling when get_areas fails."""
        with patch("app.core.vectordb.classification.get_areas", side_effect=Exception("Error")):
            entities, filters = await extract_entities("turn on lights")
            assert isinstance(entities, list)
            assert isinstance(filters, dict)


class TestExtractParameters:
    """Test the extract_parameters function."""

    @pytest.mark.asyncio
    async def test_extract_integer_value(self):
        """Test extracting integer value."""
        params = await extract_parameters("set temperature to 22")
        assert "value" in params
        assert params["value"] == 22

    @pytest.mark.asyncio
    async def test_extract_float_value(self):
        """Test extracting float value."""
        params = await extract_parameters("set temperature to 22.5")
        assert "value" in params
        assert params["value"] == 22.5

    @pytest.mark.asyncio
    async def test_extract_percentage_value(self):
        """Test extracting percentage value."""
        params = await extract_parameters("set brightness to 50%")
        assert "value" in params
        assert params["value"] == 50
        assert params.get("unit") == "percent"

    @pytest.mark.asyncio
    async def test_extract_attribute(self):
        """Test extracting attribute name."""
        params = await extract_parameters("increase brightness")
        assert "attribute" in params
        assert params["attribute"] == "brightness"

    @pytest.mark.asyncio
    async def test_extract_time_reference(self):
        """Test extracting time reference."""
        params = await extract_parameters("show me data from last 24 hours")
        assert "time" in params

    @pytest.mark.asyncio
    async def test_extract_no_parameters(self):
        """Test when no parameters are found."""
        params = await extract_parameters("what is the temperature")
        assert isinstance(params, dict)
        # May or may not have parameters depending on query


class TestRefineQuery:
    """Test the refine_query function."""

    @pytest.mark.asyncio
    async def test_refine_query_normalize_whitespace(self):
        """Test normalizing whitespace."""
        refined = await refine_query("turn  on   the  lights")
        assert refined == "turn on the lights"

    @pytest.mark.asyncio
    async def test_refine_query_strip(self):
        """Test stripping query."""
        refined = await refine_query("  turn on the lights  ")
        assert refined == "turn on the lights"

    @pytest.mark.asyncio
    async def test_refine_query_synonym_expansion(self):
        """Test synonym expansion."""
        refined = await refine_query("switch on the lights")
        # Should normalize to "turn on"
        assert "turn on" in refined or "switch on" in refined


class TestProcessQuery:
    """Test the process_query function."""

    @pytest.fixture
    def mock_manager(self):
        """Create a mock VectorDBManager."""
        manager = MagicMock()
        return manager

    @pytest.fixture
    def mock_config(self):
        """Create a mock VectorDBConfig."""
        config = MagicMock()
        return config

    @pytest.mark.asyncio
    async def test_process_control_query(self, mock_manager, mock_config):
        """Test processing a CONTROL query."""
        with patch("app.core.vectordb.classification.get_areas", return_value=[]):
            result = await process_query(
                "turn on the living room lights", manager=mock_manager, config=mock_config
            )

            assert result["intent"] == "CONTROL"
            assert "confidence" in result
            assert result["action"] == "on"
            assert "refined_query" in result
            assert "entity_filters" in result
            assert "parameters" in result

    @pytest.mark.asyncio
    async def test_process_search_query(self, mock_manager, mock_config):
        """Test processing a SEARCH query."""
        with patch("app.core.vectordb.classification.get_areas", return_value=[]):
            result = await process_query(
                "find all temperature sensors", manager=mock_manager, config=mock_config
            )

            assert result["intent"] == "SEARCH"
            assert "confidence" in result
            assert "domain" in result
            assert "refined_query" in result

    @pytest.mark.asyncio
    async def test_process_status_query(self, mock_manager, mock_config):
        """Test processing a STATUS query."""
        with patch("app.core.vectordb.classification.get_areas", return_value=[]):
            result = await process_query(
                "what is the temperature in the kitchen",
                manager=mock_manager,
                config=mock_config,
            )

            assert result["intent"] == "STATUS"
            assert "confidence" in result
            assert "domain" in result
            assert "refined_query" in result

    @pytest.mark.asyncio
    async def test_process_query_with_value(self, mock_manager, mock_config):
        """Test processing a query with numeric value."""
        with patch("app.core.vectordb.classification.get_areas", return_value=[]):
            result = await process_query(
                "set temperature to 22", manager=mock_manager, config=mock_config
            )

            assert result["intent"] == "CONTROL"
            assert result["action"] == "set"
            assert "value" in result["action_params"]
            assert result["action_params"]["value"] == 22

    @pytest.mark.asyncio
    async def test_process_query_with_area(self, mock_manager, mock_config):
        """Test processing a query with area."""
        mock_areas = [
            {
                "area_id": "living_room",
                "name": "Living Room",
                "aliases": [],
            }
        ]

        with patch("app.core.vectordb.classification.get_areas", return_value=mock_areas):
            result = await process_query(
                "turn on lights in living room", manager=mock_manager, config=mock_config
            )

            assert "entity_filters" in result
            assert "area_id" in result["entity_filters"]
            assert result["entity_filters"]["area_id"] == "living_room"

    @pytest.mark.asyncio
    async def test_process_query_complete_result(self, mock_manager, mock_config):
        """Test that process_query returns all expected fields."""
        with patch("app.core.vectordb.classification.get_areas", return_value=[]):
            result = await process_query(
                "turn on the lights", manager=mock_manager, config=mock_config
            )

            # Check all expected fields are present
            assert "intent" in result
            assert "confidence" in result
            assert "domain" in result
            assert "domain_confidence" in result
            assert "action" in result
            assert "action_params" in result
            assert "entities" in result
            assert "entity_filters" in result
            assert "parameters" in result
            assert "refined_query" in result
