"""Unit tests for app.api.areas module."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.api.areas import (
    create_area,
    delete_area,
    get_area_entities,
    get_area_summary,
    get_areas,
    update_area,
)


class TestGetAreas:
    """Test the get_areas function."""

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
    async def test_get_areas_success(self):
        """Test successful retrieval of all areas."""
        area_ids = ["living_room", "kitchen"]

        mock_client = AsyncMock()

        # Mock response for getting area IDs list
        mock_list_response = MagicMock()
        mock_list_response.text = '["living_room", "kitchen"]'
        mock_list_response.raise_for_status = MagicMock()

        # Mock responses for getting individual area names
        mock_living_response = MagicMock()
        mock_living_response.text = '"Living Room"'
        mock_living_response.raise_for_status = MagicMock()

        mock_kitchen_response = MagicMock()
        mock_kitchen_response.text = '"Kitchen"'
        mock_kitchen_response.raise_for_status = MagicMock()

        # Set up the mock to return different responses for each call
        mock_client.post = AsyncMock(
            side_effect=[
                mock_list_response,  # First call: get list of area IDs
                mock_living_response,  # Second call: get name for living_room
                mock_kitchen_response,  # Third call: get name for kitchen
            ]
        )

        with patch("app.api.areas.get_client", return_value=mock_client):
            result = await get_areas()

            assert isinstance(result, list)
            assert len(result) == 2
            assert result[0]["area_id"] == "living_room"
            assert result[0]["name"] == "Living Room"
            assert result[1]["area_id"] == "kitchen"
            assert result[1]["name"] == "Kitchen"
            # Verify we made the correct number of POST calls (1 for list + 2 for names)
            assert mock_client.post.call_count == 3
            # Verify first call was to /api/template with areas() template
            first_call_args = mock_client.post.call_args_list[0]
            assert "/api/template" in first_call_args[0][0]
            assert first_call_args[1]["json"]["template"] == "{{ areas() }}"

    @pytest.mark.asyncio
    async def test_get_areas_http_error(self):
        """Test handling of HTTP error."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not found", request=MagicMock(), response=mock_response
        )
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.api.areas.get_client", return_value=mock_client):
            result = await get_areas()

            # handle_api_errors returns a list with error dict for list-returning functions
            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], dict)
            assert "error" in result[0]


class TestGetAreaEntities:
    """Test the get_area_entities function."""

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
    async def test_get_area_entities_success(self):
        """Test successful retrieval of area entities."""
        area_id = "living_room"
        mock_entities = [
            {
                "entity_id": "light.living_room",
                "state": "on",
                "attributes": {"area_id": "living_room", "friendly_name": "Living Room Light"},
            },
            {
                "entity_id": "sensor.temperature",
                "state": "21.5",
                "attributes": {"area_id": "living_room", "unit_of_measurement": "°C"},
            },
        ]

        with patch("app.api.areas.get_entities", return_value=mock_entities):
            result = await get_area_entities(area_id)

            assert isinstance(result, list)
            assert len(result) == 2
            assert result[0]["entity_id"] == "light.living_room"
            assert result[1]["entity_id"] == "sensor.temperature"

    @pytest.mark.asyncio
    async def test_get_area_entities_no_entities(self):
        """Test area with no entities."""
        area_id = "empty_room"
        mock_entities = [
            {
                "entity_id": "light.other_room",
                "state": "off",
                "attributes": {"area_id": "other_room"},
            }
        ]

        with patch("app.api.areas.get_entities", return_value=mock_entities):
            result = await get_area_entities(area_id)

            assert isinstance(result, list)
            assert len(result) == 0

    @pytest.mark.asyncio
    async def test_get_area_entities_error(self):
        """Test handling of error when getting entities."""
        area_id = "test_area"
        error_response = {"error": "Connection error"}

        with patch("app.api.areas.get_entities", return_value=error_response):
            result = await get_area_entities(area_id)

            # Should propagate the error from get_entities as a list
            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], dict)
            assert "error" in result[0]


class TestCreateArea:
    """Test the create_area function."""

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
    async def test_create_area_success_with_name_only(self):
        """Test area creation returns error (not supported via REST)."""
        name = "Living Room"

        with patch("app.api.areas.get_client"):
            result = await create_area(name)

            assert isinstance(result, dict)
            assert "error" in result
            assert "not supported" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_create_area_success_with_aliases(self):
        """Test area creation with aliases returns error (not supported via REST)."""
        name = "Living Room"
        aliases = ["lounge", "salon"]

        with patch("app.api.areas.get_client"):
            result = await create_area(name, aliases=aliases)

            assert isinstance(result, dict)
            assert "error" in result
            assert "not supported" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_create_area_success_with_picture(self):
        """Test area creation with picture returns error (not supported via REST)."""
        name = "Living Room"
        picture = "/config/www/living_room.jpg"

        with patch("app.api.areas.get_client"):
            result = await create_area(name, picture=picture)

            assert isinstance(result, dict)
            assert "error" in result
            assert "not supported" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_create_area_http_error(self):
        """Test handling of HTTP error."""
        name = "Test Area"
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Conflict", request=MagicMock(), response=mock_response
        )
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.api.areas.get_client", return_value=mock_client):
            result = await create_area(name)

            assert isinstance(result, dict)
            assert "error" in result


