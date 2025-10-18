#!/usr/bin/env python3
"""
Script para probar el bot de WhatsApp localmente
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
            'ACS_PHONE_NUMBER',
            'ACS_WHATSAPP_ENDPOINT',
            'ACS_WHATSAPP_API_KEY'
        ]
        
        loaded_count = 0
        for var in critical_vars:
            value = values.get(var)
            if value:
                os.environ[var] = value
                loaded_count += 1
                print(f"Cargada: {var}")
            else:
                print(f"No encontrada: {var}")
        
        print(f"\nVariables cargadas: {loaded_count}/{len(critical_vars)}")
        return loaded_count == len(critical_vars)
        
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

def test_whatsapp_bot():
    """Prueba el bot de WhatsApp"""
    
    print("PRUEBA DEL BOT DE WHATSAPP")
    print("=" * 40)
    
    # Cargar variables locales
    if not load_local_settings():
        print("No se pudieron cargar las variables locales")
        return False
    
    # Obtener configuración
    conn_string = os.getenv('ACS_CONNECTION_STRING')
    from_number = os.getenv('ACS_PHONE_NUMBER')
    
    print(f"\nConfiguración:")
    print(f"  ACS_CONNECTION_STRING: {'SET' if conn_string else 'NOT SET'}")
    print(f"  ACS_PHONE_NUMBER: {'SET' if from_number else 'NOT SET'}")
    
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
    
    print(f"  Endpoint: {endpoint}")
    print(f"  Access Key: {access_key[:10]}...")
    print(f"  From Number: {from_number}")
    
    # Limpiar endpoint
    if endpoint.endswith('/'):
        endpoint = endpoint.rstrip('/')
    
    # Probar envío de mensaje
    print(f"\nProbando envío de mensaje...")
    
    # Usar la versión de API corregida
    api_version = '2024-02-15-preview'
    url = f"{endpoint}/messages?api-version={api_version}"
    
    # Mensaje de prueba
    test_payload = {
        "content": "Hola! Soy el bot de VEA Connect. Este es un mensaje de prueba.",
        "from": from_number,
        "to": ["+5215519387611"]  # Número de prueba desde los logs
    }
    
    payload_json = json.dumps(test_payload)
    
    # Generar firma HMAC
    signature = generate_hmac_signature(access_key, url, 'POST', payload_json)
    
    if not signature:
        print("Error generando firma HMAC")
        return False
    
    headers = {
        'Authorization': f'HMAC-SHA256 {signature}',
        'Content-Type': 'application/json',
        'x-ms-date': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    }
    
    print(f"  URL: {url}")
    print(f"  Payload: {payload_json}")
    
    try:
        print("  Enviando mensaje...")
        response = requests.post(url, json=test_payload, headers=headers, timeout=30)
        
        print(f"  Status Code: {response.status_code}")
        print(f"  Response Headers: {dict(response.headers)}")
        
        if response.status_code == 202:
            print("  EXITO - Mensaje enviado correctamente")
            print("  El bot está funcionando!")
            return True
        elif response.status_code == 401:
            print("  ERROR - No autorizado (verificar access key)")
        elif response.status_code == 404:
            print("  ERROR - No encontrado (verificar endpoint o API version)")
        else:
            print(f"  ERROR - {response.status_code}: {response.text[:200]}...")
            
    except Exception as e:
        print(f"  ERROR - Error de conexión: {e}")
    
    return False

if __name__ == "__main__":
    success = test_whatsapp_bot()
    if success:
        print("\nEl bot de WhatsApp está funcionando correctamente!")
    else:
        print("\nEl bot de WhatsApp no está funcionando. Revisar configuración.")
