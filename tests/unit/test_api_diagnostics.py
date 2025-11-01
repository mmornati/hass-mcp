"""Unit tests for app.api.diagnostics module."""

from unittest.mock import patch

import pytest

from app.api.diagnostics import (
    analyze_automation_conflicts,
    check_entity_dependencies,
    diagnose_entity,
    get_integration_errors,
)


class TestDiagnoseEntity:
    """Test the diagnose_entity function."""

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
    async def test_diagnose_entity_success_healthy(self):
        """Test successful diagnosis of healthy entity."""
        from datetime import UTC, datetime, timedelta

        # Use recent timestamp (30 minutes ago, well within 1 hour threshold)
        recent_time = datetime.now(UTC) - timedelta(minutes=30)
        recent_timestamp = recent_time.isoformat().replace("+00:00", "Z")

        mock_entity = {
            "entity_id": "light.living_room",
            "state": "on",
            "last_updated": recent_timestamp,
            "attributes": {},
        }

        mock_integrations = [
            {"domain": "light", "state": "loaded"},
        ]

        mock_history = [
            [
                {"state": "on", "last_changed": recent_timestamp},
                {"state": "off", "last_changed": recent_timestamp},
            ]
        ]

        with (
            patch("app.api.diagnostics.get_entity_state", return_value=mock_entity),
            patch("app.api.diagnostics.get_integrations", return_value=mock_integrations),
            patch("app.api.diagnostics.get_entity_history", return_value=mock_history),
        ):
            result = await diagnose_entity("light.living_room")

            assert isinstance(result, dict)
            assert result["entity_id"] == "light.living_room"
            assert "status" in result
            assert "issues" in result
            assert "recommendations" in result
            assert result["status"]["entity_state"] == "on"
            # Should have no issues if entity is healthy and recently updated
            # (unless last_updated_age_seconds > 3600, which we avoid with recent timestamp)
            assert len(result["issues"]) == 0  # Healthy entity should have no issues

    @pytest.mark.asyncio
    async def test_diagnose_entity_unavailable(self):
        """Test diagnosis of unavailable entity."""
        mock_entity = {
            "entity_id": "light.living_room",
            "state": "unavailable",
            "last_updated": "2025-01-01T12:00:00Z",
            "attributes": {},
        }

        mock_integrations = [
            {"domain": "light", "state": "loaded"},
        ]

        mock_history = []

        with (
            patch("app.api.diagnostics.get_entity_state", return_value=mock_entity),
            patch("app.api.diagnostics.get_integrations", return_value=mock_integrations),
            patch("app.api.diagnostics.get_entity_history", return_value=mock_history),
        ):
            result = await diagnose_entity("light.living_room")

            assert isinstance(result, dict)
            assert result["entity_id"] == "light.living_room"
            assert "Entity is unavailable" in result["issues"]
            assert len(result["recommendations"]) > 0

    @pytest.mark.asyncio
    async def test_diagnose_entity_stale_data(self):
        """Test diagnosis of entity with stale data."""
        from datetime import UTC, datetime, timedelta

        # Entity last updated 2 hours ago
        stale_time = (datetime.now(UTC) - timedelta(hours=2)).isoformat().replace("+00:00", "Z")

        mock_entity = {
            "entity_id": "sensor.temperature",
            "state": "20.5",
            "last_updated": stale_time,
            "attributes": {},
        }

        mock_integrations = [
            {"domain": "sensor", "state": "loaded"},
        ]

        mock_history = []

        with (
            patch("app.api.diagnostics.get_entity_state", return_value=mock_entity),
            patch("app.api.diagnostics.get_integrations", return_value=mock_integrations),
            patch("app.api.diagnostics.get_entity_history", return_value=mock_history),
        ):
            result = await diagnose_entity("sensor.temperature")

            assert isinstance(result, dict)
            assert "hasn't updated" in " ".join(result["issues"])

    @pytest.mark.asyncio
    async def test_diagnose_entity_integration_error(self):
        """Test diagnosis when integration has errors."""
        mock_entity = {
            "entity_id": "light.living_room",
            "state": "unavailable",
            "last_updated": "2025-01-01T12:00:00Z",
            "attributes": {},
        }

        mock_integrations = [
            {"domain": "light", "state": "setup_error"},
        ]

        mock_history = []

        with (
            patch("app.api.diagnostics.get_entity_state", return_value=mock_entity),
            patch("app.api.diagnostics.get_integrations", return_value=mock_integrations),
            patch("app.api.diagnostics.get_entity_history", return_value=mock_history),
        ):
            result = await diagnose_entity("light.living_room")

            assert isinstance(result, dict)
            assert any("Integration light is in state" in issue for issue in result["issues"])

    @pytest.mark.asyncio
    async def test_diagnose_entity_not_found(self):
        """Test diagnosis when entity not found."""
        mock_error = {"error": "Entity not found"}

        with patch("app.api.diagnostics.get_entity_state", return_value=mock_error):
            result = await diagnose_entity("light.nonexistent")

            assert isinstance(result, dict)
            assert "error" in result["issues"][0] or "not found" in " ".join(result["issues"])

    @pytest.mark.asyncio
    async def test_diagnose_entity_history_errors(self):
        """Test diagnosis when entity has error states in history."""
        mock_entity = {
            "entity_id": "light.living_room",
            "state": "on",
            "last_updated": "2025-01-01T12:00:00Z",
            "attributes": {},
        }

        mock_integrations = [
            {"domain": "light", "state": "loaded"},
        ]

        mock_history = [
            [
                {"state": "on", "last_changed": "2025-01-01T12:00:00Z"},
                {"state": "unavailable", "last_changed": "2025-01-01T11:00:00Z"},
                {"state": "error", "last_changed": "2025-01-01T10:00:00Z"},
            ]
        ]

        with (
            patch("app.api.diagnostics.get_entity_state", return_value=mock_entity),
            patch("app.api.diagnostics.get_integrations", return_value=mock_integrations),
            patch("app.api.diagnostics.get_entity_history", return_value=mock_history),
        ):
            result = await diagnose_entity("light.living_room")

            assert isinstance(result, dict)
            assert any("error/unavailable states" in issue for issue in result["issues"])


