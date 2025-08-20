# 🚀 Coder Template Scripts

This directory contains scripts to help you create, validate, and manage Coder templates for the Fisamy dashboard.

## 📁 **Files Overview**

- **`create_coder_templates.py`** - Template creation guidance and specifications
- **`validate_coder_templates.py`** - End-to-end template validation
- **`setup_coder_templates.sh`** - Interactive setup script
- **`CODER_TEMPLATE_SETUP_GUIDE.md`** - Comprehensive manual setup guide
- **`requirements.txt`** - Python dependencies for validation scripts

## 🚀 **Quick Start**

### **1. Interactive Setup (Recommended)**
```bash
cd back-end/scripts
./setup_coder_templates.sh
```

This script provides an interactive menu to:
- Show template specifications
- Display manual creation steps
- Check existing templates
- Test workspace functionality
- Run full validation

### **2. Manual Script Usage**

#### **Show Template Specifications**
```bash
python3 create_coder_templates.py --specs
```

#### **Show Manual Creation Steps**
```bash
python3 create_coder_templates.py --manual-steps
```

#### **Check Template Existence**
```bash
python3 validate_coder_templates.py --check-templates-only
```

#### **Test Workspace Functionality**
```bash
python3 validate_coder_templates.py --test-workspaces
```

#### **Run Full Validation**
```bash
python3 validate_coder_templates.py --full-validation
```

## ⚙️ **Prerequisites**

### **Environment Variables**
```bash
export CODER_API_TOKEN="your_coder_api_token_here"
export CODER_HOST="https://coder.fisamy.work"
```

### **Python Dependencies**
```bash
pip3 install -r requirements.txt
```

### **Important Directory Requirements**
The setup script **MUST** be run from the `back-end/scripts` directory, not from the `back-end` directory.

**Correct way:**
```bash
cd back-end/scripts
export CODER_API_TOKEN="your_coder_api_token_here"
export CODER_HOST="https://coder.fisamy.work"
./setup_coder_templates.sh
```

**Wrong way (will fail):**
```bash
cd back-end
./scripts/setup_coder_templates.sh  # ❌ This will fail
```

## 📋 **Required Templates**

### **no-gpu Template**
- Basic development environment
- 2 CPU cores, 4GB RAM
- VS Code on port 13337
- Ubuntu 22.04 base image

### **gpu Template**
- CUDA-enabled AI development environment
- 8 CPU cores, 16GB RAM, 1 GPU
- VS Code on port 13337 + Jupyter on port 8888
- NVIDIA CUDA 12.4.1 base image

## 🔧 **Template Creation Process**

Since Coder API doesn't support full template creation programmatically, you'll need to:

1. **Access Coder UI**: Go to `https://coder.fisamy.work/templates`
2. **Create Templates Manually**: Use the specifications from the scripts
3. **Configure Resources**: Set CPU, memory, GPU limits
4. **Add Apps**: Configure VS Code and Jupyter ports
5. **Set Autostop**: Configure 9 AM - 5 PM UTC schedule

## ✅ **Validation Process**

The validation scripts will:

1. **Check Template Existence**: Verify both templates are created
2. **Validate Configuration**: Check resource limits and settings
3. **Test Workspace Creation**: Create test workspaces from templates
4. **Verify Port Accessibility**: Test VS Code and Jupyter ports
5. **Test GPU Functionality**: Verify GPU access (for GPU template)
6. **Cleanup**: Remove test workspaces after validation

## 🚨 **Troubleshooting**

### **Common Issues**

#### **API Response Format Issues**
- **Problem**: Script fails with `'list' object has no attribute 'get'` error
- **Cause**: Coder API returns lists directly, not objects with nested keys
- **Solution**: Script has been updated to handle both response formats
- **Status**: ✅ **FIXED** - Script now handles API response format correctly

#### **Template Creation Fails**
- Check Coder permissions
- Ensure Docker provisioner is available
- Verify base images are accessible

#### **Workspace Startup Issues**
- Check startup script syntax
- Verify Docker image availability
- Check resource allocation

#### **Port Accessibility Issues**
- Verify app configuration
- Check subdomain settings
- Ensure services are running

#### **GPU Issues**
- Check NVIDIA Docker runtime
- Verify GPU device requests
- Test with `nvidia-smi` command

### **Debug Commands**
```bash
# Check workspace status
curl -H "Authorization: Bearer $CODER_API_TOKEN" "$CODER_HOST/api/v2/workspaces"

# Check template status
curl -H "Authorization: Bearer $CODER_API_TOKEN" "$CODER_HOST/api/v2/templates"

# Check container logs
docker logs <workspace-container-id>
```

## 📚 **Additional Resources**

- **Coder Documentation**: https://coder.com/docs
- **Docker Templates**: https://coder.com/docs/templates/docker
- **Template Examples**: https://github.com/coder/coder/tree/main/examples/templates
- **NVIDIA Docker**: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/

## 🎯 **Success Criteria**

Your setup is complete when:

- ✅ Both `no-gpu` and `gpu` templates exist
- ✅ Templates create workspaces successfully
- ✅ VS Code accessible on port 13337 (both templates)
- ✅ Jupyter accessible on port 8888 (GPU template only)
- ✅ GPU resources properly allocated (GPU template)
- ✅ Autostop functionality works as configured
- ✅ BFF dashboard shows templates and workspaces

---

**Need help?** Check the `CODER_TEMPLATE_SETUP_GUIDE.md` for detailed step-by-step instructions.
