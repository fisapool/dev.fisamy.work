#!/bin/bash
# Test script for Coder templates

echo "🧪 Testing Coder Templates"
echo "=========================="

# Check if we're in the right directory
if [ ! -f "docker-distracted_lamport8/main.tf" ]; then
    echo "❌ Please run this script from the scripts directory"
    exit 1
fi

# Test no-GPU template
echo -e "\n🔧 Testing No-GPU Template..."
cd docker-distracted_lamport8/no-gpu

if terraform init -backend=false > /dev/null 2>&1; then
    echo "✅ No-GPU template initialized successfully"
    
    if terraform plan > /dev/null 2>&1; then
        echo "✅ No-GPU template plan successful"
    else
        echo "❌ No-GPU template plan failed"
        exit 1
    fi
else
    echo "❌ No-GPU template initialization failed"
    exit 1
fi

cd ../gpu

# Test GPU template
echo -e "\n🎮 Testing GPU Template..."
if terraform init -backend=false > /dev/null 2>&1; then
    echo "✅ GPU template initialized successfully"
    
    if terraform plan > /dev/null 2>&1; then
        echo "✅ GPU template plan successful"
    else
        echo "❌ GPU template plan failed"
        exit 1
    fi
else
    echo "❌ GPU template initialization failed"
    exit 1
fi

cd ../..

echo -e "\n✅ All templates tested successfully!"
echo ""
echo "📋 Template Status:"
echo "• No-GPU Template: ✅ Ready for deployment"
echo "• GPU Template: ✅ Ready for deployment"
echo ""
echo "🚀 Next steps:"
echo "1. Deploy templates to Coder instance"
echo "2. Create test workspaces"
echo "3. Monitor startup performance"
echo "4. Use debugging tools if issues arise"
