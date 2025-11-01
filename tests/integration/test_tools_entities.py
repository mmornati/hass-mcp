"""Integration tests for app.tools.entities module."""

from unittest.mock import AsyncMock, patch

import pytest

from app.tools import entities


class TestEntityTools:
    """Test entity MCP tools."""

    @pytest.fixture(autouse=True)
    def mock_config(self):
        """Mock HA_URL and HA_TOKEN for all tests in this class."""
        with (
            patch("app.config.HA_URL", "http://localhost:8123"),
            patch("app.config.HA_TOKEN", "test_token"),
            patch("app.core.decorators.HA_TOKEN", "test_token"),
        ):
            yield

    @pytest.mark.asyncio
    async def test_get_entity_detailed(self, mock_httpx_client):
        """Test get_entity tool with detailed=True."""
        # Mock entity state
        mock_entity = {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {"brightness": 255, "friendly_name": "Living Room Light"},
        }

        # Mock get_entity_state response
        with patch("app.tools.entities.get_entity_state", new_callable=AsyncMock, return_value=mock_entity):
            result = await entities.get_entity("light.living_room", detailed=True)

            assert result == mock_entity

    @pytest.mark.asyncio
    async def test_get_entity_with_fields(self, mock_httpx_client):
        """Test get_entity tool with fields parameter."""
        mock_entity = {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {"brightness": 255},
        }

        with patch("app.tools.entities.get_entity_state", new_callable=AsyncMock, return_value=mock_entity):
            fields = ["state", "attr.brightness"]
            result = await entities.get_entity("light.living_room", fields=fields)

            assert result == mock_entity

    @pytest.mark.asyncio
    async def test_get_entity_lean(self, mock_httpx_client):
        """Test get_entity tool with lean format (default)."""
        mock_entity = {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {"friendly_name": "Living Room Light"},
        }

        with patch("app.tools.entities.get_entity_state", new_callable=AsyncMock, return_value=mock_entity):
            result = await entities.get_entity("light.living_room")

            assert result == mock_entity

    @pytest.mark.asyncio
    async def test_entity_action_on(self, mock_httpx_client):
        """Test entity_action tool with 'on' action."""
        mock_response = []

        with patch("app.tools.entities.call_service", new_callable=AsyncMock, return_value=mock_response):
            result = await entities.entity_action("light.living_room", "on", {"brightness": 255})

            assert result == mock_response

    @pytest.mark.asyncio
    async def test_entity_action_off(self, mock_httpx_client):
        """Test entity_action tool with 'off' action."""
        mock_response = []

        with patch("app.tools.entities.call_service", new_callable=AsyncMock, return_value=mock_response):
            result = await entities.entity_action("switch.garden_lights", "off")

            assert result == mock_response

    @pytest.mark.asyncio
    async def test_entity_action_toggle(self, mock_httpx_client):
        """Test entity_action tool with 'toggle' action."""
        mock_response = []

        with patch("app.tools.entities.call_service", new_callable=AsyncMock, return_value=mock_response):
            result = await entities.entity_action("light.bedroom", "toggle")

            assert result == mock_response

    @pytest.mark.asyncio
    async def test_entity_action_invalid(self, mock_httpx_client):
        """Test entity_action tool with invalid action."""
        result = await entities.entity_action("light.living_room", "invalid")

        assert isinstance(result, dict)
        assert "error" in result
        assert "Invalid action" in result["error"]

    @pytest.mark.asyncio
    async def test_list_entities_with_domain(self, mock_httpx_client):
        """Test list_entities tool with domain filter."""
        mock_entities = [
            {"entity_id": "light.living_room", "state": "on"},
            {"entity_id": "light.bedroom", "state": "off"},
        ]

        with patch("app.tools.entities.get_entities", new_callable=AsyncMock, return_value=mock_entities):
            result = await entities.list_entities(domain="light")

            assert result == mock_entities

    @pytest.mark.asyncio
    async def test_list_entities_with_search(self, mock_httpx_client):
        """Test list_entities tool with search query."""
        mock_entities = [{"entity_id": "sensor.kitchen_temperature", "state": "22.5"}]

        with patch("app.tools.entities.get_entities", new_callable=AsyncMock, return_value=mock_entities):
            result = await entities.list_entities(search_query="kitchen", limit=20)

            assert result == mock_entities

    @pytest.mark.asyncio
    async def test_list_entities_detailed(self, mock_httpx_client):
        """Test list_entities tool with detailed=True."""
        mock_entities = [
            {
                "entity_id": "sensor.temperature",
                "state": "22.5",
                "attributes": {"unit_of_measurement": "°C"},
            }
        ]

        with patch("app.tools.entities.get_entities", new_callable=AsyncMock, return_value=mock_entities):
            result = await entities.list_entities(domain="sensor", detailed=True)

            assert result == mock_entities

    @pytest.mark.asyncio
    async def test_list_entities_wildcard_handling(self, mock_httpx_client):
        """Test list_entities tool with wildcard search query."""
        mock_entities = [{"entity_id": "light.test", "state": "on"}]

        with patch("app.tools.entities.get_entities", new_callable=AsyncMock, return_value=mock_entities):
            result = await entities.list_entities(search_query="*")

            # Should convert "*" to None
            assert result == mock_entities

    @pytest.mark.asyncio
    async def test_search_entities_tool_with_query(self, mock_httpx_client):
        """Test search_entities_tool with a query."""
        mock_entities = [
            {
                "entity_id": "sensor.temperature",
                "state": "22.5",
                "attributes": {"friendly_name": "Temperature Sensor"},
            }
        ]

        with patch("app.tools.entities.get_entities", new_callable=AsyncMock, return_value=mock_entities):
            result = await entities.search_entities_tool("temperature", limit=10)

            assert isinstance(result, dict)
            assert "count" in result
            assert "results" in result
            assert "domains" in result
            assert result["count"] > 0

    @pytest.mark.asyncio
    async def test_search_entities_tool_empty_query(self, mock_httpx_client):
        """Test search_entities_tool with empty query."""
        mock_entities = [
            {"entity_id": "light.test1", "state": "on"},
            {"entity_id": "switch.test2", "state": "off"},
        ]

        with patch("app.tools.entities.get_entities", new_callable=AsyncMock, return_value=mock_entities):
            result = await entities.search_entities_tool("", limit=20)

            assert isinstance(result, dict)
            assert "count" in result
            assert "results" in result
            assert "domains" in result
            assert result["count"] == 2
            assert "light" in result["domains"]
            assert "switch" in result["domains"]

    @pytest.mark.asyncio
    async def test_search_entities_tool_wildcard(self, mock_httpx_client):
        """Test search_entities_tool with wildcard query."""
        mock_entities = [{"entity_id": "sensor.test", "state": "22.5"}]

        with patch("app.tools.entities.get_entities", new_callable=AsyncMock, return_value=mock_entities):
            result = await entities.search_entities_tool("*", limit=10)

            # Should convert "*" to empty query
            assert isinstance(result, dict)
            assert "count" in result

    @pytest.mark.asyncio
    async def test_search_entities_tool_error_handling(self, mock_httpx_client):
        """Test search_entities_tool error handling."""
        error_response = {"error": "API error occurred"}

        with patch("app.tools.entities.get_entities", new_callable=AsyncMock, return_value=error_response):
            result = await entities.search_entities_tool("test", limit=10)

            assert isinstance(result, dict)
            assert "error" in result
            assert result["count"] == 0
            assert result["results"] == []
            assert result["domains"] == {}

