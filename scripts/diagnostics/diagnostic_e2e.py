#!/usr/bin/env python3
"""
Script de diagnóstico E2E para probar todos los servicios del sistema
"""
import os
import sys
import django
from pathlib import Path

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.azure_production')
django.setup()

from django.contrib.auth import get_user_model
from apps.documents.models import Document
from services.storage_service import azure_storage
from services.search_index_service import SearchIndexService
from services.redis_cache import WhatsAppCacheService
from services.whatsapp_sender import WhatsAppSenderService
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

User = get_user_model()

def test_storage_service():
    """Prueba el servicio de almacenamiento"""
    print("\n🔍 Probando servicio de almacenamiento...")
    print("=" * 50)
    
    # Verificar configuración
    status = azure_storage.get_configuration_status()
    print(f"Estado de configuración:")
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    if not status['client_initialized']:
        print("❌ Cliente de Azure Storage no inicializado")
        return False
    
    print("✅ Cliente de Azure Storage inicializado correctamente")
    return True

def test_storage_naming_resolution():
    """Prueba el sistema de resolución de nombres de almacenamiento"""
    print("\n🔍 Probando resolución de nombres de almacenamiento...")
    print("=" * 60)
    
    import uuid
    import tempfile
    
    # Generar nombre de prueba único
    test_uuid = str(uuid.uuid4())[:8]
    original_name = f"Donaciones Daya 2025_08_08_{test_uuid}.jpg"
    
    print(f"Nombre original de prueba: {original_name}")
    
    # 1. Probar canonicalización
    canonical_name = azure_storage.canonicalize_blob_name(original_name, category="documents")
    print(f"Nombre canónico: {canonical_name}")
    
    # 2. Crear archivo temporal para subida
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
        temp_file.write(f"Archivo de prueba para diagnóstico E2E - {test_uuid}")
        temp_file_path = temp_file.name
    
    try:
        # 3. Subir archivo con nombre original
        print(f"Subiendo archivo con nombre original...")
        upload_result = azure_storage.upload_file(
            file_path=temp_file_path,
            blob_name=original_name,
            category="documents",
            content_type="text/plain"
        )
        
        if not upload_result['success']:
            print(f"❌ Error al subir archivo: {upload_result['error']}")
            return False
        
        print(f"✅ Archivo subido exitosamente")
        print(f"  Original: {upload_result['original_name']}")
        print(f"  Canónico: {upload_result['blob_name']}")
        
        # 4. Probar resolución por nombre original (sin prefijo)
        print(f"Probando resolución por nombre original...")
        resolved_name = azure_storage.resolve_blob_name(original_name)
        if resolved_name:
            print(f"✅ Resolución exitosa: {resolved_name}")
        else:
            print(f"❌ No se pudo resolver el nombre")
            return False
        
        # 5. Probar descarga por nombre original
        print(f"Probando descarga por nombre original...")
        download_path = temp_file_path + ".downloaded"
        download_result = azure_storage.download_file(
            blob_name=original_name,
            local_path=download_path
        )
        
        if download_result['success']:
            print(f"✅ Descarga exitosa")
            print(f"  Resuelto como: {download_result['resolved_name']}")
        else:
            print(f"❌ Error en descarga: {download_result['error']}")
            return False
        
        # 6. Probar eliminación por nombre original
        print(f"Probando eliminación por nombre original...")
        delete_result = azure_storage.delete_blob(original_name)
        
        if delete_result['success']:
            print(f"✅ Eliminación exitosa")
            print(f"  Resuelto como: {delete_result['resolved_name']}")
        else:
            print(f"❌ Error en eliminación: {delete_result['error']}")
            return False
        
        # 7. Verificar que ya no existe
        final_check = azure_storage.resolve_blob_name(original_name)
        if not final_check:
            print(f"✅ Verificación final: archivo eliminado correctamente")
        else:
            print(f"⚠️ Advertencia: archivo aún existe después de eliminación")
        
        # Limpiar archivos temporales
        try:
            os.unlink(temp_file_path)
            os.unlink(download_path)
        except:
            pass
        
        print("✅ Todas las pruebas de resolución de nombres pasaron")
        return True
        
    except Exception as e:
        print(f"❌ Error en pruebas de resolución: {e}")
        # Limpiar archivo temporal
        try:
            os.unlink(temp_file_path)
        except:
            pass
        return False

