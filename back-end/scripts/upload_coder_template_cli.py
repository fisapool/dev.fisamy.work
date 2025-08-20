#!/usr/bin/env python3
"""
🚀 Coder Template Upload Script (CLI Version)

This script uploads Coder templates using the Coder CLI instead of the API.
It handles template extraction, CLI commands, and provides better error handling.

Usage:
    python3 upload_coder_template_cli.py --template-path <path_to_template_zip>
    python3 upload_coder_template_cli.py --template-path <path_to_template_zip> --template-name <name>
    python3 upload_coder_template_cli.py --list-templates
    python3 upload_coder_template_cli.py --delete-template <template_name>
"""

import os
import sys
import json
import time
import argparse
import subprocess
import tempfile
import zipfile
import tarfile
import shutil
from typing import Dict, List, Optional
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CoderTemplateUploaderCLI:
    def __init__(self):
        self.coder_token = os.getenv("CODER_API_TOKEN")
        self.coder_host = os.getenv("CODER_HOST", "https://coder.fisamy.work")
        
        if not self.coder_token:
            logger.error("CODER_API_TOKEN environment variable not set!")
            logger.error("Please set it in your environment or .env file")
            sys.exit(1)
        
        # Check if coder CLI is available
        if not self.check_coder_cli():
            logger.error("Coder CLI not found! Please install it first.")
            sys.exit(1)
        
        # Set environment variables for CLI
        os.environ["CODER_SESSION_TOKEN"] = self.coder_token
        os.environ["CODER_URL"] = self.coder_host
    
    def check_coder_cli(self) -> bool:
        """Check if Coder CLI is available"""
        try:
            result = subprocess.run(["coder", "--version"], 
                                  capture_output=True, text=True, check=True)
            logger.info(f"Coder CLI version: {result.stdout.strip()}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def run_coder_command(self, command: List[str], cwd: str = None) -> Dict[str, any]:
        """Run a Coder CLI command"""
        try:
            logger.info(f"Running command: coder {' '.join(command)}")
            result = subprocess.run(
                ["coder"] + command,
                capture_output=True,
                text=True,
                check=True,
                cwd=cwd
            )
            
            logger.info(f"Command completed successfully")
            if result.stdout:
                logger.debug(f"Output: {result.stdout}")
            
            return {
                "success": True,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed with return code {e.returncode}")
            logger.error(f"Error output: {e.stderr}")
            if e.stdout:
                logger.debug(f"Standard output: {e.stdout}")
            
            return {
                "success": False,
                "stdout": e.stdout,
                "stderr": e.stderr,
                "returncode": e.returncode
            }
    
    def extract_template_archive(self, archive_path: str) -> Optional[str]:
        """Extract template archive to a temporary directory"""
        if not os.path.exists(archive_path):
            logger.error(f"Archive file not found: {archive_path}")
            return None
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix="coder_template_")
        logger.info(f"Created temporary directory: {temp_dir}")
        
        try:
            if archive_path.endswith('.zip'):
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                logger.info(f"Extracted ZIP archive to {temp_dir}")
                
            elif archive_path.endswith('.tar.gz') or archive_path.endswith('.tgz'):
                with tarfile.open(archive_path, 'r:gz') as tar_ref:
                    tar_ref.extractall(temp_dir)
                logger.info(f"Extracted TAR.GZ archive to {temp_dir}")
                
            elif archive_path.endswith('.tar'):
                with tarfile.open(archive_path, 'r') as tar_ref:
                    tar_ref.extractall(temp_dir)
                logger.info(f"Extracted TAR archive to {temp_dir}")
                
            else:
                logger.error(f"Unsupported archive format: {archive_path}")
                shutil.rmtree(temp_dir)
                return None
            
            # List contents
            contents = os.listdir(temp_dir)
            logger.info(f"Archive contents: {contents}")
            
            return temp_dir
            
        except Exception as e:
            logger.error(f"Failed to extract archive: {e}")
            shutil.rmtree(temp_dir)
            return None
    
    def find_terraform_files(self, directory: str) -> bool:
        """Check if directory contains Terraform files"""
        terraform_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(('.tf', '.tf.json', '.tfvars')):
                    terraform_files.append(os.path.join(root, file))
        
        if terraform_files:
            logger.info(f"Found Terraform files: {terraform_files}")
            return True
        else:
            logger.warning("No Terraform files found in directory")
            return False
    
    def list_templates(self):
        """List all available templates using CLI"""
        logger.info("Listing available templates...")
        result = self.run_coder_command(["templates", "list"])
        
        if result["success"]:
            logger.info("✅ Templates listed successfully")
            print(result["stdout"])
        else:
            logger.error("❌ Failed to list templates")
    
    def delete_template(self, template_name: str) -> bool:
        """Delete a template using CLI"""
        logger.info(f"Deleting template: {template_name}")
        result = self.run_coder_command(["templates", "delete", template_name, "-y"])
        
        if result["success"]:
            logger.info(f"✅ Template '{template_name}' deleted successfully")
            return True
        else:
            logger.error(f"❌ Failed to delete template '{template_name}'")
            return False
    
    def upload_template(self, template_path: str, template_name: str = None, 
                       display_name: str = None, description: str = None) -> bool:
        """Upload a template using the CLI"""
        logger.info(f"Starting template upload process...")
        logger.info(f"Template Path: {template_path}")
        logger.info(f"Template Name: {template_name}")
        
        # Extract the archive
        temp_dir = self.extract_template_archive(template_path)
        if not temp_dir:
            return False
        
        try:
            # Check if it contains Terraform files
            if not self.find_terraform_files(temp_dir):
                logger.warning("No Terraform files found, but continuing...")
            
            # Build the push command
            push_command = ["templates", "push"]
            
            if template_name:
                push_command.append(template_name)
            
            # Add message
            message = f"Uploaded template: {os.path.basename(template_path)}"
            if description:
                message = f"{description} - {message}"
            push_command.extend(["-m", message])
            
            # Add yes flag to skip prompts
            push_command.append("-y")
            
            # Push the template
            logger.info(f"Pushing template using CLI...")
            result = self.run_coder_command(push_command, cwd=temp_dir)
            
            if result["success"]:
                logger.info("✅ Template uploaded successfully!")
                print(result["stdout"])
                return True
            else:
                logger.error("❌ Template upload failed!")
                return False
                
        finally:
            # Clean up temporary directory
            logger.info(f"Cleaning up temporary directory: {temp_dir}")
            shutil.rmtree(temp_dir)
    
    def edit_template_metadata(self, template_name: str, display_name: str = None, 
                              description: str = None) -> bool:
        """Edit template metadata after creation"""
        if not display_name and not description:
            logger.info("No metadata to update")
            return True
        
        logger.info(f"Updating metadata for template: {template_name}")
        
        # Build edit command
        edit_command = ["templates", "edit", template_name]
        
        if display_name:
            edit_command.extend(["--display-name", display_name])
        
        if description:
            edit_command.extend(["--description", description])
        
        result = self.run_coder_command(edit_command)
        
        if result["success"]:
            logger.info(f"✅ Template metadata updated successfully")
            return True
        else:
            logger.error(f"❌ Failed to update template metadata")
            return False

def main():
    parser = argparse.ArgumentParser(description="Upload Coder templates via CLI")
    parser.add_argument("--template-path", help="Path to the template file (zip/tar)")
    parser.add_argument("--template-name", help="Name for the template (default: filename without extension)")
    parser.add_argument("--display-name", help="Display name for the template")
    parser.add_argument("--description", help="Description for the template")
    parser.add_argument("--list-templates", action="store_true", help="List all existing templates")
    parser.add_argument("--delete-template", help="Delete a template by name")
    
    args = parser.parse_args()
    
    uploader = CoderTemplateUploaderCLI()
    
    if args.list_templates:
        uploader.list_templates()
    elif args.delete_template:
        uploader.delete_template(args.delete_template)
    elif args.template_path:
        if not args.template_name:
            args.template_name = Path(args.template_path).stem
        
        success = uploader.upload_template(
            args.template_path,
            args.template_name
        )
        
        if success and (args.display_name or args.description):
            # Update metadata after successful upload
            uploader.edit_template_metadata(
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
