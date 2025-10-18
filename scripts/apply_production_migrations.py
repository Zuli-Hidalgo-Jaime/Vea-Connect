#!/usr/bin/env python
"""
Script para aplicar migraciones pendientes en producción
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.azure_production')

def apply_migrations():
    """Aplicar migraciones pendientes"""
    try:
        django.setup()
        
        from django.core.management import execute_from_command_line
        
        print("=== APLICANDO MIGRACIONES EN PRODUCCIÓN ===")
        
        # Verificar estado de migraciones
        print("1. Verificando estado de migraciones...")
        execute_from_command_line(['manage.py', 'showmigrations'])
        
        # Aplicar migraciones
        print("\n2. Aplicando migraciones...")
        execute_from_command_line(['manage.py', 'migrate'])
        
        # Verificar estado final
        print("\n3. Estado final de migraciones...")
        execute_from_command_line(['manage.py', 'showmigrations'])
        
        print("\n✅ Migraciones aplicadas exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Error aplicando migraciones: {e}")
        return False

if __name__ == "__main__":
    success = apply_migrations()
    sys.exit(0 if success else 1)
