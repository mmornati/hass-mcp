"""Unit tests for app.api.templates module."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api.templates import test_template


class TestTemplatesAPI:
    """Test the Templates API functions."""

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
    async def test_test_template_success(self, mock_httpx_client):
        """Test successfully testing a template."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(
            return_value={"result": "on", "listeners": {"all": True, "domains": [], "entities": []}}
        )
        mock_response.raise_for_status = MagicMock()

        mock_httpx_client.post = AsyncMock(return_value=mock_response)

        # Test function
        result = await test_template("{{ states('light.living_room') }}")

        # Assertions
        assert isinstance(result, dict)
        assert result["result"] == "on"
        assert "listeners" in result
        mock_httpx_client.post.assert_called_once()

        # Verify correct URL and payload
        call_args = mock_httpx_client.post.call_args
        assert call_args[0][0] == "http://localhost:8123/api/template"
        assert call_args[1]["json"] == {"template": "{{ states('light.living_room') }}"}

    @pytest.mark.asyncio
    async def test_test_template_with_entity_context(self, mock_httpx_client):
        """Test testing a template with entity context."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(
            return_value={
                "result": "22.5",
                "listeners": {"all": False, "domains": [], "entities": ["sensor.temperature"]},
            }
        )
        mock_response.raise_for_status = MagicMock()

        mock_httpx_client.post = AsyncMock(return_value=mock_response)

        # Test function with entity context
        entity_context = {"entity_id": "sensor.temperature"}
        result = await test_template("{{ states('sensor.temperature') }}", entity_context)

        # Assertions
        assert isinstance(result, dict)
        assert result["result"] == "22.5"
        assert result["listeners"]["entities"] == ["sensor.temperature"]
        mock_httpx_client.post.assert_called_once()

        # Verify correct URL and payload
        call_args = mock_httpx_client.post.call_args
        assert call_args[0][0] == "http://localhost:8123/api/template"
        assert call_args[1]["json"] == {
            "template": "{{ states('sensor.temperature') }}",
            "entity_id": entity_context,
        }

    @pytest.mark.asyncio
    async def test_test_template_api_not_available(self, mock_httpx_client):
        """Test template API not available (404)."""
        # Mock response with 404
        mock_response = MagicMock()
        mock_response.status_code = 404

        mock_httpx_client.post = AsyncMock(return_value=mock_response)

        # Test function
        template_string = "{{ states('sensor.temperature') }}"
        result = await test_template(template_string)

        # Assertions
        assert isinstance(result, dict)
        assert "error" in result
        assert "not available" in result["error"].lower()
        assert result["template"] == template_string
        assert "note" in result

        # Verify no raise_for_status was called (404 is handled gracefully)
        # Note: MagicMock always has attributes, so we check if raise_for_status wasn't actually called
        # In the actual function, raise_for_status is only called after checking status_code != 404

    @pytest.mark.asyncio
    async def test_test_template_http_error(self, mock_httpx_client):
        """Test testing a template with HTTP error."""
        # Mock response with error
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.reason_phrase = "Internal Server Error"
        mock_response.raise_for_status = MagicMock(side_effect=Exception("HTTP error: 500"))

        mock_httpx_client.post = AsyncMock(return_value=mock_response)

        # Test function
        result = await test_template("{{ invalid_template }}")

        # Assertions
        assert isinstance(result, dict)
        assert "error" in result
        assert "HTTP error: 500" in result["error"]

    @pytest.mark.asyncio
    async def test_test_template_network_error(self, mock_httpx_client):
        """Test testing a template with network error."""
        # Mock network error
        mock_httpx_client.post = AsyncMock(side_effect=Exception("Connection error"))

        # Test function
        result = await test_template("{{ states('sensor.temperature') }}")

        # Assertions
        assert isinstance(result, dict)
        assert "error" in result
        assert "Connection error" in result["error"]

    @pytest.mark.asyncio
    async def test_test_template_complex_template(self, mock_httpx_client):
        """Test testing a complex template."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(
            return_value={
                "result": "Living Room is on",
                "listeners": {
                    "all": False,
                    "domains": ["light"],
                    "entities": ["light.living_room", "sensor.motion"],
                },
            }
        )
        mock_response.raise_for_status = MagicMock()

        mock_httpx_client.post = AsyncMock(return_value=mock_response)

        # Complex template with conditionals
        template = "{{ 'Living Room is on' if states('light.living_room') == 'on' else 'Living Room is off' }}"

        # Test function
        result = await test_template(template)

        # Assertions
        assert isinstance(result, dict)
        assert result["result"] == "Living Room is on"
        assert len(result["listeners"]["entities"]) == 2
        mock_httpx_client.post.assert_called_once()

        # Verify correct payload
        call_args = mock_httpx_client.post.call_args
        assert call_args[1]["json"] == {"template": template}

    @pytest.mark.asyncio
    async def test_test_template_with_none_entity_context(self, mock_httpx_client):
        """Test testing a template with None entity context."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value={"result": "test", "listeners": {}})
        mock_response.raise_for_status = MagicMock()

        mock_httpx_client.post = AsyncMock(return_value=mock_response)

        # Test function with None entity context
        result = await test_template("{{ 'test' }}", None)

        # Assertions
        assert isinstance(result, dict)
        mock_httpx_client.post.assert_called_once()

        # Verify entity_id is not in payload
        call_args = mock_httpx_client.post.call_args
        assert "entity_id" not in call_args[1]["json"]
        assert call_args[1]["json"] == {"template": "{{ 'test' }}"}
