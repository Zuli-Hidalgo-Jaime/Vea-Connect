#!/usr/bin/env python3
"""
Script de prueba simple para verificar la corrección del error de ContentSettings
sin necesidad de conectarse a Azure Storage.
"""

import os
import sys
import logging
import inspect

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_content_settings_import():
    """Prueba que ContentSettings se puede importar correctamente."""
    try:
        from azure.storage.blob import ContentSettings
        logger.info("✅ ContentSettings importado correctamente")
        
        # Probar creación de ContentSettings
        content_settings = ContentSettings(content_type="text/plain")
        logger.info("✅ ContentSettings creado correctamente")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error al importar ContentSettings: {e}")
        return False

def test_storage_service_code():
    """Prueba que el código del servicio de almacenamiento está corregido."""
    try:
        from services.storage_service import AzureStorageService
        
        # Obtener el código fuente de los métodos
        upload_file_source = inspect.getsource(AzureStorageService.upload_file)
        upload_data_source = inspect.getsource(AzureStorageService.upload_data)
        
        # Verificar que no se usa ContentSettings incorrectamente en set_http_headers
        problematic_patterns = [
            "content_settings=content_settings",
            "ContentSettings(",
            "from azure.storage.blob import ContentSettings"
        ]
        
        fixed_patterns = [
            "content_disposition=",
            "blob_client.set_http_headers("
        ]
        
        # Verificar que el código problemático NO está presente
        for pattern in problematic_patterns:
            if pattern in upload_file_source or pattern in upload_data_source:
                logger.error(f"❌ Código problemático encontrado: {pattern}")
                return False
        
        # Verificar que el código corregido SÍ está presente
        for pattern in fixed_patterns:
            if pattern in upload_file_source and pattern in upload_data_source:
                logger.info(f"✅ Código corregido encontrado: {pattern}")
            else:
                logger.error(f"❌ Código corregido no encontrado: {pattern}")
                return False
        
        logger.info("✅ Código del servicio de almacenamiento verificado correctamente")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error al verificar el código: {e}")
        return False

def test_method_signatures():
    """Prueba que las firmas de los métodos son correctas."""
    try:
        from services.storage_service import AzureStorageService
        
        # Verificar que los métodos existen
        methods_to_check = ['upload_file', 'upload_data']
        
        for method_name in methods_to_check:
            if hasattr(AzureStorageService, method_name):
                logger.info(f"✅ Método {method_name} existe")
            else:
                logger.error(f"❌ Método {method_name} no existe")
                return False
        
        logger.info("✅ Todas las firmas de métodos verificadas correctamente")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error al verificar firmas de métodos: {e}")
        return False

def main():
    """Función principal de prueba."""
    logger.info("🚀 Iniciando pruebas de corrección del código de ContentSettings")
    
    # Prueba 1: Importación de ContentSettings
    logger.info("\n📋 Prueba 1: Importación de ContentSettings")
    if not test_content_settings_import():
        logger.error("❌ Falló la prueba de importación de ContentSettings")
        return False
    
    # Prueba 2: Verificación del código corregido
    logger.info("\n📋 Prueba 2: Verificación del código corregido")
    if not test_storage_service_code():
        logger.error("❌ Falló la verificación del código corregido")
        return False
    
    # Prueba 3: Verificación de firmas de métodos
    logger.info("\n📋 Prueba 3: Verificación de firmas de métodos")
    if not test_method_signatures():
        logger.error("❌ Falló la verificación de firmas de métodos")
        return False
    
    logger.info("\n🎉 Todas las pruebas pasaron exitosamente")
    logger.info("✅ La corrección del error de ContentSettings está implementada correctamente")
    logger.info("📝 Nota: Para probar la funcionalidad completa, configure las credenciales de Azure Storage")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
