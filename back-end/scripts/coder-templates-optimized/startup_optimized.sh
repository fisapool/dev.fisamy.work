#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

# Use writable directories instead of system log directories
LOG_FILE="/tmp/template-startup.log"
HEALTH_PORT=13133

# Ensure log directory exists and is writable
mkdir -p "$(dirname "$LOG_FILE")"
touch "$LOG_FILE"

log() {
  echo "[$(date -u +"%Y-%m-%dT%H:%M:%SZ")] $*" | tee -a "$LOG_FILE"
}

on_error() {
  log "ERROR: Startup script failed on line $1"
  exit 1
}

# Set proper error handling
trap 'on_error $LINENO' ERR

log "Starting no-gpu template initialization..."

# Check if we're running as root or have sudo access
if [ "$EUID" -eq 0 ]; then
    log "Running as root"
    SUDO_CMD=""
else
    if command -v sudo >/dev/null 2>&1; then
        log "Using sudo for privileged operations"
        SUDO_CMD="sudo"
    else
        log "WARNING: Not running as root and sudo not available"
        SUDO_CMD=""
    fi
fi

log "Updating apt and installing base packages..."
$SUDO_CMD apt-get update
$SUDO_CMD DEBIAN_FRONTEND=noninteractive apt-get install -y \
  python3 python3-venv python3-pip \
  curl git ca-certificates >/dev/null

log "Installing code-server..."
curl -fsSL https://code-server.dev/install.sh | sh >/dev/null

# Ensure coder user exists and home is prepared
if ! id -u coder >/dev/null 2>&1; then
  $SUDO_CMD useradd -m coder
  log "Created user 'coder'"
fi

$SUDO_CMD mkdir -p /home/coder/{projects,data,config}
$SUDO_CMD chown -R coder:coder /home/coder

# Start a lightweight health endpoint
start_health_server() {
  cat > /tmp/health_server.py << 'PYTHON_SCRIPT'
import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        response = {'status': 'ok', 'timestamp': __import__('datetime').datetime.utcnow().isoformat()}
        self.wfile.write(json.dumps(response).encode())
    
    def log_message(self, format, *args):
        # Suppress access logs
        pass

def run_server(port):
    server_address = ('0.0.0.0', port)
    httpd = HTTPServer(server_address, HealthHandler)
    print(f"Health server listening on :{port}")
    httpd.serve_forever()

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 13133
    run_server(port)
PYTHON_SCRIPT

  nohup python3 /tmp/health_server.py ${HEALTH_PORT} >/dev/null 2>&1 &
  log "Health server listening on :${HEALTH_PORT}"
}

start_health_server

# Start code-server as coder user
log "Starting code-server on :13337..."
if [ "$EUID" -eq 0 ]; then
    # Running as root, switch to coder user
    su -c "nohup code-server --bind-addr 0.0.0.0:13337 --auth none >/home/coder/code-server.log 2>&1 &" coder
else
    # Not root, try to start code-server directly
    nohup code-server --bind-addr 0.0.0.0:13337 --auth none >/home/coder/code-server.log 2>&1 &
fi

# Background resource monitor (lightweight)
resource_monitor() {
  while true; do
    MEM=$(free -h | awk '/Mem:/ {print $3"/"$2}' 2>/dev/null || echo "N/A")
    DISK=$(df -h / | awk 'END{print $3"/"$2" ("$5")"}' 2>/dev/null || echo "N/A")
    log "Resources: mem=$MEM disk=$DISK"
    sleep 30
  done
}

resource_monitor &

log "no-gpu template startup complete"
log "Health endpoint: http://localhost:${HEALTH_PORT}"
log "Code-server: http://localhost:13337"
