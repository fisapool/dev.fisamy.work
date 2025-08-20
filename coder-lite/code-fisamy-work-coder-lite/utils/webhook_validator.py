#!/usr/bin/env python3
"""
Webhook signature validation for Coder-lite Provision System
Supports multiple providers with constant-time comparison
"""

import os
import hmac
import hashlib
import time
import logging
from typing import Dict, Any, Optional, Union
from enum import Enum
import json
from urllib.parse import parse_qs

logger = logging.getLogger(__name__)

class WebhookProvider(Enum):
    """Supported webhook providers"""
    STRIPE = "stripe"
    SHOPEE = "shopee"
    GENERIC = "generic"
    TEST = "test"

class WebhookValidator:
    """Webhook signature validator with provider-specific logic"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.secrets = config.get('webhook_secrets', {})
        self.tolerance = config.get('webhook_tolerance', 300)  # 5 minutes
    
    def validate_webhook(
        self,
        provider: WebhookProvider,
        request_body: bytes,
        headers: Dict[str, str],
        signature: Optional[str] = None
    ) -> bool:
        """
        Validate webhook signature based on provider
        
        Args:
            provider: Webhook provider
            request_body: Raw request body
            headers: Request headers
            signature: Optional signature override
            
        Returns:
            True if valid, False otherwise
        """
        try:
            if provider == WebhookProvider.STRIPE:
                return self._validate_stripe_webhook(request_body, headers, signature)
            elif provider == WebhookProvider.SHOPEE:
                return self._validate_shopee_webhook(request_body, headers, signature)
            elif provider == WebhookProvider.GENERIC:
                return self._validate_generic_webhook(request_body, headers, signature)
            elif provider == WebhookProvider.TEST:
                return self._validate_test_webhook(request_body, headers, signature)
            else:
                logger.warning(f"Unknown webhook provider: {provider}")
                return False
                
        except Exception as e:
            logger.error(f"Webhook validation error: {e}")
            return False
    
    def _validate_stripe_webhook(
        self,
        request_body: bytes,
        headers: Dict[str, str],
        signature: Optional[str] = None
    ) -> bool:
        """Validate Stripe webhook signature"""
        try:
            # Get signature from headers
            stripe_signature = signature or headers.get('stripe-signature')
            if not stripe_signature:
                logger.warning("No Stripe signature found in headers")
                return False
            
            # Get webhook secret
            webhook_secret = self.secrets.get('stripe')
            if not webhook_secret:
                logger.warning("No Stripe webhook secret configured")
                return False
            
            # Parse signature header
            # Format: t=timestamp,v1=signature
            signature_parts = stripe_signature.split(',')
            timestamp = None
            expected_signature = None
            
            for part in signature_parts:
                if part.startswith('t='):
                    timestamp = int(part[2:])
                elif part.startswith('v1='):
                    expected_signature = part[3:]
            
            if not timestamp or not expected_signature:
                logger.warning("Invalid Stripe signature format")
                return False
            
            # Check timestamp tolerance
            current_time = int(time.time())
            if abs(current_time - timestamp) > self.tolerance:
                logger.warning(f"Webhook timestamp too old: {current_time - timestamp}s")
                return False
            
            # Calculate expected signature
            signed_payload = f"{timestamp}.{request_body.decode('utf-8')}"
            expected_sig = hmac.new(
                webhook_secret.encode('utf-8'),
                signed_payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Constant-time comparison
            return hmac.compare_digest(expected_sig, expected_signature)
            
        except Exception as e:
            logger.error(f"Stripe webhook validation error: {e}")
            return False
    
    def _validate_shopee_webhook(
        self,
        request_body: bytes,
        headers: Dict[str, str],
        signature: Optional[str] = None
    ) -> bool:
        """Validate Shopee webhook signature"""
        try:
            # Get signature from headers or query params
            shopee_signature = signature or headers.get('x-shopee-signature')
            if not shopee_signature:
                logger.warning("No Shopee signature found")
                return False
            
            # Get webhook secret
            webhook_secret = self.secrets.get('shopee')
            if not webhook_secret:
                logger.warning("No Shopee webhook secret configured")
                return False
            
            # Shopee uses HMAC-SHA256 with request body
            expected_sig = hmac.new(
                webhook_secret.encode('utf-8'),
                request_body,
                hashlib.sha256
            ).hexdigest()
            
            # Constant-time comparison
            return hmac.compare_digest(expected_sig, shopee_signature)
            
        except Exception as e:
            logger.error(f"Shopee webhook validation error: {e}")
            return False
    
    def _validate_generic_webhook(
        self,
        request_body: bytes,
        headers: Dict[str, str],
        signature: Optional[str] = None
    ) -> bool:
        """Validate generic webhook with configurable signature method"""
        try:
            # Get signature from headers
            sig_header = self.config.get('generic_signature_header', 'x-signature')
            generic_signature = signature or headers.get(sig_header)
            if not generic_signature:
                logger.warning(f"No generic signature found in {sig_header}")
                return False
            
            # Get webhook secret
            webhook_secret = self.secrets.get('generic')
            if not webhook_secret:
                logger.warning("No generic webhook secret configured")
                return False
            
            # Get signature method
            sig_method = self.config.get('generic_signature_method', 'sha256')
            
            if sig_method == 'sha256':
                expected_sig = hmac.new(
                    webhook_secret.encode('utf-8'),
                    request_body,
                    hashlib.sha256
                ).hexdigest()
            elif sig_method == 'sha1':
                expected_sig = hmac.new(
                    webhook_secret.encode('utf-8'),
                    request_body,
                    hashlib.sha1
                ).hexdigest()
            elif sig_method == 'md5':
                expected_sig = hmac.new(
                    webhook_secret.encode('utf-8'),
                    request_body,
                    hashlib.md5
                ).hexdigest()
            else:
                logger.warning(f"Unsupported signature method: {sig_method}")
                return False
            
            # Constant-time comparison
            return hmac.compare_digest(expected_sig, generic_signature)
            
        except Exception as e:
            logger.error(f"Generic webhook validation error: {e}")
            return False
    
    def _validate_test_webhook(
        self,
        request_body: bytes,
        headers: Dict[str, str],
        signature: Optional[str] = None
    ) -> bool:
        """Validate test webhook (always returns True in test mode)"""
        # In test mode, accept all webhooks
        # In production, this should be disabled
        if self.config.get('test_mode', False):
            logger.info("Test webhook accepted (test mode enabled)")
            return True
        else:
            logger.warning("Test webhook rejected (test mode disabled)")
            return False
    
    def extract_provider_from_request(
        self,
        headers: Dict[str, str],
        body: Union[str, bytes, Dict[str, Any]]
    ) -> WebhookProvider:
        """Extract webhook provider from request"""
        try:
            # Check for provider-specific headers
            if 'stripe-signature' in headers:
                return WebhookProvider.STRIPE
            elif 'x-shopee-signature' in headers:
                return WebhookProvider.SHOPEE
            elif 'x-signature' in headers:
                return WebhookProvider.GENERIC
            
            # Check body content for provider hints
            if isinstance(body, bytes):
                body_str = body.decode('utf-8')
            elif isinstance(body, str):
                body_str = body
            else:
                body_str = json.dumps(body)
            
            # Look for provider indicators in body
            if '"stripe"' in body_str.lower() or '"stripe_event"' in body_str:
                return WebhookProvider.STRIPE
            elif '"shopee"' in body_str.lower() or '"shopee_order"' in body_str:
                return WebhookProvider.SHOPEE
            
            # Default to generic
            return WebhookProvider.GENERIC
            
        except Exception as e:
            logger.error(f"Error extracting provider: {e}")
            return WebhookProvider.GENERIC
    
    def validate_timestamp(
        self,
        timestamp: Union[int, float, str],
        tolerance: Optional[int] = None
    ) -> bool:
        """Validate webhook timestamp"""
        try:
            if isinstance(timestamp, str):
                timestamp = float(timestamp)
            elif isinstance(timestamp, float):
                timestamp = int(timestamp)
            
            current_time = int(time.time())
            max_age = tolerance or self.tolerance
            
            return abs(current_time - timestamp) <= max_age
            
        except Exception as e:
            logger.error(f"Timestamp validation error: {e}")
            return False
    
    def get_webhook_secret(self, provider: WebhookProvider) -> Optional[str]:
        """Get webhook secret for provider"""
        return self.secrets.get(provider.value)
    
    def set_webhook_secret(self, provider: WebhookProvider, secret: str):
        """Set webhook secret for provider"""
        self.secrets[provider.value] = secret
        logger.info(f"Updated webhook secret for {provider.value}")
    
    def rotate_webhook_secret(self, provider: WebhookProvider) -> str:
        """Generate new webhook secret for provider"""
        import secrets
        
        new_secret = secrets.token_urlsafe(32)
        self.set_webhook_secret(provider, new_secret)
        
        logger.info(f"Rotated webhook secret for {provider.value}")
        return new_secret

# Utility functions for common webhook operations
def parse_webhook_body(body: Union[str, bytes]) -> Dict[str, Any]:
    """Parse webhook body safely"""
    try:
        if isinstance(body, bytes):
            body_str = body.decode('utf-8')
        else:
            body_str = body
        
        # Try JSON first
        try:
            return json.loads(body_str)
        except json.JSONDecodeError:
            pass
        
        # Try URL-encoded form data
        try:
            parsed = parse_qs(body_str)
            # Convert single-item lists to values
            result = {}
            for key, values in parsed.items():
                if len(values) == 1:
                    result[key] = values[0]
                else:
                    result[key] = values
            return result
        except Exception:
            pass
        
        # Return as string if all else fails
        return {"raw_body": body_str}
        
    except Exception as e:
        logger.error(f"Error parsing webhook body: {e}")
        return {"error": str(e)}

def extract_order_data(
    provider: WebhookProvider,
    body: Dict[str, Any]
) -> Dict[str, Any]:
    """Extract standardized order data from provider-specific webhook"""
    try:
        if provider == WebhookProvider.STRIPE:
            return _extract_stripe_order_data(body)
        elif provider == WebhookProvider.SHOPEE:
            return _extract_shopee_order_data(body)
        else:
            return _extract_generic_order_data(body)
            
    except Exception as e:
        logger.error(f"Error extracting order data: {e}")
        return {}

def _extract_stripe_order_data(body: Dict[str, Any]) -> Dict[str, Any]:
    """Extract order data from Stripe webhook"""
    try:
        event_type = body.get('type', '')
        
        if event_type == 'checkout.session.completed':
            session = body.get('data', {}).get('object', {})
            return {
                'provider': 'stripe',
                'order_id': session.get('id'),
                'customer_email': session.get('customer_details', {}).get('email'),
                'amount_total': session.get('amount_total'),
                'currency': session.get('currency'),
                'payment_status': session.get('payment_status'),
                'metadata': session.get('metadata', {}),
                'created': session.get('created')
            }
        elif event_type == 'invoice.payment_succeeded':
            invoice = body.get('data', {}).get('object', {})
            return {
                'provider': 'stripe',
                'order_id': invoice.get('id'),
                'customer_email': invoice.get('customer_email'),
                'amount_paid': invoice.get('amount_paid'),
                'currency': invoice.get('currency'),
                'payment_status': 'paid',
                'metadata': invoice.get('metadata', {}),
                'created': invoice.get('created')
            }
        
        return {}
        
    except Exception as e:
        logger.error(f"Error extracting Stripe order data: {e}")
        return {}

def _extract_shopee_order_data(body: Dict[str, Any]) -> Dict[str, Any]:
    """Extract order data from Shopee webhook"""
    try:
        return {
            'provider': 'shopee',
            'order_id': body.get('order_id') or body.get('orderId'),
            'customer_email': body.get('customer_email') or body.get('email'),
            'amount_total': body.get('amount') or body.get('total_amount'),
            'currency': body.get('currency', 'MYR'),
            'payment_status': body.get('status') or body.get('payment_status'),
            'metadata': {
                'shop_id': body.get('shop_id'),
                'order_sn': body.get('order_sn'),
                'order_status': body.get('order_status')
            },
            'created': body.get('create_time') or body.get('created_at')
        }
        
    except Exception as e:
        logger.error(f"Error extracting Shopee order data: {e}")
        return {}

def _extract_generic_order_data(body: Dict[str, Any]) -> Dict[str, Any]:
    """Extract order data from generic webhook"""
    try:
        return {
            'provider': 'generic',
            'order_id': body.get('order_id') or body.get('id'),
            'customer_email': body.get('customer_email') or body.get('email'),
            'amount_total': body.get('amount') or body.get('total'),
            'currency': body.get('currency', 'USD'),
            'payment_status': body.get('status') or body.get('payment_status'),
            'metadata': body.get('metadata', {}),
            'created': body.get('created_at') or body.get('timestamp')
        }
        
    except Exception as e:
        logger.error(f"Error extracting generic order data: {e}")
        return {}

# Rate limiting for webhook endpoints
class WebhookRateLimiter:
    """Rate limiter for webhook endpoints"""
    
    def __init__(self, redis_client, config: Dict[str, Any]):
        self.redis = redis_client
        self.config = config
        self.rate_limit = config.get('webhook_rate_limit', 100)  # requests per minute
        self.rate_limit_window = config.get('webhook_rate_limit_window', 60)  # seconds
    
    def is_allowed(self, identifier: str) -> bool:
        """Check if webhook request is allowed"""
        try:
            key = f"webhook_rate_limit:{identifier}"
            current_count = self.redis.get(key)
            
            if current_count is None:
                # First request in window
                self.redis.setex(key, self.rate_limit_window, 1)
                return True
            
            current_count = int(current_count)
            if current_count >= self.rate_limit:
                return False
            
            # Increment counter
            self.redis.incr(key)
            return True
            
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            # Allow request if rate limiting fails
            return True
    
    def get_remaining_requests(self, identifier: str) -> int:
        """Get remaining requests for identifier"""
        try:
            key = f"webhook_rate_limit:{identifier}"
            current_count = self.redis.get(key)
            
            if current_count is None:
                return self.rate_limit
            
            return max(0, self.rate_limit - int(current_count))
            
        except Exception as e:
            logger.error(f"Error getting remaining requests: {e}")
            return 0
