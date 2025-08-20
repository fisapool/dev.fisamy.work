#!/bin/bash
# Uptime Kuma monitoring setup for Coder deployment
# Requires: UPTIME_KUMA_URL, UPTIME_KUMA_USERNAME, UPTIME_KUMA_PASSWORD in /etc/fisamy/uptime.env

set -euo pipefail

# Source environment variables
if [ -f "/etc/fisamy/uptime.env" ]; then
    # shellcheck disable=SC1091
    source /etc/fisamy/uptime.env
else
    echo "Error: /etc/fisamy/uptime.env not found"
    echo "Please create it with:"
    echo "UPTIME_KUMA_URL=https://your-uptime-kuma.instance"
    echo "UPTIME_KUMA_USERNAME=your_username"
    echo "UPTIME_KUMA_PASSWORD=your_password"
    exit 1
fi

# Check required variables
for var in UPTIME_KUMA_URL UPTIME_KUMA_USERNAME UPTIME_KUMA_PASSWORD; do
    if [ -z "${!var:-}" ]; then
        echo "Error: $var is not set in /etc/fisamy/uptime.env"
        exit 1
    fi
done

echo "Setting up Uptime Kuma monitors for Coder deployment..."

# Login and get token
echo "Logging into Uptime Kuma..."
TOKEN=$(curl -s -X POST "$UPTIME_KUMA_URL/api/login" \
  -H "Content-Type: application/json" \
  --data "{\"username\":\"$UPTIME_KUMA_USERNAME\",\"password\":\"$UPTIME_KUMA_PASSWORD\"}" | jq -r '.token')

if [ "$TOKEN" = "null" ] || [ -z "$TOKEN" ]; then
    echo "Error: Failed to get authentication token"
    exit 1
fi

echo "Successfully authenticated"

# Create monitor for coder.fisamy.work (root URL)
echo "Creating monitor for Coder production..."
CODER_MONITOR=$(curl -s -X POST "$UPTIME_KUMA_URL/api/monitor" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  --data '{
    "name": "Coder Production",
    "url": "https://coder.fisamy.work/",
    "type": "http",
    "interval": 60,
    "retryInterval": 30,
    "maxretries": 3,
    "timeout": 10,
    "httpHeaders": [
      {"key": "User-Agent", "value": "Uptime-Kuma-Monitor"}
    ]
  }')

if echo "$CODER_MONITOR" | jq -e '.ok' >/dev/null 2>&1; then
    echo "✓ Coder production monitor created successfully"
else
    echo "✗ Failed to create Coder monitor:"
    echo "$CODER_MONITOR" | jq -r '.msg // .error // "Unknown error"'
fi

# Create monitor for BFF API health endpoint
echo "Creating monitor for BFF API..."
BFF_MONITOR=$(curl -s -X POST "$UPTIME_KUMA_URL/api/monitor" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  --data '{
    "name": "BFF API",
    "url": "https://dev.fisamy.work/health",
    "type": "http",
    "interval": 60,
    "retryInterval": 30,
    "maxretries": 3,
    "timeout": 10,
    "httpHeaders": [
      {"key": "User-Agent", "value": "Uptime-Kuma-Monitor"}
    ]
  }')

if echo "$BFF_MONITOR" | jq -e '.ok' >/dev/null 2>&1; then
    echo "✓ BFF API monitor created successfully"
else
    echo "✗ Failed to create BFF monitor:"
    echo "$BFF_MONITOR" | jq -r '.msg // .error // "Unknown error"'
fi

# Create monitor for wildcard DNS (workspace apps)
echo "Creating monitor for wildcard DNS test..."
WILDCARD_MONITOR=$(curl -s -X POST "$UPTIME_KUMA_URL/api/monitor" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  --data '{
    "name": "Wildcard DNS Test",
    "url": "https://test.coder.fisamy.work",
    "type": "http",
    "interval": 300,
    "retryInterval": 60,
    "maxretries": 2,
    "timeout": 15,
    "httpHeaders": [
      {"key": "User-Agent", "value": "Uptime-Kuma-Monitor"}
    ]
  }')

if echo "$WILDCARD_MONITOR" | jq -e '.ok' >/dev/null 2>&1; then
    echo "✓ Wildcard DNS monitor created successfully"
else
    echo "✗ Failed to create wildcard DNS monitor:"
    echo "$WILDCARD_MONITOR" | jq -r '.msg // .error // "Unknown error"'
fi

echo ""
echo "Uptime Kuma setup complete!"
echo "Monitor your Coder deployment at: $UPTIME_KUMA_URL"

