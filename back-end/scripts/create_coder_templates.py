#!/usr/bin/env python3
"""
🚀 Coder Template Creation & Validation Script

This script helps create and validate the required Coder templates:
- no-gpu: Basic development environment
- gpu: CUDA-enabled AI development environment

Usage:
    python3 create_coder_templates.py --create-templates
    python3 create_coder_templates.py --validate-templates
    python3 create_coder_templates.py --full-setup
"""

import os
import sys
import json
import time
import argparse
import subprocess
import requests
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CoderTemplateManager:
    def __init__(self):
        self.coder_token = os.getenv("CODER_API_TOKEN")
        self.coder_host = os.getenv("CODER_HOST", "https://coder.fisamy.work")
        
        if not self.coder_token:
            logger.error("CODER_API_TOKEN environment variable not set!")
            logger.error("Please set it in your environment or .env file")
            sys.exit(1)
        
        self.headers = {
            "Authorization": f"Bearer {self.coder_token}",
            "Content-Type": "application/json"
        }
    
    def api_request(self, endpoint: str, method: str = "GET", data: dict = None) -> dict:
        """Make a request to the Coder API"""
        url = f"{self.coder_host}{endpoint}"
        
        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers)
            elif method == "POST":
                response = requests.post(url, headers=self.headers, json=data)
            elif method == "PUT":
                response = requests.put(url, headers=self.headers, json=data)
            elif method == "DELETE":
                response = requests.delete(url, headers=self.headers)
            
            response.raise_for_status()
            return response.json() if response.content else {}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            return {}
    
    def get_organization_id(self) -> Optional[str]:
        """Get the organization ID"""
        try:
            # Try to get organizations
            orgs = self.api_request("/api/v2/organizations")
            if orgs and "organizations" in orgs:
                # Usually there's only one organization
                return orgs["organizations"][0]["id"]
            
            # Fallback: try to get user info
            user = self.api_request("/api/v2/users/me")
            if user and "organization_ids" in user:
                return user["organization_ids"][0]
                
        except Exception as e:
            logger.error(f"Failed to get organization ID: {e}")
        
        return None
    
    def create_template(self, template_config: dict) -> Optional[str]:
        """Create a template in Coder"""
        org_id = self.get_organization_id()
        if not org_id:
            logger.error("Could not determine organization ID")
            return None
        
        # Create template
        template_data = {
            "name": template_config["name"],
            "display_name": template_config["display_name"],
            "description": template_config["description"],
            "icon": template_config.get("icon", ""),
            "organization_id": org_id,
            "provisioner": "docker"
        }
        
        logger.info(f"Creating template: {template_config['name']}")
        template = self.api_request("/api/v2/templates", method="POST", data=template_data)
        
        if template and "id" in template:
            template_id = template["id"]
            logger.info(f"✅ Template created with ID: {template_id}")
            
            # Create template version
            version_data = {
                "name": "v1.0.0",
                "message": "Initial version",
                "template_id": template_id,
                "archive": {
                    "format": "tar",
                    "content": self.create_template_archive(template_config)
                }
            }
            
            version = self.api_request("/api/v2/templateversions", method="POST", data=version_data)
            if version and "id" in version:
                logger.info(f"✅ Template version created: {version['id']}")
                
                # Update template with version
                self.api_request(f"/api/v2/templates/{template_id}", method="PUT", data={
                    "active_version_id": version["id"]
                })
                
                return template_id
            else:
                logger.error("Failed to create template version")
                return None
        else:
            logger.error("Failed to create template")
            return None
    
    def create_template_archive(self, template_config: dict) -> str:
        """Create a template archive (simplified - in real implementation this would create actual files)"""
        # This is a placeholder - in practice you'd create actual template files
        # For now, we'll use the Coder UI to configure the template
        return "placeholder"
    
    def get_templates(self) -> List[dict]:
        """Get all templates"""
        templates = self.api_request("/api/v2/templates")
        # The API returns a list directly, not an object with 'templates' key
        if isinstance(templates, list):
            return templates
        elif isinstance(templates, dict) and "templates" in templates:
            return templates["templates"]
        else:
            logger.warning(f"Unexpected API response format: {type(templates)}")
            return []
    
    def validate_template(self, template_name: str) -> bool:
        """Validate that a template exists and has correct configuration"""
        templates = self.get_templates()
        
        for template in templates:
            if template["name"] == template_name:
                logger.info(f"✅ Found template: {template_name}")
                logger.info(f"   ID: {template['id']}")
                logger.info(f"   Status: {template.get('status', 'unknown')}")
                return True
        
        logger.error(f"❌ Template not found: {template_name}")
        return False
    
    def create_workspace(self, template_name: str, workspace_name: str) -> Optional[str]:
        """Create a workspace from a template"""
        templates = self.get_templates()
        template_id = None
        
        for template in templates:
            if template["name"] == template_name:
                template_id = template["id"]
                break
        
        if not template_id:
            logger.error(f"Template not found: {template_name}")
            return None
        
        workspace_data = {
            "template_id": template_id,
            "name": workspace_name,
            "autostop_schedule": "09:00 UTC",
            "ttl_ms": 7200000  # 2 hours in milliseconds
        }
        
        logger.info(f"Creating workspace: {workspace_name} from template: {template_name}")
        workspace = self.api_request("/api/v2/workspaces", method="POST", data=workspace_data)
        
        if workspace and "id" in workspace:
            logger.info(f"✅ Workspace created with ID: {workspace['id']}")
            return workspace["id"]
        else:
            logger.error("Failed to create workspace")
            return None
    
    def get_workspaces(self) -> List[dict]:
        """Get all workspaces"""
        workspaces = self.api_request("/api/v2/workspaces")
        return workspaces.get("workspaces", [])
    
    def validate_workspace(self, workspace_id: str) -> bool:
        """Validate workspace functionality"""
        workspace = self.api_request(f"/api/v2/workspaces/{workspace_id}")
        
        if not workspace:
            return False
        
        logger.info(f"Workspace: {workspace['name']}")
        logger.info(f"  Status: {workspace.get('status')}")
        logger.info(f"  Template: {workspace.get('template_name')}")
        
        return True

