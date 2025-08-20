#!/usr/bin/env bash
set -euo pipefail

# Create a per-user OpenVSCode container and Caddy site
# Usage: ./scripts/create_dev.sh <user> <domain> [--basic-auth user:pass]

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
SITES_DIR="$ROOT_DIR/caddy/sites"
PROJECT_NET="devnet"

log() { echo -e "\033[0;32m[INFO]\033[0m $*"; }
warn() { echo -e "\033[1;33m[WARN]\033[0m $*"; }
err()  { echo -e "\033[0;31m[ERR ]\033[0m $*"; }

if [[ $# -lt 2 ]]; then
  err "Usage: $0 <user> <domain> [--basic-auth user:pass]"
  exit 1
fi

USER_NAME="$1"
DOMAIN="$2"
AUTH_ARG="${3:-}"

CONTAINER="ovscode-${USER_NAME}"
VOLUME="ovscode_data_${USER_NAME}"
SITE_FILE="$SITES_DIR/${USER_NAME}.caddy"

mkdir -p "$SITES_DIR"

# Ensure Caddy is up (creates network too)
if ! docker compose -f "$ROOT_DIR/docker-compose.yml" ps caddy >/dev/null 2>&1; then
  log "Starting Caddy..."
  docker compose -f "$ROOT_DIR/docker-compose.yml" up -d caddy
else
  log "Caddy is present."
fi

# Ensure network exists
if ! docker network inspect "$PROJECT_NET" >/dev/null 2>&1; then
  log "Creating network $PROJECT_NET"
  docker network create "$PROJECT_NET"
fi

# Create volume if missing
if ! docker volume inspect "$VOLUME" >/dev/null 2>&1; then
  log "Creating volume $VOLUME"
  docker volume create "$VOLUME" >/dev/null
fi

# Launch OpenVSCode Server container
if docker ps -a --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  warn "Container $CONTAINER already exists. Skipping create."
  # ensure it is running and on network
  docker start "$CONTAINER" >/dev/null || true
  docker network connect "$PROJECT_NET" "$CONTAINER" >/dev/null 2>&1 || true
else
  log "Starting container $CONTAINER"
  docker run -d \
    --name "$CONTAINER" \
    --network "$PROJECT_NET" \
    -v "$VOLUME:/home/openvscode" \
    --restart unless-stopped \
    ghcr.io/coder/openvscode-server:latest >/dev/null
fi

# Build optional basic auth block
BASIC_AUTH_BLOCK=""
if [[ -n "$AUTH_ARG" ]]; then
  if [[ "$AUTH_ARG" == --basic-auth* ]]; then
    CREDS="${AUTH_ARG#--basic-auth }"
    AUTH_USER="${CREDS%%:*}"
    AUTH_PASS="${CREDS#*:}"
    if [[ -z "$AUTH_USER" || -z "$AUTH_PASS" || "$AUTH_USER" == "$AUTH_PASS" ]]; then
      err "Invalid --basic-auth user:pass"
      exit 1
    fi
    log "Hashing password for basicauth via Caddy..."
    HASH=$(docker run --rm caddy:2.8-alpine caddy hash-password --plaintext "$AUTH_PASS")
    BASIC_AUTH_BLOCK=$'  basicauth /* {\n    '"$AUTH_USER $HASH"$'\n  }\n'
  else
    warn "Unknown auth option: $AUTH_ARG (ignored)"
  fi
else
  warn "No auth configured. Protect with Cloudflare Zero Trust or add --basic-auth."
fi

# Write site file
cat > "$SITE_FILE" <<EOF
$DOMAIN {
  encode gzip
  header {
    X-Frame-Options "SAMEORIGIN"
    X-Content-Type-Options "nosniff"
    Referrer-Policy "strict-origin-when-cross-origin"
  }
${BASIC_AUTH_BLOCK}  reverse_proxy ${CONTAINER}:3000
}
EOF

log "Wrote site config: $SITE_FILE"

# Reload caddy
log "Reloading Caddy configuration"
docker compose -f "$ROOT_DIR/docker-compose.yml" exec -T caddy caddy reload --config /etc/caddy/Caddyfile >/dev/null

log "Workspace ready: https://$DOMAIN"
if [[ -n "$BASIC_AUTH_BLOCK" ]]; then
  echo "Credentials: $AUTH_USER / (hidden)"
fi

