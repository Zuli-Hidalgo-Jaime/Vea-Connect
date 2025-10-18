#!/usr/bin/env python
"""
Script para verificar la configuración de Azure Blob Storage
"""
import os
import sys
from pathlib import Path

# Agregar el directorio del proyecto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

import django
django.setup()

from django.conf import settings

def check_azure_config():
    """Verifica la configuración de Azure Blob Storage"""
    print("🔍 Verificando configuración de Azure Blob Storage...")
    print("-" * 50)
    
    # Verificar variables de entorno
    blob_account_name = getattr(settings, 'BLOB_ACCOUNT_NAME', None)
    blob_account_key = getattr(settings, 'BLOB_ACCOUNT_KEY', None)
    blob_container_name = getattr(settings, 'BLOB_CONTAINER_NAME', None)
    
    print(f"BLOB_ACCOUNT_NAME: {'✅ Configurado' if blob_account_name else '❌ No configurado'}")
    print(f"BLOB_ACCOUNT_KEY: {'✅ Configurado' if blob_account_key else '❌ No configurado'}")
    print(f"BLOB_CONTAINER_NAME: {'✅ Configurado' if blob_container_name else '❌ No configurado'}")
    
    # Verificar si Azure está deshabilitado
    azure_disabled = getattr(settings, 'DISABLE_AZURE_SIGNALS', False)
    print(f"DISABLE_AZURE_SIGNALS: {'✅ Sí (Azure deshabilitado)' if azure_disabled else '❌ No (Azure habilitado)'}")
    
    # Verificar configuración de almacenamiento
    print(f"MEDIA_URL: {getattr(settings, 'MEDIA_URL', 'No configurado')}")
    print(f"MEDIA_ROOT: {getattr(settings, 'MEDIA_ROOT', 'No configurado')}")
    
    print("-" * 50)
    
    if azure_disabled:
        print("ℹ️  Azure Blob Storage está deshabilitado. La aplicación usará almacenamiento local.")
        print("   Para habilitar Azure, configura las variables de entorno necesarias.")
    elif all([blob_account_name, blob_account_key, blob_container_name]):
        print("✅ Azure Blob Storage está configurado correctamente.")
        print("   Intentando conectar...")
        
        try:
            from utilities.azureblobstorage import get_blob_service_client
            client = get_blob_service_client()
            print("✅ Conexión exitosa a Azure Blob Storage")
            
            # Verificar si el contenedor existe
            container_client = client.get_container_client(blob_container_name)
            try:
                container_client.get_container_properties()
                print(f"✅ Contenedor '{blob_container_name}' existe")
            except Exception as e:
                print(f"❌ Contenedor '{blob_container_name}' no existe: {e}")
                
        except Exception as e:
            print(f"❌ Error al conectar con Azure Blob Storage: {e}")
    else:
        print("❌ Azure Blob Storage no está configurado completamente.")
        print("   Configura las variables de entorno necesarias o usa almacenamiento local.")

if __name__ == "__main__":
    check_azure_config() 