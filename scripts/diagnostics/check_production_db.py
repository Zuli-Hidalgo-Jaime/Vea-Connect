#!/usr/bin/env python
"""
Script para diagnosticar problemas de la base de datos de producción
"""
import os
import sys
import django
from pathlib import Path

# Agregar el directorio del proyecto al path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

from django.conf import settings
from django.db import connection
from django.core.management import execute_from_command_line
from apps.core.models import CustomUser

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

def check_migrations():
    """Verificar estado de las migraciones"""
    try:
        from django.core.management import call_command
        from io import StringIO
        
        # Capturar la salida del comando showmigrations
        out = StringIO()
        call_command('showmigrations', stdout=out)
        migrations_output = out.getvalue()
        
        print("📋 Estado de las migraciones:")
        print(migrations_output)
        
        # Verificar si hay migraciones no aplicadas
        if "[ ]" in migrations_output:
            print("⚠️  Hay migraciones pendientes de aplicar")
            return False
        else:
            print("✅ Todas las migraciones están aplicadas")
            return True
    except Exception as e:
        print(f"❌ Error al verificar migraciones: {e}")
        return False

def check_custom_user_model():
    """Verificar el modelo CustomUser"""
    try:
        # Verificar si hay usuarios en la base de datos
        user_count = CustomUser.objects.count()
        print(f"✅ Modelo CustomUser funcionando. Usuarios en BD: {user_count}")
        
        # Verificar campos del modelo
        fields = [f.name for f in CustomUser._meta.fields]
        print(f"📋 Campos del modelo: {fields}")
        
        return True
    except Exception as e:
        print(f"❌ Error con el modelo CustomUser: {e}")
        return False

def check_authentication_form():
    """Verificar el formulario de autenticación"""
    try:
        from apps.core.forms import CustomAuthenticationForm
        
        form = CustomAuthenticationForm()
        print("✅ Formulario de autenticación funcionando")
        print(f"📋 Campos del formulario: {list(form.fields.keys())}")
        
        return True
    except Exception as e:
        print(f"❌ Error con el formulario de autenticación: {e}")
        return False

def check_settings():
    """Verificar configuración de producción"""
    print("🔧 Configuración de producción:")
    print(f"   DEBUG: {settings.DEBUG}")
    print(f"   DATABASE ENGINE: {settings.DATABASES['default']['ENGINE']}")
    print(f"   ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
    print(f"   STATIC_ROOT: {settings.STATIC_ROOT}")
    print(f"   MEDIA_ROOT: {settings.MEDIA_ROOT}")

def main():
    """Función principal"""
    print("🔍 Diagnóstico de la base de datos de producción")
    print("=" * 50)
    
    # Verificar configuración
    check_settings()
    print()
    
    # Verificar conexión a la base de datos
    if not check_database_connection():
        print("❌ No se puede continuar sin conexión a la base de datos")
        return
    
    print()
    
    # Verificar migraciones
    if not check_migrations():
        print("⚠️  Se recomienda aplicar las migraciones pendientes")
    
    print()
    
    # Verificar modelo CustomUser
    if not check_custom_user_model():
        print("❌ Problema con el modelo CustomUser")
    
    print()
    
    # Verificar formulario de autenticación
    if not check_authentication_form():
        print("❌ Problema con el formulario de autenticación")
    
    print()
    print("🏁 Diagnóstico completado")

if __name__ == "__main__":
    main() 