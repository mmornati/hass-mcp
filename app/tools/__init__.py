"""Tools module for hass-mcp.

This module contains MCP tools organized by domain.
Tools are thin wrappers around API functions that expose
Home Assistant functionality via the Model Context Protocol.
"""

from app.tools import entities

__all__ = ["entities"]

