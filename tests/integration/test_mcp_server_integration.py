"""Integration tests for MCP server tool registration and functionality.

This test suite validates that all migrated commands exist, are properly
registered with the MCP server, and can communicate with Home Assistant.
"""

import inspect
from unittest.mock import AsyncMock, patch

import pytest

from app.server import mcp


class TestMCPServerToolRegistration:
    """Test that all tools are properly registered with the MCP server."""

    def test_server_initialization(self):
        """Test that the MCP server is properly initialized with server info."""
        from app.server import __version__

        assert mcp is not None
        assert hasattr(mcp, "name")
        assert mcp.name == "Hass-MCP"

        # Verify that version is set in the server module
        # FastMCP uses the version parameter internally to provide serverInfo
        assert __version__ is not None
        assert isinstance(__version__, str)
        assert len(__version__) > 0

        # The version should be a valid version string (e.g., "0.1.1")
        assert "." in __version__  # Basic version format check

    def test_tools_registered(self):
        """Test that all expected tools are registered with the MCP server."""
        # Get all registered tools from the MCP server
        # FastMCP stores tools internally, we need to check if they exist
        # by trying to access the server's internal state or by testing tool calls

        # Expected tool categories and their counts
        expected_tools = {
            # Entities (3 tools)
            "get_entity",
            "entity_action",
            "search_entities",  # Unified tool replacing list_entities, search_entities_tool, semantic_search_entities_tool
            # Automations (10 tools)
            "list_automations",
            "get_automation_config",
            "create_automation",
            "update_automation",
            "delete_automation",
            "enable_automation",
            "disable_automation",
            "trigger_automation",
            "get_automation_execution_log",
            "validate_automation_config",
            # Scripts (4 tools)
            "list_scripts",
            "get_script",
            "run_script",
            "reload_scripts",
            # Devices (3 tools)
            "list_devices",  # Via list_items
            "get_device",  # Via get_item
            "get_item_entities",  # Unified tool replacing get_device_entities, get_area_entities
            "get_item_summary",  # Unified tool replacing get_device_stats, get_area_summary
            # Areas (4 tools)
            "list_areas",  # Via list_items
            "create_area",  # Via manage_item
            "update_area",  # Via manage_item
            "delete_area",  # Via manage_item
            # Scenes (5 tools)
            "list_scenes",
            "get_scene",
            "create_scene",
            "activate_scene",
            "reload_scenes",
            # Integrations (3 tools)
            "list_integrations",
            "get_integration_config",
            "reload_integration",
            # System (3 tools)
            "get_system_info",  # Unified tool replacing get_version, system_overview, system_health, core_config
            "get_system_data",  # Unified tool replacing get_error_log, get_cache_statistics, get_history, domain_summary
            "restart_ha",
            # Services (1 tool)
            "call_service",
            # Templates (1 tool)
            "test_template",
            # Logbook (1 tool)
            "get_logbook",  # Unified tool replacing get_logbook, get_entity_logbook, search_logbook
            # Statistics (1 tool)
            "get_statistics",  # Unified tool replacing get_entity_statistics, get_domain_statistics, analyze_usage_patterns
            # Diagnostics (1 tool)
            "diagnose",  # Unified tool replacing diagnose_entity, check_entity_dependencies, analyze_automation_conflicts, get_integration_errors
            # Blueprints (4 tools)
            "list_blueprints",
            "get_blueprint",
            "import_blueprint",
            "create_automation_from_blueprint",
            # Zones (4 tools)
            "list_zones",
            "create_zone",
            "update_zone",
            "delete_zone",
            # Events (1 tool)
            "manage_events",  # Unified tool replacing fire_event, list_event_types, get_events
            # Notifications (1 tool)
            "manage_notifications",  # Unified tool replacing list_notification_services, send_notification, test_notification
            # Calendars (3 tools)
            "list_calendars",
            "get_calendar_events",
            "create_calendar_event",
            # Helpers (3 tools)
            "list_helpers",
            "get_helper",
            "update_helper",
            # Tags (4 tools)
            "list_tags",
            "create_tag",
            "delete_tag",
            "get_tag_automations",
            # Webhooks (1 tool)
            "manage_webhooks",  # Unified tool replacing list_webhooks, test_webhook
            # Backups (4 tools)
            "list_backups",
            "create_backup",
            "restore_backup",
            "delete_backup",
        }

        # Note: FastMCP doesn't expose a direct way to list all registered tools
        # So we'll test by importing the functions and verifying they exist
        # We'll also test actual tool calls in the next test class

        # Verify all tool functions can be imported from app.server
        from app.server import (
            call_service_tool,
            create_automation_tool,
            delete_automation_tool,
            disable_automation_tool,
            enable_automation_tool,
            entity_action,
            get_automation_config_tool,
            get_automation_execution_log_tool,
            get_entity,
            get_system_info,  # Unified tool replacing get_version
            list_automations,
            search_entities,  # Unified tool replacing list_entities, search_entities_tool
            trigger_automation_tool,
            update_automation_tool,
            validate_automation_config_tool,
        )

        # Verify functions exist and are callable
        assert callable(get_entity)
        assert callable(entity_action)
        assert callable(search_entities)  # Unified tool
        assert callable(list_automations)
        assert callable(get_automation_config_tool)
        assert callable(create_automation_tool)
        assert callable(update_automation_tool)
        assert callable(delete_automation_tool)
        assert callable(enable_automation_tool)
        assert callable(disable_automation_tool)
        assert callable(trigger_automation_tool)
        assert callable(get_automation_execution_log_tool)
        assert callable(validate_automation_config_tool)
        assert callable(call_service_tool)
        assert callable(get_system_info)  # Unified tool replacing get_version

        # Verify they are async functions
        assert inspect.iscoroutinefunction(get_entity)
        assert inspect.iscoroutinefunction(entity_action)
        assert inspect.iscoroutinefunction(search_entities)  # Unified tool


