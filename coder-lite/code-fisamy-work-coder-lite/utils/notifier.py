#!/usr/bin/env python3
"""
Notification system for Coder-lite Provision System
Supports multiple channels with retry logic and dead letter queue
"""

import os
import time
import logging
import json
import hashlib
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import redis
import requests
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class NotificationChannel(Enum):
    """Supported notification channels"""
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"

@dataclass
class NotificationMessage:
    """Notification message structure"""
    channel: NotificationChannel
    recipient: str
    subject: str
    body: str
    template: str
    metadata: Dict[str, Any]
    priority: int = 5  # 1=high, 5=normal, 10=low
    retry_count: int = 0
    max_retries: int = 3
    created_at: float = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Redis storage"""
        return {
            "channel": self.channel.value,
            "recipient": self.recipient,
            "subject": self.subject,
            "body": self.body,
            "template": self.template,
            "metadata": json.dumps(self.metadata),
            "priority": self.priority,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NotificationMessage':
        """Create from dictionary from Redis"""
        return cls(
            channel=NotificationChannel(data["channel"]),
            recipient=data["recipient"],
            subject=data["subject"],
            body=data["body"],
            template=data["template"],
            metadata=json.loads(data["metadata"]),
            priority=int(data["priority"]),
            retry_count=int(data["retry_count"]),
            max_retries=int(data["max_retries"]),
            created_at=float(data["created_at"])
        )

class NotificationProvider:
    """Base class for notification providers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = self.__class__.__name__
    
    async def send(self, message: NotificationMessage) -> bool:
        """Send notification - to be implemented by subclasses"""
        raise NotImplementedError
    
    def validate_config(self) -> bool:
        """Validate provider configuration"""
        raise NotImplementedError

class EmailProvider(NotificationProvider):
    """SMTP-based email provider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.smtp_host = config.get('smtp_host', 'localhost')
        self.smtp_port = config.get('smtp_port', 587)
        self.smtp_user = config.get('smtp_user')
        self.smtp_password = config.get('smtp_password')
        self.from_email = config.get('from_email', 'noreply@code.fisamy.work')
        self.use_tls = config.get('use_tls', True)
    
    def validate_config(self) -> bool:
        """Validate SMTP configuration"""
        required = ['smtp_host', 'smtp_user', 'smtp_password']
        return all(self.config.get(key) for key in required)
    
    async def send(self, message: NotificationMessage) -> bool:
        """Send email via SMTP"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = message.recipient
            msg['Subject'] = message.subject
            
            # Add body
            msg.attach(MIMEText(message.body, 'html'))
            
            # Send via SMTP
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {message.recipient}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {message.recipient}: {e}")
            return False

class WhatsAppProvider(NotificationProvider):
    """WhatsApp Business API provider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_token = config.get('whatsapp_token')
        self.phone_number_id = config.get('phone_number_id')
        self.api_version = config.get('api_version', 'v18.0')
        self.base_url = f"https://graph.facebook.com/{self.api_version}"
    
    def validate_config(self) -> bool:
        """Validate WhatsApp configuration"""
        required = ['whatsapp_token', 'phone_number_id']
        return all(self.config.get(key) for key in required)
    
    async def send(self, message: NotificationMessage) -> bool:
        """Send WhatsApp message via Business API"""
        try:
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            
            payload = {
                "messaging_product": "whatsapp",
                "to": message.recipient,
                "type": "text",
                "text": {"body": message.body}
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            logger.info(f"WhatsApp message sent successfully to {message.recipient}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message to {message.recipient}: {e}")
            return False

class TelegramProvider(NotificationProvider):
    """Telegram Bot API provider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.bot_token = config.get('telegram_bot_token')
        self.chat_id = config.get('telegram_chat_id')
        self.api_url = "https://api.telegram.org"
    
    def validate_config(self) -> bool:
        """Validate Telegram configuration"""
        required = ['telegram_bot_token', 'telegram_chat_id']
        return all(self.config.get(key) for key in required)
    
    async def send(self, message: NotificationMessage) -> bool:
        """Send Telegram message via Bot API"""
        try:
            url = f"{self.api_url}/bot{self.bot_token}/sendMessage"
            
            payload = {
                "chat_id": self.chat_id,
                "text": f"*{message.subject}*\n\n{message.body}",
                "parse_mode": "Markdown"
            }
            
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            logger.info(f"Telegram message sent successfully to {message.recipient}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send Telegram message to {message.recipient}: {e}")
            return False

