# 🌐 Custom Domains for VSCode Hosting Provider

This guide covers the implementation and usage of custom domains for your VSCode hosting provider, allowing customers to use their own domains for their workspaces.

## 🎯 **Overview**

The custom domains feature enables:
- **Multi-tenant domain support** - Customers can use their own domains
- **Automatic SSL certificates** - Let's Encrypt integration via Caddy
- **Domain verification** - Multiple verification methods (DNS, HTTP, File)
- **Health monitoring** - Continuous domain status checking
- **Dynamic routing** - Automatic Caddy configuration generation

## 🏗️ **Architecture**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Custom Domain │    │  Domain Manager  │    │     Caddy      │
│   (e.g.,       │───▶│     Service      │───▶│   (Reverse     │
│   dev.company.  │    │   (Node.js)      │    │    Proxy)      │
│   com)          │    │                  │    │                │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │   PostgreSQL     │    │      Coder      │
                       │   (Database)     │    │   (Workspace    │
                       │                  │    │   Manager)      │
                       └──────────────────┘    └─────────────────┘
```

## 🚀 **Quick Start**

### **1. Deploy the System**

```bash
# Clone and navigate to backend directory
cd backend

# Make deployment script executable
chmod +x deploy-custom-domains.sh

# Run deployment
./deploy-custom-domains.sh
```

### **2. Configure Environment**

```bash
# Copy environment template
cp env.custom-domains .env

# Edit with your values
nano .env
```

Required variables:
- `CODER_PG_PASSWORD` - Database password
- `CODER_ACCESS_URL` - Your main Coder URL
- `CODER_API_TOKEN` - Coder API token (get from admin panel)

### **3. Create Admin User**

```bash
# Create admin user in Coder
docker exec -it coder coder users create \
  --email admin@yourdomain.com \
  --username admin \
  --password 'YourSecurePassword' \
  --site-admin
```

### **4. Get API Token**

1. Log into Coder admin panel
2. Go to **User Settings** → **Tokens**
3. Create a new token with appropriate permissions
4. Add to your `.env` file as `CODER_API_TOKEN`

## 📖 **API Reference**

### **Domain Management Endpoints**

#### **Create Domain**
```http
POST /api/domains
Content-Type: application/json

{
  "domain": "dev.company.com",
  "workspaceId": "uuid-here",
  "userId": "uuid-here",
  "verificationMethod": "dns"
}
```

**Response:**
```json
{
  "id": "uuid-here",
  "domain": "dev.company.com",
  "status": "pending",
  "verification_method": "dns",
  "verification_data": "TXT record: dev.company.com -> \"verification-token-here\""
}
```

#### **Verify Domain**
```http
POST /api/domains/{id}/verify
```

**Response:**
```json
{
  "message": "Domain verified successfully",
  "status": "verified"
}
```

#### **List Domains**
```http
GET /api/domains?userId={uuid}&workspaceId={uuid}&status={status}
```

#### **Delete Domain**
```http
DELETE /api/domains/{id}
```

### **Health Check**
```http
GET /health
```

## 🔍 **Domain Verification Methods**

### **1. DNS Verification (Recommended)**

Add a TXT record to your domain:
```
Type: TXT
Name: dev.company.com
Value: "verification-token-here"
```

### **2. HTTP Verification**

Create a file at `http://dev.company.com/.well-known/domain-verification` containing the verification token.

### **3. File Verification**

Create a file at `http://dev.company.com/.well-known/domain-verification.txt` containing the verification token.

## 🛠️ **Usage Examples**

### **Example 1: Add Custom Domain via API**

```bash
# Create a new custom domain
curl -X POST http://localhost:3001/api/domains \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "dev.mycompany.com",
    "workspaceId": "your-workspace-uuid",
    "userId": "your-user-uuid",
    "verificationMethod": "dns"
  }'

# Verify the domain (after adding DNS record)
curl -X POST http://localhost:3001/api/domains/{domain-id}/verify
```

### **Example 2: Check Domain Status**

```bash
# List all domains for a user
curl "http://localhost:3001/api/domains?userId=your-user-uuid"

# Check domain health
curl http://localhost:3001/health
```

### **Example 3: Remove Domain**

```bash
# Delete a domain
curl -X DELETE http://localhost:3001/api/domains/{domain-id}
```

## 🔧 **Configuration Options**

### **Environment Variables**

