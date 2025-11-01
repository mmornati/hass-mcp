"""Unit tests for app.api.backups module."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.api.backups import (
    create_backup,
    delete_backup,
    list_backups,
    restore_backup,
)


class TestListBackups:
    """Test the list_backups function."""

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
    async def test_list_backups_success(self):
        """Test successful retrieval of backups."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "backups": [
                    {
                        "slug": "20250101_120000",
                        "name": "Full Backup 2025-01-01",
                        "date": "2025-01-01T12:00:00",
                        "size": 1024000,
                        "type": "full",
                    }
                ]
            }
        }
        mock_response.raise_for_status.return_value = None

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("app.api.backups.get_client", return_value=mock_client):
            result = await list_backups()

            assert isinstance(result, dict)
            assert result["available"] is True
            assert len(result["backups"]) == 1
            assert result["backups"][0]["slug"] == "20250101_120000"
            assert result["backups"][0]["name"] == "Full Backup 2025-01-01"
            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert call_args[0][0] == "http://localhost:8123/api/hassio/backups"

    @pytest.mark.asyncio
    async def test_list_backups_supervisor_unavailable_404(self):
        """Test when Supervisor API returns 404."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("app.api.backups.get_client", return_value=mock_client):
            result = await list_backups()

            assert isinstance(result, dict)
            assert result["available"] is False
            assert "error" in result
            assert "Supervisor API not available" in result["error"]

    @pytest.mark.asyncio
    async def test_list_backups_supervisor_unavailable_http_error(self):
        """Test when Supervisor API raises HTTPStatusError with 404."""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "404 Not Found",
                request=MagicMock(),
                response=MagicMock(status_code=404),
            )
        )

        with patch("app.api.backups.get_client", return_value=mock_client):
            result = await list_backups()

            assert isinstance(result, dict)
            assert result["available"] is False
            assert "error" in result
            assert "Supervisor API not available" in result["error"]

    @pytest.mark.asyncio
    async def test_list_backups_supervisor_unavailable_exception(self):
        """Test when Supervisor API raises a generic exception."""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=Exception("Connection error"))

        with patch("app.api.backups.get_client", return_value=mock_client):
            result = await list_backups()

            assert isinstance(result, dict)
            assert result["available"] is False
            assert "error" in result
            assert "Supervisor API not available" in result["error"]

    @pytest.mark.asyncio
    async def test_list_backups_empty_list(self):
        """Test when no backups exist."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"backups": []}}
        mock_response.raise_for_status.return_value = None

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("app.api.backups.get_client", return_value=mock_client):
            result = await list_backups()

            assert isinstance(result, dict)
            assert result["available"] is True
            assert result["backups"] == []


class TestCreateBackup:
    """Test the create_backup function."""

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
    async def test_create_backup_success_full(self):
        """Test successful creation of a full backup."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"slug": "20250101_120000"}}
        mock_response.raise_for_status.return_value = None

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.api.backups.get_client", return_value=mock_client) as mock_get_client:
            result = await create_backup("Full Backup 2025-01-01", None, True)

            assert isinstance(result, dict)
            assert result["available"] is True
            assert result["slug"] == "20250101_120000"
            assert result["message"] == "Backup created successfully"
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[0][0] == "http://localhost:8123/api/hassio/backups/new/full"
            assert call_args[1]["json"] == {"name": "Full Backup 2025-01-01"}

    @pytest.mark.asyncio
    async def test_create_backup_success_partial(self):
        """Test successful creation of a partial backup."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"slug": "20250101_130000"}}
        mock_response.raise_for_status.return_value = None

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.api.backups.get_client", return_value=mock_client):
            result = await create_backup("Partial Backup", None, False)

            assert isinstance(result, dict)
            assert result["available"] is True
            assert result["slug"] == "20250101_130000"
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[0][0] == "http://localhost:8123/api/hassio/backups/new/partial"

    @pytest.mark.asyncio
    async def test_create_backup_with_password(self):
        """Test creation of a password-protected backup."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"slug": "20250101_140000"}}
        mock_response.raise_for_status.return_value = None

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.api.backups.get_client", return_value=mock_client):
            result = await create_backup("Encrypted Backup", "secret123", True)

            assert isinstance(result, dict)
            assert result["available"] is True
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[1]["json"] == {"name": "Encrypted Backup", "password": "secret123"}

    @pytest.mark.asyncio
    async def test_create_backup_supervisor_unavailable_404(self):
        """Test when Supervisor API returns 404."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.api.backups.get_client", return_value=mock_client):
            result = await create_backup("Full Backup 2025-01-01", None, True)

            assert isinstance(result, dict)
            assert result["available"] is False
            assert "error" in result
            assert "Supervisor API not available" in result["error"]

    @pytest.mark.asyncio
    async def test_create_backup_supervisor_unavailable_http_error(self):
        """Test when Supervisor API raises HTTPStatusError with 404."""
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "404 Not Found",
                request=MagicMock(),
                response=MagicMock(status_code=404),
            )
        )

        with patch("app.api.backups.get_client", return_value=mock_client):
            result = await create_backup("Full Backup 2025-01-01", None, True)

            assert isinstance(result, dict)
            assert result["available"] is False
            assert "error" in result


