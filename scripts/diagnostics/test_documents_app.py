#!/usr/bin/env python3
"""
Script de diagnóstico específico para la aplicación documents
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
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from apps.documents.models import Document
from apps.documents.views import document_list, upload_document
from apps.documents.forms import DocumentForm
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_documents_configuration():
    """Verificar la configuración de la aplicación documents"""
    print("=== DIAGNÓSTICO DE LA APLICACIÓN DOCUMENTS ===")
    
    # 1. Verificar configuración de archivos
    print("\n1. Configuración de archivos:")
    print(f"   MEDIA_ROOT: {getattr(settings, 'MEDIA_ROOT', 'NO CONFIGURADO')}")
    print(f"   MEDIA_URL: {getattr(settings, 'MEDIA_URL', 'NO CONFIGURADO')}")
    print(f"   DEFAULT_FILE_STORAGE: {getattr(settings, 'DEFAULT_FILE_STORAGE', 'NO CONFIGURADO')}")
    
    # 2. Verificar configuración de Azure
    print("\n2. Configuración de Azure:")
    print(f"   BLOB_ACCOUNT_NAME: {getattr(settings, 'BLOB_ACCOUNT_NAME', 'NO CONFIGURADO')}")
    print(f"   BLOB_CONTAINER_NAME: {getattr(settings, 'BLOB_CONTAINER_NAME', 'NO CONFIGURADO')}")
    print(f"   DISABLE_AZURE_SIGNALS: {getattr(settings, 'DISABLE_AZURE_SIGNALS', 'NO CONFIGURADO')}")
    
    # 3. Verificar modelo Document
    print("\n3. Verificación del modelo Document:")
    try:
        # Verificar que el modelo se puede importar
        from apps.documents.models import Document
        print("   ✓ Modelo Document importado correctamente")
        
        # Verificar campos del modelo
        fields = [field.name for field in Document._meta.fields]
        print(f"   Campos del modelo: {fields}")
        
        # Verificar que el modelo se puede consultar
        count = Document.objects.count()
        print(f"   ✓ Consulta a la base de datos exitosa. Documentos: {count}")
        
    except Exception as e:
        print(f"   ❌ Error con el modelo Document: {e}")
    
    # 4. Verificar formulario
    print("\n4. Verificación del formulario:")
    try:
        form = DocumentForm()
        print("   ✓ Formulario DocumentForm creado correctamente")
        print(f"   Campos del formulario: {list(form.fields.keys())}")
    except Exception as e:
        print(f"   ❌ Error con el formulario: {e}")
    
    # 5. Verificar vistas
    print("\n5. Verificación de vistas:")
    try:
        # Crear un request factory
        factory = RequestFactory()
        
        # Verificar vista document_list
        request = factory.get('/documents/')
        request.user = None  # Sin usuario autenticado
        
        try:
            response = document_list(request)
            print("   ✓ Vista document_list ejecutada (sin usuario)")
        except Exception as e:
            print(f"   ⚠ Vista document_list con error (esperado sin usuario): {e}")
        
    except Exception as e:
        print(f"   ❌ Error con las vistas: {e}")
    
    # 6. Verificar URLs
    print("\n6. Verificación de URLs:")
    try:
        from django.urls import reverse
        urls_to_test = [
            'documents:document_list',
            'documents:create',
        ]
        
        for url_name in urls_to_test:
            try:
                url = reverse(url_name)
                print(f"   ✓ URL {url_name}: {url}")
            except Exception as e:
                print(f"   ❌ Error con URL {url_name}: {e}")
                
    except Exception as e:
        print(f"   ❌ Error verificando URLs: {e}")
    
    # 7. Verificar plantillas
    print("\n7. Verificación de plantillas:")
    try:
        from django.template.loader import get_template
        templates_to_test = [
            'documents.html',
            'documents/create.html',
        ]
        
        for template_name in templates_to_test:
            try:
                template = get_template(template_name)
                print(f"   ✓ Plantilla {template_name} cargada correctamente")
            except Exception as e:
                print(f"   ❌ Error con plantilla {template_name}: {e}")
                
    except Exception as e:
        print(f"   ❌ Error verificando plantillas: {e}")
    
    print("\n=== FIN DEL DIAGNÓSTICO ===")

if __name__ == "__main__":
    test_documents_configuration()