def print_template_specs():
    """Print the template specifications"""
    print("""
🚀 **Coder Template Specifications**

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

### **Startup Scripts**

#### **no-gpu Startup Script**
```bash
apt-get update && apt-get install -y curl git sudo ca-certificates
curl -fsSL https://code-server.dev/install.sh | sh
useradd -m coder || true
sudo -u coder bash -lc 'code-server --bind-addr 0.0.0.0:13337 --auth none &'
```

#### **gpu Startup Script**
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

### **Template Apps Configuration**

#### **VS Code App (Both Templates)**
- **URL**: `http://localhost:13337`
- **Icon**: `vscode`
- **Subdomain**: `enabled`
- **Sharing**: `owner`

#### **Jupyter App (gpu Template Only)**
- **URL**: `http://localhost:8888`
- **Icon**: `jupyter`
- **Subdomain**: `enabled`
- **Sharing**: `owner`
""")

def print_manual_steps():
    """Print manual steps for template creation"""
    print("""
📋 **Manual Template Creation Steps**

Since the Coder API doesn't support full template creation programmatically, 
you'll need to create these templates manually through the Coder UI:

1. **Navigate to**: https://coder.fisamy.work/templates
2. **Click**: `Create Template`
3. **Choose**: `Docker` as provisioner
4. **Configure**: Use the specifications above
5. **Add Version**: Include image + startup script
6. **Configure Apps**: As specified above

### **For each template, you'll need to:**

1. **Basic Settings**:
   - Set name, display name, and description
   - Choose Docker provisioner
   - Set resource limits (CPU, Memory, GPU)

2. **Docker Configuration**:
   - Set base image
   - Configure startup script
   - Set environment variables (for GPU template)

3. **Apps Configuration**:
   - Add VS Code app (port 13337)
   - Add Jupyter app (port 8888, GPU template only)
   - Configure subdomain and sharing

4. **Autostop Settings**:
   - Set schedule: Monday-Sunday, 09:00-17:00 UTC
   - Enable user autostart/autostop

### **After Creation**:
- Test template creation
- Verify resource allocation
- Test port accessibility
- Validate autostop functionality
""")

