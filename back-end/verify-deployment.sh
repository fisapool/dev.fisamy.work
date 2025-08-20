#!/bin/bash

# Fisamy Dashboard - Deployment Verification Script
# Run this after deployment to verify everything is working

set -e

echo "🔍 Verifying Fisamy Dashboard deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DOMAIN="dev.fisamy.work"
BFF_LOCAL="http://localhost:8000"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Test local BFF
echo "=== Testing Local BFF ==="
if curl -f "$BFF_LOCAL/health" >/dev/null 2>&1; then
    print_success "Local BFF health endpoint: OK"
else
    print_error "Local BFF health endpoint: FAILED"
    exit 1
fi

# Test local BFF API endpoints
echo "=== Testing Local BFF API Endpoints ==="
endpoints=("/me" "/usage" "/workspaces" "/templates" "/domains")
for endpoint in "${endpoints[@]}"; do
    if curl -f "$BFF_LOCAL$endpoint" >/dev/null 2>&1; then
        print_success "Local BFF $endpoint: OK"
    else
        print_warning "Local BFF $endpoint: FAILED (may require auth)"
    fi
done

# Test public endpoints (if domain is accessible)
echo "=== Testing Public Endpoints ==="

# Test SPA
if curl -s -o /dev/null -w "%{http_code}" "https://$DOMAIN/" | grep -q "200"; then
    print_success "Public SPA: OK"
else
    print_warning "Public SPA: May not be accessible yet"
fi

# Test BFF health through Caddy
if curl -s -o /dev/null -w "%{http_code}" "https://$DOMAIN/health" | grep -q "200"; then
    print_success "Public BFF health: OK"
else
    print_warning "Public BFF health: May not be accessible yet"
fi

# Test BFF API through Caddy
if curl -s -o /dev/null -w "%{http_code}" "https://$DOMAIN/me" | grep -q "200\|401\|403"; then
    print_success "Public BFF API: OK"
else
    print_warning "Public BFF API: May not be accessible yet"
fi

# Check Caddy status
echo "=== Checking Caddy Status ==="
if systemctl is-active --quiet caddy; then
    print_success "Caddy service: Running"
else
    print_error "Caddy service: Not running"
fi

# Check Docker containers
echo "=== Checking Docker Containers ==="
if docker-compose ps | grep -q "Up"; then
    print_success "BFF container: Running"
    docker-compose ps
else
    print_error "BFF container: Not running"
fi

# Check file permissions
echo "=== Checking File Permissions ==="
if [ -d "/var/www/dashboard" ]; then
    if [ -r "/var/www/dashboard/index.html" ]; then
        print_success "SPA files: Accessible"
        ls -la /var/www/dashboard/ | head -5
    else
        print_error "SPA files: Not accessible"
    fi
else
    print_error "SPA directory: Not found"
fi

echo ""
print_status "🎉 Verification completed!"
print_status "If all tests pass, your deployment is working correctly."
print_status "Your dashboard should be available at: https://$DOMAIN"
