#!/usr/bin/env python
"""
Script para listar todos los blobs en el contenedor de Azure
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

def list_azure_blobs():
    """Lista todos los blobs en el contenedor de Azure"""
    print("📋 Listando blobs en Azure Blob Storage...")
    print("-" * 50)
    
    try:
        from utilities.azureblobstorage import get_blob_service_client
        
        blob_service_client = get_blob_service_client()
        container_name = settings.BLOB_CONTAINER_NAME
        
        print(f"Contenedor: {container_name}")
        print("-" * 50)
        
        # Listar todos los blobs
        container_client = blob_service_client.get_container_client(container_name)
        blobs = container_client.list_blobs()
        
        blob_count = 0
        for blob in blobs:
            blob_count += 1
            print(f"{blob_count:3d}. {blob.name}")
            print(f"     Tamaño: {blob.size:,} bytes")
            print(f"     Última modificación: {blob.last_modified}")
            print(f"     Content-Type: {blob.content_settings.content_type}")
            print()
        
        if blob_count == 0:
            print("❌ No se encontraron blobs en el contenedor.")
        else:
            print(f"✅ Total de blobs encontrados: {blob_count}")
            
    except Exception as e:
        print(f"❌ Error al listar blobs: {e}")

def search_blob(blob_name):
    """Busca un blob específico"""
    print(f"🔍 Buscando blob: {blob_name}")
    print("-" * 50)
    
    try:
        from utilities.azureblobstorage import get_blob_service_client
        
        blob_service_client = get_blob_service_client()
        container_name = settings.BLOB_CONTAINER_NAME
        
        container_client = blob_service_client.get_container_client(container_name)
        blob_client = container_client.get_blob_client(blob_name)
        
        # Verificar si el blob existe
        if blob_client.exists():
            properties = blob_client.get_blob_properties()
            print(f"✅ Blob encontrado: {blob_name}")
            print(f"   Tamaño: {properties.size:,} bytes")
            print(f"   Content-Type: {properties.content_settings.content_type}")
            print(f"   Última modificación: {properties.last_modified}")
        else:
            print(f"❌ Blob no encontrado: {blob_name}")
            
            # Buscar blobs similares
            print("\n🔍 Buscando blobs similares...")
            blobs = container_client.list_blobs(name_starts_with=blob_name.split('/')[0])
            similar_blobs = list(blobs)
            
            if similar_blobs:
                print("Blobs similares encontrados:")
                for blob in similar_blobs[:5]:  # Mostrar solo los primeros 5
                    print(f"   - {blob.name}")
            else:
                print("No se encontraron blobs similares.")
                
    except Exception as e:
        print(f"❌ Error al buscar blob: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Si se proporciona un nombre de blob, buscarlo
        search_blob(sys.argv[1])
    else:
        # Listar todos los blobs
        list_azure_blobs() 