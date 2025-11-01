"""Unit tests for app.api.base module."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.api.base import BaseAPI


class TestBaseAPI:
    """Test the BaseAPI class."""

    @pytest.mark.asyncio
    async def test_init(self):
        """Test BaseAPI initialization."""
        api = BaseAPI()
        assert api._client is None

    @pytest.mark.asyncio
    async def test_get_method_success(self):
        """Test GET method with successful response."""
        api = BaseAPI()
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": True}
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("app.api.base.get_client", return_value=mock_client):
            result = await api.get("/api/states")

            assert result == {"success": True}
            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert "/api/states" in call_args[0][0]
            assert "headers" in call_args[1]

    @pytest.mark.asyncio
    async def test_get_method_with_params(self):
        """Test GET method with query parameters."""
        api = BaseAPI()
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = [{"id": "1"}]
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("app.api.base.get_client", return_value=mock_client):
            result = await api.get("/api/states", params={"limit": 10})

            assert result == [{"id": "1"}]
            call_args = mock_client.get.call_args
            assert call_args[1]["params"] == {"limit": 10}

    @pytest.mark.asyncio
    async def test_post_method_success(self):
        """Test POST method with successful response."""
        api = BaseAPI()
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"result": "ok"}
        mock_response.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.api.base.get_client", return_value=mock_client):
            result = await api.post("/api/services/light/turn_on", data={"entity_id": "light.test"})

            assert result == {"result": "ok"}
            call_args = mock_client.post.call_args
            assert "/api/services/light/turn_on" in call_args[0][0]
            assert call_args[1]["json"] == {"entity_id": "light.test"}

    @pytest.mark.asyncio
    async def test_post_method_empty_data(self):
        """Test POST method with empty data."""
        api = BaseAPI()
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"result": "ok"}
        mock_response.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.api.base.get_client", return_value=mock_client):
            result = await api.post("/api/services/light/turn_on")

            assert result == {"result": "ok"}
            call_args = mock_client.post.call_args
            assert call_args[1]["json"] == {}

    @pytest.mark.asyncio
    async def test_put_method_success(self):
        """Test PUT method with successful response."""
        api = BaseAPI()
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"result": "updated"}
        mock_response.raise_for_status = MagicMock()
        mock_client.put = AsyncMock(return_value=mock_response)

        with patch("app.api.base.get_client", return_value=mock_client):
            result = await api.put("/api/config/area_registry", data={"name": "Kitchen"})

            assert result == {"result": "updated"}
            call_args = mock_client.put.call_args
            assert "/api/config/area_registry" in call_args[0][0]
            assert call_args[1]["json"] == {"name": "Kitchen"}

    @pytest.mark.asyncio
    async def test_delete_method_success(self):
        """Test DELETE method with successful response."""
        api = BaseAPI()
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"result": "deleted"}
        mock_response.raise_for_status = MagicMock()
        mock_client.delete = AsyncMock(return_value=mock_response)

        with patch("app.api.base.get_client", return_value=mock_client):
            result = await api.delete("/api/config/area_registry/abc123")

            assert result == {"result": "deleted"}
            call_args = mock_client.delete.call_args
            assert "/api/config/area_registry/abc123" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_patch_method_success(self):
        """Test PATCH method with successful response."""
        api = BaseAPI()
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"result": "patched"}
        mock_response.raise_for_status = MagicMock()
        mock_client.patch = AsyncMock(return_value=mock_response)

        with patch("app.api.base.get_client", return_value=mock_client):
            result = await api.patch("/api/config/area_registry/abc123", data={"name": "Updated"})

            assert result == {"result": "patched"}
            call_args = mock_client.patch.call_args
            assert "/api/config/area_registry/abc123" in call_args[0][0]
            assert call_args[1]["json"] == {"name": "Updated"}

    @pytest.mark.asyncio
    async def test_client_reuse(self):
        """Test that client is reused across method calls."""
        api = BaseAPI()
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("app.api.base.get_client", return_value=mock_client) as get_client_mock:
            await api.get("/api/states")
            await api.get("/api/states")

            # Client should be fetched only once per instance (cached in self._client)
            assert get_client_mock.call_count == 1  # Called once when _client is None
            # Verify same client instance is reused
            assert api._client is mock_client

    @pytest.mark.asyncio
    async def test_get_method_http_error(self):
        """Test GET method with HTTP error."""
        api = BaseAPI()
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not found", request=MagicMock(), response=mock_response
        )
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("app.api.base.get_client", return_value=mock_client):
            with pytest.raises(httpx.HTTPStatusError):
                await api.get("/api/states/nonexistent")

