"""Unit tests for app.api.automations module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api.automations import (
    create_automation,
    delete_automation,
    disable_automation,
    enable_automation,
    get_automation_config,
    get_automation_execution_log,
    get_automations,
    reload_automations,
    trigger_automation,
    update_automation,
    validate_automation_config,
)
from app.core.cache.manager import get_cache_manager


class TestGetAutomations:
    """Test the get_automations function."""

    @pytest.fixture(autouse=True)
    def mock_config(self):
        """Mock HA_URL and HA_TOKEN for all tests in this class."""
        with (
            patch("app.config.HA_URL", "http://localhost:8123"),
            patch("app.config.HA_TOKEN", "test_token"),
            patch("app.core.decorators.HA_TOKEN", "test_token"),
        ):
            yield

    @pytest.fixture(autouse=True)
    async def clear_cache(self):
        """Clear cache before each test to ensure isolation."""
        cache = await get_cache_manager()
        await cache.clear()
        yield
        await cache.clear()

    @pytest.mark.asyncio
    async def test_get_automations_success(self):
        """Test successful retrieval of automations."""
        mock_automation_entities = [
            {
                "entity_id": "automation.test_automation",
                "state": "on",
                "attributes": {
                    "friendly_name": "Test Automation",
                    "last_triggered": "2025-01-01T10:00:00Z",
                },
            },
            {
                "entity_id": "automation.another_automation",
                "state": "off",
                "attributes": {"friendly_name": "Another Automation"},
            },
        ]

        with patch("app.api.automations.get_entities", return_value=mock_automation_entities):
            result = await get_automations()

            assert isinstance(result, list)
            assert len(result) == 2
            assert result[0]["id"] == "test_automation"
            assert result[0]["entity_id"] == "automation.test_automation"
            assert result[0]["state"] == "on"
            assert result[0]["alias"] == "Test Automation"
            assert result[0]["last_triggered"] == "2025-01-01T10:00:00Z"
            assert result[1]["id"] == "another_automation"
            assert result[1]["alias"] == "Another Automation"

    @pytest.mark.asyncio
    async def test_get_automations_error_response(self):
        """Test handling of error response from get_entities."""
        error_response = {"error": "Connection error"}

        with patch("app.api.automations.get_entities", return_value=error_response):
            result = await get_automations()

            assert isinstance(result, dict)
            assert "error" in result
            assert result["error"] == "Connection error"

    @pytest.mark.asyncio
    async def test_get_automations_processing_error(self):
        """Test handling of processing errors."""
        invalid_entities = [{"invalid": "data"}]  # Missing required fields

        with patch("app.api.automations.get_entities", return_value=invalid_entities):
            result = await get_automations()

            assert isinstance(result, dict)
            assert "error" in result
            assert "Error processing automation entities" in result["error"]


class TestReloadAutomations:
    """Test the reload_automations function."""

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
    async def test_reload_automations_success(self):
        """Test successful reload of automations."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"result": "ok"}
        mock_response.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.api.automations.get_client", return_value=mock_client):
            result = await reload_automations()

            assert result == {"result": "ok"}
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[0][0] == "http://localhost:8123/api/services/automation/reload"
            assert call_args[1]["headers"]["Authorization"] == "Bearer test_token"
            assert call_args[1]["json"] == {}


class TestGetAutomationConfig:
    """Test the get_automation_config function."""

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
    async def test_get_automation_config_success(self):
        """Test successful retrieval of automation config."""
        automation_id = "test_automation"
        mock_config = {
            "id": automation_id,
            "alias": "Test Automation",
            "trigger": [{"platform": "state", "entity_id": "sensor.test"}],
            "action": [{"service": "light.turn_on", "entity_id": "light.test"}],
            "mode": "single",
        }

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = mock_config
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("app.api.automations.get_client", return_value=mock_client):
            result = await get_automation_config(automation_id)

            assert result == mock_config
            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert (
                call_args[0][0]
                == f"http://localhost:8123/api/config/automation/config/{automation_id}"
            )
            assert call_args[1]["headers"]["Authorization"] == "Bearer test_token"


class TestCreateAutomation:
    """Test the create_automation function."""

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
    async def test_create_automation_with_id(self):
        """Test creating automation with provided ID."""
        automation_id = "test_automation"
        config = {
            "id": automation_id,
            "alias": "Test Automation",
            "trigger": [{"platform": "state"}],
            "action": [{"service": "light.turn_on"}],
        }

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"result": "created", "id": automation_id}
        mock_response.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.api.automations.get_client", return_value=mock_client):
            result = await create_automation(config)

            assert result == {"result": "created", "id": automation_id}
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert (
                call_args[0][0]
                == f"http://localhost:8123/api/config/automation/config/{automation_id}"
            )
            assert call_args[1]["headers"]["Authorization"] == "Bearer test_token"
            assert call_args[1]["json"] == config

    @pytest.mark.asyncio
    async def test_create_automation_without_id(self):
        """Test creating automation without ID (generates one)."""
        config = {
            "alias": "Test Automation",
            "trigger": [{"platform": "state"}],
            "action": [{"service": "light.turn_on"}],
        }

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"result": "created"}
        mock_response.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.api.automations.get_client", return_value=mock_client):
            with patch("uuid.uuid4") as mock_uuid:
                mock_uuid.return_value.hex = "12345678"
                result = await create_automation(config)

                assert "id" in config
                assert config["id"] == "automation_12345678"
                mock_client.post.assert_called_once()


