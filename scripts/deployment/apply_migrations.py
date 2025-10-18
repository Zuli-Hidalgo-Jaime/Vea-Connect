#!/usr/bin/env python
"""
Script para aplicar migraciones en Azure App Service.
Este script se puede ejecutar localmente o en el contenedor de Azure.
"""

import os
import sys
import django
from pathlib import Path

# Agregar el directorio del proyecto al path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

from django.core.management import execute_from_command_line
from django.db import connection
import logging

logger = logging.getLogger(__name__)

def apply_migrations():
    """Aplicar todas las migraciones pendientes"""
    try:
        print("🔍 Verificando estado de la base de datos...")
        
        # Verificar conexión a la base de datos
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"✅ Conectado a PostgreSQL: {version[0]}")
        
        # Aplicar migraciones
        print("📦 Aplicando migraciones...")
        execute_from_command_line(['manage.py', 'migrate', '--noinput'])
        
        # Recolectar archivos estáticos
        print("📁 Recolectando archivos estáticos...")
        execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])
        
        print("✅ Migraciones aplicadas exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Error aplicando migraciones: {e}")
        logger.error(f"Error applying migrations: {e}")
        return False

def check_database_schema():
    """Verificar el esquema de la base de datos"""
    try:
        from django.db import connection
        
        with connection.cursor() as cursor:
            # Verificar si existe la columna processing_state
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'documents_document' 
                AND column_name = 'processing_state';
            """)
            
            if cursor.fetchone():
                print("✅ Columna 'processing_state' existe en documents_document")
            else:
                print("❌ Columna 'processing_state' NO existe en documents_document")
                
            # Verificar si existe la columna processing_status (debería estar eliminada)
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'documents_document' 
                AND column_name = 'processing_status';
            """)
            
            if cursor.fetchone():
                print("⚠️  Columna 'processing_status' aún existe (debería estar eliminada)")
            else:
                print("✅ Columna 'processing_status' correctamente eliminada")
                
    except Exception as e:
        print(f"❌ Error verificando esquema: {e}")

if __name__ == '__main__':
    print("🚀 Iniciando aplicación de migraciones...")
    
    # Verificar esquema antes
    check_database_schema()
    
    # Aplicar migraciones
    success = apply_migrations()
    
    # Verificar esquema después
    if success:
        check_database_schema()
    
    print("🏁 Proceso completado")
    sys.exit(0 if success else 1)
