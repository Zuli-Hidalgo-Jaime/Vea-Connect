#!/usr/bin/env python3
"""
Test server status and basic endpoints.
"""

import requests
import time

def test_server():
    """Test if server is responding."""
    base_url = "http://127.0.0.1:8000"
    
    print("Server Status Test")
    print("=" * 30)
    
    # Test basic endpoints
    endpoints = [
        "/",
        "/login/",
        "/api/v1/health/",
        "/swagger/"
    ]
    
    for endpoint in endpoints:
        url = base_url + endpoint
        print(f"\nTesting: {url}")
        
        try:
            start_time = time.time()
            response = requests.get(url, timeout=5)
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000
            
            print(f"  Status: {response.status_code}")
            print(f"  Time: {response_time:.2f}ms")
            
            if response.status_code == 200:
                print("  ✅ Working")
            else:
                print(f"  ⚠️ Status {response.status_code}")
                
        except requests.exceptions.Timeout:
            print("  ❌ Timeout")
        except requests.exceptions.ConnectionError:
            print("  ❌ Connection Error")
        except Exception as e:
            print(f"  ❌ Error: {e}")

if __name__ == "__main__":
    test_server() 