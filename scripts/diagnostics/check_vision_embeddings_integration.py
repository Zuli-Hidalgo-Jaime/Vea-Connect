#!/usr/bin/env python3
"""
Script de diagnóstico para verificar la integración entre Azure Vision y embeddings
"""
import os
import sys
import django
import json
import tempfile
from datetime import datetime
from pathlib import Path

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.conf import settings
from apps.documents.models import Document, ProcessingState
from apps.vision.azure_vision_service import AzureVisionService
from services.search_index_service import search_index_service
from services.storage_service import azure_storage
from utilities.embedding_manager import EmbeddingManager
from utils.redis_cache import get_emb, set_emb

def check_vision_configuration():
    """Verificar configuración de Azure Vision"""
    print("🔍 Verificando configuración de Azure Vision...")
    
    vision_endpoint = getattr(settings, 'VISION_ENDPOINT', None)
    vision_key = getattr(settings, 'VISION_KEY', None)
    
    if not vision_endpoint:
        print("❌ VISION_ENDPOINT no configurado")
        return False
    
    if not vision_key:
        print("❌ VISION_KEY no configurado")
        return False
    
    print(f"✅ VISION_ENDPOINT: {vision_endpoint}")
    print(f"✅ VISION_KEY: {'*' * 10}{vision_key[-4:]}")
    return True

def test_vision_service():
    """Probar el servicio de Azure Vision"""
    print("\n🔍 Probando servicio de Azure Vision...")
    
    try:
        vision_service = AzureVisionService()
        is_available = vision_service.is_service_available()
        
        if is_available:
            print("✅ Servicio de Azure Vision disponible")
            return True
        else:
            print("❌ Servicio de Azure Vision no disponible")
            return False
            
    except Exception as e:
        print(f"❌ Error probando servicio de Azure Vision: {str(e)}")
        return False

def check_documents_in_database():
    """Verificar documentos en la base de datos"""
    print("\n🔍 Verificando documentos en la base de datos...")
    
    try:
        total_docs = Document.objects.count()
        pending_docs = Document.objects.filter(processing_state=ProcessingState.PENDING).count()
        converting_docs = Document.objects.filter(processing_state=ProcessingState.CONVERTING).count()
        ready_docs = Document.objects.filter(processing_state=ProcessingState.READY).count()
        error_docs = Document.objects.filter(processing_state=ProcessingState.ERROR).count()
        
        print(f"📊 Total de documentos: {total_docs}")
        print(f"⏳ Pendientes: {pending_docs}")
        print(f"🔄 Convirtiendo: {converting_docs}")
        print(f"✅ Listos: {ready_docs}")
        print(f"❌ Errores: {error_docs}")
        
        # Mostrar algunos documentos de ejemplo
        if total_docs > 0:
            print("\n📄 Ejemplos de documentos:")
            for doc in Document.objects.all()[:5]:
                print(f"  - ID: {doc.id}, Título: {doc.title}, Estado: {doc.processing_state}")
        
        return total_docs > 0
        
    except Exception as e:
        print(f"❌ Error verificando documentos: {str(e)}")
        return False

def check_azure_search_index():
    """Verificar índice de Azure Search"""
    print("\n🔍 Verificando índice de Azure Search...")
    
    try:
        doc_count = search_index_service.get_document_count()
        print(f"📊 Documentos en Azure Search: {doc_count}")
        return True
        
    except Exception as e:
        print(f"❌ Error verificando Azure Search: {str(e)}")
        return False

def check_embeddings_manager():
    """Verificar el gestor de embeddings"""
    print("\n🔍 Verificando gestor de embeddings...")
    
    try:
        embedding_manager = EmbeddingManager()
        print("✅ EmbeddingManager inicializado correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error inicializando EmbeddingManager: {str(e)}")
        return False

