# Docker Template: distracted_lamport8

This folder provides two Docker-based Coder template variants that mirror your current shell-based setup, with a path to migrate toward HCL/IaC if desired.

- no-gpu: Basic development environment with VS Code on port 13337
- gpu: CUDA-enabled environment with VS Code on 13337 and Jupyter on 8888

Both variants assume a lightweight health endpoint on port 13133 (as added to your startup scripts).

## Variants

- no-gpu/: HCL skeleton for a non-GPU workspace
- gpu/: HCL skeleton with GPU device requests and CUDA-ready base image

These examples are intentionally minimal and meant as starting points. They show resource limits, labels, health checks, and basic app ports.

## Quick Notes

- Health check: http://localhost:13133 (JSON {"status":"ok"})
- VS Code: http://localhost:13337
- Jupyter (gpu only): http://localhost:8888
- Startup logic: Keep using the existing shell scripts you added under `templates/` or adapt these into HCL via templating.

## Using With Terraform (Optional)

- The HCL uses the Docker provider to illustrate container/runtime aspects and adds helpful metadata/health checks. These are examples; adapt to your environment and provider versions.
- If you prefer Coder’s UI-managed Docker provisioner, use these as reference, not for direct deployment.

## Files

- README.md: This document
- main.tf: High-level shared values and commentary (reference)
- no-gpu/main.tf: No-GPU HCL example
- no-gpu/README.md: Notes and usage
- gpu/main.tf: GPU HCL example
- gpu/README.md: Notes and usage
