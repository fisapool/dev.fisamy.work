# Coder Template Troubleshooting Guide

## Overview
This guide provides comprehensive troubleshooting for Coder templates, covering common issues, debugging procedures, and optimization techniques.

## Common Issues and Solutions

### 1. Agent Connection Issues

**Symptoms**: 
- Workspace shows "Waiting for connection from [agent]..."
- Agent status shows as disconnected
- Workspace fails to start

**Solutions**:
1. **Check Docker Service**:
   ```bash
   systemctl status docker
   sudo systemctl restart docker
   ```

2. **Verify Docker Socket Permissions**:
   ```bash
   ls -la /var/run/docker.sock
   sudo chmod 666 /var/run/docker.sock  # If needed
   ```

3. **Check Agent Logs**:
   ```bash
   tail -f /tmp/coder-agent.log
   docker logs <container_name>
   ```

4. **Test Connectivity**:
   ```bash
   curl -f https://coder.fisamy.work/health
   ping coder.fisamy.work
   ```

### 2. Startup Script Issues

**Symptoms**:
- Workspace incomplete or missing services
- Startup script errors in logs
- VS Code or Jupyter not accessible

**Solutions**:
1. **Check Startup Script Logs**:
   ```bash
   tail -f /tmp/coder-startup-script.log
   tail -f /tmp/health-server.log
   ```

2. **Increase Timeout**:
   - Set `startup_script_timeout = 300` in template
   - Add `set -Eeuo pipefail` for better error handling

3. **Add Debugging**:
   ```bash
   # Add to startup script
   set -x  # Enable command tracing
   exec > >(tee -a /tmp/startup-debug.log) 2>&1
   ```

4. **Test Manually**:
   ```bash
   # Run startup script in container directly
   docker exec -it <container_name> bash
   # Then run startup commands manually
   ```

### 3. Performance Issues

**Symptoms**:
- Slow workspace startup (>5 minutes)
- High resource usage
- Unresponsive services

**Solutions**:
1. **Use Pre-built Images**:
   - Use `ubuntu:22.04` instead of installing packages at startup
   - Consider custom base images with pre-installed tools

2. **Optimize Startup Script**:
   - Run only necessary commands
   - Use `--no-cache-dir` for pip installations
   - Parallelize independent operations

3. **Configure Resource Limits**:
   ```terraform
   cpu_shares = 2048
   memory     = 16384  # 16GB for GPU templates
   ```

4. **Use Docker Layer Caching**:
   - Order Dockerfile commands from least to most frequently changing
   - Use multi-stage builds

### 4. GPU Template Issues

**Symptoms**:
- GPU not detected
- CUDA not working
- PyTorch GPU support unavailable

**Solutions**:
1. **Verify NVIDIA Docker Runtime**:
   ```bash
   docker info | grep nvidia
   docker run --gpus all nvidia/cuda:12.4.1-runtime-ubuntu22.04 nvidia-smi
   ```

2. **Check GPU Availability**:
   ```bash
   nvidia-smi
   lspci | grep -i nvidia
   ```

3. **Ensure Proper Environment Variables**:
   ```terraform
   env = [
     "NVIDIA_VISIBLE_DEVICES=all",
     "NVIDIA_DRIVER_CAPABILITIES=all"
   ]
   ```

4. **Test GPU Access**:
   ```bash
   # Test in container
   python3 -c "import torch; print(torch.cuda.is_available())"
   nvidia-smi
   ```

### 5. Health Check Issues

**Symptoms**:
- Health checks failing
- Workspace marked as unhealthy
- Port accessibility problems

**Solutions**:
1. **Check Health Server**:
   ```bash
   tail -f /tmp/health-server.log
   curl http://localhost:13133
   ```

2. **Verify Port Configuration**:
   ```bash
   netstat -tuln | grep :13133
   docker port <container_name>
   ```

