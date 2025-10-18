#!/usr/bin/env python3
"""
Script para probar WhatsApp usando la API de Messaging Connect
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

def test_whatsapp_messaging_connect():
    """Prueba WhatsApp usando Messaging Connect API"""
    
    print("PRUEBA DE WHATSAPP CON MESSAGING CONNECT API")
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
    
    # Channel ID del canal de WhatsApp (desde la imagen)
    channel_id = "0c5c15d7-6489-4f07-a3fd-4abf18f8e907"
    
    # Probar diferentes versiones de API para Messaging Connect
    api_versions = [
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
        '2021-10-20-preview'
    ]
    
    # Mensaje de prueba usando Messaging Connect API
    test_payload = {
        "content": "Hola! Soy el bot de VEA Connect. Este es un mensaje de prueba desde Messaging Connect API.",
        "from": from_number,
        "to": ["+5215519387611"],
        "channelId": channel_id
    }
    
    payload_json = json.dumps(test_payload)
    
    working_api_version = None
    
    for api_version in api_versions:
        print(f"\nProbando API version: {api_version}")
        
        # Usar la API de Messaging Connect
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
            print(f"  URL: {url}")
            print(f"  Payload: {payload_json}")
            
            response = requests.post(url, json=test_payload, headers=headers, timeout=30)
            
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 202:
                print(f"  EXITO - API version {api_version} funciona")
                working_api_version = api_version
                print(f"  Response Headers: {dict(response.headers)}")
                break
            elif response.status_code == 401:
                print(f"  No autorizado - verificar access key")
            elif response.status_code == 404:
                print(f"  No encontrado - endpoint o API version incorrecta")
            elif response.status_code == 400:
                try:
                    error_data = response.json()
                    error_code = error_data.get('error', {}).get('code', 'Unknown')
                    print(f"  Error 400: {error_code}")
                    print(f"  Error details: {response.text[:200]}...")
                except:
                    print(f"  Error 400: {response.text[:100]}...")
            else:
                print(f"  Error {response.status_code}: {response.text[:100]}...")
                
        except Exception as e:
            print(f"  Error de conexión: {str(e)[:50]}...")
    
    # También probar sin channelId
    if not working_api_version:
        print(f"\nProbando sin channelId...")
        
        test_payload_no_channel = {
            "content": "Hola! Soy el bot de VEA Connect. Este es un mensaje de prueba sin channelId.",
            "from": from_number,
            "to": ["+5215519387611"]
        }
        
        payload_json_no_channel = json.dumps(test_payload_no_channel)
        
        for api_version in api_versions[:3]:  # Solo probar las primeras 3 versiones
            print(f"\nProbando API version: {api_version} (sin channelId)")
            
            url = f"{endpoint}/messages?api-version={api_version}"
            
            signature = generate_hmac_signature(access_key, url, 'POST', payload_json_no_channel)
            
            if not signature:
                print(f"  Error generando firma HMAC")
                continue
            
            headers = {
                'Authorization': f'HMAC-SHA256 {signature}',
                'Content-Type': 'application/json',
                'x-ms-date': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
            }
            
            try:
                response = requests.post(url, json=test_payload_no_channel, headers=headers, timeout=30)
                
                print(f"  Status: {response.status_code}")
                
                if response.status_code == 202:
                    print(f"  EXITO - API version {api_version} funciona sin channelId")
                    working_api_version = api_version
                    break
                elif response.status_code == 400:
                    try:
                        error_data = response.json()
                        error_code = error_data.get('error', {}).get('code', 'Unknown')
                        print(f"  Error 400: {error_code}")
                    except:
                        print(f"  Error 400: {response.text[:100]}...")
                        
            except Exception as e:
                print(f"  Error de conexión: {str(e)[:50]}...")
    
    # Resumen
    print(f"\nRESUMEN:")
    print("=" * 30)
    
    if working_api_version:
        print(f"API funcionando con versión: {working_api_version}")
        print(f"Número del bot: {from_number}")
        print(f"Channel ID: {channel_id}")
        print(f"Endpoint: {endpoint}")
        
        print(f"\nRECOMENDACIONES:")
        print("   1. Actualizar la Azure Function para usar esta versión de API")
        print("   2. El bot debería funcionar correctamente")
        
        return True
    else:
        print("No se encontró versión de API funcionando")
        print("Posibles problemas:")
        print("   1. El canal de WhatsApp no está configurado correctamente")
        print("   2. El número de teléfono no está verificado")
        print("   3. La API de Messaging Connect no está habilitada")
        
        return False

if __name__ == "__main__":
    success = test_whatsapp_messaging_connect()
    if success:
        print("\nWhatsApp Messaging Connect API funciona correctamente")
    else:
        print("\nWhatsApp Messaging Connect API no funciona")
