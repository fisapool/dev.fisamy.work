#!/usr/bin/env bash
set -euo pipefail

# Initialize Terraform providers and create/update .terraform.lock.hcl

if ! command -v terraform >/dev/null 2>&1; then
  echo "Error: terraform not found on PATH. Install Terraform and retry." >&2
  exit 1
fi

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$script_dir"

echo "Initializing Terraform in $(pwd) ..."
terraform init -upgrade

echo
echo "Done. If a .terraform.lock.hcl was created/updated, commit it for reproducible provider installs." 