class TestUpdateAutomation:
    """Test the update_automation function."""

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
    async def test_update_automation_success(self):
        """Test successful update of automation."""
        automation_id = "test_automation"
        config = {
            "alias": "Updated Automation",
            "trigger": [{"platform": "state"}],
            "action": [{"service": "light.turn_on"}],
        }

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"result": "updated"}
        mock_response.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.api.automations.get_client", return_value=mock_client):
            result = await update_automation(automation_id, config)

            assert result == {"result": "updated"}
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert (
                call_args[0][0]
                == f"http://localhost:8123/api/config/automation/config/{automation_id}"
            )
            assert call_args[1]["headers"]["Authorization"] == "Bearer test_token"
            assert call_args[1]["json"] == config


class TestDeleteAutomation:
    """Test the delete_automation function."""

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
    async def test_delete_automation_success(self):
        """Test successful deletion of automation."""
        automation_id = "test_automation"

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_client.delete = AsyncMock(return_value=mock_response)

        with patch("app.api.automations.get_client", return_value=mock_client):
            result = await delete_automation(automation_id)

            assert result == {"status": "deleted", "automation_id": automation_id}
            mock_client.delete.assert_called_once()
            call_args = mock_client.delete.call_args
            assert (
                call_args[0][0]
                == f"http://localhost:8123/api/config/automation/config/{automation_id}"
            )
            assert call_args[1]["headers"]["Authorization"] == "Bearer test_token"


class TestEnableAutomation:
    """Test the enable_automation function."""

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
    async def test_enable_automation_success(self):
        """Test successful enabling of automation."""
        automation_id = "test_automation"

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"result": "ok"}
        mock_response.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.api.automations.get_client", return_value=mock_client):
            result = await enable_automation(automation_id)

            assert result == {"result": "ok"}
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[0][0] == "http://localhost:8123/api/services/automation/turn_on"
            assert call_args[1]["headers"]["Authorization"] == "Bearer test_token"
            assert call_args[1]["json"] == {"entity_id": f"automation.{automation_id}"}


class TestDisableAutomation:
    """Test the disable_automation function."""

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
    async def test_disable_automation_success(self):
        """Test successful disabling of automation."""
        automation_id = "test_automation"

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"result": "ok"}
        mock_response.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.api.automations.get_client", return_value=mock_client):
            result = await disable_automation(automation_id)

            assert result == {"result": "ok"}
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[0][0] == "http://localhost:8123/api/services/automation/turn_off"
            assert call_args[1]["headers"]["Authorization"] == "Bearer test_token"
            assert call_args[1]["json"] == {"entity_id": f"automation.{automation_id}"}


class TestTriggerAutomation:
    """Test the trigger_automation function."""

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
    async def test_trigger_automation_success(self):
        """Test successful triggering of automation."""
        automation_id = "test_automation"

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"result": "triggered"}
        mock_response.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.api.automations.get_client", return_value=mock_client):
            result = await trigger_automation(automation_id)

            assert result == {"result": "triggered"}
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[0][0] == "http://localhost:8123/api/services/automation/trigger"
            assert call_args[1]["headers"]["Authorization"] == "Bearer test_token"
            assert call_args[1]["json"] == {"entity_id": f"automation.{automation_id}"}


class TestGetAutomationExecutionLog:
    """Test the get_automation_execution_log function."""

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
    async def test_get_automation_execution_log_success(self):
        """Test successful retrieval of automation execution log."""
        automation_id = "test_automation"
        hours = 24
        mock_logbook_data = [
            {
                "when": "2025-01-01T12:00:00",
                "name": "Test Automation",
                "domain": "automation",
                "entity_id": f"automation.{automation_id}",
            },
            {
                "when": "2025-01-01T11:00:00",
                "name": "Test Automation",
                "domain": "automation",
                "entity_id": f"automation.{automation_id}",
            },
        ]

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = mock_logbook_data
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("app.api.automations.get_client", return_value=mock_client):
            result = await get_automation_execution_log(automation_id, hours)

            assert result["automation_id"] == automation_id
            assert result["executions"] == mock_logbook_data
            assert result["count"] == 2
            assert "time_range" in result
            assert "start_time" in result["time_range"]
            assert "end_time" in result["time_range"]

            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert call_args[1]["params"]["entity"] == f"automation.{automation_id}"


