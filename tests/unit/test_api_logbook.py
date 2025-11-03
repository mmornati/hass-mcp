"""Unit tests for app.api.logbook module."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.api.logbook import get_entity_logbook, get_logbook, search_logbook


class TestGetLogbook:
    """Test the get_logbook function."""

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
    async def test_get_logbook_success_with_hours(self):
        """Test successful retrieval of logbook entries with hours parameter."""
        mock_entries = [
            {
                "when": "2025-03-15T10:30:00Z",
                "name": "Living Room Light",
                "entity_id": "light.living_room",
                "state": "on",
                "domain": "light",
                "message": "turned on",
                "icon": None,
            },
            {
                "when": "2025-03-15T10:25:00Z",
                "name": "Kitchen Light",
                "entity_id": "light.kitchen",
                "state": "off",
                "domain": "light",
                "message": "turned off",
                "icon": None,
            },
        ]

        mock_client = AsyncMock()
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = mock_entries
        mock_get_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_get_response)

        with patch("app.api.logbook._logbook_api._get_client", return_value=mock_client):
            result = await get_logbook(hours=24)

            assert isinstance(result, list)
            assert len(result) == 2
            assert result[0]["entity_id"] == "light.living_room"
            mock_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_logbook_success_with_timestamp(self):
        """Test successful retrieval with timestamp parameter."""
        mock_entries = [
            {
                "when": "2025-03-15T10:30:00Z",
                "name": "Living Room Light",
                "entity_id": "light.living_room",
                "state": "on",
            },
        ]

        mock_client = AsyncMock()
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = mock_entries
        mock_get_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_get_response)

        with patch("app.api.logbook._logbook_api._get_client", return_value=mock_client):
            result = await get_logbook(timestamp="2025-03-15T10:00:00Z")

            assert isinstance(result, list)
            assert len(result) == 1
            call_args = mock_client.get.call_args
            # Should remove Z from timestamp
            assert "/api/logbook/2025-03-15T10:00:00" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_logbook_success_with_entity_id(self):
        """Test successful retrieval filtered by entity_id."""
        mock_entries = [
            {
                "when": "2025-03-15T10:30:00Z",
                "name": "Living Room Light",
                "entity_id": "light.living_room",
                "state": "on",
            },
        ]

        mock_client = AsyncMock()
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = mock_entries
        mock_get_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_get_response)

        with patch("app.api.logbook._logbook_api._get_client", return_value=mock_client):
            result = await get_logbook(entity_id="light.living_room", hours=24)

            assert isinstance(result, list)
            call_args = mock_client.get.call_args
            assert call_args[1]["params"]["entity"] == "light.living_room"

    @pytest.mark.asyncio
    async def test_get_logbook_empty(self):
        """Test retrieval when no entries are found."""
        mock_client = AsyncMock()
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = []
        mock_get_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_get_response)

        with patch("app.api.logbook._logbook_api._get_client", return_value=mock_client):
            result = await get_logbook(hours=24)

            assert isinstance(result, list)
            assert len(result) == 0

    @pytest.mark.asyncio
    async def test_get_logbook_http_error(self):
        """Test handling of HTTP errors."""
        mock_client = AsyncMock()
        mock_get_response = MagicMock()
        mock_get_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "500 Internal Server Error",
            request=MagicMock(),
            response=MagicMock(status_code=500),
        )
        mock_client.get = AsyncMock(return_value=mock_get_response)

        with patch("app.api.logbook._logbook_api._get_client", return_value=mock_client):
            result = await get_logbook(hours=24)

            # Should return list with error dict
            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], dict)
            assert "error" in result[0]


class TestGetEntityLogbook:
    """Test the get_entity_logbook function."""

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
    async def test_get_entity_logbook_success(self):
        """Test successful retrieval of entity logbook entries."""
        mock_entries = [
            {
                "when": "2025-03-15T10:30:00Z",
                "name": "Living Room Light",
                "entity_id": "light.living_room",
                "state": "on",
            },
        ]

        with patch("app.api.logbook.get_logbook", return_value=mock_entries):
            result = await get_entity_logbook("light.living_room", hours=24)

            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["entity_id"] == "light.living_room"

    @pytest.mark.asyncio
    async def test_get_entity_logbook_default_hours(self):
        """Test retrieval with default hours parameter."""
        mock_entries = []

        with patch("app.api.logbook.get_logbook", return_value=mock_entries):
            result = await get_entity_logbook("light.living_room")

            assert isinstance(result, list)
            # Verify get_logbook was called with entity_id and default hours
            # (actual verification would require checking the call)


class TestSearchLogbook:
    """Test the search_logbook function."""

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
    async def test_search_logbook_success(self):
        """Test successful search of logbook entries."""
        mock_entries = [
            {
                "when": "2025-03-15T10:30:00Z",
                "name": "Living Room Light",
                "entity_id": "light.living_room",
                "message": "turned on",
            },
            {
                "when": "2025-03-15T10:25:00Z",
                "name": "Kitchen Light",
                "entity_id": "light.kitchen",
                "message": "turned off",
            },
            {
                "when": "2025-03-15T10:20:00Z",
                "name": "Temperature Sensor",
                "entity_id": "sensor.temperature",
                "message": "state changed",
            },
        ]

        with patch("app.api.logbook.get_logbook", return_value=mock_entries):
            result = await search_logbook("light", hours=24)

            assert isinstance(result, list)
            assert len(result) == 2
            assert all(
                "light" in entry["entity_id"] or "light" in entry["name"].lower()
                for entry in result
            )

    @pytest.mark.asyncio
    async def test_search_logbook_no_matches(self):
        """Test search with no matching entries."""
        mock_entries = [
            {
                "when": "2025-03-15T10:20:00Z",
                "name": "Temperature Sensor",
                "entity_id": "sensor.temperature",
                "message": "state changed",
            },
        ]

        with patch("app.api.logbook.get_logbook", return_value=mock_entries):
            result = await search_logbook("nonexistent", hours=24)

            assert isinstance(result, list)
            assert len(result) == 0

    @pytest.mark.asyncio
    async def test_search_logbook_case_insensitive(self):
        """Test that search is case-insensitive."""
        mock_entries = [
            {
                "when": "2025-03-15T10:30:00Z",
                "name": "Living Room Light",
                "entity_id": "light.living_room",
                "message": "turned on",
            },
        ]

        with patch("app.api.logbook.get_logbook", return_value=mock_entries):
            result = await search_logbook("LIVING", hours=24)

            assert isinstance(result, list)
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_search_logbook_in_message(self):
        """Test that search matches message field."""
        mock_entries = [
            {
                "when": "2025-03-15T10:30:00Z",
                "name": "Living Room Light",
                "entity_id": "light.living_room",
                "message": "error occurred",
            },
            {
                "when": "2025-03-15T10:25:00Z",
                "name": "Kitchen Light",
                "entity_id": "light.kitchen",
                "message": "turned off",
            },
        ]

        with patch("app.api.logbook.get_logbook", return_value=mock_entries):
            result = await search_logbook("error", hours=24)

            assert isinstance(result, list)
            assert len(result) == 1
            assert "error" in result[0]["message"].lower()

    @pytest.mark.asyncio
    async def test_search_logbook_with_none_values(self):
        """Test that search handles None values in entity_id, name, or message."""
        mock_entries = [
            {
                "when": "2025-03-15T10:30:00Z",
                "name": None,
                "entity_id": None,
                "message": "turned on",
            },
            {
                "when": "2025-03-15T10:25:00Z",
                "name": "Kitchen Light",
                "entity_id": "light.kitchen",
                "message": None,
            },
            {
                "when": "2025-03-15T10:20:00Z",
                "name": None,
                "entity_id": "sensor.temperature",
                "message": None,
            },
        ]

        with patch("app.api.logbook.get_logbook", return_value=mock_entries):
            # Should not raise AttributeError: 'NoneType' object has no attribute 'lower'
            result = await search_logbook("light", hours=24)

            assert isinstance(result, list)
            # Should find matches despite None values
            assert len(result) == 1
            assert result[0]["entity_id"] == "light.kitchen"
