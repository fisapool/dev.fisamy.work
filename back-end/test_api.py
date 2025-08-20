#!/usr/bin/env python3
"""
Test script for Fisamy Dashboard BFF
Tests all API endpoints to ensure they're working correctly
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_endpoint(endpoint, method="GET", data=None, expected_status=200):
    """Test a single endpoint"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        
        if response.status_code == expected_status:
            print(f"✅ {method} {endpoint} - OK ({response.status_code})")
            if response.content:
                try:
                    result = response.json()
                    if isinstance(result, dict) and len(result) > 0:
                        print(f"   Response: {json.dumps(result, indent=2)}")
                except:
                    print(f"   Response: {response.text[:100]}...")
            return True
        else:
            print(f"❌ {method} {endpoint} - FAILED ({response.status_code})")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ {method} {endpoint} - ERROR: {e}")
        return False

def main():
    """Run all API tests"""
    print("🧪 Testing Fisamy Dashboard BFF API Endpoints")
    print("=" * 50)
    
    tests = [
        # Basic endpoints
        ("/health", "GET"),
        ("/me", "GET"),
        ("/usage", "GET"),
        ("/workspaces", "GET"),
        ("/templates", "GET"),
        ("/domains", "GET"),
        
        # API documentation
        ("/docs", "GET"),
        ("/openapi.json", "GET"),
    ]
    
    passed = 0
    total = len(tests)
    
    for endpoint, method in tests:
        if test_endpoint(endpoint, method):
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} endpoints working")
    
    if passed == total:
        print("🎉 All endpoints are working correctly!")
        return 0
    else:
        print("⚠️  Some endpoints have issues. Check the logs above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