class TestMCPToolsFunctionality:
    """Test that tools can communicate with Home Assistant (mocked)."""

    @pytest.fixture(autouse=True)
    def mock_config(self):
        """Mock HA_URL and HA_TOKEN for all tests."""
        with (
            patch("app.config.HA_URL", "http://localhost:8123"),
            patch("app.config.HA_TOKEN", "test_token"),
            patch("app.core.decorators.HA_TOKEN", "test_token"),
        ):
            yield

    @pytest.mark.asyncio
    async def test_get_entity_tool(self):
        """Test get_entity tool works correctly."""
        from app.tools.entities import get_entity

        mock_entity = {
            "entity_id": "light.living_room",
            "state": "on",
            "attributes": {"brightness": 255, "friendly_name": "Living Room Light"},
        }

        with patch(
            "app.tools.entities.get_entity_state", new_callable=AsyncMock, return_value=mock_entity
        ):
            result = await get_entity("light.living_room")

            assert isinstance(result, dict)
            assert result["entity_id"] == "light.living_room"
            assert result["state"] == "on"

    @pytest.mark.asyncio
    async def test_search_entities_tool(self):
        """Test search_entities unified tool works correctly."""
        from app.tools.unified import search_entities

        mock_entities = [
            {"entity_id": "light.living_room", "state": "on"},
            {"entity_id": "switch.kitchen", "state": "off"},
        ]

        with patch(
            "app.api.entities.get_entities", new_callable=AsyncMock, return_value=mock_entities
        ):
            result = await search_entities(domain="light", search_mode="keyword")

            assert isinstance(result, dict)
            assert "results" in result
            assert len(result["results"]) == 2

    @pytest.mark.asyncio
    async def test_entity_action_tool(self):
        """Test entity_action tool works correctly."""
        from app.tools.entities import entity_action

        mock_response = {"result": "ok"}

        with patch(
            "app.tools.entities.call_service", new_callable=AsyncMock, return_value=mock_response
        ):
            result = await entity_action("light.living_room", "on", {"brightness": 255})

            assert isinstance(result, dict)
            assert "result" in result

    @pytest.mark.asyncio
    async def test_list_automations_tool(self):
        """Test list_automations tool works correctly."""
        from app.tools.automations import list_automations

        mock_automations = [
            {
                "entity_id": "automation.morning_lights",
                "state": "on",
                "alias": "Morning Lights",
            }
        ]

        with patch(
            "app.tools.automations.get_automations",
            new_callable=AsyncMock,
            return_value=mock_automations,
        ):
            result = await list_automations()

            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["entity_id"] == "automation.morning_lights"

    @pytest.mark.asyncio
    async def test_call_service_tool(self):
        """Test call_service tool works correctly."""
        from app.tools.services import call_service_tool

        mock_response = {"result": "ok"}

        with patch(
            "app.tools.services.call_service", new_callable=AsyncMock, return_value=mock_response
        ):
            result = await call_service_tool("light", "turn_on", {"entity_id": "light.living_room"})

            assert isinstance(result, dict)
            assert "result" in result

    @pytest.mark.asyncio
    async def test_get_system_info_tool(self):
        """Test get_system_info unified tool works correctly."""
        from app.tools.unified import get_system_info

        mock_version = "2025.3.0"

        with patch(
            "app.api.system.get_hass_version",
            new_callable=AsyncMock,
            return_value=mock_version,
        ):
            result = await get_system_info(info_type="version")

            assert isinstance(result, str)
            assert result == "2025.3.0"

    @pytest.mark.asyncio
    async def test_list_scripts_tool(self):
        """Test list_scripts tool works correctly."""
        from app.tools.scripts import list_scripts_tool

        mock_scripts = [
            {
                "entity_id": "script.morning_routine",
                "state": "off",
                "alias": "Morning Routine",
            }
        ]

        with patch(
            "app.tools.scripts.get_scripts", new_callable=AsyncMock, return_value=mock_scripts
        ):
            result = await list_scripts_tool()

            assert isinstance(result, list)
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_list_devices_tool(self):
        """Test list_devices tool works correctly."""
        from app.tools.devices import list_devices_tool

        mock_devices = [
            {
                "id": "device_123",
                "name": "Living Room Device",
                "manufacturer": "Test Manufacturer",
            }
        ]

        with patch(
            "app.tools.devices.get_devices", new_callable=AsyncMock, return_value=mock_devices
        ):
            result = await list_devices_tool()

            assert isinstance(result, list)
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_list_areas_tool(self):
        """Test list_areas tool works correctly."""
        from app.tools.areas import list_areas_tool

        mock_areas = [
            {"area_id": "living_room", "name": "Living Room"},
            {"area_id": "kitchen", "name": "Kitchen"},
        ]

        with patch("app.tools.areas.get_areas", new_callable=AsyncMock, return_value=mock_areas):
            result = await list_areas_tool()

            assert isinstance(result, list)
            assert len(result) == 2

    @pytest.mark.asyncio
    async def test_list_scenes_tool(self):
        """Test list_scenes tool works correctly."""
        from app.tools.scenes import list_scenes_tool

        mock_scenes = [
            {
                "entity_id": "scene.morning",
                "state": "scening",
                "attributes": {"friendly_name": "Morning Scene"},
            }
        ]

        with patch("app.tools.scenes.get_scenes", new_callable=AsyncMock, return_value=mock_scenes):
            result = await list_scenes_tool()

            assert isinstance(result, list)
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_list_integrations_tool(self):
        """Test list_integrations tool works correctly."""
        from app.tools.integrations import list_integrations

        mock_integrations = [
            {
                "entry_id": "abc123",
                "domain": "mqtt",
                "title": "MQTT",
                "state": "loaded",
            }
        ]

        with patch(
            "app.tools.integrations.get_integrations",
            new_callable=AsyncMock,
            return_value=mock_integrations,
        ):
            result = await list_integrations()

            assert isinstance(result, list)
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_system_info_overview(self):
        """Test get_system_info unified tool with overview info_type."""
        from app.tools.unified import get_system_info

        mock_overview = {
            "total_entities": 100,
            "domains": {"light": 10, "switch": 5},
            "version": "2025.3.0",
        }

        with patch(
            "app.api.system.get_system_overview",
            new_callable=AsyncMock,
            return_value=mock_overview,
        ):
            result = await get_system_info(info_type="overview")

            assert isinstance(result, dict)
            assert "total_entities" in result

    @pytest.mark.asyncio
    async def test_list_calendars_tool(self):
        """Test list_calendars tool works correctly."""
        from app.tools.calendars import list_calendars_tool

        mock_calendars = [
            {
                "entity_id": "calendar.google",
                "state": "idle",
                "friendly_name": "Google Calendar",
            }
        ]

        with patch(
            "app.tools.calendars.list_calendars",
            new_callable=AsyncMock,
            return_value=mock_calendars,
        ):
            result = await list_calendars_tool()

            assert isinstance(result, list)
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_list_helpers_tool(self):
        """Test list_helpers tool works correctly."""
        from app.tools.helpers import list_helpers_tool

        mock_helpers = [
            {
                "entity_id": "input_boolean.work_from_home",
                "domain": "input_boolean",
                "state": "on",
            }
        ]

        with patch(
            "app.tools.helpers.list_helpers", new_callable=AsyncMock, return_value=mock_helpers
        ):
            result = await list_helpers_tool()

            assert isinstance(result, list)
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_list_tags_tool(self):
        """Test list_tags tool works correctly."""
        from app.tools.tags import list_tags_tool

        mock_tags = [
            {"tag_id": "ABC123", "name": "Front Door Key"},
            {"tag_id": "XYZ789", "name": "Office Access Card"},
        ]

        with patch("app.tools.tags.list_tags", new_callable=AsyncMock, return_value=mock_tags):
            result = await list_tags_tool()

            assert isinstance(result, list)
            assert len(result) == 2

    @pytest.mark.asyncio
    async def test_manage_webhooks_tool(self):
        """Test manage_webhooks unified tool works correctly."""
        from app.tools.unified import manage_webhooks

        mock_webhooks = [
            {
                "note": "Webhooks are typically defined in configuration.yaml",
                "webhook_url_format": "/api/webhook/{webhook_id}",
            }
        ]

        with patch(
            "app.api.webhooks.list_webhooks",
            new_callable=AsyncMock,
            return_value=mock_webhooks,
        ):
            result = await manage_webhooks(action="list")

            assert isinstance(result, list)
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_list_backups_tool(self):
        """Test list_backups tool works correctly."""
        from app.tools.backups import list_backups_tool

        mock_backups = {
            "available": True,
            "backups": [
                {
                    "slug": "20250101_120000",
                    "name": "Full Backup 2025-01-01",
                    "date": "2025-01-01T12:00:00",
                }
            ],
        }

        with patch(
            "app.tools.backups.list_backups", new_callable=AsyncMock, return_value=mock_backups
        ):
            result = await list_backups_tool()

            assert isinstance(result, dict)
            assert "available" in result
            assert result["available"] is True


