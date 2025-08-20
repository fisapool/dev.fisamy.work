#!/usr/bin/env python3
"""
🚀 Coder Template Collection Upload Script

This script uploads collections of Coder templates that contain multiple individual templates
in subdirectories. It uses the Coder CLI to upload each template individually.

Usage:
    python3 upload_template_collection.py --collection-path <path_to_template_collection_zip>
    python3 upload_template_collection.py --collection-path <path_to_template_collection_zip> --prefix <name_prefix>
    python3 upload_template_collection.py --list-templates
    python3 upload_template_collection.py --delete-template <template_name>
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

class CoderTemplateCollectionUploader:
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
    
    def extract_template_collection(self, archive_path: str) -> Optional[str]:
        """Extract template collection archive to a temporary directory"""
        if not os.path.exists(archive_path):
            logger.error(f"Archive file not found: {archive_path}")
            return None
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix="coder_template_collection_")
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
    
    def find_template_directories(self, base_dir: str) -> List[str]:
        """Find all template directories that contain Terraform files"""
        template_dirs = []
        
        for item in os.listdir(base_dir):
            item_path = os.path.join(base_dir, item)
            if os.path.isdir(item_path):
                # Check if this directory contains Terraform files
                if self.has_terraform_files(item_path):
                    template_dirs.append(item_path)
                    logger.info(f"Found template directory: {item}")
        
        return template_dirs
    
    def has_terraform_files(self, directory: str) -> bool:
        """Check if directory contains Terraform files"""
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(('.tf', '.tf.json', '.tfvars')):
                    return True
        return False
    
    def upload_single_template(self, template_dir: str, template_name: str, 
                              prefix: str = None) -> bool:
        """Upload a single template from a directory"""
        if prefix:
            full_template_name = f"{prefix}-{template_name}"
        else:
            full_template_name = template_name
        
        logger.info(f"Uploading template: {full_template_name} from {template_dir}")
        
        # Build the push command
        push_command = ["templates", "push", full_template_name, "-y"]
        
        # Add message
        message = f"Uploaded template: {template_name}"
        push_command.extend(["-m", message])
        
        # Push the template
        result = self.run_coder_command(push_command, cwd=template_dir)
        
        if result["success"]:
            logger.info(f"✅ Template '{full_template_name}' uploaded successfully!")
            return True
        else:
            logger.error(f"❌ Failed to upload template '{full_template_name}'")
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
    
    def upload_template_collection(self, collection_path: str, prefix: str = None) -> bool:
        """Upload a collection of templates"""
        logger.info(f"Starting template collection upload process...")
        logger.info(f"Collection Path: {collection_path}")
        logger.info(f"Prefix: {prefix}")
        
        # Extract the collection
        temp_dir = self.extract_template_collection(collection_path)
        if not temp_dir:
            return False
        
        try:
            # Find the main collection directory (usually the first subdirectory)
            contents = os.listdir(temp_dir)
            if len(contents) == 1 and os.path.isdir(os.path.join(temp_dir, contents[0])):
                collection_dir = os.path.join(temp_dir, contents[0])
                logger.info(f"Found collection directory: {collection_dir}")
            else:
                collection_dir = temp_dir
            
            # Find all template directories
            template_dirs = self.find_template_directories(collection_dir)
            
            if not template_dirs:
                logger.error("No template directories found in collection")
                return False
            
            logger.info(f"Found {len(template_dirs)} template directories")
            
            # Upload each template
            successful_uploads = 0
            failed_uploads = 0
            
            for template_dir in template_dirs:
                template_name = os.path.basename(template_dir)
                
                if self.upload_single_template(template_dir, template_name, prefix):
                    successful_uploads += 1
                else:
                    failed_uploads += 1
                
                # Small delay between uploads
                time.sleep(1)
            
            logger.info(f"Upload summary: {successful_uploads} successful, {failed_uploads} failed")
            
            if failed_uploads == 0:
                logger.info("🎉 All templates uploaded successfully!")
                return True
            elif successful_uploads > 0:
                logger.warning(f"⚠️  {successful_uploads} templates uploaded, {failed_uploads} failed")
                return True
            else:
                logger.error("❌ All template uploads failed!")
                return False
                
        finally:
            # Clean up temporary directory
            logger.info(f"Cleaning up temporary directory: {temp_dir}")
            shutil.rmtree(temp_dir)

def main():
    parser = argparse.ArgumentParser(description="Upload Coder template collections")
    parser.add_argument("--collection-path", help="Path to the template collection file (zip/tar)")
    parser.add_argument("--prefix", help="Prefix to add to template names (e.g., 'main' for 'main-template-name')")
    parser.add_argument("--list-templates", action="store_true", help="List all existing templates")
    parser.add_argument("--delete-template", help="Delete a template by name")
    
    args = parser.parse_args()
    
    uploader = CoderTemplateCollectionUploader()
    
    if args.list_templates:
        uploader.list_templates()
    elif args.delete_template:
        uploader.delete_template(args.delete_template)
    elif args.collection_path:
        success = uploader.upload_template_collection(
            args.collection_path,
            args.prefix
        )
        
        if success:
            logger.info("🎉 Template collection upload completed!")
            sys.exit(0)
        else:
            logger.error("❌ Template collection upload failed!")
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
