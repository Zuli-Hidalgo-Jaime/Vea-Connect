#!/usr/bin/env python3
"""
Script para verificar la corrección del servicio de almacenamiento de Azure.
Usado en el flujo de trabajo de GitHub Actions para validar que la corrección funciona.
"""

import os
import sys
import django

def main():
    """Verificar que la corrección del servicio de almacenamiento funciona correctamente."""
    print("=== Verificando corrección del servicio de almacenamiento ===")
    
    try:
        # Configurar Django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.azure_production')
        django.setup()
        
        # Verificar que el servicio de almacenamiento se puede importar
        from services.storage_service import AzureStorageService
        print('✅ AzureStorageService importado correctamente')
        
        # Verificar que ContentSettings está disponible
        from azure.storage.blob import ContentSettings
        print('✅ ContentSettings importado correctamente')
        
        # Crear instancia del servicio (sin conectar)
        service = AzureStorageService()
        print('✅ AzureStorageService instanciado correctamente')
        
        # Verificar que las dependencias de Azure están en las versiones correctas
        import azure.core
        import azure.storage.blob
        
        print(f'✅ azure-core versión: {azure.core.__version__}')
        print(f'✅ azure-storage-blob versión: {azure.storage.blob.__version__}')
        
        # Verificar que azure-core es >= 1.35.0
        from packaging import version
        core_version = version.parse(azure.core.__version__)
        min_version = version.parse("1.35.0")
        
        if core_version >= min_version:
            print('✅ azure-core está en una versión compatible (>= 1.35.0)')
        else:
            print(f'❌ azure-core versión {azure.core.__version__} es menor que 1.35.0')
            sys.exit(1)
        
        print('✅ Verificación completada - el servicio está listo')
        return 0
        
    except Exception as e:
        print(f'❌ Error durante la verificación: {e}')
        return 1

if __name__ == "__main__":
    sys.exit(main())
