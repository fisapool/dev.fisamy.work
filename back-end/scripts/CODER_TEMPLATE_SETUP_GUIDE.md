# 🚀 Coder Template Creation & Validation Guide

## 📋 **Template Specifications**

### **Template 1: no-gpu (Basic Development)**
- **Name**: `no-gpu`
- **Display Name**: `No GPU Environment`
- **Description**: `Basic development environment without GPU`
- **Image**: `ubuntu:22.04`
- **CPU**: `2`
- **Memory**: `4GB`
- **Default TTL**: `1 hour`
- **Provisioner**: `Docker`

### **Template 2: gpu (AI Development)**
- **Name**: `gpu`
- **Display Name**: `GPU Environment`
- **Description**: `CUDA-enabled development environment for AI workloads`
- **Image**: `nvidia/cuda:12.4.1-runtime-ubuntu22.04`
- **CPU**: `8`
- **Memory**: `16GB`
- **GPU**: `1`
- **Default TTL**: `2 hours`
- **Provisioner**: `Docker`

## 🔧 **Startup Scripts**

### **no-gpu Startup Script**
```bash
apt-get update && apt-get install -y curl git sudo ca-certificates
curl -fsSL https://code-server.dev/install.sh | sh
useradd -m coder || true
sudo -u coder bash -lc 'code-server --bind-addr 0.0.0.0:13337 --auth none &'
```

### **gpu Startup Script**
```bash
apt-get update && apt-get install -y python3 python3-venv python3-pip curl git sudo ca-certificates
python3 -m venv /opt/venv && . /opt/venv/bin/activate
pip install --upgrade pip wheel
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
pip install jupyter jupyterlab numpy pandas matplotlib
curl -fsSL https://code-server.dev/install.sh | sh
useradd -m coder || true
sudo -u coder bash -lc 'code-server --bind-addr 0.0.0.0:13337 --auth none &'
nohup bash -lc 'source /opt/venv/bin/activate && jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --NotebookApp.token="" --NotebookApp.password="" &' >/dev/null 2>&1
```

## 🌐 **Template Apps Configuration**

### **VS Code App (Both Templates)**
- **URL**: `http://localhost:13337`
- **Icon**: `vscode`
- **Subdomain**: `enabled`
- **Sharing**: `owner`

### **Jupyter App (gpu Template Only)**
- **URL**: `http://localhost:8888`
- **Icon**: `jupyter`
- **Subdomain**: `enabled`
- **Sharing**: `owner`

## ⚙️ **GPU Settings (gpu Template)**

### **Docker Device Requests**
- **GPU**: `1` (or `all`)

### **Environment Variables**
- `NVIDIA_VISIBLE_DEVICES=all`
- `NVIDIA_DRIVER_CAPABILITIES=all`

### **Autostop Configuration**
- **Days**: Monday–Sunday
- **Start Time**: 09:00 UTC
- **Stop Time**: 17:00 UTC
- **Timezone**: UTC
- **Allow user autostart/autostop**: `enabled`

## 🎯 **Creation Steps**

### **Step 1: Access Coder Templates**
1. **Navigate to**: `https://coder.fisamy.work/templates`
2. **Click**: `Create Template`
3. **Choose**: `Docker` as provisioner

### **Step 2: Create no-gpu Template**

#### **Basic Settings**
- **Name**: `no-gpu`
- **Display Name**: `No GPU Environment`
- **Description**: `Basic development environment without GPU`
- **Icon**: Leave default or choose appropriate icon

#### **Docker Configuration**
- **Base Image**: `ubuntu:22.04`
- **Startup Script**: Copy the no-gpu startup script above
- **CPU**: `2`
- **Memory**: `4GB`
- **Default TTL**: `1 hour`

#### **Apps Configuration**
- **Add App**: VS Code
  - **Name**: `VS Code`
  - **URL**: `http://localhost:13337`
  - **Icon**: `vscode`
  - **Subdomain**: `enabled`
  - **Sharing**: `owner`

#### **Autostop Settings**
- **Schedule**: Monday–Sunday, 09:00-17:00 UTC
- **Allow user autostart/autostop**: `enabled`

### **Step 3: Create gpu Template**

#### **Basic Settings**
- **Name**: `gpu`
- **Display Name**: `GPU Environment`
- **Description**: `CUDA-enabled development environment for AI workloads`
- **Icon**: Leave default or choose appropriate icon

