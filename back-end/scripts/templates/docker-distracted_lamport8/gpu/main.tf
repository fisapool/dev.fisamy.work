terraform {
  required_providers {
    coder = {
      source = "coder/coder"
    }
    docker = {
      source = "kreuzwerker/docker"
    }
  }
}

locals {
  username = data.coder_workspace_owner.me.name
}

variable "docker_socket" {
  default     = ""
  description = "(Optional) Docker socket URI"
  type        = string
}

provider "docker" {
  # Defaulting to null if the variable is an empty string lets us have an optional variable without having to set our own default
  host = var.docker_socket != "" ? var.docker_socket : null
}

data "coder_provisioner" "me" {}
data "coder_workspace" "me" {}
data "coder_workspace_owner" "me" {}

resource "coder_agent" "main" {
  arch           = data.coder_provisioner.me.arch
  os             = "linux"
  startup_script = <<-EOT
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
    
    log "Starting GPU template initialization..."
    
    # Prepare user home with default files on first start.
    if [ ! -f ~/.init_done ]; then
      cp -rT /etc/skel ~
      mkdir -p ~/{projects,data,config}
      touch ~/.init_done
      log "Created home directory structure"
    fi
    
    # Install essential packages
    log "Installing essential packages..."
    apt-get update
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
      python3 python3-venv python3-pip \
      curl git sudo ca-certificates >/dev/null
    
    # Create Python virtual environment
    log "Creating Python virtual environment..."
    python3 -m venv /opt/venv
    source /opt/venv/bin/activate
    
    # Install Python packages with error tolerance
    log "Installing Python packages..."
    pip install --upgrade pip wheel >/dev/null
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124 >/dev/null 2>&1 || log "Warning: Failed to preinstall torch CUDA wheels"
    pip install jupyter jupyterlab numpy pandas matplotlib >/dev/null
    
    # Start health check endpoint
    start_health_server() {
      nohup python3 - <<PY >/dev/null 2>&1 &
    import json
    from http.server import BaseHTTPRequestHandler, HTTPServer
    
    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status':'ok', 'template':'gpu'}).encode())
    
    HTTPServer(('0.0.0.0', 13133), H).serve_forever()
    PY
      log "Health server listening on :13133"
    }
    start_health_server
    
    # Start Jupyter Lab
    log "Starting Jupyter Lab on :8888..."
    nohup bash -lc 'source /opt/venv/bin/activate && jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --NotebookApp.token="" --NotebookApp.password=""' >/home/coder/jupyter.log 2>&1 &
    
    # Enhanced resource monitoring with GPU checks
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
    
    log "GPU template startup complete"
  EOT

  # These environment variables allow you to make Git commits right away after creating a
  # workspace. Note that they take precedence over configuration defined in ~/.gitconfig!
  # You can remove this block if you'd prefer to configure Git manually or using
  # dotfiles. (see docs/dotfiles.md)
  env = {
    GIT_AUTHOR_NAME     = coalesce(data.coder_workspace_owner.me.full_name, data.coder_workspace_owner.me.name)
    GIT_AUTHOR_EMAIL    = "${data.coder_workspace_owner.me.email}"
    GIT_COMMITTER_NAME  = coalesce(data.coder_workspace_owner.me.full_name, data.coder_workspace_owner.me.name)
    GIT_COMMITTER_EMAIL = "${data.coder_workspace_owner.me.email}"
  }

  # Enhanced metadata with GPU monitoring features
  metadata {
    display_name = "CPU Usage"
    key          = "0_cpu_usage"
    script       = "coder stat cpu"
    interval     = 10
    timeout      = 1
  }

  metadata {
    display_name = "RAM Usage"
    key          = "1_ram_usage"
    script       = "coder stat mem"
    interval     = 10
    timeout      = 1
  }

  metadata {
    display_name = "Home Disk"
    key          = "3_home_disk"
    script       = "coder stat disk --path $${HOME}"
    interval     = 60
    timeout      = 1
  }

  metadata {
    display_name = "Health Status"
    key          = "4_health_status"
    script       = "curl -s http://localhost:13133 | jq -r .status || echo 'unavailable'"
    interval     = 30
    timeout      = 5
  }

  metadata {
    display_name = "GPU Status"
    key          = "5_gpu_status"
    script       = "nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv,noheader 2>/dev/null | head -1 || echo 'GPU unavailable'"
    interval     = 30
    timeout      = 5
  }

  metadata {
    display_name = "Jupyter Status"
    key          = "6_jupyter_status"
    script       = "curl -s http://localhost:8888 | grep -q 'Jupyter' && echo 'running' || echo 'stopped'"
    interval     = 60
    timeout      = 5
  }

  metadata {
    display_name = "Template Logs"
    key          = "7_template_logs"
    script       = "tail -1 /var/log/template-startup.log | cut -c1-80"
    interval     = 60
    timeout      = 2
  }
}

