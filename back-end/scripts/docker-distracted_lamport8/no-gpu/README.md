# No-GPU Variant

Minimal Docker-based example mirroring your shell startup script approach.

- Image: ubuntu:22.04
- Resources: CPU 2, Memory 4GB (tune as needed)
- Ports: VS Code 13337, Health 13133
- Health: Lightweight HTTP JSON endpoint on :13133

Notes:
- Keep using `templates/no-gpu/startup.sh` as your canonical startup logic.
- In HCL, you can template the script content in, or mount and execute it.
- This example shows resource limits, labels, and health checking.

## Run (example)
This HCL uses the Docker provider for illustration. Adjust to your environment.

```
terraform init
terraform apply
```
