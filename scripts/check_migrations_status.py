#!/usr/bin/env python
"""
Script para verificar el estado de las migraciones
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.azure_production')

def check_migrations():
    """Verificar estado de migraciones"""
    try:
        django.setup()
        
        from django.db import connection
        from django.core.management import execute_from_command_line
        
        print("=== VERIFICANDO ESTADO DE MIGRACIONES ===")
        
        # Verificar estado de migraciones
        print("Estado de migraciones:")
        execute_from_command_line(['manage.py', 'showmigrations'])
        
        # Verificar si la columna vector_id existe
        print("\nVerificando columna vector_id en documents_document...")
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'documents_document' 
                AND column_name = 'vector_id'
            """)
            result = cursor.fetchone()
            
            if result:
                print("✅ Columna vector_id existe")
            else:
                print("❌ Columna vector_id NO existe")
                print("Necesitas aplicar las migraciones pendientes")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verificando migraciones: {e}")
        return False

if __name__ == "__main__":
    success = check_migrations()
    sys.exit(0 if success else 1)
