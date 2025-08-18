#!/usr/bin/env bash
# Quick Start Script for VSCode Hosting Provider
# This script helps you choose and deploy your preferred setup

set -Eeuo pipefail

echo "🚀 VSCode Hosting Provider - Quick Start"
echo "========================================"
echo ""

# Check prerequisites
echo "📋 Checking prerequisites..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first:"
    echo "   curl -fsSL https://get.docker.com | sh"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Prerequisites met"
echo ""

# Choose deployment option
echo "Choose your deployment option:"
echo "1) MVP (Simple, <10 users) - Fastest to deploy"
echo "2) Provider-Grade (Recommended) - Full-featured with Coder"
echo "3) Terraform Template - For advanced users"
echo ""

read -p "Enter your choice (1-3): " choice

case $choice in
    1)
        echo ""
        echo "🚀 Deploying MVP setup..."
        cd vscode-hosting-mvp
        
        echo "📝 Generating password hash..."
        echo "Please enter a password for basic auth:"
        read -s password
        hash=$(docker run --rm caddy caddy hash-password --plaintext "$password")
        
        echo "🔧 Updating Caddyfile..."
        sed -i "s/REPLACE_WITH_HASHED_PASSWORD/$hash/g" Caddyfile
        
        echo "🐳 Starting services..."
        docker-compose up -d
        
        echo ""
        echo "✅ MVP setup deployed!"
        echo "🌐 Access your workspaces at:"
        echo "   - Alice: https://alice.dev.fisamy.work"
        echo "   - Bob: https://bob.dev.fisamy.work"
        echo "   - Health: https://health.dev.fisamy.work"
        echo ""
        echo "📚 Next steps:"
        echo "   1. Update DNS records for dev.fisamy.work and *.dev.fisamy.work"
        echo "   2. Customize the Caddyfile for your domain"
        echo "   3. Add more users by duplicating services"
        ;;
        
    2)
        echo ""
        echo "🚀 Deploying Provider-Grade setup..."
        cd coder-provider
        
        if [[ ! -f .env ]]; then
            echo "📝 Creating environment file..."
            cp env.example .env
            echo "⚠️  Please edit .env file with your actual values before continuing"
            echo "   Press Enter when ready..."
            read
        fi
        
        echo "🔧 Loading environment variables..."
        source .env
        
        echo "🐳 Starting services..."
        docker-compose up -d
        
        echo ""
        echo "✅ Provider-Grade setup deployed!"
        echo "🌐 Access Coder at: https://dev.fisamy.work"
        echo ""
        echo "📚 Next steps:"
        echo "   1. Create admin user:"
        echo "      docker exec -it coder-server coder users create --email admin@fisamy.work --username admin --password 'YourPassword' --site-admin"
        echo "   2. Update DNS records for dev.fisamy.work and *.dev.fisamy.work"
        echo "   3. Configure SSO in Coder admin panel"
        echo "   4. Create your first workspace template"
        ;;
        
    3)
        echo ""
        echo "🚀 Setting up Terraform template..."
        cd openvscode-template
        
        echo "🔧 Initializing Terraform..."
        ./init.sh
        
        echo ""
        echo "✅ Terraform initialized!"
        echo "📚 Next steps:"
        echo "   1. Customize main.tf for your needs"
        echo "   2. Run: terraform plan"
        echo "   3. Run: terraform apply"
        echo "   4. Or use: coder templates push vscode-ai"
        ;;
        
    *)
        echo "❌ Invalid choice. Please run the script again."
        exit 1
        ;;
esac

echo ""
echo "🎉 Setup complete! Check the README files for detailed documentation."
echo "📖 For help: https://github.com/your-repo/issues"
