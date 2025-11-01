"""Backups API module for hass-mcp.

This module provides functions for interacting with Home Assistant backups via Supervisor API.
Backups are only available on Home Assistant OS with Supervisor.
"""

import logging
from typing import Any

import httpx

from app.config import HA_URL, get_ha_headers
from app.core import get_client
from app.core.decorators import handle_api_errors

logger = logging.getLogger(__name__)


@handle_api_errors
async def list_backups() -> dict[str, Any]:
    """
    List available backups (if Supervisor API available).

    Returns:
        Dictionary containing:
        - available: Boolean indicating if Supervisor API is available
        - backups: List of backup dictionaries (if available)
        - error: Error message (if Supervisor API not available)

    Example response:
        {
            "available": True,
            "backups": [
                {
                    "slug": "20250101_120000",
                    "name": "Full Backup 2025-01-01",
                    "date": "2025-01-01T12:00:00",
                    "size": 1024000,
                    "type": "full"
                }
            ]
        }

    Note:
        Backup/restore is only available for Home Assistant OS with Supervisor.
        If Supervisor API is not available (404), returns available: False.
        This feature requires Home Assistant OS installation.

    Best Practices:
        - Check available flag before attempting operations
        - Use to list existing backups before creating new ones
        - Use to verify backup creation succeeded
        - Only available on Home Assistant OS installations
    """
    client = await get_client()

    try:
        response = await client.get(
            f"{HA_URL}/api/hassio/backups",
            headers=get_ha_headers(),
        )

        if response.status_code == 404:
            return {
                "error": "Supervisor API not available",
                "note": "Backup/restore is only available for Home Assistant OS with Supervisor",
                "available": False,
            }

        response.raise_for_status()
        data = response.json().get("data", {})
        return {
            "available": True,
            "backups": data.get("backups", []),
        }
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {
                "error": "Supervisor API not available",
                "note": "Backup/restore is only available for Home Assistant OS with Supervisor",
                "available": False,
            }
        raise
    except Exception:  # nosec B112
        return {
            "error": "Supervisor API not available",
            "note": "Backup/restore is only available for Home Assistant OS with Supervisor",
            "available": False,
        }


@handle_api_errors
async def create_backup(
    name: str, password: str | None = None, full: bool = True
) -> dict[str, Any]:
    """
    Create a backup (if Supervisor API available).

    Args:
        name: Backup name (e.g., 'Full Backup 2025-01-01')
        password: Optional password for encrypted backup
        full: If True, creates full backup; if False, creates partial backup

    Returns:
        Dictionary containing backup creation response:
        - available: Boolean indicating if Supervisor API is available
        - slug: Backup slug identifier (if successful)
        - error: Error message (if Supervisor API not available or creation failed)

    Examples:
        name="Full Backup 2025-01-01", password=None, full=True
        name="Partial Backup", password="secret123", full=False

    Note:
        Backup/restore is only available for Home Assistant OS with Supervisor.
        Full backups include all data, partial backups allow selective restoration.
        Password-protected backups require password for restoration.
        If Supervisor API is not available (404), returns available: False.

    Best Practices:
        - Use descriptive backup names with dates
        - Create full backups before major changes
        - Use partial backups for specific components
        - Store passwords securely for encrypted backups
        - Only available on Home Assistant OS installations
    """
    client = await get_client()

    endpoint = "new/full" if full else "new/partial"

    payload = {"name": name}
    if password:
        payload["password"] = password

    try:
        response = await client.post(
            f"{HA_URL}/api/hassio/backups/{endpoint}",
            headers=get_ha_headers(),
            json=payload,
        )

        if response.status_code == 404:
            return {
                "error": "Supervisor API not available",
                "note": "Backup/restore is only available for Home Assistant OS with Supervisor",
                "available": False,
            }

        response.raise_for_status()
        data = response.json().get("data", {})
        return {
            "available": True,
            "slug": data.get("slug"),
            "message": "Backup created successfully",
        }
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {
                "error": "Supervisor API not available",
                "note": "Backup/restore is only available for Home Assistant OS with Supervisor",
                "available": False,
            }
        raise
    except Exception:  # nosec B112
        return {
            "error": "Supervisor API not available",
            "note": "Backup/restore is only available for Home Assistant OS with Supervisor",
            "available": False,
        }


