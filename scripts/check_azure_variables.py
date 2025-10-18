#!/usr/bin/env python
"""
Script simple para verificar las variables de Azure Storage
"""
import os
import sys
from pathlib import Path

# Agregar el directorio del proyecto al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

import django
django.setup()

from django.conf import settings

def check_azure_variables():
    """Verifica las variables de Azure Storage"""
    print("🔍 Verificando variables de Azure Storage...")
    print("-" * 50)
    
    # Variables principales
    variables = [
        ('AZURE_STORAGE_ACCOUNT_NAME', settings.AZURE_STORAGE_ACCOUNT_NAME),
        ('AZURE_STORAGE_ACCOUNT_KEY', settings.AZURE_STORAGE_ACCOUNT_KEY),
        ('AZURE_ACCOUNT_NAME', settings.AZURE_ACCOUNT_NAME),
        ('AZURE_ACCOUNT_KEY', settings.AZURE_ACCOUNT_KEY),
        ('AZURE_CONTAINER', settings.AZURE_CONTAINER),
        ('AZURE_STORAGE_CONNECTION_STRING', settings.AZURE_STORAGE_CONNECTION_STRING),
    ]
    
    # Variables de fallback
    fallback_variables = [
        ('BLOB_ACCOUNT_NAME', settings.BLOB_ACCOUNT_NAME),
        ('BLOB_ACCOUNT_KEY', settings.BLOB_ACCOUNT_KEY),
        ('BLOB_CONTAINER_NAME', settings.BLOB_CONTAINER_NAME),
    ]
    
    print("📋 Variables principales:")
    for name, value in variables:
        if value:
            print(f"  ✅ {name}: {value[:20]}..." if len(str(value)) > 20 else f"  ✅ {name}: {value}")
        else:
            print(f"  ❌ {name}: No configurada")
    
    print("\n📋 Variables de fallback:")
    for name, value in fallback_variables:
        if value:
            print(f"  ✅ {name}: {value[:20]}..." if len(str(value)) > 20 else f"  ✅ {name}: {value}")
        else:
            print(f"  ❌ {name}: No configurada")
    
    # Verificar configuración del servicio
    print("\n🔧 Verificando servicio de almacenamiento...")
    try:
        from services.storage_service import DocumentStorageService
        service = DocumentStorageService()
        print(f"  ✅ Servicio configurado correctamente")
        print(f"  📦 Contenedor: {service.container_name}")
        print(f"  🏦 Cuenta: {service.account_name}")
    except Exception as e:
        print(f"  ❌ Error en servicio: {str(e)}")

if __name__ == "__main__":
    check_azure_variables()
