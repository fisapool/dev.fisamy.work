#!/bin/bash
# Quick setup script for Coder templates

echo "🚀 Quick Coder Template Setup"
echo "============================="

# Check prerequisites
echo "Checking prerequisites..."
if [ -f "debug_startup.sh" ]; then
    echo "✅ Debug script found"
else
    echo "❌ Debug script not found"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "docker-distracted_lamport8/main.tf" ]; then
    echo "❌ Please run this script from the scripts directory"
    exit 1
fi

# Validate deployment
echo -e "\nValidating deployment..."
if [ -f "validate_deployment.sh" ]; then
    ./validate_deployment.sh
else
    echo "❌ Validation script not found"
    exit 1
fi

# Optimize performance
echo -e "\nOptimizing performance..."
if [ -f "optimize_templates.sh" ]; then
    ./optimize_templates.sh
else
    echo "❌ Optimization script not found"
    exit 1
fi

echo -e "\n✅ Setup completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Access Coder dashboard at: https://coder.fisamy.work"
echo "2. Create workspaces using the new templates"
echo "3. Monitor performance using the provided scripts"
echo "4. Check logs for any issues: tail -f /tmp/coder-startup-script.log"
echo ""
echo "🔧 Available debugging tools:"
echo "• ./debug_startup.sh - Comprehensive system check"
echo "• ./validate_deployment.sh - Deployment validation"
echo "• ./optimize_templates.sh - Performance optimization"
echo "• ./monitor_performance.sh - Real-time monitoring"
echo ""
echo "📚 Documentation:"
echo "• TROUBLESHOOTING_GUIDE.md - Complete troubleshooting guide"
echo "• README.md - Template setup instructions"