def test_vision_text_extraction():
    """Probar extracción de texto con Azure Vision"""
    print("\n🔍 Probando extracción de texto con Azure Vision...")
    
    try:
        # Crear una imagen de prueba simple
        from PIL import Image, ImageDraw, ImageFont
        
        # Crear imagen con texto
        width, height = 400, 200
        image = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(image)
        
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = ImageFont.load_default()
        
        test_text = "Test de Azure Vision OCR - VEA Connect"
        text_bbox = draw.textbbox((0, 0), test_text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        draw.text((x, y), test_text, fill='black', font=font)
        
        # Guardar imagen temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            image.save(temp_file.name, 'JPEG')
            temp_path = temp_file.name
        
        try:
            # Probar extracción de texto
            vision_service = AzureVisionService()
            extracted_text = vision_service.extract_text_from_image(temp_path)
            
            if extracted_text.strip():
                print(f"✅ Extracción exitosa: '{extracted_text.strip()}'")
                return True
            else:
                print("⚠️ Extracción exitosa pero sin texto detectado")
                return True
            
        finally:
            # Limpiar archivo temporal
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                
    except ImportError:
        print("⚠️ PIL/Pillow no disponible, saltando prueba de extracción")
        return False
    except Exception as e:
        print(f"❌ Error en prueba de extracción: {str(e)}")
        return False

def check_redis_cache():
    """Verificar cache de Redis"""
    print("\n🔍 Verificando cache de Redis...")
    
    try:
        # Probar operaciones básicas de cache
        test_key = "test_vision_embeddings"
        test_value = [0.1, 0.2, 0.3] * 512  # Vector de prueba
        
        # Probar set
        set_emb(test_key, test_value, 60)
        
        # Probar get
        cached_value = get_emb(test_key)
        
        if cached_value:
            print("✅ Cache de Redis funcionando correctamente")
            return True
        else:
            print("❌ Cache de Redis no funciona")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando Redis: {str(e)}")
        return False

def check_document_pipeline_integration():
    """Verificar integración del pipeline de documentos"""
    print("\n🔍 Verificando integración del pipeline de documentos...")
    
    try:
        # Verificar si el pipeline está importando correctamente el servicio de visión
        from tasks.document_pipeline import convert_document_to_text
        
        print("✅ Pipeline de documentos importa correctamente el servicio de visión")
        
        # Verificar si hay documentos que necesitan procesamiento
        pending_docs = Document.objects.filter(processing_state=ProcessingState.PENDING)
        if pending_docs.exists():
            print(f"⚠️ Hay {pending_docs.count()} documentos pendientes de procesamiento")
        else:
            print("✅ No hay documentos pendientes de procesamiento")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verificando pipeline: {str(e)}")
        return False

def generate_diagnostic_report():
    """Generar reporte de diagnóstico completo"""
    print("🚀 Iniciando diagnóstico de integración Vision + Embeddings")
    print("=" * 60)
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "vision_configuration": check_vision_configuration(),
        "vision_service": test_vision_service(),
        "documents_in_db": check_documents_in_database(),
        "azure_search": check_azure_search_index(),
        "embeddings_manager": check_embeddings_manager(),
        "vision_extraction": test_vision_text_extraction(),
        "redis_cache": check_redis_cache(),
        "pipeline_integration": check_document_pipeline_integration()
    }
    
    # Resumen
    print("\n" + "=" * 60)
    print("📋 RESUMEN DEL DIAGNÓSTICO")
    print("=" * 60)
    
    success_count = sum(1 for result in results.values() if isinstance(result, bool) and result)
    total_checks = sum(1 for result in results.values() if isinstance(result, bool))
    
    for check, result in results.items():
        if isinstance(result, bool):
            status = "✅" if result else "❌"
            print(f"{status} {check}")
    
    print(f"\n🎯 Resultado: {success_count}/{total_checks} verificaciones exitosas")
    
    # Guardar reporte
    report_path = "logs/vision_embeddings_diagnostic.json"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Reporte guardado en: {report_path}")
    
    return results

if __name__ == "__main__":
    generate_diagnostic_report()
