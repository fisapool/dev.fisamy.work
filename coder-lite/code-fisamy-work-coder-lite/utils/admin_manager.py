#!/usr/bin/env python3
"""
Admin management system for Coder-lite Provision System
Handles templates, audit events, and operational controls
"""

import os
import time
import logging
import json
import hashlib
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import redis
import bcrypt

logger = logging.getLogger(__name__)

class AuditAction(Enum):
    """Audit action types"""
    TEMPLATE_CREATED = "template_created"
    TEMPLATE_UPDATED = "template_updated"
    TEMPLATE_DELETED = "template_deleted"
    WORKSPACE_PROVISIONED = "workspace_provisioned"
    WORKSPACE_SUSPENDED = "workspace_suspended"
    WORKSPACE_DESTROYED = "workspace_destroyed"
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    ADMIN_LOGIN = "admin_login"
    ADMIN_ACTION = "admin_action"
    SYSTEM_CONFIG_CHANGED = "system_config_changed"
    BREAK_GLASS = "break_glass"

class TemplateStatus(Enum):
    """Template status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    TESTING = "testing"

@dataclass
class WorkspaceTemplate:
    """Workspace template configuration"""
    id: str
    name: str
    description: str
    image: str
    cpu: str
    ram: str
    disk_gb: int
    gpu: bool = False
    gpu_type: Optional[str] = None
    idle_timeout: int = 45  # minutes
    max_runtime: int = 1440  # minutes (24 hours)
    environment_vars: Dict[str, str] = field(default_factory=dict)
    labels: Dict[str, str] = field(default_factory=dict)
    status: TemplateStatus = TemplateStatus.ACTIVE
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    created_by: str = "system"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "image": self.image,
            "cpu": self.cpu,
            "ram": self.ram,
            "disk_gb": self.disk_gb,
            "gpu": self.gpu,
            "gpu_type": self.gpu_type,
            "idle_timeout": self.idle_timeout,
            "max_runtime": self.max_runtime,
            "environment_vars": self.environment_vars,
            "labels": self.labels,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "created_by": self.created_by
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkspaceTemplate':
        """Create from dictionary"""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            image=data["image"],
            cpu=data["cpu"],
            ram=data["ram"],
            disk_gb=data["disk_gb"],
            gpu=data.get("gpu", False),
            gpu_type=data.get("gpu_type"),
            idle_timeout=data.get("idle_timeout", 45),
            max_runtime=data.get("max_runtime", 1440),
            environment_vars=data.get("environment_vars", {}),
            labels=data.get("labels", {}),
            status=TemplateStatus(data.get("status", "active")),
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
            created_by=data.get("created_by", "system")
        )

@dataclass
class AuditEvent:
    """Audit event record"""
    id: str
    timestamp: float
    actor: str
    action: AuditAction
    subject_type: str
    subject_id: str
    payload: Dict[str, Any]
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "actor": self.actor,
            "action": self.action.value,
            "subject_type": self.subject_type,
            "subject_id": self.subject_id,
            "payload": json.dumps(self.payload),
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "session_id": self.session_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuditEvent':
        """Create from dictionary"""
        return cls(
            id=data["id"],
            timestamp=data["timestamp"],
            actor=data["actor"],
            action=AuditAction(data["action"]),
            subject_type=data["subject_type"],
            subject_id=data["subject_id"],
            payload=json.loads(data["payload"]),
            ip_address=data.get("ip_address"),
            user_agent=data.get("user_agent"),
            session_id=data.get("session_id")
        )

class AdminManager:
    """Admin management system"""
    
    def __init__(self, redis_client: redis.Redis, config: Dict[str, Any]):
        self.redis = redis_client
        self.config = config
        
        # Redis key prefixes
        self.template_prefix = "template:"
        self.audit_prefix = "audit:"
        self.admin_prefix = "admin:"
        self.session_prefix = "session:"
        
        # Initialize default templates
        self._init_default_templates()
    
    def _init_default_templates(self):
        """Initialize default workspace templates"""
        default_templates = [
            {
                "id": "dev-basic",
                "name": "Development Basic",
                "description": "Basic development environment with Node.js and Python",
                "image": "ghcr.io/coder/openvscode-server:latest",
                "cpu": "2.0",
                "ram": "4g",
                "disk_gb": 20,
                "gpu": False,
                "idle_timeout": 45,
                "environment_vars": {
                    "NODE_ENV": "development",
                    "PYTHON_VERSION": "3.9"
                },
                "labels": {
                    "category": "development",
                    "tier": "basic"
                }
            },
            {
                "id": "dev-plus",
                "name": "Development Plus",
                "description": "Enhanced development environment with more resources",
                "image": "ghcr.io/coder/openvscode-server:latest",
                "cpu": "4.0",
                "ram": "8g",
                "disk_gb": 40,
                "gpu": False,
                "idle_timeout": 120,
                "environment_vars": {
                    "NODE_ENV": "development",
                    "PYTHON_VERSION": "3.11"
                },
                "labels": {
                    "category": "development",
                    "tier": "plus"
                }
            },
            {
                "id": "dev-gpu",
                "name": "Development GPU",
                "description": "GPU-enabled development environment for ML/AI",
                "image": "ghcr.io/coder/openvscode-server:latest",
                "cpu": "6.0",
                "ram": "16g",
                "disk_gb": 60,
                "gpu": True,
                "gpu_type": "nvidia",
                "idle_timeout": 45,
                "environment_vars": {
                    "NODE_ENV": "development",
                    "PYTHON_VERSION": "3.11",
                    "CUDA_VISIBLE_DEVICES": "0"
                },
                "labels": {
                    "category": "development",
                    "tier": "premium",
                    "gpu": "true"
                }
            }
        ]
        
        for template_data in default_templates:
            template = WorkspaceTemplate(**template_data)
            if not self.get_template(template.id):
                self.create_template(template, "system")
    
    # Template Management
    def create_template(self, template: WorkspaceTemplate, created_by: str) -> bool:
        """Create a new workspace template"""
        try:
            # Validate template
            if not self._validate_template(template):
                return False
            
            # Check if template already exists
            if self.get_template(template.id):
                logger.warning(f"Template {template.id} already exists")
                return False
            
            # Set creation metadata
            template.created_by = created_by
            template.created_at = time.time()
            template.updated_at = time.time()
            
            # Store template
            template_key = f"{self.template_prefix}{template.id}"
            self.redis.set(template_key, json.dumps(template.to_dict()))
            
            # Add to template index
            self.redis.sadd("templates:active", template.id)
            
            # Audit event
            self._record_audit_event(
                actor=created_by,
                action=AuditAction.TEMPLATE_CREATED,
                subject_type="template",
                subject_id=template.id,
                payload=template.to_dict()
            )
            
            logger.info(f"Template {template.id} created by {created_by}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating template: {e}")
            return False
    
    def update_template(self, template_id: str, updates: Dict[str, Any], updated_by: str) -> bool:
        """Update an existing template"""
        try:
            # Get existing template
            existing = self.get_template(template_id)
            if not existing:
                logger.warning(f"Template {template_id} not found")
                return False
            
            # Apply updates
            for key, value in updates.items():
                if hasattr(existing, key) and key not in ['id', 'created_at', 'created_by']:
                    setattr(existing, key, value)
            
            existing.updated_at = time.time()
            
            # Validate updated template
            if not self._validate_template(existing):
                return False
            
            # Store updated template
            template_key = f"{self.template_prefix}{template_id}"
            self.redis.set(template_key, json.dumps(existing.to_dict()))
            
            # Update index if status changed
            if updates.get('status') == TemplateStatus.INACTIVE.value:
                self.redis.srem("templates:active", template_id)
            elif updates.get('status') == TemplateStatus.ACTIVE.value:
                self.redis.sadd("templates:active", template_id)
            
            # Audit event
            self._record_audit_event(
                actor=updated_by,
                action=AuditAction.TEMPLATE_UPDATED,
                subject_type="template",
                subject_id=template_id,
                payload={"updates": updates, "template": existing.to_dict()}
            )
            
            logger.info(f"Template {template_id} updated by {updated_by}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating template: {e}")
            return False
    
    def delete_template(self, template_id: str, deleted_by: str) -> bool:
        """Delete a template"""
        try:
            # Check if template exists
            if not self.get_template(template_id):
                logger.warning(f"Template {template_id} not found")
                return False
            
            # Check if template is in use
            if self._is_template_in_use(template_id):
                logger.warning(f"Template {template_id} is in use, cannot delete")
                return False
            
            # Remove from Redis
            template_key = f"{self.template_prefix}{template_id}"
            self.redis.delete(template_key)
            
            # Remove from index
            self.redis.srem("templates:active", template_id)
            
            # Audit event
            self._record_audit_event(
                actor=deleted_by,
                action=AuditAction.TEMPLATE_DELETED,
                subject_type="template",
                subject_id=template_id,
                payload={"deleted_at": time.time()}
            )
            
            logger.info(f"Template {template_id} deleted by {deleted_by}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting template: {e}")
            return False
    
    def get_template(self, template_id: str) -> Optional[WorkspaceTemplate]:
        """Get template by ID"""
        try:
            template_key = f"{self.template_prefix}{template_id}"
            template_data = self.redis.get(template_key)
            
            if template_data:
                return WorkspaceTemplate.from_dict(json.loads(template_data))
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting template: {e}")
            return None
    
    def list_templates(self, status: Optional[TemplateStatus] = None) -> List[WorkspaceTemplate]:
        """List templates with optional status filter"""
        try:
            templates = []
            
            if status:
                # Filter by status
                template_ids = self.redis.smembers(f"templates:{status.value}")
            else:
                # Get all templates
                template_ids = self.redis.smembers("templates:active")
                # Also get inactive templates
                inactive_ids = self.redis.smembers("templates:inactive")
                template_ids.update(inactive_ids)
            
            for template_id in template_ids:
                template = self.get_template(template_id)
                if template:
                    templates.append(template)
            
            # Sort by creation date
            templates.sort(key=lambda t: t.created_at, reverse=True)
            
            return templates
            
        except Exception as e:
            logger.error(f"Error listing templates: {e}")
            return []
    
    def _validate_template(self, template: WorkspaceTemplate) -> bool:
        """Validate template configuration"""
        try:
            # Required fields
            if not template.id or not template.name or not template.image:
                return False
            
            # Resource limits
            if template.cpu and not self._is_valid_cpu_limit(template.cpu):
                return False
            
            if template.ram and not self._is_valid_ram_limit(template.ram):
                return False
            
            if template.disk_gb <= 0 or template.disk_gb > 1000:
                return False
            
            # Timeouts
            if template.idle_timeout <= 0 or template.idle_timeout > 1440:
                return False
            
            if template.max_runtime <= 0 or template.max_runtime > 10080:  # 1 week
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Template validation error: {e}")
            return False
    
    def _is_valid_cpu_limit(self, cpu: str) -> bool:
        """Validate CPU limit format"""
        try:
            if cpu.endswith('.0'):
                cpu = cpu[:-2]
            return 0.5 <= float(cpu) <= 32.0
        except:
            return False
    
    def _is_valid_ram_limit(self, ram: str) -> bool:
        """Validate RAM limit format"""
        try:
            if ram.endswith('g'):
                value = int(ram[:-1])
            elif ram.endswith('m'):
                value = int(ram[:-1]) / 1024
            else:
                value = int(ram) / (1024 * 1024 * 1024)
            
            return 0.5 <= value <= 128.0
        except:
            return False
    
    def _is_template_in_use(self, template_id: str) -> bool:
        """Check if template is currently in use"""
        try:
            # Check for active workspaces using this template
            active_workspaces = self.redis.keys("workspace:*")
            for workspace_key in active_workspaces:
                workspace_data = self.redis.get(workspace_key)
                if workspace_data:
                    workspace = json.loads(workspace_data)
                    if workspace.get('template_id') == template_id:
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking template usage: {e}")
            return True  # Assume in use if error
    
    # Audit Management
    def _record_audit_event(
        self,
        actor: str,
        action: AuditAction,
        subject_type: str,
        subject_id: str,
        payload: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        """Record an audit event"""
        try:
            event = AuditEvent(
                id=self._generate_audit_id(),
                timestamp=time.time(),
                actor=actor,
                action=action,
                subject_type=subject_type,
                subject_id=subject_id,
                payload=payload,
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_id
            )
            
            # Store event
            event_key = f"{self.audit_prefix}{event.id}"
            self.redis.set(event_key, json.dumps(event.to_dict()))
            
            # Add to daily index
            date_key = datetime.now().strftime("%Y%m%d")
            self.redis.lpush(f"audit:{date_key}", event.id)
            
            # Keep only last 1000 events per day
            self.redis.ltrim(f"audit:{date_key}", 0, 999)
            
            # Add to actor index
            self.redis.lpush(f"audit:actor:{actor}", event.id)
            self.redis.ltrim(f"audit:actor:{actor}", 0, 999)
            
            # Add to subject index
            self.redis.lpush(f"audit:subject:{subject_type}:{subject_id}", event.id)
            self.redis.ltrim(f"audit:subject:{subject_type}:{subject_id}", 0, 999)
            
        except Exception as e:
            logger.error(f"Error recording audit event: {e}")
    
    def get_audit_events(
        self,
        actor: Optional[str] = None,
        action: Optional[AuditAction] = None,
        subject_type: Optional[str] = None,
        subject_id: Optional[str] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        limit: int = 100
    ) -> List[AuditEvent]:
        """Get audit events with filters"""
        try:
            events = []
            
            # Determine which index to use
            if actor:
                index_key = f"audit:actor:{actor}"
            elif subject_type and subject_id:
                index_key = f"audit:subject:{subject_type}:{subject_id}"
            else:
                # Use today's index
                date_key = datetime.now().strftime("%Y%m%d")
                index_key = f"audit:{date_key}"
            
            # Get event IDs
            event_ids = self.redis.lrange(index_key, 0, limit - 1)
            
            for event_id in event_ids:
                event = self._get_audit_event(event_id)
                if event:
                    # Apply filters
                    if action and event.action != action:
                        continue
                    if start_time and event.timestamp < start_time:
                        continue
                    if end_time and event.timestamp > end_time:
                        continue
                    
                    events.append(event)
            
            # Sort by timestamp
            events.sort(key=lambda e: e.timestamp, reverse=True)
            
            return events[:limit]
            
        except Exception as e:
            logger.error(f"Error getting audit events: {e}")
            return []
    
    def _get_audit_event(self, event_id: str) -> Optional[AuditEvent]:
        """Get audit event by ID"""
        try:
            event_key = f"{self.audit_prefix}{event_id}"
            event_data = self.redis.get(event_key)
            
            if event_data:
                return AuditEvent.from_dict(json.loads(event_data))
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting audit event: {e}")
            return None
    
    def _generate_audit_id(self) -> str:
        """Generate unique audit event ID"""
        timestamp = int(time.time() * 1000)
        random_part = os.urandom(4).hex()
        return f"audit_{timestamp}_{random_part}"
    
    # Admin Authentication
    def authenticate_admin(self, username: str, password: str, ip_address: str) -> Optional[str]:
        """Authenticate admin user"""
        try:
            # Get admin credentials
            admin_key = f"{self.admin_prefix}user:{username}"
            admin_data = self.redis.get(admin_key)
            
            if not admin_data:
                return None
            
            admin = json.loads(admin_data)
            
            # Check password
            if not bcrypt.checkpw(password.encode('utf-8'), admin['password_hash'].encode('utf-8')):
                return None
            
            # Check if account is active
            if not admin.get('active', True):
                return None
            
            # Generate session
            session_id = self._create_admin_session(username, ip_address)
            
            # Audit login
            self._record_audit_event(
                actor=username,
                action=AuditAction.ADMIN_LOGIN,
                subject_type="admin",
                subject_id=username,
                payload={"ip_address": ip_address, "session_id": session_id}
            )
            
            return session_id
            
        except Exception as e:
            logger.error(f"Admin authentication error: {e}")
            return None
    
    def _create_admin_session(self, username: str, ip_address: str) -> str:
        """Create admin session"""
        try:
            session_id = os.urandom(16).hex()
            session_data = {
                "username": username,
                "ip_address": ip_address,
                "created_at": time.time(),
                "last_activity": time.time()
            }
            
            session_key = f"{self.session_prefix}{session_id}"
            self.redis.setex(session_key, 3600, json.dumps(session_data))  # 1 hour TTL
            
            return session_id
            
        except Exception as e:
            logger.error(f"Error creating admin session: {e}")
            return ""
    
    def validate_admin_session(self, session_id: str) -> Optional[str]:
        """Validate admin session and return username"""
        try:
            session_key = f"{self.session_prefix}{session_id}"
            session_data = self.redis.get(session_key)
            
            if not session_data:
                return None
            
            session = json.loads(session_data)
            
            # Update last activity
            session['last_activity'] = time.time()
            self.redis.setex(session_key, 3600, json.dumps(session))
            
            return session['username']
            
        except Exception as e:
            logger.error(f"Error validating admin session: {e}")
            return None
    
    def logout_admin(self, session_id: str):
        """Logout admin user"""
        try:
            session_key = f"{self.session_prefix}{session_id}"
            self.redis.delete(session_key)
            
        except Exception as e:
            logger.error(f"Error logging out admin: {e}")
    
    # System Configuration
    def get_system_config(self) -> Dict[str, Any]:
        """Get system configuration"""
        try:
            config_key = f"{self.admin_prefix}system:config"
            config_data = self.redis.get(config_key)
            
            if config_data:
                return json.loads(config_data)
            
            # Return default config
            return self._get_default_system_config()
            
        except Exception as e:
            logger.error(f"Error getting system config: {e}")
            return {}
    
    def update_system_config(self, updates: Dict[str, Any], updated_by: str) -> bool:
        """Update system configuration"""
        try:
            current_config = self.get_system_config()
            current_config.update(updates)
            
            # Store updated config
            config_key = f"{self.admin_prefix}system:config"
            self.redis.set(config_key, json.dumps(current_config))
            
            # Audit event
            self._record_audit_event(
                actor=updated_by,
                action=AuditAction.SYSTEM_CONFIG_CHANGED,
                subject_type="system",
                subject_id="config",
                payload={"updates": updates, "config": current_config}
            )
            
            logger.info(f"System config updated by {updated_by}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating system config: {e}")
            return False
    
    def _get_default_system_config(self) -> Dict[str, Any]:
        """Get default system configuration"""
        return {
            "max_workspaces_per_user": 5,
            "default_idle_timeout": 45,
            "max_workspace_runtime": 1440,
            "port_range_start": 13001,
            "port_range_end": 65535,
            "notification_channels": ["email"],
            "webhook_rate_limit": 100,
            "webhook_rate_limit_window": 60,
            "audit_retention_days": 90,
            "backup_enabled": True,
            "backup_interval_hours": 24
        }
    
    # Break-glass Operations
    def break_glass_provision(
        self,
        username: str,
        email: str,
        plan: str,
        admin_user: str,
        reason: str,
        ip_address: str
    ) -> Dict[str, Any]:
        """Emergency provision of workspace (break-glass)"""
        try:
            # Validate admin session
            if not self.validate_admin_session(admin_user):
                raise ValueError("Invalid admin session")
            
            # Create emergency provision job
            provision_job = {
                "idempotency_key": f"break_glass_{int(time.time())}",
                "user": {
                    "username": username,
                    "email": email
                },
                "plan": plan,
                "emergency": True,
                "admin_user": admin_user,
                "reason": reason,
                "created_at": time.time()
            }
            
            # Store emergency job
            job_key = f"emergency_provision:{provision_job['idempotency_key']}"
            self.redis.setex(job_key, 3600, json.dumps(provision_job))  # 1 hour TTL
            
            # Add to emergency queue
            self.redis.lpush("emergency_provision_queue", json.dumps(provision_job))
            
            # Audit event
            self._record_audit_event(
                actor=admin_user,
                action=AuditAction.BREAK_GLASS,
                subject_type="workspace",
                subject_id=username,
                payload={
                    "action": "emergency_provision",
                    "plan": plan,
                    "reason": reason,
                    "ip_address": ip_address
                },
                ip_address=ip_address
            )
            
            logger.warning(f"Break-glass provision initiated by {admin_user} for {username}")
            
            return {
                "status": "initiated",
                "job_id": provision_job['idempotency_key'],
                "message": "Emergency provision job created"
            }
            
        except Exception as e:
            logger.error(f"Break-glass provision error: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    # Health and Status
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        try:
            status = {
                "templates": {
                    "total": len(self.list_templates()),
                    "active": len(self.list_templates(TemplateStatus.ACTIVE)),
                    "inactive": len(self.list_templates(TemplateStatus.INACTIVE))
                },
                "audit": {
                    "total_today": len(self.get_audit_events(limit=1000)),
                    "recent_events": len(self.get_audit_events(limit=10))
                },
                "admin": {
                    "active_sessions": len(self.redis.keys(f"{self.session_prefix}*"))
                },
                "system": {
                    "config": self.get_system_config(),
                    "redis_connected": self.redis.ping() if self.redis else False
                }
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {"error": str(e)}
