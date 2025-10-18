#!/usr/bin/env python
"""
Script para verificar el estado real de la aplicación en producción
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

from django.conf import settings
from django.db import connection
from django.core.management import call_command
from apps.core.models import CustomUser
from django.contrib.auth import authenticate
from django.test import RequestFactory
from django.urls import reverse

def check_database_status():
    """Verificar estado de la base de datos"""
    print("🔍 Verificando estado de la base de datos...")
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            print("✅ Conexión a la base de datos exitosa")
    except Exception as e:
        print(f"❌ Error de conexión a la base de datos: {e}")
        return False
    
    try:
        # Verificar si las tablas existen
        cursor = connection.cursor()
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('core_customuser', 'auth_user')
        """)
        tables = [row[0] for row in cursor.fetchall()]
        print(f"📋 Tablas encontradas: {tables}")
        
        # Verificar usuarios
        user_count = CustomUser.objects.count()
        print(f"👥 Usuarios en la base de datos: {user_count}")
        
        # Verificar superusuarios
        superuser_count = CustomUser.objects.filter(is_superuser=True).count()
        print(f"👑 Superusuarios: {superuser_count}")
        
        return True
    except Exception as e:
        print(f"❌ Error verificando base de datos: {e}")
        return False

def check_login_view():
    """Verificar que la vista de login funcione"""
    print("\n🔍 Verificando vista de login...")
    
    try:
        from apps.core.views import login_view
        from django.contrib.auth.forms import AuthenticationForm
        
        # Crear request factory
        factory = RequestFactory()
        
        # Simular GET request
        request = factory.get('/login/')
        response = login_view(request)
        print(f"✅ GET /login/ - Status: {response.status_code}")
        
        # Simular POST request con datos válidos
        post_data = {
            'username': 'test@example.com',
            'password': 'testpass123',
            'csrfmiddlewaretoken': 'test'
        }
        request = factory.post('/login/', post_data)
        response = login_view(request)
        print(f"✅ POST /login/ - Status: {response.status_code}")
        
        return True
    except Exception as e:
        print(f"❌ Error en vista de login: {e}")
        return False

def check_settings():
    """Verificar configuración"""
    print("\n🔍 Verificando configuración...")
    
    print(f"📊 DEBUG: {settings.DEBUG}")
    print(f"🌐 ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
    print(f"🗄️ DATABASE: {settings.DATABASES['default']['ENGINE']}")
    print(f"📁 STATIC_URL: {settings.STATIC_URL}")
    print(f"📁 MEDIA_URL: {settings.MEDIA_URL}")

def main():
    """Función principal"""
    print("🚀 Verificando estado de la aplicación en producción")
    print("=" * 50)
    
    # Verificar configuración
    check_settings()
    
    # Verificar base de datos
    db_ok = check_database_status()
    
    # Verificar vista de login
    login_ok = check_login_view()
    
    print("\n" + "=" * 50)
    if db_ok and login_ok:
        print("✅ Aplicación funcionando correctamente")
    else:
        print("❌ Hay problemas que necesitan atención")
    
    return db_ok and login_ok

if __name__ == "__main__":
    main() 