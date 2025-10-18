#!/usr/bin/env python
"""
Script de verificación pre-despliegue para VEA WebApp
Verifica que todo esté listo para el despliegue en Azure
"""
import os
import sys
import subprocess
import importlib
from pathlib import Path

# Agregar el directorio raíz del proyecto al PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def check_python_version():
    """Verifica la versión de Python"""
    print("Verificando versión de Python...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"ERROR: Se requiere Python 3.8+ (actual: {version.major}.{version.minor})")
        return False
    print(f"OK: Python {version.major}.{version.minor}.{version.micro} - OK")
    return True

def check_django_installation():
    """Verifica la instalación de Django"""
    print("Verificando instalación de Django...")
    try:
        import django
        print(f"OK: Django {django.get_version()} - OK")
        return True
    except ImportError:
        print("ERROR: Django no está instalado")
        return False

def check_dependencies():
    """Verifica las dependencias del proyecto"""
    print("Verificando dependencias...")
    required_packages = [
        ('django', 'django'),
        ('azure_storage_blob', 'azure.storage.blob'),
        # ('storages', 'storages'),  # Eliminado - no usar django-storages para archivos estáticos/media
        ('pytest', 'pytest'),
        ('pytest_django', 'pytest_django')
    ]
    
    missing_packages = []
    for package_name, import_name in required_packages:
        try:
            importlib.import_module(import_name)
            print(f"OK: {package_name} - OK")
        except ImportError:
            print(f"ERROR: {package_name} - FALTANTE")
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"ERROR: Faltan dependencias: {', '.join(missing_packages)}")
        return False
    
    return True

def check_django_settings():
    """Verifica la configuración de Django"""
    print("Verificando configuración de Django...")
    
    # Configurar Django con configuración de pruebas para evitar errores
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.test')
    
    try:
        import django
        django.setup()
        from django.conf import settings
        print("OK: Configuración de Django - OK")
        
        # Verificar configuraciones críticas
        critical_settings = [
            'SECRET_KEY',
            'DEBUG',
            'ALLOWED_HOSTS',
            'DATABASES',
            'STATIC_URL',
            'MEDIA_URL'
        ]
        
        for setting in critical_settings:
            if hasattr(settings, setting):
                print(f"OK: {setting} - Configurado")
            else:
                print(f"WARNING: {setting} - No configurado")
        
        return True
    except Exception as e:
        print(f"ERROR: Error en configuración de Django: {e}")
        return False

def check_database():
    """Verifica la conexión a la base de datos"""
    print("Verificando base de datos...")
    
    try:
        import django
        django.setup()
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            print("OK: Conexión a base de datos - OK")
        return True
    except Exception as e:
        print(f"ERROR: Error de conexión a base de datos: {e}")
        return False

def check_migrations():
    """Verifica el estado de las migraciones"""
    print("Verificando migraciones...")
    
    try:
        # Configurar Django primero
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.test')
        import django
        django.setup()
        
        # Verificar migraciones pendientes
        result = subprocess.run([
            sys.executable, 'manage.py', 'showmigrations', '--list'
        ], capture_output=True, text=True, check=True, cwd=project_root)
        
        if '[X]' in result.stdout:
            print("OK: Migraciones aplicadas - OK")
        else:
            print("WARNING: Hay migraciones pendientes")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Error verificando migraciones: {e}")
        return False

def check_static_files():
    """Verifica los archivos estáticos"""
    print("Verificando archivos estáticos...")
    
    static_dirs = ['static', 'staticfiles']
    for static_dir in static_dirs:
        if Path(project_root / static_dir).exists():
            print(f"OK: Directorio {static_dir} - Existe")
        else:
            print(f"WARNING: Directorio {static_dir} - No existe")
    
    return True

