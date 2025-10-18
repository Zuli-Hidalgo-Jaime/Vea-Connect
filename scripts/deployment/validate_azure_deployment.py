#!/usr/bin/env python3
"""
Script para validar la configuración específica de Azure App Service
"""

import os
import sys
from pathlib import Path

def check_azure_files():
    """Verifica que los archivos necesarios para Azure estén presentes"""
    required_files = [
        ('startup_azure.sh', 'Script de startup para Azure'),
        ('startup.sh', 'Script de startup original'),
        ('startup.txt', 'Comando de startup para Azure'),
        ('.deployment', 'Configuración de despliegue'),
        ('requirements.txt', 'Dependencias de Python'),
        ('runtime.txt', 'Versión de Python'),
        ('config/wsgi.py', 'Configuración WSGI'),
        ('config/settings/production.py', 'Configuración de producción')
    ]
    
    all_good = True
    for file_path, description in required_files:
        if Path(file_path).exists():
            print(f"✅ {description}: {file_path}")
        else:
            print(f"❌ {description}: {file_path} - NO ENCONTRADO")
            all_good = False
    
    return all_good

def check_startup_scripts():
    """Verifica que los scripts de startup estén configurados correctamente"""
    scripts = [
        ('startup_azure.sh', 'Script específico para Azure'),
        ('startup.sh', 'Script original')
    ]
    
    all_good = True
    for script_path, description in scripts:
        if not Path(script_path).exists():
            print(f"❌ {description}: {script_path} - NO ENCONTRADO")
            all_good = False
            continue
            
        with open(script_path, 'r') as f:
            content = f.read()
        
        required_elements = [
            ('#!/bin/bash', 'Shebang'),
            ('gunicorn', 'Gunicorn'),
            ('config.wsgi:application', 'WSGI application')
        ]
        
        for element, desc in required_elements:
            if element in content:
                print(f"✅ {description} - {desc}: encontrado")
            else:
                print(f"❌ {description} - {desc}: NO encontrado")
                all_good = False
    
    return all_good

def check_requirements():
    """Verifica que requirements.txt contenga las dependencias necesarias"""
    if not Path('requirements.txt').exists():
        print("❌ requirements.txt no encontrado")
        return False
    
    with open('requirements.txt', 'r') as f:
        content = f.read()
    
    required_packages = [
        ('Django', 'Django framework'),
        ('gunicorn', 'Servidor WSGI'),
        ('python-dotenv', 'Variables de entorno'),
        ('psycopg2-binary', 'PostgreSQL adapter'),
        ('azure-storage-blob', 'Azure Storage')
    ]
    
    all_good = True
    for package, description in required_packages:
        if package in content:
            print(f"✅ {description}: {package}")
        else:
            print(f"❌ {description}: {package} - NO encontrado")
            all_good = False
    
    return all_good

def check_azure_config():
    """Verifica la configuración específica de Azure"""
    print("\n🔧 CONFIGURACIÓN AZURE APP SERVICE:")
    
    # Verificar startup.txt
    if Path('startup.txt').exists():
        with open('startup.txt', 'r') as f:
            startup_cmd = f.read().strip()
        print(f"✅ Comando de startup: {startup_cmd}")
    else:
        print("❌ startup.txt no encontrado")
    
    # Verificar .deployment
    if Path('.deployment').exists():
        with open('.deployment', 'r') as f:
            deployment_config = f.read().strip()
        print(f"✅ Configuración de despliegue: {deployment_config}")
    else:
        print("❌ .deployment no encontrado")
    
    # Verificar runtime.txt
    if Path('runtime.txt').exists():
        with open('runtime.txt', 'r') as f:
            runtime = f.read().strip()
        print(f"✅ Runtime de Python: {runtime}")
    else:
        print("❌ runtime.txt no encontrado")
    
    return True

def main():
    """Función principal de validación"""
    print("🔍 VALIDANDO CONFIGURACIÓN AZURE APP SERVICE")
    print("=" * 60)
    
    checks = [
        check_azure_files(),
        check_startup_scripts(),
        check_requirements(),
        check_azure_config()
    ]
    
    print("\n" + "=" * 60)
    if all(checks):
        print("🎉 CONFIGURACIÓN AZURE COMPLETA - Listo para despliegue")
        print("\n📋 PRÓXIMOS PASOS:")
        print("1. Haz commit y push de estos cambios")
        print("2. En Azure App Service, configura las variables de entorno")
        print("3. Reinicia la aplicación")
        print("4. Monitorea los logs para confirmar funcionamiento")
    else:
        print("❌ HAY PROBLEMAS QUE NECESITAN SER CORREGIDOS")
        print("\n🔧 CORRECCIONES NECESARIAS:")
        print("- Verifica los archivos faltantes")
        print("- Asegúrate de que los scripts tengan permisos de ejecución")
        print("- Confirma que requirements.txt contiene todas las dependencias")

if __name__ == "__main__":
    main() 