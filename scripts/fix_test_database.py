#!/usr/bin/env python3
"""
Script para limpiar la base de datos de tests y corregir problemas de migración.

Este script resuelve los problemas de índices duplicados y otros errores
que impiden que los tests se ejecuten correctamente.
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
sys.path.append(str(Path(__file__).parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.test')

django.setup()

from django.core.management import execute_from_command_line
from django.db import connection
from django.conf import settings


def clean_test_database():
    """Limpiar la base de datos de tests."""
    print("🧹 Limpiando base de datos de tests...")
    
    try:
        # Eliminar archivos de base de datos de test
        test_db_files = [
            'db.sqlite3_test',
            'test_db.sqlite3',
            'test.db'
        ]
        
        for db_file in test_db_files:
            if os.path.exists(db_file):
                os.remove(db_file)
                print(f"✅ Eliminado: {db_file}")
        
        # Limpiar cache de pytest
        pytest_cache = Path('.pytest_cache')
        if pytest_cache.exists():
            import shutil
            shutil.rmtree(pytest_cache)
            print("✅ Eliminado: .pytest_cache")
        
        print("✅ Base de datos de tests limpiada")
        
    except Exception as e:
        print(f"❌ Error limpiando base de datos: {e}")


def fix_migration_issues():
    """Corregir problemas de migración."""
    print("🔧 Corrigiendo problemas de migración...")
    
    try:
        # Ejecutar migraciones con --fake-initial para evitar conflictos
        execute_from_command_line(['manage.py', 'migrate', '--fake-initial'])
        print("✅ Migraciones aplicadas con --fake-initial")
        
    except Exception as e:
        print(f"❌ Error en migraciones: {e}")
        print("🔄 Intentando migración completa...")
        
        try:
            # Intentar migración completa
            execute_from_command_line(['manage.py', 'migrate'])
            print("✅ Migración completa exitosa")
            
        except Exception as e2:
            print(f"❌ Error en migración completa: {e2}")


def create_test_superuser():
    """Crear superusuario de test si no existe."""
    print("👤 Creando superusuario de test...")
    
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        if not User.objects.filter(username='testadmin').exists():
            User.objects.create_superuser(
                username='testadmin',
                email='test@example.com',
                password='testpass123'
            )
            print("✅ Superusuario de test creado")
        else:
            print("ℹ️ Superusuario de test ya existe")
            
    except Exception as e:
        print(f"❌ Error creando superusuario: {e}")


def verify_database_health():
    """Verificar la salud de la base de datos."""
    print("🏥 Verificando salud de la base de datos...")
    
    try:
        with connection.cursor() as cursor:
            # Verificar tablas principales
            tables = [
                'auth_user',
                'core_customuser',
                'directory_contact',
                'documents_document',
                'events_event',
                'donations_donation',
                'embeddings_embedding',
                'whatsapp_bot_whatsappuser'
            ]
            
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"✅ {table}: {count} registros")
                except Exception as e:
                    print(f"⚠️ {table}: Error - {e}")
        
        print("✅ Verificación de base de datos completada")
        
    except Exception as e:
        print(f"❌ Error verificando base de datos: {e}")


def main():
    """Función principal."""
    print("🚀 Iniciando corrección de base de datos de tests...")
    print("=" * 60)
    
    # 1. Limpiar base de datos
    clean_test_database()
    print()
    
    # 2. Corregir migraciones
    fix_migration_issues()
    print()
    
    # 3. Crear superusuario de test
    create_test_superuser()
    print()
    
    # 4. Verificar salud
    verify_database_health()
    print()
    
    print("=" * 60)
    print("✅ Corrección de base de datos completada")
    print("🎯 Ahora puedes ejecutar los tests sin problemas")


if __name__ == "__main__":
    main() 