class NotificationManager:
    """Main notification manager with retry logic and DLQ"""
    
    def __init__(self, redis_client: redis.Redis, config: Dict[str, Any]):
        self.redis = redis_client
        self.config = config
        self.providers: Dict[NotificationChannel, NotificationProvider] = {}
        
        # Initialize providers
        self._init_providers()
        
        # Queue names
        self.notification_queue = "notifications"
        self.dead_letter_queue = "notifications_dlq"
        self.retry_queue = "notifications_retry"
        
        # Metrics
        self.metrics = {
            "sent": 0,
            "failed": 0,
            "retried": 0,
            "dlq": 0
        }
    
    def _init_providers(self):
        """Initialize notification providers based on config"""
        # Email provider
        if self.config.get('email_enabled', True):
            email_config = {
                'smtp_host': self.config.get('smtp_host'),
                'smtp_port': self.config.get('smtp_port'),
                'smtp_user': self.config.get('smtp_user'),
                'smtp_password': self.config.get('smtp_password'),
                'from_email': self.config.get('from_email')
            }
            if all(email_config.values()):
                self.providers[NotificationChannel.EMAIL] = EmailProvider(email_config)
        
        # WhatsApp provider
        if self.config.get('whatsapp_enabled', False):
            whatsapp_config = {
                'whatsapp_token': self.config.get('whatsapp_token'),
                'phone_number_id': self.config.get('phone_number_id')
            }
            if all(whatsapp_config.values()):
                self.providers[NotificationChannel.WHATSAPP] = WhatsAppProvider(whatsapp_config)
        
        # Telegram provider
        if self.config.get('telegram_enabled', False):
            telegram_config = {
                'telegram_bot_token': self.config.get('telegram_bot_token'),
                'telegram_chat_id': self.config.get('telegram_chat_id')
            }
            if all(telegram_config.values()):
                self.providers[NotificationChannel.TELEGRAM] = TelegramProvider(telegram_config)
        
        logger.info(f"Initialized {len(self.providers)} notification providers")
    
    def enqueue_notification(self, message: NotificationMessage) -> bool:
        """Add notification to queue"""
        try:
            # Validate message
            if not message.recipient or not message.body:
                logger.error("Invalid notification message")
                return False
            
            # Check if provider is available
            if message.channel not in self.providers:
                logger.error(f"No provider available for channel: {message.channel}")
                return False
            
            # Add to queue with priority
            queue_data = message.to_dict()
            queue_data['id'] = self._generate_message_id(message)
            
            # Use Redis sorted set for priority queue
            score = message.priority + (time.time() / 1000000)  # Priority + timestamp for FIFO
            self.redis.zadd(self.notification_queue, {json.dumps(queue_data): score})
            
            logger.info(f"Notification enqueued for {message.recipient} via {message.channel}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to enqueue notification: {e}")
            return False
    
    def process_notifications(self, batch_size: int = 10) -> int:
        """Process notifications from queue"""
        processed = 0
        
        try:
            # Get batch of notifications (highest priority first)
            notifications = self.redis.zrange(self.notification_queue, 0, batch_size - 1, withscores=True)
            
            for notification_data, score in notifications:
                try:
                    # Parse notification
                    message_data = json.loads(notification_data)
                    message = NotificationMessage.from_dict(message_data)
                    
                    # Try to send
                    success = self._send_notification(message)
                    
                    if success:
                        # Remove from queue
                        self.redis.zrem(self.notification_queue, notification_data)
                        self.metrics["sent"] += 1
                        processed += 1
                    else:
                        # Handle retry logic
                        self._handle_retry(message, notification_data)
                
                except Exception as e:
                    logger.error(f"Error processing notification: {e}")
                    # Move to DLQ
                    self._move_to_dlq(notification_data, str(e))
            
            # Process retry queue
            self._process_retry_queue()
            
        except Exception as e:
            logger.error(f"Error in notification processing: {e}")
        
        return processed
    
    def _send_notification(self, message: NotificationMessage) -> bool:
        """Send notification via appropriate provider"""
        try:
            provider = self.providers[message.channel]
            return provider.send(message)
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return False
    
    def _handle_retry(self, message: NotificationMessage, notification_data: str):
        """Handle retry logic for failed notifications"""
        if message.retry_count < message.max_retries:
            # Increment retry count and add to retry queue
            message.retry_count += 1
            message.created_at = time.time()  # Update timestamp
            
            retry_data = message.to_dict()
            retry_data['id'] = self._generate_message_id(message)
            
            # Add to retry queue with exponential backoff
            retry_delay = min(300, 2 ** message.retry_count)  # Max 5 minutes
            retry_score = time.time() + retry_delay
            
            self.redis.zadd(self.retry_queue, {json.dumps(retry_data): retry_score})
            self.redis.zrem(self.notification_queue, notification_data)
            
            self.metrics["retried"] += 1
            logger.info(f"Notification queued for retry {message.retry_count}/{message.max_retries}")
        else:
            # Max retries exceeded, move to DLQ
            self._move_to_dlq(notification_data, "Max retries exceeded")
            self.redis.zrem(self.notification_queue, notification_data)
    
    def _process_retry_queue(self):
        """Process notifications in retry queue"""
        try:
            current_time = time.time()
            retry_notifications = self.redis.zrangebyscore(self.retry_queue, 0, current_time, withscores=True)
            
            for notification_data, score in retry_notifications:
                try:
                    message_data = json.loads(notification_data)
                    message = NotificationMessage.from_dict(message_data)
                    
                    # Try to send again
                    success = self._send_notification(message)
                    
                    if success:
                        # Remove from retry queue
                        self.redis.zrem(self.retry_queue, notification_data)
                        self.metrics["sent"] += 1
                    else:
                        # Handle retry logic again
                        self._handle_retry(message, notification_data)
                
                except Exception as e:
                    logger.error(f"Error processing retry notification: {e}")
                    self._move_to_dlq(notification_data, str(e))
                    self.redis.zrem(self.retry_queue, notification_data)
        
        except Exception as e:
            logger.error(f"Error processing retry queue: {e}")
    
    def _move_to_dlq(self, notification_data: str, reason: str):
        """Move notification to dead letter queue"""
        try:
            dlq_entry = {
                "notification": notification_data,
                "reason": reason,
                "timestamp": time.time()
            }
            
            self.redis.lpush(self.dead_letter_queue, json.dumps(dlq_entry))
            self.metrics["dlq"] += 1
            
            logger.warning(f"Notification moved to DLQ: {reason}")
        
        except Exception as e:
            logger.error(f"Failed to move notification to DLQ: {e}")
    
    def _generate_message_id(self, message: NotificationMessage) -> str:
        """Generate unique message ID"""
        content = f"{message.channel}:{message.recipient}:{message.subject}:{message.body}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        try:
            return {
                "main_queue": self.redis.zcard(self.notification_queue),
                "retry_queue": self.redis.zcard(self.retry_queue),
                "dead_letter_queue": self.redis.llen(self.dead_letter_queue),
                "metrics": self.metrics.copy()
            }
        except Exception as e:
            logger.error(f"Error getting queue status: {e}")
            return {}
    
    def clear_dlq(self) -> int:
        """Clear dead letter queue (admin function)"""
        try:
            count = self.redis.llen(self.dead_letter_queue)
            self.redis.delete(self.dead_letter_queue)
            self.metrics["dlq"] = 0
            logger.info(f"Cleared DLQ with {count} messages")
            return count
        except Exception as e:
            logger.error(f"Error clearing DLQ: {e}")
            return 0