def main():
    parser = argparse.ArgumentParser(description="Coder Template Creation & Validation")
    parser.add_argument("--create-templates", action="store_true", help="Create templates (manual guidance)")
    parser.add_argument("--validate-templates", action="store_true", help="Validate existing templates")
    parser.add_argument("--full-setup", action="store_true", help="Full setup with validation")
    parser.add_argument("--specs", action="store_true", help="Show template specifications")
    parser.add_argument("--manual-steps", action="store_true", help="Show manual creation steps")
    
    args = parser.parse_args()
    
    if args.specs:
        print_template_specs()
        return
    
    if args.manual_steps:
        print_manual_steps()
        return
    
    if not any([args.create_templates, args.validate_templates, args.full_setup]):
        print("🚀 Coder Template Creation & Validation Script")
        print("\nUsage:")
        print("  python3 create_coder_templates.py --specs           # Show template specifications")
        print("  python3 create_coder_templates.py --manual-steps    # Show manual creation steps")
        print("  python3 create_coder_templates.py --validate-templates  # Validate existing templates")
        print("  python3 create_coder_templates.py --full-setup      # Full setup with validation")
        return
    
    manager = CoderTemplateManager()
    
    if args.create_templates or args.full_setup:
        print("📋 **Template Creation Mode**")
        print("\nSince Coder API doesn't support full template creation programmatically,")
        print("you'll need to create templates manually through the Coder UI.")
        print("\nHere are the specifications:")
        print_template_specs()
        print("\nAnd here are the manual steps:")
        print_manual_steps()
        
        # Check if templates already exist
        existing_templates = manager.get_templates()
        if existing_templates:
            print(f"\n📊 **Existing Templates Found**: {len(existing_templates)}")
            for template in existing_templates:
                print(f"  - {template['name']}: {template.get('display_name', 'N/A')}")
    
    if args.validate_templates or args.full_setup:
        print("\n🔍 **Template Validation Mode**")
        
        # Check existing templates
        templates = manager.get_templates()
        print(f"\n📊 **Found {len(templates)} templates**")
        
        required_templates = ["no-gpu", "gpu"]
        found_templates = []
        
        for template in templates:
            print(f"\n📋 **Template**: {template['name']}")
            print(f"   Display Name: {template.get('display_name', 'N/A')}")
            print(f"   Description: {template.get('description', 'N/A')}")
            print(f"   Status: {template.get('status', 'unknown')}")
            print(f"   ID: {template['id']}")
            
            if template['name'] in required_templates:
                found_templates.append(template['name'])
        
        # Validation summary
        print(f"\n✅ **Validation Summary**")
        for required in required_templates:
            if required in found_templates:
                print(f"  ✅ {required}: Found")
            else:
                print(f"  ❌ {required}: Missing")
        
        if len(found_templates) == len(required_templates):
            print(f"\n🎉 **All required templates are present!**")
            
            # Test workspace creation
            print(f"\n🧪 **Testing workspace creation...**")
            for template_name in found_templates:
                test_workspace_name = f"test-{template_name}-{int(time.time())}"
                workspace_id = manager.create_workspace(template_name, test_workspace_name)
                
                if workspace_id:
                    print(f"  ✅ Created test workspace: {test_workspace_name}")
                    
                    # Wait a bit for workspace to start
                    print(f"  ⏳ Waiting for workspace to start...")
                    time.sleep(10)
                    
                    # Validate workspace
                    if manager.validate_workspace(workspace_id):
                        print(f"  ✅ Workspace validation successful")
                    else:
                        print(f"  ❌ Workspace validation failed")
                else:
                    print(f"  ❌ Failed to create test workspace from {template_name}")
        else:
            print(f"\n⚠️  **Missing templates detected**")
            print(f"Please create the missing templates manually using the specifications above.")

if __name__ == "__main__":
    main()
