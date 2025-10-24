#!/usr/bin/env python3
"""
Test the simple health check endpoint.
"""

import requests
import time

def test_simple_health():
    """Test the simple health check endpoint."""
    url = "http://127.0.0.1:8000/health-simple/"
    
    print("Simple Health Check Test")
    print("=" * 30)
    print(f"Testing: {url}")
    
    try:
        start_time = time.time()
        response = requests.get(url, timeout=5)
        end_time = time.time()
        
        response_time = (end_time - start_time) * 1000
        
        print(f"Status: {response.status_code}")
        print(f"Response Time: {response_time:.2f}ms")
        
        if response.status_code == 200:
            data = response.json()
            print("Response Data:")
            for key, value in data.items():
                print(f"  {key}: {value}")
            print("✅ Simple health check working!")
        else:
            print(f"❌ Error: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ Timeout - server not responding")
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - server not running")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_simple_health() 