| Variable | Default | Description |
|----------|---------|-------------|
| `CODER_PG_PASSWORD` | Required | Database password |
| `CODER_ACCESS_URL` | Required | Main Coder URL |
| `CODER_API_TOKEN` | Required | Coder API token |
| `DOMAIN_MANAGER_PORT` | 3001 | Domain manager port |
| `MAX_DOMAINS_PER_USER` | 10 | Max domains per user |
| `MAX_DOMAINS_PER_WORKSPACE` | 5 | Max domains per workspace |
| `HEALTH_CHECK_INTERVAL` | 5 | Health check interval (minutes) |

### **Caddy Configuration**

The system automatically generates Caddy configurations for each verified domain:

```caddyfile
dev.company.com {
  encode zstd gzip
  
  header {
    Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
    X-Content-Type-Options "nosniff"
    X-Frame-Options "DENY"
    X-XSS-Protection "1; mode=block"
    Referrer-Policy "strict-origin-when-cross-origin"
  }

  reverse_proxy coder:3000 {
    header_up Host {host}
    header_up X-Workspace-ID workspace-uuid
    flush_interval -1
  }
}
```

## 📊 **Monitoring & Health Checks**

### **Automatic Health Monitoring**

The system runs health checks every 5 minutes for all verified domains:

- **Response time** monitoring
- **Status code** checking
- **SSL certificate** validation
- **Database logging** of all results

### **Health Check Data**

Health data is stored in the `domain_health` table with:
- Response time in milliseconds
- HTTP status codes
- SSL validity status
- Timestamp of each check

## 🔒 **Security Features**

### **Domain Validation**
- Strict domain format validation
- Prevention of duplicate domains
- User and workspace ownership verification

### **SSL/TLS**
- Automatic Let's Encrypt certificate generation
- HSTS headers for all domains
- Secure reverse proxy configuration

### **Access Control**
- User-based domain ownership
- Workspace-scoped domain access
- API token authentication

## 🚨 **Troubleshooting**

### **Common Issues**

#### **1. Domain Verification Fails**

**DNS Verification:**
- Ensure TXT record is properly set
- Wait for DNS propagation (can take up to 24 hours)
- Check for typos in the verification token

**HTTP/File Verification:**
- Verify the file path is accessible
- Check file content matches exactly
- Ensure no extra whitespace or characters

#### **2. SSL Certificate Issues**

- Verify DNS is pointing to your server
- Check firewall allows ports 80/443
- Ensure domain ownership is verified

#### **3. Domain Not Routing**

- Check Caddy configuration generation
- Verify domain status is "verified"
- Check Caddy logs for errors

### **Debug Commands**

```bash
# Check domain manager logs
docker logs domain-manager

# Check Caddy logs
docker logs caddy

# Check database connection
docker exec domain-manager node -e "
const { Pool } = require('pg');
const pool = new Pool({ connectionString: process.env.DATABASE_URL });
pool.query('SELECT 1').then(() => console.log('DB OK')).catch(console.error);
"

# Test domain verification manually
curl -v http://your-domain.com/.well-known/domain-verification
```

## 📈 **Scaling Considerations**

### **Performance**
- Database indexes for fast queries
- Connection pooling for database
- Asynchronous domain verification
- Cached Caddy configurations

### **Limits**
- Default: 10 domains per user
- Default: 5 domains per workspace
- Configurable via environment variables

### **High Availability**
- Container-based deployment
- Health check monitoring
- Automatic service restart
- Database persistence

## 🔄 **Updates & Maintenance**

### **Updating Domain Manager**

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.custom-domains.yml down
docker-compose -f docker-compose.custom-domains.yml up -d --build
```

### **Database Backups**

```bash
# Backup custom domains data
docker exec coder-postgres pg_dump -U coder -t custom_domains -t domain_verifications -t domain_health coder > custom_domains_backup.sql

# Restore if needed
docker exec -i coder-postgres psql -U coder -d coder < custom_domains_backup.sql
```

## 📞 **Support**

### **Getting Help**
1. Check this documentation
2. Review service logs
3. Verify configuration
4. Open an issue with details

### **Useful Commands**

```bash
# Service status
docker-compose -f docker-compose.custom-domains.yml ps

# Service logs
docker-compose -f docker-compose.custom-domains.yml logs -f

# Restart services
docker-compose -f docker-compose.custom-domains.yml restart

# Full reset
docker-compose -f docker-compose.custom-domains.yml down -v
./deploy-custom-domains.sh
```

---

**Next Steps:**
1. Deploy the system using the deployment script
2. Configure your environment variables
3. Test with a sample domain
4. Integrate with your frontend for domain management UI
5. Set up monitoring and alerts

For additional help or feature requests, please open an issue in the repository.
