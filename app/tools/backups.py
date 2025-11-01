"""Backups MCP tools for hass-mcp.

This module provides MCP tools for interacting with Home Assistant backups via Supervisor API.
These tools are thin wrappers around the backups API layer.
"""

import logging
from typing import Any

from app.api.backups import (
    create_backup,
    delete_backup,
    list_backups,
    restore_backup,
)

logger = logging.getLogger(__name__)


async def list_backups_tool() -> dict[str, Any]:
    """
    List available backups (if Supervisor API available).

    Returns:
        Dictionary containing:
        - available: Boolean indicating if Supervisor API is available
        - backups: List of backup dictionaries (if available)
        - error: Error message (if Supervisor API not available)

    Examples:
        Returns list of backups or error if Supervisor API not available

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
    logger.info("Getting list of backups")
    return await list_backups()


async def create_backup_tool(
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
    logger.info(f"Creating {'full' if full else 'partial'} backup: {name}")
    return await create_backup(name, password, full)


async def restore_backup_tool(
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
    logger.info(
        f"Restoring {'full' if full else 'partial'} backup: {backup_slug}"
        + (" with password" if password else "")
    )
    return await restore_backup(backup_slug, password, full)


async def delete_backup_tool(backup_slug: str) -> dict[str, Any]:
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
    logger.info(f"Deleting backup: {backup_slug}")
    return await delete_backup(backup_slug)
