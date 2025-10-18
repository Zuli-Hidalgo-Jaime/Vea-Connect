#!/usr/bin/env python3
"""
Script para verificar el estado del servicio de Azure Communication Services
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

def check_azure_cli():
    """Verifica si Azure CLI está disponible"""
    try:
        result = subprocess.run(['az', 'version'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            version_info = json.loads(result.stdout)
            print(f"✅ Azure CLI disponible: {version_info.get('azure-cli', 'N/A')}")
            return True
        else:
            print("❌ Azure CLI no disponible")
            return False
    except Exception as e:
        print(f"❌ Error verificando Azure CLI: {e}")
        return False

def check_azure_auth():
    """Verifica la autenticación de Azure"""
    try:
        result = subprocess.run(['az', 'account', 'show'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            account_info = json.loads(result.stdout)
            print(f"✅ Autenticado como: {account_info.get('user', {}).get('name', 'N/A')}")
            print(f"   Subscription: {account_info.get('id', 'N/A')}")
            return True
        else:
            print("❌ No autenticado en Azure")
            return False
    except Exception as e:
        print(f"❌ Error verificando autenticación: {e}")
        return False

def check_acs_service():
    """Verifica si el servicio de ACS existe y está activo"""
    print("\n🔍 Verificando servicio de Azure Communication Services...")
    
    service_name = "acs-veu-connect-00"
    resource_group = "rg-vea-connect-dev"
    
    try:
        # Verificar si el servicio existe
        result = subprocess.run([
            'az', 'communication', 'show',
            '--name', service_name,
            '--resource-group', resource_group
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            service_info = json.loads(result.stdout)
            print(f"✅ Servicio ACS encontrado: {service_info.get('name', 'N/A')}")
            print(f"   Location: {service_info.get('location', 'N/A')}")
            print(f"   Provisioning State: {service_info.get('properties', {}).get('provisioningState', 'N/A')}")
            print(f"   Data Location: {service_info.get('properties', {}).get('dataLocation', 'N/A')}")
            return True
        else:
            print(f"❌ Servicio ACS '{service_name}' no encontrado")
            print(f"   Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando servicio ACS: {e}")
        return False

def list_acs_services():
    """Lista todos los servicios de ACS en el grupo de recursos"""
    print("\n🔍 Listando servicios de ACS disponibles...")
    
    resource_group = "rg-vea-connect-dev"
    
    try:
        result = subprocess.run([
            'az', 'communication', 'list',
            '--resource-group', resource_group
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            services = json.loads(result.stdout)
            if services:
                print(f"✅ Encontrados {len(services)} servicios de ACS:")
                for service in services:
                    print(f"   - {service.get('name', 'N/A')} ({service.get('location', 'N/A')})")
                    print(f"     Estado: {service.get('properties', {}).get('provisioningState', 'N/A')}")
            else:
                print("❌ No se encontraron servicios de ACS")
            return services
        else:
            print(f"❌ Error listando servicios: {result.stderr}")
            return []
            
    except Exception as e:
        print(f"❌ Error listando servicios ACS: {e}")
        return []

def test_acs_endpoints():
    """Prueba diferentes endpoints de ACS"""
    print("\n🔍 Probando endpoints de ACS...")
    
    endpoint = os.environ.get('ACS_WHATSAPP_ENDPOINT')
    api_key = os.environ.get('ACS_WHATSAPP_API_KEY')
    
    if not endpoint or not api_key:
        print("❌ Endpoint o API key no configurados")
        return False
    
    # Limpiar endpoint
    endpoint = endpoint.rstrip('/')
    
    # Probar diferentes endpoints
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

def main():
    """Función principal"""
    print("🚀 VERIFICACIÓN DEL SERVICIO DE AZURE COMMUNICATION SERVICES")
    print("=" * 70)
    
    # Cargar variables de entorno
    if not load_env_from_functions():
        print("❌ No se pudieron cargar las variables de entorno")
        return
    
    # Verificar Azure CLI
    if not check_azure_cli():
        print("❌ Azure CLI no disponible")
        return
    
    # Verificar autenticación
    if not check_azure_auth():
        print("❌ No autenticado en Azure")
        return
    
    # Verificar servicio ACS específico
    service_exists = check_acs_service()
    
    # Listar todos los servicios
    services = list_acs_services()
    
    # Probar endpoints
    working_endpoints = test_acs_endpoints()
    
    # Resumen
    print("\n📋 RESUMEN:")
    print("=" * 30)
    
    if service_exists:
        print("✅ Servicio ACS existe")
    else:
        print("❌ Servicio ACS no existe")
    
    if services:
        print(f"✅ {len(services)} servicios ACS encontrados")
    else:
        print("❌ No hay servicios ACS")
    
    if working_endpoints:
        print(f"✅ {len(working_endpoints)} endpoints funcionando")
    else:
        print("❌ No hay endpoints funcionando")
    
    # Recomendaciones
    print("\n💡 RECOMENDACIONES:")
    if not service_exists:
        print("   1. Crear el servicio ACS 'acs-veu-connect-00'")
        print("   2. Configurar WhatsApp Business API")
        print("   3. Configurar Event Grid")
    elif not working_endpoints:
        print("   1. Verificar la configuración del servicio ACS")
        print("   2. Verificar las API keys")
        print("   3. Verificar la región del servicio")

if __name__ == "__main__":
    main()
