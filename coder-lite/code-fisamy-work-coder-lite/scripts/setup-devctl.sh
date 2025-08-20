#!/usr/bin/env bash
set -euo pipefail

# Enhanced devctl Setup Script
# This script sets up the enhanced devctl environment

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="/usr/local/bin"
CONFIG_DIR="/etc/devctl"
DATA_ROOT="/srv/devdata"
LOG_DIR="/var/log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root"
        exit 1
    fi
}

check_dependencies() {
    local deps=("docker" "docker-compose" "ss" "awk" "sed" "grep")
    local missing=()
    
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" >/dev/null 2>&1; then
            missing+=("$dep")
        fi
    done
    
    if [[ ${#missing[@]} -gt 0 ]]; then
        print_error "Missing dependencies: ${missing[*]}"
        print_info "Install with: apt-get install docker.io docker-compose iproute2"
        exit 1
    fi
    
    print_info "All dependencies satisfied"
}

create_directories() {
    print_info "Creating directories..."
    
    mkdir -p "$CONFIG_DIR"
    mkdir -p "$DATA_ROOT"
    mkdir -p "$LOG_DIR"
    
    # Set proper permissions
    chmod 755 "$CONFIG_DIR"
    chmod 755 "$DATA_ROOT"
    
    print_info "Directories created successfully"
}

install_files() {
    print_info "Installing devctl files..."
    
    # Install main script
    cp "$SCRIPT_DIR/devctl-enhanced" "$INSTALL_DIR/devctl"
    chmod +x "$INSTALL_DIR/devctl"
    
    # Install configuration
    if [[ ! -f "$CONFIG_DIR/devctl.conf" ]]; then
        cp "$SCRIPT_DIR/devctl.conf.example" "$CONFIG_DIR/devctl.conf"
        print_info "Configuration installed to $CONFIG_DIR/devctl.conf"
    else
        print_warning "Configuration already exists, skipping"
    fi
    
    # Install enhanced docker-compose override
    cp "$SCRIPT_DIR/docker-compose.override-enhanced.yml" "$CONFIG_DIR/docker-compose.override.yml.example"
    
    print_info "Files installed successfully"
}

setup_xfs_quota() {
    print_info "Setting up XFS quota support..."
    
    if ! command -v xfs_quota >/dev/null 2>&1; then
        print_warning "xfs_quota not found, skipping quota setup"
        return
    fi
    
    # Check if /srv is mounted with prjquota
    if ! mount | grep -q "prjquota" /srv; then
        print_warning "XFS project quota not enabled on /srv"
        print_info "To enable: mount -o remount,prjquota /srv"
    else
        print_info "XFS quota support detected"
    fi
}

setup_caddy() {
    print_info "Setting up Caddy integration..."
    
    if ! command -v caddy >/dev/null 2>&1; then
        print_warning "Caddy not found, skipping Caddy setup"
        return
    fi
    
    # Create Caddyfile if it doesn't exist
    if [[ ! -f "/etc/caddy/Caddyfile" ]]; then
        mkdir -p /etc/caddy
        cat > /etc/caddy/Caddyfile <<EOF
{
  email admin@example.com
}
EOF
        print_info "Created basic Caddyfile at /etc/caddy/Caddyfile"
    fi
    
    # Enable and start Caddy service
    if systemctl is-active --quiet caddy; then
        print_info "Caddy service is running"
    else
        print_warning "Caddy service is not running"
        print_info "Start with: systemctl enable --now caddy"
    fi
}

create_systemd_service() {
    print_info "Creating systemd service for devctl..."
    
    cat > /etc/systemd/system/devctl.service <<EOF
[Unit]
Description=Development Environment Controller
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
ExecStart=/usr/local/bin/devctl list
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    print_info "Systemd service created"
}

test_installation() {
    print_info "Testing installation..."
    
    # Test devctl command
    if command -v devctl >/dev/null 2>&1; then
        print_info "devctl command is available"
    else
        print_error "devctl command not found"
        exit 1
    fi
    
    # Test configuration
    if [[ -f "$CONFIG_DIR/devctl.conf" ]]; then
        print_info "Configuration file is present"
    else
        print_error "Configuration file missing"
        exit 1
    fi
    
    # Test Docker
    if docker info >/dev/null 2>&1; then
        print_info "Docker is running"
    else
        print_error "Docker is not running"
        exit 1
    fi
    
    print_info "Installation test passed"
}

show_usage() {
    cat <<EOF

Enhanced devctl installation completed successfully!

Usage:
  devctl create <username> [options]
  devctl update <username> [options]
  devctl delete <username> [--purge]
  devctl list
  devctl status <username>

Examples:
  devctl create john --cpu 4 --ram 8g --disk 50
  devctl create jane --domain jane.dev.example.com --healthcheck-enable
  devctl list
  devctl status john

Configuration:
  Main config: $CONFIG_DIR/devctl.conf
  Data root: $DATA_ROOT
  Logs: $LOG_DIR/devctl.log

Next steps:
  1. Review configuration: $CONFIG_DIR/devctl.conf
  2. Create your first user: devctl create testuser
  3. Start the environment: docker compose up -d testuser

For more information, see: $CONFIG_DIR/README.md
EOF
}

main() {
    print_info "Starting enhanced devctl setup..."
    
    check_root
    check_dependencies
    create_directories
    install_files
    setup_xfs_quota
    setup_caddy
    create_systemd_service
    test_installation
    
    print_info "Setup completed successfully!"
    show_usage
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [--help]"
        echo "Setup script for enhanced devctl"
        exit 0
        ;;
    *)
        main
        ;;
esac
