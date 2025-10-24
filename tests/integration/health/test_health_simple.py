#!/usr/bin/env python3
"""
Simple test script for the optimized health check endpoint.
"""

import requests
import time

def test_health_check():
    """Test the health check endpoint."""
    url = "http://localhost:8000/api/v1/health/"
    
    print("Testing health check endpoint...")
    print(f"URL: {url}")
    print("-" * 50)
    
    try:
        # Measure response time
        start_time = time.time()
        response = requests.get(url, timeout=5)
        end_time = time.time()
        
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Time: {response_time:.2f}ms")
        
        if response.status_code == 200:
            data = response.json()
            print("Response Data:")
            print(f"  Status: {data.get('status', 'N/A')}")
            print(f"  Timestamp: {data.get('timestamp', 'N/A')}")
            print(f"  Response Time (reported): {data.get('response_time_ms', 'N/A')}ms")
            
            # Performance assessment
            if response_time < 100:
                print("✅ Performance: Excellent (< 100ms)")
            elif response_time < 200:
                print("✅ Performance: Good (< 200ms)")
            else:
                print("⚠️ Performance: Needs improvement (>= 200ms)")
                
            return True
        else:
            print(f"❌ Error: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to server")
        print("Make sure the Django server is running on localhost:8000")
        return False
    except requests.exceptions.Timeout:
        print("❌ Error: Request timeout")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    test_health_check() 