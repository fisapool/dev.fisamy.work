terraform {
  required_version = ">= 1.5.0"
  required_providers {
    coder  = { source = "coder/coder", version = ">= 0.9.12" }
    docker = { source = "kreuzwerker/docker", version = ">= 3.0.2" }
  }
}

provider "coder" {}

# If the Coder server runs on the same host as Docker, defaults work.
# Otherwise: provider "docker" { host = "unix:///var/run/docker.sock" }
provider "docker" {}

# ---------- Parameters ----------
variable "workspace_name" {
  type    = string
  default = "vscode-ai"
}

variable "cpu" {
  type    = number
  default = 2
}

variable "ram_mb" {
  type    = number
  default = 4096   # MB
}

variable "disk_gb" {
  type    = number
  default = 20     # GB
}

variable "coder_access_url" {
  type    = string
  default = "https://dev.fisamy.work"
}

# AI creds / endpoints (env-driven "pre-login")
variable "openai_api_key" {
  type      = string
  sensitive = true
}

variable "openai_base_url" {
  type    = string
  default = ""
}

variable "codeium_api_key" {
  type      = string
  sensitive = true
  default  = ""
}

variable "tabby_endpoint" {
  type    = string
  default = ""
}

# ---------- Coder Agent (Terraform manages the token/id) ----------
resource "coder_agent" "dev" {
  os   = "linux"
  arch = "amd64"
  dir  = "/home/workspace"
  # The agent process itself is started inside the container (see docker_container.command).
}

# ---------- Workspace container ----------
# Use your prebuilt image with AI extensions/settings:
#   docker build -t openvscode-ai:latest ./openvscode-ai
resource "docker_image" "ide" {
  name = "openvscode-ai:latest"
  # fallback image if you haven't built your own yet:
  # name = "ghcr.io/gitpod-io/openvscode-server:latest"
  keep_locally = true
}

resource "docker_volume" "home" {
  name = "vscode_ai_${var.workspace_name}_home"
}

resource "docker_container" "ws" {
  name  = "vscode-ai-${var.workspace_name}"
  image = docker_image.ide.name
  restart = "unless-stopped"

  # No host port mapping needed; Coder proxies via Dev URL. We still expose 3000 inside.
  ports {
    internal = 3000
    protocol = "tcp"
  }

  mounts {
    target = "/home/workspace"
    type   = "volume"
    source = docker_volume.home.name
  }

  # Inject AI creds/endpoints so extensions "just work"
  env = [
    "OPENAI_API_KEY=${var.openai_api_key}",
    "OPENAI_BASE_URL=${var.openai_base_url}",
    "CODEIUM_API_KEY=${var.codeium_api_key}",
    "TABBY_ENDPOINT=${var.tabby_endpoint}",
  ]

  # Note: Docker provider doesn't support CPU/memory limits via Terraform
  # Use Docker daemon configs or host-level resource management for hard caps

  # Start the agent, then the IDE. Agent registers using the Terraform-provided token.
  command = [
    "sh", "-lc",
    join(" && ", [
      "set -e",
      # install coder CLI/agent
      "curl -fsSL https://coder.com/install.sh | sh -s -- --bin-dir /usr/local/bin >/dev/null",
      # start agent in background (registers using token from TF)
      "coder agent start --name ${var.workspace_name} --url ${var.coder_access_url} --token ${coder_agent.dev.token} --workspace /home/workspace &",
      # launch OpenVSCode
      "/openvscode-server/bin/openvscode-server --host 0.0.0.0 --port 3000"
    ])
  ]
}

# Dev URL in Coder UI
resource "coder_app" "vscode" {
  agent_id     = coder_agent.dev.id
  slug         = "vscode"
  display_name = "VS Code"
  icon         = "vscode"
  url          = "http://localhost:3000"
  subdomain    = true
}
