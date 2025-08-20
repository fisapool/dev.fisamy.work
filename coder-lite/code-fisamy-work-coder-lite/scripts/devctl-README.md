# Enhanced Development Environment Controller (devctl)

A comprehensive bash script for managing Docker-based development environments with advanced features including resource limits, health checks, Caddy reverse proxy integration, and XFS quota management.

## Features

### Core Features
- **User Environment Management**: Create, update, delete, and manage development environments
- **Resource Limits**: CPU, memory, disk, and process limits per user
- **Auto-port Allocation**: Automatic port detection starting from 13001
- **XFS Quota Support**: Disk space management with project quotas
- **Caddy Integration**: Automatic reverse proxy configuration with SSL support

### Advanced Features
- **Health Checks**: Container health monitoring with configurable parameters
- **Image Version Pinning**: Pin specific OpenVSCode Server versions
- **Enhanced Security**: Non-root containers, capability dropping, security options
- **Custom Networks**: Isolated network configurations
- **Comprehensive Logging**: Structured logging with rotation
- **Backup & Restore**: User environment backup and restore capabilities
- **Configuration Management**: External configuration file support

## Installation

### Prerequisites
- Docker and Docker Compose
- Bash 4.0+
- Optional: xfs_quota for disk quotas
- Optional: Caddy for reverse proxy
- Optional: systemd for service management

### Quick Setup
```bash
# Make the script executable
chmod +x devctl-enhanced

# Optional: Install system-wide
sudo cp devctl-enhanced /usr/local/bin/devctl
sudo mkdir -p /etc/devctl
sudo cp devctl.conf.example /etc/devctl.conf

# Create required directories
sudo mkdir -p /srv/devdata
```

## Usage

### Basic Commands

#### Create a new user environment
```bash
# Basic creation
./devctl-enhanced create john

# With custom resources
./devctl-enhanced create jane --cpu 4 --ram 8g --disk 50

# With domain configuration
./devctl-enhanced create alice --domain alice.dev.example.com

# With image version pinning
./devctl-enhanced create bob --image-version 1.93.1 --healthcheck-enable
```

#### Update existing environment
```bash
# Update resources
./devctl-enhanced update john --ram 16g --cpu 8

# Enable health checks
./devctl-enhanced update alice --healthcheck-enable
```

#### List all environments
```bash
./devctl-enhanced list
```

#### Check environment status
```bash
./devctl-enhanced status john
```

#### Delete environment
```bash
# Remove environment (keeps data)
./devctl-enhanced delete john

# Purge environment (removes data)
./devctl-enhanced delete john --purge
```

### Advanced Usage

#### Domain Configuration
```bash
# Use base domain for subdomain generation
./devctl-enhanced create user1 --domain-base dev.example.com
# Creates: user1.dev.example.com

# Custom domain
./devctl-enhanced create user2 --domain custom.example.com
```

#### Health Check Configuration
```bash
# Enable with custom parameters
./devctl-enhanced create user3 \
  --healthcheck-enable \
  --healthcheck-interval 30s \
  --healthcheck-timeout 5s \
  --healthcheck-retries 5
```

#### Resource Limits
```bash
# Comprehensive resource configuration
./devctl-enhanced create poweruser \
  --cpu 8 \
  --ram 16g \
  --disk 100 \
  --pids-limit 1024 \
  --ulimit-nofile 16384:16384
```

## Configuration

### Configuration File (/etc/devctl.conf)
```bash
# Default resource limits
DEFAULT_CPU="2"
DEFAULT_RAM="4g"
DEFAULT_DISK="20"
DEFAULT_PORT_START="13001"

# Image configuration
DEFAULT_IMAGE="ghcr.io/coder/openvscode-server:latest"

# Health check defaults
DEFAULT_HEALTHCHECK_INTERVAL="15s"
DEFAULT_HEALTHCHECK_TIMEOUT="3s"
DEFAULT_HEALTHCHECK_RETRIES="10"
DEFAULT_HEALTHCHECK_START_PERIOD="10s"

# Caddy configuration
CADDY_FILE_DEFAULT="/etc/caddy/Caddyfile"
CADDY_EMAIL="admin@example.com"

# Data directory
DATA_ROOT="/srv/devdata"
```

### Environment Variables
- `TZ`: Timezone (default: Asia/Kuala_Lumpur)
- `PASSWORD`: Optional password for web access
- `GIT_AUTHOR_NAME`: Git user name
- `GIT_AUTHOR_EMAIL`: Git user email
- `NODE_ENV`: Node.js environment

## Docker Compose Override Structure

The script generates enhanced Docker Compose configurations with:

