#!/usr/bin/env python3
"""
Quick test for the health check endpoint.
"""

import requests
import time

def quick_test():
    """Quick test of the health check endpoint."""
    url = "http://127.0.0.1:8000/api/v1/health/"
    
    print("Quick Health Check Test")
    print("=" * 30)
    print(f"Testing: {url}")
    
    try:
        # Very short timeout
        response = requests.get(url, timeout=3)
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Health check working!")
        else:
            print("❌ Health check failed")
            
    except requests.exceptions.Timeout:
        print("❌ Timeout - server not responding quickly")
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - server not running")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    quick_test() 