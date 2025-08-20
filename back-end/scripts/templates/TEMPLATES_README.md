# Coder Templates Assets

This folder contains ready-to-use startup scripts for the two required Coder templates:

- no-gpu: Basic development environment (VS Code on port 13337)
- gpu: CUDA-enabled AI environment (VS Code on 13337 + Jupyter on 8888)

## Files

- no-gpu/startup.sh: Startup script for the no-gpu template
- gpu/startup.sh: Startup script for the gpu template

## Enhanced Features

- **Health Check Endpoint:** Available at http://localhost:13133 (returns {"status":"ok"})
- **Logging:** 
  - Template startup: `/var/log/template-startup.log`
  - VS Code: `/home/coder/code-server.log`
  - Jupyter (gpu): `/home/coder/jupyter.log`
- **Resource Monitoring:** Background monitoring of memory, disk, and GPU usage
- **Home Directory:** Creates `/home/coder/{projects,data,config}` structure

## How to Use (Coder UI)

1) Navigate to https://coder.fisamy.work/templates → Create Template → Docker
2) Fill basic info:
   - Name: no-gpu (or gpu)
   - Display Name / Description: per project README/specs
3) Version → Docker configuration:
   - Base image: ubuntu:22.04 (no-gpu) or nvidia/cuda:12.4.1-runtime-ubuntu22.04 (gpu)
   - Startup script: copy the contents of the corresponding startup.sh
   - Resources: no-gpu → CPU 2, Memory 4GB; gpu → CPU 8, Memory 16GB, GPU 1
   - For gpu: set env vars NVIDIA_VISIBLE_DEVICES=all, NVIDIA_DRIVER_CAPABILITIES=all
4) Apps:
   - VS Code (both): http://localhost:13337, subdomain enabled, sharing owner
   - Jupyter (gpu only): http://localhost:8888, subdomain enabled, sharing owner
   - Health Check: http://localhost:13133 (optional - for monitoring)
5) Autostop: Mon–Sun, 09:00–17:00 UTC. Allow user autostart/autostop.

## Validate

From back-end/scripts:
- Check templates: python3 validate_coder_templates.py --check-templates-only
- Full validation: python3 validate_coder_templates.py --full-validation

If you prefer API-based creation for the template shells, export CODER_TOKEN and CODER_URL and run ./create_coder_templates.sh, then set versions in the UI.
