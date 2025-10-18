#!/usr/bin/env python3
"""
Script de prueba para verificar la corrección del error de ContentSettings
en el servicio de almacenamiento de Azure.
"""

import os
import sys
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_storage_service():
    """Prueba el servicio de almacenamiento corregido."""
    try:
        from services.storage_service import AzureStorageService
        
        # Inicializar el servicio
        storage_service = AzureStorageService()
        
        if not storage_service.client:
            logger.error("❌ No se pudo inicializar el cliente de Azure Storage")
            return False
        
        logger.info("✅ Cliente de Azure Storage inicializado correctamente")
        
        # Crear datos de prueba
        test_data = "Este es un archivo de prueba para verificar la correccion del error de ContentSettings".encode('utf-8')
        test_blob_name = f"test_content_disposition_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        # Probar upload_data con content_disposition
        logger.info(f"📤 Probando upload_data con blob: {test_blob_name}")
        
        result = storage_service.upload_data(
            data=test_data,
            blob_name=test_blob_name,
            content_type="text/plain",
            category="test"
        )
        
        if result['success']:
            logger.info("✅ Upload de datos exitoso")
            logger.info(f"   - Blob URL: {result['blob_url']}")
            logger.info(f"   - Tamaño: {result['size']} bytes")
            
            # Verificar que el blob existe
            blob_client = storage_service.client.get_blob_client(
                container=storage_service.container_name,
                blob=result['blob_name']
            )
            
            try:
                properties = blob_client.get_blob_properties()
                logger.info("✅ Blob creado correctamente")
                logger.info(f"   - Content-Type: {properties.content_settings.content_type}")
                logger.info(f"   - Content-Disposition: {properties.content_settings.content_disposition}")
                
                # Limpiar - eliminar el blob de prueba
                blob_client.delete_blob()
                logger.info("🧹 Blob de prueba eliminado")
                
                return True
                
            except Exception as e:
                logger.error(f"❌ Error al verificar propiedades del blob: {e}")
                return False
        else:
            logger.error(f"❌ Error en upload_data: {result['error']}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error en la prueba: {e}")
        return False

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

def main():
    """Función principal de prueba."""
    logger.info("🚀 Iniciando pruebas de corrección del servicio de almacenamiento")
    
    # Prueba 1: Importación de ContentSettings
    logger.info("\n📋 Prueba 1: Importación de ContentSettings")
    if not test_content_settings_import():
        logger.error("❌ Falló la prueba de importación de ContentSettings")
        return False
    
    # Prueba 2: Servicio de almacenamiento
    logger.info("\n📋 Prueba 2: Servicio de almacenamiento")
    if not test_storage_service():
        logger.error("❌ Falló la prueba del servicio de almacenamiento")
        return False
    
    logger.info("\n🎉 Todas las pruebas pasaron exitosamente")
    logger.info("✅ La corrección del error de ContentSettings está funcionando correctamente")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
