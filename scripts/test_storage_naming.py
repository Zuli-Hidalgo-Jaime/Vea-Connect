#!/usr/bin/env python3
"""
Script de prueba rápida para el sistema de resolución de nombres de almacenamiento

Este script prueba el flujo completo:
1. Subir archivo con nombre original
2. Resolver por nombre original (sin prefijo)
3. Descargar por nombre original
4. Eliminar por nombre original

Uso:
    python scripts/test_storage_naming.py
"""

import os
import sys
import tempfile
import uuid
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.storage_service import AzureStorageService

def test_storage_naming():
    """Prueba el sistema de resolución de nombres"""
    print("🧪 PRUEBA DEL SISTEMA DE RESOLUCIÓN DE NOMBRES")
    print("=" * 60)
    
    # Inicializar servicio
    storage = AzureStorageService()
    if not storage.client:
        print("❌ No se pudo inicializar el servicio de almacenamiento")
        return False
    
    # Generar datos de prueba únicos
    test_uuid = str(uuid.uuid4())[:8]
    original_name = f"Donaciones Daya 2025_08_08_{test_uuid}.jpg"
    
    print(f"📝 Nombre original de prueba: {original_name}")
    
    # Crear archivo temporal
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
        temp_file.write(f"Contenido de prueba para {test_uuid}")
        temp_file_path = temp_file.name
    
    try:
        # PASO 1: Subir archivo
        print(f"\n📤 PASO 1: Subiendo archivo...")
        upload_result = storage.upload_file(
            file_path=temp_file_path,
            blob_name=original_name,
            category="documents",
            content_type="text/plain"
        )
        
        if not upload_result['success']:
            print(f"❌ Error en subida: {upload_result['error']}")
            return False
        
        print(f"✅ Subida exitosa")
        print(f"   Original: {upload_result['original_name']}")
        print(f"   Canónico: {upload_result['blob_name']}")
        
        # PASO 2: Resolver nombre
        print(f"\n🔍 PASO 2: Resolviendo nombre...")
        resolved_name = storage.resolve_blob_name(original_name)
        
        if not resolved_name:
            print(f"❌ No se pudo resolver el nombre")
            return False
        
        print(f"✅ Resolución exitosa: {resolved_name}")
        
        # PASO 3: Descargar archivo
        print(f"\n📥 PASO 3: Descargando archivo...")
        download_path = temp_file_path + ".downloaded"
        download_result = storage.download_file(
            blob_name=original_name,
            local_path=download_path
        )
        
        if not download_result['success']:
            print(f"❌ Error en descarga: {download_result['error']}")
            return False
        
        print(f"✅ Descarga exitosa")
        print(f"   Resuelto como: {download_result['resolved_name']}")
        
        # PASO 4: Verificar contenido
        print(f"\n🔍 PASO 4: Verificando contenido...")
        with open(download_path, 'r') as f:
            downloaded_content = f.read()
        
        expected_content = f"Contenido de prueba para {test_uuid}"
        if downloaded_content == expected_content:
            print(f"✅ Contenido verificado correctamente")
        else:
            print(f"❌ Contenido incorrecto")
            print(f"   Esperado: {expected_content}")
            print(f"   Obtenido: {downloaded_content}")
            return False
        
        # PASO 5: Generar URL firmada
        print(f"\n🔗 PASO 5: Generando URL firmada...")
        url_result = storage.get_blob_url(
            blob_name=original_name,
            expires_in=3600
        )
        
        if not url_result['success']:
            print(f"❌ Error generando URL: {url_result['error']}")
            return False
        
        print(f"✅ URL generada exitosamente")
        print(f"   URL: {url_result['signed_url'][:100]}...")
        
        # PASO 6: Eliminar archivo
        print(f"\n🗑️ PASO 6: Eliminando archivo...")
        delete_result = storage.delete_blob(original_name)
        
        if not delete_result['success']:
            print(f"❌ Error en eliminación: {delete_result['error']}")
            return False
        
        print(f"✅ Eliminación exitosa")
        print(f"   Resuelto como: {delete_result['resolved_name']}")
        
        # PASO 7: Verificar eliminación
        print(f"\n🔍 PASO 7: Verificando eliminación...")
        final_check = storage.resolve_blob_name(original_name)
        if not final_check:
            print(f"✅ Verificación final: archivo eliminado correctamente")
        else:
            print(f"⚠️ Advertencia: archivo aún existe después de eliminación")
        
        # Limpiar archivos temporales
        try:
            os.unlink(temp_file_path)
            os.unlink(download_path)
        except:
            pass
        
        print(f"\n🎉 ¡TODAS LAS PRUEBAS PASARON!")
        print(f"✅ El sistema de resolución de nombres funciona correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error durante las pruebas: {e}")
        # Limpiar archivo temporal
        try:
            os.unlink(temp_file_path)
        except:
            pass
        return False

def test_canonicalization():
    """Prueba la canonicalización de nombres"""
    print(f"\n🔧 PRUEBA DE CANONICALIZACIÓN")
    print("=" * 40)
    
    storage = AzureStorageService()
    
    test_cases = [
        ("Donaciones Daya 2025_08_08.jpg", "documents"),
        ("Contacto María González.pdf", "contacts"),
        ("Evento Fiesta 2025!.png", "events"),
        ("archivo con espacios y acentos.txt", None),
    ]
    
    for original, category in test_cases:
        canonical = storage.canonicalize_blob_name(original, category=category)
        print(f"Original: {original}")
        print(f"Canónico: {canonical}")
        print(f"Categoría: {category or 'Ninguna'}")
        print("-" * 30)

def main():
    """Función principal"""
    print("🚀 INICIANDO PRUEBAS DEL SISTEMA DE ALMACENAMIENTO")
    print("=" * 70)
    
    # Prueba de canonicalización
    test_canonicalization()
    
    # Prueba completa del sistema
    success = test_storage_naming()
    
    if success:
        print(f"\n🎯 RESULTADO: ÉXITO")
        print(f"El sistema de resolución de nombres está funcionando correctamente")
        print(f"Los errores BlobNotFound deberían desaparecer")
    else:
        print(f"\n💥 RESULTADO: FALLO")
        print(f"Hay problemas con el sistema de resolución de nombres")
    
    return success

if __name__ == "__main__":
    main()
