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
    
    log "Starting no-gpu template initialization..."
    
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
            self.wfile.write(json.dumps({'status':'ok', 'template':'no-gpu'}).encode())
    
    HTTPServer(('0.0.0.0', 13133), H).serve_forever()
    PY
      log "Health server listening on :13133"
    }
    start_health_server
    
    # Start resource monitoring
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

  # Enhanced metadata with your monitoring features
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
    display_name = "Template Logs"
    key          = "5_template_logs"
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

# Optional: JetBrains Gateway for additional IDEs
module "jetbrains_gateway" {
  count  = data.coder_workspace.me.start_count
  source = "registry.coder.com/coder/jetbrains-gateway/coder"
  version = "~> 1.0"

  # Simplified IDE selection for no-gpu environment
  jetbrains_ides = ["IU", "PS", "WS", "PY", "CL"]
  default        = "IU"
  folder         = "/home/coder"
  agent_id       = coder_agent.main.id
  agent_name     = "main"
  order          = 2
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
    value = "no-gpu"
  }
}

resource "docker_container" "workspace" {
  count = data.coder_workspace.me.start_count
  image = "codercom/enterprise-base:ubuntu"
  
  name = "coder-${data.coder_workspace_owner.me.name}-${lower(data.coder_workspace.me.name)}"
  hostname = data.coder_workspace.me.name
  
  entrypoint = ["sh", "-c", replace(coder_agent.main.init_script, "/localhost|127\\.0\\.0\\.1/", "host.docker.internal")]
  env        = ["CODER_AGENT_TOKEN=${coder_agent.main.token}"]
  
  host {
    host = "host.docker.internal"
    ip   = "host-gateway"
  }
  
  volumes {
    container_path = "/home/coder"
    volume_name    = docker_volume.home_volume.name
    read_only      = false
  }

  # Resource constraints for no-gpu environment
  cpu_shares = 1024
  memory     = 4096  # 4GB
  
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
    value = "no-gpu"
  }
}
