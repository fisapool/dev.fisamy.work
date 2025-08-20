#!/usr/bin/env bash
set -euo pipefail

# Remove a per-user OpenVSCode container and/or volume, and Caddy site
# Usage: ./scripts/remove_dev.sh <user> [--delete-volume]

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
SITES_DIR="$ROOT_DIR/caddy/sites"

log() { echo -e "\033[0;32m[INFO]\033[0m $*"; }
warn() { echo -e "\033[1;33m[WARN]\033[0m $*"; }
err()  { echo -e "\033[0;31m[ERR ]\033[0m $*"; }

if [[ $# -lt 1 ]]; then
  err "Usage: $0 <user> [--delete-volume]"
  exit 1
fi

USER_NAME="$1"
DELETE_VOL="${2:-}"

CONTAINER="ovscode-${USER_NAME}"
VOLUME="ovscode_data_${USER_NAME}"
SITE_FILE="$SITES_DIR/${USER_NAME}.caddy"

# Remove caddy site config if present
if [[ -f "$SITE_FILE" ]]; then
  log "Removing site config $SITE_FILE"
  rm -f "$SITE_FILE"
  if docker compose -f "$ROOT_DIR/docker-compose.yml" ps caddy >/dev/null 2>&1; then
    log "Reloading Caddy"
    docker compose -f "$ROOT_DIR/docker-compose.yml" exec -T caddy caddy reload --config /etc/caddy/Caddyfile >/dev/null || true
  fi
else
  warn "Site file not found: $SITE_FILE"
fi

# Stop and remove container if exists
if docker ps -a --format '{{.Names}}' | grep -qx "$CONTAINER"; then
  log "Stopping and removing container $CONTAINER"
  docker rm -f "$CONTAINER" >/dev/null || true
else
  warn "Container $CONTAINER not found"
fi

# Optionally remove volume
if [[ "$DELETE_VOL" == "--delete-volume" ]]; then
  if docker volume inspect "$VOLUME" >/dev/null 2>&1; then
    log "Deleting volume $VOLUME"
    docker volume rm "$VOLUME" >/dev/null || true
  else
    warn "Volume $VOLUME not found"
  fi
fi

log "Cleanup complete for user: $USER_NAME"

