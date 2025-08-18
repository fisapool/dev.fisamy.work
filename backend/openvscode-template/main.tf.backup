terraform {
  required_providers {
    coder  = { source = "coder/coder" }
    docker = { source = "kreuzwerker/docker" }
  }
}

provider "coder" {}
provider "docker" {}

# ========== Parameters (show in Coder UI) ==========
variable "workspace_name" {
  description = "Workspace name"
  type        = string
  default     = "vscode-ai"
}

variable "openai_api_key" {
  description = "OpenAI (or compatible) API key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "openai_base_url" {
  description = "OpenAI-compatible base URL (e.g., https://ai.dev.fisamy.work/v1)"
  type        = string
  default     = ""
}

variable "codeium_api_key" {
  description = "Codeium key (optional)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "tabby_endpoint" {
  description = "Tabby endpoint (optional)"
  type        = string
  default     = ""
}

variable "cpu"  { 
  type    = number
  default = 2
}

variable "ram"  { 
  type    = number
  default = 4096   # MB
}

variable "disk" { 
  type    = number
  default = 20     # GB
}

# ========== Agent (runs inside container/VM) ==========
resource "coder_agent" "dev" {
  os   = "linux"
  arch = "amd64"
  dir  = "/home/workspace"

  startup_script = <<-EOT
    #!/bin/bash
    set -e
    
    # Start OpenVSCode on port 3000
    /openvscode-server/bin/openvscode-server \
      --host 0.0.0.0 \
      --port 3000 \
      --connection-token "$CODER_TOKEN" &
    
    # Wait for the server to start
    sleep 5
    
    # Keep the container running
    wait
  EOT
}

# ========== Workspace container via Docker module ==========
module "workspace" {
  # Use Coder's Docker workspace module from the private registry
  # Format: <host>/<namespace>/<name>/<provider>
  source    = "registry.coder.com/coder/docker/docker"
  agent_id  = coder_agent.dev.id
  image     = "ghcr.io/gitpod-io/openvscode-server:latest"  # Use official OpenVSCode image
  cpu       = var.cpu
  memory_mb = var.ram
  disk_gb   = var.disk

  env = {
    OPENAI_API_KEY  = var.openai_api_key
    OPENAI_BASE_URL = var.openai_base_url
    CODEIUM_API_KEY = var.codeium_api_key
    TABBY_ENDPOINT  = var.tabby_endpoint
    # OpenVSCode specific env vars
    OPENVSCODE_SERVER_CONNECTION_TOKEN = "$CODER_TOKEN"
  }

  # Expose IDE port internally; Coder will front it as a Dev URL
  internal_ports = [3000]
}

# Expose the IDE as a Coder "app" (Dev URL, subdomain)
resource "coder_app" "vscode" {
  agent_id     = coder_agent.dev.id
  slug         = "vscode"
  display_name = "VS Code"
  icon         = "vscode"
  url          = "http://localhost:3000"
  subdomain    = true
}

output "hint" {
  value = "Use Dev URL for IDE. Env vars are injected for AI logins."
}

output "workspace_url" {
  value = "Workspace will be accessible via Dev URL: vscode--${var.workspace_name}--[username].dev.fisamy.work"
}
