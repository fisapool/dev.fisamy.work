#!/bin/bash
# Terraform Configuration Validation Script
# This script validates the Terraform configuration without applying it

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "main.tf" ]; then
    print_error "This script must be run from the terraform directory"
    print_status "Changing to terraform directory..."
    cd "$(dirname "$0")/../terraform"
fi

print_status "Validating Terraform configuration..."

# Check Terraform syntax
print_status "Checking Terraform syntax..."
if terraform fmt -check -recursive .; then
    print_success "Terraform formatting is correct"
else
    print_error "Terraform formatting issues found"
    print_status "Running terraform fmt to fix formatting..."
    terraform fmt -recursive .
fi

# Validate configuration
print_status "Validating Terraform configuration..."
if terraform validate; then
    print_success "Terraform configuration is valid"
else
    print_error "Terraform configuration validation failed"
    exit 1
fi

# Check for required variables
print_status "Checking required variables..."
if [ -z "${TF_VAR_coder_token:-}" ]; then
    print_error "TF_VAR_coder_token is not set"
    echo "Please set it with: export TF_VAR_coder_token='your_admin_pat_here'"
    exit 1
fi

print_success "TF_VAR_coder_token is set"

# Plan without applying
print_status "Creating Terraform plan..."
if terraform plan -out=tfplan; then
    print_success "Terraform plan created successfully"
    print_status "Plan file saved as 'tfplan'"
    print_status "To apply: terraform apply tfplan"
else
    print_error "Terraform plan failed"
    exit 1
fi

print_success "Validation complete! Configuration is ready for deployment."
