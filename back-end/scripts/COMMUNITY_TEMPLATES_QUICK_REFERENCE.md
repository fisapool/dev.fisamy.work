# Community Templates Quick Reference

## bpmct/coder-templates (Most Comprehensive)

### 🐳 Docker Templates
- **`docker-limits/`** - Resource constraints, quotas, volume management
  - Key: CPU shares, memory limits, disk quotas, health checks
  - Use case: Production environments with strict resource limits
  
- **`docker-with-dind/`** - Docker-in-Docker capabilities
  - Key: Nested Docker containers, CI/CD workflows
  - Use case: Build and test Docker images within workspaces
  
- **`docker-with-sysbox/`** - Enhanced container runtime
  - Key: Better isolation, security, nested virtualization
  - Use case: When you need more container capabilities than standard Docker

### 🖥️ Desktop & GUI
- **`desktop-container/`** - VNC desktop environments
  - Key: Full desktop GUI, VNC access, custom Dockerfiles
  - Use case: GUI applications, desktop development tools
  
- **`better-vnc/`** - Improved VNC implementation
  - Key: Better performance, multiple display support
  - Use case: High-performance remote desktop needs

### ☁️ Cloud & Infrastructure
- **`aws-linux-ephemeral/`** - AWS EC2 with ephemeral storage
- **`aws-macos/`** - AWS macOS instances
- **`aws-spot/`** - Cost-optimized AWS spot instances
- **`gcp-devcontainer/`** - Google Cloud development containers

### 🚀 Kubernetes & Orchestration
- **`kubernetes/`** - Basic K8s deployment
- **`kubernetes-multi-cluster/`** - Multi-cluster management
- **`kubernetes-namespace/`** - Namespace isolation
- **`k8s-multi-jetbrains/`** - Multiple JetBrains IDEs on K8s

### 🔧 Development Tools
- **`matlab/`** - MATLAB development environment
- **`projector-container/`** - JetBrains Projector support
- **`multi-projector-pod/`** - Multiple Projector instances

## coder/community-templates (Official)

### 🐳 Container Templates
- **`aws-ecs-container/`** - AWS ECS container deployment
- **`kubernetes-podman/`** - K8s with Podman runtime

### 📋 Template Structure
- **`.sample/`** - Basic template structure
- **`new.sh`** - Template creation script

## Key Features to Adopt

### 1. Resource Management (from docker-limits)
```hcl
# CPU balancing
cpu_shares = 1024

# Memory limits  
memory = 4096

# Disk quotas
storage_opts = {
  size = "10G"
}
```

### 2. Health Checks (from docker-limits)
```hcl
healthcheck {
  url       = "http://localhost:13337/healthz"
  interval  = 5
  threshold = 6
}
```

### 3. Volume Management (from docker-limits)
```hcl
resource "docker_volume" "home_volume" {
  name = "coder-${data.coder_workspace.me.id}-home"
  driver_opts = {
    size = "10G"
  }
}
```

### 4. Proper Labeling (from docker-limits)
```hcl
labels {
  label = "coder.owner"
  value = data.coder_workspace.me.owner
}
```

## Template Selection Guide

### For Your Current Setup:
1. **Start with:** `docker-limits/` - Learn resource management
2. **Then explore:** `desktop-container/` - If you need GUI support
3. **Consider:** `docker-with-dind/` - If you need nested Docker

### For Production:
1. **Resource management:** `docker-limits/` patterns
2. **Security:** `docker-with-sysbox/` approach
3. **Monitoring:** Health check patterns from any template

### For Development:
1. **Quick start:** `.sample/` from official repo
2. **Customization:** `desktop-container/` Dockerfile patterns
3. **Integration:** Module usage from official templates

## Getting Started Commands

```bash
# Explore docker-limits (most relevant)
cd community-templates-bpmct/docker-limits
cat main.tf | head -50

# Check desktop-container
cd ../desktop-container
cat README.md | head -30

# Look at official sample
cd ../../community-templates-official/.sample
cat main.tf
```

## Next Steps

1. **Study `docker-limits/`** - Understand resource management
2. **Examine `desktop-container/`** - Learn Dockerfile patterns  
3. **Review `.sample/`** - See official template structure
4. **Apply patterns** - Enhance your current templates
5. **Plan migration** - Consider HCL-based approach

## Repository URLs
- **bpmct/coder-templates:** https://github.com/bpmct/coder-templates
- **coder/community-templates:** https://github.com/coder/community-templates
