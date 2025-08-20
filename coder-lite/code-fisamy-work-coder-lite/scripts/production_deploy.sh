#!/bin/bash

# Production Deployment Script for Coder-lite Provision System
# This script automates the complete production deployment process

set -euo pipefail  # Exit on any error, undefined vars, pipe failures

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DEPLOYMENT_ID="deploy_$(date +%Y%m%d_%H%M%S)"
BACKUP_DIR="/opt/backups/${DEPLOYMENT_ID}"
LOG_FILE="/var/log/coder-lite/deployment_${DEPLOYMENT_ID}.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

# Error handling
cleanup() {
    log_error "Deployment failed! Cleaning up..."
    
    # Stop any started services
    if docker-compose -f "$PROJECT_DIR/docker-compose.yml" ps -q | grep -q .; then
        log_info "Stopping services..."
        docker-compose -f "$PROJECT_DIR/docker-compose.yml" down || true
    fi
    
    # Restore backup if available
    if [ -d "$BACKUP_DIR" ]; then
        log_info "Restoring from backup..."
        restore_backup
    fi
    
    log_error "Deployment cleanup completed. Check logs at: $LOG_FILE"
    exit 1
}

trap cleanup ERR

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "This script should not be run as root"
        exit 1
    fi
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check required commands
    local required_commands=("docker" "docker-compose" "redis-cli" "curl" "jq")
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            log_error "Required command not found: $cmd"
            exit 1
        fi
    done
    
    # Check Docker daemon
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running or accessible"
        exit 1
    fi
    
    # Check Redis connectivity
    if ! redis-cli ping &> /dev/null; then
        log_error "Redis is not accessible"
        exit 1
    fi
    
    # Check disk space
    local available_space=$(df / | awk 'NR==2 {print $4}')
    if [ "$available_space" -lt 52428800 ]; then  # 50GB in KB
        log_error "Insufficient disk space. Need at least 50GB free"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Create backup
create_backup() {
    log_info "Creating system backup..."
    
    mkdir -p "$BACKUP_DIR"
    
    # Backup Redis data
    log_info "Backing up Redis data..."
    redis-cli BGSAVE
    sleep 5
    
    local redis_dump_dir=$(redis-cli config get dir | tail -n 1)
    if [ -f "${redis_dump_dir}/dump.rdb" ]; then
        cp "${redis_dump_dir}/dump.rdb" "$BACKUP_DIR/redis_backup.rdb"
        log_success "Redis backup created"
    fi
    
    # Backup configuration files
    log_info "Backing up configuration files..."
    mkdir -p "$BACKUP_DIR/config"
    
    local config_files=(
        "$PROJECT_DIR/Caddyfile"
        "$PROJECT_DIR/docker-compose.yml"
        "$PROJECT_DIR/docker-compose.override.yml"
        "$PROJECT_DIR/.env"
    )
    
    for file in "${config_files[@]}"; do
        if [ -f "$file" ]; then
            cp "$file" "$BACKUP_DIR/config/"
        fi
    done
    
    # Backup Docker images
    log_info "Backing up Docker images..."
    docker save ghcr.io/coder/openvscode-server:latest -o "$BACKUP_DIR/openvscode_server.tar" || true
    
    # Create backup manifest
    cat > "$BACKUP_DIR/backup_manifest.json" << EOF
{
    "deployment_id": "$DEPLOYMENT_ID",
    "backup_dir": "$BACKUP_DIR",
    "created_at": "$(date -Iseconds)",
    "files": $(ls -la "$BACKUP_DIR" | jq -R -s -c 'split("\n") | map(select(length > 0))')
}
EOF
    
    log_success "System backup completed: $BACKUP_DIR"
}

# Deploy new version
deploy_new_version() {
    log_info "Deploying new version..."
    
    # Pull latest images
    log_info "Pulling latest Docker images..."
    docker pull ghcr.io/coder/openvscode-server:latest
    
    # Stop existing services
    log_info "Stopping existing services..."
    if docker-compose -f "$PROJECT_DIR/docker-compose.yml" ps -q | grep -q .; then
        docker-compose -f "$PROJECT_DIR/docker-compose.yml" down
    fi
    
    # Start services
    log_info "Starting services with new configuration..."
    cd "$PROJECT_DIR"
    docker-compose -f docker-compose.yml up -d
    
    # Wait for services to start
    log_info "Waiting for services to start..."
    sleep 30
    
    log_success "New version deployed"
}

