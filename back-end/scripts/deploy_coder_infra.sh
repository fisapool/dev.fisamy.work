#!/bin/bash
# Coder Infrastructure Deployment Script
# This script provides guidance for setting up Coder templates and infrastructure

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if curl is available
    if ! command -v curl &> /dev/null; then
        print_error "curl is not installed. Please install curl first."
        exit 1
    fi
    
    # Check if jq is installed
    if ! command -v jq &> /dev/null; then
        print_error "jq is not installed. Please install jq first."
        exit 1
    fi
    
    print_success "All prerequisites met"
}

# Check environment variables
check_environment() {
    print_status "Checking environment variables..."
    
    if [ -z "${CODER_TOKEN:-}" ]; then
        print_error "CODER_TOKEN is not set"
        echo "Please set it with: export CODER_TOKEN='your_admin_pat_here'"
        exit 1
    fi
    
    if [ -z "${CODER_URL:-}" ]; then
        print_error "CODER_URL is not set"
        echo "Please set it with: export CODER_URL='https://coder.fisamy.work'"
        exit 1
    fi
    
    print_success "Environment variables configured"
}

# Check Coder connectivity
check_coder_connectivity() {
    print_status "Checking Coder connectivity..."
    
    if curl -s -f -H "Authorization: Bearer $CODER_TOKEN" "$CODER_URL/api/v2/workspaces" > /dev/null; then
        print_success "Coder is accessible"
    else
        print_error "Cannot connect to Coder. Please check your token and URL."
        exit 1
    fi
}

# List existing templates
list_templates() {
    print_status "Listing existing templates..."
    
    local response=$(curl -s -H "Authorization: Bearer $CODER_TOKEN" \
        "$CODER_URL/api/v2/organizations/coder/templates")
    
    echo "Current templates:"
    echo "$response" | jq -r '.[] | "  - \(.name) (\(.display_name)): \(.id)"'
    echo ""
}

# Setup Uptime Kuma monitoring
setup_monitoring() {
    print_status "Setting up Uptime Kuma monitoring..."
    
    if [ -f "/etc/fisamy/uptime.env" ]; then
        print_status "Uptime Kuma environment found, setting up monitors..."
        bash "$(dirname "$0")/setup_uptime_kuma.sh"
        print_success "Uptime Kuma monitoring configured"
    else
        print_warning "Uptime Kuma environment not found at /etc/fisamy/uptime.env"
        print_status "Skipping monitoring setup. Run setup_uptime_kuma.sh manually later."
    fi
}

# Provide manual template creation guidance
provide_template_guidance() {
    echo ""
    echo "=========================================="
    echo "Template Creation Guidance"
    echo "=========================================="
    echo ""
    echo "Since Terraform no longer supports Coder template management,"
    echo "you'll need to create templates manually through the Coder UI:"
    echo ""
    echo "1. Go to: $CODER_URL/templates"
    echo "2. Click 'Create Template'"
    echo "3. Choose 'Docker' as the provisioner"
    echo "4. Configure the following templates:"
    echo ""
    echo "   NO-GPU Template:"
    echo "   - Name: no-gpu"
    echo "   - Display Name: No GPU Environment"
    echo "   - Description: Basic development environment without GPU"
    echo "   - Image: ubuntu:22.04"
    echo "   - CPU: 2"
    echo "   - Memory: 4GB"
    echo "   - Default TTL: 1 hour"
    echo "   - Startup Script: Install code-server and start it on port 13337"
    echo ""
    echo "   GPU Template:"
    echo "   - Name: gpu"
    echo "   - Display Name: GPU Environment"
    echo "   - Description: CUDA-enabled development environment for AI workloads"
    echo "   - Image: nvidia/cuda:12.4.1-runtime-ubuntu22.04"
    echo "   - CPU: 8"
    echo "   - Memory: 16GB"
    echo "   - GPU: 1"
    echo "   - Default TTL: 2 hours"
    echo "   - Startup Script: Install Python, PyTorch, Jupyter, and start services"
    echo ""
    echo "5. Configure autostop requirements (9 AM - 5 PM UTC)"
    echo "6. Set appropriate resource limits"
    echo ""
}

# Validate deployment
validate_deployment() {
    print_status "Validating deployment..."
    
    # Check if Coder is accessible
    if curl -s -f "$CODER_URL/health" > /dev/null; then
        print_success "Coder is accessible"
    else
        print_warning "Coder health check failed - may still be starting up"
    fi
    
    # List templates again
    list_templates
}

# Main deployment flow
main() {
    echo "=========================================="
    echo "Coder Infrastructure Deployment"
    echo "=========================================="
    echo ""
    
    check_prerequisites
    check_environment
    check_coder_connectivity
    list_templates
    setup_monitoring
    provide_template_guidance
    validate_deployment
    
    echo ""
    echo "=========================================="
    print_success "Deployment guidance complete!"
    echo "=========================================="
    echo ""
    echo "Next steps:"
    echo "1. Create the required templates manually through the Coder UI"
    echo "2. Test the templates by creating workspaces"
    echo "3. Verify GPU access in GPU template"
    echo "4. Check autostop functionality"
    echo "5. Monitor resource usage"
    echo ""
    echo "Templates will be available at: $CODER_URL/templates"
    echo ""
    echo "Note: The modern Coder provider no longer supports template management"
    echo "through Terraform. Templates must be created manually or through the CLI."
}

# Run main function
main "$@"
