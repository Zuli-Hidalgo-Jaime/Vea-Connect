#!/usr/bin/env python3
"""
Script para validar la configuración de despliegue en Azure App Service
"""

import os
import sys
from pathlib import Path

def check_file_exists(file_path, description):
    """Verifica que un archivo existe"""
    if Path(file_path).exists():
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} - NO ENCONTRADO")
        return False

def check_requirements():
    """Verifica que requirements.txt contiene las dependencias necesarias"""
    if not check_file_exists('requirements.txt', 'requirements.txt'):
        return False
    
    # Verificar que los paquetes principales están presentes
    with open('requirements.txt', 'r') as f:
        content = f.read()
    
    # Verificar paquetes específicos
    checks = [
        ('Django', 'Django' in content),
        ('gunicorn', 'gunicorn' in content),
        ('python-dotenv', 'python-dotenv' in content),
        ('psycopg2-binary', 'psycopg2-binary' in content),
        ('azure-storage-blob', 'azure-storage-blob' in content)
    ]
    
    all_good = True
    for package, found in checks:
        if found:
            print(f"✅ {package} encontrado en requirements.txt")
        else:
            print(f"❌ {package} NO encontrado en requirements.txt")
            all_good = False
    
    return all_good

def check_startup_script():
    """Verifica el script de inicio"""
    if not check_file_exists('startup.sh', 'startup.sh'):
        return False
    
    with open('startup.sh', 'r') as f:
        content = f.read()
    
    required_elements = [
        ('#!/bin/bash', '#!/bin/bash' in content),
        ('gunicorn', 'gunicorn' in content),
        ('config.wsgi:application', 'config.wsgi:application' in content)
    ]
    
    all_good = True
    for element, found in required_elements:
        if found:
            print(f"✅ {element} encontrado en startup.sh")
        else:
            print(f"❌ {element} NO encontrado en startup.sh")
            all_good = False
    
    return all_good

def check_wsgi_config():
    """Verifica la configuración WSGI"""
    if not check_file_exists('config/wsgi.py', 'config/wsgi.py'):
        return False
    
    with open('config/wsgi.py', 'r') as f:
        content = f.read()
    
    if 'get_wsgi_application' in content and 'application' in content:
        print("✅ config/wsgi.py está configurado correctamente")
        return True
    else:
        print("❌ config/wsgi.py no está configurado correctamente")
        return False

def check_settings():
    """Verifica que los archivos de configuración existen"""
    settings_files = [
        'config/settings/__init__.py',
        'config/settings/base.py',
        'config/settings/production.py'
    ]
    
    all_exist = True
    for file_path in settings_files:
        if not check_file_exists(file_path, f'Archivo de configuración: {file_path}'):
            all_exist = False
    
    return all_exist

def main():
    """Función principal de validación"""
    print("🔍 VALIDANDO CONFIGURACIÓN DE DESPLIEGUE AZURE APP SERVICE")
    print("=" * 60)
    
    checks = [
        check_requirements(),
        check_startup_script(),
        check_wsgi_config(),
        check_settings()
    ]
    
    print("\n" + "=" * 60)
    if all(checks):
        print("🎉 TODAS LAS VALIDACIONES PASARON - El despliegue debería funcionar")
        print("\n📋 PRÓXIMOS PASOS:")
        print("1. Haz commit y push de estos cambios")
        print("2. En Azure App Service, configura las variables de entorno")
        print("3. Reinicia la aplicación")
    else:
        print("❌ HAY PROBLEMAS QUE NECESITAN SER CORREGIDOS")
        print("\n🔧 CORRECCIONES NECESARIAS:")
        print("- Verifica los archivos faltantes")
        print("- Asegúrate de que startup.sh tenga permisos de ejecución")
        print("- Confirma que requirements.txt contiene todas las dependencias")

if __name__ == "__main__":
    main() 