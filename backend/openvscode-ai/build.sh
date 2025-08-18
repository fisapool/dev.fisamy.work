#!/usr/bin/env bash
set -euo pipefail

echo "Building OpenVSCode AI image..."
docker build -t openvscode-ai:latest .

echo "Image built successfully: openvscode-ai:latest"
echo "You can now run: docker images | grep openvscode-ai"
