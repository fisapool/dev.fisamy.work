# Coder Terraform Configuration

## ⚠️ **Deprecated - No Longer Functional**

**This Terraform configuration is no longer functional due to significant changes in the Coder provider.**

## 🔄 **What Changed**

The Coder Terraform provider has evolved and no longer supports:
- ❌ Template management (`coder_template`)
- ❌ Organization management (`coder_organization`)
- ❌ Direct Docker provisioner configuration

## 🆕 **Current Provider Capabilities**

The modern Coder provider now supports:
- ✅ **Workspace-specific configurations** (`coder_agent`, `coder_app`)
- ✅ **Environment variables** and **metadata** (`coder_env`, `coder_metadata`)
- ✅ **Custom scripts** (`coder_script`)
- ✅ **Individual workspace management**

## 🚀 **Recommended Approach**

Instead of using Terraform for templates:

1. **Create templates manually** through the Coder UI at `https://coder.fisamy.work/templates`
2. **Use Terraform for workspace-specific configurations** after templates are created
3. **Manage infrastructure** through Coder's built-in tools

## 📋 **Template Requirements**

### **No-GPU Template**
- Name: `no-gpu`
- Image: `ubuntu:22.04`
- CPU: 2, Memory: 4GB
- TTL: 1 hour
- Apps: VS Code on port 13337

### **GPU Template**
- Name: `gpu`
- Image: `nvidia/cuda:12.4.1-runtime-ubuntu22.04`
- CPU: 8, Memory: 16GB, GPU: 1
- TTL: 2 hours
- Apps: Jupyter on port 8888, VS Code on port 13337

## 🔧 **Future Terraform Usage**

Once templates are created manually, you can use Terraform for:

```hcl
# Example: Workspace-specific configuration
resource "coder_agent" "main" {
  arch = "amd64"
  os   = "linux"
}

resource "coder_app" "code-server" {
  agent_id = coder_agent.main.id
  name     = "code-server"
  url      = "http://localhost:13337"
}
```

## 📚 **Resources**

- [Coder Documentation](https://coder.com/docs)
- [Coder Terraform Provider](https://registry.terraform.io/providers/coder/coder/latest/docs)
- [Template Management](https://coder.com/docs/templates)

---

**Note**: This directory is kept for reference but should not be used for deployment. Use the deployment script in `../scripts/deploy_coder_infra.sh` instead.

