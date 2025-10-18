#!/usr/bin/env python3
"""
Script para diagnosticar el error 500 específico en el módulo de documentos
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

from django.conf import settings
from django.db import connection
from apps.documents.models import Document
from django.contrib.auth import get_user_model
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

def check_database_connection():
    """Verificar conexión a la base de datos."""
    print_section("VERIFICACIÓN DE CONEXIÓN A BASE DE DATOS")
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            print("✅ Conexión a la base de datos exitosa")
            return True
    except Exception as e:
        print(f"❌ Error de conexión a la base de datos: {e}")
        return False

def check_document_model():
    """Verificar el modelo Document."""
    print_section("VERIFICACIÓN DEL MODELO DOCUMENT")
    
    try:
        # Verificar si la tabla existe
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'documents_document'
            """)
            
            if cursor.fetchone():
                print("✅ Tabla documents_document existe")
            else:
                print("❌ Tabla documents_document no existe")
                return False
        
        # Verificar estructura de la tabla
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'documents_document'
                ORDER BY ordinal_position
            """)
            
            columns = cursor.fetchall()
            print(f"📋 Estructura de la tabla documents_document ({len(columns)} columnas):")
            for col in columns:
                print(f"   {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verificando modelo Document: {e}")
        return False

def check_document_data():
    """Verificar datos en la tabla Document."""
    print_section("VERIFICACIÓN DE DATOS DE DOCUMENTOS")
    
    try:
        # Contar documentos
        document_count = Document.objects.count()
        print(f"📊 Total de documentos en la base de datos: {document_count}")
        
        if document_count > 0:
            # Verificar documentos con archivos
            documents_with_files = Document.objects.filter(file__isnull=False).exclude(file='').count()
            print(f"📁 Documentos con archivos: {documents_with_files}")
            
            # Verificar documentos sin archivos
            documents_without_files = Document.objects.filter(file__isnull=True).count()
            print(f"📄 Documentos sin archivos: {documents_without_files}")
            
            # Mostrar algunos ejemplos
            print("\n📋 Ejemplos de documentos:")
            for doc in Document.objects.all()[:3]:
                print(f"   - ID: {doc.id}, Título: {doc.title}, Archivo: {doc.file.name if doc.file else 'Sin archivo'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verificando datos de documentos: {e}")
        return False

def check_file_storage_configuration():
    """Verificar configuración de almacenamiento de archivos."""
    print_section("VERIFICACIÓN DE CONFIGURACIÓN DE ALMACENAMIENTO")
    
    # Verificar configuración de archivos
    print(f"📁 DEFAULT_FILE_STORAGE: {getattr(settings, 'DEFAULT_FILE_STORAGE', 'No configurado')}")
    print(f"📁 MEDIA_ROOT: {getattr(settings, 'MEDIA_ROOT', 'No configurado')}")
    print(f"📁 MEDIA_URL: {getattr(settings, 'MEDIA_URL', 'No configurado')}")
    
    # Verificar variables de Azure Blob Storage
    azure_vars = {
        'BLOB_ACCOUNT_NAME': getattr(settings, 'BLOB_ACCOUNT_NAME', None),
        'BLOB_ACCOUNT_KEY': getattr(settings, 'BLOB_ACCOUNT_KEY', None),
        'BLOB_CONTAINER_NAME': getattr(settings, 'BLOB_CONTAINER_NAME', None),
        'AZURE_ACCOUNT_NAME': getattr(settings, 'AZURE_ACCOUNT_NAME', None),
        'AZURE_ACCOUNT_KEY': getattr(settings, 'AZURE_ACCOUNT_KEY', None),
        'AZURE_CONTAINER': getattr(settings, 'AZURE_CONTAINER', None),
    }
    
    print("\n🔧 Variables de Azure Blob Storage:")
    for var_name, var_value in azure_vars.items():
        if var_value:
            if 'KEY' in var_name:
                print(f"   ✅ {var_name}: {'*' * len(var_value)}")
            else:
                print(f"   ✅ {var_name}: {var_value}")
        else:
            print(f"   ❌ {var_name}: NO CONFIGURADA")
    
    # Verificar si el directorio MEDIA_ROOT existe
    media_root = getattr(settings, 'MEDIA_ROOT', None)
    if media_root:
        if os.path.exists(media_root):
            print(f"✅ Directorio MEDIA_ROOT existe: {media_root}")
        else:
            print(f"❌ Directorio MEDIA_ROOT no existe: {media_root}")
    
    return True

def test_document_operations():
    """Probar operaciones básicas con documentos."""
    print_section("PRUEBA DE OPERACIONES CON DOCUMENTOS")
    
    try:
        # Probar consulta básica
        print("🔍 Probando consulta básica...")
        documents = Document.objects.all()
        print(f"✅ Consulta básica exitosa: {documents.count()} documentos")
        
        # Probar filtrado
        print("🔍 Probando filtrado...")
        filtered_docs = Document.objects.filter(title__icontains='test')
        print(f"✅ Filtrado exitoso: {filtered_docs.count()} documentos encontrados")
        
        # Probar acceso a propiedades
        if documents.exists():
            doc = documents.first()
            print(f"🔍 Probando acceso a propiedades del documento '{doc.title}'...")
            print(f"   - ID: {doc.id}")
            print(f"   - Título: {doc.title}")
            print(f"   - Categoría: {doc.category}")
            print(f"   - Archivo: {doc.file.name if doc.file else 'Sin archivo'}")
            print(f"   - Usuario: {doc.user.username if doc.user else 'Sin usuario'}")
            
            # Probar propiedad sas_url
            try:
                sas_url = doc.sas_url
                if sas_url:
                    print(f"   - SAS URL: Generada correctamente")
                else:
                    print(f"   - SAS URL: No disponible (normal si no hay archivo)")
            except Exception as e:
                print(f"   - SAS URL: Error - {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en operaciones con documentos: {e}")
        return False

def check_user_authentication():
    """Verificar autenticación de usuarios."""
    print_section("VERIFICACIÓN DE AUTENTICACIÓN")
    
    try:
        User = get_user_model()
        user_count = User.objects.count()
        print(f"👥 Total de usuarios en la base de datos: {user_count}")
        
        if user_count > 0:
            # Verificar usuarios activos
            active_users = User.objects.filter(is_active=True).count()
            print(f"✅ Usuarios activos: {active_users}")
            
            # Verificar superusuarios
            superusers = User.objects.filter(is_superuser=True).count()
            print(f"👑 Superusuarios: {superusers}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verificando autenticación: {e}")
        return False

def check_template_files():
    """Verificar archivos de template."""
    print_section("VERIFICACIÓN DE ARCHIVOS DE TEMPLATE")
    
    template_dirs = getattr(settings, 'TEMPLATES', [])
    if template_dirs:
        for template_config in template_dirs:
            if 'DIRS' in template_config:
                for template_dir in template_config['DIRS']:
                    print(f"📁 Directorio de templates: {template_dir}")
                    
                    # Verificar templates específicos de documentos
                    documents_template = os.path.join(template_dir, 'documents.html')
                    if os.path.exists(documents_template):
                        print(f"✅ Template documents.html encontrado: {documents_template}")
                    else:
                        print(f"❌ Template documents.html no encontrado: {documents_template}")
                    
                    # Verificar directorio de templates de documentos
                    documents_template_dir = os.path.join(template_dir, 'documents')
                    if os.path.exists(documents_template_dir):
                        print(f"✅ Directorio de templates de documentos encontrado: {documents_template_dir}")
                    else:
                        print(f"❌ Directorio de templates de documentos no encontrado: {documents_template_dir}")
    
    return True

def check_url_configuration():
    """Verificar configuración de URLs."""
    print_section("VERIFICACIÓN DE CONFIGURACIÓN DE URLS")
    
    try:
        from django.urls import get_resolver
        resolver = get_resolver()
        
        # Verificar URLs de documentos
        documents_urls = []
        for pattern in resolver.url_patterns:
            if hasattr(pattern, 'url_patterns'):
                for sub_pattern in pattern.url_patterns:
                    if 'documents' in str(sub_pattern.pattern):
                        documents_urls.append(str(sub_pattern.pattern))
        
        if documents_urls:
            print("✅ URLs de documentos encontradas:")
            for url in documents_urls:
                print(f"   - {url}")
        else:
            print("❌ No se encontraron URLs de documentos")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verificando URLs: {e}")
        return False

def generate_recommendations():
    """Generar recomendaciones basadas en los problemas encontrados."""
    print_section("RECOMENDACIONES")
    
    print("🔧 Posibles soluciones para el error 500 en documentos:")
    print()
    print("1. **Si hay problemas con archivos:**")
    print("   - Verificar que MEDIA_ROOT existe y tiene permisos de escritura")
    print("   - Verificar configuración de Azure Blob Storage")
    print("   - Asegurar que los archivos de documentos están accesibles")
    print()
    print("2. **Si hay problemas con la base de datos:**")
    print("   - Ejecutar migraciones: python manage.py migrate")
    print("   - Verificar que la tabla documents_document existe")
    print("   - Verificar permisos de usuario en la base de datos")
    print()
    print("3. **Si hay problemas con templates:**")
    print("   - Verificar que documents.html existe en el directorio correcto")
    print("   - Verificar que el directorio de templates está configurado")
    print()
    print("4. **Si hay problemas con autenticación:**")
    print("   - Verificar que el usuario está autenticado")
    print("   - Verificar que el usuario tiene permisos para acceder a documentos")
    print()
    print("5. **Para debugging adicional:**")
    print("   - Revisar logs de Django en Azure App Service")
    print("   - Habilitar DEBUG temporalmente para ver errores detallados")
    print("   - Verificar logs de la aplicación en Azure Portal")

def main():
    """Función principal."""
    print_header("DIAGNÓSTICO ESPECÍFICO DEL MÓDULO DE DOCUMENTOS")
    
    # Ejecutar todas las verificaciones
    checks = [
        ("Conexión a base de datos", check_database_connection),
        ("Modelo Document", check_document_model),
        ("Datos de documentos", check_document_data),
        ("Configuración de almacenamiento", check_file_storage_configuration),
        ("Operaciones con documentos", test_document_operations),
        ("Autenticación de usuarios", check_user_authentication),
        ("Archivos de template", check_template_files),
        ("Configuración de URLs", check_url_configuration),
    ]
    
    results = []
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
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
    
    print("\n🎯 Diagnóstico completado.")
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