class TestCheckEntityDependencies:
    """Test the check_entity_dependencies function."""

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
    async def test_check_entity_dependencies_success(self):
        """Test successful dependency check."""
        mock_automations = [
            {"entity_id": "automation.turn_on_lights", "alias": "Turn on lights"},
        ]

        mock_automation_config = {
            "action": [
                {"service": "light.turn_on", "entity_id": "light.living_room"},
            ]
        }

        mock_scripts = [
            {"entity_id": "script.lights_on", "friendly_name": "Lights On"},
        ]

        mock_script_config = {
            "sequence": [
                {"service": "light.turn_on", "entity_id": "light.living_room"},
            ]
        }

        mock_scenes = [
            {
                "entity_id": "scene.living_room_dim",
                "friendly_name": "Living Room Dim",
                "entity_id_list": ["light.living_room"],
            }
        ]

        with (
            patch("app.api.diagnostics.get_automations", return_value=mock_automations),
            patch("app.api.diagnostics.get_automation_config", return_value=mock_automation_config),
            patch("app.api.diagnostics.get_scripts", return_value=mock_scripts),
            patch("app.api.diagnostics.get_script_config", return_value=mock_script_config),
            patch("app.api.diagnostics.get_scenes", return_value=mock_scenes),
        ):
            result = await check_entity_dependencies("light.living_room")

            assert isinstance(result, dict)
            assert result["entity_id"] == "light.living_room"
            assert "automations" in result
            assert "scripts" in result
            assert "scenes" in result
            assert len(result["automations"]) == 1
            assert len(result["scripts"]) == 1
            assert len(result["scenes"]) == 1

    @pytest.mark.asyncio
    async def test_check_entity_dependencies_no_dependencies(self):
        """Test dependency check with no dependencies."""
        mock_automations = []
        mock_scripts = []
        mock_scenes = []

        with (
            patch("app.api.diagnostics.get_automations", return_value=mock_automations),
            patch("app.api.diagnostics.get_scripts", return_value=mock_scripts),
            patch("app.api.diagnostics.get_scenes", return_value=mock_scenes),
        ):
            result = await check_entity_dependencies("light.unused")

            assert isinstance(result, dict)
            assert result["entity_id"] == "light.unused"
            assert len(result["automations"]) == 0
            assert len(result["scripts"]) == 0
            assert len(result["scenes"]) == 0

    @pytest.mark.asyncio
    async def test_check_entity_dependencies_automations_error(self):
        """Test dependency check when automations API returns error."""
        mock_error = {"error": "Could not get automations"}

        with patch("app.api.diagnostics.get_automations", return_value=mock_error):
            result = await check_entity_dependencies("light.living_room")

            assert isinstance(result, dict)
            assert len(result["automations"]) == 0
            assert len(result["scripts"]) == 0
            assert len(result["scenes"]) == 0


