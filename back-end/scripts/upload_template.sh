#!/bin/bash

# 🚀 Coder Template Upload Script Wrapper
# This script provides a convenient way to upload Coder templates

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if Python script exists
if [ ! -f "upload_coder_template.py" ]; then
    echo -e "${RED}Error: upload_coder_template.py not found in $SCRIPT_DIR${NC}"
    exit 1
fi

# Check if .env file exists and source it
if [ -f "../.env" ]; then
    echo -e "${BLUE}Loading environment from ../.env${NC}"
    export $(cat ../.env | grep -v '^#' | xargs)
elif [ -f ".env" ]; then
    echo -e "${BLUE}Loading environment from .env${NC}"
    export $(cat .env | grep -v '^#' | xargs)
else
    echo -e "${YELLOW}Warning: No .env file found. Make sure CODER_API_TOKEN and CODER_HOST are set.${NC}"
fi

# Check required environment variables
if [ -z "$CODER_API_TOKEN" ]; then
    echo -e "${RED}Error: CODER_API_TOKEN environment variable not set${NC}"
    echo "Please set it in your environment or .env file"
    exit 1
fi

if [ -z "$CODER_HOST" ]; then
    echo -e "${YELLOW}Warning: CODER_HOST not set, using default: https://coder.fisamy.work${NC}"
    export CODER_HOST="https://coder.fisamy.work"
fi

# Function to show usage
show_usage() {
    echo -e "${BLUE}Usage:${NC}"
    echo "  $0 <template_file> [template_name] [display_name] [description]"
    echo "  $0 --list"
    echo "  $0 --delete <template_name>"
    echo ""
    echo -e "${BLUE}Examples:${NC}"
    echo "  $0 ../coder-templates-optimized/docker-distracted_lamport8.zip"
    echo "  $0 ../coder-templates-optimized/docker-distracted_lamport8.zip my-template 'My Template' 'Description here'"
    echo "  $0 --list"
    echo "  $0 --delete my-template"
    echo ""
    echo -e "${BLUE}Environment Variables:${NC}"
    echo "  CODER_API_TOKEN: Your Coder API token"
    echo "  CODER_HOST: Coder instance URL (default: https://coder.fisamy.work)"
}

# Function to check if file exists
check_file() {
    local file="$1"
    if [ ! -f "$file" ]; then
        echo -e "${RED}Error: Template file not found: $file${NC}"
        exit 1
    fi
    
    # Check file size
    local size=$(stat -c%s "$file" 2>/dev/null || stat -f%z "$file" 2>/dev/null)
    local size_mb=$((size / 1024 / 1024))
    echo -e "${BLUE}Template file: $file (${size_mb}MB)${NC}"
}

# Function to upload template
upload_template() {
    local template_file="$1"
    local template_name="$2"
    local display_name="$3"
    local description="$4"
    
    echo -e "${BLUE}🚀 Starting template upload...${NC}"
    
    # Build command
    local cmd="python3 upload_coder_template.py --template-path \"$template_file\""
    
    if [ -n "$template_name" ]; then
        cmd="$cmd --template-name \"$template_name\""
    fi
    
    if [ -n "$display_name" ]; then
        cmd="$cmd --display-name \"$display_name\""
    fi
    
    if [ -n "$description" ]; then
        cmd="$cmd --description \"$description\""
    fi
    
    echo -e "${BLUE}Executing: $cmd${NC}"
    echo ""
    
    # Execute the command
    eval $cmd
}

# Function to list templates
list_templates() {
    echo -e "${BLUE}📋 Listing available templates...${NC}"
    python3 upload_coder_template.py --list-templates
}

# Function to delete template
delete_template() {
    local template_name="$1"
    if [ -z "$template_name" ]; then
        echo -e "${RED}Error: Template name required for deletion${NC}"
        show_usage
        exit 1
    fi
    
    echo -e "${YELLOW}🗑️  Deleting template: $template_name${NC}"
    python3 upload_coder_template.py --delete-template "$template_name"
}

# Main script logic
case "$1" in
    --help|-h|help)
        show_usage
        exit 0
        ;;
    --list)
        list_templates
        exit 0
        ;;
    --delete)
        delete_template "$2"
        exit 0
        ;;
    "")
        echo -e "${RED}Error: No arguments provided${NC}"
        show_usage
        exit 1
        ;;
    *)
        # Check if first argument is a file
        if [ -f "$1" ]; then
            check_file "$1"
            upload_template "$1" "$2" "$3" "$4"
        else
            echo -e "${RED}Error: First argument must be a valid template file${NC}"
            show_usage
            exit 1
        fi
        ;;
esac
