# 🚀 Coder-lite Provision System Backend

This is the backend API for the Coder-lite auto-provisioning system. It handles order webhooks, queues provision jobs, and manages the entire workspace provisioning workflow.

## 🏗️ **Architecture Overview**

```
[Webhook API] → [Redis Queue] → [Provision Worker] → [Secure Host Helper]
     ↓              ↓                    ↓                    ↓
[Order Intake] [Job Queue]      [Docker + Caddy]    [System Operations]
```

## 📋 **Prerequisites**

### **System Requirements**
- Python 3.8+
- Redis server
- Docker and Docker Compose (for full functionality)
- Coder-lite stack installed (optional for development)

### **Python Dependencies**
All dependencies are listed in `requirements.txt` and will be installed automatically.

## 🚀 **Quick Start**

### **1. Install Dependencies**

```bash
# Navigate to the backend directory
cd coder-lite/code-fisamy-work-coder-lite

# Install Python dependencies
pip install -r requirements.txt

# Or use a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### **2. Start Redis**

```bash
# Ubuntu/Debian
sudo systemctl start redis-server
sudo systemctl enable redis-server

# macOS
brew services start redis

# Or run manually
redis-server
```

### **3. Configure Environment**

```bash
# Copy environment template
cp env.example .env

# Edit configuration
nano .env

# Key settings to adjust:
# - REDIS_HOST, REDIS_PORT, REDIS_PASSWORD
# - HOST, PORT for the API server
# - CODER_LITE_PATH for full functionality
```

### **4. Run the Backend**

```bash
# Simple start
python run_backend.py

# Or start with custom settings
PORT=9000 RELOAD=true python run_backend.py

# Or run directly
python main.py
```

## 🌐 **API Endpoints**

### **Core Endpoints**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Root endpoint with system info |
| `/health` | GET | Health check for all services |
| `/metrics` | GET | Prometheus metrics export |
| `/docs` | GET | Interactive API documentation |

### **Provision Endpoints**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/webhooks/orders` | POST | Process order webhooks |
| `/provision/status` | GET | Get queue and system status |
| `/provision/process` | POST | Process provision jobs manually |

## 📨 **Webhook Integration**

### **Order Webhook Format**

```json
{
  "provider": "shopee",
  "order_id": "SP-12345",
  "customer": {
    "email": "buyer@example.com",
    "phone": "+60123456789"
  },
  "line_items": [
    {
      "sku": "DEV-BASIC-1M",
      "qty": 1
    }
  ],
  "paid": true,
  "signature": "HMAC_SIGNATURE"
}
```

### **Supported Plans**

| SKU | CPU | RAM | Disk | GPU | Idle Timeout |
|-----|-----|-----|------|-----|--------------|
| `DEV-BASIC-1M` | 2.0 | 4g | 20GB | ❌ | 45 min |
| `DEV-PLUS-1M` | 4.0 | 8g | 40GB | ❌ | 120 min |
| `DEV-GPU-1M` | 6.0 | 16g | 60GB | ✅ | 45 min |

## 🧪 **Testing**

### **Run All Tests**

```bash
# Make sure backend is running first
python run_backend.py &

# Run tests
python test_backend.py

# Or run specific tests
python -m pytest tests/ -v
```

### **Manual Testing**

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test order webhook
curl -X POST http://localhost:8000/webhooks/orders \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "test",
    "order_id": "TEST-001",
    "customer": {"email": "test@example.com"},
    "line_items": [{"sku": "DEV-BASIC-1M", "qty": 1}],
    "paid": true
  }'

# Check queue status
curl http://localhost:8000/provision/status
```

## ⚙️ **Configuration**

### **Environment Variables**

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | API server host |
| `PORT` | `8000` | API server port |
| `RELOAD` | `false` | Enable auto-reload for development |
| `LOG_LEVEL` | `info` | Logging level |
| `REDIS_HOST` | `localhost` | Redis server host |
| `REDIS_PORT` | `6379` | Redis server port |
| `REDIS_PASSWORD` | `` | Redis password (if set) |
| `START_PORT` | `13001` | Start port for workspace allocation |
| `MAX_PORT` | `65535` | Maximum port for workspace allocation |
| `CODER_LITE_PATH` | `/opt/coder-lite` | Path to Coder-lite installation |

### **Development vs Production**

```bash
# Development mode
RELOAD=true LOG_LEVEL=debug python run_backend.py

# Production mode
RELOAD=false LOG_LEVEL=info python run_backend.py

# Custom port
PORT=9000 python run_backend.py
```

## 🔧 **Development**

### **Project Structure**

```
coder-lite/
├── main.py                 # FastAPI application entry point
├── run_backend.py          # Backend runner script
├── test_backend.py         # Test script
├── requirements.txt        # Python dependencies
├── env.example            # Environment template
├── utils/                 # Utility modules
│   ├── atomic_writer.py   # Atomic file operations
│   ├── distributed_lock.py # Redis-based locking
│   ├── port_allocator.py  # Port allocation
│   └── metrics.py         # Metrics collection
├── workers/               # Background workers
│   └── provision_worker.py # Workspace provision worker
└── config/                # Configuration files
    └── production.yml     # Production configuration
