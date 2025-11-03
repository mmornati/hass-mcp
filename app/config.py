import os

# Home Assistant configuration
HA_URL: str = os.environ.get("HA_URL", "http://localhost:8123")
HA_TOKEN: str = os.environ.get("HA_TOKEN", "")

# Cache configuration
CACHE_ENABLED: bool = os.environ.get("HASS_MCP_CACHE_ENABLED", "true").lower() in (
    "true",
    "1",
    "yes",
)
CACHE_BACKEND: str = os.environ.get("HASS_MCP_CACHE_BACKEND", "memory").lower()
CACHE_DEFAULT_TTL: int = int(os.environ.get("HASS_MCP_CACHE_DEFAULT_TTL", "300"))
CACHE_MAX_SIZE: int = int(os.environ.get("HASS_MCP_CACHE_MAX_SIZE", "1000"))
REDIS_URL: str | None = os.environ.get("HASS_MCP_CACHE_REDIS_URL")
CACHE_DIR: str = os.environ.get("HASS_MCP_CACHE_DIR", ".cache")


def get_ha_headers() -> dict:
    """Return the headers needed for Home Assistant API requests"""
    headers = {
        "Content-Type": "application/json",
    }

    # Only add Authorization header if token is provided
    if HA_TOKEN:
        headers["Authorization"] = f"Bearer {HA_TOKEN}"

    return headers
