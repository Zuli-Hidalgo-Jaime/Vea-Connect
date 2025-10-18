#!/usr/bin/env python
"""
Script para arreglar el problema de migración en producción
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

from django.db import connection
from django.core.management import execute_from_command_line

def main():
    """Arreglar el problema de migración"""
    print("🔧 Arreglando problema de migración...")
    
    try:
        with connection.cursor() as cursor:
            # Marcar la migración problemática como aplicada
            cursor.execute("""
                INSERT INTO django_migrations (app, name, applied) 
                VALUES ('directory', '0004_alter_contact_first_name_alter_contact_last_name', NOW())
                ON CONFLICT (app, name) DO NOTHING;
            """)
            print("✅ Migración problemática marcada como aplicada")
        
        # Ejecutar las nuevas migraciones
        print("🚀 Ejecutando nuevas migraciones...")
        execute_from_command_line(['manage.py', 'migrate', '--settings=config.settings.production'])
        print("✅ Nuevas migraciones aplicadas exitosamente")
        
        # Verificar estado
        execute_from_command_line(['manage.py', 'showmigrations', '--settings=config.settings.production'])
        print("✅ Estado de migraciones verificado")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 