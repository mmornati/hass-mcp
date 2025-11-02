#!/usr/bin/env python3
"""Create a test long-lived access token for Home Assistant testing.

This script creates a persistent access token for integration testing.
The token is stored in tests/fixtures/ha_storage/auth_provider.homeassistant.json
"""

import json
import secrets
from pathlib import Path


def create_test_token(username: str = "test_user") -> str:
    """Create a long-lived access token for testing."""
    token = secrets.token_urlsafe(32)

    # Create storage directory if it doesn't exist
    storage_dir = Path(__file__).parent / "ha_storage" / ".storage"
    storage_dir.mkdir(parents=True, exist_ok=True)

    # Create auth data
    auth_data = {
        "version": 1,
        "key": secrets.token_hex(32),
        "data": {
            "users": [
                {
                    "id": username,
                    "username": username,
                    "is_owner": True,
                    "is_active": True,
                    "system_generated": False,
                    "local_only": False,
                    "credentials": [],
                    "mfa_modules": [],
                }
            ],
            "refresh_tokens": [
                {
                    "token": token,
                    "user_id": username,
                    "client_id": None,
                    "client_name": None,
                    "client_icon": None,
                    "token_type": "normal",
                    "created_at": "2024-01-01T00:00:00.000Z",
                    "expires_at": None,
                    "is_current": False,
                }
            ],
        },
    }

    # Write auth file
    auth_file = storage_dir / "auth_provider.homeassistant.json"
    with open(auth_file, "w") as f:
        json.dump(auth_data, f, indent=2)

    return token


if __name__ == "__main__":
    token = create_test_token()
    print(token)
