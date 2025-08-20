#!/usr/bin/env python3
"""
🚀 Coder Template Upload Script

This script uploads Coder templates to the Coder instance using the API.
It handles template creation, version management, and archive uploads.

Usage:
    python3 upload_coder_template.py --template-path <path_to_template_zip>
    python3 upload_coder_template.py --template-path <path_to_template_zip> --template-name <name>
    python3 upload_coder_template.py --list-templates
    python3 upload_coder_template.py --delete-template <template_name>
"""

import os
import sys
import json
import time
import argparse
import subprocess
import requests
import base64
from typing import Dict, List, Optional
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CoderTemplateUploader:
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
    
    def api_request(self, endpoint: str, method: str = "GET", data: dict = None, files: dict = None) -> dict:
        """Make a request to the Coder API"""
        url = f"{self.coder_host}{endpoint}"
        
        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers)
            elif method == "POST":
                if files:
                    # Remove Content-Type header for file uploads
                    headers = self.headers.copy()
                    headers.pop("Content-Type", None)
                    response = requests.post(url, headers=headers, data=data, files=files)
                else:
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
    
    def create_template(self, template_name: str, display_name: str, description: str) -> Optional[str]:
        """Create a template in Coder"""
        org_id = self.get_organization_id()
        if not org_id:
            logger.error("Could not determine organization ID")
            return None
        
        # Check if template already exists
        existing_templates = self.get_templates()
        for template in existing_templates:
            if template["name"] == template_name:
                logger.info(f"Template '{template_name}' already exists with ID: {template['id']}")
                return template["id"]
        
        # Create template with terraform provisioner (like existing templates)
        template_data = {
            "name": template_name,
            "display_name": display_name,
            "description": description,
            "icon": "",
            "organization_id": org_id,
            "provisioner": "terraform"  # Changed from "docker" to "terraform"
        }
        
        logger.info(f"Creating template: {template_name}")
        logger.info(f"Template data: {json.dumps(template_data, indent=2)}")
        
        template = self.api_request("/api/v2/templates", method="POST", data=template_data)
        
        if template and "id" in template:
            template_id = template["id"]
            logger.info(f"✅ Template created with ID: {template_id}")
            return template_id
        else:
            logger.error("Failed to create template")
            logger.error(f"Response: {template}")
            return None
    
    def upload_template_version(self, template_id: str, template_path: str, version_name: str = "v1.0.0") -> Optional[str]:
        """Upload a template version with the actual archive"""
        if not os.path.exists(template_path):
            logger.error(f"Template file not found: {template_path}")
            return None
        
        # Read the template file
        try:
            with open(template_path, 'rb') as f:
                template_content = f.read()
        except Exception as e:
            logger.error(f"Failed to read template file: {e}")
            return None
        
        # Encode the content as base64
        template_b64 = base64.b64encode(template_content).decode('utf-8')
        
        # Create template version
        version_data = {
            "name": version_name,
            "message": f"Uploaded template: {os.path.basename(template_path)}",
            "template_id": template_id,
            "archive": {
                "format": "zip" if template_path.endswith('.zip') else "tar",
                "content": template_b64
            }
        }
        
        logger.info(f"Creating template version: {version_name}")
        version = self.api_request("/api/v2/templateversions", method="POST", data=version_data)
        
        if version and "id" in version:
            version_id = version["id"]
            logger.info(f"✅ Template version created: {version_id}")
            
            # Wait for the version to be provisioned
            self.wait_for_version_provisioning(template_id, version_id)
            
            # Update template with active version
            self.api_request(f"/api/v2/templates/{template_id}", method="PUT", data={
                "active_version_id": version_id
            })
            
            return version_id
        else:
            logger.error("Failed to create template version")
            return None
    
    def wait_for_version_provisioning(self, template_id: str, version_id: str, timeout: int = 300) -> bool:
        """Wait for template version to be provisioned"""
        logger.info("Waiting for template version to be provisioned...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                version = self.api_request(f"/api/v2/templateversions/{version_id}")
                if version and "status" in version:
                    status = version["status"]
                    logger.info(f"Template version status: {status}")
                    
                    if status == "active":
                        logger.info("✅ Template version is now active")
                        return True
                    elif status in ["failed", "canceled"]:
                        logger.error(f"❌ Template version failed with status: {status}")
                        return False
                    
                    # Wait before checking again
                    time.sleep(10)
                else:
                    logger.warning("Could not get version status, retrying...")
                    time.sleep(10)
                    
            except Exception as e:
                logger.warning(f"Error checking version status: {e}")
                time.sleep(10)
        
        logger.error(f"Timeout waiting for template version provisioning after {timeout} seconds")
        return False
    
    def get_templates(self) -> List[dict]:
        """Get all templates"""
        templates = self.api_request("/api/v2/templates")
        if isinstance(templates, list):
            return templates
        elif isinstance(templates, dict) and "templates" in templates:
            return templates["templates"]
        else:
            logger.warning(f"Unexpected API response format: {type(templates)}")
            return []
    
    def list_templates(self):
        """List all available templates"""
        templates = self.get_templates()
        if not templates:
            logger.info("No templates found")
            return
        
        logger.info(f"Found {len(templates)} templates:")
        for template in templates:
            logger.info(f"  - {template['name']} (ID: {template['id']})")
            logger.info(f"    Display Name: {template.get('display_name', 'N/A')}")
            logger.info(f"    Status: {template.get('status', 'unknown')}")
            logger.info(f"    Active Version: {template.get('active_version_id', 'N/A')}")
            logger.info("")
    
    def delete_template(self, template_name: str) -> bool:
        """Delete a template"""
        templates = self.get_templates()
        template_id = None
        
        for template in templates:
            if template["name"] == template_name:
                template_id = template["id"]
                break
        
        if not template_id:
            logger.error(f"Template not found: {template_name}")
            return False
        
        logger.info(f"Deleting template: {template_name} (ID: {template_id})")
        
        # Delete the template
        result = self.api_request(f"/api/v2/templates/{template_id}", method="DELETE")
        if result is not None:  # DELETE requests might return empty response
            logger.info(f"✅ Template '{template_name}' deleted successfully")
            return True
        else:
            logger.error(f"Failed to delete template '{template_name}'")
            return False
    
    def upload_template(self, template_path: str, template_name: str = None, display_name: str = None, description: str = None) -> bool:
        """Upload a complete template"""
        if not template_name:
            template_name = Path(template_path).stem
        
        if not display_name:
            display_name = template_name.replace('-', ' ').replace('_', ' ').title()
        
        if not description:
            description = f"Template uploaded from {os.path.basename(template_path)}"
        
        logger.info(f"Starting template upload process...")
        logger.info(f"Template Path: {template_path}")
        logger.info(f"Template Name: {template_name}")
        logger.info(f"Display Name: {display_name}")
        logger.info(f"Description: {description}")
        
        # Create template
        template_id = self.create_template(template_name, display_name, description)
        if not template_id:
            return False
        
        # Upload template version
        version_id = self.upload_template_version(template_id, template_path)
        if not version_id:
            return False
        
        logger.info(f"✅ Template '{template_name}' uploaded successfully!")
        logger.info(f"Template ID: {template_id}")
        logger.info(f"Version ID: {version_id}")
        
        return True

def main():
    parser = argparse.ArgumentParser(description="Upload Coder templates via API")
    parser.add_argument("--template-path", help="Path to the template file (zip/tar)")
    parser.add_argument("--template-name", help="Name for the template (default: filename without extension)")
    parser.add_argument("--display-name", help="Display name for the template")
    parser.add_argument("--description", help="Description for the template")
    parser.add_argument("--list-templates", action="store_true", help="List all existing templates")
    parser.add_argument("--delete-template", help="Delete a template by name")
    
    args = parser.parse_args()
    
    uploader = CoderTemplateUploader()
    
    if args.list_templates:
        uploader.list_templates()
    elif args.delete_template:
        uploader.delete_template(args.delete_template)
    elif args.template_path:
        success = uploader.upload_template(
            args.template_path,
            args.template_name,
            args.display_name,
            args.description
        )
        if success:
            logger.info("🎉 Template upload completed successfully!")
            sys.exit(0)
        else:
            logger.error("❌ Template upload failed!")
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
