#!/usr/bin/env python3
"""
Script de diagnóstico específico para WhatsApp usando el SDK oficial de Azure Communication Advanced Messages
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
            'WHATSAPP_CHANNEL_ID_GUID'
        ]
        
        for var in critical_vars:
            value = values.get(var)
            if value:
                os.environ[var] = value
                print(f"Cargada: {var}")
            else:
                print(f"No encontrada: {var}")
        
        return True
        
    except Exception as e:
        print(f"Error cargando variables: {e}")
        return False

def test_advanced_messages_sdk():
    """Prueba el SDK oficial de Azure Communication Advanced Messages"""
    print("\nPRUEBA CON SDK OFICIAL DE ADVANCED MESSAGES")
    print("=" * 50)
    
    try:
        from azure.communication.messages import NotificationMessagesClient
        from azure.communication.messages.models import TextNotificationContent, ImageNotificationContent
        
        # Obtener configuración
        connection_string = os.getenv('ACS_CONNECTION_STRING')
        channel_registration_id = os.getenv('WHATSAPP_CHANNEL_ID_GUID')
        recipient_number = "+5215519387611"  # Número de prueba
        
        if not connection_string:
            print("ERROR - ACS_CONNECTION_STRING no configurada")
            return False
        
        if not channel_registration_id:
            print("ERROR - WHATSAPP_CHANNEL_ID_GUID no configurado")
            return False
        
        print(f"Connection String: {'SET' if connection_string else 'NOT SET'}")
        print(f"Channel Registration ID: {channel_registration_id}")
        print(f"Recipient Number: {recipient_number}")
        
        # Crear cliente
        messaging_client = NotificationMessagesClient.from_connection_string(connection_string)
        print("EXITO - Cliente Advanced Messages creado correctamente")
        
        # Probar mensaje de texto
        print("\nEnviando mensaje de texto...")
        text_options = TextNotificationContent(
            channel_registration_id=channel_registration_id,
            to=[recipient_number],
            content="Hola! Soy el bot de VEA Connect. Este es un mensaje de prueba desde el diagnóstico usando el SDK oficial."
        )
        
        message_responses = messaging_client.send(text_options)
        response = message_responses.receipts[0]
        
        if response is not None:
            print(f"EXITO - Mensaje de texto enviado correctamente")
            print(f"  Message ID: {response.message_id}")
            print(f"  To: {response.to}")
        else:
            print("ERROR - El mensaje de texto falló al enviar")
            return False
        
        # Probar mensaje con imagen
        print("\nEnviando mensaje con imagen...")
        image_url = "https://aka.ms/acsicon1"
        image_options = ImageNotificationContent(
            channel_registration_id=channel_registration_id,
            to=[recipient_number],
            media_uri=image_url
        )
        
        message_responses = messaging_client.send(image_options)
        response = message_responses.receipts[0]
        
        if response is not None:
            print(f"EXITO - Mensaje con imagen enviado correctamente")
            print(f"  Message ID: {response.message_id}")
            print(f"  To: {response.to}")
        else:
            print("ERROR - El mensaje con imagen falló al enviar")
            return False
        
        print("\nEXITO - Todos los mensajes se enviaron correctamente con el SDK oficial")
        return True
        
    except ImportError as e:
        print(f"ERROR - No se pudo importar el SDK: {e}")
        print("Instalar con: pip install azure-communication-messages")
        return False
    except Exception as e:
        print(f"ERROR - Error con el SDK: {e}")
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

def diagnose_whatsapp_config():
    """Diagnóstico completo de la configuración de WhatsApp"""
    
    print("DIAGNÓSTICO DE CONFIGURACIÓN DE WHATSAPP")
    print("=" * 50)
    
    # Cargar variables locales
    if not load_local_settings():
        print("No se pudieron cargar las variables locales")
        return False
    
    # Verificar variables de entorno
    print("\nVariables de entorno:")
    
    # Variables principales
    acs_connection_string = os.getenv('ACS_CONNECTION_STRING')
    acs_phone_number = os.getenv('ACS_PHONE_NUMBER')
    whatsapp_channel_id = os.getenv('WHATSAPP_CHANNEL_ID_GUID')
    
    print(f"  ACS_CONNECTION_STRING: {'SET' if acs_connection_string else 'NOT SET'}")
    print(f"  ACS_PHONE_NUMBER: {'SET' if acs_phone_number else 'NOT SET'}")
    print(f"  WHATSAPP_CHANNEL_ID_GUID: {'SET' if whatsapp_channel_id else 'NOT SET'}")
    
    # Variables adicionales
    acs_endpoint = os.getenv('ACS_WHATSAPP_ENDPOINT')
    acs_api_key = os.getenv('ACS_WHATSAPP_API_KEY')
    
    print(f"  ACS_WHATSAPP_ENDPOINT: {'SET' if acs_endpoint else 'NOT SET'}")
    print(f"  ACS_WHATSAPP_API_KEY: {'SET' if acs_api_key else 'NOT SET'}")
    
    # Determinar qué número usar
    from_number = acs_phone_number
    if from_number:
        print(f"\nNúmero del bot: {from_number}")
        
        # Normalizar formato
        if not from_number.startswith('+'):
            from_number = '+' + from_number
            print(f"Número normalizado: {from_number}")
    else:
        print("\nNo hay número de teléfono configurado")
        return False
    
    # Parsear connection string
    if not acs_connection_string:
        print("\nACS_CONNECTION_STRING no configurada")
        return False
    
    print(f"\nParseando connection string...")
    
    conn_parts = acs_connection_string.split(';')
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
    print(f"  Access Key: {'SET' if access_key else 'NOT SET'}")
    
    # Limpiar endpoint
    if endpoint.endswith('/'):
        endpoint = endpoint.rstrip('/')
    
    # Probar diferentes versiones de API
    print(f"\nProbando versiones de API...")
    
    api_versions = [
        '2024-02-15-preview',
        '2023-10-01-preview',
        '2021-10-20-preview'
    ]
    
    test_payload = {
        "content": "Mensaje de prueba desde diagnóstico",
        "from": from_number,
        "to": ["+5215519387611"]  # Número de prueba desde los logs
    }
    
    payload_json = json.dumps(test_payload)
    
    working_api_version = None
    
    for api_version in api_versions:
        print(f"\n  Probando API version: {api_version}")
        
        url = f"{endpoint}/messages?api-version={api_version}"
        print(f"    URL: {url}")
        
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
                print(f"    EXITO - API version {api_version} funciona")
                working_api_version = api_version
                break
            elif response.status_code == 401:
                print(f"    No autorizado - verificar access key")
            elif response.status_code == 404:
                print(f"    No encontrado - endpoint o API version incorrecta")
            else:
                print(f"    Error {response.status_code}: {response.text[:100]}...")
                
        except Exception as e:
            print(f"    Error de conexión: {str(e)[:50]}...")
    
    # Probar con el SDK oficial
    sdk_success = test_advanced_messages_sdk()
    
    # Resumen
    print(f"\nRESUMEN:")
    print("=" * 30)
    
    if sdk_success:
        print(f"EXITO - SDK oficial funcionando correctamente")
        print(f"Número del bot: {from_number}")
        print(f"Channel ID: {whatsapp_channel_id}")
        
        print(f"\nRECOMENDACIONES:")
        print("   1. El SDK oficial está funcionando correctamente")
        print("   2. Usar el SDK oficial en lugar de HTTP directo")
        print("   3. El código está actualizado con las mejores prácticas")
        
        return True
    elif working_api_version:
        print(f"API funcionando con versión: {working_api_version}")
        print(f"Número del bot: {from_number}")
        print(f"Endpoint: {endpoint}")
        
        print(f"\nRECOMENDACIONES:")
        print("   1. La configuración parece correcta")
        print("   2. Instalar el SDK: pip install azure-communication-messages")
        print("   3. Actualizar el código para usar el SDK oficial")
        
        return True
    else:
        print(f"No hay versión de API funcionando")
        print(f"Número del bot: {from_number}")
        print(f"Endpoint: {endpoint}")
        
        print(f"\nRECOMENDACIONES:")
        print("   1. Verificar que el servicio ACS esté activo")
        print("   2. Verificar que el número de teléfono esté verificado en WhatsApp")
        print("   3. Verificar que la connection string sea correcta")
        
        return False

if __name__ == "__main__":
    success = diagnose_whatsapp_config()
    if success:
        print("\nDiagnóstico completado - Configuración correcta")
    else:
        print("\nDiagnóstico completado - Problemas encontrados")
