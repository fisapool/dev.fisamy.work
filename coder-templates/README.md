# Coder Templates

This directory contains ready-to-upload templates for Coder.

## Templates

### no-gpu/
- **Image**: Ubuntu 22.04
- **Resources**: 2 CPU, 4GB RAM
- **Apps**: VS Code (port 13337)
- **Use case**: Lightweight development environment

### gpu/
- **Image**: NVIDIA CUDA 12.4.1 + Ubuntu 22.04
- **Resources**: 8 CPU, 16GB RAM, 1 GPU
- **Apps**: VS Code (port 13337) + Jupyter Lab (port 8888)
- **Use case**: Machine learning and GPU-accelerated development

## Upload Instructions

1. **Package the templates**:
   ```bash
   # From this directory:
   tar -czf no-gpu.tar.gz no-gpu/
   tar -czf gpu.tar.gz gpu/
   ```

2. **Upload to Coder**:
   - Go to your Coder dashboard
   - Click "Upload template"
   - Select the `.tar.gz` file
   - Fill in name, description, and icon
   - Save

## Features

Both templates include:
- Automatic package updates
- VS Code Server installation
- Health monitoring endpoint (port 13133)
- Resource monitoring
- Auto-stop configuration (9 AM - 5 PM UTC)
- User 'coder' with proper permissions

GPU template additionally includes:
- CUDA toolkit
- Jupyter Lab
- PyTorch, TensorFlow, and ML libraries
- GPU resource monitoring
