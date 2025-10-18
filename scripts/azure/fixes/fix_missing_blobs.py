#!/usr/bin/env python
"""
Script para identificar y corregir documentos con blobs faltantes
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

def find_missing_blobs():
    """Encuentra documentos con blobs faltantes"""
    print("🔍 Buscando documentos con blobs faltantes...")
    print("-" * 50)
    
    try:
        documents = Document.objects.all()
        missing_blobs = []
        
        for doc in documents:
            if doc.file:
                try:
                    from utilities.azureblobstorage import get_blob_service_client
                    blob_service_client = get_blob_service_client()
                    container_client = blob_service_client.get_container_client(settings.BLOB_CONTAINER_NAME)
                    blob_client = container_client.get_blob_client(doc.file.name)
                    
                    if not blob_client.exists():
                        missing_blobs.append(doc)
                        print(f"❌ Documento '{doc.title}' - Blob faltante: {doc.file.name}")
                        
                except Exception as e:
                    print(f"⚠️  Error verificando '{doc.title}': {e}")
        
        print(f"\n📊 Resumen:")
        print(f"   Total de documentos: {documents.count()}")
        print(f"   Documentos con blobs faltantes: {len(missing_blobs)}")
        
        return missing_blobs
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def fix_missing_blob(doc):
    """Intenta corregir un blob faltante"""
    print(f"\n🔧 Intentando corregir blob faltante para: {doc.title}")
    
    try:
        # Opción 1: Buscar archivo con nombre similar
        from utilities.azureblobstorage import get_blob_service_client
        blob_service_client = get_blob_service_client()
        container_client = blob_service_client.get_container_client(settings.BLOB_CONTAINER_NAME)
        
        # Extraer el nombre base del archivo
        original_name = doc.file.name
        base_name = os.path.splitext(os.path.basename(original_name))[0]
        extension = os.path.splitext(original_name)[1]
        
        print(f"   Buscando archivos similares a: {base_name}{extension}")
        
        # Buscar archivos con el mismo nombre base
        blobs = container_client.list_blobs()
        similar_files = []
        
        for blob in blobs:
            blob_name = blob.name
            blob_base = os.path.splitext(os.path.basename(blob_name))[0]
            blob_ext = os.path.splitext(blob_name)[1]
            
            if blob_base == base_name and blob_ext == extension:
                similar_files.append(blob_name)
        
        if similar_files:
            print(f"   ✅ Encontrados {len(similar_files)} archivos similares:")
            for file in similar_files:
                print(f"      - {file}")
            
            # Usar el primer archivo encontrado
            new_path = similar_files[0]
            print(f"   🔄 Actualizando ruta de: {original_name} -> {new_path}")
            
            # Actualizar el modelo
            doc.file.name = new_path
            doc.save(update_fields=['file'])
            
            print(f"   ✅ Documento actualizado correctamente")
            return True
        else:
            print(f"   ❌ No se encontraron archivos similares")
            
            # Opción 2: Crear un archivo de marcador de posición
            print(f"   📝 Creando archivo de marcador de posición...")
            
            # Crear un archivo temporal con contenido de marcador
            placeholder_content = f"Archivo faltante: {original_name}\nEste archivo no se encontró en Azure Blob Storage."
            
            from utilities.azureblobstorage import upload_to_blob
            from io import BytesIO
            
            buffer = BytesIO(placeholder_content.encode('utf-8'))
            upload_to_blob(buffer, original_name)
            
            print(f"   ✅ Archivo de marcador creado")
            return True
            
    except Exception as e:
        print(f"   ❌ Error al corregir: {e}")
        return False

def cleanup_database():
    """Limpia documentos sin archivos válidos"""
    print("\n🧹 Limpiando base de datos...")
    print("-" * 50)
    
    try:
        documents = Document.objects.all()
        cleaned_count = 0
        
        for doc in documents:
            if not doc.file or not doc.file.name:
                print(f"   🗑️  Eliminando documento sin archivo: {doc.title}")
                doc.delete()
                cleaned_count += 1
            else:
                # Verificar si el blob existe
                try:
                    from utilities.azureblobstorage import get_blob_service_client
                    blob_service_client = get_blob_service_client()
                    container_client = blob_service_client.get_container_client(settings.BLOB_CONTAINER_NAME)
                    blob_client = container_client.get_blob_client(doc.file.name)
                    
                    if not blob_client.exists():
                        print(f"   🗑️  Eliminando documento con blob faltante: {doc.title}")
                        doc.delete()
                        cleaned_count += 1
                        
                except Exception as e:
                    print(f"   ⚠️  Error verificando {doc.title}: {e}")
        
        print(f"   ✅ Documentos eliminados: {cleaned_count}")
        
    except Exception as e:
        print(f"   ❌ Error en limpieza: {e}")

def main():
    """Función principal"""
    print("🔧 Herramienta de corrección de blobs faltantes")
    print("=" * 50)
    
    # Encontrar blobs faltantes
    missing_blobs = find_missing_blobs()
    
    if not missing_blobs:
        print("\n✅ No se encontraron blobs faltantes")
        return
    
    # Preguntar qué hacer
    print(f"\n¿Qué deseas hacer?")
    print("1. Intentar corregir automáticamente")
    print("2. Limpiar documentos con blobs faltantes")
    print("3. Solo mostrar información")
    
    choice = input("\nSelecciona una opción (1-3): ").strip()
    
    if choice == "1":
        print("\n🔧 Corrigiendo blobs faltantes...")
        fixed_count = 0
        for doc in missing_blobs:
            if fix_missing_blob(doc):
                fixed_count += 1
        print(f"\n✅ Blobs corregidos: {fixed_count}/{len(missing_blobs)}")
        
    elif choice == "2":
        cleanup_database()
        
    elif choice == "3":
        print("\nℹ️  Solo mostrando información")
        
    else:
        print("\n❌ Opción no válida")

if __name__ == "__main__":
    main() 