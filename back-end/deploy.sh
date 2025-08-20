#!/bin/bash

# Fisamy Dashboard - Same-Origin Deployment Script
# This script builds the frontend SPA and deploys both BFF and SPA

set -e

echo "🚀 Starting Fisamy Dashboard deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
FRONTEND_DIR="../frontend"
BUILD_DIR="/var/www/dashboard"
CADDY_CONFIG="/etc/caddy/Caddyfile"
BFF_SERVICE="fisamy-bff"

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

# Check if running as root (needed for /var/www and /etc/caddy)
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root (sudo)"
   exit 1
fi

# Step 1: Build the frontend SPA
print_status "Building frontend SPA..."
cd "$FRONTEND_DIR"

if [ ! -f "package.json" ]; then
    print_error "Frontend directory not found or invalid. Expected: $FRONTEND_DIR"
    exit 1
fi

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    print_status "Installing frontend dependencies..."
    npm install
fi

# Build the SPA
print_status "Building production SPA..."
npm run build

if [ ! -d "dist" ]; then
    print_error "Build failed - dist directory not created"
    exit 1
fi

print_status "Frontend build completed successfully"

# Step 2: Deploy the SPA to /var/www/dashboard
print_status "Deploying SPA to $BUILD_DIR..."

# Create directory if it doesn't exist
mkdir -p "$BUILD_DIR"

# Clean existing files
rm -rf "$BUILD_DIR"/*

# Copy built files
cp -r dist/* "$BUILD_DIR/"

# Set proper permissions
chown -R www-data:www-data "$BUILD_DIR"
chmod -R 755 "$BUILD_DIR"

print_status "SPA deployed to $BUILD_DIR"

# Step 3: Deploy the BFF
print_status "Deploying BFF service..."

# Build and start the BFF container
cd - > /dev/null  # Return to back-end directory

# Stop existing container if running
docker-compose down 2>/dev/null || true

# Build and start
docker-compose up -d --build

# Wait for BFF to be healthy
print_status "Waiting for BFF to be healthy..."
timeout=60
counter=0
while [ $counter -lt $timeout ]; do
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        print_status "BFF is healthy and responding"
        break
    fi
    sleep 2
    counter=$((counter + 2))
done

if [ $counter -ge $timeout ]; then
    print_warning "BFF health check timeout - continuing anyway"
fi

# Step 4: Deploy Caddy configuration
print_status "Deploying Caddy configuration..."

# Copy Caddyfile to system location
cp Caddyfile "$CADDY_CONFIG"

# Test Caddy configuration
if caddy validate --config "$CADDY_CONFIG"; then
    print_status "Caddy configuration is valid"
else
    print_error "Caddy configuration is invalid"
    exit 1
fi

# Reload Caddy
print_status "Reloading Caddy..."
if systemctl is-active --quiet caddy; then
    systemctl reload caddy
    print_status "Caddy reloaded successfully"
else
    print_warning "Caddy service not running. Starting it..."
    systemctl start caddy
    systemctl enable caddy
fi

# Step 5: Verify deployment
print_status "Verifying deployment..."

# Wait a moment for everything to settle
sleep 3

# Test endpoints
echo "Testing endpoints:"

# Test SPA
if curl -s -o /dev/null -w "%{http_code}" https://dev.fisamy.work/ | grep -q "200"; then
    print_status "✅ SPA is accessible"
else
    print_warning "⚠️  SPA may not be accessible yet"
fi

# Test BFF health
if curl -s -o /dev/null -w "%{http_code}" https://dev.fisamy.work/health | grep -q "200"; then
    print_status "✅ BFF health endpoint is accessible"
else
    print_warning "⚠️  BFF health endpoint may not be accessible yet"
fi

# Test BFF API endpoint
if curl -s -o /dev/null -w "%{http_code}" https://dev.fisamy.work/me | grep -q "200\|401\|403"; then
    print_status "✅ BFF API endpoint is accessible"
else
    print_warning "⚠️  BFF API endpoint may not be accessible yet"
fi

print_status "🎉 Deployment completed successfully!"
print_status "Your dashboard is now available at: https://dev.fisamy.work"
print_status "BFF API endpoints are accessible at: https://dev.fisamy.work/me, /usage, /workspaces, etc."

# Show running services
echo ""
print_status "Service status:"
docker-compose ps
systemctl status caddy --no-pager -l
