---
display_name: Enhanced Docker Templates
description: Professional Docker-based Coder templates with enhanced monitoring and GPU support
icon: ../../../site/static/icon/docker.png
maintainer_github: coder
verified: true
tags: [docker, container, monitoring, gpu, ai, ml]
---

# Enhanced Docker Templates for Coder

This directory contains professional-grade Docker-based Coder templates with enhanced monitoring, health checks, and GPU support. Built on the foundation of community best practices and enhanced with production-ready features.

## Template Variants

### 🖥️ **No-GPU Environment** (`/no-gpu/`)
- **Base Image**: Ubuntu 22.04
- **Resources**: CPU shares 1024, Memory 4GB
- **Features**: VS Code, JetBrains IDEs, health monitoring
- **Use Case**: General development, web development, basic programming

### 🚀 **GPU Environment** (`/gpu/`)
- **Base Image**: NVIDIA CUDA 12.4 runtime with Ubuntu 22.04
- **Resources**: CPU shares 2048, Memory 16GB, GPU access
- **Features**: VS Code, Jupyter Lab, PyTorch, CUDA support, GPU monitoring
- **Use Case**: AI/ML development, data science, GPU-accelerated workloads

## Enhanced Features

### 🔍 **Health Monitoring**
- **Health Endpoint**: HTTP server on port 13133
- **Real-time Status**: JSON responses with template information
- **Health Checks**: Built into Coder apps for reliability

### 📊 **Resource Monitoring**
- **CPU Usage**: Real-time CPU utilization tracking
- **Memory Usage**: RAM consumption monitoring
- **Disk Usage**: Home directory space tracking
- **GPU Status**: Real-time GPU information (GPU template)
- **Template Logs**: Comprehensive startup and runtime logging

### 🏗️ **Professional Architecture**
- **HCL-based**: Infrastructure as code with Terraform
- **Module-based**: Uses official Coder modules
- **Resource Management**: Proper Docker resource constraints
- **Volume Management**: Persistent home directories with labeling
- **Error Handling**: Comprehensive error handling and logging

## Prerequisites

### Infrastructure Requirements

1. **Docker**: Running Docker socket with coder user access
2. **NVIDIA GPU** (GPU template only): Compatible GPU with CUDA support
3. **NVIDIA Drivers** (GPU template only): Latest drivers installed on the host

### Setup Commands

```sh
# Add coder user to Docker group
sudo adduser coder docker

# Verify Docker access
sudo -u coder docker ps

# Verify NVIDIA drivers (GPU template only)
nvidia-smi

# Restart Coder server
sudo systemctl restart coder
```

## Quick Start

### 1. Choose Your Template

- **For general development**: Use `/no-gpu/main.tf`
- **For AI/ML workloads**: Use `/gpu/main.tf`

### 2. Deploy Template

```sh
# Navigate to template directory
cd no-gpu  # or gpu

# Deploy template
coder templates create

# Or use the archive
coder templates create --archive-path ../enhanced-templates.tar.gz
```

### 3. Create Workspace

- Use the template to provision a new workspace
- Access VS Code on port 13337
- Monitor resources through the metadata panel
- Check health status at port 13133

## Architecture Overview

### Core Components

- **coder_agent**: Enhanced startup script with monitoring
- **code-server**: VS Code web IDE with health checks
- **docker_container**: Resource-constrained Docker containers
- **docker_volume**: Persistent home directory storage
- **Metadata**: Real-time resource monitoring and status

### Monitoring Stack

- **Health Endpoint**: Lightweight HTTP server for status checks
- **Resource Monitor**: Background monitoring of system resources
- **GPU Monitor**: Real-time GPU status and memory usage
- **Logging**: Comprehensive logging with error handling

## Customization

### Modifying Templates

1. **Edit main.tf**: Modify the Terraform configuration
2. **Update startup script**: Enhance the coder_agent startup script
3. **Adjust resources**: Modify CPU, memory, and GPU constraints
4. **Add packages**: Install additional software in startup script

### Adding Features

- **New Apps**: Add additional coder_app resources
- **Monitoring**: Extend metadata blocks for new metrics
- **Packages**: Install additional software in startup script
- **Health Checks**: Add new health endpoints and checks

## Best Practices

### Resource Management

- **CPU Shares**: Use appropriate CPU sharing for workload types
- **Memory Limits**: Set realistic memory constraints
- **GPU Access**: Ensure proper GPU device mapping
- **Volume Management**: Use persistent volumes for data

### Monitoring

- **Health Checks**: Implement comprehensive health monitoring
- **Resource Tracking**: Monitor all critical resources
- **Logging**: Maintain detailed logs for troubleshooting
- **Error Handling**: Implement robust error handling

### Security

- **User Isolation**: Run as non-root user when possible
- **Resource Limits**: Enforce resource constraints
- **Network Security**: Use appropriate port bindings
- **Volume Security**: Secure persistent storage access

## Troubleshooting

### Common Issues

- **Health Endpoint Unavailable**: Check if startup script completed successfully
- **Resource Monitoring**: Verify metadata scripts are running
- **GPU Access**: Check NVIDIA drivers and Docker GPU support
- **Port Conflicts**: Ensure ports 13337, 8888, and 13133 are available

### Debug Commands

```sh
# Check template logs
tail -f /var/log/template-startup.log

# Verify health endpoint
curl http://localhost:13133

# Check GPU status (GPU template)
nvidia-smi

# Monitor resources
coder stat cpu
coder stat mem
coder stat disk
```

## Contributing

### Template Development

1. **Fork the repository**
2. **Create feature branch**
3. **Implement enhancements**
4. **Test thoroughly**
5. **Submit pull request**

### Enhancement Ideas

- **Additional IDEs**: Support for more development environments
- **Package Management**: Automated package installation and updates
- **Backup/Restore**: Automated backup and restore functionality
- **Multi-GPU Support**: Enhanced GPU management for multiple devices

## Support

For issues and questions:

1. **Check logs**: `/var/log/template-startup.log`
2. **Verify prerequisites**: Docker, NVIDIA drivers, Coder setup
3. **Review configuration**: Template parameters and resource limits
4. **Community support**: Coder community forums and documentation

---

**Note**: These templates are designed for production use with enhanced monitoring and reliability features. They build upon community best practices and add enterprise-grade functionality for professional development environments.
