terraform {
  required_providers {
    coder = {
      source  = "coder/coder"
      version = ">= 2.5"
    }
  }
}

# Coder provider configuration via environment variables:
# CODER_URL and CODER_TOKEN

# Coder data sources for workspace context
data "coder_workspace" "me" {}
data "coder_workspace_owner" "me" {}

# Coder agent for the workspace
resource "coder_agent" "main" {
  arch = "amd64"
  os   = "linux"
  
  startup_script = <<-EOT
    #!/bin/bash
    # Update package list and install basic tools
    apt-get update
    apt-get install -y curl git sudo ca-certificates
    
    # Create coder user if it doesn't exist
    useradd -m coder || true
    
    # Install code-server as an alternative
    curl -fsSL https://code-server.dev/install.sh | sh
    
    # Start code-server in the background
    sudo -u coder bash -lc 'code-server --bind-addr 0.0.0.0:13337 --auth none &'
    
    # Keep the script running
    tail -f /dev/null
  EOT
}

# VS Code Web Module
module "vscode-web" {
  source         = "registry.coder.com/coder/vscode-web/coder"
  version        = "1.3.1"
  agent_id       = coder_agent.main.id
  accept_license = true
  port           = 13338
  display_name   = "VS Code Web"
  slug           = "vscode-web"
  subdomain      = true
  share          = "owner"
  extensions     = ["ms-python.python", "ms-vscode.vscode-json", "ms-vscode.vscode-typescript-next"]
  settings = {
    "workbench.colorTheme" = "Default Dark+"
    "editor.fontSize"      = 14
    "terminal.integrated.fontSize" = 14
  }
}

# Code Server App (alternative to VS Code Web)
resource "coder_app" "code-server" {
  agent_id     = coder_agent.main.id
  slug         = "code-server"
  display_name = "Code Server"
  url          = "http://localhost:13337"
  icon         = "/icon/code.svg"
  subdomain    = true
  share        = "owner"
  
  healthcheck {
    url       = "http://localhost:13337"
    interval  = 5
    threshold = 6
  }
}

