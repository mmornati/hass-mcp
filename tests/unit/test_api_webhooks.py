"""Unit tests for app.api.webhooks module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api.webhooks import list_webhooks, test_webhook


class TestListWebhooks:
    """Test the list_webhooks function."""

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
    async def test_list_webhooks_success(self):
        """Test successful retrieval of webhook information."""
        result = await list_webhooks()

        assert isinstance(result, list)
        assert len(result) == 1
        assert (
            result[0]["note"]
            == "Webhooks are typically defined in configuration.yaml or automation/script triggers"
        )
        assert result[0]["webhook_url_format"] == "/api/webhook/{webhook_id}"
        assert result[0]["authentication"] == "Webhooks don't require authentication token"


class TestTestWebhook:
    """Test the test_webhook function."""

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
    async def test_test_webhook_success_with_json(self):
        """Test successful webhook test with JSON response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": "Webhook triggered successfully"}
        mock_response.text = ""

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.api.webhooks.get_client", return_value=mock_client):
            result = await test_webhook("my_webhook", {"entity_id": "light.living_room"})

            assert isinstance(result, dict)
            assert result["status"] == "success"
            assert result["status_code"] == 200
            assert result["response_json"] == {"message": "Webhook triggered successfully"}
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[0][0] == "http://localhost:8123/api/webhook/my_webhook"
            assert call_args[1]["json"] == {"entity_id": "light.living_room"}

    @pytest.mark.asyncio
    async def test_test_webhook_success_with_text(self):
        """Test successful webhook test with text response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Not JSON")
        mock_response.text = "Webhook triggered successfully"

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.api.webhooks.get_client", return_value=mock_client):
            result = await test_webhook("my_webhook")

            assert isinstance(result, dict)
            assert result["status"] == "success"
            assert result["status_code"] == 200
            assert result["response_text"] == "Webhook triggered successfully"

    @pytest.mark.asyncio
    async def test_test_webhook_success_with_long_text(self):
        """Test successful webhook test with long text response (truncated)."""
        long_text = "x" * 600  # Longer than 500 character limit

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Not JSON")
        mock_response.text = long_text

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.api.webhooks.get_client", return_value=mock_client):
            result = await test_webhook("my_webhook")

            assert isinstance(result, dict)
            assert result["status"] == "success"
            assert result["status_code"] == 200
            assert len(result["response_text"]) == 500  # Truncated to 500

    @pytest.mark.asyncio
    async def test_test_webhook_without_payload(self):
        """Test webhook test without payload."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": "OK"}
        mock_response.text = ""

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.api.webhooks.get_client", return_value=mock_client):
            result = await test_webhook("my_webhook")

            assert isinstance(result, dict)
            assert result["status"] == "success"
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[1]["json"] == {}  # Empty dict for None payload

    @pytest.mark.asyncio
    async def test_test_webhook_error_status(self):
        """Test webhook test with error status code."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Webhook not found"

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.api.webhooks.get_client", return_value=mock_client):
            result = await test_webhook("nonexistent_webhook")

            assert isinstance(result, dict)
            assert result["status"] == "error"
            assert result["status_code"] == 404
            assert result["error"] == "Webhook request failed"
            assert result["response_text"] == "Webhook not found"

    @pytest.mark.asyncio
    async def test_test_webhook_error_with_empty_text(self):
        """Test webhook test with error status and empty text."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = None

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.api.webhooks.get_client", return_value=mock_client):
            result = await test_webhook("my_webhook")

            assert isinstance(result, dict)
            assert result["status"] == "error"
            assert result["status_code"] == 500
            assert result["response_text"] == ""  # Empty string for None text

    @pytest.mark.asyncio
    async def test_test_webhook_error_with_long_text(self):
        """Test webhook test with error status and long text (truncated)."""
        long_text = "x" * 600  # Longer than 500 character limit

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = long_text

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.api.webhooks.get_client", return_value=mock_client):
            result = await test_webhook("my_webhook")

            assert isinstance(result, dict)
            assert result["status"] == "error"
            assert result["status_code"] == 400
            assert len(result["response_text"]) == 500  # Truncated to 500
