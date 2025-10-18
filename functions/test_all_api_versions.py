#!/usr/bin/env python3
"""
Script para probar todas las versiones de API de Azure Communication Services
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

def test_api_versions():
    """Prueba todas las versiones de API disponibles"""
    
    print("PRUEBA DE TODAS LAS VERSIONES DE API")
    print("=" * 50)
    
    # Cargar variables locales
    if not load_local_settings():
        return False
    
    # Obtener configuración
    conn_string = os.getenv('ACS_CONNECTION_STRING')
    from_number = os.getenv('ACS_PHONE_NUMBER')
    
    if not conn_string or not from_number:
        print("Variables requeridas no configuradas")
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
    print(f"From Number: {from_number}")
    
    # Lista de versiones de API a probar
    api_versions = [
        '2024-02-15-preview',
        '2023-10-01-preview',
        '2021-10-20-preview',
        '2023-11-01',
        '2023-08-01-preview',
        '2023-06-01-preview',
        '2023-04-01-preview',
        '2023-03-01-preview',
        '2022-10-01-preview',
        '2022-08-01-preview',
        '2022-06-01-preview',
        '2022-04-01-preview',
        '2022-02-01-preview',
        '2021-10-20-preview',
        '2021-09-01-preview',
        '2021-08-01-preview',
        '2021-07-01-preview',
        '2021-06-01-preview',
        '2021-05-01-preview',
        '2021-04-01-preview'
    ]
    
    # Mensaje de prueba
    test_payload = {
        "content": "Mensaje de prueba desde script de diagnóstico",
        "from": from_number,
        "to": ["+5215519387611"]
    }
    
    payload_json = json.dumps(test_payload)
    
    working_versions = []
    
    for api_version in api_versions:
        print(f"\nProbando API version: {api_version}")
        
        url = f"{endpoint}/messages?api-version={api_version}"
        
        # Generar firma HMAC
        signature = generate_hmac_signature(access_key, url, 'POST', payload_json)
        
        if not signature:
            print(f"  Error generando firma HMAC")
            continue
        
        headers = {
            'Authorization': f'HMAC-SHA256 {signature}',
            'Content-Type': 'application/json',
            'x-ms-date': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        }
        
        try:
            response = requests.post(url, json=test_payload, headers=headers, timeout=30)
            
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 202:
                print(f"  EXITO - API version {api_version} funciona")
                working_versions.append(api_version)
            elif response.status_code == 401:
                print(f"  No autorizado - verificar access key")
            elif response.status_code == 404:
                print(f"  No encontrado - endpoint o API version incorrecta")
            else:
                print(f"  Error {response.status_code}: {response.text[:100]}...")
                
        except Exception as e:
            print(f"  Error de conexión: {str(e)[:50]}...")
    
    # Resumen
    print(f"\nRESUMEN:")
    print("=" * 30)
    
    if working_versions:
        print(f"Versiones de API que funcionan: {working_versions}")
        print(f"Recomendación: Usar {working_versions[0]}")
        return True
    else:
        print("Ninguna versión de API funciona")
        print("Posibles problemas:")
        print("  1. El servicio ACS no está configurado correctamente")
        print("  2. El número de teléfono no está verificado en WhatsApp")
        print("  3. La connection string es incorrecta")
        print("  4. El endpoint no es válido")
        return False

if __name__ == "__main__":
    success = test_api_versions()
    if success:
        print("\nSe encontraron versiones de API que funcionan")
    else:
        print("\nNo se encontraron versiones de API que funcionen")
