#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

# Enhanced logging and debugging
LOG_FILE="/var/log/template-startup.log"
HEALTH_PORT=13133
STARTUP_LOG="/tmp/coder-startup-script.log"

# Redirect all output to both log files
exec > >(tee -a "$LOG_FILE" "$STARTUP_LOG") 2>&1

log() {
  echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] $*"
}

on_error() {
  log "ERROR: Startup script failed on line $1"
  log "Check logs at: $LOG_FILE and $STARTUP_LOG"
  exit 1
}
trap 'on_error $LINENO' ERR

log "=== Starting no-gpu template startup script ==="
log "Logs will be available at: $LOG_FILE and $STARTUP_LOG"

# Function to check command status
run_command() {
  local cmd="$1"
  local description="$2"
  
  log "Running: $description"
  log "Command: $cmd"
  
  if eval "$cmd"; then
    log "SUCCESS: $description completed"
  else
    local status=$?
    log "ERROR: $description failed with exit status: $status"
    return $status
  fi
}

# Check if we can reach external resources
log "Checking network connectivity..."
if ! curl -s --max-time 10 https://httpbin.org/get >/dev/null; then
  log "WARNING: Cannot reach external resources, but continuing..."
else
  log "Network connectivity confirmed"
fi

log "Updating apt and installing base packages..."
run_command "apt-get update" "apt-get update"
run_command "DEBIAN_FRONTEND=noninteractive apt-get install -y python3 python3-venv python3-pip curl git sudo ca-certificates" "Install base packages"

log "Installing code-server..."
run_command "curl -fsSL https://code-server.dev/install.sh | sh" "Install code-server"

# Ensure coder user exists and home is prepared
log "Setting up coder user..."
if ! id -u coder >/dev/null 2>&1; then
  run_command "useradd -m coder" "Create coder user"
  log "Created user 'coder'"
else
  log "User 'coder' already exists"
fi

run_command "mkdir -p /home/coder/{projects,data,config}" "Create coder directories"
run_command "chown -R coder:coder /home/coder" "Set coder ownership"

# Start a lightweight health endpoint
start_health_server() {
  log "Starting health server on port ${HEALTH_PORT}..."
  nohup python3 - <<PY >/dev/null 2>&1 &
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import socket

class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'status':'ok', 'service':'health'}).encode())
    
    def log_message(self, format, *args):
        # Suppress access logs
        pass

try:
    server = HTTPServer(('0.0.0.0', ${HEALTH_PORT}), H)
    server.serve_forever()
except socket.error as e:
    print(f"Health server error: {e}")
PY
  log "Health server started on :${HEALTH_PORT}"
}
start_health_server

# Start code-server as coder
log "Starting code-server on :13337..."
run_command "sudo -u coder bash -lc 'nohup code-server --bind-addr 0.0.0.0:13337 --auth none >/home/coder/code-server.log 2>&1 &'" "Start code-server"

# Background resource monitor (lightweight)
resource_monitor() {
  log "Starting resource monitor..."
  while true; do
    MEM=$(free -h | awk '/Mem:/ {print $3"/"$2}')
    DISK=$(df -h / | awk 'END{print $3"/"$2" ("$5")"}')
    log "Resources: mem=$MEM disk=$DISK"
    sleep 30
  done
}
resource_monitor &

# Wait a moment for services to start
sleep 5

# Verify services are running
log "Verifying services..."
if pgrep -f "code-server" >/dev/null; then
  log "SUCCESS: code-server is running"
else
  log "ERROR: code-server is not running"
  exit 1
fi

if netstat -tlnp 2>/dev/null | grep ":${HEALTH_PORT}" >/dev/null; then
  log "SUCCESS: Health server is listening on :${HEALTH_PORT}"
else
  log "WARNING: Health server may not be listening on :${HEALTH_PORT}"
fi

log "=== no-gpu template startup complete ==="
log "VS Code available at: http://localhost:13337"
log "Health endpoint at: http://localhost:${HEALTH_PORT}"
log "Logs available at: $LOG_FILE and $STARTUP_LOG"
