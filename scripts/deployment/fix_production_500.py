#!/usr/bin/env python
"""
Script para resolver el error 500 en producción
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
from django.core.management.base import CommandError

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

def apply_migrations():
    """Aplicar migraciones pendientes"""
    print("🔄 Aplicando migraciones...")
    try:
        # Mostrar estado actual
        print("📋 Estado actual de las migraciones:")
        call_command('showmigrations')
        
        # Aplicar migraciones
        call_command('migrate', verbosity=2)
        print("✅ Migraciones aplicadas exitosamente")
        
        # Mostrar estado final
        print("📋 Estado final de las migraciones:")
        call_command('showmigrations')
        
        return True
    except Exception as e:
        print(f"❌ Error al aplicar migraciones: {e}")
        return False

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

def check_custom_user_table():
    """Verificar que la tabla CustomUser existe y tiene la estructura correcta"""
    try:
        with connection.cursor() as cursor:
            # Verificar si la tabla existe
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'core_customuser'
            """)
            
            if not cursor.fetchone():
                print("❌ Tabla core_customuser no existe")
                return False
            
            # Verificar estructura de la tabla
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'core_customuser'
                ORDER BY ordinal_position
            """)
            
            columns = cursor.fetchall()
            print("📋 Estructura de la tabla core_customuser:")
            for col in columns:
                print(f"   {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")
            
            # Verificar si hay usuarios
            cursor.execute("SELECT COUNT(*) FROM core_customuser")
            user_count = cursor.fetchone()[0]
            print(f"👥 Usuarios en la tabla: {user_count}")
            
            return True
    except Exception as e:
        print(f"❌ Error al verificar tabla CustomUser: {e}")
        return False

def create_superuser_if_needed():
    """Crear superusuario si no existe"""
    try:
        from apps.core.models import CustomUser
        
        if not CustomUser.objects.filter(is_superuser=True).exists():
            print("👤 No hay superusuarios. Creando uno...")
            
            # Crear superusuario con datos por defecto
            superuser = CustomUser.objects.create_superuser(
                email='admin@veaconnect.com',
                password='Admin123!',
                username='admin'
            )
            print(f"✅ Superusuario creado: {superuser.email}")
        else:
            print("✅ Ya existe un superusuario")
        
        return True
    except Exception as e:
        print(f"⚠️  Error al verificar/crear superusuario: {e}")
        return False

def fix_email_field():
    """Arreglar el campo email si es necesario"""
    try:
        with connection.cursor() as cursor:
            # Verificar si hay usuarios con email NULL
            cursor.execute("SELECT COUNT(*) FROM core_customuser WHERE email IS NULL")
            null_emails = cursor.fetchone()[0]
            
            if null_emails > 0:
                print(f"⚠️  Encontrados {null_emails} usuarios con email NULL")
                
                # Actualizar usuarios con email NULL
                cursor.execute("""
                    UPDATE core_customuser 
                    SET email = CONCAT('user_', id, '@example.com')
                    WHERE email IS NULL
                """)
                
                print(f"✅ Actualizados {null_emails} usuarios con email por defecto")
            else:
                print("✅ Todos los usuarios tienen email válido")
        
        return True
    except Exception as e:
        print(f"❌ Error al arreglar campo email: {e}")
        return False

def main():
    """Función principal"""
    print("🔧 Resolviendo error 500 en producción")
    print("=" * 50)
    
    # Verificar conexión a la base de datos
    if not check_database_connection():
        print("❌ No se puede continuar sin conexión a la base de datos")
        return
    
    print()
    
    # Verificar tabla CustomUser
    if not check_custom_user_table():
        print("❌ Problema con la tabla CustomUser")
        return
    
    print()
    
    # Arreglar campo email
    if not fix_email_field():
        print("❌ Error al arreglar campo email")
        return
    
    print()
    
    # Aplicar migraciones
    if not apply_migrations():
        print("❌ Error al aplicar migraciones")
        return
    
    print()
    
    # Crear superusuario si es necesario
    if not create_superuser_if_needed():
        print("⚠️  Error al crear superusuario")
    
    print()
    
    # Recolectar archivos estáticos
    if not collect_static_files():
        print("⚠️  Error al recolectar archivos estáticos")
    
    print()
    print("🏁 Proceso completado")
    print("\n💡 Verifica que el error 500 se haya resuelto:")
    print("   https://veaconnect-webapp-prod-c7aaezbce3ftacdp.centralus-01.azurewebsites.net/login/")

if __name__ == "__main__":
    main() 