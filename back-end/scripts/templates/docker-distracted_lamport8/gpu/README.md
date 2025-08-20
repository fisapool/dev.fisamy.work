---
display_name: GPU-Enabled AI Development Environment
description: CUDA-enabled development environment for AI and machine learning workloads
icon: ../../../site/static/icon/docker.png
maintainer_github: coder
verified: true
tags: [docker, container, ai, ml, gpu, cuda, jupyter]
---

# GPU-Enabled AI Development Environment

Provision a CUDA-enabled Docker container as a [Coder workspace](https://coder.com/docs/workspaces) with this enhanced template designed for AI and machine learning workloads.

## Features

- **VS Code Server**: Web-based IDE on port 13337
- **Jupyter Lab**: Interactive notebooks on port 8888
- **CUDA Support**: Full GPU acceleration with NVIDIA drivers
- **PyTorch**: Pre-installed with CUDA 12.4 support
- **Health Monitoring**: Built-in health endpoint on port 13133
- **Resource Tracking**: Real-time CPU, memory, disk, and GPU monitoring
- **JetBrains IDEs**: Full IDE selection for development
- **Enhanced Logging**: Comprehensive logging with error handling
- **Home Directory**: Persistent storage with organized folder structure

## Prerequisites

### Infrastructure

The VM you run Coder on must have:

1. **Docker**: Running Docker socket with coder user access
2. **NVIDIA GPU**: Compatible GPU with CUDA support
3. **NVIDIA Drivers**: Latest drivers installed on the host
4. **CUDA Runtime**: CUDA 12.4 or compatible runtime

```sh
# Add coder user to Docker group
sudo adduser coder docker

# Verify NVIDIA drivers
nvidia-smi

# Verify Docker access
sudo -u coder docker ps

# Restart Coder server
sudo systemctl restart coder
```

## Architecture

This template provisions the following resources:

- **Docker Container**: NVIDIA CUDA 12.4 runtime with Ubuntu 22.04
- **Resource Limits**: CPU shares 2048, Memory 16GB
- **GPU Access**: Full GPU device access with CUDA support
- **Persistent Volume**: Home directory on `/home/coder`
- **Health Endpoint**: HTTP server on port 13133
- **Monitoring**: Built-in resource tracking, GPU monitoring, and logging

## Apps

- **VS Code**: http://localhost:13337 (with health checks)
- **Jupyter Lab**: http://localhost:8888 (AI/ML notebooks)
- **Health Check**: http://localhost:13133 (returns JSON status)
- **JetBrains IDEs**: Full selection through JetBrains Gateway

## AI/ML Stack

### Pre-installed Packages

- **PyTorch**: Latest version with CUDA 12.4 support
- **Jupyter Lab**: Interactive notebook environment
- **Data Science**: NumPy, Pandas, Matplotlib
- **Development**: Python 3, pip, virtual environments

### GPU Support

- **CUDA Runtime**: 12.4.1 with full GPU access
- **NVIDIA Drivers**: Host driver passthrough
- **GPU Monitoring**: Real-time GPU status and memory usage
- **PyTorch Integration**: Automatic CUDA detection and utilization

## Monitoring

The template includes comprehensive monitoring:

- **CPU Usage**: Real-time CPU utilization
- **Memory Usage**: RAM consumption tracking
- **Disk Usage**: Home directory space monitoring
- **Health Status**: Endpoint availability checks
- **GPU Status**: Real-time GPU information and memory usage
- **Jupyter Status**: Jupyter Lab availability monitoring
- **Template Logs**: Startup and runtime logging

## Environment Variables

The GPU template automatically sets:

```bash
NVIDIA_VISIBLE_DEVICES=all
NVIDIA_DRIVER_CAPABILITIES=all
```

## Customization

### Modifying the Image

Edit the `main.tf` file and run `coder templates push` to update workspaces.

### Adding AI/ML Packages

Modify the `startup_script` in the `coder_agent` resource to install additional packages:

```bash
pip install tensorflow torchvision transformers datasets
```

### Resource Limits

Adjust `cpu_shares` and `memory` in the `docker_container` resource.

### GPU Configuration

Modify the `device` block for different GPU configurations or multiple GPU support.

## Usage

1. **Create Workspace**: Use this template to provision a new GPU workspace
2. **Access VS Code**: Navigate to the VS Code app for development
3. **Use Jupyter**: Access Jupyter Lab for AI/ML notebooks
4. **Monitor Resources**: Check the metadata panel for real-time stats including GPU
5. **Health Checks**: Verify template health at port 13133

## AI/ML Workflows

### PyTorch Development

```python
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"GPU count: {torch.cuda.device_count()}")
```

### Jupyter Notebooks

- Create new notebooks in `/home/coder/projects`
- Use GPU acceleration for training
- Monitor GPU usage in real-time

## Troubleshooting

- **Health Endpoint**: Check if port 13133 is accessible
- **GPU Access**: Verify `nvidia-smi` works in the container
- **Jupyter**: Check if port 8888 is accessible and Jupyter is running
- **Resource Monitoring**: Verify metadata scripts are running
- **Logs**: Check `/var/log/template-startup.log` for detailed information
- **Docker**: Ensure Docker socket is accessible to the coder user
- **NVIDIA**: Verify host has compatible NVIDIA drivers and CUDA runtime
