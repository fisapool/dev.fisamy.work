# 🚀 Coder Template Setup Guide

This guide will help you create the required `no-gpu` and `gpu` templates in Coder manually.

## 📋 Prerequisites

- Coder instance running and accessible
- Admin access to Coder
- Docker provisioner enabled
- GPU support configured (for GPU template)

## 🔧 Template 1: no-gpu (Basic Development)

### Step 1: Create Template
1. Navigate to **Templates** in your Coder dashboard
2. Click **Create Template**
3. Choose **Docker** as the provisioner
4. Set the following values:

**Basic Settings:**
- **Name**: `no-gpu`
- **Display Name**: `No GPU Environment`
- **Description**: `Basic development environment without GPU for general development work`
- **Icon**: `vscode`
- **Default TTL**: `1 hour`
- **Max TTL**: `24 hours`

**Docker Configuration:**
- **Image**: `ubuntu:22.04`
- **CPU**: `2`
- **Memory**: `4 GiB`
- **Disk**: `10 GiB`
- **Startup Script**: Copy content from `startup.sh`
- **Startup Script Behavior**: `Non-blocking`

### Step 2: Add Version
1. Click **Add Version**
2. Set **Name**: `v1.0.0`
3. Copy the startup script content from `startup.sh`
4. Set **Startup Script Behavior**: `Non-blocking`

### Step 3: Configure Apps
1. Click **Add App**
2. Configure VS Code app:
   - **Name**: `VS Code`
   - **URL**: `http://localhost:13337`
   - **Icon**: `vscode`
   - **Subdomain**: `enabled`
   - **Sharing**: `owner`
   - **Health Check**: `http://localhost:13133`

### Step 4: Set Variables
1. Click **Add Variable**
2. Add workspace name variable:
   - **Name**: `WORKSPACE_NAME`
   - **Description**: `Name for the workspace`
   - **Type**: `string`
   - **Required**: `true`
   - **Default Value**: `dev-workspace`

## 🔧 Template 2: gpu (AI Development)

### Step 1: Create Template
1. Navigate to **Templates** in your Coder dashboard
2. Click **Create Template**
3. Choose **Docker** as the provisioner
4. Set the following values:

**Basic Settings:**
- **Name**: `gpu`
- **Display Name**: `GPU Environment`
- **Description**: `CUDA-enabled development environment for AI workloads and machine learning`
- **Icon**: `gpu`
- **Default TTL**: `2 hours`
- **Max TTL**: `24 hours`

**Docker Configuration:**
- **Image**: `nvidia/cuda:12.4.1-runtime-ubuntu22.04`
- **CPU**: `8`
- **Memory**: `16 GiB`
- **Disk**: `20 GiB`
- **GPU**: `1`
- **Startup Script**: Copy content from `startup.sh`
- **Startup Script Behavior**: `Non-blocking`
- **Environment Variables**:
  - `NVIDIA_VISIBLE_DEVICES=all`
  - `NVIDIA_DRIVER_CAPABILITIES=all`

### Step 2: Add Version
1. Click **Add Version**
2. Set **Name**: `v1.0.0`
3. Copy the startup script content from `startup.sh`
4. Set **Startup Script Behavior**: `Non-blocking`

### Step 3: Configure Apps
1. **VS Code App**:
   - **Name**: `VS Code`
   - **URL**: `http://localhost:13337`
   - **Icon**: `vscode`
   - **Subdomain**: `enabled`
   - **Sharing**: `owner`
   - **Health Check**: `http://localhost:13133`

2. **Jupyter Lab App**:
   - **Name**: `Jupyter Lab`
   - **URL**: `http://localhost:8888`
   - **Icon**: `jupyter`
   - **Subdomain**: `enabled`
   - **Sharing**: `owner`
   - **Health Check**: `http://localhost:8888`

### Step 4: Set Variables
1. **Workspace Name**:
   - **Name**: `WORKSPACE_NAME`
   - **Description**: `Name for the workspace`
   - **Type**: `string`
   - **Required**: `true`
   - **Default Value**: `ai-workspace`

2. **GPU Count**:
   - **Name**: `GPU_COUNT`
   - **Description**: `Number of GPUs to allocate`
   - **Type**: `number`
   - **Required**: `false`
   - **Default Value**: `1`
   - **Min**: `1`
   - **Max**: `4`

## ✅ Validation Steps

After creating both templates:

1. **Test Template Creation**:
   - Create a workspace from each template
   - Verify the startup script runs successfully
   - Check that apps are accessible

2. **Test Resource Allocation**:
   - Verify CPU, memory, and disk limits
   - For GPU template: verify GPU is accessible

3. **Test App Functionality**:
   - VS Code should be accessible on port 13337
   - Jupyter Lab should be accessible on port 8888 (GPU template only)
   - Health endpoint should respond on port 13133

## 🚨 Troubleshooting

### Common Issues

1. **Startup Script Fails**:
   - Check logs in the workspace
   - Verify the startup script has proper permissions
   - Ensure all required packages are available

2. **Apps Not Accessible**:
   - Verify ports are correctly configured
   - Check firewall settings
   - Ensure health checks are passing

3. **GPU Not Available**:
   - Verify NVIDIA drivers are installed on the host
   - Check Docker GPU runtime configuration
   - Ensure the CUDA image is compatible

### Logs and Debugging

- **Startup Logs**: Check `/tmp/coder-startup-script.log`
- **Application Logs**: Check `/var/log/template-startup.log`
- **Health Endpoint**: Test `http://localhost:13133`

## 🔄 Next Steps

After successful template creation:

1. **Test with Real Users**: Create test workspaces and verify functionality
2. **Monitor Performance**: Use the monitoring scripts to track resource usage
3. **Customize Further**: Adjust resource limits and configurations as needed
4. **Document Usage**: Create user guides for your team

## 📚 Additional Resources

- [Coder Documentation](https://coder.com/docs)
- [Docker Provisioner Guide](https://coder.com/docs/v0.25/admin/provisioners/docker)
- [Template Best Practices](https://coder.com/docs/v0.25/admin/templates)
- [GPU Support Guide](https://coder.com/docs/v0.25/admin/provisioners/docker#gpu-support)
