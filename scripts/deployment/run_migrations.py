#!/usr/bin/env python3
"""
Script para ejecutar migraciones manualmente en Azure App Service.
Este script se puede ejecutar via SSH en Azure para verificar que las migraciones funcionen.
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

def setup_django():
    """Configurar Django para ejecutar comandos."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
    django.setup()

def run_migrations():
    """Ejecutar migraciones de Django."""
    print("=== EJECUTANDO MIGRACIONES DE DJANGO ===")
    print()
    
    try:
        # Configurar Django
        setup_django()
        
        # Ejecutar migraciones
        print("Ejecutando migraciones...")
        execute_from_command_line(['manage.py', 'migrate', '--noinput'])
        
        print("✅ Migraciones ejecutadas exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Error al ejecutar migraciones: {e}")
        return False

def check_database():
    """Verificar conexión a la base de datos."""
    print("=== VERIFICANDO CONEXIÓN A BASE DE DATOS ===")
    print()
    
    try:
        setup_django()
        
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"✅ Conexión exitosa a PostgreSQL: {version[0]}")
            
            # Verificar tablas de Django
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE 'django_%'
                LIMIT 5;
            """)
            tables = cursor.fetchall()
            print(f"✅ Tablas de Django encontradas: {len(tables)}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error de conexión a la base de datos: {e}")
        return False

def main():
    """Función principal."""
    print("Script de migraciones para Azure App Service")
    print("=" * 50)
    print()
    
    # Verificar conexión
    if not check_database():
        print("❌ No se pudo conectar a la base de datos")
        return 1
    
    print()
    
    # Ejecutar migraciones
    if not run_migrations():
        print("❌ Error al ejecutar migraciones")
        return 1
    
    print()
    print("🎉 Todas las operaciones completadas exitosamente")
    return 0

if __name__ == "__main__":
    sys.exit(main())
