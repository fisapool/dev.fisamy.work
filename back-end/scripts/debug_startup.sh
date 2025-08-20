#!/bin/bash
# Startup script debugging utility

set -e

echo "🔍 Coder Template Startup Script Debugger"
echo "========================================="

# Check if required tools are available
echo "Checking system requirements..."
for tool in curl wget busybox; do
    if command -v $tool &> /dev/null; then
        echo "✅ $tool is available"
    else
        echo "❌ $tool is missing"
    fi
done

# Test connectivity to Coder
echo -e "\n🌐 Testing Coder connectivity..."
CODER_URL="${CODER_HOST:-https://coder.fisamy.work}"
if curl -f -s "$CODER_URL/health" > /dev/null; then
    echo "✅ Coder access URL is reachable"
else
    echo "❌ Cannot reach Coder access URL"
fi

# Check log files
echo -e "\n📋 Checking log files..."
log_files=(
    "/tmp/coder-agent.log"
    "/tmp/coder-startup-script.log" 
    "/tmp/coder-shutdown-script.log"
    "/tmp/health-server.log"
)

for log_file in "${log_files[@]}"; do
    if [ -f "$log_file" ]; then
        echo "✅ $log_file exists"
        echo "   Last 10 lines:"
        tail -n 10 "$log_file" 2>/dev/null || echo "   (empty)"
    else
        echo "ℹ️  $log_file not found (expected if no workspaces running)"
    fi
done

# Check Docker socket
echo -e "\n🐳 Checking Docker socket..."
if [ -S "/var/run/docker.sock" ]; then
    echo "✅ Docker socket available"
else
    echo "❌ Docker socket not found"
fi

# Check GPU availability
echo -e "\n🎮 Checking GPU availability..."
if command -v nvidia-smi &> /dev/null; then
    echo "✅ NVIDIA GPU detected"
    nvidia-smi --query-gpu=name --format=csv,noheader,nounits | head -1
else
    echo "ℹ️  No NVIDIA GPU detected"
fi

# Check running containers
echo -e "\n📦 Checking running containers..."
if command -v docker &> /dev/null; then
    echo "Running Coder containers:"
    docker ps --filter "label=coder.template" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "   No containers found or Docker not accessible"
else
    echo "❌ Docker command not available"
fi

# Check system resources
echo -e "\n💾 Checking system resources..."
echo "CPU usage: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
echo "Memory usage: $(free -m | awk 'NR==2{printf "%.1f%%", $3*100/$2}')"
echo "Disk usage: $(df -h / | awk 'NR==2{print $5}')"

# Check network connectivity
echo -e "\n🌐 Checking network connectivity..."
ports_status=()
for port in 13133 13337 8888; do
    if ss -tuln | grep ":$port " > /dev/null; then
        echo "✅ Port $port is listening"
        ports_status+=("✅")
    else
        echo "ℹ️  Port $port is not listening (expected if no workspaces running)"
        ports_status+=("ℹ️")
    fi
done

# Provide guidance based on port status
if [[ "${ports_status[*]}" =~ "✅" ]]; then
    echo "✅ Some Coder services are running"
else
    echo "ℹ️  No Coder services currently running - this is normal for a fresh system"
    echo "   Start a workspace to see these ports become active"
fi

# Check Python environment
echo -e "\n🐍 Checking Python environment..."
if command -v python3 &> /dev/null; then
    echo "✅ Python3 is available"
    python3 --version
    if [ -d "/opt/venv" ]; then
        echo "✅ Virtual environment exists"
        source /opt/venv/bin/activate
        python3 -c "import torch; print(f'PyTorch version: {torch.__version__}')" 2>/dev/null || echo "❌ PyTorch not available"
    else
        echo "ℹ️  No virtual environment found"
    fi
else
    echo "❌ Python3 not available"
fi

echo -e "\n✅ Debug check completed"
echo -e "\n📝 Next steps:"
echo "1. Check startup script logs: tail -f /tmp/coder-startup-script.log"
echo "2. Check health server logs: tail -f /tmp/health-server.log"
echo "3. Verify container status: docker ps"
echo "4. Test health endpoint: curl http://localhost:13133"