#### **Docker Configuration**
- **Base Image**: `nvidia/cuda:12.4.1-runtime-ubuntu22.04`
- **Startup Script**: Copy the gpu startup script above
- **CPU**: `8`
- **Memory**: `16GB`
- **GPU**: `1`
- **Default TTL**: `2 hours`

#### **Environment Variables**
- `NVIDIA_VISIBLE_DEVICES=all`
- `NVIDIA_DRIVER_CAPABILITIES=all`

#### **Apps Configuration**
- **Add App 1**: VS Code
  - **Name**: `VS Code`
  - **URL**: `http://localhost:13337`
  - **Icon**: `vscode`
  - **Subdomain**: `enabled`
  - **Sharing**: `owner`

- **Add App 2**: Jupyter
  - **Name**: `Jupyter`
  - **URL**: `http://localhost:8888`
  - **Icon**: `jupyter`
  - **Subdomain**: `enabled`
  - **Sharing**: `owner`

#### **Autostop Settings**
- **Schedule**: Monday–Sunday, 09:00-17:00 UTC
- **Allow user autostart/autostop**: `enabled`

## ✅ **End-to-End Validation**

### **Template Creation Validation**
- [ ] Both templates appear in `/templates` list
- [ ] Template names match exactly: `no-gpu` and `gpu`
- [ ] Resource limits are correctly set

### **Workspace Creation Validation**

#### **no-gpu Template Test**
- [ ] Create workspace from `no-gpu` template
- [ ] Confirm VS Code opens on port 13337
- [ ] Inside workspace: `ss -ltnp | grep 13337` shows listening port

#### **gpu Template Test**
- [ ] Create workspace from `gpu` template
- [ ] Confirm Jupyter opens on port 8888
- [ ] Confirm VS Code opens on port 13337
- [ ] Verify GPU access: `nvidia-smi`
- [ ] Test PyTorch CUDA: `python3 -c "import torch; print(torch.cuda.is_available())"`

### **Dashboard Integration Validation**
- [ ] With `CODER_API_TOKEN` set, BFF `/templates` endpoint shows new templates
- [ ] BFF `/workspaces` endpoint reflects created workspaces
- [ ] Template resources are properly allocated

## 🔍 **Troubleshooting Commands**

### **Port Verification**
```bash
# Check if services are listening
ss -ltnp | grep -E "(13337|8888)"

# Check container logs
docker logs <workspace-container-id>
```

### **GPU Verification**
```bash
# Check GPU availability
nvidia-smi

# Test PyTorch CUDA
python3 -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

### **Service Status**
```bash
# Check code-server process
ps aux | grep code-server

# Check Jupyter process
ps aux | grep jupyter
```

## 🧪 **Automated Validation**

### **Using the Validation Scripts**

#### **Check Template Existence**
```bash
cd back-end/scripts
python3 validate_coder_templates.py --check-templates-only
```

#### **Test Workspace Functionality**
```bash
python3 validate_coder_templates.py --test-workspaces
```

#### **Full End-to-End Validation**
```bash
python3 validate_coder_templates.py --full-validation
```

### **Using the Template Creation Script**
```bash
cd back-end/scripts
python3 create_coder_templates.py --specs           # Show specifications
python3 create_coder_templates.py --manual-steps    # Show manual steps
python3 create_coder_templates.py --full-setup      # Full setup guidance
```

## 🎯 **Success Criteria**

- ✅ Both templates create workspaces successfully
- ✅ VS Code accessible on port 13337 (both templates)
- ✅ Jupyter accessible on port 8888 (gpu template only)
- ✅ GPU resources properly allocated (gpu template)
- ✅ Autostop functionality works as configured
- ✅ BFF dashboard shows templates and workspaces

## 🚨 **Common Issues & Solutions**

### **Template Creation Issues**
- **Problem**: Template creation fails
- **Solution**: Check Coder permissions and ensure Docker provisioner is available

### **Workspace Startup Issues**
- **Problem**: Workspace fails to start
- **Solution**: Check startup script syntax and Docker image availability

### **Port Accessibility Issues**
- **Problem**: Ports not accessible
- **Solution**: Verify app configuration and subdomain settings

### **GPU Issues**
- **Problem**: GPU not accessible in workspace
- **Solution**: Check NVIDIA Docker runtime and GPU device requests

---

**Ready to execute?** This guide provides everything needed to create and validate your Coder templates end-to-end.

## 📚 **Additional Resources**

- **Coder Documentation**: https://coder.com/docs
- **Docker Templates**: https://coder.com/docs/templates/docker
- **Template Examples**: https://github.com/coder/coder/tree/main/examples/templates
- **NVIDIA Docker**: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/
