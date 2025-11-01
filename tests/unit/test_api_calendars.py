"""Unit tests for app.api.calendars module."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.api.calendars import (
    create_calendar_event,
    get_calendar_events,
    list_calendars,
)


class TestListCalendars:
    """Test the list_calendars function."""

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
    async def test_list_calendars_success(self):
        """Test successful retrieval of calendars."""
        mock_entities = [
            {
                "entity_id": "calendar.google",
                "state": "idle",
                "attributes": {
                    "friendly_name": "Google Calendar",
                    "supported_features": 3,
                },
            },
            {
                "entity_id": "calendar.local",
                "state": "idle",
                "attributes": {
                    "friendly_name": "Local Calendar",
                    "supported_features": 1,
                },
            },
        ]

        with patch("app.api.calendars.get_entities", return_value=mock_entities):
            result = await list_calendars()

            assert isinstance(result, list)
            assert len(result) == 2
            assert result[0]["entity_id"] == "calendar.google"
            assert result[0]["friendly_name"] == "Google Calendar"
            assert result[0]["supported_features"] == 3
            assert result[1]["entity_id"] == "calendar.local"

    @pytest.mark.asyncio
    async def test_list_calendars_empty(self):
        """Test when no calendars are found."""
        with patch("app.api.calendars.get_entities", return_value=[]):
            result = await list_calendars()

            assert isinstance(result, list)
            assert len(result) == 0

    @pytest.mark.asyncio
    async def test_list_calendars_missing_attributes(self):
        """Test when calendar entities have missing attributes."""
        mock_entities = [
            {
                "entity_id": "calendar.simple",
                "state": "idle",
                "attributes": {},
            }
        ]

        with patch("app.api.calendars.get_entities", return_value=mock_entities):
            result = await list_calendars()

            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["entity_id"] == "calendar.simple"
            assert result[0]["friendly_name"] is None
            assert result[0]["supported_features"] == 0


class TestGetCalendarEvents:
    """Test the get_calendar_events function."""

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
    async def test_get_calendar_events_success(self):
        """Test successful retrieval of calendar events."""
        mock_events = [
            {
                "summary": "Meeting",
                "start": {"dateTime": "2025-01-01T10:00:00"},
                "end": {"dateTime": "2025-01-01T11:00:00"},
                "description": "Team meeting",
                "location": "Conference Room A",
                "uid": "event_12345",
            }
        ]

        with patch("app.api.calendars._calendars_api.get", return_value=mock_events) as mock_get:
            result = await get_calendar_events("calendar.google", "2025-01-01", "2025-01-07")

            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["summary"] == "Meeting"
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            assert call_args[0][0] == "/api/calendars/calendar.google"
            assert call_args[1]["params"]["start_date_time"] == "2025-01-01T00:00:00"
            assert call_args[1]["params"]["end_date_time"] == "2025-01-07T23:59:59"

    @pytest.mark.asyncio
    async def test_get_calendar_events_with_datetime(self):
        """Test retrieval with full datetime strings."""
        mock_events = []

        with patch("app.api.calendars._calendars_api.get", return_value=mock_events) as mock_get:
            result = await get_calendar_events(
                "calendar.google",
                "2025-01-01T09:00:00",
                "2025-01-07T18:00:00",
            )

            assert isinstance(result, list)
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            assert call_args[1]["params"]["start_date_time"] == "2025-01-01T09:00:00"
            assert call_args[1]["params"]["end_date_time"] == "2025-01-07T18:00:00"

    @pytest.mark.asyncio
    async def test_get_calendar_events_empty(self):
        """Test when no events are found."""
        with patch("app.api.calendars._calendars_api.get", return_value=[]):
            result = await get_calendar_events("calendar.google", "2025-01-01", "2025-01-07")

            assert isinstance(result, list)
            assert len(result) == 0

    @pytest.mark.asyncio
    async def test_get_calendar_events_http_error(self):
        """Test HTTP error handling."""
        with patch(
            "app.api.calendars._calendars_api.get",
            side_effect=httpx.HTTPStatusError(
                "404 Not Found",
                request=MagicMock(),
                response=MagicMock(status_code=404),
            ),
        ):
            result = await get_calendar_events("calendar.nonexistent", "2025-01-01", "2025-01-07")

            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], dict)
            assert "error" in result[0]
            assert "404" in result[0]["error"]


class TestCreateCalendarEvent:
    """Test the create_calendar_event function."""

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
    async def test_create_calendar_event_success(self):
        """Test successful calendar event creation."""
        mock_response = {"uid": "event_12345", "message": "Event created"}

        with patch(
            "app.api.calendars._calendars_api.post", return_value=mock_response
        ) as mock_post:
            result = await create_calendar_event(
                "calendar.google",
                "Meeting",
                "2025-01-01T10:00:00",
                "2025-01-01T11:00:00",
            )

            assert isinstance(result, dict)
            assert result["uid"] == "event_12345"
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args[0][0] == "/api/calendars/calendar.google/events"
            payload = call_args[1]["data"]
            assert payload["summary"] == "Meeting"
            assert payload["dtstart"] == "2025-01-01T10:00:00"
            assert payload["dtend"] == "2025-01-01T11:00:00"

    @pytest.mark.asyncio
    async def test_create_calendar_event_with_date_only(self):
        """Test event creation with date-only format."""
        mock_response = {"uid": "event_12345", "message": "Event created"}

        with patch(
            "app.api.calendars._calendars_api.post", return_value=mock_response
        ) as mock_post:
            result = await create_calendar_event(
                "calendar.google", "All Day Event", "2025-01-01", "2025-01-01"
            )

            assert isinstance(result, dict)
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            payload = call_args[1]["data"]
            assert payload["dtstart"] == "2025-01-01T00:00:00"
            assert payload["dtend"] == "2025-01-01T23:59:59"

    @pytest.mark.asyncio
    async def test_create_calendar_event_with_description(self):
        """Test event creation with description."""
        mock_response = {"uid": "event_12345", "message": "Event created"}

        with patch(
            "app.api.calendars._calendars_api.post", return_value=mock_response
        ) as mock_post:
            result = await create_calendar_event(
                "calendar.google",
                "Meeting",
                "2025-01-01T10:00:00",
                "2025-01-01T11:00:00",
                description="Team meeting",
            )

            assert isinstance(result, dict)
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            payload = call_args[1]["data"]
            assert payload["summary"] == "Meeting"
            assert payload["description"] == "Team meeting"

    @pytest.mark.asyncio
    async def test_create_calendar_event_without_description(self):
        """Test event creation without description."""
        mock_response = {"uid": "event_12345", "message": "Event created"}

        with patch(
            "app.api.calendars._calendars_api.post", return_value=mock_response
        ) as mock_post:
            result = await create_calendar_event(
                "calendar.google",
                "Meeting",
                "2025-01-01T10:00:00",
                "2025-01-01T11:00:00",
            )

            assert isinstance(result, dict)
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            payload = call_args[1]["data"]
            assert "description" not in payload

    @pytest.mark.asyncio
    async def test_create_calendar_event_http_error(self):
        """Test HTTP error handling."""
        with patch(
            "app.api.calendars._calendars_api.post",
            side_effect=httpx.HTTPStatusError(
                "400 Bad Request",
                request=MagicMock(),
                response=MagicMock(status_code=400),
            ),
        ):
            result = await create_calendar_event(
                "calendar.google",
                "Meeting",
                "2025-01-01T10:00:00",
                "2025-01-01T11:00:00",
            )

            assert isinstance(result, dict)
            assert "error" in result
            assert "400" in result["error"]
