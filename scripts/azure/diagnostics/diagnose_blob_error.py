#!/usr/bin/env python
"""
Script para diagnosticar problemas con Azure Blob Storage
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
from apps.documents.models import Document

def test_blob_urls():
    """Prueba las URLs de los blobs en la base de datos"""
    print("🔍 Probando URLs de blobs en la base de datos...")
    print("-" * 50)
    
    try:
        documents = Document.objects.all()
        print(f"Total de documentos en la base de datos: {documents.count()}")
        print()
        
        for i, doc in enumerate(documents[:5], 1):  # Probar solo los primeros 5
            print(f"Documento {i}: {doc.title}")
            print(f"  Archivo: {doc.file.name if doc.file else 'Sin archivo'}")
            
            if doc.file:
                try:
                    # Probar la URL SAS
                    sas_url = doc.sas_url
                    if sas_url:
                        print(f"  URL SAS: {sas_url[:100]}...")
                        
                        # Verificar si el blob existe
                        from utilities.azureblobstorage import get_blob_service_client
                        blob_service_client = get_blob_service_client()
                        container_client = blob_service_client.get_container_client(settings.BLOB_CONTAINER_NAME)
                        blob_client = container_client.get_blob_client(doc.file.name)
                        
                        if blob_client.exists():
                            print(f"  ✅ Blob existe en Azure")
                            properties = blob_client.get_blob_properties()
                            print(f"     Tamaño: {properties.size:,} bytes")
                        else:
                            print(f"  ❌ Blob NO existe en Azure")
                            
                except Exception as e:
                    print(f"  ❌ Error al verificar blob: {e}")
            else:
                print(f"  ⚠️  Documento sin archivo")
            print()
            
    except Exception as e:
        print(f"❌ Error al acceder a la base de datos: {e}")

def test_specific_blob(blob_name):
    """Prueba un blob específico"""
    print(f"🔍 Probando blob específico: {blob_name}")
    print("-" * 50)
    
    try:
        from utilities.azureblobstorage import get_blob_service_client
        
        blob_service_client = get_blob_service_client()
        container_name = settings.BLOB_CONTAINER_NAME
        
        container_client = blob_service_client.get_container_client(container_name)
        blob_client = container_client.get_blob_client(blob_name)
        
        # Verificar si existe
        if blob_client.exists():
            print(f"✅ Blob existe")
            properties = blob_client.get_blob_properties()
            print(f"   Tamaño: {properties.size:,} bytes")
            print(f"   Content-Type: {properties.content_settings.content_type}")
            print(f"   Última modificación: {properties.last_modified}")
            
            # Generar URL SAS
            from azure.storage.blob import generate_blob_sas, BlobSasPermissions
            from datetime import datetime, timedelta
            
            sas_token = generate_blob_sas(
                account_name=settings.BLOB_ACCOUNT_NAME,
                container_name=container_name,
                blob_name=blob_name,
                account_key=settings.BLOB_ACCOUNT_KEY,
                permission=BlobSasPermissions(read=True),
                expiry=datetime.utcnow() + timedelta(hours=2)
            )
            
            url = f"https://{settings.BLOB_ACCOUNT_NAME}.blob.core.windows.net/{container_name}/{blob_name}?{sas_token}"
            print(f"   URL SAS: {url}")
            
        else:
            print(f"❌ Blob no existe")
            
            # Buscar blobs similares
            print("\n🔍 Buscando blobs similares...")
            blobs = container_client.list_blobs(name_starts_with=blob_name.split('/')[0])
            similar_blobs = list(blobs)
            
            if similar_blobs:
                print("Blobs similares encontrados:")
                for blob in similar_blobs[:5]:
                    print(f"   - {blob.name}")
            else:
                print("No se encontraron blobs similares.")
                
    except Exception as e:
        print(f"❌ Error: {e}")

def generate_test_urls():
    """Genera URLs de prueba para archivos conocidos"""
    print("🔗 Generando URLs de prueba...")
    print("-" * 50)
    
    test_files = [
        "test.pdf",
        "documents/test_document.pdf",
        "minuta.pdf"
    ]
    
    try:
        from utilities.azureblobstorage import get_blob_service_client
        from azure.storage.blob import generate_blob_sas, BlobSasPermissions
        from datetime import datetime, timedelta
        
        blob_service_client = get_blob_service_client()
        container_name = settings.BLOB_CONTAINER_NAME
        
        for test_file in test_files:
            print(f"Archivo: {test_file}")
            
            try:
                container_client = blob_service_client.get_container_client(container_name)
                blob_client = container_client.get_blob_client(test_file)
                
                if blob_client.exists():
                    sas_token = generate_blob_sas(
                        account_name=settings.BLOB_ACCOUNT_NAME,
                        container_name=container_name,
                        blob_name=test_file,
                        account_key=settings.BLOB_ACCOUNT_KEY,
                        permission=BlobSasPermissions(read=True),
                        expiry=datetime.utcnow() + timedelta(hours=2)
                    )
                    
                    url = f"https://{settings.BLOB_ACCOUNT_NAME}.blob.core.windows.net/{container_name}/{test_file}?{sas_token}"
                    print(f"  ✅ URL: {url}")
                else:
                    print(f"  ❌ No existe")
                    
            except Exception as e:
                print(f"  ❌ Error: {e}")
            print()
            
    except Exception as e:
        print(f"❌ Error general: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            test_blob_urls()
        elif sys.argv[1] == "urls":
            generate_test_urls()
        else:
            test_specific_blob(sys.argv[1])
    else:
        print("Uso:")
        print("  python diagnose_blob_error.py test     - Probar URLs de documentos en BD")
        print("  python diagnose_blob_error.py urls     - Generar URLs de prueba")
        print("  python diagnose_blob_error.py <blob>   - Probar blob específico")
        print()
        test_blob_urls() 