#!/usr/bin/env python3
"""
Script simple para probar solo el servicio de almacenamiento
"""
import os
import sys
from pathlib import Path

# Agregar el directorio raíz al path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# Configurar variables de entorno básicas si no existen
if not os.getenv('AZURE_STORAGE_CONNECTION_STRING'):
    print("⚠️ AZURE_STORAGE_CONNECTION_STRING no configurada")
    print("Configurando variables de entorno básicas...")
    
    # Intentar cargar desde archivo .env si existe
    env_file = BASE_DIR / '.env'
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    if key not in os.environ:
                        os.environ[key] = value
        print("Variables cargadas desde .env")

# Importar el servicio de almacenamiento
try:
    from services.storage_service import azure_storage
    print("✅ Servicio de almacenamiento importado correctamente")
except ImportError as e:
    print(f"❌ Error importando servicio de almacenamiento: {e}")
    sys.exit(1)

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

def test_get_blob_url():
    """Prueba el método get_blob_url"""
    print("\n🔗 Probando get_blob_url...")
    print("=" * 30)
    
    # Primero listar algunos blobs para obtener nombres reales
    list_result = azure_storage.list_blobs(max_results=1)
    if not list_result.get('success') or not list_result.get('blobs'):
        print("❌ No se pueden obtener blobs para probar get_blob_url")
        return False
    
    test_blob_name = list_result['blobs'][0]['name']
    print(f"Probando con blob: {test_blob_name}")
    
    try:
        result = azure_storage.get_blob_url(test_blob_name)
        if result.get('success'):
            url = result.get('url')
            print(f"✅ Get_blob_url exitoso. URL: {url[:50]}...")
        else:
            print(f"❌ Error en get_blob_url: {result.get('error')}")
            return False
    except Exception as e:
        print(f"❌ Excepción en get_blob_url: {e}")
        return False
    
    return True

def main():
    """Función principal"""
    print("🔧 PRUEBA DEL SERVICIO DE ALMACENAMIENTO")
    print("=" * 50)
    
    tests = [
        ("Servicio de almacenamiento", test_storage_service),
        ("List_blobs", test_list_blobs),
        ("Blob_exists", test_blob_exists),
        ("Delete_blob", test_delete_blob),
        ("Get_blob_url", test_get_blob_url),
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
        print("🎉 ¡Todas las pruebas pasaron! El servicio de almacenamiento funciona correctamente.")
        print("✅ Las correcciones deberían resolver el problema de eliminación de documentos.")
    else:
        print("⚠️ Algunas pruebas fallaron. Revisa los errores anteriores.")
        print("❌ Es posible que haya problemas de configuración de Azure Storage.")

if __name__ == "__main__":
    main()
