#!/bin/bash
# Create Coder Templates Script
# This script creates the required templates using the Coder API directly

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

# Create No-GPU Template
create_no_gpu_template() {
    print_status "Creating No-GPU template..."
    
    local template_data='{
        "name": "no-gpu",
        "display_name": "No GPU Environment",
        "description": "Basic development environment without GPU",
        "default_ttl_ms": 3600000,
        "activity_bump_ms": 3600000,
        "autostop_requirement": {
            "days_of_week": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
            "start_time": "09:00",
            "stop_time": "17:00",
            "timezone": "UTC"
        },
        "autostart_requirement": {
            "days_of_week": ["monday", "tuesday", "wednesday", "thursday", "friday"]
        },
        "allow_user_autostart": true,
        "allow_user_autostop": true,
        "allow_user_cancel_workspace_jobs": true,
        "failure_ttl_ms": 0,
        "time_til_dormant_ms": 0,
        "time_til_dormant_autodelete_ms": 0,
        "require_active_version": false,
        "max_port_share_level": "public"
    }'
    
    local response=$(curl -s -w "%{http_code}" -X POST \
        -H "Authorization: Bearer $CODER_TOKEN" \
        -H "Content-Type: application/json" \
        -d "$template_data" \
        "$CODER_URL/api/v2/organizations/coder/templates")
    
    local http_code="${response: -3}"
    local response_body="${response%???}"
    
    if [ "$http_code" = "201" ]; then
        local template_id=$(echo "$response_body" | jq -r '.id')
        print_success "No-GPU template created with ID: $template_id"
        echo "$template_id" > /tmp/no_gpu_template_id.txt
    else
        print_error "Failed to create No-GPU template. HTTP: $http_code"
        echo "Response: $response_body"
        return 1
    fi
}

# Create GPU Template
create_gpu_template() {
    print_status "Creating GPU template..."
    
    local template_data='{
        "name": "gpu",
        "display_name": "GPU Environment",
        "description": "CUDA-enabled development environment for AI workloads",
        "default_ttl_ms": 7200000,
        "activity_bump_ms": 3600000,
        "autostop_requirement": {
            "days_of_week": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
            "start_time": "09:00",
            "stop_time": "17:00",
            "timezone": "UTC"
        },
        "autostart_requirement": {
            "days_of_week": ["monday", "tuesday", "wednesday", "thursday", "friday"]
        },
        "allow_user_autostart": true,
        "allow_user_autostop": true,
        "allow_user_cancel_workspace_jobs": true,
        "failure_ttl_ms": 0,
        "time_til_dormant_ms": 0,
        "time_til_dormant_autodelete_ms": 0,
        "require_active_version": false,
        "max_port_share_level": "public"
    }'
    
    local response=$(curl -s -w "%{http_code}" -X POST \
        -H "Authorization: Bearer $CODER_TOKEN" \
        -H "Content-Type: application/json" \
        -d "$template_data" \
        "$CODER_URL/api/v2/organizations/coder/templates")
    
    local http_code="${response: -3}"
    local response_body="${response%???}"
    
    if [ "$http_code" = "201" ]; then
        local template_id=$(echo "$response_body" | jq -r '.id')
        print_success "GPU template created with ID: $template_id"
        echo "$template_id" > /tmp/gpu_template_id.txt
    else
        print_error "Failed to create GPU template. HTTP: $http_code"
        echo "Response: $response_body"
        return 1
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

# Main execution
main() {
    echo "=========================================="
    echo "Coder Templates Creation"
    echo "=========================================="
    echo ""
    
    check_environment
    list_templates
    
    # Check if templates already exist
    local existing_templates=$(curl -s -H "Authorization: Bearer $CODER_TOKEN" \
        "$CODER_URL/api/v2/organizations/coder/templates" | \
        jq -r '.[] | .name')
    
    if echo "$existing_templates" | grep -q "no-gpu"; then
        print_warning "No-GPU template already exists, skipping creation"
    else
        create_no_gpu_template
    fi
    
    if echo "$existing_templates" | grep -q "gpu"; then
        print_warning "GPU template already exists, skipping creation"
    else
        create_gpu_template
    fi
    
    echo ""
    echo "=========================================="
    print_success "Template creation complete!"
    echo "=========================================="
    echo ""
    
    if [ -f "/tmp/no_gpu_template_id.txt" ]; then
        echo "No-GPU Template ID: $(cat /tmp/no_gpu_template_id.txt)"
    fi
    
    if [ -f "/tmp/gpu_template_id.txt" ]; then
        echo "GPU Template ID: $(cat /tmp/gpu_template_id.txt)"
    fi
    
    echo ""
    echo "Templates are available at: $CODER_URL/templates"
    echo ""
    echo "Note: You'll need to configure the template versions with Docker images and startup scripts"
    echo "through the Coder UI or CLI, as Terraform no longer supports template management."
}

# Run main function
main "$@"
