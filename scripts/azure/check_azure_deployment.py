#!/usr/bin/env python3
"""
Script de diagnóstico específico para problemas de despliegue en Azure.
Enfocado en resolver el error "ModuleNotFoundError: No module named 'config'"
"""

import os
import sys
import subprocess
import json

def run_command(command, description):
    """Execute a command and display the result."""
    print(f"\n=== {description} ===")
    print(f"Command: {command}")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        print(f"Exit code: {result.returncode}")
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"Error executing command: {e}")
        return False

def check_azure_environment():
    """Check the Azure environment."""
    print("=== AZURE ENVIRONMENT VERIFICATION ===")
    
    # Check Azure environment variables
    azure_vars = [
        'WEBSITE_HOSTNAME',
        'WEBSITE_SITE_NAME',
        'WEBSITE_INSTANCE_ID',
        'WEBSITE_OWNER_NAME',
        'WEBSITE_RESOURCE_GROUP',
        'WEBSITE_SKU',
        'WEBSITE_RUN_FROM_PACKAGE',
    ]
    
    for var in azure_vars:
        value = os.environ.get(var, 'NOT DEFINED')
        print(f"{var}: {value}")
    
    # Check working directory
    print(f"\nCurrent directory: {os.getcwd()}")
    print(f"Directory contents:")
    try:
        files = os.listdir('.')
        for file in sorted(files):
            if os.path.isdir(file):
                print(f"  [DIR] {file}/")
            else:
                print(f"  [FILE] {file}")
    except Exception as e:
        print(f"Error listing files: {e}")

def check_python_environment():
    """Check the Python environment."""
    print("\n=== PYTHON ENVIRONMENT VERIFICATION ===")
    
    # Check Python
    run_command("python3 --version", "Python 3 version")
    run_command("python --version", "Python version")
    
    # Check pip
    run_command("pip3 --version", "pip 3 version")
    run_command("pip --version", "pip version")
    
    # Check PYTHONPATH
    print(f"\nPYTHONPATH: {os.environ.get('PYTHONPATH', 'NOT DEFINED')}")
    print(f"sys.path: {sys.path}")

def check_django_installation():
    """Check Django installation."""
    print("\n=== DJANGO VERIFICATION ===")
    
    # Check Django installed
    run_command("python3 -c 'import django; print(f\"Django {django.get_version()}\")'", "Check Django")
    
    # Check gunicorn
    run_command("python3 -c 'import gunicorn; print(\"Gunicorn available\")'", "Check Gunicorn")

def check_project_structure():
    """Check project structure."""
    print("\n=== PROJECT STRUCTURE VERIFICATION ===")
    
    # Check critical files
    critical_files = [
        'manage.py',
        'requirements.txt',
        'config/__init__.py',
        'config/wsgi.py',
        'config/settings/__init__.py',
        'config/settings/production.py',
    ]
    
    for file_path in critical_files:
        if os.path.exists(file_path):
            print(f"[OK] {file_path}")
        else:
            print(f"[ERROR] {file_path} - NOT FOUND")
    
    # Check critical directories
    critical_dirs = [
        'config',
        'config/settings',
        'apps',
    ]
    
    for dir_path in critical_dirs:
        if os.path.isdir(dir_path):
            print(f"[OK] {dir_path}/")
        else:
            print(f"[ERROR] {dir_path}/ - NOT FOUND")

def test_module_imports():
    """Test critical module imports."""
    print("\n=== MODULE IMPORT TEST ===")
    
    # Add current directory to path
    current_dir = os.getcwd()
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
        print(f"Added {current_dir} to sys.path")
    
    # Test imports
    modules_to_test = [
        ('config', 'config module'),
        ('config.wsgi', 'config.wsgi module'),
        ('config.settings', 'config.settings module'),
        ('config.settings.production', 'config.settings.production module'),
    ]
    
    for module_name, description in modules_to_test:
        try:
            __import__(module_name)
            print(f"[OK] {description}: {module_name}")
        except ImportError as e:
            print(f"[ERROR] {description}: {module_name} - {e}")
        except Exception as e:
            print(f"[WARNING] {description}: {module_name} - {e}")

def test_django_commands():
    """Test Django commands."""
    print("\n=== DJANGO COMMANDS TEST ===")
    
    # Test check
    run_command("python3 manage.py check --settings=config.settings.production", "Django check")
    
    # Test showmigrations
    run_command("python3 manage.py showmigrations --settings=config.settings.production", "Show migrations")