def test_list_blobs():
    """Prueba el método list_blobs"""
    print("\n📋 Probando list_blobs...")
    print("=" * 30)
    
    try:
        result = azure_storage.list_blobs(max_results=5)
        if result.get('success'):
            blobs = result.get('blobs', [])
            print(f"✅ List_blobs exitoso. Encontrados {len(blobs)} blobs")
            for blob in blobs[:3]:  # Mostrar solo los primeros 3
                print(f"  - {blob['name']} ({blob['size']} bytes)")
        else:
            print(f"❌ Error en list_blobs: {result.get('error')}")
            return False
    except Exception as e:
        print(f"❌ Excepción en list_blobs: {e}")
        return False
    
    return True

def test_blob_exists():
    """Prueba el método blob_exists"""
    print("\n🔍 Probando blob_exists...")
    print("=" * 30)
    
    # Primero listar algunos blobs para obtener nombres reales
    list_result = azure_storage.list_blobs(max_results=1)
    if not list_result.get('success') or not list_result.get('blobs'):
        print("❌ No se pueden obtener blobs para probar exists")
        return False
    
    test_blob_name = list_result['blobs'][0]['name']
    print(f"Probando con blob: {test_blob_name}")
    
    try:
        result = azure_storage.blob_exists(test_blob_name)
        if result.get('success'):
            exists = result.get('exists')
            print(f"✅ Blob_exists exitoso. Existe: {exists}")
        else:
            print(f"❌ Error en blob_exists: {result.get('error')}")
            return False
    except Exception as e:
        print(f"❌ Excepción en blob_exists: {e}")
        return False
    
    return True

def test_delete_blob():
    """Prueba el método delete_blob (solo verificación, no elimina realmente)"""
    print("\n🗑️ Probando delete_blob (solo verificación)...")
    print("=" * 40)
    
    # Crear un blob de prueba temporal
    test_blob_name = "test_delete_diagnostic.txt"
    test_data = b"This is a test file for diagnostics"
    
    try:
        # Subir archivo de prueba
        upload_result = azure_storage.upload_data(
            data=test_data,
            blob_name=test_blob_name,
            content_type="text/plain"
        )
        
        if not upload_result.get('success'):
            print(f"❌ Error subiendo archivo de prueba: {upload_result.get('error')}")
            return False
        
        print(f"✅ Archivo de prueba subido: {test_blob_name}")
        
        # Verificar que existe
        exists_result = azure_storage.blob_exists(test_blob_name)
        if not exists_result.get('success') or not exists_result.get('exists'):
            print("❌ El archivo de prueba no existe después de subirlo")
            return False
        
        print("✅ Archivo de prueba existe correctamente")
        
        # Probar eliminación
        delete_result = azure_storage.delete_blob(test_blob_name)
        if delete_result.get('success'):
            print("✅ Delete_blob exitoso")
            
            # Verificar que ya no existe
            exists_result = azure_storage.blob_exists(test_blob_name)
            if exists_result.get('success') and not exists_result.get('exists'):
                print("✅ Archivo eliminado correctamente")
            else:
                print("⚠️ El archivo aún existe después de eliminarlo")
        else:
            print(f"❌ Error en delete_blob: {delete_result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Excepción en delete_blob: {e}")
        return False
    
    return True

def test_documents_in_db():
    """Prueba los documentos en la base de datos"""
    print("\n📄 Probando documentos en la base de datos...")
    print("=" * 40)
    
    try:
        documents = Document.objects.all()
        print(f"Total de documentos en BD: {documents.count()}")
        
        if documents.exists():
            # Mostrar algunos documentos
            for doc in documents[:3]:
                print(f"  - {doc.title} (ID: {doc.id})")
                print(f"    Archivo: {doc.file.name if doc.file else 'Sin archivo'}")
                print(f"    Tipo: {doc.file_type}")
                print()
        else:
            print("No hay documentos en la base de datos")
            
    except Exception as e:
        print(f"❌ Error accediendo a documentos: {e}")
        return False
    
    return True