@handle_api_errors
async def restore_backup(
    backup_slug: str, password: str | None = None, full: bool = True
) -> dict[str, Any]:
    """
    Restore a backup (if Supervisor API available).

    Args:
        backup_slug: Backup slug identifier (e.g., '20250101_120000')
        password: Optional password for encrypted backup
        full: If True, restores full backup; if False, restores partial backup

    Returns:
        Dictionary containing restore response:
        - available: Boolean indicating if Supervisor API is available
        - message: Restore status message
        - error: Error message (if Supervisor API not available or restore failed)

    Examples:
        backup_slug="20250101_120000", password=None, full=True
        backup_slug="backup_2025", password="secret123", full=False

    Note:
        Backup/restore is only available for Home Assistant OS with Supervisor.
        Full restore restores entire system, partial restore allows selective restoration.
        Password-protected backups require password for restoration.
        Restoring will restart Home Assistant and may take several minutes.
        If Supervisor API is not available (404), returns available: False.

    Best Practices:
        - Verify backup exists before restoring
        - Use full restore for complete system recovery
        - Use partial restore for specific components
        - Provide password for encrypted backups
        - Only available on Home Assistant OS installations
        - System will restart after restore
    """
    client = await get_client()

    endpoint = "restore/full" if full else "restore/partial"

    payload = {}
    if password:
        payload["password"] = password

    try:
        response = await client.post(
            f"{HA_URL}/api/hassio/backups/{backup_slug}/{endpoint}",
            headers=get_ha_headers(),
            json=payload,
        )

        if response.status_code == 404:
            return {
                "error": "Supervisor API not available",
                "note": "Backup/restore is only available for Home Assistant OS with Supervisor",
                "available": False,
            }

        response.raise_for_status()
        return {
            "available": True,
            "message": "Backup restore initiated successfully",
        }
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {
                "error": "Supervisor API not available",
                "note": "Backup/restore is only available for Home Assistant OS with Supervisor",
                "available": False,
            }
        raise
    except Exception:  # nosec B112
        return {
            "error": "Supervisor API not available",
            "note": "Backup/restore is only available for Home Assistant OS with Supervisor",
            "available": False,
        }


@handle_api_errors
async def delete_backup(backup_slug: str) -> dict[str, Any]:
    """
    Delete a backup (if Supervisor API available).

    Args:
        backup_slug: Backup slug identifier (e.g., '20250101_120000')

    Returns:
        Dictionary containing delete response:
        - available: Boolean indicating if Supervisor API is available
        - message: Delete status message
        - error: Error message (if Supervisor API not available or delete failed)

    Examples:
        backup_slug="20250101_120000"

    Note:
        Backup/restore is only available for Home Assistant OS with Supervisor.
        Deleting a backup is permanent and cannot be undone.
        If Supervisor API is not available (404), returns available: False.

    Best Practices:
        - Verify backup slug exists before deleting
        - Use with caution as deletion is permanent
        - Only delete backups you no longer need
        - Only available on Home Assistant OS installations
    """
    client = await get_client()

    try:
        response = await client.delete(
            f"{HA_URL}/api/hassio/backups/{backup_slug}",
            headers=get_ha_headers(),
        )

        if response.status_code == 404:
            return {
                "error": "Supervisor API not available",
                "note": "Backup/restore is only available for Home Assistant OS with Supervisor",
                "available": False,
            }

        response.raise_for_status()
        return {
            "available": True,
            "message": "Backup deleted successfully",
        }
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {
                "error": "Supervisor API not available",
                "note": "Backup/restore is only available for Home Assistant OS with Supervisor",
                "available": False,
            }
        raise
    except Exception:  # nosec B112
        return {
            "error": "Supervisor API not available",
            "note": "Backup/restore is only available for Home Assistant OS with Supervisor",
            "available": False,
        }