3. **Check Health Check Configuration**:
   ```terraform
   healthcheck {
     test         = ["CMD", "curl", "-fsS", "http://localhost:13133"]
     interval     = "5s"
     timeout      = "3s"
     retries      = 6
     start_period = "10s"
   }
   ```

## Quick Debug Commands

### System Health Check
```bash
# Run comprehensive debug
./back-end/scripts/debug_startup.sh

# Check specific services
systemctl status docker
systemctl status coder  # if applicable

# Monitor resources
htop
free -h
df -h
```

### Container Debugging
```bash
# List running containers
docker ps --filter "label=coder.template"

# Check container logs
docker logs <container_name>

# Execute commands in container
docker exec -it <container_name> bash

# Check container resources
docker stats <container_name>
```

### Network Debugging
```bash
# Check port availability
netstat -tuln | grep -E ':(13133|13337|8888)'

# Test connectivity
curl -v http://localhost:13133
telnet localhost 13337

# Check firewall
sudo ufw status
sudo iptables -L
```

## Monitoring and Logging

### Log File Locations
- **Agent logs**: `/tmp/coder-agent.log`
- **Startup logs**: `/tmp/coder-startup-script.log`
- **Health server logs**: `/tmp/health-server.log`
- **System logs**: `journalctl -u docker`

### Performance Monitoring
```bash
# Monitor startup times
grep "Starting.*script\|completed successfully" /tmp/coder-startup-script.log

# Monitor resource usage
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Monitor health check response times
time curl -s http://localhost:13133 > /dev/null
```

### Automated Monitoring Scripts
```bash
# Run performance monitoring
./monitor_performance.sh

# Validate deployment
./validate_deployment.sh

# Optimize templates
./optimize_templates.sh
```

## Prevention and Best Practices

### Template Design
1. **Use Pre-built Images**: Minimize runtime package installation
2. **Implement Proper Error Handling**: Use `set -Eeuo pipefail` and trap errors
3. **Add Comprehensive Logging**: Log all major operations with timestamps
4. **Configure Resource Limits**: Set appropriate CPU and memory constraints
5. **Use Health Checks**: Implement proper health endpoints

### Startup Script Optimization
1. **Parallel Operations**: Run independent commands in background
2. **Conditional Installation**: Only install packages if not already present
3. **Error Recovery**: Implement retry logic for network operations
4. **Progress Indicators**: Show progress for long-running operations

### Resource Management
1. **Monitor Usage**: Track CPU, memory, and disk usage
2. **Set Limits**: Configure appropriate resource constraints
3. **Cleanup**: Remove temporary files and unused packages
4. **Optimization**: Use efficient package managers and installation methods

## Emergency Procedures

### Workspace Recovery
```bash
# Force restart container
docker restart <container_name>

# Recreate workspace from template
# Use Coder UI or API to recreate

# Check system resources
./debug_startup.sh
```

### System Recovery
```bash
# Restart Docker service
sudo systemctl restart docker

# Check system resources
free -h
df -h

# Verify network connectivity
ping 8.8.8.8
```

### Data Recovery
```bash
# Backup container data
docker cp <container_name>:/home/coder ./backup/

# Check volume mounts
docker inspect <container_name> | grep -A 10 "Mounts"
```

## Support and Escalation

### Self-Service Tools
1. **Debug Scripts**: Use provided debugging utilities
2. **Monitoring**: Regular performance monitoring
3. **Documentation**: Refer to this troubleshooting guide

### Escalation Path
1. **Check Logs**: Review all relevant log files
2. **Document Issues**: Record symptoms and attempted solutions
3. **Contact Support**: Provide detailed error information and logs

### Information to Collect
- Error messages and stack traces
- Log file contents
- System resource usage
- Network connectivity status
- Container configuration
- Steps to reproduce the issue

---

**Last Updated**: $(date)
**Version**: 1.0
**Maintainer**: DevOps Team
