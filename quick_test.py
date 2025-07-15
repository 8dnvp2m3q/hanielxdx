#!/usr/bin/env python3
"""
Simple Backend API Test - Quick connectivity check
"""

import requests
import json
import time
import sys

def test_api_simple():
    """Simple API test with timeout"""
    base_url = "https://a23a3c63-c7d5-4829-95ff-e1173adaedc9.preview.emergentagent.com/api"
    
    print("Testing API connectivity...")
    
    try:
        # Test with a short timeout
        response = requests.get(f"{base_url}/", timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ API is accessible")
            return True
        else:
            print("❌ API returned error status")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ API request timed out")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_local_api():
    """Test local API"""
    print("Testing local API...")
    
    try:
        response = requests.get("http://localhost:8001/api/", timeout=5)
        print(f"Local API Status: {response.status_code}")
        print(f"Local API Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Local API error: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Quick Backend API Test")
    print("=" * 40)
    
    # Test local first
    local_success = test_local_api()
    
    # Test external
    external_success = test_api_simple()
    
    print("\n📊 Results:")
    print(f"Local API: {'✅ Working' if local_success else '❌ Failed'}")
    print(f"External API: {'✅ Working' if external_success else '❌ Failed'}")
    
    if local_success or external_success:
        print("\n✅ At least one API endpoint is working")
        sys.exit(0)
    else:
        print("\n❌ Both API endpoints failed")
        sys.exit(1)