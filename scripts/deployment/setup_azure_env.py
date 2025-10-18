#!/usr/bin/env python
"""
Script para configurar variables de entorno en Azure App Service
"""
import os
import subprocess
import sys

def run_azure_command(command):
    """Ejecutar comando de Azure CLI"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {command}")
            return result.stdout
        else:
            print(f"❌ {command}")
            print(f"Error: {result.stderr}")
            return None
    except Exception as e:
        print(f"❌ Error ejecutando: {command}")
        print(f"Error: {e}")
        return None

def setup_azure_environment():
    """Configurar variables de entorno en Azure"""
    print("🔧 Configurando variables de entorno en Azure...")
    
    # Variables de entorno necesarias
    env_vars = {
        'AZURE_POSTGRESQL_NAME': 'veaconnect-db',
        'AZURE_POSTGRESQL_USERNAME': 'veaconnect_user',
        'AZURE_POSTGRESQL_PASSWORD': '[CONFIGURAR_EN_AZURE]',
        'AZURE_POSTGRESQL_HOST': 'veaconnect-db.postgres.database.azure.com',
        'DB_PORT': '5432',
        'AZURE_STORAGE_CONNECTION_STRING': '[CONFIGURAR_EN_AZURE]',
        'BLOB_ACCOUNT_NAME': 'veaconnectstorage',
        'BLOB_ACCOUNT_KEY': '[CONFIGURAR_EN_AZURE]',
        'BLOB_CONTAINER_NAME': 'veaconnect-container',
        'AZURE_OPENAI_ENDPOINT': 'https://veaconnect-openai.openai.azure.com/',
        'AZURE_OPENAI_CHAT_DEPLOYMENT': 'gpt-4',
        'AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT': 'text-embedding-ada-002',
        'AZURE_OPENAI_CHAT_API_VERSION': '2024-02-15-preview',
        'AZURE_OPENAI_EMBEDDINGS_API_VERSION': '2024-02-15-preview',
        'OPENAI_API_KEY': '[CONFIGURAR_EN_AZURE]',
        'ACS_CONNECTION_STRING': '[CONFIGURAR_EN_AZURE]',
        'ACS_EVENT_GRID_TOPIC_ENDPOINT': 'https://veaconnect-events.westus2-1.eventgrid.azure.net/api/events',
        'ACS_EVENT_GRID_TOPIC_KEY': '[CONFIGURAR_EN_AZURE]',
        'ACS_PHONE_NUMBER': '+1234567890',
        'ACS_WHATSAPP_API_KEY': '[CONFIGURAR_EN_AZURE]',
        'ACS_WHATSAPP_ENDPOINT': 'https://veaconnect-acs.communication.azure.com/',
        'WHATSAPP_ACCESS_TOKEN': '[CONFIGURAR_EN_AZURE]',
        'WHATSAPP_CHANNEL_ID_GUID': '[CONFIGURAR_EN_AZURE]',
        'AZURE_KEYVAULT_RESOURCEENDPOINT': 'https://vault.azure.net/',
        'AZURE_KEYVAULT_SCOPE': 'https://vault.azure.net/.default',
        'APPLICATIONINSIGHTS_CONNECTION_STRING': '[CONFIGURAR_EN_AZURE]',
        'ApplicationInsightsAgent_EXTENSION_VERSION': '~3',
        'QUEUE_NAME': 'veaconnect-queue',
        'BUILD_FLAGS': '--build-arg BUILDKIT_INLINE_CACHE=1',
        'SCM_DO_BUILD_DURING_DEPLOYMENT': 'true',
        'XDT_MicrosoftApplicationInsights_Mode': 'Recommended',
        'WEBSITE_HOSTNAME': 'veaconnect-webapp-prod-c7aaezbce3ftacdp.centralus-01.azurewebsites.net',
        'ALLOWED_HOSTS': 'veaconnect-webapp-prod-c7aaezbce3ftacdp.centralus-01.azurewebsites.net,localhost,127.0.0.1'
    }
    
    app_service_name = "veaconnect-webapp-prod-c7aaezbce3ftacdp"
    resource_group = "veaconnect-webapp-prod-rg"
    
    print(f"🎯 Configurando App Service: {app_service_name}")
    print(f"📦 Resource Group: {resource_group}")
    
    # Configurar cada variable de entorno
    for key, value in env_vars.items():
        command = f'az webapp config appsettings set --name {app_service_name} --resource-group {resource_group} --settings {key}="{value}"'
        result = run_azure_command(command)
        if result:
            print(f"✅ {key} configurado")
        else:
            print(f"❌ Error configurando {key}")
    
    print("\n🔄 Reiniciando App Service...")
    restart_command = f'az webapp restart --name {app_service_name} --resource-group {resource_group}'
    run_azure_command(restart_command)
    
    print("\n✅ Configuración completada")
    print("⚠️  IMPORTANTE: Actualiza las claves y valores reales en Azure Portal")

def main():
    """Función principal"""
    print("🚀 Configurador de Variables de Entorno para Azure")
    print("=" * 60)
    
    # Verificar si Azure CLI está instalado
    try:
        result = subprocess.run(['az', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Azure CLI no está instalado")
            print("📥 Instala Azure CLI desde: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli")
            return False
    except FileNotFoundError:
        print("❌ Azure CLI no está instalado")
        print("📥 Instala Azure CLI desde: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli")
        return False
    
    # Verificar si estamos logueados
    account_result = subprocess.run(['az', 'account', 'show'], capture_output=True, text=True)
    if account_result.returncode != 0:
        print("❌ No estás logueado en Azure")
        print("🔐 Ejecuta: az login")
        return False
    
    setup_azure_environment()
    return True

if __name__ == "__main__":
    main() 