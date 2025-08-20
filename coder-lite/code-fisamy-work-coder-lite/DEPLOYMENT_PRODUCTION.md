# Production Deployment Guide - Coder-lite Provision System

This guide covers deploying the production-hardened provision system with all tight upgrades implemented.

## 🚀 **Pre-deployment Checklist**

### **System Requirements**
- [ ] Ubuntu 22.04+ with root/sudo access
- [ ] Docker Engine + Docker Compose v2
- [ ] Caddy installed and configured
- [ ] XFS filesystem with `pquota` support (recommended)
- [ ] Redis server for distributed locking
- [ ] PostgreSQL database for persistence
- [ ] At least 4GB RAM, 2 CPU cores available

### **Security Prerequisites**
- [ ] Firewall configured (ufw/iptables)
- [ ] SSH key-based authentication only
- [ ] Regular security updates enabled
- [ ] Fail2ban configured
- [ ] SSL certificates ready for domains

## 📋 **Installation Steps**

### **1. Base Coder-lite Setup**

```bash
# Create installation directory
sudo mkdir -p /opt/coder-lite && cd /opt/coder-lite

# Extract the bundle
sudo tar -xzf code-fisamy-work-coder-lite.tgz

# Set proper ownership
sudo chown -R root:root /opt/coder-lite
sudo chmod -R 755 /opt/coder-lite

# Create data directory
sudo mkdir -p /srv/devdata
sudo chown root:root /srv/devdata
sudo chmod 755 /srv/devdata
```

### **2. Install Dependencies**

```bash
# System packages
sudo apt-get update
sudo apt-get install -y \
    python3-pip \
    python3-venv \
    redis-server \
    postgresql \
    postgresql-contrib \
    curl \
    bcrypt \
    xfsprogs

# Python dependencies
cd /opt/coder-lite
sudo python3 -m pip install -r requirements.txt
```

### **3. Configure Redis**

```bash
# Edit Redis configuration
sudo nano /etc/redis/redis.conf

# Add/modify these lines:
bind 127.0.0.1
protected-mode yes
requirepass your_strong_redis_password
maxmemory 256mb
maxmemory-policy allkeys-lru

# Restart Redis
sudo systemctl restart redis-server
sudo systemctl enable redis-server
```

### **4. Configure PostgreSQL**

```bash
# Create database and user
sudo -u postgres psql

CREATE DATABASE coder_lite;
CREATE USER coder WITH PASSWORD 'your_strong_db_password';
GRANT ALL PRIVILEGES ON DATABASE coder_lite TO coder;
\q

# Test connection
psql -h localhost -U coder -d coder_lite
```

### **5. Configure Caddy**

```bash
# Copy Caddyfile
sudo cp /opt/coder-lite/Caddyfile /etc/caddy/Caddyfile

# Test configuration
sudo caddy validate --config /etc/caddy/Caddyfile

# Reload Caddy
sudo systemctl reload caddy
```

### **6. Setup Secure Host Helper**

```bash
# Make script executable
sudo chmod +x /opt/coder-lite/scripts/dev-provision

# Configure sudoers
sudo cp /opt/coder-lite/systemd/dev-provision.sudoers /etc/sudoers.d/dev-provision
sudo chmod 440 /etc/sudoers.d/dev-provision

# Verify syntax
sudo visudo -c -f /etc/sudoers.d/dev-provision

# Create worker user
sudo useradd -r -s /bin/false coder-worker
sudo usermod -aG docker coder-worker
```

### **7. Configure XFS Quotas (if available)**

```bash
# Check filesystem type
df -T /srv/devdata

# If XFS, ensure pquota is enabled
sudo mount -o remount,pquota /srv/devdata

# Verify in /etc/fstab
sudo nano /etc/fstab
# Add pquota to mount options: UUID=... /srv/devdata xfs defaults,pquota 0 2
```

### **8. Setup Systemd Services**

```bash
# Copy service files
sudo cp /opt/coder-lite/systemd/dev-idle-reaper.service /etc/systemd/system/
sudo cp /opt/coder-lite/systemd/dev-idle-reaper.timer /etc/systemd/system/

# Enable and start services
sudo systemctl daemon-reload
sudo systemctl enable --now dev-idle-reaper.timer
```

## 🔧 **Configuration**

### **1. Production Configuration**

```bash
# Copy production config
sudo cp /opt/coder-lite/config/production.yml /etc/coder-lite/config.yml

# Edit configuration
sudo nano /etc/coder-lite/config.yml

# Key settings to adjust:
# - Database connection strings
# - Redis passwords
# - Domain names
# - Plan matrix
# - Alert thresholds
```

