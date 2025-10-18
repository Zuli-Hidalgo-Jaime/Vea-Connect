#!/usr/bin/env python3
"""
Script de diagnóstico para Azure Blob Storage.

Este script verifica la configuración de Azure Storage y lista
los archivos disponibles en el contenedor especificado.
"""

import os
import sys
from pathlib import Path

# Agregar el directorio raíz del proyecto al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.azure_production')

import django
django.setup()

from django.conf import settings
from azure.storage.blob import BlobServiceClient
from config.azure_storage import get_azure_account_name, get_azure_account_key, get_azure_container


def verify_azure_configuration():
    """Verifica la configuración de Azure Storage."""
    print("🔍 Verificando configuración de Azure Storage...")
    print("=" * 50)
    
    # Obtener configuración
    account_name = get_azure_account_name()
    account_key = get_azure_account_key()
    container_name = get_azure_container()
    
    print(f"📋 Account Name: {account_name}")
    print(f"🔑 Account Key: {'SET' if account_key else 'NOT SET'}")
    print(f"📦 Container Name: {container_name}")
    print()
    
    if not all([account_name, account_key, container_name]):
        print("❌ Configuración incompleta de Azure Storage")
        return False
    
    print("✅ Configuración básica de Azure Storage encontrada")
    return True


def test_azure_connection():
    """Prueba la conexión a Azure Blob Storage."""
    print("\n🔗 Probando conexión a Azure Blob Storage...")
    print("=" * 50)
    
    try:
        account_name = get_azure_account_name()
        account_key = get_azure_account_key()
        
        # Crear cliente de servicio
        connection_string = f"DefaultEndpointsProtocol=https;AccountName={account_name};AccountKey={account_key};EndpointSuffix=core.windows.net"
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        
        # Verificar que la cuenta existe
        account_info = blob_service_client.get_account_information()
        print(f"✅ Conexión exitosa a cuenta: {account_name}")
        print(f"📊 SKU: {account_info['sku_name']}")
        print(f"🌍 Location: {account_info['location']}")
        
        return blob_service_client
        
    except Exception as e:
        print(f"❌ Error al conectar con Azure Storage: {str(e)}")
        return None


def list_container_blobs(blob_service_client):
    """Lista los blobs en el contenedor especificado."""
    print("\n📋 Listando archivos en el contenedor...")
    print("=" * 50)
    
    try:
        container_name = get_azure_container()
        container_client = blob_service_client.get_container_client(container_name)
        
        # Listar todos los blobs
        blobs = list(container_client.list_blobs())
        
        if not blobs:
            print(f"📭 El contenedor '{container_name}' está vacío")
            return
        
        print(f"📁 Contenedor: {container_name}")
        print(f"📊 Total de archivos: {len(blobs)}")
        print()
        
        # Mostrar los primeros 20 archivos
        for i, blob in enumerate(blobs[:20]):
            print(f"  {i+1:2d}. {blob.name} ({blob.size} bytes)")
        
        if len(blobs) > 20:
            print(f"  ... y {len(blobs) - 20} archivos más")
            
    except Exception as e:
        print(f"❌ Error al listar archivos: {str(e)}")


def search_specific_file(blob_service_client, filename):
    """Busca un archivo específico en el contenedor."""
    print(f"\n🔍 Buscando archivo: {filename}")
    print("=" * 50)
    
    try:
        container_name = get_azure_container()
        container_client = blob_service_client.get_container_client(container_name)
        
        # Buscar archivos que coincidan con el patrón
        blobs = list(container_client.list_blobs(name_starts_with=filename.split('.')[0]))
        
        if not blobs:
            print(f"❌ No se encontraron archivos que coincidan con '{filename}'")
            
            # Buscar archivos similares
            print("\n🔍 Buscando archivos similares...")
            all_blobs = list(container_client.list_blobs())
            similar_files = []
            
            for blob in all_blobs:
                if 'tipos_donativos' in blob.name.lower():
                    similar_files.append(blob.name)
            
            if similar_files:
                print("📋 Archivos similares encontrados:")
                for file in similar_files:
                    print(f"  - {file}")
            else:
                print("❌ No se encontraron archivos similares")
        else:
            print("✅ Archivos encontrados:")
            for blob in blobs:
                print(f"  - {blob.name} ({blob.size} bytes)")
                
    except Exception as e:
        print(f"❌ Error al buscar archivo: {str(e)}")


def main():
    """Función principal del script."""
    print("🚀 Diagnóstico de Azure Blob Storage")
    print("=" * 60)
    
    # Verificar configuración
    if not verify_azure_configuration():
        print("\n❌ No se puede continuar sin configuración válida")
        return
    
    # Probar conexión
    blob_service_client = test_azure_connection()
    if not blob_service_client:
        print("\n❌ No se puede continuar sin conexión válida")
        return
    
    # Listar archivos
    list_container_blobs(blob_service_client)
    
    # Buscar archivo específico del log
    search_specific_file(blob_service_client, "tipos_donativos_202508120433_5457ea.jpg")
    
    print("\n✅ Diagnóstico completado")


if __name__ == "__main__":
    main()
