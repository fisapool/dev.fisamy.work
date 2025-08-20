// Reference-only root. See variant subfolders for concrete configs.

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = ">= 3.0.2"
    }
  }
}

// Shared locals to keep variants consistent
locals {
  health_port   = 13133
  vscode_port   = 13337
  jupyter_port  = 8888
  // Health endpoint implemented in startup scripts
  healthcheck_cmd = ["CMD", "curl", "-fsS", "http://localhost:${local.health_port}"]
}

// See ./no-gpu/main.tf and ./gpu/main.tf for runnable examples.

