#!/usr/bin/env python3
"""
Script para probar el endpoint específico de Messaging Connect
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

def test_messaging_connect_endpoint():
    """Prueba el endpoint específico de Messaging Connect"""
    
    print("PRUEBA DEL ENDPOINT ESPECÍFICO DE MESSAGING CONNECT")
    print("=" * 55)
    
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
    
    # Probar diferentes endpoints de Messaging Connect
    test_endpoints = [
        "/messaging/connect/messages",
        "/messagingConnect/messages",
        "/messaging-connect/messages",
        "/channels/{channel_id}/messages",
        "/channels/messages",
        "/messaging/messages",
        "/connect/messages"
    ]
    
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
    
    working_combination = None
    
    for test_path in test_endpoints:
        # Reemplazar {channel_id} con el ID real
        if "{channel_id}" in test_path:
            test_path = test_path.replace("{channel_id}", channel_id)
        
        print(f"\nProbando endpoint: {test_path}")
        
        for api_version in api_versions:
            print(f"  Con API version: {api_version}")
            
            url = f"{endpoint}{test_path}?api-version={api_version}"
            
            # Mensaje de prueba
            test_payload = {
                "content": "Hola! Soy el bot de VEA Connect. Este es un mensaje de prueba.",
                "from": from_number,
                "to": ["+5215519387611"]
            }
            
            # Agregar channelId si el endpoint lo requiere
            if "channels" in test_path:
                test_payload["channelId"] = channel_id
            
            payload_json = json.dumps(test_payload)
            
            # Generar firma HMAC
            signature = generate_hmac_signature(access_key, url, 'POST', payload_json)
            
            if not signature:
                print(f"    Error generando firma HMAC")
                continue
            
            headers = {
                'Authorization': f'HMAC-SHA256 {signature}',
                'Content-Type': 'application/json',
                'x-ms-date': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
            }
            
            try:
                response = requests.post(url, json=test_payload, headers=headers, timeout=30)
                
                print(f"    Status: {response.status_code}")
                
                if response.status_code == 202:
                    print(f"    EXITO - Endpoint y API version funcionan")
                    working_combination = (test_path, api_version)
                    print(f"    Response Headers: {dict(response.headers)}")
                    break
                elif response.status_code == 401:
                    print(f"    No autorizado - verificar access key")
                    break
                elif response.status_code == 404:
                    print(f"    No encontrado - endpoint no existe")
                elif response.status_code == 400:
                    try:
                        error_data = response.json()
                        error_code = error_data.get('error', {}).get('code', 'Unknown')
                        print(f"    Error 400: {error_code}")
                    except:
                        print(f"    Error 400: {response.text[:100]}...")
                else:
                    print(f"    Error {response.status_code}: {response.text[:100]}...")
                    
            except Exception as e:
                print(f"    Error de conexión: {str(e)[:50]}...")
            
            # Si encontramos una combinación que funciona, salir del bucle
            if working_combination:
                break
        
        # Si encontramos una combinación que funciona, salir del bucle
        if working_combination:
            break
    
    # También probar con el endpoint tradicional pero con diferentes payloads
    if not working_combination:
        print(f"\nProbando endpoint tradicional con diferentes payloads...")
        
        traditional_endpoints = [
            "/messages",
            "/send",
            "/sendMessage"
        ]
        
        for test_path in traditional_endpoints:
            print(f"\nProbando endpoint: {test_path}")
            
            for api_version in api_versions[:3]:  # Solo probar las primeras 3 versiones
                print(f"  Con API version: {api_version}")
                
                url = f"{endpoint}{test_path}?api-version={api_version}"
                
                # Diferentes formatos de payload
                payload_variants = [
                    {
                        "content": "Hola! Soy el bot de VEA Connect.",
                        "from": from_number,
                        "to": ["+5215519387611"]
                    },
                    {
                        "message": "Hola! Soy el bot de VEA Connect.",
                        "from": from_number,
                        "to": ["+5215519387611"]
                    },
                    {
                        "text": "Hola! Soy el bot de VEA Connect.",
                        "from": from_number,
                        "to": ["+5215519387611"]
                    },
                    {
                        "content": "Hola! Soy el bot de VEA Connect.",
                        "from": from_number,
                        "to": ["+5215519387611"],
                        "channelId": channel_id
                    }
                ]
                
                for i, test_payload in enumerate(payload_variants):
                    print(f"    Con payload variant {i+1}")
                    
                    payload_json = json.dumps(test_payload)
                    
                    signature = generate_hmac_signature(access_key, url, 'POST', payload_json)
                    
                    if not signature:
                        print(f"      Error generando firma HMAC")
                        continue
                    
                    headers = {
                        'Authorization': f'HMAC-SHA256 {signature}',
                        'Content-Type': 'application/json',
                        'x-ms-date': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
                    }
                    
                    try:
                        response = requests.post(url, json=test_payload, headers=headers, timeout=30)
                        
                        print(f"      Status: {response.status_code}")
                        
                        if response.status_code == 202:
                            print(f"      EXITO - Endpoint, API version y payload funcionan")
                            working_combination = (test_path, api_version, f"payload_variant_{i+1}")
                            break
                        elif response.status_code == 400:
                            try:
                                error_data = response.json()
                                error_code = error_data.get('error', {}).get('code', 'Unknown')
                                print(f"      Error 400: {error_code}")
                            except:
                                print(f"      Error 400: {response.text[:100]}...")
                                
                    except Exception as e:
                        print(f"      Error de conexión: {str(e)[:50]}...")
                
                if working_combination:
                    break
            
            if working_combination:
                break
    
    # Resumen
    print(f"\nRESUMEN:")
    print("=" * 30)
    
    if working_combination:
        print(f"Combinación funcionando encontrada:")
        print(f"  Endpoint: {working_combination[0]}")
        print(f"  API Version: {working_combination[1]}")
        if len(working_combination) > 2:
            print(f"  Payload: {working_combination[2]}")
        
        print(f"\nRECOMENDACIONES:")
        print("   1. Actualizar la Azure Function para usar esta configuración")
        print("   2. El bot debería funcionar correctamente")
        
        return True
    else:
        print("No se encontró combinación funcionando")
        print("Posibles problemas:")
        print("   1. El servicio ACS no tiene Messaging Connect habilitado")
        print("   2. El canal de WhatsApp no está configurado correctamente")
        print("   3. La API no está disponible en esta región")
        print("   4. El access key no tiene permisos para Messaging Connect")
        
        return False

if __name__ == "__main__":
    success = test_messaging_connect_endpoint()
    if success:
        print("\nSe encontró una configuración funcionando")
    else:
        print("\nNo se encontró configuración funcionando")