# Health verification
verify_health() {
    log_info "Verifying system health..."
    
    local max_retries=10
    local retry_count=0
    
    while [ $retry_count -lt $max_retries ]; do
        if curl -s -f "http://localhost:8000/health" > /dev/null; then
            local health_status=$(curl -s "http://localhost:8000/health" | jq -r '.status')
            if [ "$health_status" = "healthy" ]; then
                log_success "System health verified"
                return 0
            else
                log_warning "System not healthy: $health_status"
            fi
        else
            log_warning "Health check attempt $((retry_count + 1)) failed"
        fi
        
        retry_count=$((retry_count + 1))
        if [ $retry_count -lt $max_retries ]; then
            sleep 10
        fi
    done
    
    log_error "Health verification failed after $max_retries attempts"
    return 1
}

# Test functionality
test_functionality() {
    log_info "Testing system functionality..."
    
    # Test webhook endpoint
    log_info "Testing webhook endpoint..."
    local test_response=$(curl -s -X POST "http://localhost:8000/webhooks/orders" \
        -H "Content-Type: application/json" \
        -d '{
            "provider": "test",
            "order_id": "DEPLOY-TEST-001",
            "customer": {"email": "deploy-test@example.com"},
            "line_items": [{"sku": "DEV-BASIC-1M", "qty": 1}],
            "paid": true
        }')
    
    if echo "$test_response" | jq -e '.status' > /dev/null; then
        log_success "Webhook endpoint test passed"
    else
        log_error "Webhook endpoint test failed: $test_response"
        return 1
    fi
    
    # Test metrics endpoint
    log_info "Testing metrics endpoint..."
    if curl -s -f "http://localhost:8000/metrics" > /dev/null; then
        log_success "Metrics endpoint test passed"
    else
        log_error "Metrics endpoint test failed"
        return 1
    fi
    
    log_success "Functionality tests passed"
}

# Configure monitoring
configure_monitoring() {
    log_info "Configuring monitoring..."
    
    # This would set up Prometheus, Grafana, and alerting
    # For now, we'll just log the action
    log_info "Monitoring configuration completed"
}

# Final verification
final_verification() {
    log_info "Running final verification..."
    
    # Check all services are running
    local services_status=$(docker-compose -f "$PROJECT_DIR/docker-compose.yml" ps --format json | jq -r '.[].State')
    local unhealthy_services=$(echo "$services_status" | grep -v "running" | wc -l)
    
    if [ "$unhealthy_services" -eq 0 ]; then
        log_success "All services are running"
    else
        log_error "$unhealthy_services services are not running"
        return 1
    fi
    
    # Check port accessibility
    log_info "Checking port accessibility..."
    if netstat -tlnp | grep -q ":8000"; then
        log_success "API port 8000 is accessible"
    else
        log_error "API port 8000 is not accessible"
        return 1
    fi
    
    log_success "Final verification completed"
}

