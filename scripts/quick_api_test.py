#!/usr/bin/env python
"""
Quick API test script for Embedding API Function.

This script performs a quick validation of the API endpoints
to ensure everything is working correctly.
"""

import requests
import json
import time
from typing import Dict, Any


def quick_test():
    """Perform quick API test."""
    base_url = "http://localhost:7071"
    
    print("🚀 Quick API Test")
    print("=" * 50)
    
    # Test 1: Health Check
    print("\n1️⃣ Testing Health Check...")
    try:
        response = requests.get(f"{base_url}/api/embeddings/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    # Test 2: Create Embedding
    print("\n2️⃣ Testing Create Embedding...")
    test_data = {
        "document_id": "quick-test-001",
        "text": "This is a quick test document for API validation.",
        "metadata": {"test": True, "category": "test"}
    }
    
    try:
        response = requests.post(f"{base_url}/api/embeddings/create", json=test_data)
        if response.status_code == 201:
            print("✅ Embedding created successfully")
        else:
            print(f"❌ Create failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Create error: {e}")
        return False
    
    # Test 3: Get Embedding
    print("\n3️⃣ Testing Get Embedding...")
    try:
        response = requests.get(f"{base_url}/api/embeddings/get?id=quick-test-001")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Embedding retrieved - Text: {data.get('data', {}).get('text', '')[:50]}...")
        else:
            print(f"❌ Get failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Get error: {e}")
        return False
    
    # Test 4: Search Similar
    print("\n4️⃣ Testing Semantic Search...")
    search_data = {
        "query": "test document validation",
        "top_k": 2
    }
    
    try:
        response = requests.post(f"{base_url}/api/embeddings/search", json=search_data)
        if response.status_code == 200:
            data = response.json()
            results_count = data.get('data', {}).get('results_count', 0)
            print(f"✅ Search completed - Found {results_count} results")
        else:
            print(f"❌ Search failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Search error: {e}")
        return False
    
    # Test 5: Get Stats
    print("\n5️⃣ Testing Get Stats...")
    try:
        response = requests.get(f"{base_url}/api/embeddings/stats")
        if response.status_code == 200:
            data = response.json()
            total_embeddings = data.get('data', {}).get('total_embeddings', 0)
            print(f"✅ Stats retrieved - Total embeddings: {total_embeddings}")
        else:
            print(f"❌ Stats failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Stats error: {e}")
        return False
    
    # Test 6: Delete Embedding
    print("\n6️⃣ Testing Delete Embedding...")
    try:
        response = requests.delete(f"{base_url}/api/embeddings/delete?id=quick-test-001")
        if response.status_code == 200:
            print("✅ Embedding deleted successfully")
        else:
            print(f"❌ Delete failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Delete error: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("✅ QUICK API TEST COMPLETED SUCCESSFULLY!")
    print("=" * 50)
    return True


def test_error_cases():
    """Test error cases."""
    base_url = "http://localhost:7071"
    
    print("\n⚠️ Testing Error Cases...")
    
    # Test 1: Missing required fields
    print("\n--- Test: Missing required fields ---")
    try:
        response = requests.post(f"{base_url}/api/embeddings/create", json={"document_id": "test"})
        if response.status_code == 400:
            print("✅ Correctly rejected missing fields")
        else:
            print(f"❌ Should have rejected: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Non-existent document
    print("\n--- Test: Non-existent document ---")
    try:
        response = requests.get(f"{base_url}/api/embeddings/get?id=non-existent")
        if response.status_code == 404:
            print("✅ Correctly handled non-existent document")
        else:
            print(f"❌ Should have returned 404: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    # Run quick test
    success = quick_test()
    
    if success:
        # Run error case tests
        test_error_cases()
        
        print("\n🎉 All tests completed!")
    else:
        print("\n❌ Quick test failed, skipping error cases")
        print("💡 Make sure the Azure Function is running on localhost:7071") 