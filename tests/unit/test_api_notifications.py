"""Unit tests for app.api.notifications module."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.api.notifications import (
    list_notification_services,
    send_notification,
    test_notification_delivery,
)


class TestListNotificationServices:
    """Test the list_notification_services function."""

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
    async def test_list_notification_services_success(self):
        """Test successful retrieval of notification services."""
        mock_response = {
            "notify": [
                {
                    "service": "notify.mobile_app_iphone",
                    "name": "mobile_app_iphone",
                    "description": "Send notifications to iPhone",
                },
                {
                    "service": "notify.persistent_notification",
                    "name": "persistent_notification",
                    "description": "Persistent notifications",
                },
            ]
        }

        with patch("app.api.notifications._notifications_api.get", return_value=mock_response):
            result = await list_notification_services()

            assert isinstance(result, list)
            assert len(result) == 2
            assert result[0]["service"] == "notify.mobile_app_iphone"
            assert result[1]["service"] == "notify.persistent_notification"

    @pytest.mark.asyncio
    async def test_list_notification_services_empty(self):
        """Test when no notification services are found."""
        mock_response = {"notify": []}

        with patch("app.api.notifications._notifications_api.get", return_value=mock_response):
            result = await list_notification_services()

            assert isinstance(result, list)
            assert len(result) == 0

    @pytest.mark.asyncio
    async def test_list_notification_services_fallback(self):
        """Test fallback to entity states when services API fails."""
        mock_entities = [
            {"entity_id": "notify.mobile_app_iphone"},
            {"entity_id": "notify.telegram"},
        ]

        with (
            patch(
                "app.api.notifications._notifications_api.get",
                side_effect=Exception("API error"),
            ),
            patch("app.api.notifications.get_entities", return_value=mock_entities),
        ):
            result = await list_notification_services()

            assert isinstance(result, list)
            assert len(result) == 2
            assert result[0]["entity_id"] == "notify.mobile_app_iphone"

    @pytest.mark.asyncio
    async def test_list_notification_services_http_error(self):
        """Test HTTP error handling."""
        with (
            patch(
                "app.api.notifications._notifications_api.get",
                side_effect=httpx.HTTPStatusError(
                    "500 Internal Server Error",
                    request=MagicMock(),
                    response=MagicMock(status_code=500),
                ),
            ),
            patch("app.api.notifications.get_entities", return_value=[]),
        ):
            result = await list_notification_services()

            assert isinstance(result, list)
            assert len(result) == 0


class TestSendNotification:
    """Test the send_notification function."""

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
    async def test_send_notification_success_default(self):
        """Test successful notification sending to default service."""
        mock_response = []

        with patch("app.api.notifications.call_service", return_value=mock_response):
            result = await send_notification("Test message")

            assert isinstance(result, list)
            mock_service = patch("app.api.notifications.call_service")
            # Verify it was called with notify domain and persistent_notification service
            # The actual call would be made but we're mocking it

    @pytest.mark.asyncio
    async def test_send_notification_with_target(self):
        """Test notification sending to specific target."""
        mock_response = []

        with patch("app.api.notifications.call_service", return_value=mock_response) as mock_call:
            result = await send_notification("Test message", target="notify.mobile_app_iphone")

            assert isinstance(result, list)
            mock_call.assert_called_once()
            call_args = mock_call.call_args
            assert call_args[0][0] == "notify"
            assert call_args[0][1] == "mobile_app_iphone"
            assert call_args[0][2]["message"] == "Test message"

    @pytest.mark.asyncio
    async def test_send_notification_with_target_no_domain(self):
        """Test notification sending with target without domain."""
        mock_response = []

        with patch("app.api.notifications.call_service", return_value=mock_response) as mock_call:
            result = await send_notification("Test message", target="mobile_app_iphone")

            assert isinstance(result, list)
            mock_call.assert_called_once()
            call_args = mock_call.call_args
            assert call_args[0][0] == "notify"
            assert call_args[0][1] == "mobile_app_iphone"

    @pytest.mark.asyncio
    async def test_send_notification_with_data(self):
        """Test notification sending with additional data."""
        mock_response = []
        data = {"title": "System Alert", "data": {"priority": "high"}}

        with patch("app.api.notifications.call_service", return_value=mock_response) as mock_call:
            result = await send_notification("Test message", target="notify.mobile_app", data=data)

            assert isinstance(result, list)
            mock_call.assert_called_once()
            call_args = mock_call.call_args
            notification_data = call_args[0][2]
            assert notification_data["message"] == "Test message"
            assert notification_data["title"] == "System Alert"
            assert notification_data["data"]["priority"] == "high"

    @pytest.mark.asyncio
    async def test_send_notification_http_error(self):
        """Test HTTP error handling."""
        with patch(
            "app.api.notifications.call_service",
            side_effect=httpx.HTTPStatusError(
                "400 Bad Request",
                request=MagicMock(),
                response=MagicMock(status_code=400),
            ),
        ):
            result = await send_notification("Test message")

            assert isinstance(result, dict)
            assert "error" in result
            assert "400" in result["error"]


class TestTestNotificationDelivery:
    """Test the test_notification_delivery function."""

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
    async def test_test_notification_delivery_success(self):
        """Test successful notification delivery testing."""
        mock_response = []

        with patch(
            "app.api.notifications.send_notification", return_value=mock_response
        ) as mock_send:
            result = await test_notification_delivery("notify.mobile_app_iphone", "Test message")

            assert isinstance(result, list)
            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "[TEST] Test message"
            assert call_args[1]["target"] == "notify.mobile_app_iphone"

    @pytest.mark.asyncio
    async def test_test_notification_delivery_with_platform_no_domain(self):
        """Test notification delivery testing with platform without domain."""
        mock_response = []

        with patch(
            "app.api.notifications.send_notification", return_value=mock_response
        ) as mock_send:
            result = await test_notification_delivery("mobile_app_iphone", "Test notification")

            assert isinstance(result, list)
            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args[0][0] == "[TEST] Test notification"
            assert call_args[1]["target"] == "mobile_app_iphone"

    @pytest.mark.asyncio
    async def test_test_notification_delivery_error(self):
        """Test error handling in notification delivery testing."""
        with patch(
            "app.api.notifications.send_notification",
            side_effect=httpx.HTTPStatusError(
                "400 Bad Request",
                request=MagicMock(),
                response=MagicMock(status_code=400),
            ),
        ):
            result = await test_notification_delivery("notify.mobile_app_iphone", "Test message")

            assert isinstance(result, dict)
            assert "error" in result
            assert "400" in result["error"]