class TestRestoreBackup:
    """Test the restore_backup function."""

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
    async def test_restore_backup_success_full(self):
        """Test successful restoration of a full backup."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_response.raise_for_status.return_value = None

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.api.backups.get_client", return_value=mock_client):
            result = await restore_backup("20250101_120000", None, True)

            assert isinstance(result, dict)
            assert result["available"] is True
            assert result["message"] == "Backup restore initiated successfully"
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert (
                call_args[0][0]
                == "http://localhost:8123/api/hassio/backups/20250101_120000/restore/full"
            )
            assert call_args[1]["json"] == {}

    @pytest.mark.asyncio
    async def test_restore_backup_success_partial(self):
        """Test successful restoration of a partial backup."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_response.raise_for_status.return_value = None

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.api.backups.get_client", return_value=mock_client):
            result = await restore_backup("20250101_120000", None, False)

            assert isinstance(result, dict)
            assert result["available"] is True
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert (
                call_args[0][0]
                == "http://localhost:8123/api/hassio/backups/20250101_120000/restore/partial"
            )

    @pytest.mark.asyncio
    async def test_restore_backup_with_password(self):
        """Test restoration of a password-protected backup."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_response.raise_for_status.return_value = None

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.api.backups.get_client", return_value=mock_client):
            result = await restore_backup("20250101_120000", "secret123", True)

            assert isinstance(result, dict)
            assert result["available"] is True
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[1]["json"] == {"password": "secret123"}

    @pytest.mark.asyncio
    async def test_restore_backup_supervisor_unavailable_404(self):
        """Test when Supervisor API returns 404."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.api.backups.get_client", return_value=mock_client):
            result = await restore_backup("20250101_120000", None, True)

            assert isinstance(result, dict)
            assert result["available"] is False
            assert "error" in result

    @pytest.mark.asyncio
    async def test_restore_backup_supervisor_unavailable_http_error(self):
        """Test when Supervisor API raises HTTPStatusError with 404."""
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "404 Not Found",
                request=MagicMock(),
                response=MagicMock(status_code=404),
            )
        )

        with patch("app.api.backups.get_client", return_value=mock_client):
            result = await restore_backup("20250101_120000", None, True)

            assert isinstance(result, dict)
            assert result["available"] is False
            assert "error" in result


class TestDeleteBackup:
    """Test the delete_backup function."""

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
    async def test_delete_backup_success(self):
        """Test successful deletion of a backup."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_response.raise_for_status.return_value = None

        mock_client = AsyncMock()
        mock_client.delete = AsyncMock(return_value=mock_response)

        with patch("app.api.backups.get_client", return_value=mock_client):
            result = await delete_backup("20250101_120000")

            assert isinstance(result, dict)
            assert result["available"] is True
            assert result["message"] == "Backup deleted successfully"
            mock_client.delete.assert_called_once()
            call_args = mock_client.delete.call_args
            assert call_args[0][0] == "http://localhost:8123/api/hassio/backups/20250101_120000"

    @pytest.mark.asyncio
    async def test_delete_backup_supervisor_unavailable_404(self):
        """Test when Supervisor API returns 404."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        mock_client = AsyncMock()
        mock_client.delete = AsyncMock(return_value=mock_response)

        with patch("app.api.backups.get_client", return_value=mock_client):
            result = await delete_backup("20250101_120000")

            assert isinstance(result, dict)
            assert result["available"] is False
            assert "error" in result
            assert "Supervisor API not available" in result["error"]

    @pytest.mark.asyncio
    async def test_delete_backup_supervisor_unavailable_http_error(self):
        """Test when Supervisor API raises HTTPStatusError with 404."""
        mock_client = AsyncMock()
        mock_client.delete = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "404 Not Found",
                request=MagicMock(),
                response=MagicMock(status_code=404),
            )
        )

        with patch("app.api.backups.get_client", return_value=mock_client):
            result = await delete_backup("20250101_120000")

            assert isinstance(result, dict)
            assert result["available"] is False
            assert "error" in result

    @pytest.mark.asyncio
    async def test_delete_backup_supervisor_unavailable_exception(self):
        """Test when Supervisor API raises a generic exception."""
        mock_client = AsyncMock()
        mock_client.delete = AsyncMock(side_effect=Exception("Connection error"))

        with patch("app.api.backups.get_client", return_value=mock_client):
            result = await delete_backup("20250101_120000")

            assert isinstance(result, dict)
            assert result["available"] is False
            assert "error" in result
            assert "Supervisor API not available" in result["error"]
