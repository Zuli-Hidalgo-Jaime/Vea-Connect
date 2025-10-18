#!/usr/bin/env python3
"""
Diagnóstico Completo del Proyecto VEA-WEBAPP-PROCESS-BOTCONNECT
"""

import os
import sys
import django
import importlib
from pathlib import Path
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

def print_header(title):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print(f"{'='*60}")

def print_section(title):
    """Print a formatted section."""
    print(f"\n📋 {title}")
    print(f"{'-'*40}")

def check_dependencies():
    """Check if all required dependencies are installed."""
    print_section("VERIFICACIÓN DE DEPENDENCIAS")
    
    required_packages = [
        'django',
        'djangorestframework',
        'djangorestframework_simplejwt',
        'drf_yasg',

        'numpy',
        'openai',
        'azure-cognitiveservices-vision-computervision',
        'azure-ai-formrecognizer',
        # 'django-storages',  # Eliminado - no usar django-storages para archivos estáticos/media
        'whitenoise',
        'psycopg2-binary',
        'Pillow',
        'pytest',
        'pytest-django'
    ]
    
    missing_packages = []
    installed_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package.replace('-', '_'))
            installed_packages.append(f"✅ {package}")
        except ImportError:
            missing_packages.append(f"❌ {package}")
    
    print("Paquetes instalados:")
    for pkg in installed_packages:
        print(f"  {pkg}")
    
    if missing_packages:
        print("\nPaquetes faltantes:")
        for pkg in missing_packages:
            print(f"  {pkg}")
        return False
    else:
        print("\n✅ Todas las dependencias están instaladas")
        return True

def check_django_configuration():
    """Check Django configuration."""
    print_section("CONFIGURACIÓN DE DJANGO")
    
    from django.conf import settings
    
    # Check basic settings
    checks = [
        ("DEBUG", settings.DEBUG),
        ("SECRET_KEY", bool(settings.SECRET_KEY)),
        ("ALLOWED_HOSTS", settings.ALLOWED_HOSTS),
        ("DATABASES", bool(settings.DATABASES)),
        ("INSTALLED_APPS", len(settings.INSTALLED_APPS)),
        ("MIDDLEWARE", len(settings.MIDDLEWARE)),
    ]
    
    for name, value in checks:
        status = "✅" if value else "❌"
        print(f"{status} {name}: {value}")
    
    # Check installed apps
    print(f"\nAplicaciones instaladas ({len(settings.INSTALLED_APPS)}):")
    for app in settings.INSTALLED_APPS:
        print(f"  • {app}")

def check_database():
    """Check database configuration."""
    print_section("CONFIGURACIÓN DE BASE DE DATOS")
    
    from django.db import connection
    from django.core.management import execute_from_command_line
    
    try:
        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            print("✅ Conexión a base de datos exitosa")
        
        # Check migrations
        print("\nVerificando migraciones...")
        execute_from_command_line(['manage.py', 'showmigrations', '--list'])
        
    except Exception as e:
        print(f"❌ Error en base de datos: {e}")

def check_urls():
    """Check URL configuration."""
    print_section("CONFIGURACIÓN DE URLs")
    
    try:
        from django.urls import get_resolver
        resolver = get_resolver()
        
        print("Patrones de URL disponibles:")
        for pattern in resolver.url_patterns:
            if hasattr(pattern, 'pattern'):
                print(f"  • {pattern.pattern}")
        
        # Check API URLs specifically
        print("\nVerificando URLs de API...")
        try:
            from apps.embeddings.api_urls import urlpatterns
            print(f"✅ API URLs cargadas: {len(urlpatterns)} patrones")
            for pattern in urlpatterns:
                print(f"  • {pattern.pattern}")
        except Exception as e:
            print(f"❌ Error cargando API URLs: {e}")
            
    except Exception as e:
        print(f"❌ Error verificando URLs: {e}")

def check_models():
    """Check Django models."""
    print_section("VERIFICACIÓN DE MODELOS")
    
    try:
        from django.apps import apps
        
        for app_config in apps.get_app_configs():
            if app_config.name.startswith('apps.'):
                print(f"\n📦 {app_config.name}:")
                for model in app_config.get_models():
                    print(f"  • {model.__name__}")
                    
    except Exception as e:
        print(f"❌ Error verificando modelos: {e}")

def check_embeddings_app():
    """Check embeddings app specifically."""
    print_section("VERIFICACIÓN DE APP EMBEDDINGS")
    
    try:
        # Check models
        from apps.embeddings.models import Embedding, EmbeddingSearchLog
        print("✅ Modelos cargados correctamente")
        
        # Check serializers
        from apps.embeddings.serializers import EmbeddingSerializer
        print("✅ Serializers cargados correctamente")
        
        # Check views
        from apps.embeddings.api_views import EmbeddingViewSet
        print("✅ Views cargados correctamente")
        
        # Test EmbeddingManager
        print("Testing EmbeddingManager...")
        from utilities.embedding_manager import EmbeddingManager
        print("✅ EmbeddingManager cargado correctamente")
        
    except Exception as e:
        print(f"❌ Error en app embeddings: {e}")