# Enhanced code-server module
module "code-server" {
  count  = data.coder_workspace.me.start_count
  source = "registry.coder.com/coder/code-server/coder"
  version = "~> 1.0"

  agent_id = coder_agent.main.id
  order    = 1
}

# Jupyter Lab app
resource "coder_app" "jupyter" {
  agent_id     = coder_agent.main.id
  slug         = "jupyter"
  display_name = "Jupyter Lab"
  url          = "http://localhost:8888"
  icon         = "/icon/jupyter.svg"
  subdomain    = true
  share        = "owner"
  
  healthcheck {
    url       = "http://localhost:8888"
    interval  = 30
    threshold = 3
  }
}

# Optional: JetBrains Gateway for additional IDEs
module "jetbrains_gateway" {
  count  = data.coder_workspace.me.start_count
  source = "registry.coder.com/coder/jetbrains-gateway/coder"
  version = "~> 1.0"

  # Full IDE selection for GPU environment
  jetbrains_ides = ["IU", "PS", "WS", "PY", "CL", "GO", "RM", "RD", "RR"]
  default        = "IU"
  folder         = "/home/coder"
  agent_id       = coder_agent.main.id
  agent_name     = "main"
  order          = 3
}

resource "docker_volume" "home_volume" {
  name = "coder-${data.coder_workspace.me.id}-home"
  
  lifecycle {
    ignore_changes = all
  }
  
  labels {
    label = "coder.owner"
    value = data.coder_workspace_owner.me.name
  }
  labels {
    label = "coder.owner_id"
    value = data.coder_workspace_owner.me.id
  }
  labels {
    label = "coder.workspace_id"
    value = data.coder_workspace.me.id
  }
  labels {
    label = "coder.workspace_name_at_creation"
    value = data.coder_workspace.me.name
  }
  labels {
    label = "coder.template_type"
    value = "gpu"
  }
}

resource "docker_container" "workspace" {
  count = data.coder_workspace.me.start_count
  image = "nvidia/cuda:12.4.1-runtime-ubuntu22.04"
  
  name = "coder-${data.coder_workspace_owner.me.name}-${lower(data.coder_workspace.me.name)}"
  hostname = data.coder_workspace.me.name
  
  entrypoint = ["sh", "-c", replace(coder_agent.main.init_script, "/localhost|127\\.0\\.0\\.1/", "host.docker.internal")]
  env        = [
    "CODER_AGENT_TOKEN=${coder_agent.main.token}",
    "NVIDIA_VISIBLE_DEVICES=all",
    "NVIDIA_DRIVER_CAPABILITIES=all"
  ]
  
  host {
    host = "host.docker.internal"
    ip   = "host-gateway"
  }
  
  volumes {
    container_path = "/home/coder"
    volume_name    = docker_volume.home_volume.name
    read_only      = false
  }

  # Resource constraints for GPU environment
  cpu_shares = 2048
  memory     = 16384  # 16GB
  
  # GPU device access
  devices {
    host_path      = "/dev/nvidia0"
    container_path = "/dev/nvidia0"
    permissions    = "rwm"
  }
  
  labels {
    label = "coder.owner"
    value = data.coder_workspace_owner.me.name
  }
  labels {
    label = "coder.owner_id"
    value = data.coder_workspace_owner.me.id
  }
  labels {
    label = "coder.workspace_id"
    value = data.coder_workspace.me.id
  }
  labels {
    label = "coder.workspace_name"
    value = data.coder_workspace.me.name
  }
  labels {
    label = "coder.template_type"
    value = "gpu"
  }
}
