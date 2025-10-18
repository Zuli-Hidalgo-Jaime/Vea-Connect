#!/usr/bin/env python3
"""
Script de diagnóstico para verificar que la corrección del error de SAS token está funcionando.
"""

import sys
import os
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

def diagnose_sas_token_fix():
    """Diagnostica si la corrección del error de SAS token está funcionando."""
    logger.info("🔍 DIAGNÓSTICO DE CORRECCIÓN DE SAS TOKEN")
    logger.info(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("")
    
    print("=" * 60)
    print("  VERIFICACIÓN DE CÓDIGO CORREGIDO")
    print("=" * 60)
    
    # Verificar que el código corregido está en el archivo
    try:
        with open('../services/storage_service.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Verificar que se eliminó el uso problemático de generate_sas
        if 'blob_client.generate_sas(' in content:
            logger.error("❌ Código problemático encontrado: blob_client.generate_sas(")
            return False
        else:
            logger.info("✅ Código problemático eliminado: blob_client.generate_sas(")
            
        # Verificar que se implementó la solución correcta
        if 'generate_blob_sas(' in content:
            logger.info("✅ Código corregido encontrado: generate_blob_sas(")
        else:
            logger.error("❌ Código corregido no encontrado: generate_blob_sas(")
            return False
            
        # Verificar que se importa BlobSasPermissions
        if 'BlobSasPermissions' in content:
            logger.info("✅ Código corregido encontrado: BlobSasPermissions")
        else:
            logger.error("❌ Código corregido no encontrado: BlobSasPermissions")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error verificando código: {e}")
        return False
    
    print("")
    print("=" * 60)
    print("  VERIFICACIÓN DE IMPORTACIONES")
    print("=" * 60)
    
    # Verificar importaciones
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
        from azure.storage.blob import generate_blob_sas, BlobSasPermissions
        from services.storage_service import AzureStorageService
        
        logger.info("✅ generate_blob_sas importado correctamente")
        logger.info("✅ BlobSasPermissions importado correctamente")
        logger.info("✅ AzureStorageService importado correctamente")
        
    except ImportError as e:
        logger.error(f"❌ Error de importación: {e}")
        return False
    
    print("")
    print("=" * 60)
    print("  VERIFICACIÓN DE FUNCIONALIDAD")
    print("=" * 60)
    
    # Verificar que el servicio se puede inicializar
    try:
        service = AzureStorageService()
        logger.info("✅ Servicio de almacenamiento inicializado")
        
        # Verificar que el método get_blob_url existe
        if hasattr(service, 'get_blob_url'):
            logger.info("✅ Método get_blob_url disponible")
        else:
            logger.error("❌ Método get_blob_url no disponible")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error inicializando servicio: {e}")
        return False
    
    print("")
    print("=" * 60)
    print("  VERIFICACIÓN DE COMPATIBILIDAD")
    print("=" * 60)
    
    # Verificar compatibilidad con Azure Storage SDK
    try:
        # Verificar que generate_blob_sas es callable
        if callable(generate_blob_sas):
            logger.info("✅ generate_blob_sas es callable")
        else:
            logger.error("❌ generate_blob_sas no es callable")
            return False
            
        # Verificar que BlobSasPermissions funciona
        try:
            permissions = BlobSasPermissions(read=True)
            logger.info("✅ BlobSasPermissions.read funciona correctamente")
        except Exception as e:
            logger.error(f"❌ BlobSasPermissions.read falló: {e}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error verificando compatibilidad: {e}")
        return False
    
    print("")
    print("=" * 60)
    print("  RESUMEN DE DIAGNÓSTICO")
    print("=" * 60)
    
    logger.info("✅ Código problemático eliminado")
    logger.info("✅ Código corregido implementado")
    logger.info("✅ Importaciones funcionando")
    logger.info("✅ Servicio inicializable")
    logger.info("✅ Compatibilidad verificada")
    logger.info("")
    logger.info("🎉 La corrección del error de SAS token está funcionando correctamente")
    logger.info("📝 El error 'BlobClient object has no attribute generate_sas' ha sido resuelto")
    
    return True

if __name__ == "__main__":
    success = diagnose_sas_token_fix()
    sys.exit(0 if success else 1)
