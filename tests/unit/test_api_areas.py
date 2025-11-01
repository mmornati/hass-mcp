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
        mock_areas = [
            {
                "area_id": "living_room",
                "name": "Living Room",
                "aliases": [],
                "picture": None,
            },
            {
                "area_id": "kitchen",
                "name": "Kitchen",
                "aliases": ["cooking_area"],
                "picture": "/config/www/kitchen.jpg",
            },
        ]

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = mock_areas
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("app.api.areas.get_client", return_value=mock_client):
            result = await get_areas()

            assert isinstance(result, list)
            assert len(result) == 2
            assert result[0]["area_id"] == "living_room"
            assert result[0]["name"] == "Living Room"
            assert result[1]["area_id"] == "kitchen"
            assert result[1]["aliases"] == ["cooking_area"]
            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert call_args[0][0] == "http://localhost:8123/api/config/area_registry"

    @pytest.mark.asyncio
    async def test_get_areas_http_error(self):
        """Test handling of HTTP error."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not found", request=MagicMock(), response=mock_response
        )
        mock_client.get = AsyncMock(return_value=mock_response)

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
        """Test successful area creation with just name."""
        name = "Living Room"
        mock_area = {
            "area_id": "living_room",
            "name": "Living Room",
            "aliases": [],
            "picture": None,
        }

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = mock_area
        mock_response.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.api.areas.get_client", return_value=mock_client):
            result = await create_area(name)

            assert isinstance(result, dict)
            assert result["area_id"] == "living_room"
            assert result["name"] == "Living Room"
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[0][0] == "http://localhost:8123/api/config/area_registry/create"
            assert call_args[1]["json"] == {"name": name}

    @pytest.mark.asyncio
    async def test_create_area_success_with_aliases(self):
        """Test successful area creation with aliases."""
        name = "Living Room"
        aliases = ["lounge", "salon"]
        mock_area = {
            "area_id": "living_room",
            "name": "Living Room",
            "aliases": aliases,
            "picture": None,
        }

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = mock_area
        mock_response.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.api.areas.get_client", return_value=mock_client):
            result = await create_area(name, aliases=aliases)

            assert isinstance(result, dict)
            assert result["aliases"] == aliases
            call_args = mock_client.post.call_args
            assert call_args[1]["json"] == {"name": name, "aliases": aliases}

    @pytest.mark.asyncio
    async def test_create_area_success_with_picture(self):
        """Test successful area creation with picture."""
        name = "Living Room"
        picture = "/config/www/living_room.jpg"
        mock_area = {
            "area_id": "living_room",
            "name": "Living Room",
            "aliases": [],
            "picture": picture,
        }

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = mock_area
        mock_response.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.api.areas.get_client", return_value=mock_client):
            result = await create_area(name, picture=picture)

            assert isinstance(result, dict)
            assert result["picture"] == picture
            call_args = mock_client.post.call_args
            assert call_args[1]["json"] == {"name": name, "picture": picture}

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
        """Test successful area update with name."""
        area_id = "living_room"
        name = "Family Room"
        mock_area = {
            "area_id": "living_room",
            "name": "Family Room",
            "aliases": [],
            "picture": None,
        }

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = mock_area
        mock_response.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.api.areas.get_client", return_value=mock_client):
            result = await update_area(area_id, name=name)

            assert isinstance(result, dict)
            assert result["name"] == "Family Room"
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[0][0] == f"http://localhost:8123/api/config/area_registry/{area_id}"
            assert call_args[1]["json"] == {"name": name}

    @pytest.mark.asyncio
    async def test_update_area_success_with_aliases(self):
        """Test successful area update with aliases."""
        area_id = "living_room"
        aliases = ["lounge", "salon"]
        mock_area = {
            "area_id": "living_room",
            "name": "Living Room",
            "aliases": aliases,
            "picture": None,
        }

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = mock_area
        mock_response.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.api.areas.get_client", return_value=mock_client):
            result = await update_area(area_id, aliases=aliases)

            assert isinstance(result, dict)
            assert result["aliases"] == aliases
            call_args = mock_client.post.call_args
            assert call_args[1]["json"] == {"aliases": aliases}

    @pytest.mark.asyncio
    async def test_update_area_success_with_multiple_fields(self):
        """Test successful area update with multiple fields."""
        area_id = "living_room"
        name = "Family Room"
        aliases = ["lounge"]
        mock_area = {
            "area_id": "living_room",
            "name": "Family Room",
            "aliases": aliases,
            "picture": None,
        }

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = mock_area
        mock_response.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.api.areas.get_client", return_value=mock_client):
            result = await update_area(area_id, name=name, aliases=aliases)

            assert isinstance(result, dict)
            assert result["name"] == "Family Room"
            assert result["aliases"] == aliases
            call_args = mock_client.post.call_args
            assert call_args[1]["json"] == {"name": name, "aliases": aliases}

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
        """Test handling of HTTP error."""
        area_id = "nonexistent"
        name = "Test Area"
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not found", request=MagicMock(), response=mock_response
        )
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.api.areas.get_client", return_value=mock_client):
            result = await update_area(area_id, name=name)

            assert isinstance(result, dict)
            assert "error" in result


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
        """Test successful area deletion."""
        area_id = "living_room"

        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_client.delete = AsyncMock(return_value=mock_response)

        with patch("app.api.areas.get_client", return_value=mock_client):
            result = await delete_area(area_id)

            assert isinstance(result, dict)
            assert result["status"] == "deleted"
            assert result["area_id"] == area_id
            mock_client.delete.assert_called_once()
            call_args = mock_client.delete.call_args
            assert call_args[0][0] == f"http://localhost:8123/api/config/area_registry/{area_id}"

    @pytest.mark.asyncio
    async def test_delete_area_http_error(self):
        """Test handling of HTTP error."""
        area_id = "nonexistent"
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not found", request=MagicMock(), response=mock_response
        )
        mock_client.delete = AsyncMock(return_value=mock_response)

        with patch("app.api.areas.get_client", return_value=mock_client):
            result = await delete_area(area_id)

            assert isinstance(result, dict)
            assert "error" in result


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
