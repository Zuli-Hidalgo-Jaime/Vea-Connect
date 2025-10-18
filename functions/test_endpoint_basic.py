#!/usr/bin/env python3
"""
Script para probar el endpoint básico de Azure Communication Services
"""

import os
import json
import requests
import hmac
import hashlib
import base64
from datetime import datetime
from urllib.parse import urlparse

def load_local_settings():
    """Carga las variables de entorno desde local.settings.json"""
    try:
        with open('local.settings.json', 'r') as f:
            settings = json.load(f)
        
        values = settings.get('Values', {})
        
        # Cargar variables críticas
        critical_vars = [
            'ACS_CONNECTION_STRING',
            'ACS_PHONE_NUMBER'
        ]
        
        for var in critical_vars:
            value = values.get(var)
            if value:
                os.environ[var] = value
        
        return True
        
    except Exception as e:
        print(f"Error cargando variables: {e}")
        return False

def generate_hmac_signature(access_key: str, url: str, method: str = 'GET', content: str = '') -> str:
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

def test_basic_endpoint():
    """Prueba el endpoint básico de ACS"""
    
    print("PRUEBA DEL ENDPOINT BÁSICO DE ACS")
    print("=" * 40)
    
    # Cargar variables locales
    if not load_local_settings():
        return False
    
    # Obtener configuración
    conn_string = os.getenv('ACS_CONNECTION_STRING')
    
    if not conn_string:
        print("ACS_CONNECTION_STRING no configurada")
        return False
    
    # Parsear connection string
    conn_parts = conn_string.split(';')
    endpoint = None
    access_key = None
    
    for part in conn_parts:
        if part.startswith('endpoint='):
            endpoint = part.split('=', 1)[1]
        elif part.startswith('accesskey='):
            access_key = part.split('=', 1)[1]
    
    if not endpoint or not access_key:
        print("No se pudo parsear la connection string")
        return False
    
    # Limpiar endpoint
    if endpoint.endswith('/'):
        endpoint = endpoint.rstrip('/')
    
    print(f"Endpoint: {endpoint}")
    print(f"Access Key: {access_key[:10]}...")
    
    # Probar diferentes endpoints básicos
    test_endpoints = [
        "/",
        "/phoneNumbers",
        "/phoneNumbers?api-version=2021-10-20-preview",
        "/messages",
        "/messages?api-version=2021-10-20-preview"
    ]
    
    for test_path in test_endpoints:
        print(f"\nProbando: {test_path}")
        
        url = f"{endpoint}{test_path}"
        
        # Generar firma HMAC para GET request
        signature = generate_hmac_signature(access_key, url, 'GET')
        
        if not signature:
            print(f"  Error generando firma HMAC")
            continue
        
        headers = {
            'Authorization': f'HMAC-SHA256 {signature}',
            'Content-Type': 'application/json',
            'x-ms-date': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"  EXITO - Endpoint responde correctamente")
                try:
                    data = response.json()
                    print(f"  Response: {json.dumps(data, indent=2)[:200]}...")
                except:
                    print(f"  Response: {response.text[:200]}...")
            elif response.status_code == 401:
                print(f"  No autorizado - verificar access key")
            elif response.status_code == 404:
                print(f"  No encontrado - endpoint no existe")
            else:
                print(f"  Error {response.status_code}: {response.text[:100]}...")
                
        except Exception as e:
            print(f"  Error de conexión: {str(e)[:50]}...")
    
    # Probar también con POST a /messages
    print(f"\nProbando POST a /messages...")
    
    url = f"{endpoint}/messages?api-version=2021-10-20-preview"
    
    test_payload = {
        "content": "Test message",
        "from": "+5215574908943",
        "to": ["+5215519387611"]
    }
    
    payload_json = json.dumps(test_payload)
    
    # Generar firma HMAC para POST request
    signature = generate_hmac_signature(access_key, url, 'POST', payload_json)
    
    if signature:
        headers = {
            'Authorization': f'HMAC-SHA256 {signature}',
            'Content-Type': 'application/json',
            'x-ms-date': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        }
        
        try:
            response = requests.post(url, json=test_payload, headers=headers, timeout=30)
            
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 202:
                print(f"  EXITO - Mensaje enviado correctamente")
            elif response.status_code == 401:
                print(f"  No autorizado - verificar access key")
            elif response.status_code == 404:
                print(f"  No encontrado - endpoint no existe")
            else:
                print(f"  Error {response.status_code}: {response.text[:100]}...")
                
        except Exception as e:
            print(f"  Error de conexión: {str(e)[:50]}...")
    
    return True

if __name__ == "__main__":
    test_basic_endpoint()
