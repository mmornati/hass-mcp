"""Unit tests for app.api.events module."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.api.events import fire_event, get_events, list_event_types


class TestFireEvent:
    """Test the fire_event function."""

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
    async def test_fire_event_success(self):
        """Test successful event firing."""
        mock_response = {"message": "Event fired successfully"}

        with patch("app.api.events._events_api.post", return_value=mock_response):
            result = await fire_event("custom_event", {"message": "Hello"})

            assert isinstance(result, dict)
            assert result["message"] == "Event fired successfully"

    @pytest.mark.asyncio
    async def test_fire_event_without_data(self):
        """Test event firing without event data."""
        mock_response = {"message": "Event fired successfully"}

        with patch("app.api.events._events_api.post", return_value=mock_response):
            result = await fire_event("custom_event")

            assert isinstance(result, dict)
            assert result["message"] == "Event fired successfully"

    @pytest.mark.asyncio
    async def test_fire_event_with_empty_data(self):
        """Test event firing with empty event data."""
        mock_response = {"message": "Event fired successfully"}

        with patch("app.api.events._events_api.post", return_value=mock_response):
            result = await fire_event("custom_event", {})

            assert isinstance(result, dict)
            assert result["message"] == "Event fired successfully"

    @pytest.mark.asyncio
    async def test_fire_event_http_error(self):
        """Test HTTP error handling."""
        with patch(
            "app.api.events._events_api.post",
            side_effect=httpx.HTTPStatusError(
                "400 Bad Request",
                request=MagicMock(),
                response=MagicMock(status_code=400),
            ),
        ):
            result = await fire_event("custom_event", {"message": "Hello"})

            assert isinstance(result, dict)
            assert "error" in result
            assert "400" in result["error"]


class TestListEventTypes:
    """Test the list_event_types function."""

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
    async def test_list_event_types_success(self):
        """Test successful retrieval of event types."""
        result = await list_event_types()

        assert isinstance(result, list)
        assert len(result) > 0
        assert "state_changed" in result
        assert "custom_event" in result

    @pytest.mark.asyncio
    async def test_list_event_types_contains_common_types(self):
        """Test that common event types are included."""
        result = await list_event_types()

        assert isinstance(result, list)
        expected_types = [
            "state_changed",
            "time_changed",
            "service_registered",
            "call_service",
            "homeassistant_start",
            "homeassistant_stop",
            "automation_triggered",
            "script_started",
            "scene_on",
            "custom_event",
        ]

        for event_type in expected_types:
            assert event_type in result, f"Expected event type '{event_type}' not found in result"


class TestGetEvents:
    """Test the get_events function."""

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
    async def test_get_events_success(self):
        """Test successful retrieval of events."""
        mock_events = [
            {
                "when": "2025-01-01T10:00:00",
                "name": "Living Room Light",
                "entity_id": "light.living_room",
                "state": "on",
                "domain": "light",
                "message": "turned on",
            }
        ]

        with patch("app.api.events.get_logbook", return_value=mock_events):
            result = await get_events()

            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["entity_id"] == "light.living_room"

    @pytest.mark.asyncio
    async def test_get_events_with_entity_id(self):
        """Test retrieval of events for specific entity."""
        mock_events = [
            {
                "when": "2025-01-01T10:00:00",
                "name": "Living Room Light",
                "entity_id": "light.living_room",
                "state": "on",
                "domain": "light",
                "message": "turned on",
            }
        ]

        with patch("app.api.events.get_logbook", return_value=mock_events):
            result = await get_events(entity_id="light.living_room")

            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["entity_id"] == "light.living_room"

    @pytest.mark.asyncio
    async def test_get_events_with_hours(self):
        """Test retrieval of events with custom hours parameter."""
        mock_events = [
            {
                "when": "2025-01-01T10:00:00",
                "name": "Living Room Light",
                "entity_id": "light.living_room",
                "state": "on",
                "domain": "light",
                "message": "turned on",
            }
        ]

        with patch("app.api.events.get_logbook", return_value=mock_events):
            result = await get_events(hours=24)

            assert isinstance(result, list)
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_events_empty(self):
        """Test retrieval when no events are found."""
        with patch("app.api.events.get_logbook", return_value=[]):
            result = await get_events()

            assert isinstance(result, list)
            assert len(result) == 0

    @pytest.mark.asyncio
    async def test_get_events_error(self):
        """Test error handling."""
        with patch(
            "app.api.events.get_logbook",
            return_value=[{"error": "Failed to get logbook entries"}],
        ):
            result = await get_events()

            assert isinstance(result, list)
            assert len(result) == 1
            assert "error" in result[0]
