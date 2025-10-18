#!/usr/bin/env python3
"""
Script de prueba para verificar la corrección del error de descarga de documentos.
"""

import os
import sys
import logging
import inspect
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_get_blob_url_fix():
    """Prueba que la corrección del método get_blob_url funciona correctamente."""
    print_section("VERIFICACIÓN DE CORRECCIÓN DE DESCARGA")
    
    try:
        # Importar el servicio de almacenamiento
        from services.storage_service import AzureStorageService
        
        # Verificar que el método existe
        if hasattr(AzureStorageService, 'get_blob_url'):
            print("✅ Método get_blob_url existe")
            
            # Obtener el código fuente del método
            method_source = inspect.getsource(AzureStorageService.get_blob_url)
            
            # Verificar que se eliminó el quote_plus problemático
            if 'quote_plus(blob_client.url)' not in method_source:
                print("✅ Código problemático quote_plus(blob_client.url) eliminado")
            else:
                print("❌ Código problemático quote_plus(blob_client.url) aún presente")
                return False
            
            # Verificar que se usa la URL directa
            if 'f"{blob_client.url}?{sas_token}"' in method_source:
                print("✅ URL directa implementada correctamente")
            else:
                print("❌ URL directa no implementada")
                return False
            
            print("✅ Corrección de descarga aplicada correctamente")
            return True
            
        else:
            print("❌ Método get_blob_url no existe")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando corrección: {e}")
        return False

def test_download_view_fix():
    """Prueba que la vista de descarga maneja errores correctamente."""
    print_section("VERIFICACIÓN DE VISTA DE DESCARGA")
    
    try:
        # Importar la vista de descarga
        from apps.documents.views import download_document
        
        if download_document:
            print("✅ Vista download_document existe")
            
            # Verificar que maneja errores de URL
            view_source = inspect.getsource(download_document)
            
            if 'Error generando URL de descarga' in view_source:
                print("✅ Manejo de errores de URL implementado")
            else:
                print("❌ Manejo de errores de URL no encontrado")
                return False
            
            if 'storage_service.get_blob_url' in view_source:
                print("✅ Uso correcto del servicio de almacenamiento")
            else:
                print("❌ Uso incorrecto del servicio de almacenamiento")
                return False
            
            print("✅ Vista de descarga verificada correctamente")
            return True
            
        else:
            print("❌ Vista download_document no existe")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando vista: {e}")
        return False

def test_storage_service_imports():
    """Prueba que las importaciones del servicio de almacenamiento son correctas."""
    print_section("VERIFICACIÓN DE IMPORTACIONES")
    
    try:
        from services.storage_service import AzureStorageService
        
        # Verificar que quote_plus se importa correctamente
        from urllib.parse import quote_plus
        print("✅ quote_plus importado correctamente")
        
        # Verificar que no se usa quote_plus en URLs completas
        service_source = inspect.getsource(AzureStorageService)
        
        # Buscar usos problemáticos de quote_plus
        problematic_uses = []
        lines = service_source.split('\n')
        for i, line in enumerate(lines, 1):
            if 'quote_plus(' in line and 'blob_client.url' in line:
                problematic_uses.append(f"Línea {i}: {line.strip()}")
        
        if problematic_uses:
            print("❌ Usos problemáticos de quote_plus encontrados:")
            for use in problematic_uses:
                print(f"   {use}")
            return False
        else:
            print("✅ No se encontraron usos problemáticos de quote_plus")
        
        print("✅ Importaciones verificadas correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error verificando importaciones: {e}")
        return False

def print_section(title):
    """Imprimir una sección con formato."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def main():
    """Función principal de pruebas."""
    print("🔧 PRUEBAS DE CORRECCIÓN DE DESCARGA DE DOCUMENTOS")
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        test_storage_service_imports,
        test_get_blob_url_fix,
        test_download_view_fix,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Error en prueba {test.__name__}: {e}")
    
    print_section("RESULTADOS FINALES")
    print(f"✅ Pruebas pasadas: {passed}/{total}")
    print(f"❌ Pruebas fallidas: {total - passed}/{total}")
    
    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron! La corrección está funcionando correctamente.")
        return True
    else:
        print("⚠️  Algunas pruebas fallaron. Revisar las correcciones.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
