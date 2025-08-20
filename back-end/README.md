# Fisamy Dashboard BFF (Backend for Frontend)

A FastAPI-based backend service that provides a clean API for the Fisamy Dashboard frontend, integrating with Coder and Domain Manager services.

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Copy environment template
cp env.example .env

# Edit .env with your actual values
nano .env
```

Required environment variables:
- `CODER_API_TOKEN`: Your Coder API token
- `CODER_HOST`: Coder instance URL (default: https://coder.fisamy.work)
- `DOMAIN_MANAGER_TOKEN`: Domain Manager API token
- `DOMAIN_MANAGER_URL`: Domain Manager URL (default: https://domain-manager.fisamy.work)

### 4. Setup Coder Templates (Optional)

If you want to set up and validate Coder templates:

```bash
# Navigate to scripts directory
cd scripts

# Set environment variables
export CODER_API_TOKEN="your_coder_api_token_here"
export CODER_HOST="https://coder.fisamy.work"

# Run the setup script
./setup_coder_templates.sh
```

**Note**: The setup script must be run from the `back-end/scripts` directory, not from the `back-end` directory.

📖 **For detailed setup instructions, see**: [scripts/QUICK_SETUP.md](scripts/QUICK_SETUP.md)

### 2. Install Dependencies

```bash
# Using pip
pip install -r requirements.txt

# Or using Docker
docker-compose up -d
```

### 3. Run the Service

```bash
# Direct Python
python -m uvicorn bff_main:app --host 0.0.0.0 --port 8000 --reload

# Or using Docker
docker-compose up
```

## 🏗️ Architecture

```
Frontend (React) → BFF (FastAPI) → Coder API + Domain Manager
     ↓                    ↓                    ↓
  Dashboard         Clean API           Provider Services
  Components        Contract            (Tokens hidden)
```

## 📡 API Endpoints

The BFF implements the exact contract your dashboard expects:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/me` | User info and plan details |
| `GET` | `/usage` | Current resource usage |
| `GET` | `/workspaces` | List user workspaces |
| `POST` | `/workspaces` | Create new workspace |
| `POST` | `/workspaces/{id}/start` | Start workspace |
| `POST` | `/workspaces/{id}/stop` | Stop workspace |
| `DELETE` | `/workspaces/{id}` | Delete workspace |
| `GET` | `/templates` | Available templates |
| `GET` | `/domains` | Custom domains |
| `POST` | `/domains` | Create domain |
| `POST` | `/domains/{id}/verify` | Verify domain |

## 🔒 Security Features

- **CORS locked** to `dev.fisamy.work` and `localhost:3000`
- **Rate limiting** on workspace actions (10 requests/minute)
- **No token exposure** - all provider tokens stay server-side
- **Input validation** with Pydantic models
- **Security headers** in Caddy configuration

## 🐳 Docker Deployment

### Development
```bash
docker-compose up -d
```

### Production
```bash
# Make deploy script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

## 🌐 Caddy Configuration

The project now uses Caddy instead of Nginx for automatic HTTPS and reverse proxy functionality. The `Caddyfile` is already configured and will be deployed automatically by the deployment script.

## 🚨 **Troubleshooting**

### **Common Issues**

#### **Setup Script Fails with "Please run this script from the back-end/scripts directory"**
- **Problem**: Running the script from the wrong directory
- **Solution**: Always run from `back-end/scripts` directory:
  ```bash
  cd back-end/scripts
  export CODER_API_TOKEN="your_token_here"
  ./setup_coder_templates.sh
  ```

#### **CODER_API_TOKEN Environment Variable Not Set**
- **Problem**: Environment variables not loaded
- **Solution**: Set them manually or source the .env file:
  ```bash
  export CODER_API_TOKEN="your_token_here"
  export CODER_HOST="https://coder.fisamy.work"
  ```

#### **Python Dependencies Missing**
- **Problem**: Required packages not installed
- **Solution**: Install from requirements.txt:
  ```bash
  pip3 install -r requirements.txt
  ```

### Manual Caddy Setup (if needed)

If you need to manually configure Caddy:

```bash
# Copy the Caddyfile to the system location
sudo cp back-end/Caddyfile /etc/caddy/Caddyfile

# Test the configuration
sudo caddy validate --config /etc/caddy/Caddyfile

# Restart Caddy
sudo systemctl restart caddy

# Enable Caddy to start on boot
sudo systemctl enable caddy
```

## 🔧 Customization

### Adding Authentication

Replace the mock `get_current_user` function with your actual auth:

```python
async def get_current_user(request: Request):
    # Extract JWT from Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token")
    
    token = auth_header.split(" ")[1]
    # Verify JWT and return user data
    user = verify_jwt_token(token)
    return user
```

### Rate Limiting

The Caddy configuration includes essential security headers. For more sophisticated rate limiting, uncomment Redis in docker-compose.yml and implement Redis-based rate limiting in the BFF.

### Monitoring

Add Prometheus metrics or integrate with your existing monitoring:

```python
from prometheus_client import Counter, Histogram

workspace_actions = Counter('workspace_actions_total', 'Total workspace actions')
api_latency = Histogram('api_latency_seconds', 'API latency')
```

## 🧪 Testing

### Manual Testing
```bash
# Health check
curl http://localhost:8000/health

# Test endpoints (with auth)
curl -H "Authorization: Bearer your-token" http://localhost:8000/me
```

### Automated Testing
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

## 📊 Monitoring & Logs

### View Logs
```bash
# Docker logs
docker-compose logs -f

# Direct logs
tail -f /var/log/fisamy-bff.log
```

### Health Checks
- **Endpoint**: `/health`
- **Docker**: Built-in health check every 30s
- **Caddy**: Automatic HTTPS and reverse proxy

## 🚨 Troubleshooting

### Common Issues

1. **CORS errors**: Check `ALLOWED_ORIGINS` in environment
2. **API timeouts**: Verify Coder and Domain Manager URLs are accessible
3. **Rate limiting**: Check Caddy logs for any proxy errors
4. **Authentication**: Ensure your auth middleware is properly implemented

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python -m uvicorn bff_main:app --reload --log-level debug
```

## 🔄 Updates & Maintenance

### Updating Dependencies
```bash
# Update requirements
pip install --upgrade -r requirements.txt

# Rebuild Docker image
docker-compose build --no-cache
docker-compose up -d
```

### Database Migrations
Currently stateless - no database migrations needed. If you add persistence later, implement Alembic migrations.

## 📞 Support

For issues or questions:
1. Check the logs: `docker-compose logs -f`
2. Verify environment variables
3. Test individual endpoints
4. Check Coder and Domain Manager connectivity

## 🎯 Next Steps

1. **Implement real authentication** (JWT, session cookies, etc.)
2. **Add database persistence** for user preferences
3. **Implement caching** for frequently accessed data
4. **Add metrics and monitoring** (Prometheus, Grafana)
5. **Set up CI/CD pipeline** for automated deployments
