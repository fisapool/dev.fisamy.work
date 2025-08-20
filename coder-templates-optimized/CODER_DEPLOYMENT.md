# 🚀 Coder Deployment Guide

## 📥 **Uploading to Coder**

### **Step 1: Prepare the Package**
```bash
# The package is already prepared as coder-templates-optimized/
# It contains all necessary files for deployment
```

### **Step 2: Upload to Coder**
1. **Access your Coder instance** at your Coder URL
2. **Navigate to Templates** section
3. **Click "Create Template"** or "Upload Template"
4. **Select the template directory** (`docker-distracted_lamport8/`)
5. **Choose template type**: Docker
6. **Set template name**: `docker-optimized` or your preferred name

### **Step 3: Configure Template Settings**
```yaml
# Template Configuration
Name: docker-optimized
Description: Production-ready Docker templates with advanced error handling
Type: Docker
Icon: 🐳
```

## 🔧 **Template Variants**

### **No-GPU Template**
- **Use case**: General development, web development, non-ML workloads
- **Resources**: 4GB RAM, 2 CPU cores
- **Features**: VS Code, health monitoring, comprehensive logging

### **GPU Template**
- **Use case**: Machine learning, data science, GPU-accelerated workloads
- **Resources**: 16GB RAM, 4 CPU cores, NVIDIA GPU
- **Features**: VS Code, Jupyter Lab, PyTorch GPU support, CUDA 12.4.1

## 🚀 **Creating Workspaces**

### **From Coder UI**
1. **Click "Create Workspace"**
2. **Select your uploaded template**
3. **Choose template variant** (no-gpu or gpu)
4. **Configure workspace settings**:
   - **Name**: Your workspace name
   - **Autostop**: 2 hours (7200000ms)
   - **Resource limits**: As defined in template
5. **Click "Create Workspace"**

### **From Coder CLI**
```bash
# Install Coder CLI
curl -L https://coder.com/install.sh | sh

# Login to your Coder instance
coder login https://your-coder-instance.com

# Create workspace
coder create --template docker-optimized --name my-workspace

# List workspaces
coder list

# Connect to workspace
coder ssh my-workspace
```

## 📊 **Monitoring Workspace Health**

### **Health Check Endpoints**
- **Port 13133**: Health server with JSON responses
- **Port 13337**: VS Code server
- **Port 8888**: Jupyter Lab (GPU template only)

### **Health Check Commands**
```bash
# Check health endpoint
curl http://localhost:13133

# Expected response:
{
  "status": "ok",
  "template": "no-gpu|gpu",
  "timestamp": "2025-08-19T07:55:00Z"
}
```

### **Log Monitoring**
```bash
# Startup script logs
tail -f /tmp/coder-startup-script.log

# Health server logs
tail -f /tmp/health-server.log

# VS Code logs
tail -f ~/.local/share/code-server/logs/*.log
```

## 🔍 **Troubleshooting in Coder**

### **Common Issues**

#### **1. Workspace Stuck in "Starting" State**
```bash
# Check startup logs
tail -f /tmp/coder-startup-script.log

# Look for error messages or timeout issues
# Default timeout is 300 seconds
```

#### **2. Health Checks Failing**
```bash
# Check if health server is running
ps aux | grep python3

# Test health endpoint
curl -v http://localhost:13133

# Check port availability
ss -tuln | grep :13133
```

#### **3. GPU Not Available (GPU Template)**
```bash
# Check GPU availability
nvidia-smi

# Verify PyTorch GPU support
python3 -c "import torch; print(torch.cuda.is_available())"

# Check Docker GPU runtime
docker info | grep nvidia
```

### **Debugging Commands**
```bash
# Check system resources
free -h
df -h
top

# Check Docker containers
docker ps
docker stats

# Check network connectivity
ss -tuln
curl -I http://localhost:13133
```

## 📈 **Performance Optimization**

### **Startup Time Optimization**
- **Target**: <5 minutes for full startup
- **Monitoring**: Use startup script logs to track progress
- **Optimization**: Package pre-installation for common tools

### **Resource Usage Monitoring**
```bash
# Monitor resource usage
docker stats

# Check memory usage
cat /proc/meminfo | grep MemAvailable

# Monitor CPU usage
top -bn1 | grep "Cpu(s)"
```

### **Health Check Optimization**
- **Interval**: 5 seconds (configurable)
- **Timeout**: 3 seconds (configurable)
- **Retries**: 6 attempts before marking unhealthy

## 🔄 **Template Updates**

### **Updating Existing Templates**
1. **Backup current template** configuration
2. **Upload new template version**
3. **Test with new workspace** before updating production
4. **Update existing workspaces** if needed

### **Version Control**
- **Track template changes** in version control
- **Document configuration updates**
- **Test changes** in development environment
- **Rollback plan** for failed updates

## 📋 **Best Practices**

### **Template Management**
- **Use descriptive names** for templates
- **Document template purpose** and requirements
- **Test templates** before production use
- **Monitor template performance** regularly

### **Workspace Management**
- **Set appropriate autostop** times
- **Monitor resource usage** patterns
- **Clean up unused workspaces** regularly
- **Use resource limits** appropriately

### **Monitoring and Alerting**
- **Set up health check monitoring**
- **Alert on workspace failures**
- **Track performance metrics**
- **Monitor resource utilization**

## 🎯 **Success Metrics**

### **Template Performance**
- **Startup success rate**: >95%
- **Average startup time**: <5 minutes
- **Health check response**: <100ms
- **Resource utilization**: Optimized for efficiency

### **User Experience**
- **Workspace creation success**: >98%
- **Error resolution time**: <15 minutes
- **User satisfaction**: High ratings
- **Support ticket reduction**: >50%

## 🆘 **Getting Help**

### **Self-Service Resources**
1. **Check workspace logs** for error details
2. **Use health endpoints** to verify status
3. **Review template configuration** for issues
4. **Check system resources** for constraints

### **Escalation Process**
1. **Gather error logs** and status information
2. **Document issue details** and steps to reproduce
3. **Check troubleshooting guide** for solutions
4. **Contact support** with comprehensive information

---

**Deployment Status**: ✅ **Ready for Production**  
**Last Updated**: $(date)  
**Template Version**: 1.0  
**Coder Compatibility**: 0.20+
