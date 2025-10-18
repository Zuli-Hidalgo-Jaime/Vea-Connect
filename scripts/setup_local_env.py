#!/usr/bin/env python3
"""
Script para configurar el entorno local de desarrollo
"""

import os
import sys
from pathlib import Path

def setup_local_environment():
    """Configura las variables de entorno necesarias para desarrollo local"""
    
    # Variables de entorno básicas para desarrollo
    env_vars = {
        'DJANGO_SETTINGS_MODULE': 'config.settings.base',
        'DEBUG': 'True',
        'SECRET_KEY': 'django-insecure-dev-secret-key-change-in-production',
        'ALLOWED_HOSTS': 'localhost,127.0.0.1',
        'DATABASE_URL': 'sqlite:///db.sqlite3',
        'CONFIG_ADAPTER_ENABLED': 'False',
        'CACHE_LAYER_ENABLED': 'False',
        'CANARY_INGEST_ENABLED': 'False',
    }
    
    # Configurar variables de entorno
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"✓ Configurado {key} = {value}")
    
    print("\n✅ Entorno local configurado correctamente")
    print("📝 Nota: Para usar servicios de Azure, configura las variables correspondientes")
    
    return True

if __name__ == "__main__":
    setup_local_environment()