class TestMCPToolErrorHandling:
    """Test error handling for MCP tools."""

    @pytest.fixture(autouse=True)
    def mock_config(self):
        """Mock HA_URL and HA_TOKEN for all tests."""
        with (
            patch("app.config.HA_URL", "http://localhost:8123"),
            patch("app.config.HA_TOKEN", "test_token"),
            patch("app.core.decorators.HA_TOKEN", "test_token"),
        ):
            yield

    @pytest.mark.asyncio
    async def test_get_entity_with_nonexistent_entity(self):
        """Test get_entity handles nonexistent entities gracefully."""
        from app.server import get_entity

        error_response = {"error": "Entity not found: light.nonexistent"}

        async def mock_get_entity_state_error(*args, **kwargs):
            return error_response

        with patch("app.api.entities.get_entity_state", side_effect=mock_get_entity_state_error):
            result = await get_entity("light.nonexistent")

            assert isinstance(result, dict)
            assert "error" in result

    @pytest.mark.asyncio
    async def test_search_entities_with_error(self):
        """Test search_entities handles errors gracefully."""
        from app.server import search_entities

        error_response = {"error": "Connection error"}

        with patch(
            "app.api.entities.get_entities", new_callable=AsyncMock, return_value=error_response
        ):
            result = await search_entities(search_mode="keyword")

            assert isinstance(result, dict)
            assert "error" in result


