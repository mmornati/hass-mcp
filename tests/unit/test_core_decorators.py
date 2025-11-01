"""Unit tests for app.core.decorators module."""

import inspect
from typing import Any
from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.core.decorators import async_handler, handle_api_errors


class TestHandleAPIErrors:
    """Test the handle_api_errors decorator."""

    def test_handle_api_errors_preserves_function_metadata(self):
        """Test that handle_api_errors preserves function metadata."""

        @handle_api_errors
        async def test_function() -> dict[str, str]:
            """Test function docstring."""
            return {}

        # Check docstring is preserved
        assert test_function.__doc__ == "Test function docstring."

        # Check return annotation is preserved
        signature = inspect.signature(test_function)
        assert "dict" in str(signature.return_annotation).lower()

    @pytest.mark.asyncio
    async def test_handle_api_errors_returns_dict_error_for_dict_function(self):
        """Test that handle_api_errors returns dict error for dict return type."""

        @handle_api_errors
        async def test_function() -> dict[str, Any]:
            """Test function that returns a dict."""
            raise httpx.ConnectError("Connection failed")

        with patch("app.core.decorators.HA_TOKEN", "test_token"):
            result = await test_function()

            assert isinstance(result, dict)
            assert "error" in result
            assert "Connection error" in result["error"]

    @pytest.mark.asyncio
    async def test_handle_api_errors_returns_list_error_for_list_function(self):
        """Test that handle_api_errors returns list error for list return type."""

        @handle_api_errors
        async def test_function() -> list[dict[str, Any]]:
            """Test function that returns a list."""
            raise httpx.ConnectError("Connection failed")

        with patch("app.core.decorators.HA_TOKEN", "test_token"):
            result = await test_function()

            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], dict)
            assert "error" in result[0]

    @pytest.mark.asyncio
    async def test_handle_api_errors_returns_string_error_for_string_function(self):
        """Test that handle_api_errors returns string error for string return type."""

        @handle_api_errors
        async def test_function() -> str:
            """Test function that returns a string."""
            raise httpx.ConnectError("Connection failed")

        with patch("app.core.decorators.HA_TOKEN", "test_token"):
            result = await test_function()

            assert isinstance(result, str)
            assert "Connection error" in result

    @pytest.mark.asyncio
    async def test_handle_api_errors_handles_connection_error(self):
        """Test that handle_api_errors handles connection errors."""

        @handle_api_errors
        async def test_function() -> dict[str, Any]:
            """Test function."""
            raise httpx.ConnectError("Connection failed")

        with patch("app.core.decorators.HA_TOKEN", "test_token"):
            result = await test_function()

            assert "error" in result
            assert "Connection error" in result["error"]

    @pytest.mark.asyncio
    async def test_handle_api_errors_handles_timeout_error(self):
        """Test that handle_api_errors handles timeout errors."""

        @handle_api_errors
        async def test_function() -> dict[str, Any]:
            """Test function."""
            raise httpx.TimeoutException("Request timeout")

        with patch("app.core.decorators.HA_TOKEN", "test_token"):
            result = await test_function()

            assert "error" in result
            assert "Timeout error" in result["error"]

    @pytest.mark.asyncio
    async def test_handle_api_errors_handles_http_status_error(self):
        """Test that handle_api_errors handles HTTP status errors."""

        @handle_api_errors
        async def test_function() -> dict[str, Any]:
            """Test function."""
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.reason_phrase = "Not Found"
            raise httpx.HTTPStatusError("Not found", request=MagicMock(), response=mock_response)

        with patch("app.core.decorators.HA_TOKEN", "test_token"):
            result = await test_function()

            assert "error" in result
            assert "HTTP error" in result["error"]
            assert "404" in result["error"]

    @pytest.mark.asyncio
    async def test_handle_api_errors_handles_request_error(self):
        """Test that handle_api_errors handles request errors."""

        @handle_api_errors
        async def test_function() -> dict[str, Any]:
            """Test function."""
            raise httpx.RequestError("Request failed")

        with patch("app.core.decorators.HA_TOKEN", "test_token"):
            result = await test_function()

            assert "error" in result
            assert "Error connecting" in result["error"]

    @pytest.mark.asyncio
    async def test_handle_api_errors_handles_generic_exception(self):
        """Test that handle_api_errors handles generic exceptions."""

        @handle_api_errors
        async def test_function() -> dict[str, Any]:
            """Test function."""
            raise ValueError("Something went wrong")

        with patch("app.core.decorators.HA_TOKEN", "test_token"):
            result = await test_function()

            assert "error" in result
            assert "Unexpected error" in result["error"]

    @pytest.mark.asyncio
    async def test_handle_api_errors_handles_missing_token(self):
        """Test that handle_api_errors handles missing token."""

        @handle_api_errors
        async def test_function() -> dict[str, Any]:
            """Test function."""
            return {"success": True}

        with patch("app.core.decorators.HA_TOKEN", None):
            result = await test_function()

            assert "error" in result
            assert "No Home Assistant token" in result["error"]

    @pytest.mark.asyncio
    async def test_handle_api_errors_passes_through_successful_call(self):
        """Test that handle_api_errors passes through successful calls."""

        @handle_api_errors
        async def test_function() -> dict[str, str]:
            """Test function."""
            return {"success": True}

        with patch("app.core.decorators.HA_TOKEN", "test_token"):
            result = await test_function()

            assert result == {"success": True}


class TestAsyncHandler:
    """Test the async_handler decorator."""

    def test_async_handler_preserves_function_metadata(self):
        """Test that async_handler preserves function metadata."""

        @async_handler("test_command")
        async def test_function(arg1: str, arg2: int = 0) -> str:
            """Test function docstring."""
            return f"{arg1}_{arg2}"

        # Check docstring is preserved
        assert test_function.__doc__ == "Test function docstring."

        # Check signature is preserved
        signature = inspect.signature(test_function)
        assert "arg1" in signature.parameters
        assert "arg2" in signature.parameters

    @pytest.mark.asyncio
    async def test_async_handler_logs_command_execution(self, caplog):
        """Test that async_handler logs command execution."""

        @async_handler("test_command")
        async def test_function() -> str:
            """Test function."""
            return "success"

        with caplog.at_level("INFO"):
            result = await test_function()

            assert result == "success"
            assert "Executing command: test_command" in caplog.text

    @pytest.mark.asyncio
    async def test_async_handler_passes_through_function_result(self):
        """Test that async_handler passes through function result."""

        @async_handler("test_command")
        async def test_function(arg1: str, arg2: int = 0) -> str:
            """Test function."""
            return f"{arg1}_{arg2}"

        result = await test_function("val1", arg2=5)

        assert result == "val1_5"

    @pytest.mark.asyncio
    async def test_async_handler_preserves_exceptions(self):
        """Test that async_handler preserves exceptions."""

        @async_handler("test_command")
        async def test_function() -> str:
            """Test function."""
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            await test_function()
