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

log "Creating Python venv and installing packages..."
python3 -m venv /opt/venv
source /opt/venv/bin/activate

pip install --upgrade pip wheel >/dev/null
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124 >/dev/null 2>&1 || log "Warning: Failed to preinstall torch CUDA wheels"
pip install jupyter jupyterlab numpy pandas matplotlib >/dev/null

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

# Start Jupyter Lab
log "Starting Jupyter Lab on :8888..."
nohup bash -lc 'source /opt/venv/bin/activate && jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --NotebookApp.token="" --NotebookApp.password="" ' >/home/coder/jupyter.log 2>&1 &

# Background resource monitor (lightweight) + basic GPU checks
resource_monitor() {
  while true; do
    MEM=$(free -h | awk '/Mem:/ {print $3"/"$2}')
    DISK=$(df -h / | awk 'END{print $3"/"$2" ("$5")"}')
    GPU_INFO=""
    if command -v nvidia-smi >/dev/null 2>&1; then
      GPU_INFO="gpu=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null | head -1 | xargs)"
    else
      GPU_INFO="gpu=unavailable"
    fi
    log "Resources: mem=$MEM disk=$DISK $GPU_INFO"
    sleep 30
  done
}
resource_monitor &

# Torch CUDA availability probe (non-fatal)
python3 - <<'PY' >> "$LOG_FILE" 2>&1 || true
import sys
try:
    import torch
    print(f"Torch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA device count: {torch.cuda.device_count()}")
        print(f"CUDA device name: {torch.cuda.get_device_name(0)}")
except Exception as e:
    print(f"Torch probe failed: {e}")
PY

log "gpu template startup complete"
