#!/usr/bin/env python3
"""
Script para configurar WhatsApp en Azure Communication Services
"""
import os
import json
import requests
import subprocess
from pathlib import Path

def load_env_from_functions():
    """Carga variables de entorno desde functions/local.settings.json"""
    functions_settings_path = Path(__file__).parent / "functions" / "local.settings.json"
    
    if functions_settings_path.exists():
        try:
            with open(functions_settings_path, 'r') as f:
                settings = json.load(f)
            
            values = settings.get('Values', {})
            
            # Variables críticas para ACS
            acs_vars = [
                'ACS_CONNECTION_STRING',
                'ACS_WHATSAPP_ENDPOINT',
                'ACS_WHATSAPP_API_KEY',
                'ACS_PHONE_NUMBER',
                'WHATSAPP_CHANNEL_ID_GUID'
            ]
            
            loaded_count = 0
            for var in acs_vars:
                value = values.get(var)
                if value:
                    os.environ[var] = value
                    loaded_count += 1
            
            print(f"✅ Variables de ACS cargadas: {loaded_count}/{len(acs_vars)}")
            return True
        except Exception as e:
            print(f"❌ Error cargando variables: {e}")
            return False
    return False

def check_acs_service():
    """Verifica el estado del servicio ACS"""
    print("\n🔍 Verificando servicio ACS...")
    
    try:
        result = subprocess.run([
            'az', 'resource', 'show',
            '--name', 'acs-veu-connect-00',
            '--resource-group', 'rg-vea-connect-dev',
            '--resource-type', 'Microsoft.Communication/communicationServices'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            service_info = json.loads(result.stdout)
            print(f"✅ Servicio ACS encontrado: {service_info.get('name', 'N/A')}")
            print(f"   Hostname: {service_info.get('properties', {}).get('hostName', 'N/A')}")
            print(f"   Estado: {service_info.get('properties', {}).get('provisioningState', 'N/A')}")
            return service_info
        else:
            print(f"❌ Error verificando servicio: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def get_acs_keys():
    """Obtiene las claves de acceso del servicio ACS"""
    print("\n🔑 Obteniendo claves de acceso...")
    
    try:
        # Intentar obtener las claves usando REST API
        subscription_id = "9f47ecda-6fbc-479d-888a-a5966f0c9c50"
        resource_group = "rg-vea-connect-dev"
        service_name = "acs-veu-connect-00"
        
        # Primero obtener el token de acceso
        result = subprocess.run([
            'az', 'account', 'get-access-token',
            '--resource', 'https://management.azure.com/'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            token_info = json.loads(result.stdout)
            access_token = token_info.get('accessToken')
            
            if access_token:
                # Usar REST API para obtener las claves
                url = f"https://management.azure.com/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Communication/communicationServices/{service_name}/listKeys?api-version=2023-03-31"
                
                headers = {
                    'Authorization': f'Bearer {access_token}',
                    'Content-Type': 'application/json'
                }
                
                response = requests.post(url, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    keys = response.json()
                    print("✅ Claves obtenidas exitosamente")
                    return keys
                else:
                    print(f"❌ Error obteniendo claves: {response.status_code}")
                    print(f"   Respuesta: {response.text}")
                    return None
            else:
                print("❌ No se pudo obtener el token de acceso")
                return None
        else:
            print(f"❌ Error obteniendo token: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Error obteniendo claves: {e}")
        return None

def test_whatsapp_configuration():
    """Prueba la configuración actual de WhatsApp"""
    print("\n🔍 Probando configuración actual de WhatsApp...")
    
    endpoint = os.environ.get('ACS_WHATSAPP_ENDPOINT')
    api_key = os.environ.get('ACS_WHATSAPP_API_KEY')
    
    if not endpoint or not api_key:
        print("❌ Endpoint o API key no configurados")
        return False
    
    # Limpiar endpoint
    endpoint = endpoint.rstrip('/')
    
    # Probar diferentes endpoints de WhatsApp
    test_endpoints = [
        f"{endpoint}/",
        f"{endpoint}/messages",
        f"{endpoint}/messages?api-version=2024-02-15-preview",
        f"{endpoint}/phoneNumbers",
        f"{endpoint}/phoneNumbers?api-version=2024-02-15-preview"
    ]
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    working_endpoints = []
    
    for test_url in test_endpoints:
        try:
            print(f"🔍 Probando: {test_url}")
            response = requests.get(test_url, headers=headers, timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                working_endpoints.append(test_url)
                print(f"   ✅ Funcionando")
            elif response.status_code == 401:
                print(f"   ⚠️ No autorizado (posible problema de API key)")
            elif response.status_code == 404:
                print(f"   ❌ No encontrado")
            else:
                print(f"   ❌ Error: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:50]}...")
    
    return working_endpoints

def setup_whatsapp_webhook():
    """Configura el webhook de WhatsApp"""
    print("\n🔧 Configurando webhook de WhatsApp...")
    
    # El webhook debe apuntar a las Azure Functions
    function_url = os.environ.get('FUNCTION_APP_URL')
    if not function_url:
        print("❌ FUNCTION_APP_URL no configurada")
        return False
    
    webhook_url = f"{function_url}/runtime/webhooks/eventgrid?functionName=whatsapp_event_grid_trigger"
    
    print(f"📍 Webhook URL: {webhook_url}")
    
    # Aquí necesitarías configurar el webhook en Azure Communication Services
    # Esto requiere acceso al portal de Azure o usar la API REST
    print("⚠️ La configuración del webhook requiere acceso al portal de Azure")
    print("   Pasos manuales:")
    print("   1. Ir a Azure Portal")
    print("   2. Buscar el servicio 'acs-veu-connect-00'")
    print("   3. Ir a 'WhatsApp' en el menú lateral")
    print("   4. Configurar el webhook con la URL:")
    print(f"      {webhook_url}")
    
    return True

def main():
    """Función principal"""
    print("🚀 CONFIGURACIÓN DE WHATSAPP EN AZURE COMMUNICATION SERVICES")
    print("=" * 70)
    
    # Cargar variables de entorno
    if not load_env_from_functions():
        print("❌ No se pudieron cargar las variables de entorno")
        return
    
    # Verificar servicio ACS
    service_info = check_acs_service()
    if not service_info:
        print("❌ No se pudo verificar el servicio ACS")
        return
    
    # Obtener claves de acceso
    keys = get_acs_keys()
    if keys:
        print(f"✅ Claves disponibles: {list(keys.keys())}")
    
    # Probar configuración actual
    working_endpoints = test_whatsapp_configuration()
    
    # Configurar webhook
    setup_whatsapp_webhook()
    
    # Resumen
    print("\n📋 RESUMEN:")
    print("=" * 30)
    
    if service_info:
        print("✅ Servicio ACS existe y está activo")
    else:
        print("❌ Problema con el servicio ACS")
    
    if keys:
        print("✅ Claves de acceso disponibles")
    else:
        print("❌ No se pudieron obtener las claves")
    
    if working_endpoints:
        print(f"✅ {len(working_endpoints)} endpoints funcionando")
    else:
        print("❌ No hay endpoints funcionando")
    
    # Recomendaciones
    print("\n💡 PRÓXIMOS PASOS:")
    print("   1. Verificar que WhatsApp esté habilitado en el servicio ACS")
    print("   2. Configurar el webhook en Azure Portal")
    print("   3. Verificar que las Azure Functions estén desplegadas")
    print("   4. Probar el envío de mensajes")

if __name__ == "__main__":
    main()
