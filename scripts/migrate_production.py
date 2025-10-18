#!/usr/bin/env python
"""
Script para ejecutar migraciones en producción
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

from django.core.management import execute_from_command_line

def main():
    """Ejecutar migraciones en producción"""
    print("🚀 Iniciando migraciones en producción...")
    
    try:
        # Ejecutar migraciones
        execute_from_command_line(['manage.py', 'migrate'])
        print("✅ Migraciones aplicadas exitosamente")
        
        # Verificar estado de migraciones
        execute_from_command_line(['manage.py', 'showmigrations'])
        print("✅ Estado de migraciones verificado")
        
    except Exception as e:
        print(f"❌ Error durante las migraciones: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 