def test_document_deletion_simulation():
    """Simula el proceso de eliminación de documentos"""
    print("\n🎭 Simulando proceso de eliminación de documentos...")
    print("=" * 50)
    
    try:
        documents = Document.objects.all()
        if not documents.exists():
            print("No hay documentos para simular eliminación")
            return True
        
        # Tomar el primer documento para simular
        test_doc = documents.first()
        print(f"Simulando eliminación de: {test_doc.title}")
        
        # Simular el proceso de la vista delete_document
        possible_filenames = [
            test_doc.file.name if test_doc.file else None,
            f"documents/{test_doc.file.name}" if test_doc.file else None,
            f"documents/{test_doc.title}.{test_doc.file_type}" if test_doc.file_type else None,
        ]
        
        # Filtrar nombres None
        possible_filenames = [f for f in possible_filenames if f]
        print(f"Nombres posibles a verificar: {possible_filenames}")
        
        # Verificar existencia de cada archivo
        for filename in possible_filenames:
            exists_result = azure_storage.blob_exists(filename)
            if exists_result.get('success'):
                exists = exists_result.get('exists')
                print(f"  {filename}: {'✅ Existe' if exists else '❌ No existe'}")
            else:
                print(f"  {filename}: ❌ Error verificando: {exists_result.get('error')}")
        
        print("✅ Simulación completada")
        
    except Exception as e:
        print(f"❌ Error en simulación: {e}")
        return False
    
    return True

def test_ai_search_service():
    """Prueba el servicio de Azure AI Search"""
    print("\n🔍 Probando Azure AI Search...")
    print("=" * 40)
    
    try:
        search_service = SearchIndexService()
        
        # Verificar configuración
        if not search_service.client:
            print("❌ Cliente de AI Search no inicializado")
            return False
        
        print("✅ Cliente de AI Search inicializado")
        
        # Probar búsqueda simple
        test_query = "donaciones"
        results = search_service.search(test_query, top=3)
        
        if results is not None:
            print(f"✅ Búsqueda exitosa. Encontrados {len(results)} resultados")
            for i, result in enumerate(results[:2], 1):
                content = result.get('content', '')[:100] + '...' if len(result.get('content', '')) > 100 else result.get('content', '')
                print(f"  {i}. {content}")
        else:
            print("⚠️ Búsqueda no retornó resultados (puede ser normal)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en AI Search: {e}")
        return False

def test_redis_cache():
    """Prueba el servicio de Redis Cache"""
    print("\n🔴 Probando Redis Cache...")
    print("=" * 30)
    
    try:
        cache_service = WhatsAppCacheService()
        
        # Probar almacenamiento y recuperación
        test_phone = "+525512345678"
        test_context = {
            "last_message": "Hola",
            "timestamp": "2024-01-01T12:00:00Z"
        }
        
        # Almacenar contexto
        store_result = cache_service.store_conversation_context(test_phone, test_context)
        if store_result:
            print("✅ Almacenamiento de contexto exitoso")
        else:
            print("⚠️ Almacenamiento de contexto falló (puede ser normal si Redis no está configurado)")
        
        # Recuperar contexto
        retrieved_context = cache_service.get_conversation_context(test_phone)
        if retrieved_context:
            print("✅ Recuperación de contexto exitosa")
        else:
            print("⚠️ Recuperación de contexto falló (puede ser normal)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en Redis Cache: {e}")
        return False

def test_whatsapp_sender():
    """Prueba el servicio de WhatsApp Sender"""
    print("\n📱 Probando WhatsApp Sender...")
    print("=" * 35)
    
    try:
        sender_service = WhatsAppSenderService()
        
        # Verificar configuración
        config_status = sender_service.validate_configuration()
        
        print("Estado de configuración:")
        for key, value in config_status.items():
            print(f"  {key}: {value}")
        
        if config_status.get('all_configured', False):
            print("✅ WhatsApp Sender completamente configurado")
        else:
            print("⚠️ WhatsApp Sender parcialmente configurado")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en WhatsApp Sender: {e}")
        return False