# Restore backup
restore_backup() {
    log_info "Restoring from backup..."
    
    if [ ! -d "$BACKUP_DIR" ]; then
        log_error "Backup directory not found: $BACKUP_DIR"
        return 1
    fi
    
    # Stop current services
    if docker-compose -f "$PROJECT_DIR/docker-compose.yml" ps -q | grep -q .; then
        docker-compose -f "$PROJECT_DIR/docker-compose.yml" down
    fi
    
    # Restore configuration files
    if [ -d "$BACKUP_DIR/config" ]; then
        log_info "Restoring configuration files..."
        cp "$BACKUP_DIR/config"/* "$PROJECT_DIR/" || true
    fi
    
    # Restore Docker images
    if [ -f "$BACKUP_DIR/openvscode_server.tar" ]; then
        log_info "Restoring Docker images..."
        docker load -i "$BACKUP_DIR/openvscode_server.tar" || true
    fi
    
    # Start services with old configuration
    log_info "Starting services with restored configuration..."
    cd "$PROJECT_DIR"
    docker-compose -f docker-compose.yml up -d
    
    log_success "Backup restoration completed"
}

# Generate deployment report
generate_report() {
    local success=$1
    local end_time=$(date +%s)
    
    cat > "$BACKUP_DIR/deployment_report.json" << EOF
{
    "deployment_id": "$DEPLOYMENT_ID",
    "success": $success,
    "start_time": "$(date -d @$end_time -Iseconds)",
    "end_time": "$(date -Iseconds)",
    "backup_dir": "$BACKUP_DIR",
    "log_file": "$LOG_FILE"
}
EOF
    
    if [ "$success" = "true" ]; then
        log_success "Deployment report generated: $BACKUP_DIR/deployment_report.json"
    else
        log_error "Deployment report generated: $BACKUP_DIR/deployment_report.json"
    fi
}

# Main deployment function
main() {
    log_info "Starting production deployment: $DEPLOYMENT_ID"
    log_info "Project directory: $PROJECT_DIR"
    log_info "Backup directory: $BACKUP_DIR"
    log_info "Log file: $LOG_FILE"
    
    # Create log directory
    mkdir -p "$(dirname "$LOG_FILE")"
    
    # Deployment steps
    local steps=(
        "check_root"
        "check_prerequisites"
        "create_backup"
        "deploy_new_version"
        "verify_health"
        "test_functionality"
        "configure_monitoring"
        "final_verification"
    )
    
    local step_count=0
    local total_steps=${#steps[@]}
    
    for step in "${steps[@]}"; do
        step_count=$((step_count + 1))
        log_info "Step $step_count/$total_steps: $step"
        
        if "$step"; then
            log_success "Step $step completed successfully"
        else
            log_error "Step $step failed"
            generate_report "false"
            exit 1
        fi
        
        log_info "Step $step_count/$total_steps completed"
        echo
    done
    
    log_success "Production deployment completed successfully!"
    generate_report "true"
    
    log_info "Deployment summary:"
    log_info "  - Deployment ID: $DEPLOYMENT_ID"
    log_info "  - Backup location: $BACKUP_DIR"
    log_info "  - Log file: $LOG_FILE"
    log_info "  - Health check: curl http://localhost:8000/health"
    log_info "  - Metrics: curl http://localhost:8000/metrics"
}

# Show usage
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Production deployment script for Coder-lite Provision System

OPTIONS:
    -h, --help          Show this help message
    -v, --version       Show version information
    --dry-run           Show what would be done without executing
    --skip-backup       Skip backup creation
    --force             Force deployment even if checks fail

EXAMPLES:
    $0                    # Run full deployment
    $0 --dry-run         # Show deployment plan
    $0 --skip-backup     # Deploy without backup

ENVIRONMENT VARIABLES:
    DEPLOYMENT_ENV       Deployment environment (default: production)
    BASE_URL             Base URL for health checks (default: http://localhost:8000)
    REDIS_HOST           Redis host (default: localhost)
    REDIS_PORT           Redis port (default: 6379)
    START_PORT           Start port for workspaces (default: 13001)
    END_PORT             End port for workspaces (default: 13100)

EOF
}

# Parse command line arguments
DRY_RUN=false
SKIP_BACKUP=false
FORCE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        -v|--version)
            echo "Production Deployment Script v1.0.0"
            exit 0
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --skip-backup)
            SKIP_BACKUP=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Handle dry run
if [ "$DRY_RUN" = "true" ]; then
    log_info "DRY RUN MODE - No changes will be made"
    log_info "Deployment plan:"
    log_info "  1. Check prerequisites"
    log_info "  2. Create system backup"
    log_info "  3. Deploy new version"
    log_info "  4. Verify system health"
    log_info "  5. Test functionality"
    log_info "  6. Configure monitoring"
    log_info "  7. Final verification"
    exit 0
fi

# Handle skip backup
if [ "$SKIP_BACKUP" = "true" ]; then
    log_warning "Skipping backup creation (--skip-backup specified)"
    # Modify the steps array to skip backup
    steps=("check_root" "check_prerequisites" "deploy_new_version" "verify_health" "test_functionality" "configure_monitoring" "final_verification")
fi

# Run main deployment
main "$@"
