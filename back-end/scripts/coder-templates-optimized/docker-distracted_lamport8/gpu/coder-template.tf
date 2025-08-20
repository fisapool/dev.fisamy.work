terraform {
  required_version = ">= 1.0.0"
  required_providers {
    coder = {
      source  = "coder/coder"
      version = "~> 0.20.0"
    }
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.6.2"
    }
  }
}

provider "docker" {}

data "coder_provisioner" "me" {
}

data "coder_workspace" "me" {
}

locals {
  image = "nvidia/cuda:12.4.1-runtime-ubuntu22.04"
}

resource "docker_image" "base" {
  name = local.image
  keep_locally = true
}

resource "docker_container" "workspace" {
  count = data.coder_workspace.me.start_count
  image = docker_image.base.image_id
  name  = "coder-${data.coder_workspace.me.owner}-${data.coder_workspace.me.name}"
  
  # Resource constraints
  cpu_shares = 2048  # 8 CPU equivalent
  memory     = 16384 * 1024 * 1024  # 16GB
  
  # GPU access
  gpus = "all"
  
  env = [
    "CODER_AGENT_TOKEN=${coder_agent.main.token}",
    "NVIDIA_VISIBLE_DEVICES=all",
    "NVIDIA_DRIVER_CAPABILITIES=all"
  ]
  
  host {
    host = "host.docker.internal"
    ip   = "host-gateway"
  }

  # Optimized healthcheck
  healthcheck {
    test         = ["CMD", "curl", "-fsS", "http://localhost:13133"]
    interval     = "5s"
    timeout      = "3s"
    retries      = 6
    start_period = "15s"
  }
}

resource "coder_agent" "main" {
  arch           = "amd64"
  os             = "linux"
  connection_timeout = 600

  startup_script = <<-EOT
    #!/bin/bash
    set -Eeuo pipefail

    # Write logs somewhere the container user owns
    LOG_DIR="$${LOG_DIR:-$$HOME/.coder-logs}"
    mkdir -p "$$LOG_DIR"
    exec > >(tee -a "$$LOG_DIR/startup.log") 2>&1
    
    echo "=== Starting GPU startup script at $(date) ==="
    
    # Function to handle errors
    handle_error() {
      echo "Error occurred in startup script at line $1"
      echo "Exit code: $2"
      echo "Stack trace:"
      caller
      exit $2
    }
    
    trap 'handle_error $LINENO $?' ERR
    
    # Check GPU availability
    echo "Checking GPU availability..."
    if command -v nvidia-smi &> /dev/null; then
      echo "NVIDIA GPU detected:"
      nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits
    else
      echo "Warning: NVIDIA GPU not detected"
    fi
    
    # Prepare user home with default files on first start
    if [ ! -f ~/.init_done ]; then
      echo "Initializing user home directory..."
      cp -rT /etc/skel ~
      touch ~/.init_done
      echo "User home initialized successfully"
    fi
    
    # Install required packages
    echo "Installing required packages..."
    apt-get update
    apt-get install -y curl git sudo ca-certificates python3 python3-venv python3-pip
    
    # Setup Python environment
    echo "Setting up Python environment..."
    python3 -m venv /opt/venv
    source /opt/venv/bin/activate
    
    # Install PyTorch and ML packages
    echo "Installing PyTorch and ML packages..."
    pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
    pip install --no-cache-dir jupyter jupyterlab numpy pandas matplotlib scikit-learn
    
    # Verify PyTorch GPU support
    echo "Verifying PyTorch GPU support..."
    python3 -c "
import torch
print(f'PyTorch version: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'CUDA version: {torch.version.cuda}')
    print(f'GPU count: {torch.cuda.device_count()}')
    print(f'GPU name: {torch.cuda.get_device_name(0)}')
"
    
    # Setup VS Code
    echo "Setting up VS Code..."
    if ! command -v code-server &> /dev/null; then
      echo "Installing code-server..."
      curl -fsSL https://code-server.dev/install.sh | sh
    fi
    
    # Create user if it doesn't exist
    useradd -m coder || true
    
    # Start health server
    echo "Starting health server..."
    nohup python3 - <<'PY' >/tmp/health-server.log 2>&1 &
import json
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {
                'status': 'ok',
                'template': 'gpu',
                'timestamp': __import__('datetime').datetime.now().isoformat()
            }
            self.wfile.write(json.dumps(response).encode())
            logger.info(f"Health check request from {self.client_address[0]}")
        except Exception as e:
            logger.error(f"Health check error: {e}")
            self.send_response(500)
            self.end_headers()
    
    def log_message(self, format, *args):
        logger.info(f"{self.address_string()} - {format % args}")

if __name__ == "__main__":
    try:
        server = HTTPServer(('0.0.0.0', 13133), HealthHandler)
        logger.info("Health server started on port 13133")
        server.serve_forever()
    except Exception as e:
        logger.error(f"Failed to start health server: {e}")
        exit(1)
PY
    
    # Start VS Code server
    echo "Starting VS Code server..."
    sudo -u coder bash -lc 'code-server --bind-addr 0.0.0.0:13337 --auth none --log debug' &
    
    # Start Jupyter Lab
    echo "Starting Jupyter Lab..."
    sudo -u coder bash -lc 'source /opt/venv/bin/activate && jupyter lab \
      --ServerApp.token="" \
      --ServerApp.password="" \
      --ServerApp.allow_origin="*" \
      --port=8888 --ip=0.0.0.0 --no-browser' &
    
    echo "=== GPU startup script completed successfully at $(date) ==="
    
    # Keep container running
    tail -f /dev/null
  EOT

  env = {
    NVIDIA_VISIBLE_DEVICES = "all"
    NVIDIA_DRIVER_CAPABILITIES = "all"
  }
}

resource "coder_app" "vscode" {
  agent_id = coder_agent.main.id
  slug     = "vscode"
  display_name = "VS Code"
  url      = "http://localhost:13337"
  icon     = "/icon/vscode.svg"
  subdomain = true
}

resource "coder_app" "jupyter" {
  agent_id = coder_agent.main.id
  slug     = "jupyter"
  display_name = "Jupyter Lab"
  url      = "http://localhost:8888"
  icon     = "/icon/jupyter.svg"
  subdomain = true
}
