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
  name          = "no-gpu"
  image         = "ubuntu:22.04"
  vscode_port   = 13337
  health_port   = 13133
  cpu_shares    = 512    // relative CPU weight
  memory_mb     = 4096   // 4GB
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

  // App ports
  ports {
    internal = local.vscode_port
    external = local.vscode_port
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
    start_period = "10s"
  }

  // Labels for traceability
  labels {
    label = "coder.template"
    value = local.name
  }

  // Persist home data
  volumes {
    container_path = "/home/coder"
    host_path      = abspath("./data/home-coder")
  }

  // Environment variables for debugging
  env = [
    "CODER_TEMPLATE_TYPE=no-gpu",
    "CODER_DEBUG=true",
    "CODER_LOG_LEVEL=info"
  ]

  // Optimized startup script with error handling and debugging
  entrypoint = ["/bin/bash", "-lc"]
  command = [
    <<-EOT
      #!/bin/bash
      set -Eeuo pipefail
      
      # Create log file for debugging
      exec > >(tee -a /tmp/coder-startup-script.log)
      exec 2>&1
      
      echo "=== Starting no-gpu startup script at $(date) ==="
      
      # Function to handle errors
      handle_error() {
        echo "Error occurred in startup script at line $1"
        echo "Exit code: $2"
        echo "Stack trace:"
        caller
        exit $2
      }
      
      trap 'handle_error $LINENO $?' ERR
      
      # Prepare user home with default files on first start
      if [ ! -f ~/.init_done ]; then
        echo "Initializing user home directory..."
        cp -rT /etc/skel ~
        touch ~/.init_done
        echo "User home initialized successfully"
      fi
      
      # Install required packages with error handling
      echo "Installing required packages..."
      apt-get update
      apt-get install -y curl git sudo ca-certificates python3 python3-venv python3-pip
      
      # Setup VS Code with proper error handling
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
                'template': 'no-gpu',
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
      
      echo "=== Startup script completed successfully at $(date) ==="
      
      # Keep container running
      tail -f /dev/null
    EOT
  ]
}

