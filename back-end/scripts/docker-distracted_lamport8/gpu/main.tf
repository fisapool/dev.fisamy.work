terraform {
  required_version = ">= 1.5.0"
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = ">= 3.0.2"
    }
  }
}

provider "docker" {}

locals {
  name          = "gpu"
  image         = "nvidia/cuda:12.4.1-runtime-ubuntu22.04"
  vscode_port   = 13337
  jupyter_port  = 8888
  health_port   = 13133
  cpu_shares    = 2048   // relative CPU weight
  memory_mb     = 16384  // 16GB
  healthcheck   = ["CMD", "curl", "-fsS", "http://localhost:${local.health_port}"]
}

resource "docker_image" "base" {
  name = local.image
  keep_locally = true
}

resource "docker_container" "dev" {
  name  = "coder-${local.name}"
  image = docker_image.base.image_id

  // Resource constraints
  cpu_shares = local.cpu_shares
  memory     = local.memory_mb

  // GPU device requests
  gpus = "all"

  env = [
    "NVIDIA_VISIBLE_DEVICES=all",
    "NVIDIA_DRIVER_CAPABILITIES=all",
    "CODER_TEMPLATE_TYPE=gpu",
    "CODER_DEBUG=true",
    "CODER_LOG_LEVEL=info"
  ]

  // App ports
  ports {
    internal = local.vscode_port
    external = local.vscode_port
  }
  ports {
    internal = local.jupyter_port
    external = local.jupyter_port
  }
  ports {
    internal = local.health_port
    external = local.health_port
  }

  // Optimized healthcheck
  healthcheck {
    test         = local.healthcheck
    interval     = "5s"
    timeout      = "3s"
    retries      = 6
    start_period = "15s"
  }

  // Labels for traceability
  labels {
    label = "coder.template"
    value = local.name
  }

  volumes {
    container_path = "/home/coder"
    host_path      = abspath("./data/home-coder")
  }

  // Optimized startup script with GPU support and error handling
  entrypoint = ["/bin/bash", "-lc"]
  command = [
    <<-EOT
      #!/bin/bash
      set -Eeuo pipefail
      
      # Create log file for debugging
      exec > >(tee -a /tmp/coder-startup-script.log)
      exec 2>&1
      
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
      sudo -u coder bash -lc 'source /opt/venv/bin/activate && jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root --LabApp.token="" --LabApp.password=""' &
      
      echo "=== GPU startup script completed successfully at $(date) ==="
      
      # Keep container running
      tail -f /dev/null
    EOT
  ]
}

