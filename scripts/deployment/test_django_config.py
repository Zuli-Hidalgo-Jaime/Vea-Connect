#!/usr/bin/env python3
"""
Script para probar la configuración de Django en Azure App Service
"""

import os
import sys
import django

def test_django_config():
    """Prueba la configuración de Django"""
    print("=== PRUEBA DE CONFIGURACIÓN DJANGO ===")
    
    # Configurar variables de entorno
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
    
    # Agregar el directorio actual al path para desarrollo local
    current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, current_dir)
    
    print(f"DJANGO_SETTINGS_MODULE: {os.environ.get('DJANGO_SETTINGS_MODULE')}")
    print(f"PYTHONPATH: {os.environ.get('PYTHONPATH')}")
    
    try:
        # Configurar Django
        django.setup()
        print("✅ Django configurado correctamente")
        
        # Importar settings
        from django.conf import settings
        print(f"✅ Settings importados: {settings.SETTINGS_MODULE}")
        
        # Verificar ALLOWED_HOSTS
        print(f"✅ ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
        
        # Verificar DEBUG
        print(f"✅ DEBUG: {settings.DEBUG}")
        
        # Verificar DATABASES
        print(f"✅ DATABASES configurado: {'default' in settings.DATABASES}")
        
        # Verificar INSTALLED_APPS
        print(f"✅ INSTALLED_APPS: {len(settings.INSTALLED_APPS)} aplicaciones")
        
        # Verificar MIDDLEWARE
        print(f"✅ MIDDLEWARE: {len(settings.MIDDLEWARE)} middlewares")
        
        # Verificar STATIC_ROOT
        print(f"✅ STATIC_ROOT: {settings.STATIC_ROOT}")
        
        # Verificar CSRF_TRUSTED_ORIGINS
        print(f"✅ CSRF_TRUSTED_ORIGINS: {getattr(settings, 'CSRF_TRUSTED_ORIGINS', 'No configurado')}")
        
        print("\n🎉 TODAS LAS PRUEBAS PASARON - Django está configurado correctamente")
        return True
        
    except Exception as e:
        print(f"❌ ERROR en la configuración de Django: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_wsgi_application():
    """Prueba la aplicación WSGI"""
    print("\n=== PRUEBA DE APLICACIÓN WSGI ===")
    
    try:
        # Importar la aplicación WSGI
        from config.wsgi import application
        print("✅ Aplicación WSGI importada correctamente")
        
        # Verificar que es callable
        if callable(application):
            print("✅ Aplicación WSGI es callable")
        else:
            print("❌ Aplicación WSGI no es callable")
            return False
            
        print("🎉 Aplicación WSGI está configurada correctamente")
        return True
        
    except Exception as e:
        print(f"❌ ERROR en la aplicación WSGI: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Función principal"""
    print("🔍 PROBANDO CONFIGURACIÓN DE DJANGO EN AZURE")
    print("=" * 60)
    
    # Probar configuración de Django
    django_ok = test_django_config()
    
    # Probar aplicación WSGI
    wsgi_ok = test_wsgi_application()
    
    print("\n" + "=" * 60)
    if django_ok and wsgi_ok:
        print("🎉 TODAS LAS PRUEBAS PASARON - Django está listo para funcionar")
        print("\n📋 PRÓXIMOS PASOS:")
        print("1. El error 500 debería estar resuelto")
        print("2. Verifica los logs de Azure para confirmar")
        print("3. Accede a la aplicación en el navegador")
    else:
        print("❌ HAY PROBLEMAS EN LA CONFIGURACIÓN")
        print("\n🔧 CORRECCIONES NECESARIAS:")
        print("- Verifica las variables de entorno")
        print("- Confirma que los archivos de configuración existen")
        print("- Revisa los logs de Azure para más detalles")

if __name__ == "__main__":
    main() 