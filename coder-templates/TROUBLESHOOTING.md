# Troubleshooting Guide for Coder Templates

This guide helps you resolve common issues when using our no-gpu and gpu templates.

## 🚨 **Common Issues & Solutions**

### **1. Agent Connection Issues**

**Problem**: `coder ssh myworkspace` shows "Waiting for connection from [agent]..."

**Solutions**:
- Check if the resource has `curl` installed (our templates install this)
- Verify the resource can reach your Coder access URL
- Check agent logs: `/tmp/coder-agent.log`
- Check startup script logs: `/tmp/coder-startup-script.log`

**Debug Commands**:
```bash
# Check if curl is available
which curl

# Test network connectivity
curl -s --max-time 10 https://httpbin.org/get

# Check agent logs
tail -f /tmp/coder-agent.log
```

### **2. Startup Script Issues**

**Problem**: Workspace shows "may be incomplete" warning

**Solutions**:
- Our templates use **non-blocking** startup scripts
- You can access the workspace while startup is running
- Check startup logs for specific errors

**Debug Commands**:
```bash
# Check startup script logs
tail -f /tmp/coder-startup-script.log
tail -f /var/log/template-startup.log

# Check if services are running
pgrep -f "code-server"
pgrep -f "jupyter"

# Check port status
netstat -tlnp | grep ":13337"
netstat -tlnp | grep ":8888"
netstat -tlnp | grep ":13133"
```

### **3. Service Not Starting**

**Problem**: VS Code or Jupyter not accessible

**Solutions**:
- Check service logs in `/home/coder/`
- Verify port bindings
- Check user permissions

**Debug Commands**:
```bash
# Check service logs
tail -f /home/coder/code-server.log
tail -f /home/coder/jupyter.log

# Check service status
ps aux | grep code-server
ps aux | grep jupyter

# Test health endpoint
curl http://localhost:13133
```

### **4. GPU Template Issues**

**Problem**: CUDA/GPU not working

**Solutions**:
- Verify NVIDIA drivers are installed
- Check GPU availability
- Test PyTorch CUDA support

**Debug Commands**:
```bash
# Check GPU status
nvidia-smi

# Test CUDA availability
python3 -c "import torch; print(torch.cuda.is_available())"

# Check CUDA version
nvcc --version
```

### **5. Package Installation Issues**

**Problem**: apt-get or pip fails

**Solutions**:
- Check network connectivity
- Verify package sources
- Check disk space

**Debug Commands**:
```bash
# Check disk space
df -h

# Check network
ping -c 3 8.8.8.8

# Check package sources
cat /etc/apt/sources.list
```

## 🔍 **Log Locations**

Our templates create logs in multiple locations:

- **Startup Script**: `/tmp/coder-startup-script.log`
- **Template Logs**: `/var/log/template-startup.log`
- **VS Code**: `/home/coder/code-server.log`
- **Jupyter**: `/home/coder/jupyter.log`
- **Coder Agent**: `/tmp/coder-agent.log`

## 🛠️ **Manual Recovery Steps**

### **If Startup Script Fails**:

1. **Access via web terminal** (always available)
2. **Check logs** for specific errors
3. **Manually run commands** from startup script
4. **Restart services** if needed

### **If Services Won't Start**:

```bash
# Restart code-server
sudo -u coder bash -lc "code-server --bind-addr 0.0.0.0:13337 --auth none"

# Restart Jupyter (GPU template only)
sudo -u coder bash -lc "jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root --NotebookApp.token=''"
```

### **If User Issues**:

```bash
# Recreate coder user if needed
userdel -r coder
useradd -m coder
mkdir -p /home/coder/{projects,data,config}
chown -R coder:coder /home/coder
```

## 📋 **Health Check Commands**

Run these to verify your workspace is healthy:

```bash
# Check all services
pgrep -f "code-server" && echo "VS Code: OK" || echo "VS Code: FAILED"
pgrep -f "jupyter" && echo "Jupyter: OK" || echo "Jupyter: FAILED"
netstat -tlnp | grep ":13133" && echo "Health: OK" || echo "Health: FAILED"

# Check resources
free -h
df -h /
nvidia-smi 2>/dev/null || echo "No GPU detected"

# Test endpoints
curl -s http://localhost:13133 | jq . 2>/dev/null || echo "Health endpoint failed"
```

## 🖥️ **Using Cursor IDE with Coder Workspaces**

Cursor is a modern IDE built on top of VS Code with enhanced AI capabilities that can connect to your Coder workspaces.

### **Installation & Setup**

1. **Install Cursor** on your local machine
2. **Open Cursor** and log in or create a Cursor account
3. **Install the Coder extension**:
   - Search for "Coder" in the Extensions pane
   - Select Install
   - The extension includes Remote - SSH support

### **Connecting to Workspaces**

1. **From Command Palette** (`Ctrl+Shift+P` or `Cmd+Shift+P`):
   - Enter `coder` and select `Coder: Login`
   - Follow prompts to login and copy your session token
   - Paste the session token in the "Paste your API key" box
   - Select "Open Workspace" or use `Coder: Open Workspace`

2. **Alternative Connection**:
   - Use the Coder extension's built-in workspace browser
   - Select your desired workspace to open

### **Benefits of Using Cursor**

- **AI-powered coding assistance** with your remote Coder environment
- **Full VS Code compatibility** with all extensions
- **Seamless remote development** experience
- **Enhanced productivity** with AI code completion and suggestions

### **Troubleshooting Cursor Connection**

**If connection fails**:
- Verify your Coder session token is valid
- Check that your Coder instance is accessible from your network
- Ensure the Coder extension is properly installed
- Try re-authenticating with `Coder: Login`

## 🆘 **Still Having Issues?**

1. **Check the logs** - they contain detailed error information
2. **Verify resource requirements** - ensure your Coder instance has enough resources
3. **Check Coder version** - ensure you're running a recent version
4. **Review network policies** - ensure outbound internet access is allowed

## 📚 **Additional Resources**

- [Coder Troubleshooting Docs](https://coder.com/docs/v2/admin/troubleshooting)
- [Startup Script Best Practices](https://coder.com/docs/v2/admin/templates/startup-scripts)
- [Template Configuration](https://coder.com/docs/v2/admin/templates)
