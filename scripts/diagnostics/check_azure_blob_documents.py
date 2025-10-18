#!/usr/bin/env python3
"""
Script para verificar documentos en Azure Blob Storage vs Base de Datos
"""
import os
import sys
import django
import json
from datetime import datetime

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.conf import settings
from apps.documents.models import Document
from services.storage_service import azure_storage

def check_azure_blob_documents():
    """Verificar documentos en Azure Blob Storage"""
    print("🔍 Verificando documentos en Azure Blob Storage...")
    
    try:
        # Listar blobs en el contenedor de documentos
        result = azure_storage.list_blobs(
            container_name='documents',
            name_starts_with=''
        )
        
        if not result.get('success'):
            print(f"❌ Error listando blobs: {result.get('error')}")
            return False
        
        blobs = result.get('blobs', [])
        print(f"📊 Total de blobs en Azure Storage: {len(blobs)}")
        
        # Mostrar algunos blobs de ejemplo
        if blobs:
            print("\n📄 Ejemplos de blobs:")
            for blob in blobs[:10]:
                print(f"  - {blob['name']} ({blob['size']} bytes)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verificando Azure Blob Storage: {str(e)}")
        return False

def check_database_documents():
    """Verificar documentos en la base de datos"""
    print("\n🔍 Verificando documentos en la base de datos...")
    
    try:
        total_docs = Document.objects.count()
        print(f"📊 Total de documentos en BD: {total_docs}")
        
        if total_docs > 0:
            print("\n📄 Documentos en BD:")
            for doc in Document.objects.all()[:10]:
                print(f"  - ID: {doc.id}, Título: {doc.title}, Archivo: {doc.file.name}")
        
        return total_docs
        
    except Exception as e:
        print(f"❌ Error verificando base de datos: {str(e)}")
        return 0

def check_converted_documents():
    """Verificar documentos convertidos en Azure Storage"""
    print("\n🔍 Verificando documentos convertidos...")
    
    try:
        # Listar blobs convertidos
        result = azure_storage.list_blobs(
            container_name='documents',
            name_starts_with='converted/'
        )
        
        if not result.get('success'):
            print(f"❌ Error listando documentos convertidos: {result.get('error')}")
            return False
        
        converted_blobs = result.get('blobs', [])
        print(f"📊 Total de documentos convertidos: {len(converted_blobs)}")
        
        if converted_blobs:
            print("\n📄 Documentos convertidos:")
            for blob in converted_blobs[:5]:
                print(f"  - {blob['name']} ({blob['size']} bytes)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verificando documentos convertidos: {str(e)}")
        return False

def generate_comparison_report():
    """Generar reporte de comparación"""
    print("🚀 Iniciando verificación de documentos Azure vs BD")
    print("=" * 60)
    
    # Verificar Azure Blob Storage
    azure_success = check_azure_blob_documents()
    
    # Verificar base de datos
    db_count = check_database_documents()
    
    # Verificar documentos convertidos
    converted_success = check_converted_documents()
    
    # Resumen
    print("\n" + "=" * 60)
    print("📋 RESUMEN DE DOCUMENTOS")
    print("=" * 60)
    
    if azure_success and converted_success:
        print("✅ Azure Blob Storage accesible")
    else:
        print("❌ Problemas con Azure Blob Storage")
    
    if db_count > 0:
        print(f"✅ Base de datos tiene {db_count} documentos")
    else:
        print("❌ Base de datos vacía")
    
    # Guardar reporte
    report = {
        "timestamp": datetime.now().isoformat(),
        "azure_blob_success": azure_success,
        "database_count": db_count,
        "converted_success": converted_success
    }
    
    report_path = "logs/azure_blob_comparison.json"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Reporte guardado en: {report_path}")
    
    return report

if __name__ == "__main__":
    generate_comparison_report()