# Template functions for common notifications
def create_workspace_access_notification(
    user_email: str,
    username: str,
    workspace_url: str,
    password: str,
    plan: str,
    channel: NotificationChannel = NotificationChannel.EMAIL
) -> NotificationMessage:
    """Create workspace access notification"""
    
    if channel == NotificationChannel.EMAIL:
        subject = f"Your {plan} Workspace is Ready! 🚀"
        body = f"""
        <html>
        <body>
            <h2>Welcome to Code.fisamy.work! 🎉</h2>
            <p>Your development workspace is now ready and accessible.</p>
            
            <h3>Access Details:</h3>
            <ul>
                <li><strong>Workspace URL:</strong> <a href="{workspace_url}">{workspace_url}</a></li>
                <li><strong>Username:</strong> {username}</li>
                <li><strong>Password:</strong> {password}</li>
                <li><strong>Plan:</strong> {plan}</li>
            </ul>
            
            <h3>Quick Start:</h3>
            <ol>
                <li>Click the workspace URL above</li>
                <li>Enter your username and password</li>
                <li>Start coding immediately!</li>
            </ol>
            
            <p><strong>Security Note:</strong> Keep your password safe and don't share it with others.</p>
            
            <p>Need help? Contact our support team.</p>
            
            <p>Happy coding! 🖥️💻</p>
        </body>
        </html>
        """
    
    elif channel == NotificationChannel.WHATSAPP:
        subject = "Workspace Ready"
        body = f"""🚀 Your {plan} workspace is ready!

📍 Access URL: {workspace_url}
👤 Username: {username}
🔑 Password: {password}

Quick start:
1. Click the URL
2. Login with credentials above
3. Start coding!

Need help? Contact support."""
    
    elif channel == NotificationChannel.TELEGRAM:
        subject = "Workspace Ready"
        body = f"""🚀 Your {plan} workspace is ready!

📍 Access URL: {workspace_url}
👤 Username: {username}
🔑 Password: {password}

Quick start:
1. Click the URL
2. Login with credentials above
3. Start coding!

Need help? Contact support."""
    
    return NotificationMessage(
        channel=channel,
        recipient=user_email,
        subject=subject,
        body=body,
        template="workspace_access",
        metadata={
            "username": username,
            "workspace_url": workspace_url,
            "plan": plan,
            "notification_type": "workspace_access"
        },
        priority=1  # High priority
    )

def create_workspace_suspended_notification(
    user_email: str,
    username: str,
    reason: str,
    channel: NotificationChannel = NotificationChannel.EMAIL
) -> NotificationMessage:
    """Create workspace suspended notification"""
    
    subject = "Workspace Access Suspended ⚠️"
    body = f"""
    <html>
    <body>
        <h2>Workspace Access Suspended</h2>
        <p>Your workspace access has been temporarily suspended.</p>
        
        <h3>Details:</h3>
        <ul>
            <li><strong>Username:</strong> {username}</li>
            <li><strong>Reason:</strong> {reason}</li>
        </ul>
        
        <p>To restore access, please contact our support team.</p>
        
        <p>We're here to help! 📧</p>
    </body>
    </html>
    """
    
    return NotificationMessage(
        channel=channel,
        recipient=user_email,
        subject=subject,
        body=body,
        template="workspace_suspended",
        metadata={
            "username": username,
            "reason": reason,
            "notification_type": "workspace_suspended"
        },
        priority=3  # Medium priority
    )
