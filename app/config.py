import os
import os.path
import logging

# Home Assistant configuration
HA_URL: str = os.environ.get("HA_URL", "http://localhost:8123")
HA_TOKEN: str = os.environ.get("HA_TOKEN", "")

# SSL/TLS Configuration
HA_SSL_VERIFY: str | bool = os.environ.get("HA_SSL_VERIFY", "true")

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


def get_ssl_verify_value() -> str | bool:
    """
    Parse HA_SSL_VERIFY environment variable into httpx-compatible value.

    Returns:
        - True: Use system CA certificates (default)
        - False: Disable SSL verification (for self-signed certificates)
        - str: Path to custom CA certificate bundle

    Examples:
        HA_SSL_VERIFY="true" -> True (system CAs)
        HA_SSL_VERIFY="false" -> False (disable verification)
        HA_SSL_VERIFY="/path/to/ca.pem" -> "/path/to/ca.pem" (custom CA)
    """
    value = HA_SSL_VERIFY
    logger = logging.getLogger(__name__)

    if isinstance(value, str):
        lower_value = value.lower()
        if lower_value in ("true", "1", "yes"):
            return True
        elif lower_value in ("false", "0", "no"):
            return False
        else:
            # Treat as file path - validate it exists
            if os.path.isfile(value):
                return value
            else:
                logger.warning(
                    f"HA_SSL_VERIFY points to non-existent file: {value}. "
                    f"Falling back to system CA certificates."
                )
                return True

    # Default to True (system CAs)
    return True
