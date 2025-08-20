#!/bin/bash

# 🚀 Coder Template Setup Script
# This script prepares the no-gpu and gpu templates for manual creation in Coder

set -e

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

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "🚀 Coder Template Setup Script"
echo "=============================="
echo

# Check if we're in the right directory
if [ ! -d "no-gpu" ] || [ ! -d "gpu" ]; then
    print_error "Please run this script from the coder-templates directory"
    exit 1
fi

print_status "Preparing templates for manual creation in Coder..."

# Create template archives
print_status "Creating template archives..."

# Create no-gpu template archive
if [ -d "no-gpu" ]; then
    tar -czf "no-gpu-template.tar.gz" -C "no-gpu" .
    print_success "Created no-gpu-template.tar.gz"
else
    print_error "no-gpu directory not found"
    exit 1
fi

# Create gpu template archive
if [ -d "gpu" ]; then
    tar -czf "gpu-template.tar.gz" -C "gpu" .
    print_success "Created gpu-template.tar.gz"
else
    print_error "gpu directory not found"
    exit 1
fi

# Display template specifications
echo
echo "📋 Template Specifications"
echo "========================="
echo

echo "🔧 Template 1: no-gpu (Basic Development)"
echo "   - Name: no-gpu"
echo "   - Display Name: No GPU Environment"
echo "   - Image: ubuntu:22.04"
echo "   - CPU: 2"
echo "   - Memory: 4 GiB"
echo "   - Disk: 10 GiB"
echo "   - Apps: VS Code (port 13337)"
echo "   - Health Check: port 13133"
echo

echo "🔧 Template 2: gpu (AI Development)"
echo "   - Name: gpu"
echo "   - Display Name: GPU Environment"
echo "   - Image: nvidia/cuda:12.4.1-runtime-ubuntu22.04"
echo "   - CPU: 8"
echo "   - Memory: 16 GiB"
echo "   - Disk: 20 GiB"
echo "   - GPU: 1"
echo "   - Apps: VS Code (port 13337), Jupyter Lab (port 8888)"
echo "   - Health Check: port 13133"
echo

# Display manual creation steps
echo "📝 Manual Creation Steps"
echo "========================"
echo
echo "1. Navigate to your Coder dashboard: https://coder.fisamy.work/templates"
echo "2. Click 'Create Template' for each template"
echo "3. Choose 'Docker' as the provisioner"
echo "4. Use the specifications above"
echo "5. Copy the startup script content from the respective startup.sh files"
echo "6. Configure apps and variables as specified"
echo

# Show startup script content for easy copying
echo "📄 Startup Scripts"
echo "=================="
echo

echo "🔧 no-gpu startup script (copy this):"
echo "--------------------------------------"
cat "no-gpu/startup.sh"
echo
echo "--------------------------------------"
echo

echo "🔧 gpu startup script (copy this):"
echo "-----------------------------------"
cat "gpu/startup.sh"
echo
echo "-----------------------------------"
echo

print_success "Template preparation complete!"
echo
print_status "Next steps:"
echo "1. Follow the manual creation steps above"
echo "2. Use the startup script content provided"
echo "3. Test the templates by creating workspaces"
echo "4. Run validation scripts to verify functionality"
echo
print_status "For detailed instructions, see TEMPLATE_SETUP_GUIDE.md"
echo
print_status "Template archives created:"
echo "  - no-gpu-template.tar.gz"
echo "  - gpu-template.tar.gz"
echo
print_status "You can now manually create these templates in Coder!"