### **2. Environment Variables**

```bash
# Create environment file
sudo nano /etc/coder-lite/.env

# Add these variables:
DATABASE_URL=postgresql://coder:password@localhost/coder_lite
REDIS_URL=redis://:password@localhost:6379/0
DOMAIN_BASE=code.fisamy.work
SMTP_PASSWORD=your_smtp_password
SLACK_WEBHOOK_URL=your_slack_webhook
```

### **3. Logging Configuration**

```bash
# Create log directory
sudo mkdir -p /var/log/coder-lite
sudo chown coder-worker:coder-worker /var/log/coder-lite

# Configure logrotate
sudo nano /etc/logrotate.d/coder-lite

/var/log/coder-lite/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 coder-worker coder-worker
    postrotate
        systemctl reload coder-lite
    endscript
}
```

## 🚀 **Deployment**

### **1. Start Provision Worker**

```bash
# Create worker service
sudo nano /etc/systemd/system/coder-provision-worker.service

[Unit]
Description=Coder-lite Provision Worker
After=network.target redis.service postgresql.service

[Service]
Type=simple
User=coder-worker
Group=coder-worker
WorkingDirectory=/opt/coder-lite
EnvironmentFile=/etc/coder-lite/.env
ExecStart=/usr/bin/python3 -m workers.provision_worker
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable --now coder-provision-worker
```

### **2. Test Provision System**

```bash
# Test basic functionality
curl -X POST http://localhost:8000/webhooks/orders \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "test",
    "order_id": "TEST-001",
    "customer": {"email": "test@example.com"},
    "line_items": [{"sku": "DEV-BASIC-1M", "qty": 1}],
    "paid": true
  }'

# Check worker logs
sudo journalctl -u coder-provision-worker -f

# Check metrics
curl http://localhost:8000/metrics
```

## 📊 **Monitoring & Alerting**

### **1. Prometheus Configuration**

```yaml
# /etc/prometheus/prometheus.yml
scrape_configs:
  - job_name: 'coder-lite'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

### **2. Grafana Dashboard**

Import the provided dashboard JSON or create custom panels for:
- Provision success/failure rates
- Time-to-ready metrics
- Resource utilization
- Error breakdown by plan
- Active workspace count

### **3. Alert Rules**

```yaml
# /etc/prometheus/rules/coder-lite.yml
groups:
  - name: coder-lite
    rules:
      - alert: ProvisionFailureRate
        expr: rate(provision_failure_total[5m]) > 0.05
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High provision failure rate"
          
      - alert: ProvisionTimeout
        expr: provision_duration_ms > 300000
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Provision taking too long"
```

## 🔒 **Security Hardening**

### **1. Network Security**

```bash
# Configure firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8000/tcp  # API port
sudo ufw enable

# Restrict Redis access
sudo ufw deny 6379/tcp
```

### **2. File Permissions**

```bash
# Secure configuration files
sudo chmod 600 /etc/coder-lite/.env
sudo chmod 600 /etc/coder-lite/config.yml
sudo chown coder-worker:coder-worker /etc/coder-lite/.env

# Secure scripts
sudo chmod 750 /opt/coder-lite/scripts/dev-provision
sudo chown root:root /opt/coder-lite/scripts/dev-provision
```

### **3. SSL/TLS Configuration**

```bash
# Update Caddyfile with SSL
sudo nano /etc/caddy/Caddyfile

# Add automatic HTTPS
*.code.fisamy.work {
    tls {
        on_demand
    }
    # ... rest of configuration
}
```

## 🧪 **Testing & Validation**

### **1. Load Testing**

```bash
# Install artillery
npm install -g artillery

# Create test scenario
cat > load-test.yml << EOF
config:
  target: 'http://localhost:8000'
  phases:
    - duration: 60
      arrivalRate: 10
scenarios:
  - name: "Provision orders"
    requests:
      - post:
          url: "/webhooks/orders"
          json:
            provider: "loadtest"
            order_id: "{{ $randomString() }}"
            customer: {"email": "{{ $randomEmail() }}"}
            line_items: [{"sku": "DEV-BASIC-1M", "qty": 1}]
            paid: true
EOF

# Run load test
artillery run load-test.yml
```

### **2. Chaos Engineering**

```bash
# Test Redis failure
sudo systemctl stop redis-server
# Verify system degrades gracefully

# Test database failure
sudo systemctl stop postgresql
# Verify proper error handling

