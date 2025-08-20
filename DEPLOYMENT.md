# VSCode Hosting Provider - Deployment Guide

This guide covers deploying both the frontend landing page and the backend VSCode hosting infrastructure.

## Prerequisites

- Ubuntu 22.04+ server with Docker installed
- Domain name (e.g., `dev.fisamy.work`) with DNS access
- Basic knowledge of Docker, Terraform, and Linux administration

## Quick Start (5 minutes)

### 1. DNS Setup

Create these A records pointing to your server IP:
- `dev.fisamy.work` → Your server IP
- `*.dev.fisamy.work` → Your server IP (wildcard for workspaces)

### 2. Frontend Deployment

```bash
# Clone and build
git clone <your-repo>
cd <your-repo>
npm install
npm run build

# Deploy to any static hosting (Vercel, Netlify, or your server)
# The dist/ folder contains the built application
```

### 3. Backend Infrastructure

```bash
cd back-end/openvscode-template

# Initialize Terraform
./init.sh

# Deploy template to Coder
coder templates push vscode-ai --directory back-end/openvscode-template
```

## Detailed Deployment

### Frontend Configuration

1. **Environment Setup**
   ```bash
   cp env.example .env.local
   # Edit .env.local with your actual values
   ```

2. **Build & Deploy**
   ```bash
   npm run build
   # Upload dist/ folder to your web server
   ```

### Backend Infrastructure

#### Option A: MVP (Simple, <10 users)

```bash
cd back-end/vscode-hosting-mvp

# Generate password hash
docker run --rm caddy caddy hash-password --plaintext 'YourPassword'

# Edit Caddyfile with your password hash
# Edit docker-compose.yml if needed

# Deploy
docker compose up -d
```

#### Option B: Provider-Grade (Recommended)

```bash
cd back-end/coder-provider

# Set environment variables
export CODER_PG_PASSWORD="$(openssl rand -base64 24 | tr -d '=+/')"
export CODER_ACCESS_URL="https://dev.fisamy.work"
export CODER_MAX_WORKSPACE_CPUS=6
export CODER_MAX_WORKSPACE_MEMORY=16Gi
export CODER_MAX_WORKSPACE_DISK=100Gi

# Deploy
docker compose up -d

# Create admin user
docker exec -it coder coder users create \
  --email admin@fisamy.work \
  --username admin \
  --password 'ChangeMe$trong' \
  --site-admin
```

### Terraform Template Deployment

```bash
cd back-end/openvscode-template

# Initialize
terraform init

# Plan deployment
terraform plan

# Apply
terraform apply

# Or use Coder CLI
coder templates push vscode-ai
```

## Monitoring & Maintenance

### Health Checks

```bash
# Check Coder health
curl https://dev.fisamy.work/healthz

# Check monitoring
./monitor_extras.sh --json
./monitor_extras.sh --prometheus
```

### Logs

```bash
# Coder logs
docker logs coder

# Caddy logs
docker logs caddy

# Monitor logs
./monitor_extras.sh --interval 60
```

### Backups

```bash
# PostgreSQL backup
docker exec coder pg_dump -U coder coder > backup_$(date +%Y%m%d).sql

# Volume snapshots
docker run --rm -v coder_data:/data -v $(pwd):/backup alpine tar czf /backup/coder_data_$(date +%Y%m%d).tar.gz /data
```

## Security Checklist

- [ ] Firewall: Only ports 80/443 open
- [ ] Strong admin password
- [ ] SSO configured (GitHub, Google, OIDC)
- [ ] Regular security updates
- [ ] Monitoring alerts configured
- [ ] Backup strategy implemented

## Troubleshooting

### Common Issues

1. **Caddy can't get Let's Encrypt cert**
   - Ensure DNS is pointing to your server
   - Check firewall allows ports 80/443
   - Verify domain ownership

2. **Workspaces won't start**
   - Check Docker daemon status
   - Verify resource limits in Coder
   - Check container logs

3. **Performance issues**
   - Monitor resource usage with `monitor_extras.sh`
   - Adjust workspace limits
   - Check host system resources

### Support

- **Documentation**: Check README files in each directory
- **Issues**: Open GitHub issue with logs and error details
- **Community**: Join Coder Discord for help

## Scaling

### Horizontal Scaling

- Use load balancer for multiple Coder instances
- Shared PostgreSQL database
- Redis for session management

### Vertical Scaling

- Increase host resources
- Adjust workspace limits
- Optimize container images

## Cost Optimization

- Enable idle auto-suspend
- Use spot instances for non-critical workloads
- Monitor and adjust resource allocation
- Implement usage quotas

## Next Steps

1. **Customize branding** in the frontend
2. **Set up Stripe integration** for billing
3. **Configure monitoring alerts** (Slack, email)
4. **Add custom workspace templates**
5. **Implement user onboarding flows**
6. **Set up CI/CD for template updates**

---

For additional help, check the README files in each directory or open an issue.
