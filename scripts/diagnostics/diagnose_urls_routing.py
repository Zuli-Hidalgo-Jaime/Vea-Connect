#!/usr/bin/env python3
"""
Script para diagnosticar problemas de URLs y routing específicamente en el módulo de documentos
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

from django.urls import get_resolver, reverse, NoReverseMatch
from django.conf import settings
from django.template.loader import get_template
from django.template import TemplateDoesNotExist
from apps.documents import views
import logging

def print_header(title):
    """Imprimir un encabezado formateado."""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print(f"{'='*60}")

def print_section(title):
    """Imprimir una sección formateada."""
    print(f"\n📋 {title}")
    print(f"{'-'*40}")

def check_url_resolution():
    """Verificar resolución de URLs de documentos."""
    print_section("VERIFICACIÓN DE RESOLUCIÓN DE URLS")
    
    # URLs específicas de documentos a probar
    document_urls = [
        'documents:document_list',
        'documents:create',
        'documents:edit',
        'documents:delete',
        'documents:download',
    ]
    
    for url_name in document_urls:
        try:
            if 'edit' in url_name or 'delete' in url_name or 'download' in url_name:
                # Para URLs que requieren pk
                url = reverse(url_name, kwargs={'pk': 1})
                print(f"✅ {url_name}: {url}")
            else:
                url = reverse(url_name)
                print(f"✅ {url_name}: {url}")
        except NoReverseMatch as e:
            print(f"❌ {url_name}: Error - {e}")
        except Exception as e:
            print(f"❌ {url_name}: Error inesperado - {e}")

def check_url_patterns():
    """Verificar patrones de URL registrados."""
    print_section("VERIFICACIÓN DE PATRONES DE URL")
    
    try:
        resolver = get_resolver()
        
        # Buscar patrones relacionados con documentos
        documents_patterns = []
        
        def find_documents_patterns(patterns, prefix=""):
            for pattern in patterns:
                if hasattr(pattern, 'url_patterns'):
                    # Es un include
                    if 'documents' in str(pattern.pattern):
                        documents_patterns.append(f"{prefix}{pattern.pattern}")
                    find_documents_patterns(pattern.url_patterns, f"{prefix}{pattern.pattern}")
                else:
                    # Es un path
                    if 'documents' in str(pattern.pattern):
                        documents_patterns.append(f"{prefix}{pattern.pattern}")
        
        find_documents_patterns(resolver.url_patterns)
        
        if documents_patterns:
            print("✅ Patrones de documentos encontrados:")
            for pattern in documents_patterns:
                print(f"   - {pattern}")
        else:
            print("❌ No se encontraron patrones de documentos")
            
    except Exception as e:
        print(f"❌ Error verificando patrones de URL: {e}")

def check_template_existence():
    """Verificar existencia de templates."""
    print_section("VERIFICACIÓN DE TEMPLATES")
    
    templates_to_check = [
        'documents.html',
        'documents/create.html',
        'core/base_dashboard.html',
    ]
    
    for template_name in templates_to_check:
        try:
            template = get_template(template_name)
            print(f"✅ {template_name}: Encontrado")
            print(f"   Ruta: {template.origin.name}")
        except TemplateDoesNotExist:
            print(f"❌ {template_name}: NO ENCONTRADO")
        except Exception as e:
            print(f"❌ {template_name}: Error - {e}")

def check_view_functions():
    """Verificar funciones de vista."""
    print_section("VERIFICACIÓN DE FUNCIONES DE VISTA")
    
    view_functions = [
        'document_list',
        'upload_document',
        'edit_document',
        'delete_document',
        'download_document',
    ]
    
    for func_name in view_functions:
        try:
            func = getattr(views, func_name)
            print(f"✅ {func_name}: Encontrada")
            print(f"   Tipo: {type(func).__name__}")
            if hasattr(func, '__name__'):
                print(f"   Nombre: {func.__name__}")
        except AttributeError:
            print(f"❌ {func_name}: NO ENCONTRADA")
        except Exception as e:
            print(f"❌ {func_name}: Error - {e}")

def check_app_configuration():
    """Verificar configuración de la aplicación."""
    print_section("VERIFICACIÓN DE CONFIGURACIÓN DE APLICACIÓN")
    
    # Verificar si la app está en INSTALLED_APPS
    if 'apps.documents' in settings.INSTALLED_APPS:
        print("✅ apps.documents está en INSTALLED_APPS")
    else:
        print("❌ apps.documents NO está en INSTALLED_APPS")
    
    # Verificar configuración de templates
    template_dirs = getattr(settings, 'TEMPLATES', [])
    if template_dirs:
        for i, template_config in enumerate(template_dirs):
            print(f"📁 Configuración de templates {i+1}:")
            if 'DIRS' in template_config:
                for template_dir in template_config['DIRS']:
                    print(f"   - {template_dir}")
                    if os.path.exists(template_dir):
                        print(f"     ✅ Directorio existe")
                    else:
                        print(f"     ❌ Directorio NO existe")

def test_url_access():
    """Probar acceso a URLs específicas."""
    print_section("PRUEBA DE ACCESO A URLS")
    
    # Crear un request simulado para probar
    from django.test import RequestFactory
    from django.contrib.auth import get_user_model
    
    try:
        factory = RequestFactory()
        
        # Probar URL principal de documentos
        request = factory.get('/documents/')
        
        # Verificar si la vista document_list puede ser llamada
        try:
            # Esto solo verifica que la función existe y es callable
            # No ejecuta la lógica completa para evitar errores de base de datos
            if hasattr(views, 'document_list'):
                print("✅ Vista document_list es accesible")
            else:
                print("❌ Vista document_list NO es accesible")
        except Exception as e:
            print(f"❌ Error accediendo a document_list: {e}")
            
    except Exception as e:
        print(f"❌ Error en prueba de acceso: {e}")

def check_imports():
    """Verificar imports necesarios."""
    print_section("VERIFICACIÓN DE IMPORTS")
    
    try:
        from apps.documents import urls
        print("✅ apps.documents.urls importado correctamente")
        
        from apps.documents import views
        print("✅ apps.documents.views importado correctamente")
        
        from apps.documents.models import Document
        print("✅ apps.documents.models importado correctamente")
        
    except ImportError as e:
        print(f"❌ Error de import: {e}")
    except Exception as e:
        print(f"❌ Error inesperado en imports: {e}")

def check_urls_file():
    """Verificar archivo de URLs de documentos."""
    print_section("VERIFICACIÓN DE ARCHIVO DE URLS")
    
    urls_file = Path('apps/documents/urls.py')
    if urls_file.exists():
        print(f"✅ Archivo de URLs existe: {urls_file}")
        
        # Leer y verificar contenido básico
        try:
            with open(urls_file, 'r') as f:
                content = f.read()
                if 'urlpatterns' in content:
                    print("✅ urlpatterns encontrado en el archivo")
                else:
                    print("❌ urlpatterns NO encontrado en el archivo")
                    
                if 'app_name' in content:
                    print("✅ app_name encontrado en el archivo")
                else:
                    print("❌ app_name NO encontrado en el archivo")
                    
        except Exception as e:
            print(f"❌ Error leyendo archivo de URLs: {e}")
    else:
        print(f"❌ Archivo de URLs NO existe: {urls_file}")

def generate_recommendations():
    """Generar recomendaciones basadas en los problemas encontrados."""
    print_section("RECOMENDACIONES")
    
    print("🔧 Posibles soluciones para el error 500 en /documents/:")
    print()
    print("1. **Si hay problemas con URLs:**")
    print("   - Verificar que apps.documents está en INSTALLED_APPS")
    print("   - Verificar que el archivo apps/documents/urls.py existe")
    print("   - Verificar que las funciones de vista están definidas")
    print()
    print("2. **Si hay problemas con templates:**")
    print("   - Verificar que documents.html existe en templates/")
    print("   - Verificar que core/base_dashboard.html existe")
    print("   - Verificar que los directorios de templates están configurados")
    print()
    print("3. **Si hay problemas con imports:**")
    print("   - Verificar que todos los módulos están instalados")
    print("   - Verificar que no hay errores de sintaxis en los archivos")
    print()
    print("4. **Para debugging adicional:**")
    print("   - Habilitar DEBUG temporalmente para ver errores detallados")
    print("   - Revisar logs de Django en Azure App Service")
    print("   - Verificar que la aplicación está correctamente desplegada")

def main():
    """Función principal."""
    print_header("DIAGNÓSTICO DE URLS Y ROUTING PARA DOCUMENTOS")
    
    # Ejecutar todas las verificaciones
    checks = [
        ("Imports", check_imports),
        ("Archivo de URLs", check_urls_file),
        ("Configuración de aplicación", check_app_configuration),
        ("Patrones de URL", check_url_patterns),
        ("Resolución de URLs", check_url_resolution),
        ("Funciones de vista", check_view_functions),
        ("Templates", check_template_existence),
        ("Acceso a URLs", test_url_access),
    ]
    
    results = []
    for check_name, check_func in checks:
        try:
            check_func()
            results.append((check_name, True))
        except Exception as e:
            print(f"❌ Error en {check_name}: {e}")
            results.append((check_name, False))
    
    # Resumen de resultados
    print_section("RESUMEN DE VERIFICACIONES")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"✅ Verificaciones exitosas: {passed}/{total}")
    print(f"❌ Verificaciones fallidas: {total - passed}/{total}")
    
    for check_name, result in results:
        status = "✅" if result else "❌"
        print(f"   {status} {check_name}")
    
    # Generar recomendaciones
    if passed < total:
        generate_recommendations()
    
    print("\n🎯 Diagnóstico de URLs y routing completado.")
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
