#!/usr/bin/env python
"""
Script para aplicar migraciones en producción de forma segura
"""
import os
import sys
import django
from pathlib import Path

# Agregar el directorio del proyecto al path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# Configurar Django para producción
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

from django.core.management import call_command
from django.db import connection
from django.conf import settings

def check_database_connection():
    """Verificar conexión a la base de datos"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            print("✅ Conexión a la base de datos exitosa")
            return True
    except Exception as e:
        print(f"❌ Error de conexión a la base de datos: {e}")
        return False

def show_current_migrations():
    """Mostrar el estado actual de las migraciones"""
    print("📋 Estado actual de las migraciones:")
    try:
        call_command('showmigrations')
    except Exception as e:
        print(f"❌ Error al mostrar migraciones: {e}")

def apply_migrations():
    """Aplicar migraciones pendientes"""
    print("🔄 Aplicando migraciones...")
    try:
        call_command('migrate', verbosity=2)
        print("✅ Migraciones aplicadas exitosamente")
        return True
    except Exception as e:
        print(f"❌ Error al aplicar migraciones: {e}")
        return False

def create_superuser_if_needed():
    """Crear superusuario si no existe"""
    try:
        from apps.core.models import CustomUser
        
        if not CustomUser.objects.filter(is_superuser=True).exists():
            print("👤 No hay superusuarios. Creando uno...")
            call_command('createsuperuser', interactive=False)
            print("✅ Superusuario creado")
        else:
            print("✅ Ya existe un superusuario")
    except Exception as e:
        print(f"⚠️  Error al verificar/crear superusuario: {e}")

def collect_static_files():
    """Recolectar archivos estáticos"""
    print("📁 Recolectando archivos estáticos...")
    try:
        call_command('collectstatic', '--noinput', verbosity=2)
        print("✅ Archivos estáticos recolectados")
        return True
    except Exception as e:
        print(f"❌ Error al recolectar archivos estáticos: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 Aplicando migraciones en producción")
    print("=" * 50)
    
    # Verificar conexión a la base de datos
    if not check_database_connection():
        print("❌ No se puede continuar sin conexión a la base de datos")
        return
    
    print()
    
    # Mostrar estado actual de migraciones
    show_current_migrations()
    print()
    
    # Aplicar migraciones
    if not apply_migrations():
        print("❌ Error al aplicar migraciones")
        return
    
    print()
    
    # Crear superusuario si es necesario
    create_superuser_if_needed()
    print()
    
    # Recolectar archivos estáticos
    collect_static_files()
    print()
    
    # Mostrar estado final de migraciones
    print("📋 Estado final de las migraciones:")
    show_current_migrations()
    
    print()
    print("🏁 Proceso completado")

if __name__ == "__main__":
    main() 