def check_tests():
    """Ejecuta las pruebas para verificar que todo funciona"""
    print("Ejecutando pruebas...")
    
    try:
        # Configurar variables de entorno para las pruebas
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.test')
        os.environ.setdefault('CI_ENVIRONMENT', 'true')
        
        # Ejecutar pruebas unitarias rápidas
        result = subprocess.run([
            sys.executable, '-m', 'pytest', 'tests/unit/', '-v', '--tb=short', '--maxfail=3'
        ], capture_output=True, text=True, timeout=300, cwd=project_root)
        
        if result.returncode == 0:
            print("OK: Pruebas unitarias - PASARON")
        else:
            print("ERROR: Pruebas unitarias - FALLARON")
            print(result.stdout)
            print(result.stderr)
            return False
        
        return True
    except subprocess.TimeoutExpired:
        print("ERROR: Pruebas tardaron demasiado tiempo")
        return False
    except Exception as e:
        print(f"ERROR: Error ejecutando pruebas: {e}")
        return False

def check_azure_config():
    """Verifica la configuración de Azure"""
    print("Verificando configuración de Azure...")
    
    # Verificar archivos de configuración de Azure
    azure_files = [
        'azure.yaml',
        'infra/main.bicep',
        'infra/main.parameters.json'
    ]
    
    for azure_file in azure_files:
        if Path(project_root / azure_file).exists():
            print(f"OK: {azure_file} - Existe")
        else:
            print(f"WARNING: {azure_file} - No existe")
    
    # Verificar variables de entorno de Azure
    azure_env_vars = [
        'AZURE_STORAGE_CONNECTION_STRING',
        'BLOB_ACCOUNT_NAME',
        'BLOB_ACCOUNT_KEY'
    ]
    
    for env_var in azure_env_vars:
        if os.getenv(env_var):
            print(f"OK: {env_var} - Configurado")
        else:
            print(f"WARNING: {env_var} - No configurado")
    
    return True

def check_security():
    """Verifica configuraciones de seguridad"""
    print("Verificando configuraciones de seguridad...")
    
    try:
        # Configurar Django primero
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.test')
        import django
        django.setup()
        from django.conf import settings
        
        # Verificar que DEBUG está en False para producción
        if settings.DEBUG:
            print("WARNING: DEBUG está en True - No recomendado para producción")
        else:
            print("OK: DEBUG está en False - OK")
        
        # Verificar SECRET_KEY
        if settings.SECRET_KEY and settings.SECRET_KEY != 'your-secret-key-here':
            print("OK: SECRET_KEY configurado - OK")
        else:
            print("ERROR: SECRET_KEY no configurado correctamente")
            return False
        
        # Verificar ALLOWED_HOSTS
        if settings.ALLOWED_HOSTS:
            print("OK: ALLOWED_HOSTS configurado - OK")
        else:
            print("WARNING: ALLOWED_HOSTS no configurado")
        
        return True
    except Exception as e:
        print(f"ERROR: Error verificando seguridad: {e}")
        return False

def check_performance():
    """Verifica configuraciones de rendimiento"""
    print("Verificando configuraciones de rendimiento...")
    
    try:
        # Configurar Django primero
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.test')
        import django
        django.setup()
        from django.conf import settings
        
        # Verificar configuración de caché
        if hasattr(settings, 'CACHES') and settings.CACHES:
            print("OK: Caché configurado - OK")
        else:
            print("WARNING: Caché no configurado")
        
        # Verificar configuración de sesiones
        if hasattr(settings, 'SESSION_ENGINE'):
            print("OK: Sesiones configuradas - OK")
        else:
            print("WARNING: Sesiones no configuradas")
        
        return True
    except Exception as e:
        print(f"ERROR: Error verificando rendimiento: {e}")
        return False

def main():
    """Función principal"""
    print("Iniciando verificación pre-despliegue para VEA WebApp")
    print("=" * 60)
    
    checks = [
        check_python_version,
        check_django_installation,
        check_dependencies,
        check_django_settings,
        check_database,
        check_migrations,
        check_static_files,
        check_tests,
        check_azure_config,
        check_security,
        check_performance
    ]
    
    passed_checks = 0
    total_checks = len(checks)
    
    for check in checks:
        try:
            if check():
                passed_checks += 1
            print()
        except Exception as e:
            print(f"ERROR: Error en verificación: {e}")
            print()
    
    print("=" * 60)
    print(f"Resumen: {passed_checks}/{total_checks} verificaciones pasaron")
    
    if passed_checks == total_checks:
        print("¡Todo listo para el despliegue!")
        return True
    else:
        print("WARNING: Hay problemas que deben resolverse antes del despliegue")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 