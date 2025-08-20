# GPU Variant

Minimal Docker-based example with CUDA-ready base image mirroring your shell startup script approach.

- Image: nvidia/cuda:12.4.1-runtime-ubuntu22.04
- Resources: CPU 8, Memory 16GB (tune as needed), GPU 1
- Ports: VS Code 13337, Jupyter 8888, Health 13133
- Env: NVIDIA_VISIBLE_DEVICES=all, NVIDIA_DRIVER_CAPABILITIES=all

Notes:
- Keep using `templates/gpu/startup.sh` as your canonical startup logic.
- In HCL, you can template the script content in, or mount and execute it.
- Includes basic GPU device requests and health checking.

## Run (example)
This HCL uses the Docker provider for illustration. Adjust to your environment and GPU runtime.

```
terraform init
terraform apply
```