class TestAnalyzeAutomationConflicts:
    """Test the analyze_automation_conflicts function."""

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
    async def test_analyze_automation_conflicts_no_conflicts(self):
        """Test conflict analysis with no conflicts."""
        mock_automations = [
            {"entity_id": "automation.turn_on", "alias": "Turn on"},
        ]

        mock_automation_config = {
            "action": [
                {"service": "light.turn_on", "entity_id": "light.living_room"},
            ]
        }

        with (
            patch("app.api.diagnostics.get_automations", return_value=mock_automations),
            patch("app.api.diagnostics.get_automation_config", return_value=mock_automation_config),
        ):
            result = await analyze_automation_conflicts()

            assert isinstance(result, dict)
            assert "total_automations" in result
            assert "conflicts" in result
            assert "warnings" in result
            assert len(result["conflicts"]) == 0

    @pytest.mark.asyncio
    async def test_analyze_automation_conflicts_opposing_actions(self):
        """Test conflict analysis with opposing actions."""
        mock_automations = [
            {"entity_id": "automation.turn_on", "alias": "Turn on"},
            {"entity_id": "automation.turn_off", "alias": "Turn off"},
        ]

        mock_config_turn_on = {
            "action": [
                {"service": "light.turn_on", "entity_id": "light.living_room"},
            ]
        }

        mock_config_turn_off = {
            "action": [
                {"service": "light.turn_off", "entity_id": "light.living_room"},
            ]
        }

        def get_config_side_effect(automation_id):
            if "turn_on" in automation_id:
                return mock_config_turn_on
            return mock_config_turn_off

        with (
            patch("app.api.diagnostics.get_automations", return_value=mock_automations),
            patch("app.api.diagnostics.get_automation_config", side_effect=get_config_side_effect),
        ):
            result = await analyze_automation_conflicts()

            assert isinstance(result, dict)
            assert len(result["conflicts"]) > 0
            assert any(
                "opposing_actions" in conflict.get("type", "") for conflict in result["conflicts"]
            )

    @pytest.mark.asyncio
    async def test_analyze_automation_conflicts_automations_error(self):
        """Test conflict analysis when automations API returns error."""
        mock_error = {"error": "Could not get automations"}

        with patch("app.api.diagnostics.get_automations", return_value=mock_error):
            result = await analyze_automation_conflicts()

            assert isinstance(result, dict)
            assert "error" in result
            assert result["total_automations"] == 0


class TestGetIntegrationErrors:
    """Test the get_integration_errors function."""

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
    async def test_get_integration_errors_success(self):
        """Test successful retrieval of integration errors."""
        mock_error_log = {
            "log_text": """2024-01-01 12:00:00 ERROR (MainThread) [homeassistant.components.hue] Connection failed
2024-01-01 12:00:01 ERROR (MainThread) [homeassistant.components.mqtt] Failed to connect
2024-01-01 12:00:02 INFO (MainThread) [homeassistant.components.light] Loaded""",
            "error_count": 2,
            "warning_count": 0,
        }

        with patch("app.api.diagnostics.get_hass_error_log", return_value=mock_error_log):
            result = await get_integration_errors()

            assert isinstance(result, dict)
            assert "integration_errors" in result
            assert "total_integrations_with_errors" in result
            assert "note" in result
            assert "hue" in result["integration_errors"]
            assert "mqtt" in result["integration_errors"]
            assert result["total_integrations_with_errors"] == 2

    @pytest.mark.asyncio
    async def test_get_integration_errors_filtered_by_domain(self):
        """Test integration errors filtered by domain."""
        mock_error_log = {
            "log_text": """2024-01-01 12:00:00 ERROR (MainThread) [homeassistant.components.hue] Connection failed
2024-01-01 12:00:01 ERROR (MainThread) [homeassistant.components.mqtt] Failed to connect""",
            "error_count": 2,
            "warning_count": 0,
        }

        with patch("app.api.diagnostics.get_hass_error_log", return_value=mock_error_log):
            result = await get_integration_errors(domain="hue")

            assert isinstance(result, dict)
            assert "hue" in result["integration_errors"]
            assert "mqtt" not in result["integration_errors"]
            assert result["total_integrations_with_errors"] == 1

    @pytest.mark.asyncio
    async def test_get_integration_errors_no_errors(self):
        """Test integration errors with no errors in log."""
        mock_error_log = {
            "log_text": """2024-01-01 12:00:00 INFO (MainThread) [homeassistant.components.light] Loaded
2024-01-01 12:00:01 INFO (MainThread) [homeassistant.components.sensor] Loaded""",
            "error_count": 0,
            "warning_count": 0,
        }

        with patch("app.api.diagnostics.get_hass_error_log", return_value=mock_error_log):
            result = await get_integration_errors()

            assert isinstance(result, dict)
            assert result["total_integrations_with_errors"] == 0
            assert len(result["integration_errors"]) == 0

    @pytest.mark.asyncio
    async def test_get_integration_errors_error_log_error(self):
        """Test integration errors when error log API returns error."""
        mock_error = {"error": "Could not get error log"}

        with patch("app.api.diagnostics.get_hass_error_log", return_value=mock_error):
            result = await get_integration_errors()

            assert isinstance(result, dict)
            assert "error" in result
            assert result["total_integrations_with_errors"] == 0

    @pytest.mark.asyncio
    async def test_get_integration_errors_exception_in_line(self):
        """Test integration errors with exception in log line."""
        mock_error_log = {
            "log_text": """2024-01-01 12:00:00 ERROR (MainThread) [homeassistant.components.hue] Connection failed
Exception: Traceback (most recent call last):
  File "homeassistant/components/hue/__init__.py", line 42, in setup
    raise ConnectionError
ConnectionError""",
            "error_count": 1,
            "warning_count": 0,
        }

        with patch("app.api.diagnostics.get_hass_error_log", return_value=mock_error_log):
            result = await get_integration_errors()

            assert isinstance(result, dict)
            assert "hue" in result["integration_errors"]
            assert result["total_integrations_with_errors"] == 1
