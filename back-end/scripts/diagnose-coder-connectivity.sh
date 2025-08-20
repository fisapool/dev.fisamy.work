#!/bin/bash

# Coder Connectivity Diagnostic Script
# Run this from the host to diagnose container-to-Coder connectivity issues

set -e

echo "🔍 Coder Connectivity Diagnostic Script"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${GREEN}[INFO]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARN]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }
print_header() { echo -e "${BLUE}[HEADER]${NC} $1"; }

# Configuration
CODER_HOST="coder.fisamy.work"
CODER_PORT="443"
BFF_CONTAINER="back-end_bff_1"

print_header "1. Host Network Connectivity Tests"
echo "----------------------------------------"

# Test host connectivity to Coder
print_status "Testing host connectivity to $CODER_HOST..."
if curl -s -o /dev/null -w "%{http_code}" "https://$CODER_HOST" | grep -q "200\|401\|403"; then
    print_status "✅ Host can reach Coder successfully"
else
    print_error "❌ Host cannot reach Coder"
fi

# Test DNS resolution
print_status "Testing DNS resolution..."
CODER_IP=$(dig +short "$CODER_HOST" A | head -1)
if [ -n "$CODER_IP" ]; then
    print_status "✅ DNS resolution successful: $CODER_HOST → $CODER_IP"
else
    print_error "❌ DNS resolution failed for $CODER_HOST"
fi

# Test port connectivity
print_status "Testing port connectivity to $CODER_IP:$CODER_PORT..."
if nc -z "$CODER_IP" "$CODER_PORT" 2>/dev/null; then
    print_status "✅ Port $CODER_PORT is reachable on $CODER_IP"
else
    print_error "❌ Port $CODER_PORT is not reachable on $CODER_IP"
fi

print_header "2. Docker Network Configuration"
echo "-----------------------------------"

# Check Docker network configuration
print_status "Current Docker networks:"
docker network ls

# Check BFF container network
if docker ps | grep -q "$BFF_CONTAINER"; then
    print_status "BFF container network info:"
    docker inspect "$BFF_CONTAINER" | jq -r '.[0].NetworkSettings.Networks | to_entries[] | "\(.key): \(.value.IPAddress)"'
else
    print_warning "BFF container not running"
fi

print_header "3. Container Network Tests"
echo "--------------------------------"

# Test container connectivity to Coder
if docker ps | grep -q "$BFF_CONTAINER"; then
    print_status "Testing container DNS resolution..."
    if docker exec "$BFF_CONTAINER" nslookup "$CODER_HOST" >/dev/null 2>&1; then
        print_status "✅ Container can resolve $CODER_HOST"
    else
        print_error "❌ Container cannot resolve $CODER_HOST"
    fi
    
    print_status "Testing container connectivity to Coder..."
    if docker exec "$BFF_CONTAINER" curl -s -o /dev/null -w "%{http_code}" "https://$CODER_HOST" | grep -q "200\|401\|403"; then
        print_status "✅ Container can reach Coder successfully"
    else
        print_error "❌ Container cannot reach Coder"
    fi
    
    print_status "Testing container outbound HTTPS..."
    if docker exec "$BFF_CONTAINER" curl -s -o /dev/null -w "%{http_code}" "https://httpbin.org/get" | grep -q "200"; then
        print_status "✅ Container can make outbound HTTPS requests"
    else
        print_error "❌ Container cannot make outbound HTTPS requests"
    fi
else
    print_warning "BFF container not running - starting it for testing..."
    cd back-end && docker-compose up -d
    sleep 10
    # Re-run the container tests
fi

print_header "4. Firewall and Network Policies"
echo "--------------------------------------"

# Check iptables rules
print_status "Checking iptables rules..."
if command -v iptables >/dev/null 2>&1; then
    print_status "OUTPUT chain rules:"
    iptables -L OUTPUT -n --line-numbers | head -20
else
    print_warning "iptables not available"
fi

# Check Docker daemon configuration
print_status "Docker daemon configuration:"
if [ -f /etc/docker/daemon.json ]; then
    cat /etc/docker/daemon.json
else
    print_warning "No custom Docker daemon configuration found"
fi

print_header "5. SSL/TLS Certificate Validation"
echo "----------------------------------------"

# Test SSL certificate from host
print_status "Testing SSL certificate from host..."
if command -v openssl >/dev/null 2>&1; then
    echo | openssl s_client -connect "$CODER_HOST:$CODER_PORT" -servername "$CODER_HOST" 2>/dev/null | openssl x509 -noout -subject -issuer -dates
else
    print_warning "openssl not available"
fi

# Test SSL certificate from container
if docker ps | grep -q "$BFF_CONTAINER"; then
    print_status "Testing SSL certificate from container..."
    if docker exec "$BFF_CONTAINER" command -v openssl >/dev/null 2>&1; then
        docker exec "$BFF_CONTAINER" bash -c "echo | openssl s_client -connect $CODER_HOST:$CODER_PORT -servername $CODER_HOST 2>/dev/null | openssl x509 -noout -subject -issuer -dates"
    else
        print_warning "openssl not available in container"
    fi
fi

print_header "6. Environment Variables Check"
echo "-----------------------------------"

# Check environment variables
print_status "Checking Coder environment variables..."
if [ -f /etc/fisamy/coder.env ]; then
    print_status "Coder environment file exists:"
    grep -E "CODER_(HOST|URL|API_TOKEN)" /etc/fisamy/coder.env | sed 's/=.*/=***/'
else
    print_error "❌ Coder environment file not found at /etc/fisamy/coder.env"
fi

print_header "7. Recommended Fixes"
echo "---------------------------"

echo "Based on the diagnostics above, here are the likely fixes:"
echo ""
echo "1. If DNS resolution fails in container:"
echo "   - Add DNS servers to Docker daemon configuration"
echo "   - Use --dns flag when running containers"
echo ""
echo "2. If outbound HTTPS is blocked:"
echo "   - Check iptables OUTPUT chain rules"
echo "   - Verify Docker network allows outbound connections"
echo ""
echo "3. If SSL certificate validation fails:"
echo "   - Ensure container has proper CA certificates"
echo "   - Check certificate chain and trust"
echo ""
echo "4. If network isolation is the issue:"
echo "   - Use host networking: --network host"
echo "   - Or configure proper bridge networking"

echo ""
print_status "Diagnostic script completed. Review the output above for issues."
