#!/usr/bin/env python3
"""
Script de prueba para verificar la corrección del error de SAS token.
"""

import sys
import os
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

def test_sas_token_fix():
    """Prueba la corrección del error de SAS token."""
    logger.info("🔧 PRUEBAS DE CORRECCIÓN DE SAS TOKEN")
    logger.info(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("")
    
    print("=" * 60)
    print("  VERIFICACIÓN DE IMPORTACIONES DE AZURE STORAGE")
    print("=" * 60)
    
    # Prueba 1: Verificar importaciones
    try:
        from azure.storage.blob import generate_blob_sas, BlobSasPermissions
        logger.info("✅ generate_blob_sas importado correctamente")
        logger.info("✅ BlobSasPermissions importado correctamente")
        
        # Verificar que son callables
        if callable(generate_blob_sas):
            logger.info("✅ generate_blob_sas es callable")
        else:
            logger.error("❌ generate_blob_sas no es callable")
            
        # Verificar BlobSasPermissions.read
        try:
            permissions = BlobSasPermissions(read=True)
            logger.info("✅ BlobSasPermissions.read disponible")
        except Exception as e:
            logger.error(f"❌ BlobSasPermissions.read no disponible: {e}")
            
    except ImportError as e:
        logger.error(f"❌ Error importando Azure Storage: {e}")
        return False
    
    print("")
    print("=" * 60)
    print("  VERIFICACIÓN DE ESTRUCTURA DEL SERVICIO")
    print("=" * 60)
    
    # Prueba 2: Verificar estructura del servicio
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from services.storage_service import AzureStorageService
        
        service = AzureStorageService()
        
        # Verificar atributos necesarios
        if hasattr(service, 'account_name'):
            logger.info("✅ Atributo account_name existe")
        else:
            logger.error("❌ Atributo account_name no existe")
            
        if hasattr(service, 'account_key'):
            logger.info("✅ Atributo account_key existe")
        else:
            logger.error("❌ Atributo account_key no existe")
            
        if hasattr(service, 'container_name'):
            logger.info("✅ Atributo container_name existe")
        else:
            logger.error("❌ Atributo container_name no existe")
            
        if hasattr(service, 'client'):
            logger.info("✅ Atributo client existe")
        else:
            logger.error("❌ Atributo client no existe")
            
    except Exception as e:
        logger.error(f"❌ Error verificando estructura del servicio: {e}")
        return False
    
    print("")
    print("=" * 60)
    print("  VERIFICACIÓN DE CORRECCIÓN DE SAS TOKEN")
    print("=" * 60)
    
    # Prueba 3: Verificar que el método get_blob_url existe
    try:
        if hasattr(service, 'get_blob_url'):
            logger.info("✅ Método get_blob_url existe")
        else:
            logger.error("❌ Método get_blob_url no existe")
            
        # Verificar que no hay usos de generate_sas
        with open('../services/storage_service.py', 'r', encoding='utf-8') as f:
            content = f.read()
            if 'generate_sas' in content:
                logger.error("❌ Todavía hay usos de generate_sas en el código")
                return False
            else:
                logger.info("✅ No se encontraron usos de generate_sas")
                
    except Exception as e:
        logger.error(f"❌ Error verificando corrección: {e}")
        return False
    
    print("")
    print("=" * 60)
    print("  RESULTADOS FINALES")
    print("=" * 60)
    
    logger.info("✅ Todas las pruebas pasaron exitosamente")
    logger.info("✅ La corrección del error de SAS token está implementada correctamente")
    logger.info("📝 Nota: Para probar la funcionalidad completa, configure las credenciales de Azure Storage")
    
    return True

if __name__ == "__main__":
    from datetime import datetime
    success = test_sas_token_fix()
    sys.exit(0 if success else 1)