```

### **Adding New Endpoints**

```python
# In main.py
@app.post("/api/new-endpoint")
async def new_endpoint(data: YourModel):
    """Your new endpoint"""
    # Your logic here
    return {"status": "success"}
```

### **Adding New Workers**

```python
# Create new worker file
# workers/your_worker.py
class YourWorker:
    def __init__(self, config):
        self.config = config
    
    def process_job(self, job_data):
        # Your processing logic
        pass

# Register in main.py
your_worker = YourWorker(config)
```

## 📊 **Monitoring & Metrics**

### **Health Checks**

The backend provides comprehensive health monitoring:

- **Service Health**: Redis, Port Allocator, Provision Worker
- **Queue Status**: Job count, processing status
- **System Metrics**: Response times, error rates

### **Prometheus Metrics**

```bash
# View metrics
curl http://localhost:8000/metrics

# Key metrics available:
# - provision_success_total
# - provision_failure_total
# - provision_duration_ms
# - queue_length
# - active_workspaces
```

### **Logging**

```bash
# View logs
tail -f /var/log/coder-lite/provision.log

# Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
```

## 🚨 **Troubleshooting**

### **Common Issues**

#### **1. Redis Connection Failed**
```bash
# Check Redis status
sudo systemctl status redis-server

# Start Redis if stopped
sudo systemctl start redis-server

# Test connection
redis-cli ping
```

#### **2. Port Already in Use**
```bash
# Check what's using the port
sudo netstat -tlnp | grep :8000

# Kill process or change port
PORT=9000 python run_backend.py
```

#### **3. Import Errors**
```bash
# Check Python path
python -c "import sys; print(sys.path)"

# Install missing dependencies
pip install -r requirements.txt

# Check virtual environment
which python
```

#### **4. Permission Denied**
```bash
# Check file permissions
ls -la run_backend.py

# Make executable
chmod +x run_backend.py

# Check user permissions
whoami
```

### **Debug Mode**

```bash
# Enable debug logging
LOG_LEVEL=debug python run_backend.py

# Enable auto-reload for development
RELOAD=true python run_backend.py

# Check detailed error messages
python -u run_backend.py
```

## 🔒 **Security Considerations**

### **Production Hardening**

1. **Environment Variables**: Never commit `.env` files
2. **Redis Security**: Set strong passwords and bind to localhost
3. **API Security**: Implement proper authentication and rate limiting
4. **Network Security**: Use firewalls and restrict access
5. **Logging**: Secure log files and rotate regularly

### **Webhook Security**

```python
# Implement proper signature verification
def verify_webhook_signature(payload, signature, secret):
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
```

## 📈 **Scaling**

### **Multiple Workers**

```bash
# Start multiple worker processes
python -m workers.provision_worker --worker-id 1 &
python -m workers.provision_worker --worker-id 2 &
python -m workers.provision_worker --worker-id 3 &
```

### **Load Balancing**

```bash
# Use nginx for load balancing
upstream backend {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}
```

### **Queue Management**

```bash
# Monitor queue health
redis-cli llen provision_jobs

# Clear stuck jobs (if needed)
redis-cli del provision_jobs

# Check processed orders
redis-cli keys "processed:*"
```

## 🔄 **Deployment**

### **Systemd Service**

```bash
# Create service file
sudo nano /etc/systemd/system/coder-provision-backend.service

[Unit]
Description=Coder-lite Provision Backend
After=network.target redis.service

[Service]
Type=simple
User=coder-worker
WorkingDirectory=/opt/coder-lite
EnvironmentFile=/opt/coder-lite/.env
ExecStart=/usr/bin/python3 /opt/coder-lite/run_backend.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable coder-provision-backend
sudo systemctl start coder-provision-backend
```

### **Docker Deployment**

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "run_backend.py"]
```

## 📚 **API Documentation**

Once the backend is running, visit:

- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🆘 **Getting Help**

### **Debug Information**

```bash
# System information
python -c "import sys; print(sys.version)"
python -c "import platform; print(platform.platform())"

# Package versions
pip freeze | grep -E "(fastapi|uvicorn|redis)"

# Redis info
redis-cli info server
```

### **Log Analysis**

```bash
# Follow logs in real-time
tail -f /var/log/coder-lite/provision.log

# Search for errors
grep -i error /var/log/coder-lite/provision.log

# Check recent activity
tail -100 /var/log/coder-lite/provision.log
```

---

## 🎯 **Next Steps**

1. **Test the backend** with the provided test script
2. **Configure your environment** for production use
3. **Set up monitoring** with Prometheus and Grafana
4. **Implement authentication** for production APIs
5. **Add more webhook providers** (Stripe, PayPal, etc.)
6. **Scale horizontally** with multiple worker instances

The backend is now ready to handle real order webhooks and provision workspaces automatically! 🚀
