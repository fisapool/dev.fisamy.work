import redis
import time
import uuid
import logging
from typing import Optional, Callable, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class DistributedLock:
    """Redis-based distributed lock with automatic cleanup"""
    
    def __init__(self, redis_client: redis.Redis, lock_prefix: str = "lock"):
        self.redis = redis_client
        self.lock_prefix = lock_prefix
        
    def acquire_lock(self, key: str, ttl_ms: int = 60000) -> Optional[str]:
        """
        Acquire a distributed lock
        
        Args:
            key: Lock key
            ttl_ms: Lock TTL in milliseconds
            
        Returns:
            Lock token if acquired, None if already locked
        """
        lock_key = f"{self.lock_prefix}:{key}"
        token = str(uuid.uuid4())
        
        # Use SET with NX (only if not exists) and PX (expire in milliseconds)
        acquired = self.redis.set(lock_key, token, nx=True, px=ttl_ms)
        
        if acquired:
            logger.debug(f"Lock acquired: {lock_key} with token {token}")
            return token
        else:
            logger.debug(f"Lock already held: {lock_key}")
            return None
    
    def release_lock(self, key: str, token: str) -> bool:
        """
        Release a distributed lock using Lua script for atomicity
        
        Args:
            key: Lock key
            token: Lock token returned by acquire_lock
            
        Returns:
            True if lock was released, False otherwise
        """
        lock_key = f"{self.lock_prefix}:{key}"
        
        # Lua script to ensure atomic check-and-delete
        lua_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        
        result = self.redis.eval(lua_script, 1, lock_key, token)
        released = bool(result)
        
        if released:
            logger.debug(f"Lock released: {lock_key}")
        else:
            logger.warning(f"Failed to release lock: {lock_key} (token mismatch or expired)")
            
        return released
    
    def extend_lock(self, key: str, token: str, ttl_ms: int = 60000) -> bool:
        """
        Extend lock TTL if still held
        
        Args:
            key: Lock key
            token: Lock token
            ttl_ms: New TTL in milliseconds
            
        Returns:
            True if lock was extended, False otherwise
        """
        lock_key = f"{self.lock_prefix}:{key}"
        
        # Lua script to extend TTL only if token matches
        lua_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("pexpire", KEYS[1], ARGV[2])
        else
            return 0
        end
        """
        
        result = self.redis.eval(lua_script, 1, lock_key, token, ttl_ms)
        extended = bool(result)
        
        if extended:
            logger.debug(f"Lock extended: {lock_key} for {ttl_ms}ms")
        else:
            logger.warning(f"Failed to extend lock: {lock_key}")
            
        return extended
    
    @contextmanager
    def lock(self, key: str, ttl_ms: int = 60000, auto_extend: bool = True):
        """
        Context manager for distributed locks
        
        Args:
            key: Lock key
            ttl_ms: Lock TTL in milliseconds
            auto_extend: Whether to automatically extend lock during long operations
            
        Yields:
            Lock token if acquired
            
        Raises:
            Exception: If lock cannot be acquired
        """
        token = self.acquire_lock(key, ttl_ms)
        if not token:
            raise Exception(f"Could not acquire lock: {key}")
        
        try:
            yield token
            
            # Auto-extend if operation takes longer than TTL
            if auto_extend and ttl_ms > 0:
                # Start background thread to extend lock
                import threading
                def extend_loop():
                    while True:
                        time.sleep(ttl_ms / 2000)  # Extend at 50% of TTL
                        if not self.extend_lock(key, token, ttl_ms):
                            break
                
                extend_thread = threading.Thread(target=extend_loop, daemon=True)
                extend_thread.start()
                
        finally:
            self.release_lock(key, token)

class IdempotencyLock:
    """Specialized lock for order idempotency"""
    
    def __init__(self, redis_client: redis.Redis):
        self.lock = DistributedLock(redis_client, "idem")
    
    def acquire_order_lock(self, provider: str, order_id: str, ttl_ms: int = 300000) -> Optional[str]:
        """
        Acquire lock for order processing
        
        Args:
            provider: Order provider (shopee, stripe, etc.)
            order_id: Provider's order ID
            ttl_ms: Lock TTL (default 5 minutes)
            
        Returns:
            Lock token if acquired, None if already processing
        """
        lock_key = f"{provider}:{order_id}"
        return self.lock.acquire_lock(lock_key, ttl_ms)
    
    def release_order_lock(self, provider: str, order_id: str, token: str) -> bool:
        """Release order lock"""
        lock_key = f"{provider}:{order_id}"
        return self.lock.release_lock(lock_key, token)
    
    @contextmanager
    def order_lock(self, provider: str, order_id: str, ttl_ms: int = 300000):
        """Context manager for order processing locks"""
        lock_key = f"{provider}:{order_id}"
        with self.lock.lock(lock_key, ttl_ms) as token:
            yield token

# Convenience functions
def with_idempotency_lock(redis_client: redis.Redis, provider: str, order_id: str, 
                          ttl_ms: int = 300000):
    """Decorator for idempotent order processing"""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            lock = IdempotencyLock(redis_client)
            token = lock.acquire_order_lock(provider, order_id, ttl_ms)
            
            if not token:
                logger.info(f"Order {provider}:{order_id} already being processed")
                return {"status": "already_processing", "message": "Order is being processed"}
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                lock.release_order_lock(provider, order_id, token)
        
        return wrapper
    return decorator