def check_environment_variables():
    """Check environment variables."""
    print_section("VARIABLES DE ENTORNO")
    
    important_vars = [
        'DJANGO_ENV',
        'DEBUG',
        'SECRET_KEY',
        'DATABASE_URL',

        'VISION_ENDPOINT',
        'VISION_KEY',
        'OPENAI_API_KEY',
        'AZURE_STORAGE_CONNECTION_STRING'
    ]
    
    for var in important_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if 'KEY' in var or 'PASSWORD' in var or 'SECRET' in var:
                masked_value = value[:4] + '*' * (len(value) - 8) + value[-4:] if len(value) > 8 else '***'
                print(f"✅ {var}: {masked_value}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"⚠️ {var}: No definida")

def check_api_endpoints():
    """Check if API endpoints are accessible."""
    print_section("VERIFICACIÓN DE ENDPOINTS DE API")
    
    try:
        from django.test import Client
        from django.urls import reverse
        
        client = Client()
        
        # Test health endpoint
        try:
            response = client.get('/api/v1/health/')
            if response.status_code == 200:
                print("✅ Health endpoint: Funcionando")
            else:
                print(f"⚠️ Health endpoint: Status {response.status_code}")
        except Exception as e:
            print(f"❌ Health endpoint: Error - {e}")
        
        # Test Swagger endpoint
        try:
            response = client.get('/swagger/')
            if response.status_code == 200:
                print("✅ Swagger endpoint: Funcionando")
            else:
                print(f"⚠️ Swagger endpoint: Status {response.status_code}")
        except Exception as e:
            print(f"❌ Swagger endpoint: Error - {e}")
            
    except Exception as e:
        print(f"❌ Error verificando endpoints: {e}")



def check_azure_services():
    """Check Azure services configuration."""
    print_section("SERVICIOS DE AZURE")
    
    # Check Azure Computer Vision
    try:
        from apps.vision.azure_vision_service import AzureVisionService
        vision_service = AzureVisionService()
        print("✅ AzureVisionService cargado correctamente")
    except Exception as e:
        print(f"❌ Error en AzureVisionService: {e}")
    
    # Check OpenAI service
    try:
        from apps.embeddings.openai_service import OpenAIService
        openai_service = OpenAIService()
        print("✅ OpenAIService cargado correctamente")
    except Exception as e:
        print(f"❌ Error en OpenAIService: {e}")

def generate_recommendations():
    """Generate recommendations based on the diagnostic."""
    print_section("RECOMENDACIONES")
    
    recommendations = [
        "🔧 Instalar djangorestframework-simplejwt si no está instalado",
        "🔧 Verificar que todas las variables de entorno estén configuradas",

        "🔧 Verificar que las migraciones estén aplicadas",
        "🔧 Revisar la configuración de Azure si se usan servicios de Azure",
        "🔧 Considerar agregar logging estructurado para mejor debugging",
        "🔧 Implementar tests unitarios para componentes críticos",
        "🔧 Configurar monitoreo y alertas para producción",
        "🔧 Revisar la seguridad de las configuraciones",
        "🔧 Optimizar consultas de base de datos si es necesario"
    ]
    
    for rec in recommendations:
        print(f"  {rec}")

def main():
    """Run complete diagnostic."""
    print_header("DIAGNÓSTICO COMPLETO DEL PROYECTO")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Directorio: {Path.cwd()}")
    
    # Run all checks
    deps_ok = check_dependencies()
    check_django_configuration()
    check_database()
    check_urls()
    check_models()
    check_embeddings_app()
    check_environment_variables()
    check_api_endpoints()

    check_azure_services()
    
    # Generate recommendations
    generate_recommendations()
    
    # Summary
    print_header("RESUMEN")
    if deps_ok:
        print("✅ El proyecto parece estar configurado correctamente")
        print("⚠️ Revisa las recomendaciones para optimizaciones")
    else:
        print("❌ Hay problemas críticos que necesitan atención")
        print("🔧 Instala las dependencias faltantes primero")
    
    print("\n🎯 Próximos pasos sugeridos:")
    print("  1. Resolver dependencias faltantes")
    print("  2. Verificar configuración de URLs de API")
    print("  3. Probar endpoints críticos")
    print("  4. Ejecutar tests")
    print("  5. Revisar logs para errores específicos")

if __name__ == "__main__":
    main() 