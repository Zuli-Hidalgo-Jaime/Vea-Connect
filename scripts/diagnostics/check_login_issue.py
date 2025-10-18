#!/usr/bin/env python
"""
Script para diagnosticar el problema del login en producción
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
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm
from apps.core.forms import CustomAuthenticationForm
from apps.core.models import CustomUser
from django.template.loader import get_template
from django.urls import reverse
from django.test import RequestFactory

def check_login_view():
    """Verificar la vista de login"""
    try:
        from django.contrib.auth import views as auth_views
        from apps.core.forms import CustomAuthenticationForm
        
        # Crear una vista de login
        login_view = auth_views.LoginView.as_view(
            template_name='core/login.html',
            form_class=CustomAuthenticationForm,
            redirect_authenticated_user=True
        )
        
        print("✅ Vista de login creada correctamente")
        return True
    except Exception as e:
        print(f"❌ Error al crear vista de login: {e}")
        return False

def check_template():
    """Verificar el template de login"""
    try:
        template = get_template('core/login.html')
        print("✅ Template de login cargado correctamente")
        
        # Verificar si el template se puede renderizar
        context = {'form': CustomAuthenticationForm()}
        rendered = template.render(context)
        print("✅ Template de login se puede renderizar")
        
        return True
    except Exception as e:
        print(f"❌ Error con el template de login: {e}")
        return False

def check_form():
    """Verificar el formulario de autenticación"""
    try:
        form = CustomAuthenticationForm()
        print("✅ Formulario de autenticación creado correctamente")
        
        # Verificar campos del formulario
        fields = list(form.fields.keys())
        print(f"📋 Campos del formulario: {fields}")
        
        # Verificar si el formulario es válido con datos de prueba
        test_data = {
            'username': 'test@example.com',
            'password': 'testpassword123'
        }
        form = CustomAuthenticationForm(data=test_data)
        print("✅ Formulario de autenticación puede procesar datos")
        
        return True
    except Exception as e:
        print(f"❌ Error con el formulario de autenticación: {e}")
        return False

def check_authentication():
    """Verificar el proceso de autenticación"""
    try:
        # Verificar si hay usuarios en la base de datos
        user_count = CustomUser.objects.count()
        print(f"📊 Usuarios en la base de datos: {user_count}")
        
        # Verificar si hay superusuarios
        superuser_count = CustomUser.objects.filter(is_superuser=True).count()
        print(f"👤 Superusuarios en la base de datos: {superuser_count}")
        
        return True
    except Exception as e:
        print(f"❌ Error al verificar autenticación: {e}")
        return False

def check_urls():
    """Verificar las URLs de login"""
    try:
        from django.urls import reverse
        
        # Verificar si la URL de login existe
        login_url = reverse('core:login')
        print(f"✅ URL de login: {login_url}")
        
        # Verificar otras URLs relacionadas
        logout_url = reverse('core:logout')
        print(f"✅ URL de logout: {logout_url}")
        
        return True
    except Exception as e:
        print(f"❌ Error al verificar URLs: {e}")
        return False

def check_database_connection():
    """Verificar conexión a la base de datos"""
    try:
        from django.db import connection
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            print("✅ Conexión a la base de datos exitosa")
        
        # Verificar si la tabla de usuarios existe
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'core_customuser'
        """)
        
        if cursor.fetchone():
            print("✅ Tabla core_customuser existe")
        else:
            print("❌ Tabla core_customuser no existe")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Error de conexión a la base de datos: {e}")
        return False

def check_migrations():
    """Verificar estado de las migraciones"""
    try:
        from django.core.management import call_command
        from io import StringIO
        
        out = StringIO()
        call_command('showmigrations', 'core', stdout=out)
        migrations_output = out.getvalue()
        
        print("📋 Migraciones de core:")
        print(migrations_output)
        
        # Verificar si hay migraciones no aplicadas
        if "[ ]" in migrations_output:
            print("⚠️  Hay migraciones pendientes de aplicar")
            return False
        else:
            print("✅ Todas las migraciones de core están aplicadas")
            return True
    except Exception as e:
        print(f"❌ Error al verificar migraciones: {e}")
        return False

def main():
    """Función principal"""
    print("🔍 Diagnóstico del problema de login en producción")
    print("=" * 60)
    
    # Verificar conexión a la base de datos
    if not check_database_connection():
        print("❌ No se puede continuar sin conexión a la base de datos")
        return
    
    print()
    
    # Verificar migraciones
    if not check_migrations():
        print("⚠️  Se recomienda aplicar las migraciones pendientes")
    
    print()
    
    # Verificar autenticación
    if not check_authentication():
        print("❌ Problema con la autenticación")
    
    print()
    
    # Verificar formulario
    if not check_form():
        print("❌ Problema con el formulario de autenticación")
    
    print()
    
    # Verificar template
    if not check_template():
        print("❌ Problema con el template de login")
    
    print()
    
    # Verificar vista
    if not check_login_view():
        print("❌ Problema con la vista de login")
    
    print()
    
    # Verificar URLs
    if not check_urls():
        print("❌ Problema con las URLs")
    
    print()
    print("🏁 Diagnóstico completado")
    print("\n💡 Posibles soluciones:")
    print("1. Aplicar migraciones pendientes")
    print("2. Verificar variables de entorno de producción")
    print("3. Verificar logs de Azure App Service")
    print("4. Verificar configuración de la base de datos PostgreSQL")

if __name__ == "__main__":
    main() 