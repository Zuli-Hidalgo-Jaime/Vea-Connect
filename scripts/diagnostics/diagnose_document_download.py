#!/usr/bin/env python3
"""
Script para diagnosticar problemas de descarga de documentos.
Específicamente para el archivo 'Donaciones_Daya'.
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

django.setup()

def diagnose_document_download():
    """Diagnosticar problemas de descarga de documentos."""
    print("🔍 Diagnóstico de descarga de documentos...")
    
    try:
        from apps.documents.models import Document
        from django.conf import settings
        import requests
        
        # Buscar el documento específico
        documents = Document.objects.filter(title__icontains='Donaciones_Daya')
        
        if not documents.exists():
            print("❌ No se encontró ningún documento con 'Donaciones_Daya' en el título")
            return
        
        print(f"✅ Se encontraron {documents.count()} documentos:")
        
        for doc in documents:
            print(f"\n📄 Documento: {doc.title}")
            print(f"   ID: {doc.pk}")
            print(f"   Categoría: {doc.category}")
            print(f"   Fecha: {doc.date}")
            print(f"   Usuario: {doc.user.username if doc.user else 'N/A'}")
            
            # Verificar archivo
            if doc.file:
                print(f"   ✅ Tiene archivo: {doc.file.name}")
                print(f"   📁 Ruta del archivo: {doc.file.path if hasattr(doc.file, 'path') else 'N/A'}")
                
                # Verificar si el archivo existe físicamente
                if hasattr(doc.file, 'path') and os.path.exists(doc.file.path):
                    print(f"   ✅ Archivo existe físicamente")
                    file_size = os.path.getsize(doc.file.path)
                    print(f"   📏 Tamaño: {file_size} bytes")
                else:
                    print(f"   ❌ Archivo no existe físicamente")
                
                # Verificar URL
                if hasattr(doc.file, 'url'):
                    print(f"   🌐 URL: {doc.file.url}")
                    
                    # Probar la URL
                    try:
                        response = requests.head(doc.file.url, timeout=5)
                        print(f"   🔗 Estado de URL: {response.status_code}")
                        if response.status_code == 200:
                            print(f"   ✅ URL accesible")
                        else:
                            print(f"   ❌ URL no accesible")
                    except Exception as e:
                        print(f"   ❌ Error al probar URL: {e}")
                else:
                    print(f"   ❌ No tiene URL")
                
                # Verificar SAS URL
                if hasattr(doc, 'sas_url') and doc.sas_url:
                    print(f"   🔑 SAS URL disponible")
                    try:
                        response = requests.head(doc.sas_url, timeout=5)
                        print(f"   🔗 Estado de SAS URL: {response.status_code}")
                        if response.status_code == 200:
                            print(f"   ✅ SAS URL accesible")
                        else:
                            print(f"   ❌ SAS URL no accesible")
                    except Exception as e:
                        print(f"   ❌ Error al probar SAS URL: {e}")
                else:
                    print(f"   ❌ No tiene SAS URL")
                    
            else:
                print(f"   ❌ No tiene archivo asociado")
            
            # Verificar configuración de almacenamiento
            print(f"   ⚙️  Configuración de almacenamiento:")
            print(f"      DEFAULT_FILE_STORAGE: {getattr(settings, 'DEFAULT_FILE_STORAGE', 'No configurado')}")
            print(f"      MEDIA_ROOT: {getattr(settings, 'MEDIA_ROOT', 'No configurado')}")
            print(f"      MEDIA_URL: {getattr(settings, 'MEDIA_URL', 'No configurado')}")
            
    except Exception as e:
        print(f"❌ Error durante el diagnóstico: {e}")
        import traceback
        traceback.print_exc()

def test_download_functionality():
    """Probar la funcionalidad de descarga."""
    print("\n🧪 Probando funcionalidad de descarga...")
    
    try:
        from apps.documents.models import Document
        from apps.documents.views import download_document
        from django.test import RequestFactory
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        # Buscar el documento
        documents = Document.objects.filter(title__icontains='Donaciones_Daya')
        
        if not documents.exists():
            print("❌ No se encontró el documento para probar")
            return
        
        doc = documents.first()
        
        # Crear un request de prueba
        factory = RequestFactory()
        request = factory.get(f'/documents/download/{doc.pk}/')
        
        # Simular usuario autenticado
        user = User.objects.first()
        if user:
            request.user = user
            
            print(f"📋 Probando descarga del documento: {doc.title}")
            
            # Intentar la descarga
            try:
                response = download_document(request, doc.pk)
                print(f"   📤 Respuesta: {response.status_code}")
                print(f"   📋 Tipo de contenido: {response.get('Content-Type', 'N/A')}")
                print(f"   📎 Disposición: {response.get('Content-Disposition', 'N/A')}")
                
                if response.status_code == 200:
                    print(f"   ✅ Descarga exitosa")
                else:
                    print(f"   ❌ Error en descarga")
                    
            except Exception as e:
                print(f"   ❌ Error durante la descarga: {e}")
        else:
            print("❌ No hay usuarios disponibles para la prueba")
            
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Iniciando diagnóstico de documentos...")
    diagnose_document_download()
    test_download_functionality()
    print("\n✅ Diagnóstico completado")
