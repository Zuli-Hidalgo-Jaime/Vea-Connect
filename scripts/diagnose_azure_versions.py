#!/usr/bin/env python3
"""
Script para diagnosticar versiones de bibliotecas de Azure y detectar conflictos.
"""

import sys
import pkg_resources
import importlib

def check_azure_versions():
    """Verificar versiones de bibliotecas de Azure."""
    print("=== DIAGNÓSTICO DE VERSIONES DE AZURE ===\n")
    
    # Lista de bibliotecas de Azure a verificar
    azure_packages = [
        'azure-core',
        'azure-storage-blob',
        'azure-identity',
        'azure-common',
        'requests',
        'urllib3'
    ]
    
    print("Versiones instaladas:")
    print("-" * 50)
    
    for package in azure_packages:
        try:
            version = pkg_resources.get_distribution(package).version
            print(f"{package:<20} {version}")
        except pkg_resources.DistributionNotFound:
            print(f"{package:<20} NO INSTALADO")
        except Exception as e:
            print(f"{package:<20} ERROR: {e}")
    
    print("\n=== VERIFICACIÓN DE COMPATIBILIDAD ===")
    
    # Verificar si las versiones son compatibles
    try:
        import azure.core
        import azure.storage.blob
        import requests
        
        print("✓ Todas las bibliotecas principales están disponibles")
        
        # Verificar versión específica de azure-core
        core_version = pkg_resources.get_distribution('azure-core').version
        if core_version.startswith('1.35'):
            print("✓ azure-core 1.35.x es compatible")
        else:
            print(f"⚠ azure-core {core_version} puede tener problemas de compatibilidad")
        
        # Verificar versión de requests
        requests_version = pkg_resources.get_distribution('requests').version
        if requests_version.startswith('2.31'):
            print("✓ requests 2.31.x es compatible")
        else:
            print(f"⚠ requests {requests_version} puede tener problemas de compatibilidad")
            
    except ImportError as e:
        print(f"✗ Error al importar bibliotecas: {e}")
    
    print("\n=== PRUEBA DE FUNCIONALIDAD ===")
    
    try:
        from azure.storage.blob import ContentSettings, BlobServiceClient
        print("✓ ContentSettings y BlobServiceClient importados correctamente")
        
        # Probar creación de ContentSettings
        content_settings = ContentSettings(content_disposition='attachment; filename="test.txt"')
        print("✓ ContentSettings creado correctamente")
        
    except Exception as e:
        print(f"✗ Error al probar funcionalidad: {e}")

def check_storage_service():
    """Verificar que el servicio de almacenamiento funciona correctamente."""
    print("\n=== PRUEBA DEL SERVICIO DE ALMACENAMIENTO ===")
    
    try:
        from services.storage_service import AzureStorageService
        
        service = AzureStorageService()
        status = service.get_configuration_status()
        
        print(f"Estado del servicio: {status.get('status', 'unknown')}")
        if status.get('status') == 'configured':
            print("✓ Servicio de almacenamiento configurado correctamente")
        else:
            print(f"⚠ Servicio no configurado: {status.get('message', 'unknown error')}")
            
    except Exception as e:
        print(f"✗ Error al verificar servicio de almacenamiento: {e}")

if __name__ == "__main__":
    check_azure_versions()
    check_storage_service()
    
    print("\n=== RECOMENDACIONES ===")
    print("1. Si hay conflictos de versiones, actualiza requirements.txt")
    print("2. Asegúrate de que azure-core >= 1.35.0")
    print("3. Verifica que requests >= 2.31.0")
    print("4. Si persisten los problemas, considera usar ContentSettings en lugar de parámetros directos")
