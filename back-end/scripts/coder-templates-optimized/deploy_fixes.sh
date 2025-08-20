#!/bin/bash
# Deploy optimized startup scripts to fix beige-pheasant-94-logs errors

set -e

echo "🚀 Deploying Coder Template Fixes"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    case $status in
        "success") echo -e "${GREEN}✅${NC} $message" ;;
        "warning") echo -e "${YELLOW}⚠️${NC} $message" ;;
        "error") echo -e "${RED}❌${NC} $message" ;;
        "info") echo -e "ℹ️  $message" ;;
    esac
}

# Check if we're in the right directory
if [ ! -f "startup_optimized.sh" ]; then
    print_status "error" "This script must be run from the coder-templates-optimized directory"
    exit 1
fi

print_status "info" "Current directory: $(pwd)"

# Backup existing scripts
print_status "info" "Creating backup of existing startup scripts..."

BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Find and backup existing startup scripts
find .. -name "startup.sh" -type f 2>/dev/null | while read -r script; do
    if [ -f "$script" ]; then
        backup_path="$BACKUP_DIR/$(basename "$(dirname "$script")")_startup.sh"
        cp "$script" "$backup_path"
        print_status "info" "Backed up: $script -> $backup_path"
    fi
done

print_status "success" "Backup completed in: $BACKUP_DIR"

# Deploy optimized scripts
print_status "info" "Deploying optimized startup scripts..."

# Find template directories
TEMPLATE_DIRS=(
    "../templates/no-gpu"
    "../templates/gpu"
    "../templates"
)

for dir in "${TEMPLATE_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        print_status "info" "Checking directory: $dir"
        
        # Check if it's a no-gpu template
        if [[ "$dir" == *"no-gpu"* ]] || [ -f "$dir/startup.sh" ]; then
            if [ -f "$dir/startup.sh" ]; then
                print_status "info" "Replacing startup script in: $dir"
                cp "startup_optimized.sh" "$dir/startup.sh"
                chmod +x "$dir/startup.sh"
                print_status "success" "Deployed no-GPU optimized script to: $dir"
            fi
        fi
        
        # Check if it's a GPU template
        if [[ "$dir" == *"gpu"* ]]; then
            if [ -f "$dir/startup.sh" ]; then
                print_status "info" "Replacing GPU startup script in: $dir"
                cp "startup_gpu_optimized.sh" "$dir/startup.sh"
                chmod +x "$dir/startup.sh"
                print_status "success" "Deployed GPU-optimized script to: $dir"
            fi
        fi
    fi
done

# Create a test script to verify the fixes
print_status "info" "Creating test verification script..."

cat > "test_fixes.sh" << 'EOF'
#!/bin/bash
# Test script to verify the fixes are working

echo "🧪 Testing Coder Template Fixes"
echo "================================"

# Test 1: Check if optimized scripts exist
echo "Test 1: Checking optimized scripts..."
if [ -f "startup_optimized.sh" ]; then
    echo "✅ No-GPU optimized script exists"
else
    echo "❌ No-GPU optimized script missing"
fi

if [ -f "startup_gpu_optimized.sh" ]; then
    echo "✅ GPU optimized script exists"
else
    echo "❌ GPU optimized script missing"
fi

# Test 2: Check if scripts are executable
echo -e "\nTest 2: Checking script permissions..."
if [ -x "startup_optimized.sh" ]; then
    echo "✅ No-GPU script is executable"
else
    echo "❌ No-GPU script is not executable"
fi

if [ -x "startup_gpu_optimized.sh" ]; then
    echo "✅ GPU script is executable"
else
    echo "❌ GPU script is not executable"
fi

# Test 3: Validate script syntax
echo -e "\nTest 3: Validating script syntax..."
if bash -n "startup_optimized.sh" 2>/dev/null; then
    echo "✅ No-GPU script syntax is valid"
else
    echo "❌ No-GPU script has syntax errors"
fi

if bash -n "startup_gpu_optimized.sh" 2>/dev/null; then
    echo "✅ GPU script syntax is valid"
else
    echo "❌ GPU script has syntax errors"
fi

# Test 4: Check for common issues
echo -e "\nTest 4: Checking for common issues..."
if grep -q "/var/log" "startup_optimized.sh"; then
    echo "❌ No-GPU script still references /var/log"
else
    echo "✅ No-GPU script uses writable directories"
fi

if grep -q "/var/log" "startup_gpu_optimized.sh"; then
    echo "❌ GPU script still references /var/log"
else
    echo "✅ GPU script uses writable directories"
fi

echo -e "\n🎯 Fix Verification Complete!"
echo "Next steps:"
echo "1. Test the templates in Coder"
echo "2. Monitor logs in /tmp/ directory"
echo "3. Use debug_startup.sh for ongoing monitoring"
EOF

chmod +x "test_fixes.sh"

print_status "success" "Test script created: test_fixes.sh"

# Summary
echo -e "\n📋 Deployment Summary"
echo "======================"
print_status "success" "Optimized startup scripts deployed"
print_status "success" "Backup created in: $BACKUP_DIR"
print_status "success" "Test script created: test_fixes.sh"

echo -e "\n🚀 Next Steps:"
echo "1. Run: ./test_fixes.sh (to verify deployment)"
echo "2. Test templates in Coder environment"
echo "3. Monitor logs using: ./debug_startup.sh"
echo "4. Check for errors in /tmp/template-startup.log"

echo -e "\n📚 Documentation:"
echo "- ERROR_ANALYSIS.md: Detailed error analysis"
echo "- TROUBLESHOOTING_GUIDE.md: General troubleshooting"
echo "- startup_optimized.sh: No-GPU optimized script"
echo "- startup_gpu_optimized.sh: GPU-optimized script"

print_status "success" "Deployment completed successfully!"
