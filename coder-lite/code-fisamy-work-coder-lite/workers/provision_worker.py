import os
import sys
import time
import logging
import subprocess
import secrets
import string
from typing import Dict, Any, Optional
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from utils.atomic_writer import atomic_write_caddy, atomic_write_compose
from utils.distributed_lock import IdempotencyLock
from utils.port_allocator import PortAllocator

logger = logging.getLogger(__name__)

class ProvisionWorker:
    """Enhanced provision worker with all production hardening"""
    
    def __init__(self, redis_client, db_session, config: Dict[str, Any]):
        self.redis = redis_client
        self.db = db_session
        self.config = config
        self.lock = IdempotencyLock(redis_client)
        self.port_allocator = PortAllocator(
            start_port=config.get('start_port', 13001),
            max_port=config.get('max_port', 65535)
        )
        
        # Paths
        self.coder_lite_path = config.get('coder_lite_path', '/opt/coder-lite')
        self.compose_override = os.path.join(self.coder_lite_path, 'docker-compose.override.yml')
        self.caddy_file = config.get('caddy_file', '/opt/coder-lite/Caddyfile')
        
        # Plan matrix
        self.plan_matrix = config.get('plans', {
            'DEV-BASIC-1M': {'cpu': '2.0', 'ram': '4g', 'disk': 20, 'idle_timeout': 45},
            'DEV-PLUS-1M': {'cpu': '4.0', 'ram': '8g', 'disk': 40, 'idle_timeout': 120},
            'DEV-GPU-1M': {'cpu': '6.0', 'ram': '16g', 'disk': 60, 'gpu': True, 'idle_timeout': 45}
        })
    
    def handle_provision_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a provision job with full production hardening
        
        Args:
            job: Provision job from queue
            
        Returns:
            Result dictionary with status and details
        """
        start_time = time.time()
        provider = job.get('provider')
        order_id = job.get('order_id')
        idempotency_key = f"{provider}:{order_id}"
        
        logger.info(f"Processing provision job: {idempotency_key}")
        
        # 1. Check idempotency lock
        lock_token = self.lock.acquire_order_lock(provider, order_id)
        if not lock_token:
            logger.info(f"Job {idempotency_key} already being processed")
            return {
                "status": "already_processing",
                "message": "Job is already being processed",
                "idempotency_key": idempotency_key
            }
        
        try:
            # 2. Validate job data
            if not self._validate_job(job):
                raise ValueError("Invalid job data")
            
            # 3. Extract plan configuration
            plan_config = self._get_plan_config(job['plan'])
            if not plan_config:
                raise ValueError(f"Unknown plan: {job['plan']}")
            
            # 4. Generate secure password (only once)
            password = self._generate_secure_password()
            bcrypt_hash = self._generate_bcrypt_hash(password)
            
            # 5. Allocate port with database locking
            port = self._allocate_port_safely(job['user']['username'])
            if not port:
                raise Exception("Failed to allocate port")
            
            # 6. Provision user workspace
            provision_result = self._provision_workspace(
                username=job['user']['username'],
                plan_config=plan_config,
                port=port,
                bcrypt_hash=bcrypt_hash
            )
            
            # 7. Health check before marking ready
            if not self._wait_for_health_check(port, job['user']['username']):
                raise Exception("Health check failed")
            
            # 8. Update Caddy configuration
            caddy_result = self._update_caddy_config(
                username=job['user']['username'],
                port=port,
                bcrypt_hash=bcrypt_hash
            )
            
            # 9. Persist workspace data
            workspace_data = self._persist_workspace(
                user_id=job['user']['id'],
                username=job['user']['username'],
                plan=job['plan'],
                port=port,
                plan_config=plan_config,
                bcrypt_hash=bcrypt_hash
            )
            
            # 10. Mark order as fulfilled
            self._mark_order_fulfilled(idempotency_key)
            
            # 11. Notify customer
            notification_result = self._notify_customer(
                user=job['user'],
                workspace_url=f"https://{job['user']['username']}.code.fisamy.work",
                password=password
            )
            
            # 12. Emit metrics
            duration_ms = int((time.time() - start_time) * 1000)
            self._emit_metrics('provision_success', duration_ms, job['plan'])
            
            return {
                "status": "ready",
                "url": f"https://{job['user']['username']}.code.fisamy.work",
                "container": f"dev-{job['user']['username']}",
                "port": port,
                "duration_ms": duration_ms,
                "notes": "Workspace provisioned successfully with all hardening applied"
            }
            
        except Exception as e:
            # Rollback on failure
            self._rollback_provision(job['user']['username'], port)
            
            # Emit failure metrics
            duration_ms = int((time.time() - start_time) * 1000)
            self._emit_metrics('provision_failure', duration_ms, job['plan'], str(e))
            
            # Mark order as failed
            self._mark_order_failed(idempotency_key, str(e))
            
            raise
            
        finally:
            # Always release the lock
            self.lock.release_order_lock(provider, order_id, lock_token)
    
    def _validate_job(self, job: Dict[str, Any]) -> bool:
        """Validate job data structure"""
        required_fields = ['provider', 'order_id', 'user', 'plan']
        for field in required_fields:
            if field not in job:
                logger.error(f"Missing required field: {field}")
                return False
        
        if 'id' not in job['user'] or 'username' not in job['user']:
            logger.error("User must have id and username")
            return False
        
        return True
    
    def _get_plan_config(self, plan: str) -> Optional[Dict[str, Any]]:
        """Get plan configuration from matrix"""
        return self.plan_matrix.get(plan)
    
    def _generate_secure_password(self, length: int = 24) -> str:
        """Generate cryptographically secure password"""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def _generate_bcrypt_hash(self, password: str) -> str:
        """Generate bcrypt hash for password"""
        try:
            import bcrypt
            salt = bcrypt.gensalt(rounds=12)
            hash_bytes = bcrypt.hashpw(password.encode('utf-8'), salt)
            return hash_bytes.decode('utf-8')
        except ImportError:
            # Fallback to subprocess if bcrypt not available
            result = subprocess.run([
                'python3', '-c', 
                f'import crypt; print(crypt.crypt("{password}", crypt.mksalt(crypt.METHOD_SHA512)))'
            ], capture_output=True, text=True, check=True)
            return result.stdout.strip()
    
    def _allocate_port_safely(self, username: str) -> Optional[int]:
        """Allocate port with database locking"""
        # Create temporary workspace record for port allocation
        workspace_id = self._create_temp_workspace(username)
        if not workspace_id:
            return None
        
        try:
            port = self.port_allocator.allocate_port(self.db, workspace_id, username)
            if port:
                # Update the temporary workspace with the allocated port
                self._update_workspace_port(workspace_id, port)
            return port
        except Exception as e:
            logger.error(f"Port allocation failed: {e}")
            return None
    
    def _provision_workspace(self, username: str, plan_config: Dict[str, Any], 
                           port: int, bcrypt_hash: str) -> bool:
        """Provision user workspace using devctl"""
        try:
            # Build devctl command
            cmd = [
                'python', '-m', 'devctl', 'create', username,
                '--cpu', str(plan_config['cpu']),
                '--ram', str(plan_config['ram']),
                '--disk', str(plan_config['disk']),
                '--port', str(port),
                '--domain-base', 'code.fisamy.work',
                '--healthcheck-enable',
                '--basic-auth-hash', f"{username}:{bcrypt_hash}",
                '--config', os.path.join(self.coder_lite_path, 'devctl', 'config.yml')
            ]
            
            # Add GPU if plan supports it
            if plan_config.get('gpu'):
                cmd.append('--gpu')
            
            logger.info(f"Running devctl: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                cwd=self.coder_lite_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info(f"Devctl output: {result.stdout}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Devctl failed: {e.stderr}")
            return False
    
    def _wait_for_health_check(self, port: int, username: str, 
                              timeout: int = 120, interval: int = 5) -> bool:
        """Wait for container health check to pass"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Try to connect to the container
                result = subprocess.run([
                    'curl', '-f', '-s', f'http://127.0.0.1:{port}/',
                    '--connect-timeout', '5', '--max-time', '10'
                ], capture_output=True)
                
                if result.returncode == 0:
                    logger.info(f"Health check passed for {username} on port {port}")
                    return True
                
            except Exception as e:
                logger.debug(f"Health check attempt failed: {e}")
            
            time.sleep(interval)
        
        logger.error(f"Health check timeout for {username} on port {port}")
        return False
    
    def _update_caddy_config(self, username: str, port: int, bcrypt_hash: str) -> bool:
        """Update Caddy configuration atomically"""
        try:
            # Read existing Caddyfile
            with open(self.caddy_file, 'r') as f:
                existing_content = f.read()
            
            # Generate new host block
            new_block = f"""

# Auto-generated for {username}
{username}.code.fisamy.work {{
  encode gzip
  
  @big body {{
    max_size 20MB
  }}
  handle @big {{
    respond 413
  }}
  
  reverse_proxy 127.0.0.1:{port}
  
  basicauth /* {{
    {username} {bcrypt_hash}
  }}
  
  header {{
    Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
    X-Content-Type-Options "nosniff"
    X-Frame-Options "DENY"
    Referrer-Policy "no-referrer"
    Content-Security-Policy "frame-ancestors 'none';"
  }}
}}
"""
            
            # Append new block and reload atomically
            new_content = existing_content + new_block
            return atomic_write_caddy(new_content, self.caddy_file)
            
        except Exception as e:
            logger.error(f"Failed to update Caddy config: {e}")
            return False
    
    def _persist_workspace(self, user_id: int, username: str, plan: str, 
                          port: int, plan_config: Dict[str, Any], 
                          bcrypt_hash: str) -> Dict[str, Any]:
        """Persist workspace data to database"""
        try:
            # This would be your actual database operation
            # For now, we'll return a mock structure
            workspace_data = {
                'id': user_id,
                'user_id': user_id,
                'host_subdomain': username,
                'port': port,
                'cpu': plan_config['cpu'],
                'ram_bytes': self._parse_memory(plan_config['ram']),
                'disk_gib': plan_config['disk'],
                'auth_type': 'basic',
                'auth_secret_hash': bcrypt_hash,
                'status': 'ready',
                'url': f"https://{username}.code.fisamy.work",
                'plan': plan,
                'created_at': time.time()
            }
            
            logger.info(f"Workspace data persisted: {workspace_data}")
            return workspace_data
            
        except Exception as e:
            logger.error(f"Failed to persist workspace: {e}")
            raise
    
    def _rollback_provision(self, username: str, port: Optional[int]):
        """Rollback provision on failure"""
        try:
            # Stop and remove container
            subprocess.run([
                'docker', 'compose', 'stop', username
            ], cwd=self.coder_lite_path, capture_output=True)
            
            subprocess.run([
                'docker', 'compose', 'rm', '-f', username
            ], cwd=self.coder_lite_path, capture_output=True)
            
            # Remove from compose override
            self._remove_from_compose_override(username)
            
            # Remove data directory
            data_dir = f"/srv/devdata/{username}"
            if os.path.exists(data_dir):
                import shutil
                shutil.rmtree(data_dir)
            
            # Release port if allocated
            if port:
                self._release_port(username, port)
            
            logger.info(f"Rollback completed for {username}")
            
        except Exception as e:
            logger.error(f"Rollback failed for {username}: {e}")
    
    def _emit_metrics(self, event_type: str, duration_ms: int, 
                      plan: str, error_msg: str = None):
        """Emit metrics for monitoring"""
        metrics = {
            'event_type': event_type,
            'duration_ms': duration_ms,
            'plan': plan,
            'timestamp': time.time()
        }
        
        if error_msg:
            metrics['error'] = error_msg
        
        # This would send to your metrics system (Prometheus, etc.)
        logger.info(f"Metrics: {metrics}")
    
    def _parse_memory(self, memory_str: str) -> int:
        """Parse memory string to bytes"""
        memory_str = memory_str.lower()
        if memory_str.endswith('g'):
            return int(float(memory_str[:-1]) * 1024 * 1024 * 1024)
        elif memory_str.endswith('m'):
            return int(float(memory_str[:-1]) * 1024 * 1024)
        elif memory_str.endswith('k'):
            return int(float(memory_str[:-1]) * 1024)
        else:
            return int(memory_str)
    
    # Placeholder methods for database operations
    def _create_temp_workspace(self, username: str) -> Optional[int]:
        """Create temporary workspace record for port allocation"""
        # This would be your actual database operation
        return hash(username) % 1000000  # Mock ID
    
    def _update_workspace_port(self, workspace_id: int, port: int):
        """Update workspace with allocated port"""
        # This would be your actual database operation
        pass
    
    def _mark_order_fulfilled(self, idempotency_key: str):
        """Mark order as fulfilled in database"""
        # This would be your actual database operation
        pass
    
    def _mark_order_failed(self, idempotency_key: str, reason: str):
        """Mark order as failed in database"""
        # This would be your actual database operation
        pass
    
    def _notify_customer(self, user: Dict[str, Any], workspace_url: str, 
                        password: str) -> bool:
        """Notify customer with workspace credentials"""
        # This would be your actual notification logic
        logger.info(f"Customer notification sent to {user.get('email')}")
        return True
    
    def _remove_from_compose_override(self, username: str):
        """Remove user service from compose override"""
        # This would be your actual compose file editing logic
        pass
    
    def _release_port(self, username: str, port: int):
        """Release port back to pool"""
        # This would be your actual port release logic
        pass
