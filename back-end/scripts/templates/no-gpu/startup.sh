#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

LOG_FILE="/var/log/template-startup.log"
HEALTH_PORT=13133

log() {
  echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] $*" | tee -a "$LOG_FILE"
}

on_error() {
  log "ERROR: Startup script failed on line $1"
}
trap 'on_error $LINENO' ERR

log "Updating apt and installing base packages..."
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y \
  python3 python3-venv python3-pip \
  curl git sudo ca-certificates >/dev/null

log "Installing code-server..."
curl -fsSL https://code-server.dev/install.sh | sh >/dev/null

# Ensure coder user exists and home is prepared
if ! id -u coder >/dev/null 2>&1; then
  useradd -m coder
  log "Created user 'coder'"
fi

mkdir -p /home/coder/{projects,data,config}
chown -R coder:coder /home/coder

# Start a lightweight health endpoint
start_health_server() {
  nohup python3 - <<PY >/dev/null 2>&1 &
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'status':'ok'}).encode())

HTTPServer(('0.0.0.0', ${HEALTH_PORT}), H).serve_forever()
PY
  log "Health server listening on :${HEALTH_PORT}"
}
start_health_server

# Start code-server as coder
log "Starting code-server on :13337..."
sudo -u coder bash -lc "nohup code-server --bind-addr 0.0.0.0:13337 --auth none >/home/coder/code-server.log 2>&1 &"

# Background resource monitor (lightweight)
resource_monitor() {
  while true; do
    MEM=$(free -h | awk '/Mem:/ {print $3"/"$2}')
    DISK=$(df -h / | awk 'END{print $3"/"$2" ("$5")"}')
    log "Resources: mem=$MEM disk=$DISK"
    sleep 30
  done
}
resource_monitor &

log "no-gpu template startup complete"
