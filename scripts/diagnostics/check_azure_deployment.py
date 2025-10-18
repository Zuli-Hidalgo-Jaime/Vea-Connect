#!/usr/bin/env python3
"""
Script de diagnóstico para verificar la configuración de despliegue en Azure
"""

import os
import sys
import subprocess
from pathlib import Path

def check_file_exists(filepath, description):
    """Verifica si un archivo existe"""
    if Path(filepath).exists():
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description}: {filepath} - NO ENCONTRADO")
        return False

def check_python_packages():
    """Verifica que los paquetes Python necesarios estén instalados"""
    required_packages = [
        ('django', 'django'),
        ('gunicorn', 'gunicorn'),
        ('python-dotenv', 'dotenv'),
        ('psycopg2', 'psycopg2'),
        ('azure-storage-blob', 'azure.storage.blob')
    ]
    
    print("\n🔍 Verificando paquetes Python...")
    missing_packages = []
    
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"✅ {package_name}")
        except ImportError:
            print(f"❌ {package_name} - NO INSTALADO")
            missing_packages.append(package_name)
    
    return len(missing_packages) == 0

def check_django_config():
    """Verifica la configuración de Django"""
    print("\n🔍 Verificando configuración de Django...")
    
    try:
        # Agregar el directorio actual al path
        sys.path.insert(0, os.getcwd())
        
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
        from django.conf import settings
        from django.core.management import execute_from_command_line
        
        print("✅ Django se puede importar correctamente")
        print(f"✅ Settings module: {settings.SETTINGS_MODULE}")
        print(f"✅ DEBUG: {settings.DEBUG}")
        print(f"✅ ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
        
        return True
    except Exception as e:
        print(f"❌ Error en configuración de Django: {e}")
        return False

def check_azure_environment():
    """Verifica variables de entorno de Azure (solo informativo en desarrollo local)"""
    print("\n🔍 Verificando variables de entorno de Azure...")
    
    azure_vars = [
        'WEBSITE_HOSTNAME',
        'AZURE_POSTGRESQL_HOST',
        'AZURE_STORAGE_CONNECTION_STRING',
        'AZURE_OPENAI_ENDPOINT'
    ]
    
    print("ℹ️  Variables de Azure (solo necesarias en producción):")
    for var in azure_vars:
        if os.environ.get(var):
            print(f"✅ {var}: Configurado")
        else:
            print(f"ℹ️  {var}: No configurado (normal en desarrollo local)")
    
    # En desarrollo local, no es un error que estas variables no estén
    return True

def main():
    """Función principal de diagnóstico"""
    print("🚀 Diagnóstico de configuración para Azure App Service")
    print("=" * 60)
    
    # Verificar archivos críticos
    critical_files = [
        ('manage.py', 'Archivo principal de Django'),
        ('requirements.txt', 'Dependencias de Python'),
        ('startup.sh', 'Script de inicio'),
        ('config/wsgi.py', 'Configuración WSGI'),
        ('config/settings/production.py', 'Configuración de producción'),
        ('web.config', 'Configuración de Azure'),
    ]
    
    print("\n📁 Verificando archivos críticos...")
    all_files_present = True
    for filepath, description in critical_files:
        if not check_file_exists(filepath, description):
            all_files_present = False
    
    # Verificar paquetes Python
    packages_ok = check_python_packages()
    
    # Verificar configuración de Django
    django_ok = check_django_config()
    
    # Verificar entorno de Azure (solo informativo)
    azure_ok = check_azure_environment()
    
    # Resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN DEL DIAGNÓSTICO")
    print("=" * 60)
    
    print(f"Archivos críticos: {'✅ OK' if all_files_present else '❌ PROBLEMAS'}")
    print(f"Paquetes Python: {'✅ OK' if packages_ok else '❌ PROBLEMAS'}")
    print(f"Configuración Django: {'✅ OK' if django_ok else '❌ PROBLEMAS'}")
    print(f"Variables Azure: {'ℹ️  INFORMATIVO' if azure_ok else '⚠️  PROBLEMAS'}")
    
    if all_files_present and packages_ok and django_ok:
        print("\n🎉 ¡Configuración lista para despliegue!")
        print("📝 Nota: Las variables de entorno de Azure se configurarán en producción.")
        return 0
    else:
        print("\n⚠️ Se encontraron problemas que deben resolverse antes del despliegue.")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 