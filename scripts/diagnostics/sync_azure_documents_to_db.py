#!/usr/bin/env python3
"""
Script para sincronizar documentos de Azure Storage con la base de datos de Django
"""
import os
import sys
import django
import json
from datetime import datetime
from pathlib import Path

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model
from apps.documents.models import Document, ProcessingState
from services.storage_service import azure_storage

User = get_user_model()

def get_or_create_default_user():
    """Obtener o crear un usuario por defecto para los documentos"""
    try:
        # Intentar obtener el primer usuario disponible
        user = User.objects.first()
        if user:
            return user
        
        # Si no hay usuarios, crear uno por defecto
        user = User.objects.create_user(
            username='admin',
            email='admin@veaconnect.com',
            password='admin123'
        )
        print(f"✅ Usuario por defecto creado: {user.username}")
        return user
        
    except Exception as e:
        print(f"❌ Error creando usuario por defecto: {str(e)}")
        return None

def categorize_document(filename):
    """Categorizar documento basado en el nombre del archivo"""
    filename_lower = filename.lower()
    
    if 'donacion' in filename_lower or 'donation' in filename_lower:
        return 'campanas'
    elif 'evento' in filename_lower or 'event' in filename_lower:
        return 'eventos_generales'
    elif 'ministerio' in filename_lower or 'ministry' in filename_lower:
        return 'ministerios'
    elif 'formacion' in filename_lower or 'training' in filename_lower:
        return 'formacion'
    else:
        return 'avisos_globales'

def extract_title_from_filename(filename):
    """Extraer título del nombre del archivo"""
    # Remover extensión
    name_without_ext = Path(filename).stem
    
    # Remover timestamp si existe (formato: _YYYYMMDD_HHMMSS)
    import re
    name_clean = re.sub(r'_\d{8}_\d{6}_[a-f0-9]{8}$', '', name_without_ext)
    
    # Reemplazar guiones bajos con espacios
    title = name_clean.replace('_', ' ').replace('-', ' ')
    
    # Capitalizar
    title = ' '.join(word.capitalize() for word in title.split())
    
    return title or "Documento sin título"

def sync_azure_documents_to_db():
    """Sincronizar documentos de Azure Storage con la base de datos"""
    print("🚀 Iniciando sincronización de documentos Azure → BD")
    print("=" * 60)
    
    try:
        # Obtener usuario por defecto
        default_user = get_or_create_default_user()
        if not default_user:
            print("❌ No se pudo obtener usuario por defecto")
            return False
        
        # Listar todos los blobs en el contenedor de documentos
        result = azure_storage.list_blobs(
            container_name='documents',
            name_starts_with=''
        )
        
        if not result.get('success'):
            print(f"❌ Error listando blobs: {result.get('error')}")
            return False
        
        blobs = result.get('blobs', [])
        print(f"📊 Total de blobs encontrados: {len(blobs)}")
        
        # Filtrar solo archivos de documentos (excluir archivos de sistema)
        document_extensions = {'.pdf', '.doc', '.docx', '.txt', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif'}
        document_blobs = []
        
        for blob in blobs:
            file_ext = Path(blob['name']).suffix.lower()
            if file_ext in document_extensions and not blob['name'].startswith('__'):
                document_blobs.append(blob)
        
        print(f"📄 Documentos válidos encontrados: {len(document_blobs)}")
        
        # Sincronizar cada documento
        created_count = 0
        existing_count = 0
        error_count = 0
        
        for blob in document_blobs:
            try:
                filename = blob['name']
                
                # Verificar si ya existe en la BD
                existing_doc = Document.objects.filter(file=filename).first()
                if existing_doc:
                    existing_count += 1
                    continue
                
                # Crear nuevo documento
                title = extract_title_from_filename(filename)
                category = categorize_document(filename)
                file_type = Path(filename).suffix.lower().lstrip('.')
                
                # Crear el documento
                document = Document.objects.create(
                    title=title,
                    file=filename,
                    description=f"Documento sincronizado desde Azure Storage: {filename}",
                    category=category,
                    file_type=file_type,
                    user=default_user,
                    processing_state=ProcessingState.PENDING,
                    is_processed=False
                )
                
                created_count += 1
                print(f"✅ Creado: {title} ({filename})")
                
            except Exception as e:
                error_count += 1
                print(f"❌ Error creando documento {blob['name']}: {str(e)}")
        
        # Resumen
        print("\n" + "=" * 60)
        print("📋 RESUMEN DE SINCRONIZACIÓN")
        print("=" * 60)
        print(f"✅ Documentos creados: {created_count}")
        print(f"⏭️ Documentos existentes: {existing_count}")
        print(f"❌ Errores: {error_count}")
        print(f"📊 Total procesados: {created_count + existing_count + error_count}")
        
        # Guardar reporte
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_blobs": len(blobs),
            "valid_documents": len(document_blobs),
            "created_count": created_count,
            "existing_count": existing_count,
            "error_count": error_count
        }
        
        report_path = "logs/azure_sync_report.json"
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Reporte guardado en: {report_path}")
        
        return created_count > 0
        
    except Exception as e:
        print(f"❌ Error en sincronización: {str(e)}")
        return False

def trigger_document_processing():
    """Disparar procesamiento de documentos pendientes"""
    print("\n🔄 Disparando procesamiento de documentos pendientes...")
    
    try:
        from tasks.document_pipeline import process_document_async
        
        pending_docs = Document.objects.filter(processing_state=ProcessingState.PENDING)
        print(f"📄 Documentos pendientes de procesamiento: {pending_docs.count()}")
        
        processed_count = 0
        for doc in pending_docs[:5]:  # Procesar solo los primeros 5 para prueba
            try:
                success = process_document_async(doc.id)
                if success:
                    processed_count += 1
                    print(f"✅ Procesado: {doc.title}")
                else:
                    print(f"❌ Error procesando: {doc.title}")
            except Exception as e:
                print(f"❌ Error procesando {doc.title}: {str(e)}")
        
        print(f"📊 Documentos procesados: {processed_count}")
        return processed_count
        
    except Exception as e:
        print(f"❌ Error disparando procesamiento: {str(e)}")
        return 0

if __name__ == "__main__":
    # Sincronizar documentos
    sync_success = sync_azure_documents_to_db()
    
    if sync_success:
        print("\n🎯 Sincronización exitosa. Disparando procesamiento...")
        trigger_document_processing()
    else:
        print("\n⚠️ No se crearon nuevos documentos para procesar")
