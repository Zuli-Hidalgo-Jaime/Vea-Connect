#!/usr/bin/env python
"""
Script específico para diagnosticar el error 500
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
from django.test import RequestFactory
from django.contrib.auth import authenticate
from django.urls import reverse
from django.template.loader import get_template
from django.template import TemplateDoesNotExist

def check_critical_settings():
    """Verificar configuraciones críticas"""
    print("🔍 Verificando configuraciones críticas...")
    
    critical_settings = [
        'SECRET_KEY',
        'DEBUG',
        'ALLOWED_HOSTS',
        'AUTH_USER_MODEL',
        'LOGIN_URL',
        'LOGIN_REDIRECT_URL',
    ]
    
    for setting in critical_settings:
        try:
            value = getattr(settings, setting)
            print(f"✅ {setting}: {value}")
        except Exception as e:
            print(f"❌ {setting}: Error - {e}")

def check_database_connection():
    """Verificar conexión a la base de datos"""
    print("\n🔍 Verificando conexión a la base de datos...")
    
    try:
        # Verificar conexión básica
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            print("✅ Conexión básica exitosa")
        
        # Verificar tablas críticas
        cursor = connection.cursor()
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('core_customuser', 'auth_user', 'django_migrations')
        """)
        tables = [row[0] for row in cursor.fetchall()]
        print(f"✅ Tablas encontradas: {tables}")
        
        # Verificar migraciones
        cursor.execute("SELECT app, name FROM django_migrations ORDER BY id DESC LIMIT 5")
        migrations = cursor.fetchall()
        print(f"✅ Últimas migraciones: {migrations}")
        
        return True
    except Exception as e:
        print(f"❌ Error de base de datos: {e}")
        return False

def check_template_system():
    """Verificar sistema de templates"""
    print("\n🔍 Verificando sistema de templates...")
    
    try:
        # Verificar template de login
        template = get_template('core/login.html')
        print("✅ Template core/login.html encontrado")
        
        # Verificar template base
        template = get_template('core/base.html')
        print("✅ Template core/base.html encontrado")
        
        return True
    except TemplateDoesNotExist as e:
        print(f"❌ Template no encontrado: {e}")
        return False
    except Exception as e:
        print(f"❌ Error en templates: {e}")
        return False

def check_url_configuration():
    """Verificar configuración de URLs"""
    print("\n🔍 Verificando configuración de URLs...")
    
    try:
        from django.urls import get_resolver
        resolver = get_resolver()
        
        # Verificar URL de login
        login_url = reverse('core:login')
        print(f"✅ URL de login: {login_url}")
        
        # Verificar URL de index
        index_url = reverse('core:index')
        print(f"✅ URL de index: {index_url}")
        
        return True
    except Exception as e:
        print(f"❌ Error en URLs: {e}")
        return False

def check_authentication_system():
    """Verificar sistema de autenticación"""
    print("\n🔍 Verificando sistema de autenticación...")
    
    try:
        from apps.core.models import CustomUser
        from apps.core.forms import CustomAuthenticationForm
        
        # Verificar modelo CustomUser
        user_count = CustomUser.objects.count()
        print(f"✅ Usuarios en BD: {user_count}")
        
        # Verificar formulario de autenticación
        form = CustomAuthenticationForm()
        print("✅ Formulario de autenticación creado")
        
        # Verificar autenticación
        user = authenticate(username='test@example.com', password='testpass123')
        if user:
            print("✅ Autenticación funciona")
        else:
            print("⚠️  Autenticación falló (esperado para credenciales de prueba)")
        
        return True
    except Exception as e:
        print(f"❌ Error en autenticación: {e}")
        return False

def check_static_files():
    """Verificar archivos estáticos"""
    print("\n🔍 Verificando archivos estáticos...")
    
    try:
        print(f"✅ STATIC_URL: {settings.STATIC_URL}")
        print(f"✅ STATIC_ROOT: {settings.STATIC_ROOT}")
        print(f"✅ STATICFILES_DIRS: {settings.STATICFILES_DIRS}")
        
        # Verificar si existen archivos estáticos
        static_dir = Path(settings.STATIC_ROOT)
        if static_dir.exists():
            print("✅ Directorio de archivos estáticos existe")
        else:
            print("⚠️  Directorio de archivos estáticos no existe")
        
        return True
    except Exception as e:
        print(f"❌ Error en archivos estáticos: {e}")
        return False

def check_middleware():
    """Verificar middleware"""
    print("\n🔍 Verificando middleware...")
    
    try:
        middleware = settings.MIDDLEWARE
        print(f"✅ Middleware configurado: {len(middleware)} elementos")
        
        critical_middleware = [
            'django.middleware.security.SecurityMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
        ]
        
        for mw in critical_middleware:
            if mw in middleware:
                print(f"✅ {mw}")
            else:
                print(f"❌ {mw} - FALTANTE")
        
        return True
    except Exception as e:
        print(f"❌ Error en middleware: {e}")
        return False

def check_installed_apps():
    """Verificar aplicaciones instaladas"""
    print("\n🔍 Verificando aplicaciones instaladas...")
    
    try:
        apps = settings.INSTALLED_APPS
        print(f"✅ Aplicaciones instaladas: {len(apps)}")
        
        critical_apps = [
            'django.contrib.auth',
            'django.contrib.sessions',
            'apps.core',
        ]
        
        for app in critical_apps:
            if app in apps:
                print(f"✅ {app}")
            else:
                print(f"❌ {app} - FALTANTE")
        
        return True
    except Exception as e:
        print(f"❌ Error en aplicaciones: {e}")
        return False

def main():
    """Función principal"""
    print("🚀 Diagnóstico completo del error 500")
    print("=" * 60)
    
    checks = [
        check_critical_settings,
        check_database_connection,
        check_template_system,
        check_url_configuration,
        check_authentication_system,
        check_static_files,
        check_middleware,
        check_installed_apps,
    ]
    
    results = []
    for check in checks:
        try:
            result = check()
            results.append(result)
        except Exception as e:
            print(f"❌ Error ejecutando {check.__name__}: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("📊 RESUMEN DEL DIAGNÓSTICO")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Checks pasados: {passed}/{total}")
    print(f"❌ Checks fallidos: {total - passed}/{total}")
    
    if passed == total:
        print("🎉 Todos los checks pasaron. El problema puede ser específico del navegador.")
    else:
        print("⚠️  Hay problemas que necesitan atención.")
    
    return passed == total

if __name__ == "__main__":
    main() 