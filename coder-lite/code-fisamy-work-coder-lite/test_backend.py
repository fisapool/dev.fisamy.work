#!/usr/bin/env python3
"""
Test script for Coder-lite Provision System Backend
"""

import requests
import json
import time
import sys

# Configuration
BASE_URL = "http://localhost:8000"
TEST_EMAIL = "test@example.com"

def test_health():
    """Test health endpoint"""
    print("🧪 Testing health endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data['status']}")
            print(f"   Services: {data['services']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_metrics():
    """Test metrics endpoint"""
    print("\n📊 Testing metrics endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/metrics")
        if response.status_code == 200:
            print("✅ Metrics endpoint working")
            return True
        else:
            print(f"❌ Metrics endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Metrics endpoint error: {e}")
        return False

def test_webhook():
    """Test order webhook endpoint"""
    print("\n📨 Testing order webhook...")
    
    test_order = {
        "provider": "test",
        "order_id": f"TEST-{int(time.time())}",
        "customer": {
            "email": TEST_EMAIL,
            "phone": "+60123456789"
        },
        "line_items": [
            {
                "sku": "DEV-BASIC-1M",
                "qty": 1
            }
        ],
        "paid": True,
        "signature": "test_signature"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/webhooks/orders",
            json=test_order,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Webhook processed: {data['status']}")
            print(f"   Username: {data['username']}")
            print(f"   Idempotency key: {data['idempotency_key']}")
            return data['idempotency_key']
        else:
            print(f"❌ Webhook failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Webhook error: {e}")
        return None

def test_provision_status():
    """Test provision status endpoint"""
    print("\n📋 Testing provision status...")
    
    try:
        response = requests.get(f"{BASE_URL}/provision/status")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status retrieved:")
            print(f"   Queue length: {data['queue_length']}")
            print(f"   Processed count: {data['processed_count']}")
            print(f"   Status: {data['status']}")
            return True
        else:
            print(f"❌ Status failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Status error: {e}")
        return False

def test_provision_processing():
    """Test provision job processing"""
    print("\n⚙️  Testing provision processing...")
    
    try:
        response = requests.post(f"{BASE_URL}/provision/process")
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'no_jobs':
                print("✅ No jobs to process (expected)")
            else:
                print(f"✅ Job processed: {data['status']}")
            return True
        else:
            print(f"❌ Processing failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Processing error: {e}")
        return False

def test_idempotency(idempotency_key):
    """Test idempotency by sending the same order again"""
    print(f"\n🔄 Testing idempotency with key: {idempotency_key}")
    
    test_order = {
        "provider": "test",
        "order_id": idempotency_key.split(":")[1],  # Extract order_id
        "customer": {
            "email": TEST_EMAIL,
            "phone": "+60123456789"
        },
        "line_items": [
            {
                "sku": "DEV-BASIC-1M",
                "qty": 1
            }
        ],
        "paid": True,
        "signature": "test_signature"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/webhooks/orders",
            json=test_order,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'already_processed':
                print("✅ Idempotency working correctly")
                return True
            else:
                print(f"⚠️  Unexpected response: {data['status']}")
                return False
        else:
            print(f"❌ Idempotency test failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Idempotency test error: {e}")
        return False

def run_all_tests():
    """Run all tests"""
    print("🚀 Running Coder-lite Provision System Backend Tests\n")
    
    # Test basic endpoints
    if not test_health():
        print("❌ Health check failed, stopping tests")
        return False
    
    if not test_metrics():
        print("❌ Metrics endpoint failed")
        return False
    
    if not test_provision_status():
        print("❌ Provision status failed")
        return False
    
    # Test webhook processing
    idempotency_key = test_webhook()
    if not idempotency_key:
        print("❌ Webhook test failed")
        return False
    
    # Test idempotency
    if not test_idempotency(idempotency_key):
        print("❌ Idempotency test failed")
        return False
    
    # Test provision processing
    if not test_provision_processing():
        print("❌ Provision processing test failed")
        return False
    
    print("\n🎉 All tests passed! Backend is working correctly.")
    return True

def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("""
🧪 Coder-lite Provision System Backend Test Script

Usage:
  python test_backend.py [--help]

This script tests all major backend endpoints:
- Health check
- Metrics endpoint
- Order webhook processing
- Provision status
- Provision job processing
- Idempotency

Prerequisites:
- Backend must be running on http://localhost:8000
- Redis should be available (optional for basic tests)

Examples:
  # Run all tests
  python test_backend.py
  
  # Show help
  python test_backend.py --help
""")
        return
    
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
