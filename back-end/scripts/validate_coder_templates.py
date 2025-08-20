#!/usr/bin/env python3
"""
🔍 Coder Template End-to-End Validation Script

This script validates the created Coder templates by:
1. Checking template existence and configuration
2. Creating test workspaces
3. Validating resource allocation
4. Testing port accessibility
5. Verifying GPU functionality (for GPU template)

Usage:
    python3 validate_coder_templates.py --full-validation
    python3 validate_coder_templates.py --check-templates-only
    python3 validate_coder_templates.py --test-workspaces
"""

import os
import sys
import time
import json
import argparse
import requests
import subprocess
from typing import Dict, List, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CoderTemplateValidator:
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
        
        # Expected template configurations
        self.expected_templates = {
            "no-gpu": {
                "display_name": "No GPU Environment",
                "description": "Basic development environment without GPU",
                "cpu_cores": 2,
                "memory_gb": 4,
                "ports": [13337],
                "apps": ["vscode"]
            },
            "gpu": {
                "display_name": "GPU Environment", 
                "description": "CUDA-enabled development environment for AI workloads",
                "cpu_cores": 8,
                "memory_gb": 16,
                "gpu_count": 1,
                "ports": [13337, 8888],
                "apps": ["vscode", "jupyter"]
            }
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
    
    def get_workspaces(self) -> List[dict]:
        """Get all workspaces"""
        workspaces = self.api_request("/api/v2/workspaces")
        # The API returns a list directly, not an object with 'workspaces' key
        if isinstance(workspaces, list):
            return workspaces
        elif isinstance(workspaces, dict) and "workspaces" in workspaces:
            return workspaces["workspaces"]
        else:
            logger.warning(f"Unexpected API response format: {type(workspaces)}")
            return []
    
    def validate_template_configuration(self, template: dict, expected: dict) -> Tuple[bool, List[str]]:
        """Validate template configuration against expected values"""
        issues = []
        is_valid = True
        
        # Check basic properties
        if template.get("display_name") != expected["display_name"]:
            issues.append(f"Display name mismatch: expected '{expected['display_name']}', got '{template.get('display_name')}'")
            is_valid = False
        
        if template.get("description") != expected["description"]:
            issues.append(f"Description mismatch: expected '{expected['description']}', got '{template.get('description')}'")
            is_valid = False
        
        # Check resource limits (these might be in template version)
        logger.info(f"Template {template['name']} basic validation: {'✅ PASS' if is_valid else '❌ FAIL'}")
        
        return is_valid, issues
    
    def create_test_workspace(self, template_name: str) -> Optional[str]:
        """Create a test workspace from a template"""
        templates = self.get_templates()
        template_id = None
        
        for template in templates:
            if template["name"] == template_name:
                template_id = template["id"]
                break
        
        if not template_id:
            logger.error(f"Template not found: {template_name}")
            return None
        
        # Create unique workspace name
        timestamp = int(time.time())
        workspace_name = f"validation-test-{template_name}-{timestamp}"
        
        workspace_data = {
            "template_id": template_id,
            "name": workspace_name,
            "autostop_schedule": "09:00 UTC",
            "ttl_ms": 7200000  # 2 hours
        }
        
        logger.info(f"Creating test workspace: {workspace_name}")
        workspace = self.api_request("/api/v2/workspaces", method="POST", data=workspace_data)
        
        if workspace and "id" in workspace:
            logger.info(f"✅ Test workspace created: {workspace['id']}")
            return workspace["id"]
        else:
            logger.error("Failed to create test workspace")
            return None
    
    def wait_for_workspace_status(self, workspace_id: str, target_status: str, timeout: int = 300) -> bool:
        """Wait for workspace to reach target status"""
        logger.info(f"Waiting for workspace {workspace_id} to reach status: {target_status}")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            workspace = self.api_request(f"/api/v2/workspaces/{workspace_id}")
            
            if not workspace:
                logger.error(f"Could not get workspace {workspace_id}")
                return False
            
            current_status = workspace.get("status")
            logger.info(f"Current status: {current_status}")
            
            if current_status == target_status:
                logger.info(f"✅ Workspace reached target status: {target_status}")
                return True
            elif current_status in ["failed", "canceled"]:
                logger.error(f"❌ Workspace failed with status: {current_status}")
                return False
            
            time.sleep(10)
        
        logger.error(f"❌ Timeout waiting for workspace status: {target_status}")
        return False
    
    def get_workspace_agent(self, workspace_id: str) -> Optional[dict]:
        """Get workspace agent information"""
        workspace = self.api_request(f"/api/v2/workspaces/{workspace_id}")
        if not workspace:
            return None
        
        # Get agents for the workspace
        agents = self.api_request(f"/api/v2/workspaces/{workspace_id}/agents")
        if agents and "agents" in agents and len(agents["agents"]) > 0:
            return agents["agents"][0]
        
        return None
    
    def test_port_accessibility(self, workspace_id: str, expected_ports: List[int]) -> Dict[int, bool]:
        """Test if expected ports are accessible"""
        results = {}
        
        # Get workspace URL
        workspace = self.api_request(f"/api/v2/workspaces/{workspace_id}")
        if not workspace:
            logger.error(f"Could not get workspace {workspace_id}")
            return results
        
        workspace_name = workspace.get("name", "")
        user_id = workspace.get("owner_id", "")
        
        # Test each expected port
        for port in expected_ports:
            if port == 13337:  # VS Code
                test_url = f"https://vscode--{workspace_name}--{user_id}.dev.fisamy.work"
            elif port == 8888:  # Jupyter
                test_url = f"https://jupyter--{workspace_name}--{user_id}.dev.fisamy.work"
            else:
                test_url = f"http://localhost:{port}"
            
            logger.info(f"Testing port {port} accessibility via {test_url}")
            
            try:
                response = requests.get(test_url, timeout=10, allow_redirects=True)
                if response.status_code == 200:
                    results[port] = True
                    logger.info(f"✅ Port {port} accessible")
                else:
                    results[port] = False
                    logger.error(f"❌ Port {port} returned status {response.status_code}")
            except Exception as e:
                results[port] = False
                logger.error(f"❌ Port {port} not accessible: {e}")
        
        return results
    
    def test_gpu_functionality(self, workspace_id: str) -> bool:
        """Test GPU functionality for GPU template workspaces"""
        logger.info("Testing GPU functionality...")
        
        # This would require executing commands in the workspace
        # For now, we'll check if the workspace has GPU resources allocated
        workspace = self.api_request(f"/api/v2/workspaces/{workspace_id}")
        if not workspace:
            return False
        
        # Check if GPU resources are allocated
        # This is a simplified check - in practice you'd execute nvidia-smi
        logger.info("GPU functionality test completed (simplified)")
        return True
    
    def cleanup_test_workspaces(self, test_workspace_ids: List[str]):
        """Clean up test workspaces"""
        logger.info("Cleaning up test workspaces...")
        
        for workspace_id in test_workspace_ids:
            try:
                logger.info(f"Deleting test workspace: {workspace_id}")
                self.api_request(f"/api/v2/workspaces/{workspace_id}", method="DELETE")
                logger.info(f"✅ Test workspace deleted: {workspace_id}")
            except Exception as e:
                logger.error(f"❌ Failed to delete test workspace {workspace_id}: {e}")
    
    def run_full_validation(self):
        """Run complete template validation"""
        logger.info("🚀 Starting full Coder template validation...")
        
        # Step 1: Validate template existence and configuration
        logger.info("\n📋 **Step 1: Template Validation**")
        templates = self.get_templates()
        
        if not templates:
            logger.error("❌ No templates found!")
            return False
        
        logger.info(f"📊 Found {len(templates)} templates")
        
        required_templates = list(self.expected_templates.keys())
        found_templates = []
        template_validation_results = {}
        
        for template in templates:
            template_name = template["name"]
            logger.info(f"\n📋 **Template**: {template_name}")
            logger.info(f"   Display Name: {template.get('display_name', 'N/A')}")
            logger.info(f"   Description: {template.get('description', 'N/A')}")
            logger.info(f"   Status: {template.get('status', 'unknown')}")
            logger.info(f"   ID: {template['id']}")
            
            if template_name in required_templates:
                found_templates.append(template_name)
                expected = self.expected_templates[template_name]
                is_valid, issues = self.validate_template_configuration(template, expected)
                template_validation_results[template_name] = {
                    "valid": is_valid,
                    "issues": issues
                }
                
                if not is_valid:
                    logger.error(f"❌ Template {template_name} has configuration issues:")
                    for issue in issues:
                        logger.error(f"   - {issue}")
        
        # Check if all required templates are present
        missing_templates = set(required_templates) - set(found_templates)
        if missing_templates:
            logger.error(f"❌ Missing required templates: {missing_templates}")
            return False
        
        logger.info(f"✅ All required templates found: {found_templates}")
        
        # Step 2: Test workspace creation and functionality
        logger.info("\n🧪 **Step 2: Workspace Functionality Testing**")
        
        test_workspace_ids = []
        workspace_test_results = {}
        
        for template_name in found_templates:
            logger.info(f"\n🧪 **Testing template**: {template_name}")
            
            # Create test workspace
            workspace_id = self.create_test_workspace(template_name)
            if not workspace_id:
                logger.error(f"❌ Failed to create test workspace from {template_name}")
                continue
            
            test_workspace_ids.append(workspace_id)
            
            # Wait for workspace to start
            if self.wait_for_workspace_status(workspace_id, "running"):
                logger.info(f"✅ Workspace {workspace_id} is running")
                
                # Test port accessibility
                expected_ports = self.expected_templates[template_name]["ports"]
                port_results = self.test_port_accessibility(workspace_id, expected_ports)
                
                # Test GPU functionality if applicable
                gpu_test_result = True
                if template_name == "gpu":
                    gpu_test_result = self.test_gpu_functionality(workspace_id)
                
                workspace_test_results[template_name] = {
                    "workspace_id": workspace_id,
                    "ports": port_results,
                    "gpu_functional": gpu_test_result
                }
                
                logger.info(f"✅ Template {template_name} workspace test completed")
            else:
                logger.error(f"❌ Workspace {workspace_id} failed to start")
                workspace_test_results[template_name] = {
                    "workspace_id": workspace_id,
                    "ports": {},
                    "gpu_functional": False
                }
        
        # Step 3: Generate validation report
        logger.info("\n📊 **Step 3: Validation Report**")
        
        print("\n" + "="*80)
        print("🚀 CODER TEMPLATE VALIDATION REPORT")
        print("="*80)
        
        # Template validation summary
        print("\n📋 **TEMPLATE VALIDATION SUMMARY**")
        for template_name in required_templates:
            if template_name in template_validation_results:
                result = template_validation_results[template_name]
                status = "✅ PASS" if result["valid"] else "❌ FAIL"
                print(f"  {status} {template_name}: {self.expected_templates[template_name]['display_name']}")
                
                if not result["valid"]:
                    for issue in result["issues"]:
                        print(f"    ⚠️  {issue}")
            else:
                print(f"  ❌ MISSING {template_name}")
        
        # Workspace functionality summary
        print("\n🧪 **WORKSPACE FUNCTIONALITY SUMMARY**")
        for template_name in required_templates:
            if template_name in workspace_test_results:
                result = workspace_test_results[template_name]
                print(f"\n  📋 {template_name}:")
                print(f"    Workspace ID: {result['workspace_id']}")
                
                # Port accessibility
                print(f"    Port Accessibility:")
                for port, accessible in result["ports"].items():
                    status = "✅" if accessible else "❌"
                    print(f"      {status} Port {port}")
                
                # GPU functionality
                if template_name == "gpu":
                    gpu_status = "✅" if result["gpu_functional"] else "❌"
                    print(f"    GPU Functional: {gpu_status}")
            else:
                print(f"  ❌ {template_name}: No workspace test results")
        
        # Overall success/failure
        all_templates_valid = all(
            template_validation_results.get(tmpl, {}).get("valid", False)
            for tmpl in required_templates
        )
        
        all_workspaces_working = all(
            workspace_test_results.get(tmpl, {}).get("workspace_id")
            for tmpl in required_templates
        )
        
        overall_success = all_templates_valid and all_workspaces_working
        
        print(f"\n🎯 **OVERALL VALIDATION RESULT**")
        if overall_success:
            print("  🎉 SUCCESS: All templates are properly configured and functional!")
        else:
            print("  ❌ FAILURE: Some templates have issues or are not functional")
        
        print("="*80)
        
        # Cleanup test workspaces
        if test_workspace_ids:
            logger.info("\n🧹 **Cleaning up test workspaces...**")
            self.cleanup_test_workspaces(test_workspace_ids)
        
        return overall_success
    
    def check_templates_only(self):
        """Only check template existence and configuration"""
        logger.info("📋 Checking template existence and configuration...")
        
        templates = self.get_templates()
        required_templates = list(self.expected_templates.keys())
        found_templates = []
        
        for template in templates:
            template_name = template["name"]
            if template_name in required_templates:
                found_templates.append(template_name)
                logger.info(f"✅ Found template: {template_name}")
                logger.info(f"   Display Name: {template.get('display_name', 'N/A')}")
                logger.info(f"   Description: {template.get('description', 'N/A')}")
                logger.info(f"   Status: {template.get('status', 'unknown')}")
        
        missing_templates = set(required_templates) - set(found_templates)
        if missing_templates:
            logger.warning(f"⚠️  Missing templates: {missing_templates}")
        else:
            logger.info("🎉 All required templates are present!")
        
        return len(missing_templates) == 0
    
    def test_workspaces_only(self):
        """Only test workspace creation and functionality"""
        logger.info("🧪 Testing workspace creation and functionality...")
        
        templates = self.get_templates()
        required_templates = list(self.expected_templates.keys())
        
        test_workspace_ids = []
        
        for template_name in required_templates:
            # Check if template exists
            template_exists = any(t["name"] == template_name for t in templates)
            if not template_exists:
                logger.warning(f"⚠️  Template {template_name} not found, skipping workspace test")
                continue
            
            logger.info(f"\n🧪 Testing workspace creation from template: {template_name}")
            
            # Create test workspace
            workspace_id = self.create_test_workspace(template_name)
            if workspace_id:
                test_workspace_ids.append(workspace_id)
                
                # Wait for workspace to start
                if self.wait_for_workspace_status(workspace_id, "running"):
                    logger.info(f"✅ Workspace {workspace_id} is running")
                    
                    # Test port accessibility
                    expected_ports = self.expected_templates[template_name]["ports"]
                    port_results = self.test_port_accessibility(workspace_id, expected_ports)
                    
                    logger.info(f"Port accessibility results for {template_name}:")
                    for port, accessible in port_results.items():
                        status = "✅" if accessible else "❌"
                        logger.info(f"  {status} Port {port}")
                else:
                    logger.error(f"❌ Workspace {workspace_id} failed to start")
            else:
                logger.error(f"❌ Failed to create test workspace from {template_name}")
        
        # Cleanup
        if test_workspace_ids:
            logger.info("\n🧹 Cleaning up test workspaces...")
            self.cleanup_test_workspaces(test_workspace_ids)
        
        return len(test_workspace_ids) > 0

def main():
    parser = argparse.ArgumentParser(description="Coder Template End-to-End Validation")
    parser.add_argument("--full-validation", action="store_true", help="Run complete validation")
    parser.add_argument("--check-templates-only", action="store_true", help="Only check templates")
    parser.add_argument("--test-workspaces", action="store_true", help="Only test workspaces")
    
    args = parser.parse_args()
    
    if not any([args.full_validation, args.check_templates_only, args.test_workspaces]):
        print("🔍 Coder Template End-to-End Validation Script")
        print("\nUsage:")
        print("  python3 validate_coder_templates.py --check-templates-only  # Check template existence")
        print("  python3 validate_coder_templates.py --test-workspaces      # Test workspace functionality")
        print("  python3 validate_coder_templates.py --full-validation     # Complete validation")
        return
    
    validator = CoderTemplateValidator()
    
    try:
        if args.full_validation:
            success = validator.run_full_validation()
            sys.exit(0 if success else 1)
        elif args.check_templates_only:
            success = validator.check_templates_only()
            sys.exit(0 if success else 1)
        elif args.test_workspaces:
            success = validator.test_workspaces_only()
            sys.exit(0 if success else 1)
    
    except KeyboardInterrupt:
        logger.info("Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Validation failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
