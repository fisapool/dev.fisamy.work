#!/bin/bash

# 🚀 Coder Template Setup & Validation Script
# This script helps you set up and validate the required Coder templates

set -e

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

# Check if we're in the right directory
if [ ! -f "create_coder_templates.py" ]; then
    print_error "Please run this script from the back-end/scripts directory"
    exit 1
fi

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not installed"
    exit 1
fi

# Check if required packages are installed
print_status "Checking Python dependencies..."
if ! python3 -c "import requests" &> /dev/null; then
    print_warning "requests package not found, installing..."
    pip3 install -r requirements.txt
fi

# Check environment variables
print_status "Checking environment variables..."
if [ -z "$CODER_API_TOKEN" ]; then
    print_error "CODER_API_TOKEN environment variable not set!"
    print_error "Please set it in your environment or .env file"
    print_error "Example: export CODER_API_TOKEN=your_token_here"
    exit 1
fi

if [ -z "$CODER_HOST" ]; then
    print_warning "CODER_HOST not set, using default: https://coder.fisamy.work"
    export CODER_HOST="https://coder.fisamy.work"
fi

print_success "Environment variables configured"

# Main menu
echo
echo "🚀 Coder Template Setup & Validation"
echo "====================================="
echo
echo "Choose an option:"
echo "1. Show template specifications"
echo "2. Show manual creation steps"
echo "3. Check existing templates"
echo "4. Test workspace functionality"
echo "5. Run full validation"
echo "6. Exit"
echo

read -p "Enter your choice (1-6): " choice

case $choice in
    1)
        print_status "Showing template specifications..."
        python3 create_coder_templates.py --specs
        ;;
    2)
        print_status "Showing manual creation steps..."
        python3 create_coder_templates.py --manual-steps
        ;;
    3)
        print_status "Checking existing templates..."
        python3 validate_coder_templates.py --check-templates-only
        ;;
    4)
        print_status "Testing workspace functionality..."
        python3 validate_coder_templates.py --test-workspaces
        ;;
    5)
        print_status "Running full validation..."
        python3 validate_coder_templates.py --full-validation
        ;;
    6)
        print_status "Exiting..."
        exit 0
        ;;
    *)
        print_error "Invalid choice. Please enter a number between 1 and 6."
        exit 1
        ;;
esac

echo
print_success "Operation completed successfully!"
echo
print_status "Next steps:"
echo "1. If templates don't exist, create them manually using the Coder UI"
echo "2. Use the validation scripts to test functionality"
echo "3. Check the CODER_TEMPLATE_SETUP_GUIDE.md for detailed instructions"
echo
print_status "Manual template creation URL: https://coder.fisamy.work/templates"
