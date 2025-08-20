# Coder Provider Terraform Templates

This directory contains Coder provider Terraform templates for both GPU and no-GPU environments.

## Templates

### 1. GPU Template (`gpu/coder-template.tf`)
- **Name**: gpu
- **Display Name**: GPU Environment
- **Image**: nvidia/cuda:12.4.1-runtime-ubuntu22.04
- **Resources**: 8 CPU, 16GB RAM, 1 GPU
- **Apps**: VS Code (port 13337), Jupyter Lab (port 8888)
- **Healthcheck**: HTTP to localhost:13133
- **Features**: PyTorch with CUDA 12.4 support, Python packages, VS Code Server

### 2. No-GPU Template (`no-gpu/coder-template.tf`)
- **Name**: no-gpu
- **Display Name**: No GPU Headless
- **Image**: ubuntu:22.04
- **Resources**: 2 CPU, 4GB RAM
- **Apps**: None (headless)
- **Healthcheck**: None
- **Features**: Minimal environment for background tasks

## Usage

### Option 1: CLI Push (Recommended)

1. **Login to Coder**:
   ```bash
   coder login https://coder.fisamy.work
   ```

2. **Push GPU Template**:
   ```bash
   cd gpu
   coder templates push . --name gpu
   ```

3. **Push No-GPU Template**:
   ```bash
   cd ../no-gpu
   coder templates push . --name no-gpu
   ```

### Option 2: Manual UI Creation

1. Navigate to https://coder.fisamy.work/templates
2. Click "Create Template" → "Docker"
3. Use the settings from the original specifications in your message

## Template Features

### GPU Template
- CUDA 12.4 runtime with PyTorch support
- VS Code Server with no authentication
- Jupyter Lab with no authentication
- Health monitoring server on port 13133
- Automatic workspace scheduling (9 AM start, 5 PM stop)

### No-GPU Template
- Minimal Ubuntu 22.04 base
- No exposed ports or applications
- Lightweight resource usage
- Suitable for background processing tasks

## File Structure

```
docker-distracted_lamport8/
├── gpu/
│   ├── coder-template.tf    # Coder provider GPU template
│   ├── main.tf             # Original Docker provider template
│   └── README.md
├── no-gpu/
│   ├── coder-template.tf   # Coder provider no-GPU template
│   ├── main.tf             # Original Docker provider template
│   └── README.md
├── main.tf                 # Shared configuration
├── variables.tf            # Shared variables
├── README.md              # Original documentation
└── README-CODER.md        # This file
```

## Notes

- The Coder provider templates use `coder_agent`, `coder_app`, and `coder_template` resources
- Both templates include automatic workspace scheduling
- GPU template includes comprehensive health monitoring
- No-GPU template is designed for minimal resource usage
- All templates use the latest Coder provider (~> 0.20.0)
