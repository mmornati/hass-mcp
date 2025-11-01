"""Unit tests for app.api.zones module."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.api.zones import create_zone, delete_zone, list_zones, update_zone


class TestListZones:
    """Test the list_zones function."""

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
    async def test_list_zones_success(self):
        """Test successful retrieval of all zones."""
        mock_zones = [
            {
                "id": "home",
                "name": "Home",
                "latitude": 37.7749,
                "longitude": -122.4194,
                "radius": 100,
                "icon": "mdi:home",
                "passive": False,
            },
            {
                "id": "work",
                "name": "Work",
                "latitude": 37.7849,
                "longitude": -122.4094,
                "radius": 200,
                "icon": "mdi:office",
                "passive": False,
            },
        ]

        with patch("app.api.zones._zones_api.get", return_value=mock_zones):
            result = await list_zones()

            assert isinstance(result, list)
            assert len(result) == 2
            assert result[0]["id"] == "home"
            assert result[1]["id"] == "work"

    @pytest.mark.asyncio
    async def test_list_zones_empty(self):
        """Test retrieval when no zones are found."""
        with patch("app.api.zones._zones_api.get", return_value=[]):
            result = await list_zones()

            assert isinstance(result, list)
            assert len(result) == 0

    @pytest.mark.asyncio
    async def test_list_zones_http_error(self):
        """Test HTTP error handling."""
        with patch(
            "app.api.zones._zones_api.get",
            side_effect=httpx.HTTPStatusError(
                "404 Not Found",
                request=MagicMock(),
                response=MagicMock(status_code=404),
            ),
        ):
            result = await list_zones()

            # Error handler wraps list-returning functions in a list
            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], dict)
            assert "error" in result[0]
            assert "404" in result[0]["error"]


class TestCreateZone:
    """Test the create_zone function."""

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
    async def test_create_zone_success(self):
        """Test successful zone creation."""
        mock_response = {
            "id": "school",
            "name": "School",
            "latitude": 37.7949,
            "longitude": -122.3994,
            "radius": 150,
            "icon": "mdi:school",
            "passive": True,
        }

        with patch("app.api.zones._zones_api.post", return_value=mock_response):
            result = await create_zone("School", 37.7949, -122.3994, 150, "mdi:school", True)

            assert isinstance(result, dict)
            assert result["id"] == "school"
            assert result["name"] == "School"
            assert result["passive"] is True

    @pytest.mark.asyncio
    async def test_create_zone_without_icon(self):
        """Test zone creation without icon."""
        mock_response = {
            "id": "work",
            "name": "Work",
            "latitude": 37.7849,
            "longitude": -122.4094,
            "radius": 200,
            "passive": False,
        }

        with patch("app.api.zones._zones_api.post", return_value=mock_response):
            result = await create_zone("Work", 37.7849, -122.4094, 200)

            assert isinstance(result, dict)
            assert result["name"] == "Work"
            assert "icon" not in result or result.get("icon") is None

    @pytest.mark.asyncio
    async def test_create_zone_invalid_latitude(self):
        """Test zone creation with invalid latitude."""
        result = await create_zone("Test", 91.0, -122.4194, 100)

        assert isinstance(result, dict)
        assert "error" in result
        assert "latitude" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_create_zone_invalid_longitude(self):
        """Test zone creation with invalid longitude."""
        result = await create_zone("Test", 37.7749, 181.0, 100)

        assert isinstance(result, dict)
        assert "error" in result
        assert "longitude" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_create_zone_invalid_radius(self):
        """Test zone creation with invalid radius."""
        result = await create_zone("Test", 37.7749, -122.4194, -10)

        assert isinstance(result, dict)
        assert "error" in result
        assert "radius" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_create_zone_zero_radius(self):
        """Test zone creation with zero radius."""
        result = await create_zone("Test", 37.7749, -122.4194, 0)

        assert isinstance(result, dict)
        assert "error" in result
        assert "radius" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_create_zone_http_error(self):
        """Test HTTP error handling."""
        with patch(
            "app.api.zones._zones_api.post",
            side_effect=httpx.HTTPStatusError(
                "400 Bad Request",
                request=MagicMock(),
                response=MagicMock(status_code=400),
            ),
        ):
            result = await create_zone("Test", 37.7749, -122.4194, 100)

            assert isinstance(result, dict)
            assert "error" in result
            assert "400" in result["error"]


class TestUpdateZone:
    """Test the update_zone function."""

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
    async def test_update_zone_name_success(self):
        """Test successful zone name update."""
        mock_response = {
            "id": "home",
            "name": "My Home",
            "latitude": 37.7749,
            "longitude": -122.4194,
            "radius": 100,
        }

        with patch("app.api.zones._zones_api.post", return_value=mock_response):
            result = await update_zone("home", name="My Home")

            assert isinstance(result, dict)
            assert result["name"] == "My Home"

    @pytest.mark.asyncio
    async def test_update_zone_location_success(self):
        """Test successful zone location update."""
        mock_response = {
            "id": "work",
            "name": "Work",
            "latitude": 37.7849,
            "longitude": -122.4094,
            "radius": 200,
        }

        with patch("app.api.zones._zones_api.post", return_value=mock_response):
            result = await update_zone("work", latitude=37.7849, longitude=-122.4094)

            assert isinstance(result, dict)
            assert result["latitude"] == 37.7849
            assert result["longitude"] == -122.4094

    @pytest.mark.asyncio
    async def test_update_zone_radius_success(self):
        """Test successful zone radius update."""
        mock_response = {
            "id": "home",
            "name": "Home",
            "latitude": 37.7749,
            "longitude": -122.4194,
            "radius": 150,
        }

        with patch("app.api.zones._zones_api.post", return_value=mock_response):
            result = await update_zone("home", radius=150)

            assert isinstance(result, dict)
            assert result["radius"] == 150

    @pytest.mark.asyncio
    async def test_update_zone_multiple_fields_success(self):
        """Test successful zone update with multiple fields."""
        mock_response = {
            "id": "work",
            "name": "Office",
            "latitude": 37.7849,
            "longitude": -122.4094,
            "radius": 200,
            "icon": "mdi:office",
        }

        with patch("app.api.zones._zones_api.post", return_value=mock_response):
            result = await update_zone(
                "work",
                name="Office",
                latitude=37.7849,
                longitude=-122.4094,
                radius=200,
                icon="mdi:office",
            )

            assert isinstance(result, dict)
            assert result["name"] == "Office"
            assert result["radius"] == 200
            assert result["icon"] == "mdi:office"

    @pytest.mark.asyncio
    async def test_update_zone_no_fields(self):
        """Test zone update with no fields provided."""
        result = await update_zone("home")

        assert isinstance(result, dict)
        assert "error" in result
        assert "field" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_update_zone_invalid_latitude(self):
        """Test zone update with invalid latitude."""
        result = await update_zone("home", latitude=91.0)

        assert isinstance(result, dict)
        assert "error" in result
        assert "latitude" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_update_zone_invalid_longitude(self):
        """Test zone update with invalid longitude."""
        result = await update_zone("home", longitude=181.0)

        assert isinstance(result, dict)
        assert "error" in result
        assert "longitude" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_update_zone_invalid_radius(self):
        """Test zone update with invalid radius."""
        result = await update_zone("home", radius=-10)

        assert isinstance(result, dict)
        assert "error" in result
        assert "radius" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_update_zone_http_error(self):
        """Test HTTP error handling."""
        with patch(
            "app.api.zones._zones_api.post",
            side_effect=httpx.HTTPStatusError(
                "404 Not Found",
                request=MagicMock(),
                response=MagicMock(status_code=404),
            ),
        ):
            result = await update_zone("nonexistent", name="New Name")

            assert isinstance(result, dict)
            assert "error" in result
            assert "404" in result["error"]


class TestDeleteZone:
    """Test the delete_zone function."""

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
    async def test_delete_zone_success(self):
        """Test successful zone deletion."""
        with patch("app.api.zones._zones_api.delete", return_value=None):
            result = await delete_zone("work")

            assert isinstance(result, dict)
            assert result["status"] == "deleted"
            assert result["zone_id"] == "work"

    @pytest.mark.asyncio
    async def test_delete_zone_http_error(self):
        """Test HTTP error handling."""
        with patch(
            "app.api.zones._zones_api.delete",
            side_effect=httpx.HTTPStatusError(
                "404 Not Found",
                request=MagicMock(),
                response=MagicMock(status_code=404),
            ),
        ):
            result = await delete_zone("nonexistent")

            assert isinstance(result, dict)
            assert "error" in result
            assert "404" in result["error"]
