#!/usr/bin/env python3
"""
Script de diagnóstico para Azure Communication Services
"""
import os
import json
import requests
import hmac
import hashlib
import base64
from datetime import datetime
from urllib.parse import urlparse

def load_acs_config():
    """Carga la configuración de ACS desde variables de entorno"""
    config = {
        'connection_string': os.getenv('ACS_CONNECTION_STRING'),
        'from_number': os.getenv('ACS_WHATSAPP_FROM'),
        'endpoint': os.getenv('ACS_WHATSAPP_ENDPOINT'),
        'api_key': os.getenv('ACS_WHATSAPP_API_KEY')
    }
    
    print("🔍 Configuración de ACS:")
    for key, value in config.items():
        if value:
            if 'key' in key.lower() or 'secret' in key.lower():
                print(f"  {key}: {'SET' if value else 'NOT SET'} - {value[:20]}...")
            else:
                print(f"  {key}: {value}")
        else:
            print(f"  {key}: NOT SET")
    
    return config

def parse_connection_string(conn_string):
    """Parsea la connection string de ACS"""
    if not conn_string:
        return None, None
    
    parts = conn_string.split(';')
    endpoint = None
    access_key = None
    
    for part in parts:
        if part.startswith('endpoint='):
            endpoint = part.split('=', 1)[1]
        elif part.startswith('accesskey='):
            access_key = part.split('=', 1)[1]
    
    return endpoint, access_key

def generate_hmac_signature(access_key, url, method='POST', content=''):
    """Genera la firma HMAC para ACS"""
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
        print(f"❌ Error generando firma HMAC: {e}")
        return None

def test_acs_endpoint(endpoint, access_key):
    """Prueba la conectividad con el endpoint de ACS"""
    print(f"\n🔍 Probando endpoint: {endpoint}")
    
    # Limpiar endpoint
    if endpoint.endswith('/'):
        endpoint = endpoint.rstrip('/')
    
    # Probar diferentes versiones de API
    api_versions = [
        '2024-02-15-preview',
        '2023-10-01-preview',
        '2021-10-20-preview'
    ]
    
    for api_version in api_versions:
        url = f"{endpoint}/messages?api-version={api_version}"
        
        # Crear payload de prueba
        test_payload = {
            "content": "Test message",
            "from": "+1234567890",
            "to": ["+1234567890"]
        }
        
        payload_json = json.dumps(test_payload)
        
        # Generar firma HMAC
        signature = generate_hmac_signature(access_key, url, 'POST', payload_json)
        
        if not signature:
            continue
        
        headers = {
            'Authorization': f'HMAC-SHA256 {signature}',
            'Content-Type': 'application/json',
            'x-ms-date': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        }
        
        try:
            print(f"  Probando API version: {api_version}")
            response = requests.post(url, json=test_payload, headers=headers, timeout=10)
            
            print(f"    Status: {response.status_code}")
            
            if response.status_code == 202:
                print(f"    ✅ Éxito - API version {api_version} funciona")
                return api_version
            elif response.status_code == 401:
                print(f"    ⚠️ No autorizado - verificar access key")
            elif response.status_code == 404:
                print(f"    ❌ No encontrado - endpoint o API version incorrecta")
            else:
                print(f"    ❌ Error {response.status_code}: {response.text[:100]}...")
                
        except Exception as e:
            print(f"    ❌ Error de conexión: {str(e)[:50]}...")
    
    return None

def test_phone_numbers_endpoint(endpoint, access_key):
    """Prueba el endpoint de números de teléfono"""
    print(f"\n🔍 Probando endpoint de números de teléfono...")
    
    if endpoint.endswith('/'):
        endpoint = endpoint.rstrip('/')
    
    url = f"{endpoint}/phoneNumbers?api-version=2024-02-15-preview"
    
    # Generar firma HMAC para GET request
    signature = generate_hmac_signature(access_key, url, 'GET')
    
    if not signature:
        return False
    
    headers = {
        'Authorization': f'HMAC-SHA256 {signature}',
        'Content-Type': 'application/json',
        'x-ms-date': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            phone_numbers = data.get('phoneNumbers', [])
            print(f"  ✅ Encontrados {len(phone_numbers)} números de teléfono:")
            for phone in phone_numbers:
                print(f"    - {phone.get('phoneNumber', 'N/A')} ({phone.get('capabilities', {}).get('sms', 'N/A')})")
            return True
        else:
            print(f"  ❌ Error: {response.text[:100]}...")
            return False
            
    except Exception as e:
        print(f"  ❌ Error: {str(e)[:50]}...")
        return False

def main():
    """Función principal"""
    print("🚀 DIAGNÓSTICO DE AZURE COMMUNICATION SERVICES")
    print("=" * 50)
    
    # Cargar configuración
    config = load_acs_config()
    
    if not config['connection_string']:
        print("\n❌ ACS_CONNECTION_STRING no configurado")
        return
    
    # Parsear connection string
    endpoint, access_key = parse_connection_string(config['connection_string'])
    
    if not endpoint or not access_key:
        print("\n❌ No se pudo parsear la connection string")
        return
    
    print(f"\n✅ Connection string parseada correctamente")
    print(f"  Endpoint: {endpoint}")
    print(f"  Access Key: {'SET' if access_key else 'NOT SET'}")
    
    # Probar endpoint
    working_api_version = test_acs_endpoint(endpoint, access_key)
    
    if working_api_version:
        print(f"\n✅ Endpoint funcionando con API version: {working_api_version}")
    else:
        print(f"\n❌ Endpoint no funciona con ninguna API version")
    
    # Probar endpoint de números de teléfono
    test_phone_numbers_endpoint(endpoint, access_key)
    
    # Recomendaciones
    print(f"\n💡 RECOMENDACIONES:")
    if not working_api_version:
        print("  1. Verificar que el servicio ACS esté activo en Azure Portal")
        print("  2. Verificar que la connection string sea correcta")
        print("  3. Verificar que el access key tenga permisos suficientes")
        print("  4. Verificar que el endpoint esté en la región correcta")
    else:
        print("  1. El endpoint funciona correctamente")
        print("  2. Verificar la configuración de WhatsApp Business API")
        print("  3. Verificar que el número de teléfono esté verificado")

if __name__ == "__main__":
    main()