# Test disk space
# Fill up /srv/devdata to test quota enforcement
```

## 📈 **Performance Tuning**

### **1. Database Optimization**

```sql
-- Add indexes for performance
CREATE INDEX idx_orders_idempotency_key ON orders(idempotency_key);
CREATE INDEX idx_workspaces_username ON workspaces(username);
CREATE INDEX idx_workspaces_port ON workspaces(port);

-- Analyze table statistics
ANALYZE orders;
ANALYZE workspaces;
```

### **2. Redis Optimization**

```bash
# Tune Redis for performance
sudo nano /etc/redis/redis.conf

# Key settings:
maxmemory 1gb
maxmemory-policy allkeys-lru
save ""  # Disable persistence for better performance
```

### **3. Worker Scaling**

```bash
# Scale workers based on load
sudo systemctl set-property coder-provision-worker CPUQuota=200%
sudo systemctl set-property coder-provision-worker MemoryLimit=1G
```

## 🚨 **Troubleshooting**

### **Common Issues**

1. **Port allocation conflicts**
   ```bash
   # Check used ports
   sudo netstat -tlnp | grep :13
   
   # Check database port allocation
   psql -h localhost -U coder -d coder_lite -c "SELECT port FROM workspaces WHERE port IS NOT NULL;"
   ```

2. **Caddy reload failures**
   ```bash
   # Check Caddy syntax
   sudo caddy validate --config /etc/caddy/Caddyfile
   
   # Check Caddy logs
   sudo journalctl -u caddy -f
   ```

3. **Docker permission issues**
   ```bash
   # Add user to docker group
   sudo usermod -aG docker coder-worker
   
   # Restart worker service
   sudo systemctl restart coder-provision-worker
   ```

### **Log Analysis**

```bash
# Follow all relevant logs
sudo journalctl -f -u coder-provision-worker -u caddy -u dev-idle-reaper

# Search for errors
sudo journalctl -u coder-provision-worker | grep -i error

# Check system resources
htop
df -h
free -h
```

## 🔄 **Maintenance**

### **1. Regular Backups**

```bash
# Create backup script
sudo nano /opt/coder-lite/scripts/backup.sh

#!/bin/bash
BACKUP_DIR="/backups/coder-lite/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# Backup data
tar -czf "$BACKUP_DIR/devdata.tar.gz" /srv/devdata

# Backup configurations
cp /opt/coder-lite/Caddyfile "$BACKUP_DIR/"
cp /opt/coder-lite/docker-compose.override.yml "$BACKUP_DIR/"

# Backup database
pg_dump -h localhost -U coder coder_lite > "$BACKUP_DIR/database.sql"

# Cleanup old backups (keep 30 days)
find /backups/coder-lite -type d -mtime +30 -exec rm -rf {} \;
```

### **2. Updates and Upgrades**

```bash
# Update Coder-lite
cd /opt/coder-lite
sudo git pull origin main

# Update dependencies
sudo python3 -m pip install -r requirements.txt

# Restart services
sudo systemctl restart coder-provision-worker
sudo systemctl reload caddy
```

### **3. Health Checks**

```bash
# Create health check script
sudo nano /opt/coder-lite/scripts/health-check.sh

#!/bin/bash
# Check all services
systemctl is-active coder-provision-worker
systemctl is-active caddy
systemctl is-active redis-server
systemctl is-active postgresql

# Check API endpoint
curl -f http://localhost:8000/health

# Check metrics endpoint
curl -f http://localhost:8000/metrics
```

## 🎯 **Success Metrics**

### **Key Performance Indicators**

- **Provision Success Rate**: > 99%
- **Time to Ready**: < 2 minutes (p95)
- **Error Rate**: < 0.1%
- **System Uptime**: > 99.9%
- **Resource Utilization**: < 80%

### **Monitoring Dashboard**

Ensure your monitoring covers:
- Real-time provision status
- Queue depth and processing times
- Resource usage per plan
- Error rates and types
- Customer satisfaction metrics

## 🚀 **Go-Live Checklist**

- [ ] All services running and healthy
- [ ] SSL certificates configured
- [ ] Monitoring and alerting active
- [ ] Backup system tested
- [ ] Load testing completed
- [ ] Security audit passed
- [ ] Documentation updated
- [ ] Team trained on operations
- [ ] Rollback plan ready
- [ ] Support escalation defined

---

**Congratulations!** You now have a production-hardened Coder-lite provision system with all the tight upgrades implemented. The system is ready to handle real traffic with enterprise-grade reliability and security.