### Service Template
```yaml
username:
  image: ghcr.io/coder/openvscode-server:latest
  container_name: dev-username
  environment:
    - TZ=${TZ:-Asia/Kuala_Lumpur}
  ports:
    - "127.0.0.1:13001:3000"
  volumes:
    - /srv/devdata/username:/home/openvscode
  restart: unless-stopped
  
  # Resource limits
  mem_limit: "4g"
  memswap_limit: "4g"
  cpus: "2.0"
  pids_limit: 512
  
  # Health check
  healthcheck:
    test: ["CMD-SHELL", "bash -c ': </dev/tcp/127.0.0.1/3000' || exit 1"]
    interval: 15s
    timeout: 3s
    retries: 10
    start_period: 10s
  
  # Security
  security_opt:
    - no-new-privileges:true
  cap_drop:
    - ALL
  cap_add:
    - CHOWN
    - SETGID
    - SETUID
  
  # Labels
  labels:
    - fisamy.role=ovscode
    - fisamy.user=username
```

## Caddy Integration

### Automatic Caddy Configuration
The script automatically configures Caddy reverse proxy with:

- SSL/TLS certificates via Let's Encrypt
- Security headers (HSTS, CSP, etc.)
- Rate limiting
- Basic auth support (optional)
- Custom domain support

### Caddy Site Block Example
```caddy
username.dev.example.com {
  encode gzip
  
  # Rate limiting
  @big body {
    max_size 20MB
  }
  handle @big {
    respond 413
  }

  reverse_proxy 127.0.0.1:13001

  # Security headers
  header {
    Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
    X-Content-Type-Options "nosniff"
    X-Frame-Options "DENY"
    Referrer-Policy "no-referrer"
    Content-Security-Policy "frame-ancestors 'none';"
  }

  # Basic auth (optional)
  # basicauth /* {
  #   username $2y$05$hash
  # }
}
```

## XFS Quota Management

### Setup Requirements
```bash
# Enable XFS project quota
sudo mount -o remount,prjquota /srv
sudo xfs_quota -x -c "project -s username" /srv/devdata
sudo xfs_quota -x -c "limit -p bhard=20g username" /srv/devdata
```

### Monitoring Quota Usage
```bash
# Check quota for user
sudo xfs_quota -x -c "quota -p username" /srv/devdata

# Report quota usage
sudo xfs_quota -x -c "report -p" /srv/devdata
```

## Health Checks

### Available Health Check Methods
1. **TCP Port Check**: Basic port connectivity
2. **HTTP Health Check**: Web endpoint verification
3. **Custom Script**: User-defined health checks

### Health Check Parameters
- `interval`: How often to check (default: 15s)
- `timeout`: Response timeout (default: 3s)
- `retries`: Failure threshold (default: 10)
- `start_period`: Startup grace period (default: 10s)

## Monitoring and Logging

### Log Locations
- **Application Logs**: `/var/log/devctl.log`
- **Container Logs**: `docker logs dev-username`
- **Caddy Logs**: `/var/log/caddy/`

### Monitoring Labels
All containers include labels for monitoring:
- `fisamy.user`: Username
- `fisamy.role`: Service type
- `fisamy.cpu`: CPU allocation
- `fisamy.ram`: RAM allocation
- `fisamy.disk`: Disk allocation

## Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Check port usage
ss -ltn | grep :13001

# Use custom port
./devctl-enhanced create user --port 13002
```

#### Caddy Configuration Issues
```bash
# Validate Caddy configuration
caddy validate --config /etc/caddy/Caddyfile

# Check Caddy logs
journalctl -u caddy -f
```

#### Docker Issues
```bash
# Check container status
docker ps -a | grep dev-user

# View container logs
docker logs dev-user

# Check resource usage
docker stats dev-user
```

#### Quota Issues
```bash
# Check if prjquota is enabled
mount | grep /srv

# Verify quota setup
sudo xfs_quota -x -c "report -p" /srv/devdata
```

### Debug Mode
Enable verbose logging:
```bash
./devctl-enhanced create user --verbose --dry-run
```

## Examples

### Complete Setup Example
```bash
# 1. Create user with full configuration
./devctl-enhanced create developer1 \
  --cpu 4 \
  --ram 8g \
  --disk 50 \
  --domain-base dev.example.com \
  --image-version 1.93.1 \
  --healthcheck-enable \
  --reload-caddy

# 2. Start the environment
docker compose up -d developer1

# 3. Access the environment
# Via domain: https://developer1.dev.example.com
# Via port: http://localhost:13001
```

### Batch User Creation
```bash
# Create multiple users
for user in alice bob charlie; do
  ./devctl-enhanced create "$user" \
    --domain-base dev.example.com \
    --cpu 2 \
    --ram 4g \
    --disk 20
done
```

### Resource Monitoring
```bash
# Monitor all user containers
docker stats $(docker ps --filter label=fisamy.role=ovscode --format "{{.Names}}")

# Check quota usage for all users
sudo xfs_quota -x -c "report -p" /srv/devdata
```

## Security Considerations

- All containers run as non-root users
- Capabilities are dropped to minimum required
- Network isolation via custom networks
- Resource limits prevent resource exhaustion
- Security headers in Caddy configuration
- Regular security updates via image version pinning

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

## License

MIT License - see LICENSE file for details
