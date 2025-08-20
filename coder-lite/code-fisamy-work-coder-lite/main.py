#!/usr/bin/env python3
"""
Main FastAPI application for Coder-lite Provision System
"""

import os
import sys
import logging
from pathlib import Path
from contextlib import asynccontextmanager

# Add current directory to Python path
sys.path.append(str(Path(__file__).parent))

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import uvicorn
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import redis
import json
import time

# Import our utilities
from utils.metrics import metrics, record_provision_success, record_provision_failure
from utils.distributed_lock import IdempotencyLock
from utils.port_allocator import PortAllocator
from workers.provision_worker import ProvisionWorker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variables
redis_client = None
port_allocator = None
provision_worker = None

# Pydantic models
class Customer(BaseModel):
    email: str = Field(..., description="Customer email address")
    phone: Optional[str] = Field(None, description="Customer phone number")

class LineItem(BaseModel):
    sku: str = Field(..., description="Product SKU")
    qty: int = Field(1, description="Quantity")

class OrderWebhook(BaseModel):
    provider: str = Field(..., description="Order provider (shopee, stripe, etc.)")
    order_id: str = Field(..., description="Provider's order ID")
    customer: Customer = Field(..., description="Customer information")
    line_items: List[LineItem] = Field(..., description="Order line items")
    paid: bool = Field(True, description="Payment status")
    signature: Optional[str] = Field(None, description="Webhook signature for verification")

class ProvisionJob(BaseModel):
    idempotency_key: str = Field(..., description="Unique idempotency key")
    user: Dict[str, Any] = Field(..., description="User information")
    plan: str = Field(..., description="Plan SKU")
    limits: Dict[str, Any] = Field(..., description="Resource limits")
    network: Dict[str, Any] = Field(..., description="Network configuration")
    auth: Dict[str, Any] = Field(..., description="Authentication configuration")

class HealthResponse(BaseModel):
    status: str = Field(..., description="Health status")
    timestamp: float = Field(..., description="Current timestamp")
    services: Dict[str, str] = Field(..., description="Service status")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Coder-lite Provision System...")
    
    # Initialize Redis connection
    global redis_client
    try:
        redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=int(os.getenv('REDIS_DB', 0)),
            password=os.getenv('REDIS_PASSWORD'),
            decode_responses=True
        )
        redis_client.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        redis_client = None
    
    # Initialize port allocator
    global port_allocator
    try:
        port_allocator = PortAllocator(
            start_port=int(os.getenv('START_PORT', 13001)),
            max_port=int(os.getenv('MAX_PORT', 65535))
        )
        logger.info("Port allocator initialized")
    except Exception as e:
        logger.error(f"Failed to initialize port allocator: {e}")
        port_allocator = None
    
    # Initialize provision worker
    global provision_worker
    try:
        config = {
            'coder_lite_path': os.getenv('CODER_LITE_PATH', '/opt/coder-lite'),
            'start_port': int(os.getenv('START_PORT', 13001)),
            'max_port': int(os.getenv('MAX_PORT', 65535)),
            'plans': {
                'DEV-BASIC-1M': {'cpu': '2.0', 'ram': '4g', 'disk': 20, 'idle_timeout': 45},
                'DEV-PLUS-1M': {'cpu': '4.0', 'ram': '8g', 'disk': 40, 'idle_timeout': 120},
                'DEV-GPU-1M': {'cpu': '6.0', 'ram': '16g', 'disk': 60, 'gpu': True, 'idle_timeout': 45}
            }
        }
        provision_worker = ProvisionWorker(redis_client, None, config)  # No DB session for now
        logger.info("Provision worker initialized")
    except Exception as e:
        logger.error(f"Failed to initialize provision worker: {e}")
        provision_worker = None
    
    yield
    
    # Shutdown
    logger.info("Shutting down Coder-lite Provision System...")
    if redis_client:
        redis_client.close()

# Create FastAPI app
app = FastAPI(
    title="Coder-lite Provision System",
    description="Backend API for auto-provisioning user workspaces",
    version="1.0.0",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure appropriately for production
)

# Dependency functions
def get_redis():
    """Get Redis client"""
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis not available")
    return redis_client

def get_port_allocator():
    """Get port allocator"""
    if not port_allocator:
        raise HTTPException(status_code=503, detail="Port allocator not available")
    return port_allocator

def get_provision_worker():
    """Get provision worker"""
    if not provision_worker:
        raise HTTPException(status_code=503, detail="Provision worker not available")
    return provision_worker

# API endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Coder-lite Provision System",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    services = {
        "redis": "healthy" if redis_client and redis_client.ping() else "unhealthy",
        "port_allocator": "healthy" if port_allocator else "unhealthy",
        "provision_worker": "healthy" if provision_worker else "unhealthy"
    }
    
    overall_status = "healthy" if all(s == "healthy" for s in services.values()) else "unhealthy"
    
    return HealthResponse(
        status=overall_status,
        timestamp=time.time(),
        services=services
    )

@app.get("/metrics")
async def metrics_endpoint():
    """Prometheus metrics endpoint"""
    return metrics.export_prometheus()