class TestMCPToolImportPaths:
    """Test that all tools can be imported from their new locations."""

    def test_entities_tools_import(self):
        """Test entities tools can be imported from app.tools.entities and app.tools.unified."""
        from app.tools.entities import (
            entity_action,
            get_entity,
        )
        from app.tools.unified import search_entities

        assert callable(get_entity)
        assert callable(entity_action)
        assert callable(search_entities)  # Unified tool

    def test_automations_tools_import(self):
        """Test automations tools can be imported from app.tools.automations."""
        from app.tools.automations import (
            create_automation_tool,
            delete_automation_tool,
            list_automations,
            update_automation_tool,
        )

        assert callable(list_automations)
        assert callable(create_automation_tool)
        assert callable(update_automation_tool)
        assert callable(delete_automation_tool)

    def test_system_tools_import(self):
        """Test system tools can be imported from app.tools.unified."""
        from app.tools.unified import (
            get_system_data,
            get_system_info,
        )

        assert callable(
            get_system_info
        )  # Unified tool replacing get_version, system_overview, system_health, core_config
        assert callable(
            get_system_data
        )  # Unified tool replacing get_error_log, get_cache_statistics, get_history, domain_summary

    def test_api_modules_import(self):
        """Test API modules can be imported correctly."""
        from app.api.entities import get_entities, get_entity_state, summarize_domain
        from app.api.services import call_service
        from app.api.system import get_hass_version

        assert callable(get_entities)
        assert callable(get_entity_state)
        assert callable(summarize_domain)
        assert callable(call_service)
        assert callable(get_hass_version)

    def test_no_hass_imports(self):
        """Test that app.hass module no longer exists."""
        import importlib

        # Verify app.hass doesn't exist
        with pytest.raises((ImportError, ModuleNotFoundError)):
            importlib.import_module("app.hass")

        # Verify we can import from app.api instead
        from app.api import automations, entities, services

        assert entities is not None
        assert automations is not None
        assert services is not None