class TestValidateAutomationConfig:
    """Test the validate_automation_config function."""

    @pytest.fixture(autouse=True)
    def mock_config(self):
        """Mock HA_TOKEN for all tests in this class."""
        with patch("app.core.decorators.HA_TOKEN", "test_token"):
            yield

    @pytest.mark.asyncio
    async def test_validate_automation_config_valid(self):
        """Test validation of valid automation config."""
        config = {
            "alias": "Test Automation",
            "description": "Test description",
            "trigger": [{"platform": "state", "entity_id": "sensor.test"}],
            "action": [{"service": "light.turn_on", "entity_id": "light.test"}],
            "mode": "single",
        }

        result = await validate_automation_config(config)

        assert result["valid"] is True
        assert len(result["errors"]) == 0
        assert len(result["warnings"]) == 0

    @pytest.mark.asyncio
    async def test_validate_automation_config_missing_trigger(self):
        """Test validation of config missing trigger."""
        config = {
            "alias": "Test Automation",
            "action": [{"service": "light.turn_on"}],
        }

        result = await validate_automation_config(config)

        assert result["valid"] is False
        assert len(result["errors"]) > 0
        assert any("trigger" in error.lower() for error in result["errors"])

    @pytest.mark.asyncio
    async def test_validate_automation_config_missing_action(self):
        """Test validation of config missing action."""
        config = {
            "alias": "Test Automation",
            "trigger": [{"platform": "state"}],
        }

        result = await validate_automation_config(config)

        assert result["valid"] is False
        assert len(result["errors"]) > 0
        assert any("action" in error.lower() for error in result["errors"])

    @pytest.mark.asyncio
    async def test_validate_automation_config_invalid_mode(self):
        """Test validation of config with invalid mode."""
        config = {
            "alias": "Test Automation",
            "trigger": [{"platform": "state"}],
            "action": [{"service": "light.turn_on"}],
            "mode": "invalid_mode",
        }

        result = await validate_automation_config(config)

        assert result["valid"] is False
        assert len(result["errors"]) > 0
        assert any("mode" in error.lower() for error in result["errors"])

    @pytest.mark.asyncio
    async def test_validate_automation_config_missing_alias_warning(self):
        """Test validation of config missing alias generates warning."""
        config = {
            "trigger": [{"platform": "state"}],
            "action": [{"service": "light.turn_on"}],
        }

        result = await validate_automation_config(config)

        assert result["valid"] is True  # Missing alias is just a warning
        assert len(result["warnings"]) > 0
        assert any("alias" in warning.lower() for warning in result["warnings"])
        assert len(result["suggestions"]) > 0

    @pytest.mark.asyncio
    async def test_validate_automation_config_missing_description_warning(self):
        """Test validation of config missing description generates warning."""
        config = {
            "alias": "Test Automation",
            "trigger": [{"platform": "state"}],
            "action": [{"service": "light.turn_on"}],
        }

        result = await validate_automation_config(config)

        assert result["valid"] is True
        assert len(result["warnings"]) > 0
        assert any("description" in warning.lower() for warning in result["warnings"])

    @pytest.mark.asyncio
    async def test_validate_automation_config_invalid_trigger_structure(self):
        """Test validation of config with invalid trigger structure."""
        config = {
            "alias": "Test Automation",
            "trigger": ["invalid_trigger"],  # Should be a list of dicts
            "action": [{"service": "light.turn_on"}],
        }

        result = await validate_automation_config(config)

        assert result["valid"] is False
        assert len(result["errors"]) > 0
        assert any("trigger" in error.lower() for error in result["errors"])

    @pytest.mark.asyncio
    async def test_validate_automation_config_trigger_missing_platform(self):
        """Test validation of trigger missing platform field."""
        config = {
            "alias": "Test Automation",
            "trigger": [{"entity_id": "sensor.test"}],  # Missing platform
            "action": [{"service": "light.turn_on"}],
        }

        result = await validate_automation_config(config)

        assert result["valid"] is False
        assert len(result["errors"]) > 0
        assert any("platform" in error.lower() for error in result["errors"])

    @pytest.mark.asyncio
    async def test_validate_automation_config_empty_action_error(self):
        """Test validation of config with empty action list generates error."""
        config = {
            "alias": "Test Automation",
            "trigger": [{"platform": "state"}],
            "action": [],  # Empty list is treated as missing
        }

        result = await validate_automation_config(config)

        assert result["valid"] is False  # Empty action list is treated as error
        assert len(result["errors"]) > 0
        assert any("action" in error.lower() for error in result["errors"])
