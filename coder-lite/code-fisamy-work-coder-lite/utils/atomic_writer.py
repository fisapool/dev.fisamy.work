import os
import tempfile
import shutil
import subprocess
import logging
from typing import List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class AtomicWriter:
    """Atomic file writer with validation and rollback capabilities"""
    
    def __init__(self, file_path: str, backup_suffix: str = ".bak"):
        self.file_path = Path(file_path)
        self.backup_path = self.file_path.with_suffix(backup_suffix)
        self.temp_path: Optional[Path] = None
        
    def __enter__(self):
        # Create temp file in same directory for atomic rename
        self.temp_path = self.file_path.with_suffix(f".tmp.{os.getpid()}")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.temp_path and self.temp_path.exists():
            try:
                os.remove(self.temp_path)
            except OSError:
                logger.warning(f"Failed to cleanup temp file: {self.temp_path}")
    
    def write_and_reload(self, content: str, validate_cmd: List[str], 
                        reload_cmd: List[str]) -> bool:
        """
        Atomically write content, validate, and reload service
        
        Args:
            content: File content to write
            validate_cmd: Command to validate the file (e.g., ['caddy', 'validate'])
            reload_cmd: Command to reload the service (e.g., ['systemctl', 'reload', 'caddy'])
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            Exception: If validation or reload fails
        """
        try:
            # Write content to temp file
            with open(self.temp_path, 'w') as f:
                f.write(content)
            
            # Validate using temp file
            logger.info(f"Validating {self.file_path} with temp file")
            validate_result = subprocess.run(
                validate_cmd + ["--config", str(self.temp_path)],
                capture_output=True,
                text=True,
                check=True
            )
            logger.debug(f"Validation output: {validate_result.stdout}")
            
            # Create backup of existing file
            if self.file_path.exists():
                shutil.copy2(self.file_path, self.backup_path)
                logger.info(f"Backup created: {self.backup_path}")
            
            # Atomic replace
            os.replace(self.temp_path, self.file_path)
            self.temp_path = None  # Prevent cleanup
            logger.info(f"File atomically replaced: {self.file_path}")
            
            # Reload service
            logger.info(f"Reloading service with: {' '.join(reload_cmd)}")
            reload_result = subprocess.run(reload_cmd, check=True, capture_output=True, text=True)
            logger.debug(f"Reload output: {reload_result.stdout}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {' '.join(e.cmd)}")
            logger.error(f"Error output: {e.stderr}")
            self._rollback()
            raise Exception(f"Operation failed: {e.stderr}")
            
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            self._rollback()
            raise
            
    def _rollback(self):
        """Rollback to backup file if available"""
        if self.backup_path.exists():
            try:
                shutil.copy2(self.backup_path, self.file_path)
                logger.info(f"Rolled back to backup: {self.backup_path}")
            except Exception as e:
                logger.error(f"Rollback failed: {e}")
        else:
            logger.warning("No backup available for rollback")

def atomic_write_caddy(content: str, caddy_file: str = "/opt/coder-lite/Caddyfile") -> bool:
    """Atomically write Caddyfile and reload Caddy"""
    with AtomicWriter(caddy_file) as writer:
        return writer.write_and_reload(
            content=content,
            validate_cmd=["caddy", "validate"],
            reload_cmd=["systemctl", "reload", "caddy"]
        )

def atomic_write_compose(content: str, compose_file: str = "docker-compose.override.yml") -> bool:
    """Atomically write Docker Compose file"""
    with AtomicWriter(compose_file) as writer:
        # Docker Compose doesn't have a validate command, so we just write
        # The file will be validated when docker compose up is run
        try:
            with open(writer.temp_path, 'w') as f:
                f.write(content)
            
            # Create backup
            if writer.file_path.exists():
                shutil.copy2(writer.file_path, writer.backup_path)
            
            # Atomic replace
            os.replace(writer.temp_path, writer.file_path)
            writer.temp_path = None
            
            return True
            
        except Exception as e:
            logger.error(f"Compose write failed: {e}")
            writer._rollback()
            raise
