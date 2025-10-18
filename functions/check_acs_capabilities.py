#!/usr/bin/env python3
"""
Script para verificar las capacidades del servicio ACS
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

def check_acs_capabilities():
    """Verifica las capacidades del servicio ACS"""
    
    print("VERIFICACIÓN DE CAPACIDADES DEL SERVICIO ACS")
    print("=" * 50)
    
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
    print(f"Access Key: {'SET' if access_key else 'NOT SET'}")
    
    # Probar diferentes versiones de API para phoneNumbers
    print(f"\nVerificando capacidades de números de teléfono...")
    
    phone_api_versions = [
        '2022-12-01',
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
    
    working_phone_api = None
    
    for api_version in phone_api_versions:
        print(f"\nProbando phoneNumbers con API version: {api_version}")
        
        url = f"{endpoint}/phoneNumbers?api-version={api_version}"
        
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
                print(f"  EXITO - API version {api_version} funciona para phoneNumbers")
                working_phone_api = api_version
                try:
                    data = response.json()
                    phone_numbers = data.get('phoneNumbers', [])
                    print(f"  Números de teléfono encontrados: {len(phone_numbers)}")
                    for phone in phone_numbers:
                        print(f"    - {phone.get('phoneNumber', 'N/A')}")
                        capabilities = phone.get('capabilities', {})
                        print(f"      SMS: {capabilities.get('sms', 'N/A')}")
                        print(f"      Voice: {capabilities.get('voice', 'N/A')}")
                        print(f"      WhatsApp: {capabilities.get('whatsapp', 'N/A')}")
                except Exception as e:
                    print(f"  Error parseando respuesta: {e}")
                break
            elif response.status_code == 400:
                try:
                    error_data = response.json()
                    error_code = error_data.get('error', {}).get('code', 'Unknown')
                    print(f"  Error 400: {error_code}")
                except:
                    print(f"  Error 400: {response.text[:100]}...")
            elif response.status_code == 401:
                print(f"  No autorizado - verificar access key")
                break
            else:
                print(f"  Error {response.status_code}: {response.text[:100]}...")
                
        except Exception as e:
            print(f"  Error de conexión: {str(e)[:50]}...")
    
    # Probar diferentes versiones de API para messages
    print(f"\nVerificando capacidades de mensajes...")
    
    message_api_versions = [
        '2024-02-15-preview',
        '2023-10-01-preview',
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
    
    working_message_api = None
    
    for api_version in message_api_versions:
        print(f"\nProbando messages con API version: {api_version}")
        
        url = f"{endpoint}/messages?api-version={api_version}"
        
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
                print(f"  EXITO - API version {api_version} funciona para messages")
                working_message_api = api_version
                break
            elif response.status_code == 400:
                try:
                    error_data = response.json()
                    error_code = error_data.get('error', {}).get('code', 'Unknown')
                    print(f"  Error 400: {error_code}")
                except:
                    print(f"  Error 400: {response.text[:100]}...")
            elif response.status_code == 401:
                print(f"  No autorizado - verificar access key")
                break
            elif response.status_code == 404:
                print(f"  No encontrado - endpoint no existe")
            else:
                print(f"  Error {response.status_code}: {response.text[:100]}...")
                
        except Exception as e:
            print(f"  Error de conexión: {str(e)[:50]}...")
    
    # Resumen
    print(f"\nRESUMEN:")
    print("=" * 30)
    
    if working_phone_api:
        print(f"API de números de teléfono funcionando: {working_phone_api}")
    else:
        print("No se encontró API de números de teléfono funcionando")
    
    if working_message_api:
        print(f"API de mensajes funcionando: {working_message_api}")
    else:
        print("No se encontró API de mensajes funcionando")
    
    if not working_phone_api and not working_message_api:
        print("\nPROBLEMAS DETECTADOS:")
        print("  1. El servicio ACS no tiene las capacidades necesarias")
        print("  2. El servicio ACS no está configurado para WhatsApp")
        print("  3. La connection string es incorrecta")
        print("  4. El servicio ACS no está activo")
    
    return working_phone_api is not None or working_message_api is not None

if __name__ == "__main__":
    success = check_acs_capabilities()
    if success:
        print("\nEl servicio ACS tiene algunas capacidades funcionando")
    else:
        print("\nEl servicio ACS no tiene capacidades funcionando")
