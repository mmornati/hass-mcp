"""Unit tests for app.api.tags module."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.api.tags import (
    create_tag,
    delete_tag,
    get_tag_automations,
    list_tags,
)
from app.core.cache.manager import get_cache_manager


class TestListTags:
    """Test the list_tags function."""

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
    async def test_list_tags_success(self):
        """Test successful retrieval of tags."""
        mock_tags = [
            {
                "tag_id": "ABC123",
                "name": "Front Door Key",
                "last_scanned": "2025-01-01T10:00:00",
                "device_id": "device_123",
            },
            {
                "tag_id": "XYZ789",
                "name": "Office Access Card",
                "last_scanned": "2025-01-01T11:00:00",
                "device_id": "device_456",
            },
        ]

        with patch("app.api.tags._tags_api.get", return_value=mock_tags) as mock_get:
            result = await list_tags()

            assert isinstance(result, list)
            assert len(result) == 2
            assert result[0]["tag_id"] == "ABC123"
            assert result[0]["name"] == "Front Door Key"
            assert result[1]["tag_id"] == "XYZ789"
            mock_get.assert_called_with("/api/tag")

    @pytest.mark.asyncio
    async def test_list_tags_empty(self):
        """Test retrieval when no tags are configured."""
        with patch("app.api.tags._tags_api.get", return_value=[]):
            result = await list_tags()

            assert isinstance(result, list)
            assert len(result) == 0


class TestCreateTag:
    """Test the create_tag function."""

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
    async def test_create_tag_success(self):
        """Test successful creation of a tag."""
        mock_response = {"tag_id": "ABC123", "name": "Front Door Key"}

        with patch("app.api.tags._tags_api.post", return_value=mock_response) as mock_post:
            result = await create_tag("ABC123", "Front Door Key")

            assert isinstance(result, dict)
            assert result["tag_id"] == "ABC123"
            assert result["name"] == "Front Door Key"
            mock_post.assert_called_with(
                "/api/tag",
                data={"tag_id": "ABC123", "name": "Front Door Key"},
            )

    @pytest.mark.asyncio
    async def test_create_tag_http_error(self):
        """Test HTTP error handling during tag creation."""
        with patch(
            "app.api.tags._tags_api.post",
            side_effect=httpx.HTTPStatusError(
                "400 Bad Request",
                request=MagicMock(),
                response=MagicMock(status_code=400),
            ),
        ):
            result = await create_tag("ABC123", "Front Door Key")

            assert isinstance(result, dict)
            assert "error" in result
            assert "400" in result["error"]


class TestDeleteTag:
    """Test the delete_tag function."""

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
    async def test_delete_tag_success(self):
        """Test successful deletion of a tag."""
        mock_response = {"message": "Tag deleted successfully"}

        with patch("app.api.tags._tags_api.delete", return_value=mock_response) as mock_delete:
            result = await delete_tag("ABC123")

            assert isinstance(result, dict)
            assert result["message"] == "Tag deleted successfully"
            mock_delete.assert_called_with("/api/tag/ABC123")

    @pytest.mark.asyncio
    async def test_delete_tag_http_error(self):
        """Test HTTP error handling during tag deletion."""
        with patch(
            "app.api.tags._tags_api.delete",
            side_effect=httpx.HTTPStatusError(
                "404 Not Found",
                request=MagicMock(),
                response=MagicMock(status_code=404),
            ),
        ):
            result = await delete_tag("ABC123")

            assert isinstance(result, dict)
            assert "error" in result
            assert "404" in result["error"]


class TestGetTagAutomations:
    """Test the get_tag_automations function."""

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
    async def test_get_tag_automations_success(self):
        """Test successful retrieval of tag automations."""
        mock_automations = [
            {
                "entity_id": "automation.front_door_unlock",
                "state": "on",
                "attributes": {"friendly_name": "Front Door Unlock"},
            }
        ]

        mock_config = {
            "alias": "Front Door Unlock",
            "trigger": [
                {
                    "platform": "tag",
                    "tag_id": "ABC123",
                }
            ],
            "action": [],
        }

        with (
            patch("app.api.tags.get_automations", return_value=mock_automations),
            patch("app.api.tags.get_automation_config", return_value=mock_config),
        ):
            result = await get_tag_automations("ABC123")

            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["automation_id"] == "automation.front_door_unlock"
            assert result[0]["alias"] == "Front Door Unlock"
            assert result[0]["enabled"] is True

    @pytest.mark.asyncio
    async def test_get_tag_automations_empty(self):
        """Test when no automations use the tag."""
        mock_automations = [
            {
                "entity_id": "automation.other",
                "state": "on",
                "attributes": {"friendly_name": "Other Automation"},
            }
        ]

        mock_config = {
            "alias": "Other Automation",
            "trigger": [
                {
                    "platform": "state",
                    "entity_id": "light.living_room",
                }
            ],
            "action": [],
        }

        with (
            patch("app.api.tags.get_automations", return_value=mock_automations),
            patch("app.api.tags.get_automation_config", return_value=mock_config),
        ):
            result = await get_tag_automations("ABC123")

            assert isinstance(result, list)
            assert len(result) == 0

    @pytest.mark.asyncio
    async def test_get_tag_automations_multiple_triggers(self):
        """Test when automation has multiple triggers with one tag trigger."""
        mock_automations = [
            {
                "entity_id": "automation.multi_trigger",
                "state": "on",
                "attributes": {"friendly_name": "Multi Trigger"},
            }
        ]

        mock_config = {
            "alias": "Multi Trigger",
            "trigger": [
                {
                    "platform": "state",
                    "entity_id": "light.living_room",
                },
                {
                    "platform": "tag",
                    "tag_id": "ABC123",
                },
            ],
            "action": [],
        }

        with (
            patch("app.api.tags.get_automations", return_value=mock_automations),
            patch("app.api.tags.get_automation_config", return_value=mock_config),
        ):
            result = await get_tag_automations("ABC123")

            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["automation_id"] == "automation.multi_trigger"

    @pytest.mark.asyncio
    async def test_get_tag_automations_config_error(self):
        """Test when get_automation_config raises an exception."""
        mock_automations = [
            {
                "entity_id": "automation.error",
                "state": "on",
                "attributes": {"friendly_name": "Error Automation"},
            }
        ]

        with (
            patch("app.api.tags.get_automations", return_value=mock_automations),
            patch("app.api.tags.get_automation_config", side_effect=Exception("Config error")),
        ):
            result = await get_tag_automations("ABC123")

            assert isinstance(result, list)
            assert len(result) == 0

    @pytest.mark.asyncio
    async def test_get_tag_automations_no_entity_id(self):
        """Test when automation has no entity_id."""
        mock_automations = [{"state": "on", "attributes": {"friendly_name": "No Entity ID"}}]

        with patch("app.api.tags.get_automations", return_value=mock_automations):
            result = await get_tag_automations("ABC123")

            assert isinstance(result, list)
            assert len(result) == 0
