#!/usr/bin/env python3
"""
Script de prueba para verificar la configuración de WhatsApp API
"""

import os
import json
import requests
import hmac
import hashlib
import base64
from datetime import datetime
from urllib.parse import urlparse

def generate_hmac_signature(access_key: str, url: str, method: str = 'POST', content: str = '') -> str:
    """Generate HMAC signature for Azure Communication Services."""
    try:
        parsed_url = urlparse(url)
        path_and_query = parsed_url.path
        if parsed_url.query:
            path_and_query += '?' + parsed_url.query
        
        string_to_sign = f"{method}\n{path_and_query}\n{content}"
        key_bytes = base64.b64decode(access_key)
        signature = hmac.new(key_bytes, string_to_sign.encode('utf-8'), hashlib.sha256)
        signature_bytes = signature.digest()
        signature_b64 = base64.b64encode(signature_bytes).decode('utf-8')
        return signature_b64
    except Exception as e:
        print(f"Error generating HMAC signature: {e}")
        return ""

def test_whatsapp_api():
    """Test WhatsApp API configuration."""
    
    # Get configuration from environment variables
    conn_string = os.getenv('ACS_CONNECTION_STRING')
    from_id = os.getenv('ACS_PHONE_NUMBER')  # Use ACS_PHONE_NUMBER instead of ACS_WHATSAPP_FROM
    
    print("=== WhatsApp API Configuration Test ===")
    print(f"ACS_CONNECTION_STRING: {'SET' if conn_string else 'NOT SET'}")
    print(f"ACS_PHONE_NUMBER: {'SET' if from_id else 'NOT SET'}")
    
    if not conn_string or not from_id:
        print("Missing required environment variables")
        return False
    
    # Parse connection string
    conn_parts = conn_string.split(';')
    endpoint = None
    access_key = None
    
    for part in conn_parts:
        if part.startswith('endpoint='):
            endpoint = part.split('=', 1)[1]
        elif part.startswith('accesskey='):
            access_key = part.split('=', 1)[1]
    
    if not endpoint or not access_key:
        print("Could not parse ACS_CONNECTION_STRING")
        return False
    
    print(f"Endpoint: {endpoint}")
    print(f"Access Key: {access_key[:10]}...")
    print(f"From ID: {from_id}")
    
    # Clean up endpoint
    if endpoint.endswith('/'):
        endpoint = endpoint.rstrip('/')
    
    # Test different API versions
    api_versions = [
        '2024-02-15-preview',
        '2023-10-01-preview',
        '2021-10-20-preview',
        '2023-11-01'
    ]
    
    test_payload = {
        "content": "Test message from diagnostic script",
        "from": from_id,
        "to": ["+5215519387611"]  # Test number from logs
    }
    
    payload_json = json.dumps(test_payload)
    
    for api_version in api_versions:
        print(f"\n--- Testing API version: {api_version} ---")
        
        url = f"{endpoint}/messages?api-version={api_version}"
        print(f"URL: {url}")
        
        # Generate HMAC signature
        signature = generate_hmac_signature(access_key, url, 'POST', payload_json)
        
        if not signature:
            print("Failed to generate HMAC signature")
            continue
        
        headers = {
            'Authorization': f'HMAC-SHA256 {signature}',
            'Content-Type': 'application/json',
            'x-ms-date': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        }
        
        try:
            print("Sending request...")
            response = requests.post(url, json=test_payload, headers=headers, timeout=30)
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            
            if response.status_code == 202:
                print("SUCCESS - Message accepted")
                return True
            elif response.status_code == 401:
                print("Unauthorized - Check access key")
            elif response.status_code == 404:
                print("Not Found - Check endpoint or API version")
            else:
                print(f"Error: {response.text[:200]}...")
                
        except Exception as e:
            print(f"Request failed: {e}")
    
    return False

if __name__ == "__main__":
    success = test_whatsapp_api()
    if success:
        print("\nWhatsApp API test completed successfully")
    else:
        print("\nWhatsApp API test failed")
