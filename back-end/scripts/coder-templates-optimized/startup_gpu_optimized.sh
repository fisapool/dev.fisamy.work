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

log "Starting GPU-enabled template initialization..."

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
  curl git ca-certificates wget >/dev/null

log "Installing code-server..."
curl -fsSL https://code-server.dev/install.sh | sh >/dev/null

# Ensure coder user exists and home is prepared
if ! id -u coder >/dev/null 2>&1; then
  $SUDO_CMD useradd -m coder
  log "Created user 'coder'"
fi

$SUDO_CMD mkdir -p /home/coder/{projects,data,config}
$SUDO_CMD chown -R coder:coder /home/coder

# Check GPU availability and install CUDA if needed
log "Checking GPU availability..."
if command -v nvidia-smi &> /dev/null; then
    log "✅ NVIDIA GPU detected"
    nvidia-smi --query-gpu=name --format=csv,noheader,nounits | head -1
    log "Installing PyTorch with CUDA support..."
    
    # Create virtual environment for Python packages
    $SUDO_CMD python3 -m venv /opt/venv
    $SUDO_CMD chown -R coder:coder /opt/venv
    
    # Install PyTorch with CUDA support
    su -c "source /opt/venv/bin/activate && pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118" coder
    
    log "PyTorch installation completed"
else
    log "ℹ️  No NVIDIA GPU detected, installing CPU-only PyTorch"
    $SUDO_CMD python3 -m venv /opt/venv
    $SUDO_CMD chown -R coder:coder /opt/venv
    
    su -c "source /opt/venv/bin/activate && pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu" coder
fi

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
        
        # Check GPU status if available
        gpu_info = {}
        try:
            import torch
            gpu_info = {
                'pytorch_version': torch.__version__,
                'cuda_available': torch.cuda.is_available(),
                'cuda_version': torch.version.cuda if torch.cuda.is_available() else None,
                'gpu_count': torch.cuda.device_count() if torch.cuda.is_available() else 0
            }
        except ImportError:
            gpu_info = {'error': 'PyTorch not available'}
        
        response = {
            'status': 'ok', 
            'timestamp': __import__('datetime').datetime.utcnow().isoformat(),
            'gpu_info': gpu_info
        }
        self.wfile.write(json.dumps(response, indent=2).encode())
    
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
    
    # GPU info if available
    GPU_INFO=""
    if command -v nvidia-smi &> /dev/null; then
        GPU_INFO=$(nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits 2>/dev/null | head -1 | awk -F', ' '{print "GPU: " $1 "% util, " $2 "/" $3 " MB"}' || echo "")
    fi
    
    log "Resources: mem=$MEM disk=$DISK $GPU_INFO"
    sleep 30
  done
}

resource_monitor &

log "GPU-enabled template startup complete"
log "Health endpoint: http://localhost:${HEALTH_PORT}"
log "Code-server: http://localhost:13337"
log "PyTorch environment: /opt/venv"
