#!/usr/bin/env python3
"""
Script de diagnóstico rápido para error 500
Verifica configuración, dependencias y posibles causas
"""

import os
import sys
import django
from pathlib import Path

# Agregar el directorio raíz al path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

def check_django_version():
    """Verificar versión de Django y compatibilidad"""
    print("=== VERIFICACIÓN DE DJANGO ===")
    print(f"Django version: {django.get_version()}")
    
    # Verificar si es compatible
    django_version = django.VERSION
    if django_version[0] == 5 and django_version[1] == 0:
        print("✅ Django 5.0.x detectado - compatible")
    elif django_version[0] == 5 and django_version[1] == 2:
        print("⚠️  Django 5.2.x detectado - puede causar problemas")
    else:
        print(f"❌ Versión inesperada: {django_version}")
    
    return True

def check_settings():
    """Verificar configuración de Django"""
    print("\n=== VERIFICACIÓN DE CONFIGURACIÓN ===")
    
    # Configurar Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.azure_production')
    
    try:
        django.setup()
        print("✅ Django configurado correctamente")
        
        # Verificar configuración crítica
        from django.conf import settings
        
        print(f"DEBUG: {settings.DEBUG}")
        print(f"ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
        print(f"DATABASES: {settings.DATABASES['default']['ENGINE']}")
        
        # Verificar variables críticas
        critical_vars = [
            'AZURE_POSTGRESQL_NAME',
            'AZURE_POSTGRESQL_USERNAME', 
            'AZURE_POSTGRESQL_PASSWORD',
            'AZURE_POSTGRESQL_HOST'
        ]
        
        for var in critical_vars:
            value = os.environ.get(var)
            if value:
                print(f"✅ {var}: {'*' * len(value)}")
            else:
                print(f"❌ {var}: NO CONFIGURADA")
                
        return True
        
    except Exception as e:
        print(f"❌ Error configurando Django: {e}")
        return False

def check_imports():
    """Verificar imports críticos"""
    print("\n=== VERIFICACIÓN DE IMPORTS ===")
    
    try:
        from apps.core.models import CustomUser
        print("✅ CustomUser importado correctamente")
    except Exception as e:
        print(f"❌ Error importando CustomUser: {e}")
    
    try:
        from apps.documents.models import Document
        print("✅ Document importado correctamente")
    except Exception as e:
        print(f"❌ Error importando Document: {e}")
    
    try:
        from services.storage_service import AzureStorageService
        print("✅ AzureStorageService importado correctamente")
    except Exception as e:
        print(f"❌ Error importando AzureStorageService: {e}")
    
    return True

def check_migrations():
    """Verificar estado de migraciones"""
    print("\n=== VERIFICACIÓN DE MIGRACIONES ===")
    
    try:
        from django.core.management import execute_from_command_line
        from django.db import connection
        
        # Verificar conexión a BD
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"✅ Conexión a BD: {version[0]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verificando migraciones: {e}")
        return False

def main():
    """Función principal"""
    print("🔍 DIAGNÓSTICO DE ERROR 500")
    print("=" * 50)
    
    checks = [
        check_django_version,
        check_settings,
        check_imports,
        check_migrations
    ]
    
    results = []
    for check in checks:
        try:
            result = check()
            results.append(result)
        except Exception as e:
            print(f"❌ Error en check: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 RESUMEN")
    
    if all(results):
        print("✅ Todos los checks pasaron - el problema puede ser temporal")
        print("💡 Sugerencias:")
        print("   - Revisar logs de Azure App Service")
        print("   - Verificar si hay problemas de red")
        print("   - Comprobar si el servicio está sobrecargado")
    else:
        print("❌ Se encontraron problemas de configuración")
        print("💡 Acciones recomendadas:")
        print("   - Revisar variables de entorno en Azure")
        print("   - Verificar configuración de base de datos")
        print("   - Comprobar compatibilidad de versiones")

if __name__ == "__main__":
    main()