def test_gunicorn():
    """Test gunicorn directly."""
    print("\n=== GUNICORN TEST ===")
    
    # Test WSGI application import
    test_script = """
import os
import sys

# Configure environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
sys.path.insert(0, os.getcwd())

try:
    from config.wsgi import application
    print("[OK] WSGI application imported correctly")
    print(f"Application type: {type(application)}")
except Exception as e:
    print(f"[ERROR] Error importing WSGI application: {e}")
"""
    
    with open('test_wsgi.py', 'w') as f:
        f.write(test_script)
    
    run_command("python3 test_wsgi.py", "WSGI import test")
    
    # Clean temporary file
    if os.path.exists('test_wsgi.py'):
        os.remove('test_wsgi.py')

def generate_startup_script():
    """Generate an improved startup script."""
    print("\n=== GENERATING IMPROVED STARTUP SCRIPT ===")
    
    startup_script = '''#!/bin/bash

# Script de startup mejorado para Azure App Service
set -e  # Salir en caso de error

echo "=== INICIANDO DESPLIEGUE EN AZURE APP SERVICE ==="
echo "Timestamp: $(date)"
echo "Directorio actual: $(pwd)"

# Navegar al directorio correcto
cd /home/site/wwwroot
echo "Navegado a: $(pwd)"

# Mostrar estructura del proyecto
echo "=== ESTRUCTURA DEL PROYECTO ==="
ls -la

# Configurar variables de entorno
export DJANGO_SETTINGS_MODULE=config.settings.production
export PYTHONPATH=/home/site/wwwroot
export PYTHONUNBUFFERED=1

echo "DJANGO_SETTINGS_MODULE: $DJANGO_SETTINGS_MODULE"
echo "PYTHONPATH: $PYTHONPATH"

# Activar entorno virtual si existe
if [ -d "/antenv" ]; then
    source /antenv/bin/activate
    echo "✅ Entorno virtual antenv activado"
elif [ -d "antenv" ]; then
    source antenv/bin/activate
    echo "✅ Entorno virtual antenv activado"
else
    echo "⚠️ No se encontró entorno virtual antenv"
fi

# Verificar Python
echo "=== VERIFICACIÓN DE PYTHON ==="
python3 --version || python --version

# Instalar dependencias
echo "=== INSTALACIÓN DE DEPENDENCIAS ==="
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

# Verificar módulos críticos
echo "=== VERIFICACIÓN DE MÓDULOS ==="
python3 -c "import django; print(f'✅ Django {django.get_version()}')"
python3 -c "import config; print('✅ Módulo config')"
python3 -c "import config.wsgi; print('✅ Módulo config.wsgi')"
python3 -c "import gunicorn; print('✅ Gunicorn')"

# Ejecutar migraciones
echo "=== MIGRACIONES ==="
python3 manage.py migrate --noinput --settings=config.settings.production

# Recolectar archivos estáticos
echo "=== ARCHIVOS ESTÁTICOS ==="
python3 manage.py collectstatic --noinput --settings=config.settings.production

# Iniciar aplicación
echo "=== INICIANDO APLICACIÓN ==="
echo "Comando: gunicorn config.wsgi:application --bind=0.0.0.0:8000 --timeout 600 --workers 4"
exec gunicorn config.wsgi:application --bind=0.0.0.0:8000 --timeout 600 --workers 4
'''
    
    with open('startup_improved.sh', 'w') as f:
        f.write(startup_script)
    
    print("[OK] Improved startup script generated: startup_improved.sh")
    print("You can use this script as an alternative to the current startup.sh")

def main():
    """Main diagnostic function."""
    print("COMPLETE DIAGNOSTIC FOR AZURE APP SERVICE")
    print("=" * 60)
    
    # Run all verifications
    check_azure_environment()
    check_python_environment()
    check_django_installation()
    check_project_structure()
    test_module_imports()
    test_django_commands()
    test_gunicorn()
    generate_startup_script()
    
    print("\n" + "=" * 60)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 60)
    print("1. If there are errors with the 'config' module, verify:")
    print("   - The 'config' directory exists in /home/site/wwwroot")
    print("   - The 'config/__init__.py' file exists")
    print("   - PYTHONPATH is configured correctly")
    print()
    print("2. Recommended solutions:")
    print("   - Use the generated startup_improved.sh script")
    print("   - Verify that all files are deployed correctly")
    print("   - Check Azure App Service logs")
    print()
    print("3. Useful debugging commands:")
    print("   python3 scripts/diagnostics/check_project_structure.py")
    print("   python3 manage.py check --settings=config.settings.production")
    print("   gunicorn config.wsgi:application --bind=0.0.0.0:8000")

if __name__ == "__main__":
    main() 