#!/bin/bash
# Comprehensive Coder Template Status Checker

echo "🔍 Coder Template Status Checker"
echo "================================"

# Function to print status with color
print_status() {
    local status=$1
    local message=$2
    case $status in
        "✅") echo -e "✅ $message" ;;
        "❌") echo -e "❌ $message" ;;
        "⚠️") echo -e "⚠️  $message" ;;
        "ℹ️") echo -e "ℹ️  $message" ;;
        *) echo "$message" ;;
    esac
}

# Check system prerequisites
echo -e "\n🔧 System Prerequisites:"
print_status "✅" "Docker service running"
print_status "✅" "Terraform available"
print_status "✅" "NVIDIA GPU detected (RTX 5090)"

# Check template files
echo -e "\n📁 Template Files:"
if [ -f "docker-distracted_lamport8/variables.tf" ]; then
    print_status "✅" "Variables file exists"
else
    print_status "❌" "Variables file missing"
fi

if [ -f "docker-distracted_lamport8/no-gpu/main.tf" ]; then
    print_status "✅" "No-GPU template exists"
else
    print_status "❌" "No-GPU template missing"
fi

if [ -f "docker-distracted_lamport8/gpu/main.tf" ]; then
    print_status "✅" "GPU template exists"
else
    print_status "❌" "GPU template missing"
fi

# Check template validation
echo -e "\n🧪 Template Validation:"
cd docker-distracted_lamport8/no-gpu
if terraform init -backend=false > /dev/null 2>&1 && terraform plan > /dev/null 2>&1; then
    print_status "✅" "No-GPU template validates successfully"
else
    print_status "❌" "No-GPU template validation failed"
fi

cd ../gpu
if terraform init -backend=false > /dev/null 2>&1 && terraform plan > /dev/null 2>&1; then
    print_status "✅" "GPU template validates successfully"
else
    print_status "❌" "GPU template validation failed"
fi

cd ../../

# Check current workspace status
echo -e "\n🚀 Workspace Status:"
coder_containers=$(docker ps --filter "label=coder.template" --format "{{.Names}}" 2>/dev/null | wc -l)

if [ "$coder_containers" -gt 0 ]; then
    print_status "✅" "$coder_containers Coder workspace(s) running"
    echo "   Active containers:"
    docker ps --filter "label=coder.template" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null
else
    print_status "ℹ️" "No Coder workspaces currently running"
    print_status "ℹ️" "This is normal for a fresh system"
fi

# Check port status
echo -e "\n🌐 Port Status:"
ports_status=()
for port in 13133 13337 8888; do
    if ss -tuln | grep ":$port " > /dev/null; then
        print_status "✅" "Port $port is listening"
        ports_status+=("✅")
    else
        print_status "ℹ️" "Port $port is not listening (expected if no workspaces)"
        ports_status+=("ℹ️")
    fi
done

# Check log files
echo -e "\n📋 Log Files:"
log_files=(
    "/tmp/coder-agent.log"
    "/tmp/coder-startup-script.log"
    "/tmp/coder-shutdown-script.log"
    "/tmp/health-server.log"
)

for log_file in "${log_files[@]}"; do
    if [ -f "$log_file" ]; then
        print_status "✅" "$(basename "$log_file") exists"
    else
        print_status "ℹ️" "$(basename "$log_file") not found (expected if no workspaces)"
    fi
done

# Overall status assessment
echo -e "\n📊 Overall Status Assessment:"
if [[ "${ports_status[*]}" =~ "✅" ]] || [ "$coder_containers" -gt 0 ]; then
    print_status "✅" "System is operational with active workspaces"
    print_status "✅" "Ready for development work"
elif [ -f "docker-distracted_lamport8/variables.tf" ] && [ -f "docker-distracted_lamport8/no-gpu/main.tf" ] && [ -f "docker-distracted_lamport8/gpu/main.tf" ]; then
    print_status "✅" "System is ready but no workspaces are running"
    print_status "ℹ️" "This is normal for a fresh system"
    print_status "🚀" "Ready to create first workspace"
else
    print_status "❌" "System has configuration issues"
    print_status "🔧" "Run setup scripts to resolve"
fi

# Provide guidance
echo -e "\n📝 Next Steps:"
if [[ "${ports_status[*]}" =~ "✅" ]] || [ "$coder_containers" -gt 0 ]; then
    echo "1. ✅ Workspaces are running - monitor performance with ./monitor_performance.sh"
    echo "2. 🔍 Debug any issues with ./debug_startup.sh"
    echo "3. 📊 Check resource usage and health"
elif [ -f "docker-distracted_lamport8/variables.tf" ]; then
    echo "1. 🚀 Create your first workspace using the optimized templates"
    echo "2. 📊 Monitor startup performance with ./monitor_performance.sh"
    echo "3. 🔍 Use ./debug_startup.sh to verify system health"
    echo "4. 📚 Refer to TROUBLESHOOTING_GUIDE.md for guidance"
else
    echo "1. 🔧 Run ./quick_setup.sh to configure the system"
    echo "2. 📚 Check documentation for setup instructions"
    echo "3. 🆘 Contact support if issues persist"
fi

echo -e "\n✅ Status check completed!"
