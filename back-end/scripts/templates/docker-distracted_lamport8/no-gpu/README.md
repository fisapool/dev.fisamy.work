---
display_name: No-GPU Development Environment
description: Basic development environment without GPU acceleration
icon: ../../../site/static/icon/docker.png
maintainer_github: coder
verified: true
tags: [docker, container, development, no-gpu]
---

# No-GPU Development Environment

Provision a lightweight Docker container as a [Coder workspace](https://coder.com/docs/workspaces) with this enhanced template.

## Features

- **VS Code Server**: Web-based IDE on port 13337
- **Health Monitoring**: Built-in health endpoint on port 13133
- **Resource Tracking**: Real-time CPU, memory, and disk monitoring
- **JetBrains IDEs**: Optional access to IntelliJ, PyCharm, WebStorm, etc.
- **Enhanced Logging**: Comprehensive logging with error handling
- **Home Directory**: Persistent storage with organized folder structure

## Prerequisites

### Infrastructure

The VM you run Coder on must have a running Docker socket and the `coder` user must be added to the Docker group:

```sh
# Add coder user to Docker group
sudo adduser coder docker

# Restart Coder server
sudo systemctl restart coder

# Test Docker
sudo -u coder docker ps
```

## Architecture

This template provisions the following resources:

- **Docker Container**: Ubuntu 22.04 base image
- **Resource Limits**: CPU shares 1024, Memory 4GB
- **Persistent Volume**: Home directory on `/home/coder`
- **Health Endpoint**: HTTP server on port 13133
- **Monitoring**: Built-in resource tracking and logging

## Apps

- **VS Code**: http://localhost:13337 (with health checks)
- **Health Check**: http://localhost:13133 (returns JSON status)
- **JetBrains IDEs**: Available through JetBrains Gateway

## Monitoring

The template includes comprehensive monitoring:

- **CPU Usage**: Real-time CPU utilization
- **Memory Usage**: RAM consumption tracking
- **Disk Usage**: Home directory space monitoring
- **Health Status**: Endpoint availability checks
- **Template Logs**: Startup and runtime logging

## Customization

### Modifying the Image

Edit the `main.tf` file and run `coder templates push` to update workspaces.

### Adding Packages

Modify the `startup_script` in the `coder_agent` resource to install additional packages.

### Resource Limits

Adjust `cpu_shares` and `memory` in the `docker_container` resource.

## Usage

1. **Create Workspace**: Use this template to provision a new workspace
2. **Access VS Code**: Navigate to the VS Code app in your workspace
3. **Monitor Resources**: Check the metadata panel for real-time stats
4. **Health Checks**: Verify template health at port 13133

## Troubleshooting

- **Health Endpoint**: Check if port 13133 is accessible
- **Resource Monitoring**: Verify metadata scripts are running
- **Logs**: Check `/var/log/template-startup.log` for detailed information
- **Docker**: Ensure Docker socket is accessible to the coder user