@app.post("/webhooks/orders")
async def webhook_orders(
    order: OrderWebhook,
    request: Request,
    redis_client: redis.Redis = Depends(get_redis)
):
    """Process order webhook and enqueue provision job"""
    start_time = time.time()
    
    try:
        # Validate webhook signature (implement based on provider)
        if not _validate_webhook_signature(request, order):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
        
        # Check idempotency
        idempotency_key = f"{order.provider}:{order.order_id}"
        if redis_client.exists(f"processed:{idempotency_key}"):
            logger.info(f"Order already processed: {idempotency_key}")
            return {"status": "already_processed", "idempotency_key": idempotency_key}
        
        # Extract user information
        username = _generate_username(order.customer.email)
        
        # Get plan configuration
        plan_config = _get_plan_config(order.line_items[0].sku)
        if not plan_config:
            raise HTTPException(status_code=400, detail=f"Unknown plan: {order.line_items[0].sku}")
        
        # Allocate port
        port_allocator = get_port_allocator()
        port = port_allocator._find_available_port(set())  # Simplified for demo
        
        # Generate secure password
        password = _generate_secure_password()
        bcrypt_hash = _generate_bcrypt_hash(password)
        
        # Create provision job
        provision_job = ProvisionJob(
            idempotency_key=idempotency_key,
            user={
                "id": hash(username) % 1000000,  # Simplified ID generation
                "username": username,
                "email": order.customer.email
            },
            plan=order.line_items[0].sku,
            limits={
                "cpu": plan_config["cpu"],
                "ram": plan_config["ram"],
                "disk_gib": plan_config["disk"]
            },
            network={
                "port": port,
                "subdomain": username
            },
            auth={
                "type": "basic",
                "password": password,
                "bcrypt_hash": bcrypt_hash
            }
        )
        
        # Enqueue job to Redis
        job_data = provision_job.dict()
        redis_client.lpush("provision_jobs", json.dumps(job_data))
        
        # Mark as processed
        redis_client.setex(f"processed:{idempotency_key}", 86400, "1")  # 24h TTL
        
        # Record metrics
        duration_ms = int((time.time() - start_time) * 1000)
        record_provision_success(duration_ms, order.line_items[0].sku)
        
        logger.info(f"Order enqueued successfully: {idempotency_key}")
        
        return {
            "status": "enqueued",
            "idempotency_key": idempotency_key,
            "username": username,
            "estimated_time": "2-5 minutes"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process order: {e}")
        duration_ms = int((time.time() - start_time) * 1000)
        record_provision_failure(duration_ms, order.line_items[0].sku, str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/provision/process")
async def process_provision_jobs(
    redis_client: redis.Redis = Depends(get_redis),
    provision_worker: ProvisionWorker = Depends(get_provision_worker)
):
    """Process provision jobs from queue (for testing)"""
    try:
        # Get job from queue
        job_data = redis_client.rpop("provision_jobs")
        if not job_data:
            return {"status": "no_jobs", "message": "No jobs in queue"}
        
        # Parse job
        job = json.loads(job_data)
        
        # Process with worker
        result = provision_worker.handle_provision_job(job)
        
        return {
            "status": "processed",
            "job": job,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Failed to process provision job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/provision/status")
async def provision_status(
    redis_client: redis.Redis = Depends(get_redis)
):
    """Get provision queue status"""
    try:
        queue_length = redis_client.llen("provision_jobs")
        processed_count = len(redis_client.keys("processed:*"))
        
        return {
            "queue_length": queue_length,
            "processed_count": processed_count,
            "status": "operational" if queue_length < 100 else "high_load"
        }
        
    except Exception as e:
        logger.error(f"Failed to get provision status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Utility functions
def _validate_webhook_signature(request: Request, order: OrderWebhook) -> bool:
    """Validate webhook signature (implement based on provider)"""
    # This is a simplified implementation
    # In production, implement proper signature verification
    return True

def _generate_username(email: str) -> str:
    """Generate username from email"""
    username = email.split('@')[0].lower()
    username = ''.join(c for c in username if c.isalnum())
    return username[:20]  # Limit length

def _get_plan_config(sku: str) -> Optional[Dict[str, Any]]:
    """Get plan configuration"""
    plans = {
        'DEV-BASIC-1M': {'cpu': '2.0', 'ram': '4g', 'disk': 20, 'idle_timeout': 45},
        'DEV-PLUS-1M': {'cpu': '4.0', 'ram': '8g', 'disk': 40, 'idle_timeout': 120},
        'DEV-GPU-1M': {'cpu': '6.0', 'ram': '16g', 'disk': 60, 'gpu': True, 'idle_timeout': 45}
    }
    return plans.get(sku)

def _generate_secure_password(length: int = 24) -> str:
    """Generate secure password"""
    import secrets
    import string
    
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def _generate_bcrypt_hash(password: str) -> str:
    """Generate bcrypt hash"""
    try:
        import bcrypt
        salt = bcrypt.gensalt(rounds=12)
        hash_bytes = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hash_bytes.decode('utf-8')
    except ImportError:
        # Fallback
        import crypt
        return crypt.crypt(password, crypt.mksalt(crypt.METHOD_SHA512))

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run the application
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("RELOAD", "false").lower() == "true",
        log_level=os.getenv("LOG_LEVEL", "info")
    )
