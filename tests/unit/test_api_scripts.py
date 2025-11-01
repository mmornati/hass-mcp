"""Unit tests for app.api.scripts module."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.api.scripts import (
    get_script_config,
    get_scripts,
    reload_scripts,
    run_script,
)


class TestGetScripts:
    """Test the get_scripts function."""

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
    async def test_get_scripts_success(self):
        """Test successful retrieval of scripts."""
        mock_script_entities = [
            {
                "entity_id": "script.turn_on_lights",
                "state": "idle",
                "attributes": {
                    "friendly_name": "Turn on lights",
                    "alias": "Turn on lights",
                    "last_triggered": "2025-01-01T10:00:00Z",
                },
            },
            {
                "entity_id": "script.notify_user",
                "state": "running",
                "attributes": {"friendly_name": "Notify user"},
            },
        ]

        with patch("app.api.scripts.get_entities", return_value=mock_script_entities):
            result = await get_scripts()

            assert isinstance(result, list)
            assert len(result) == 2
            assert result[0]["entity_id"] == "script.turn_on_lights"
            assert result[0]["state"] == "idle"
            assert result[0]["friendly_name"] == "Turn on lights"
            assert result[0]["alias"] == "Turn on lights"
            assert result[0]["last_triggered"] == "2025-01-01T10:00:00Z"
            assert result[1]["entity_id"] == "script.notify_user"
            assert result[1]["state"] == "running"
            assert result[1]["friendly_name"] == "Notify user"

    @pytest.mark.asyncio
    async def test_get_scripts_error_response(self):
        """Test handling of error response from get_entities."""
        error_response = {"error": "Connection error"}

        with patch("app.api.scripts.get_entities", return_value=error_response):
            result = await get_scripts()

            assert isinstance(result, dict)
            assert "error" in result
            assert result["error"] == "Connection error"

    @pytest.mark.asyncio
    async def test_get_scripts_processing_error(self):
        """Test handling of processing errors."""
        # Test with entity that will raise KeyError when accessing nested attributes
        invalid_entities = [{"entity_id": "script.test", "state": "idle", "attributes": None}]

        with patch("app.api.scripts.get_entities", return_value=invalid_entities):
            result = await get_scripts()

            # When processing fails due to invalid structure, function returns error dict
            assert isinstance(result, dict)
            assert "error" in result
            assert "Error processing script entities" in result["error"]


class TestGetScriptConfig:
    """Test the get_script_config function."""

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
    async def test_get_script_config_via_config_api(self):
        """Test getting script config via config API."""
        script_id = "test_script"
        mock_config_data = {
            "sequence": [{"service": "light.turn_on", "entity_id": "light.test"}],
            "alias": "Test Script",
        }
        mock_entity = {
            "entity_id": "script.test_script",
            "state": "idle",
            "attributes": {"friendly_name": "Test Script"},
        }

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_config_data
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("app.api.scripts.get_client", return_value=mock_client):
            with patch("app.api.scripts.get_entity_state", return_value=mock_entity):
                result = await get_script_config(script_id)

                assert result["sequence"] == mock_config_data["sequence"]
                assert result["entity"] == mock_entity
                mock_client.get.assert_called_once()
                call_args = mock_client.get.call_args
                assert call_args[0][0] == f"http://localhost:8123/api/config/scripts/{script_id}"
                assert call_args[1]["headers"]["Authorization"] == "Bearer test_token"

    @pytest.mark.asyncio
    async def test_get_script_config_fallback_to_entity_state(self):
        """Test fallback to entity state when config API unavailable."""
        script_id = "test_script"
        mock_entity = {
            "entity_id": "script.test_script",
            "state": "idle",
            "attributes": {"friendly_name": "Test Script"},
        }

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 404  # Config API not available
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("app.api.scripts.get_client", return_value=mock_client):
            with patch("app.api.scripts.get_entity_state", return_value=mock_entity):
                result = await get_script_config(script_id)

                assert result == mock_entity
                assert result["entity_id"] == "script.test_script"

    @pytest.mark.asyncio
    async def test_get_script_config_exception_fallback(self):
        """Test fallback when exception occurs."""
        script_id = "test_script"
        mock_entity = {
            "entity_id": "script.test_script",
            "state": "idle",
            "attributes": {"friendly_name": "Test Script"},
        }

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=Exception("API error"))

        with patch("app.api.scripts.get_client", return_value=mock_client):
            with patch("app.api.scripts.get_entity_state", return_value=mock_entity):
                result = await get_script_config(script_id)

                assert result == mock_entity


class TestRunScript:
    """Test the run_script function."""

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
    async def test_run_script_without_variables(self):
        """Test running script without variables."""
        script_id = "turn_on_lights"

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.api.scripts.get_client", return_value=mock_client):
            result = await run_script(script_id)

            assert result == {}
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[0][0] == f"http://localhost:8123/api/services/script/{script_id}"
            assert call_args[1]["headers"]["Authorization"] == "Bearer test_token"
            assert call_args[1]["json"] == {}

    @pytest.mark.asyncio
    async def test_run_script_with_variables(self):
        """Test running script with variables."""
        script_id = "notify_user"
        variables = {"message": "Hello", "target": "user1"}

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.api.scripts.get_client", return_value=mock_client):
            result = await run_script(script_id, variables)

            assert result == {}
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[0][0] == f"http://localhost:8123/api/services/script/{script_id}"
            assert call_args[1]["headers"]["Authorization"] == "Bearer test_token"
            assert call_args[1]["json"] == {"variables": variables}


class TestReloadScripts:
    """Test the reload_scripts function."""

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
    async def test_reload_scripts_success(self):
        """Test successful reload of scripts."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.api.scripts.get_client", return_value=mock_client):
            result = await reload_scripts()

            assert result == {}
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[0][0] == "http://localhost:8123/api/services/script/reload"
            assert call_args[1]["headers"]["Authorization"] == "Bearer test_token"
            assert call_args[1]["json"] == {}

    @pytest.mark.asyncio
    async def test_reload_scripts_http_error(self):
        """Test reload scripts with HTTP error."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not found", request=MagicMock(), response=mock_response
        )
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.api.scripts.get_client", return_value=mock_client):
            result = await reload_scripts()

            assert isinstance(result, dict)
            assert "error" in result
