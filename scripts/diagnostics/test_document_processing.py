#!/usr/bin/env python3
"""
Script para probar el procesamiento de un documento específico
"""
import os
import sys
import django
import tempfile
from pathlib import Path

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.conf import settings
from apps.documents.models import Document, ProcessingState
from apps.vision.azure_vision_service import AzureVisionService
from services.storage_service import azure_storage

def test_document_processing(document_id: int):
    """Probar el procesamiento de un documento específico"""
    print(f"🔍 Probando procesamiento del documento ID: {document_id}")
    print("=" * 60)
    
    try:
        # Obtener el documento
        document = Document.objects.get(id=document_id)
        print(f"📄 Documento: {document.title}")
        print(f"📁 Archivo: {document.file.name}")
        print(f"📊 Estado actual: {document.processing_state}")
        
        # Paso 1: Descargar archivo
        print("\n📥 Descargando archivo...")
        temp_file_path = azure_storage.download_to_tempfile(document.file.name)
        print(f"✅ Archivo descargado: {temp_file_path}")
        
        # Paso 2: Probar extracción de texto con Vision
        print("\n🔍 Probando extracción de texto con Azure Vision...")
        vision_service = AzureVisionService()
        
        file_extension = Path(document.file.name).suffix.lower()
        if file_extension in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.tif']:
            extracted_text = vision_service.extract_text_from_image(temp_file_path)
            print(f"✅ Texto extraído de imagen: {len(extracted_text)} caracteres")
        elif file_extension == '.pdf':
            extracted_text = vision_service.extract_text_from_pdf(temp_file_path)
            print(f"✅ Texto extraído de PDF: {len(extracted_text)} caracteres")
        else:
            print(f"⚠️ Formato no soportado: {file_extension}")
            extracted_text = f"Contenido del archivo: {document.file.name}"
        
        # Mostrar parte del texto extraído
        if extracted_text:
            preview = extracted_text[:200] + "..." if len(extracted_text) > 200 else extracted_text
            print(f"📝 Vista previa: {preview}")
        
        # Limpiar archivo temporal
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
            print("🧹 Archivo temporal eliminado")
        
        return True
        
    except Document.DoesNotExist:
        print(f"❌ Documento con ID {document_id} no encontrado")
        return False
    except Exception as e:
        print(f"❌ Error procesando documento: {str(e)}")
        return False

def list_documents():
    """Listar documentos disponibles"""
    print("📋 Documentos disponibles:")
    print("=" * 60)
    
    documents = Document.objects.all()[:10]  # Solo los primeros 10
    
    for doc in documents:
        print(f"ID: {doc.id} | {doc.title} | {doc.file.name} | Estado: {doc.processing_state}")
    
    return documents

if __name__ == "__main__":
    # Listar documentos disponibles
    documents = list_documents()
    
    if documents:
        # Probar con el primer documento
        first_doc = documents[0]
        print(f"\n🎯 Probando con el primer documento (ID: {first_doc.id})")
        test_document_processing(first_doc.id)
    else:
        print("❌ No hay documentos disponibles para probar")
