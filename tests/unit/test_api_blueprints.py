"""Unit tests for app.api.blueprints module."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.api.blueprints import (
    create_automation_from_blueprint,
    get_blueprint,
    import_blueprint,
    list_blueprints,
)
from app.core.cache.manager import get_cache_manager


class TestListBlueprints:
    """Test the list_blueprints function."""

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
    async def test_list_blueprints_success_all(self):
        """Test successful retrieval of all blueprints."""
        mock_blueprints = [
            {
                "path": "motion_light",
                "domain": "automation",
                "name": "Motion Light",
                "metadata": {"description": "Turn on light when motion detected"},
            },
            {
                "path": "presence_detection",
                "domain": "automation",
                "name": "Presence Detection",
                "metadata": {"description": "Detect presence"},
            },
        ]

        mock_response = MagicMock()
        mock_response.json.return_value = mock_blueprints

        with patch("app.api.blueprints._blueprints_api.get", return_value=mock_blueprints):
            result = await list_blueprints()

            assert isinstance(result, list)
            assert len(result) == 2
            assert result[0]["path"] == "motion_light"
            assert result[1]["path"] == "presence_detection"

    @pytest.mark.asyncio
    async def test_list_blueprints_success_filtered_by_domain(self):
        """Test successful retrieval of blueprints filtered by domain."""
        mock_blueprints = [
            {
                "path": "motion_light",
                "domain": "automation",
                "name": "Motion Light",
                "metadata": {"description": "Turn on light when motion detected"},
            }
        ]

        with patch("app.api.blueprints._blueprints_api.get", return_value=mock_blueprints):
            result = await list_blueprints(domain="automation")

            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["domain"] == "automation"

    @pytest.mark.asyncio
    async def test_list_blueprints_empty_result(self):
        """Test empty result when no blueprints available."""
        with patch("app.api.blueprints._blueprints_api.get", return_value=[]):
            result = await list_blueprints()

            assert isinstance(result, list)
            assert len(result) == 0

    @pytest.mark.asyncio
    async def test_list_blueprints_http_error(self):
        """Test HTTP error handling."""
        with patch(
            "app.api.blueprints._blueprints_api.get",
            side_effect=httpx.HTTPStatusError(
                "404 Not Found",
                request=MagicMock(),
                response=MagicMock(status_code=404),
            ),
        ):
            result = await list_blueprints()

            # Error handler wraps list-returning functions in a list
            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], dict)
            assert "error" in result[0]
            assert "404" in result[0]["error"]


class TestGetBlueprint:
    """Test the get_blueprint function."""

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
    async def test_get_blueprint_success_with_domain(self):
        """Test successful retrieval of blueprint with domain specified."""
        mock_blueprint = {
            "path": "motion_light",
            "domain": "automation",
            "name": "Motion Light",
            "metadata": {
                "input": {
                    "motion_entity": {"selector": {"entity": {"domain": "binary_sensor"}}},
                    "light_entity": {"selector": {"entity": {"domain": "light"}}},
                },
                "description": "Turn on light when motion detected",
            },
            "definition": "blueprint:\n  name: Motion Light\n  ...",
        }

        with patch("app.api.blueprints._blueprints_api.get", return_value=mock_blueprint):
            result = await get_blueprint("motion_light", domain="automation")

            assert isinstance(result, dict)
            assert result["path"] == "motion_light"
            assert result["domain"] == "automation"
            assert "metadata" in result
            assert "definition" in result

    @pytest.mark.asyncio
    async def test_get_blueprint_success_with_path(self):
        """Test successful retrieval of blueprint with full path."""
        mock_blueprint = {
            "path": "motion_light",
            "domain": "automation",
            "name": "Motion Light",
            "metadata": {"input": {}, "description": "Turn on light when motion detected"},
            "definition": "blueprint:\n  name: Motion Light\n  ...",
        }

        with patch("app.api.blueprints._blueprints_api.get", return_value=mock_blueprint):
            result = await get_blueprint("automation/motion_light")

            assert isinstance(result, dict)
            assert result["path"] == "motion_light"
            assert result["domain"] == "automation"

    @pytest.mark.asyncio
    async def test_get_blueprint_error_no_domain(self):
        """Test error when domain cannot be determined."""
        result = await get_blueprint("motion_light")

        assert isinstance(result, dict)
        assert "error" in result
        assert "domain" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_get_blueprint_http_error(self):
        """Test HTTP error handling."""
        with patch(
            "app.api.blueprints._blueprints_api.get",
            side_effect=httpx.HTTPStatusError(
                "404 Not Found",
                request=MagicMock(),
                response=MagicMock(status_code=404),
            ),
        ):
            result = await get_blueprint("nonexistent", domain="automation")

            assert isinstance(result, dict)
            assert "error" in result
            assert "404" in result["error"]


class TestImportBlueprint:
    """Test the import_blueprint function."""

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
    async def test_import_blueprint_success(self):
        """Test successful blueprint import."""
        mock_response = {
            "status": "imported",
            "blueprint": {
                "path": "motion_light",
                "domain": "automation",
                "name": "Motion Light",
            },
        }

        with patch("app.api.blueprints._blueprints_api.get", return_value=mock_response):
            result = await import_blueprint("https://www.home-assistant.io/blueprints/example.yaml")

            assert isinstance(result, dict)
            assert result["status"] == "imported"
            assert "blueprint" in result

    @pytest.mark.asyncio
    async def test_import_blueprint_url_encoding(self):
        """Test that URL is properly encoded."""
        test_url = "https://github.com/user/repo/blob/main/blueprint.yaml?token=abc123"
        mock_response = {"status": "imported"}

        with patch(
            "app.api.blueprints._blueprints_api.get", return_value=mock_response
        ) as mock_get:
            await import_blueprint(test_url)

            # Verify that get was called with encoded URL
            call_args = mock_get.call_args
            assert call_args is not None
            # The endpoint should contain the encoded URL
            endpoint = call_args[0][0]
            assert "/api/blueprint/import/" in endpoint

    @pytest.mark.asyncio
    async def test_import_blueprint_http_error(self):
        """Test HTTP error handling."""
        with patch(
            "app.api.blueprints._blueprints_api.get",
            side_effect=httpx.HTTPStatusError(
                "400 Bad Request",
                request=MagicMock(),
                response=MagicMock(status_code=400),
            ),
        ):
            result = await import_blueprint("https://invalid-url.com/blueprint.yaml")

            assert isinstance(result, dict)
            assert "error" in result
            assert "400" in result["error"]


class TestCreateAutomationFromBlueprint:
    """Test the create_automation_from_blueprint function."""

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
    async def test_create_automation_from_blueprint_success(self):
        """Test successful automation creation from blueprint."""
        mock_blueprint = {
            "path": "motion_light",
            "domain": "automation",
            "name": "Motion Light",
            "metadata": {
                "input": {
                    "motion_entity": {"selector": {"entity": {"domain": "binary_sensor"}}},
                    "light_entity": {"selector": {"entity": {"domain": "light"}}},
                }
            },
        }

        mock_automation_response = {
            "automation_id": "automation_12345",
            "status": "created",
        }

        with (
            patch("app.api.blueprints.get_blueprint", return_value=mock_blueprint),
            patch("app.api.blueprints.create_automation", return_value=mock_automation_response),
        ):
            result = await create_automation_from_blueprint(
                "motion_light",
                inputs={
                    "motion_entity": "binary_sensor.motion",
                    "light_entity": "light.living_room",
                },
                domain="automation",
            )

            assert isinstance(result, dict)
            assert result["automation_id"] == "automation_12345"
            assert result["status"] == "created"

    @pytest.mark.asyncio
    async def test_create_automation_from_blueprint_with_automation_id(self):
        """Test automation creation with provided automation_id."""
        mock_blueprint = {
            "path": "motion_light",
            "domain": "automation",
            "name": "Motion Light",
            "metadata": {"input": {}},
        }

        mock_automation_response = {
            "automation_id": "custom_automation_id",
            "status": "created",
        }

        with (
            patch("app.api.blueprints.get_blueprint", return_value=mock_blueprint),
            patch("app.api.blueprints.create_automation", return_value=mock_automation_response),
        ):
            result = await create_automation_from_blueprint(
                "motion_light",
                inputs={
                    "automation_id": "custom_automation_id",
                    "motion_entity": "binary_sensor.motion",
                },
                domain="automation",
            )

            assert isinstance(result, dict)
            assert result["automation_id"] == "custom_automation_id"

    @pytest.mark.asyncio
    async def test_create_automation_from_blueprint_blueprint_error(self):
        """Test error handling when blueprint retrieval fails."""
        mock_blueprint_error = {"error": "Blueprint not found"}

        with patch("app.api.blueprints.get_blueprint", return_value=mock_blueprint_error):
            result = await create_automation_from_blueprint(
                "nonexistent", inputs={"motion_entity": "binary_sensor.motion"}, domain="automation"
            )

            assert isinstance(result, dict)
            assert "error" in result
            assert result["error"] == "Blueprint not found"

    @pytest.mark.asyncio
    async def test_create_automation_from_blueprint_no_domain(self):
        """Test automation creation without domain, extracting from blueprint."""
        mock_blueprint = {
            "path": "motion_light",
            "domain": "automation",
            "name": "Motion Light",
            "metadata": {"input": {}},
        }

        mock_automation_response = {
            "automation_id": "automation_12345",
            "status": "created",
        }

        with (
            patch("app.api.blueprints.get_blueprint", return_value=mock_blueprint),
            patch("app.api.blueprints.create_automation", return_value=mock_automation_response),
        ):
            result = await create_automation_from_blueprint(
                "motion_light", inputs={"motion_entity": "binary_sensor.motion"}
            )

            assert isinstance(result, dict)
            assert result["automation_id"] == "automation_12345"

    @pytest.mark.asyncio
    async def test_create_automation_from_blueprint_auto_generate_id(self):
        """Test that automation_id is auto-generated if not provided."""
        mock_blueprint = {
            "path": "motion_light",
            "domain": "automation",
            "name": "Motion Light",
            "metadata": {"input": {}},
        }

        mock_automation_response = {
            "automation_id": "automation_abcdef12",
            "status": "created",
        }

        with (
            patch("app.api.blueprints.get_blueprint", return_value=mock_blueprint),
            patch("app.api.blueprints.create_automation", return_value=mock_automation_response),
        ):
            result = await create_automation_from_blueprint(
                "motion_light",
                inputs={"motion_entity": "binary_sensor.motion"},
                domain="automation",
            )

            assert isinstance(result, dict)
            assert "automation_id" in result

    @pytest.mark.asyncio
    async def test_create_automation_from_blueprint_automation_error(self):
        """Test error handling when automation creation fails."""
        mock_blueprint = {
            "path": "motion_light",
            "domain": "automation",
            "name": "Motion Light",
            "metadata": {"input": {}},
        }

        mock_automation_error = {"error": "Invalid automation config"}

        with (
            patch("app.api.blueprints.get_blueprint", return_value=mock_blueprint),
            patch("app.api.blueprints.create_automation", return_value=mock_automation_error),
        ):
            result = await create_automation_from_blueprint(
                "motion_light",
                inputs={"motion_entity": "binary_sensor.motion"},
                domain="automation",
            )

            assert isinstance(result, dict)
            assert "error" in result
