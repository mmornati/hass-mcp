import asyncio
import os
import sys
from unittest.mock import AsyncMock, patch

import pytest

# Add the app directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
app_dir = os.path.join(parent_dir, "app")
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)


class TestMCPServer:
    """Test the MCP server functionality."""

    def test_server_version(self):
        """Test that the server is initialized with version for server info."""
        # Import the server module directly without mocking
        # This ensures we're testing the actual code
        from app.server import __version__, mcp

        # All MCP servers should have a name, and it should be "Hass-MCP"
        assert hasattr(mcp, "name")
        assert mcp.name == "Hass-MCP"

        # Verify that __version__ is set in the server module
        # FastMCP uses the version parameter internally to provide serverInfo
        assert __version__ is not None
        assert isinstance(__version__, str)
        assert len(__version__) > 0

        # The version should be a valid version string (e.g., "0.1.1")
        assert "." in __version__  # Basic version format check

    def test_async_handler_decorator(self):
        """Test the async_handler decorator."""
        # Import the decorator
        from app.core import async_handler

        # Create a test async function
        async def test_func(arg1, arg2=None):
            return f"{arg1}_{arg2}"

        # Apply the decorator
        decorated_func = async_handler("test_command")(test_func)

        # Run the decorated function
        result = asyncio.run(decorated_func("val1", arg2="val2"))

        # Verify the result
        assert result == "val1_val2"

    def test_tool_functions_exist(self):
        """Test that tool functions exist in the server module."""
        # Import the server module directly
        import app.server

        # List of expected tool functions
        # Note: Some tools have been unified and extracted to app.tools modules but are re-exported
        expected_tools = [
            "get_entity",
            "entity_action",
            "search_entities",  # Unified tool replacing list_entities, search_entities_tool, semantic_search_entities_tool
            "get_system_info",  # Unified tool replacing get_version, system_overview, system_health, core_config
            "get_system_data",  # Unified tool replacing get_error_log, get_cache_statistics, get_history, domain_summary
            "list_items",  # Unified tool for listing items
            "get_item",  # Unified tool for getting items
            "manage_item",  # Unified tool for managing items
            "list_automations",  # Re-exported from app.tools.automations
            # Tools that exist but may be in different modules:
            "list_scripts_tool",  # Re-exported from app.tools.scripts
            "list_devices_tool",  # Re-exported from app.tools.devices
            "list_areas_tool",  # Re-exported from app.tools.areas
        ]

        # Check that each expected tool function exists
        for tool_name in expected_tools:
            assert hasattr(app.server, tool_name)
            assert callable(getattr(app.server, tool_name))

    def test_resource_functions_exist(self):
        """Test that resource functions exist in the server module."""
        # Import the server module directly
        import app.server

        # List of expected resource functions - Use only the ones actually in server.py
        expected_resources = [
            "get_entity_resource",
            "get_entity_resource_detailed",
            "get_all_entities_resource",
            "list_states_by_domain_resource",  # Domain-specific resource
            "search_entities_resource_with_limit",  # Search resource with limit parameter
        ]

        # Check that each expected resource function exists
        for resource_name in expected_resources:
            assert hasattr(app.server, resource_name)
            assert callable(getattr(app.server, resource_name))

    @pytest.mark.asyncio
    async def test_list_automations_error_handling(self):
        """Test that list_automations handles errors properly."""
        from app.server import list_automations

        # Mock the get_automations function with different scenarios
        # Note: list_automations is now in app.tools.automations, which calls app.api.automations.get_automations
        with patch(
            "app.tools.automations.get_automations", new_callable=AsyncMock
        ) as mock_get_automations:
            # Case 1: Test with 404 error response format (list with single dict with error key)
            mock_get_automations.return_value = [{"error": "HTTP error: 404 - Not Found"}]

            # Should return an empty list
            result = await list_automations()
            assert isinstance(result, list)
            assert len(result) == 0

            # Case 2: Test with dict error response
            mock_get_automations.return_value = {"error": "HTTP error: 404 - Not Found"}

            # Should return an empty list
            result = await list_automations()
            assert isinstance(result, list)
            assert len(result) == 0

            # Case 3: Test with unexpected error
            mock_get_automations.side_effect = Exception("Unexpected error")

            # Should return an empty list and log the error
            result = await list_automations()
            assert isinstance(result, list)
            assert len(result) == 0

            # Case 4: Test with successful response
            mock_automations = [
                {
                    "id": "morning_lights",
                    "entity_id": "automation.morning_lights",
                    "state": "on",
                    "alias": "Turn on lights in the morning",
                }
            ]
            mock_get_automations.side_effect = None
            mock_get_automations.return_value = mock_automations

            # Should return the automations list
            result = await list_automations()
            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["id"] == "morning_lights"

    def test_tools_have_proper_docstrings(self):
        """Test that tool functions have proper docstrings"""
        # Import the server module directly
        import app.server

        # List of expected tool functions
        # Note: Some tools have been unified and extracted to app.tools modules but are re-exported
        tool_functions = [
            "get_entity",
            "entity_action",
            "search_entities",  # Unified tool replacing list_entities, search_entities_tool, semantic_search_entities_tool
            "get_system_info",  # Unified tool replacing get_version, system_overview, system_health, core_config
            "get_system_data",  # Unified tool replacing get_error_log, get_cache_statistics, get_history, domain_summary
            "list_items",  # Unified tool for listing items
            "get_item",  # Unified tool for getting items
            "manage_item",  # Unified tool for managing items
            "list_automations",  # Re-exported from app.tools.automations
            # Tools that exist but may be in different modules:
            "list_scripts_tool",  # Re-exported from app.tools.scripts
            "list_devices_tool",  # Re-exported from app.tools.devices
            "list_areas_tool",  # Re-exported from app.tools.areas
        ]

        # Check that each tool function has a proper docstring and exists
        for tool_name in tool_functions:
            assert hasattr(app.server, tool_name), f"{tool_name} function missing"
            tool_function = getattr(app.server, tool_name)
            assert tool_function.__doc__ is not None, f"{tool_name} missing docstring"
            assert len(tool_function.__doc__.strip()) > 10, (
                f"{tool_name} has insufficient docstring"
            )

    def test_prompt_functions_exist(self):
        """Test that prompt functions exist in the server module."""
        # Import the server module directly
        import app.server

        # List of expected prompt functions
        expected_prompts = ["create_automation", "debug_automation", "troubleshoot_entity"]

        # Check that each expected prompt function exists
        for prompt_name in expected_prompts:
            assert hasattr(app.server, prompt_name)
            assert callable(getattr(app.server, prompt_name))

    @pytest.mark.asyncio
    async def test_search_entities_resource(self):
        """Test the search_entities unified tool function"""
        from app.server import search_entities

        # Mock the get_entities function with test data
        mock_entities = [
            {
                "entity_id": "light.living_room",
                "state": "on",
                "attributes": {"friendly_name": "Living Room Light", "brightness": 255},
            },
            {
                "entity_id": "light.kitchen",
                "state": "off",
                "attributes": {"friendly_name": "Kitchen Light"},
            },
        ]

        with patch(
            "app.tools.unified.get_entities", new_callable=AsyncMock, return_value=mock_entities
        ) as mock_get:
            # Test search with a valid query (keyword mode by default)
            result = await search_entities(query="living", search_mode="keyword")

            # Verify the function was called with the right parameters including lean format
            mock_get.assert_called_once_with(
                domain=None, search_query="living", limit=100, lean=True
            )

            # Check that the result contains the expected entity data
            assert result["count"] == 2
            assert any(e["entity_id"] == "light.living_room" for e in result["results"])

            # Check that domain counts are included
            assert "domains" in result
            assert "light" in result["domains"]

            # Test with empty query (returns all entities instead of error)
            mock_get.reset_mock()
            result = await search_entities(query=None, search_mode="keyword")
            assert "error" not in result
            assert result["count"] > 0

            # Test that simplified representation includes domain-specific attributes
            mock_get.reset_mock()
            result = await search_entities(query="living", search_mode="keyword")
            assert any("brightness" in e for e in result["results"])

            # Test with custom limit as an integer
            mock_get.reset_mock()
            result = await search_entities(query="light", limit=5, search_mode="keyword")
            mock_get.assert_called_once_with(domain=None, search_query="light", limit=5, lean=True)

            # Test with a different limit to ensure it's respected
            mock_get.reset_mock()
            result = await search_entities(query="light", limit=10, search_mode="keyword")
            mock_get.assert_called_once_with(domain=None, search_query="light", limit=10, lean=True)

    @pytest.mark.asyncio
    async def test_get_system_data_domain_summary(self):
        """Test the get_system_data unified tool function with domain_summary data_type"""
        from app.server import get_system_data

        # Mock the summarize_domain function
        mock_summary = {
            "domain": "light",
            "total_count": 2,
            "state_distribution": {"on": 1, "off": 1},
            "examples": {
                "on": [{"entity_id": "light.living_room", "friendly_name": "Living Room Light"}],
                "off": [{"entity_id": "light.kitchen", "friendly_name": "Kitchen Light"}],
            },
            "common_attributes": [("friendly_name", 2), ("brightness", 1)],
        }

        with patch(
            "app.tools.unified.summarize_domain",
            new_callable=AsyncMock,
            return_value=mock_summary,
        ) as mock_summarize:
            # Test the function
            result = await get_system_data(data_type="domain_summary", domain="light")

            # Verify the function was called with the right parameters
            mock_summarize.assert_called_once_with("light")

            # Check that the result matches the mock data
            assert result == mock_summary

    @pytest.mark.asyncio
    async def test_get_entity_with_field_filtering(self):
        """Test the get_entity function with field filtering"""
        from app.server import get_entity

        # Mock entity data
        mock_entity = {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {
                "friendly_name": "Living Room Light",
                "brightness": 255,
                "color_temp": 370,
            },
        }

        # Mock filtered entity data
        mock_filtered = {"entity_id": "light.living_room", "state": "on"}

        # Set up mock for get_entity_state to handle different calls
        with patch(
            "app.tools.entities.get_entity_state",
            new_callable=AsyncMock,
            return_value=mock_filtered,
        ) as mock_get_state:
            # Test with field filtering
            result = await get_entity(entity_id="light.living_room", fields=["state"])

            # Verify the function call with fields parameter
            mock_get_state.assert_called_with("light.living_room", fields=["state"])
            assert result == mock_filtered

            # Test with detailed=True
            mock_get_state.reset_mock()
            mock_get_state.return_value = mock_entity
            result = await get_entity(entity_id="light.living_room", detailed=True)

            # Verify the function call with detailed parameter
            mock_get_state.assert_called_with("light.living_room", lean=False)
            assert result == mock_entity

            # Test default lean mode
            mock_get_state.reset_mock()
            mock_get_state.return_value = mock_filtered
            result = await get_entity(entity_id="light.living_room")

            # Verify the function call with lean=True parameter
            mock_get_state.assert_called_with("light.living_room", lean=True)
            assert result == mock_filtered

    @pytest.mark.asyncio
    async def test_get_system_info_tool(self):
        """Test the get_system_info unified tool function"""
        from app.server import get_system_info

        # Test system_health info_type
        mock_health_data = {
            "homeassistant": {"healthy": True, "version": "2025.3.0"},
            "supervisor": {"healthy": True, "version": "2025.03.1"},
            "recorder": {"healthy": True},
        }

        with patch(
            "app.api.system.get_system_health",
            new_callable=AsyncMock,
            return_value=mock_health_data,
        ) as mock_get:
            # Test the function with health info_type
            result = await get_system_info(info_type="health")

            # Verify the function was called
            mock_get.assert_called_once()

            # Check that the result matches the mock data
            assert result == mock_health_data
            assert "homeassistant" in result
            assert result["homeassistant"]["healthy"] is True
            assert "supervisor" in result

        # Test core_config info_type
        mock_config_data = {
            "location_name": "Home",
            "time_zone": "America/New_York",
            "unit_system": {
                "length": "km",
                "mass": "g",
                "temperature": "°C",
                "volume": "L",
            },
            "version": "2025.3.0",
            "components": ["mqtt", "hue", "automation"],
            "latitude": 40.7128,
            "longitude": -74.0060,
        }

        with patch(
            "app.api.system.get_core_config",
            new_callable=AsyncMock,
            return_value=mock_config_data,
        ) as mock_get:
            # Test the function with config info_type
            result = await get_system_info(info_type="config")

            # Verify the function was called
            mock_get.assert_called_once()

            # Check that the result matches the mock data
            assert result == mock_config_data
            assert result["location_name"] == "Home"
            assert result["time_zone"] == "America/New_York"
            assert "mqtt" in result["components"]

        # Test version info_type
        mock_version = "2025.3.0"
        with patch(
            "app.api.system.get_hass_version",
            new_callable=AsyncMock,
            return_value=mock_version,
        ) as mock_get:
            result = await get_system_info(info_type="version")
            mock_get.assert_called_once()
            assert result == "2025.3.0"