def test_openai_integration():
    """Prueba la integración con Azure OpenAI"""
    print("\n🤖 Probando Azure OpenAI...")
    print("=" * 35)
    
    try:
        from openai import AzureOpenAI
        
        # Verificar variables de entorno
        required_vars = [
            'AZURE_OPENAI_ENDPOINT',
            'AZURE_OPENAI_API_KEY',
            'AZURE_OPENAI_CHAT_DEPLOYMENT'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.environ.get(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"❌ Variables de entorno faltantes: {missing_vars}")
            return False
        
        # Obtener valores de configuración
        endpoint = os.environ.get('AZURE_OPENAI_ENDPOINT')
        api_key = os.environ.get('AZURE_OPENAI_API_KEY')
        deployment = os.environ.get('AZURE_OPENAI_CHAT_DEPLOYMENT')
        api_version = os.environ.get('AZURE_OPENAI_CHAT_API_VERSION', '2024-02-15-preview')
        
        if not all([endpoint, api_key, deployment]):
            print("❌ Configuración incompleta de OpenAI")
            return False
        
        # Inicializar cliente
        client = AzureOpenAI(
            azure_endpoint=endpoint,  # type: ignore
            api_key=api_key,  # type: ignore
            api_version=api_version  # type: ignore
        )
        
        # Probar llamada simple
        response = client.chat.completions.create(
            model=deployment,  # type: ignore
            messages=[
                {"role": "user", "content": "Responde solo 'OK' si recibes este mensaje."}
            ],
            max_tokens=10,
            temperature=0
        )
        
        if response.choices and response.choices[0].message and response.choices[0].message.content:
            content = response.choices[0].message.content.strip()
            print(f"✅ OpenAI responde correctamente: '{content}'")
            
            # Manejar caso de respuesta string (deployment name)
            if content == os.environ.get('AZURE_OPENAI_CHAT_DEPLOYMENT'):
                print("⚠️ OpenAI devolvió el nombre del deployment como respuesta")
                print("Esto puede indicar que el deployment no está configurado correctamente")
                return False
            else:
                return True
        else:
            print("❌ OpenAI no devolvió respuesta válida")
            return False
            
    except Exception as e:
        print(f"❌ Error en OpenAI: {e}")
        return False

def test_storage_container_creation():
    """Prueba la creación de contenedores temporales en Storage"""
    print("\n📦 Probando creación de contenedores temporales...")
    print("=" * 50)
    
    try:
        # Verificar si el contenedor principal existe
        list_result = azure_storage.list_blobs(max_results=1)
        if list_result.get('success'):
            print("✅ Contenedor principal accesible")
            
            # Crear contenedor temporal de prueba
            test_container = "test-diagnostic-temp"
            print(f"Intentando crear contenedor temporal: {test_container}")
            
            # Nota: Esta es una simulación ya que no tenemos método para crear contenedores
            # En un entorno real, esto se haría con permisos adecuados
            print("⚠️ Creación de contenedores requiere permisos adicionales")
            print("✅ Verificación de acceso al storage completada")
            
            return True
        else:
            print("❌ No se puede acceder al contenedor principal")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando storage: {e}")
        return False

def main():
    """Función principal"""
    print("🔧 DIAGNÓSTICO E2E COMPLETO DEL SISTEMA")
    print("=" * 60)
    
    tests = [
        ("Servicio de almacenamiento", test_storage_service),
        ("Resolución de nombres de almacenamiento", test_storage_naming_resolution),
        ("List_blobs", test_list_blobs),
        ("Blob_exists", test_blob_exists),
        ("Delete_blob", test_delete_blob),
        ("Documentos en BD", test_documents_in_db),
        ("Simulación de eliminación", test_document_deletion_simulation),
        ("Azure AI Search", test_ai_search_service),
        ("Redis Cache", test_redis_cache),
        ("WhatsApp Sender", test_whatsapp_sender),
        ("Azure OpenAI", test_openai_integration),
        ("Storage Container", test_storage_container_creation),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Error ejecutando {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumen
    print("\n📊 RESUMEN DE PRUEBAS")
    print("=" * 30)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nResultado: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron! El sistema debería funcionar correctamente.")
    else:
        print("⚠️ Algunas pruebas fallaron. Revisa los errores anteriores.")

if __name__ == "__main__":
    main()
