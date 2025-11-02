#!/bin/bash
# Wait for Home Assistant to be ready for integration testing

set -e

HA_URL=${HA_URL:-"http://localhost:18123"}
HA_TOKEN=${HA_TOKEN:-"test-token-change-me"}
MAX_ATTEMPTS=60
ATTEMPT=0

echo "Waiting for Home Assistant to be ready at $HA_URL..."

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if curl -s -f -H "Authorization: Bearer $HA_TOKEN" "$HA_URL/api/" > /dev/null 2>&1; then
        echo "✅ Home Assistant is ready!"
        exit 0
    fi

    ATTEMPT=$((ATTEMPT + 1))
    if [ $((ATTEMPT % 5)) -eq 0 ]; then
        echo "Still waiting... (attempt $ATTEMPT/$MAX_ATTEMPTS)"
    fi

    sleep 2
done

echo "❌ Home Assistant failed to start within $MAX_ATTEMPTS attempts"
exit 1
