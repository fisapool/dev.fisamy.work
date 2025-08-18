#!/usr/bin/env bash
# Custom Domains Deployment Script for VSCode Hosting Provider

set -Eeuo pipefail

echo "🌐 Custom Domains Deployment Script"
echo "==================================="
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

# Check if environment file exists
if [[ ! -f ".env" ]]; then
    echo "📝 Environment file not found. Creating from template..."
    if [[ -f "env.custom-domains" ]]; then
        cp env.custom-domains .env
        echo "⚠️  Please edit .env file with your actual values before continuing"
        echo "   Press Enter when ready..."
        read
    else
        echo "❌ Environment template not found. Please create .env file manually."
        exit 1
    fi
fi

# Load environment variables
echo "🔧 Loading environment variables..."
source .env

# Check required environment variables
if [[ -z "${CODER_PG_PASSWORD:-}" ]]; then
    echo "❌ CODER_PG_PASSWORD is not set in .env file"
    exit 1
fi

if [[ -z "${CODER_ACCESS_URL:-}" ]]; then
    echo "❌ CODER_ACCESS_URL is not set in .env file"
    exit 1
fi

echo "✅ Environment variables loaded"
echo ""

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p custom-domains
mkdir -p domain-manager/logs

# Install domain manager dependencies
echo "📦 Installing domain manager dependencies..."
cd domain-manager
if [[ ! -d "node_modules" ]]; then
    npm install
fi
cd ..

echo "✅ Dependencies installed"
echo ""

# Run database migrations
echo "🗄️  Running database migrations..."
echo "   This will create the custom_domains table and related schemas"
echo "   Press Enter to continue..."
read

# Check if PostgreSQL is running
if ! docker ps | grep -q "coder-postgres"; then
    echo "🐳 Starting PostgreSQL container for migration..."
    docker-compose -f docker-compose.custom-domains.yml up -d postgres
    echo "⏳ Waiting for PostgreSQL to be ready..."
    sleep 10
fi

# Run migration
echo "🔧 Running database migration..."
docker exec coder-postgres psql -U coder -d coder -c "
-- Custom domains table
CREATE TABLE IF NOT EXISTS custom_domains (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    domain VARCHAR(255) UNIQUE NOT NULL,
    verification_token VARCHAR(255) NOT NULL,
    verification_method VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    ssl_status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'
);

-- Domain verification records
CREATE TABLE IF NOT EXISTS domain_verifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain_id UUID REFERENCES custom_domains(id) ON DELETE CASCADE,
    verification_type VARCHAR(50) NOT NULL,
    verification_data TEXT NOT NULL,
    verified_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Domain health monitoring
CREATE TABLE IF NOT EXISTS domain_health (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain_id UUID REFERENCES custom_domains(id) ON DELETE CASCADE,
    status_code INTEGER,
    response_time_ms INTEGER,
    ssl_valid BOOLEAN,
    checked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_custom_domains_user_id ON custom_domains(user_id);
CREATE INDEX IF NOT EXISTS idx_custom_domains_workspace_id ON custom_domains(workspace_id);
CREATE INDEX IF NOT EXISTS idx_custom_domains_status ON custom_domains(status);
CREATE INDEX IF NOT EXISTS idx_custom_domains_domain ON custom_domains(domain);
"

echo "✅ Database migration completed"
echo ""

# Start all services
echo "🚀 Starting all services..."
docker-compose -f docker-compose.custom-domains.yml up -d

echo "⏳ Waiting for services to be ready..."
sleep 15

# Check service health
echo "🔍 Checking service health..."
if curl -s http://localhost:3000/healthz > /dev/null; then
    echo "✅ Coder is running at: ${CODER_ACCESS_URL}"
else
    echo "⚠️  Coder might still be starting up..."
fi

if curl -s http://localhost:3001/health > /dev/null; then
    echo "✅ Domain Manager is running at: http://localhost:3001"
else
    echo "⚠️  Domain Manager might still be starting up..."
fi

echo ""
echo "🎉 Custom Domains deployment completed!"
echo ""
echo "📱 Access Points:"
echo "   - Coder UI: ${CODER_ACCESS_URL}"
echo "   - Domain Manager API: http://localhost:3001"
echo "   - Domain Manager Health: http://localhost:3001/health"
echo ""
echo "🔧 Next Steps:"
echo "   1. Create your first admin user in Coder"
echo "   2. Get a Coder API token for domain management"
echo "   3. Update .env with your CODER_API_TOKEN"
echo "   4. Test domain creation and verification"
echo ""
echo "📚 API Endpoints:"
echo "   - POST /api/domains - Create a new custom domain"
echo "   - POST /api/domains/:id/verify - Verify a domain"
echo "   - GET /api/domains - List domains"
echo "   - DELETE /api/domains/:id - Delete a domain"
echo ""
echo "📖 For help: Check the README files or open an issue"
