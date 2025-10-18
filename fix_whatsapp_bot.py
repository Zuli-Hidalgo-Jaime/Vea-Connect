#!/usr/bin/env python3
"""
Script para verificar y configurar el bot de WhatsApp
"""
import os
import json
import requests
from pathlib import Path

def load_env_from_functions():
    """Carga variables de entorno desde functions/local.settings.json"""
    functions_settings_path = Path(__file__).parent / "functions" / "local.settings.json"
    
    if functions_settings_path.exists():
        try:
            with open(functions_settings_path, 'r') as f:
                settings = json.load(f)
            
            values = settings.get('Values', {})
            
            # Variables críticas para WhatsApp
            whatsapp_vars = [
                'ACS_WHATSAPP_ENDPOINT',
                'ACS_WHATSAPP_API_KEY',
                'ACS_PHONE_NUMBER',
                'WHATSAPP_CHANNEL_ID_GUID',
                'FUNCTION_APP_URL'
            ]
            
            loaded_count = 0
            for var in whatsapp_vars:
                value = values.get(var)
                if value:
                    os.environ[var] = value
                    loaded_count += 1
            
            print(f"✅ Variables de WhatsApp cargadas: {loaded_count}/{len(whatsapp_vars)}")
            return True
        except Exception as e:
            print(f"❌ Error cargando variables: {e}")
            return False
    return False

def test_whatsapp_configuration():
    """Prueba la configuración de WhatsApp"""
    print("\n🔍 Verificando configuración de WhatsApp...")
    
    required_vars = [
        'ACS_WHATSAPP_ENDPOINT',
        'ACS_WHATSAPP_API_KEY', 
        'ACS_PHONE_NUMBER',
        'WHATSAPP_CHANNEL_ID_GUID'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.environ.get(var)
        if not value:
            missing_vars.append(var)
        else:
            print(f"✅ {var}: {value[:20]}..." if len(value) > 20 else f"✅ {var}: {value}")
    
    if missing_vars:
        print(f"❌ Variables faltantes: {missing_vars}")
        return False
    
    return True

def test_azure_functions():
    """Prueba las Azure Functions"""
    print("\n🔍 Verificando Azure Functions...")
    
    function_url = os.environ.get('FUNCTION_APP_URL')
    if not function_url:
        print("❌ FUNCTION_APP_URL no configurada")
        return False
    
    print(f"📍 URL de funciones: {function_url}")
    
    # Probar diferentes endpoints
    endpoints = [
        "/",
        "/health", 
        "/api/health",
        "/runtime/webhooks/eventgrid"
    ]
    
    for endpoint in endpoints:
        try:
            url = f"{function_url}{endpoint}"
            response = requests.get(url, timeout=10)
            print(f"✅ {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint}: {str(e)[:50]}...")
    
    return True

def test_whatsapp_send():
    """Prueba el envío de mensajes de WhatsApp"""
    print("\n🔍 Probando envío de WhatsApp...")
    
    endpoint = os.environ.get('ACS_WHATSAPP_ENDPOINT')
    api_key = os.environ.get('ACS_WHATSAPP_API_KEY')
    phone_number = os.environ.get('ACS_PHONE_NUMBER')
    channel_id = os.environ.get('WHATSAPP_CHANNEL_ID_GUID')
    
    if not all([endpoint, api_key, phone_number, channel_id]):
        print("❌ Variables de WhatsApp incompletas")
        return False
    
    print(f"📍 Endpoint: {endpoint}")
    print(f"📍 Número: {phone_number}")
    print(f"📍 Channel ID: {channel_id}")
    
    # Corregir el endpoint para usar la API correcta
    # El endpoint debe ser: https://acs-veu-connect-00.unitedstates.communication.azure.com/
    # Y la URL completa: https://acs-veaconnect-01.unitedstates.communication.azure.com/messages?api-version=2024-02-15-preview
    
    # Limpiar el endpoint si tiene trailing slash
    endpoint = endpoint.rstrip('/')
    send_url = f"{endpoint}/messages?api-version=2024-02-15-preview"
    
    print(f"📍 URL de envío: {send_url}")
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    # Mensaje de prueba usando el formato correcto para Azure Communication Services
    test_message = {
        "content": {
            "type": "text",
            "text": "🤖 Bot de prueba: Hola, este es un mensaje de prueba desde VEA Connect."
        },
        "from": f"whatsapp:{phone_number}",
        "to": [phone_number]  # Enviar al mismo número para prueba
    }
    
    print(f"📤 Enviando mensaje de prueba...")
    print(f"   Headers: {headers}")
    print(f"   Message: {json.dumps(test_message, indent=2)}")
    
    try:
        response = requests.post(send_url, headers=headers, json=test_message, timeout=30)
        
        print(f"📥 Respuesta: {response.status_code}")
        print(f"📥 Headers: {dict(response.headers)}")
        print(f"📥 Body: {response.text[:500]}...")
        
        if response.status_code == 202:
            print("✅ Mensaje enviado exitosamente")
            return True
        else:
            print(f"❌ Error enviando mensaje: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error en envío: {e}")
        return False

def test_acs_connection():
    """Prueba la conexión básica a Azure Communication Services"""
    print("\n🔍 Probando conexión a Azure Communication Services...")
    
    endpoint = os.environ.get('ACS_WHATSAPP_ENDPOINT')
    api_key = os.environ.get('ACS_WHATSAPP_API_KEY')
    
    if not endpoint or not api_key:
        print("❌ Endpoint o API key no configurados")
        return False
    
    # Limpiar endpoint
    endpoint = endpoint.rstrip('/')
    
    # Probar diferentes endpoints de ACS
    test_endpoints = [
        f"{endpoint}/",
        f"{endpoint}/messages",
        f"{endpoint}/messages?api-version=2024-02-15-preview"
    ]
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    for test_url in test_endpoints:
        try:
            print(f"🔍 Probando: {test_url}")
            response = requests.get(test_url, headers=headers, timeout=10)
            print(f"   Status: {response.status_code}")
            if response.status_code != 200:
                print(f"   Response: {response.text[:200]}...")
        except Exception as e:
            print(f"   Error: {str(e)[:50]}...")

def main():
    """Función principal"""
    print("🚀 VERIFICACIÓN Y CONFIGURACIÓN DEL BOT DE WHATSAPP")
    print("=" * 60)
    
    # Cargar variables de entorno
    if not load_env_from_functions():
        print("❌ No se pudieron cargar las variables de entorno")
        return
    
    # Verificar configuración
    if not test_whatsapp_configuration():
        print("❌ Configuración de WhatsApp incompleta")
        return
    
    # Verificar Azure Functions
    if not test_azure_functions():
        print("❌ Azure Functions no disponibles")
        return
    
    # Probar conexión a ACS
    test_acs_connection()
    
    # Probar envío de WhatsApp
    if test_whatsapp_send():
        print("\n🎉 ¡El bot de WhatsApp está configurado y funcionando!")
        print("\n📋 Resumen:")
        print("   ✅ Variables de entorno configuradas")
        print("   ✅ Azure Functions disponibles")
        print("   ✅ Envío de mensajes funcionando")
        print("\n💡 El bot debería responder a mensajes entrantes ahora.")
    else:
        print("\n❌ El bot de WhatsApp no está funcionando correctamente.")
        print("   Revisa la configuración de Azure Communication Services.")

if __name__ == "__main__":
    main()