class TestUpdateArea:
    """Test the update_area function."""

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
    async def test_update_area_success_with_name(self):
        """Test area update returns error (not supported via REST)."""
        area_id = "living_room"
        name = "Family Room"

        with patch("app.api.areas.get_client"):
            result = await update_area(area_id, name=name)

            assert isinstance(result, dict)
            assert "error" in result
            assert "not supported" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_update_area_success_with_aliases(self):
        """Test area update with aliases returns error (not supported via REST)."""
        area_id = "living_room"
        aliases = ["lounge", "salon"]

        with patch("app.api.areas.get_client"):
            result = await update_area(area_id, aliases=aliases)

            assert isinstance(result, dict)
            assert "error" in result
            assert "not supported" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_update_area_success_with_multiple_fields(self):
        """Test area update with multiple fields returns error (not supported via REST)."""
        area_id = "living_room"
        name = "Family Room"
        aliases = ["lounge"]

        with patch("app.api.areas.get_client"):
            result = await update_area(area_id, name=name, aliases=aliases)

            assert isinstance(result, dict)
            assert "error" in result
            assert "not supported" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_update_area_no_fields_provided(self):
        """Test update with no fields provided."""
        area_id = "living_room"

        result = await update_area(area_id)

        assert isinstance(result, dict)
        assert "error" in result
        assert "At least one field" in result["error"]

    @pytest.mark.asyncio
    async def test_update_area_http_error(self):
        """Test area update returns error (not supported via REST)."""
        area_id = "nonexistent"
        name = "Test Area"

        with patch("app.api.areas.get_client"):
            result = await update_area(area_id, name=name)

            assert isinstance(result, dict)
            assert "error" in result
            assert "not supported" in result["error"].lower()


class TestDeleteArea:
    """Test the delete_area function."""

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
    async def test_delete_area_success(self):
        """Test area deletion returns error (not supported via REST)."""
        area_id = "living_room"

        with patch("app.api.areas.get_client"):
            result = await delete_area(area_id)

            assert isinstance(result, dict)
            assert "error" in result
            assert "not supported" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_delete_area_http_error(self):
        """Test area deletion returns error (not supported via REST)."""
        area_id = "nonexistent"

        with patch("app.api.areas.get_client"):
            result = await delete_area(area_id)

            assert isinstance(result, dict)
            assert "error" in result
            assert "not supported" in result["error"].lower()


class TestGetAreaSummary:
    """Test the get_area_summary function."""

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
    async def test_get_area_summary_success(self):
        """Test successful calculation of area summary."""
        mock_areas = [
            {"area_id": "living_room", "name": "Living Room"},
            {"area_id": "kitchen", "name": "Kitchen"},
        ]
        mock_entities = [
            {
                "entity_id": "light.living_room",
                "state": "on",
                "attributes": {"area_id": "living_room"},
            },
            {
                "entity_id": "light.living_room_2",
                "state": "off",
                "attributes": {"area_id": "living_room"},
            },
            {
                "entity_id": "switch.living_room",
                "state": "on",
                "attributes": {"area_id": "living_room"},
            },
            {
                "entity_id": "sensor.kitchen_temp",
                "state": "21.5",
                "attributes": {"area_id": "kitchen"},
            },
        ]

        with patch("app.api.areas.get_areas", return_value=mock_areas):
            with patch("app.api.areas.get_entities", return_value=mock_entities):
                result = await get_area_summary()

                assert isinstance(result, dict)
                assert result["total_areas"] == 2
                assert "areas" in result
                assert "living_room" in result["areas"]
                assert result["areas"]["living_room"]["name"] == "Living Room"
                assert result["areas"]["living_room"]["entity_count"] == 3
                assert result["areas"]["living_room"]["domain_counts"]["light"] == 2
                assert result["areas"]["living_room"]["domain_counts"]["switch"] == 1
                assert "kitchen" in result["areas"]
                assert result["areas"]["kitchen"]["entity_count"] == 1
                assert result["areas"]["kitchen"]["domain_counts"]["sensor"] == 1

    @pytest.mark.asyncio
    async def test_get_area_summary_empty(self):
        """Test summary with no areas."""
        mock_areas = []
        mock_entities = []

        with patch("app.api.areas.get_areas", return_value=mock_areas):
            with patch("app.api.areas.get_entities", return_value=mock_entities):
                result = await get_area_summary()

                assert isinstance(result, dict)
                assert result["total_areas"] == 0
                assert len(result["areas"]) == 0

    @pytest.mark.asyncio
    async def test_get_area_summary_areas_error(self):
        """Test handling of error when getting areas."""
        error_response = {"error": "Connection error"}

        with patch("app.api.areas.get_areas", return_value=error_response):
            result = await get_area_summary()

            # Should propagate the error from get_areas
            assert isinstance(result, dict)
            assert "error" in result

    @pytest.mark.asyncio
    async def test_get_area_summary_entities_error(self):
        """Test handling of error when getting entities."""
        mock_areas = [{"area_id": "living_room", "name": "Living Room"}]
        error_response = {"error": "Connection error"}

        with patch("app.api.areas.get_areas", return_value=mock_areas):
            with patch("app.api.areas.get_entities", return_value=error_response):
                result = await get_area_summary()

                # Should propagate the error from get_entities
                assert isinstance(result, dict)
                assert "error" in result
