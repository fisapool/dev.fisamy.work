# 🚀 Coder-lite Provision System - Complete Implementation

> **End-to-end workspace provisioning system with enterprise-grade reliability, security, and observability**

## 📋 Table of Contents

- [System Overview](#system-overview)
- [Architecture](#architecture)
- [Components](#components)
- [Quick Start](#quick-start)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Testing](#testing)
- [Monitoring & Observability](#monitoring--observability)
- [Security](#security)
- [Troubleshooting](#troubleshooting)
- [Production Checklist](#production-checklist)

## 🎯 System Overview

The Coder-lite Provision System is a production-ready, auto-scaling platform for hosting VS Code workspaces in the cloud. It provides:

- **Automated Provisioning**: Order webhook → Workspace live in <5 minutes
- **Multi-Provider Support**: Stripe, Shopee, and generic webhook providers
- **Enterprise Security**: Webhook signature validation, rate limiting, audit trails
- **High Availability**: Redis-based job queues, idempotency, rollback capabilities
- **Comprehensive Monitoring**: Prometheus metrics, health checks, alerting
- **Admin Operations**: Template management, break-glass procedures, audit logs

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Webhook API   │    │   Redis Queue   │    │ Provision Worker│
│   (FastAPI)     │───▶│   + Locks       │───▶│   (Docker)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Notification   │    │   Port Allocator│    │   Caddy Proxy   │
│   System        │    │   + Health      │    │   + Config      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Data Flow

1. **Order Webhook** → Signature validation → Idempotency check → Job enqueued
2. **Provision Worker** → Port allocation → Docker compose → Caddy config
3. **Health Check** → Workspace verification → User notification → First login tracking

## 🧩 Components

### Core Backend (`main.py`)
- FastAPI application with health checks and metrics
- Webhook processing with provider-specific validation
- Job queue management and status endpoints

### Provision Worker (`workers/provision_worker.py`)
- Docker container orchestration
- Port allocation with conflict resolution
- Workspace health monitoring and rollback

### Notification System (`utils/notifier.py`)
- Multi-channel support (Email, WhatsApp, Telegram)
- Retry logic with exponential backoff
- Dead letter queue for failed notifications

### Webhook Validation (`utils/webhook_validator.py`)
- Provider-specific signature validation (Stripe, Shopee)
- Constant-time comparison for security
- Rate limiting and abuse prevention

### Admin Management (`utils/admin_manager.py`)
- Workspace template CRUD operations
- Audit event logging and retrieval
- Break-glass emergency procedures

### Metrics & Monitoring (`utils/metrics.py`)
- Prometheus-compatible metrics export
- Performance tracking and alerting
- Custom provision event metrics

### Port Allocation (`utils/port_allocator.py`)
- Dynamic port assignment
- Conflict detection and resolution
- Port range management

### Distributed Locking (`utils/distributed_lock.py`)
- Redis-based idempotency locks
- Order processing deduplication
- Concurrent job safety

### Atomic Operations (`utils/atomic_writer.py`)
- Safe configuration file updates
- Caddy config atomic writes
- Rollback capabilities

## 🚀 Quick Start

### Prerequisites

```bash
# System requirements
- Python 3.8+
- Redis 6.0+
- Docker & Docker Compose
- Linux environment (Ubuntu 20.04+ recommended)

# Network requirements
- Ports 8000 (API), 6379 (Redis), 13001-65535 (workspaces)
- Outbound SMTP/API access for notifications
```

### 1. Clone and Setup

```bash
cd coder-lite/code-fisamy-work-coder-lite

# Install dependencies
pip install -r requirements.txt

# Copy environment configuration
cp env.example .env
nano .env  # Configure your settings
```

### 2. Start Redis

```bash
# Ubuntu/Debian
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Or manually
redis-server --daemonize yes
```

### 3. Run the System

```bash
# Development mode
python main.py

# Production mode
python run_backend.py

# Or with custom settings
PORT=9000 RELOAD=false python main.py
```

### 4. Verify Installation

```bash
# Health check
curl http://localhost:8000/health

# Metrics
curl http://localhost:8000/metrics

# API docs
curl http://localhost:8000/docs
```

## 🔌 API Reference

### Core Endpoints

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `/health` | GET | System health status | None |
| `/metrics` | GET | Prometheus metrics | None |
| `/webhooks/orders` | POST | Process order webhooks | Signature |
| `/provision/status` | GET | Queue and system status | None |
| `/provision/process` | POST | Process provision jobs | None |

### Webhook Format

```json
{
  "provider": "stripe",
  "order_id": "ord_123456789",
  "customer": {
    "email": "user@example.com",
    "phone": "+60123456789"
  },
  "line_items": [
    {
      "sku": "DEV-BASIC-1M",
      "qty": 1
    }
  ],
  "paid": true,
  "signature": "whsec_..."
}
```

### Response Format

```json
{
  "status": "enqueued",
  "idempotency_key": "stripe:ord_123456789",
  "username": "user",
  "estimated_time": "2-5 minutes"
}
```

## ⚙️ Configuration

### Environment Variables

```bash
# Server Configuration
HOST=0.0.0.0
PORT=8000
RELOAD=false
LOG_LEVEL=info

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Port Allocation
START_PORT=13001
MAX_PORT=65535

# Coder-lite Paths
CODER_LITE_PATH=/opt/coder-lite

# Security
WEBHOOK_SECRET=your_webhook_secret_here
JWT_SECRET=your_jwt_secret_here

# Notifications
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=noreply@code.fisamy.work
SMTP_PASSWORD=your_smtp_password

# WhatsApp Business API
WHATSAPP_TOKEN=your_whatsapp_token
PHONE_NUMBER_ID=your_phone_number_id

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

### Plan Configuration

```python
plans = {
    'DEV-BASIC-1M': {
        'cpu': '2.0',
        'ram': '4g',
        'disk': 20,
        'idle_timeout': 45
    },
    'DEV-PLUS-1M': {
        'cpu': '4.0',
        'ram': '8g',
        'disk': 40,
        'idle_timeout': 120
    },
    'DEV-GPU-1M': {
        'cpu': '6.0',
        'ram': '16g',
        'disk': 60,
        'gpu': True,
        'idle_timeout': 45
    }
}
```

## 🚀 Deployment

### Production Deployment

```bash
# 1. Run deployment playbook
python scripts/deployment_playbook.py

# 2. Or manual deployment
cd /opt/coder-lite
docker-compose -f docker-compose.yml up -d

# 3. Verify deployment
curl http://localhost:8000/health
```

### Docker Compose

```yaml
version: "3.9"
services:
  coder-lite-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - REDIS_HOST=redis
      - CODER_LITE_PATH=/opt/coder-lite
    depends_on:
      - redis
    volumes:
      - /opt/coder-lite:/opt/coder-lite
      - /var/run/docker.sock:/var/run/docker.sock

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  caddy:
    image: caddy:2-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
      - caddy_config:/config

volumes:
  redis_data:
  caddy_data:
  caddy_config:
```

### Systemd Service

```ini
[Unit]
Description=Coder-lite Provision System
After=network.target redis.service

[Service]
Type=simple
User=coder-lite
WorkingDirectory=/opt/coder-lite
Environment=PATH=/opt/coder-lite/venv/bin
ExecStart=/opt/coder-lite/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## 🧪 Testing

### Manual Test Suite

```bash
# Run comprehensive test suite
python scripts/manual_test.py

# Test specific components
python test_backend.py

# Load testing
python -m pytest tests/ -v
```

### Test Coverage

The manual test suite covers:

- ✅ Basic health checks and connectivity
- ✅ Webhook processing and idempotency
- ✅ Complete provisioning workflow
- ✅ Notification system functionality
- ✅ Admin operations and templates
- ✅ Failure scenarios and edge cases
- ✅ Rollback and recovery testing
- ✅ Performance and load testing
- ✅ Security validation
- ✅ Cleanup and verification

### cURL Smoke Tests

```bash
# Health check
curl -sS http://localhost:8000/health | jq

# Metrics
curl -sS http://localhost:8000/metrics | head -n 20

# Test webhook
curl -sS -X POST http://localhost:8000/webhooks/orders \
  -H 'content-type: application/json' \
  -d '{"order_id":"ord_test_001","user_email":"user@example.com","plan":"pro"}' | jq
```

## 📊 Monitoring & Observability

### Health Checks

```bash
# System health
GET /health
Response: {"status": "healthy", "services": {"redis": "healthy", "port_allocator": "healthy"}}

# Detailed health
GET /health/detailed
Response: {"status": "healthy", "checks": {...}}
```

### Metrics (Prometheus)

```bash
# Provision metrics
provision_jobs_total{result="success"} 42
provision_jobs_total{result="failure"} 3

# Timing metrics
provision_duration_ms_bucket{le="5000"} 15
provision_duration_ms_bucket{le="10000"} 28

# Queue metrics
provision_queue_length 5
notification_queue_length 2
```

### Alerting Rules

```yaml
# Prometheus alerting rules
groups:
  - name: coder-lite
    rules:
      - alert: ProvisionFailures
        expr: provision_jobs_total{result="failure"} > 0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Provision jobs failing"
          description: "{{ $value }} provision jobs have failed in the last 5 minutes"

      - alert: HighQueueLength
        expr: provision_queue_length > 100
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High provision queue length"
          description: "Queue length is {{ $value }} (threshold: 100)"
```

### Logging

```python
# Structured logging with correlation IDs
logger.info("Processing provision job", extra={
    "job_id": job_id,
    "user_email": user_email,
    "plan": plan,
    "correlation_id": correlation_id
})
```

## 🔒 Security

### Webhook Security

- **Signature Validation**: HMAC-SHA256 with provider-specific secrets
- **Timestamp Validation**: 5-minute tolerance window
- **Rate Limiting**: 100 requests per minute per IP
- **Input Sanitization**: JSON schema validation, XSS protection

### Access Control

- **Admin Authentication**: bcrypt password hashing
- **Session Management**: Redis-based sessions with TTL
- **Audit Logging**: All admin actions logged with IP addresses
- **Break-glass Procedures**: Emergency access with full audit trail

### Data Protection

- **No Secrets in Logs**: Only IDs and metadata logged
- **Encrypted Communication**: TLS 1.3 for all external communication
- **Secure Password Generation**: Cryptographically secure random passwords
- **Data Retention**: Configurable audit log retention policies

## 🚨 Troubleshooting

### Common Issues

#### 1. Redis Connection Failed

```bash
# Check Redis status
sudo systemctl status redis-server

# Check Redis connectivity
redis-cli ping

# Check Redis configuration
redis-cli config get bind
redis-cli config get port
```

#### 2. Port Allocation Failed

```bash
# Check available ports
netstat -tlnp | grep :13001

# Check port range configuration
echo $START_PORT
echo $MAX_PORT

# Test port binding
python -c "import socket; s=socket.socket(); s.bind(('localhost', 13001)); print('Port available')"
```

#### 3. Docker Container Failed

```bash
# Check container status
docker ps -a

# Check container logs
docker logs <container_id>

# Check Docker daemon
sudo systemctl status docker

# Check disk space
df -h
```

#### 4. Caddy Configuration Error

```bash
# Validate Caddyfile
docker exec caddy caddy validate --config /etc/caddy/Caddyfile

# Check Caddy status
docker exec caddy caddy status

# Reload Caddy configuration
docker exec caddy caddy reload
```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=debug
python main.py

# Enable verbose Docker output
docker-compose logs -f

# Check Redis keys
redis-cli keys "*"
redis-cli llen provision_jobs
```

### Performance Issues

```bash
# Check system resources
htop
iotop
nethogs

# Check Redis performance
redis-cli info memory
redis-cli info stats

# Check API response times
curl -w "@curl-format.txt" -o /dev/null -s "http://localhost:8000/health"
```

## ✅ Production Checklist

### Pre-Launch

- [ ] **Environment Configuration**
  - [ ] All environment variables set
  - [ ] Redis password configured
  - [ ] Webhook secrets configured
  - [ ] SMTP/notification credentials set

- [ ] **Infrastructure**
  - [ ] Redis cluster configured and tested
  - [ ] Docker daemon running and accessible
  - [ ] Port range available and tested
  - [ ] Disk space sufficient (>50GB free)

- [ ] **Security**
  - [ ] Webhook signature validation enabled
  - [ ] Rate limiting configured
  - [ ] Admin passwords changed from defaults
  - [ ] Firewall rules configured

### Launch Day

- [ ] **Deployment**
  - [ ] Backup current system (if applicable)
  - [ ] Deploy new version
  - [ ] Verify all services healthy
  - [ ] Test end-to-end workflow

- [ ] **Monitoring**
  - [ ] Prometheus metrics collection working
  - [ ] Grafana dashboards accessible
  - [ ] Alerting rules configured
  - [ ] Log aggregation working

- [ ] **Testing**
  - [ ] Manual test suite passes
  - [ ] Load testing completed
  - [ ] Failure scenarios tested
  - [ ] Rollback procedures verified

### Post-Launch

- [ ] **Operations**
  - [ ] Monitor system metrics for 24 hours
  - [ ] Verify notification delivery
  - [ ] Check audit logs for anomalies
  - [ ] Validate backup procedures

- [ ] **Documentation**
  - [ ] Runbook updated with lessons learned
  - [ ] Incident response procedures documented
  - [ ] Team training completed
  - [ ] Support escalation paths defined

## 📚 Additional Resources

### Documentation

- [Backend README](BACKEND_README.md) - Detailed backend implementation
- [Deployment Guide](DEPLOYMENT_PRODUCTION.md) - Production deployment procedures
- [Enhancement Summary](ENHANCEMENT_SUMMARY.md) - Recent improvements and features

### Scripts

- `scripts/manual_test.py` - Comprehensive testing suite
- `scripts/deployment_playbook.py` - Production deployment automation
- `devctl/` - Development and debugging tools

### Configuration Examples

- `docker-compose.override-enhanced.yml` - Enhanced Docker configuration
- `Caddyfile` - Reverse proxy configuration
- `env.example` - Environment variable template

## 🤝 Support & Contributing

### Getting Help

1. **Check the logs**: `docker-compose logs -f`
2. **Review metrics**: `curl localhost:8000/metrics`
3. **Run tests**: `python scripts/manual_test.py`
4. **Check health**: `curl localhost:8000/health`

### Reporting Issues

When reporting issues, please include:

- System information (OS, Python version, Docker version)
- Error logs and stack traces
- Steps to reproduce
- Expected vs actual behavior
- Environment configuration (sanitized)

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Coder Team** - For the excellent OpenVSCode Server
- **FastAPI** - For the modern, fast web framework
- **Redis** - For the reliable data store and job queue
- **Docker** - For containerization and orchestration

---

**🚀 Ready to deploy? Run the deployment playbook:**

```bash
python scripts/deployment_playbook.py
```

**🧪 Test your deployment:**

```bash
python scripts/manual_test.py
```

**📊 Monitor your system:**

```bash
curl localhost:8000/health
curl localhost:8000/metrics
```
