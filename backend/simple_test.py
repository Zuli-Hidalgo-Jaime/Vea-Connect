"""
VEA Connect - Test Simple
Test básico para verificar conexiones de Azure
"""

import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def test_azure_search():
    """Probar conexión con Azure AI Search"""
    print("🔍 Probando Azure AI Search...")
    
    try:
        from azure.core.credentials import AzureKeyCredential
        from azure.search.documents import SearchClient
        
        endpoint = os.getenv('SEARCH_SERVICE_ENDPOINT')
        key = os.getenv('SEARCH_SERVICE_KEY')
        index_name = os.getenv('SEARCH_INDEX_NAME')
        
        if not all([endpoint, key, index_name]):
            print("❌ Faltan variables de entorno para Azure AI Search")
            return False
        
        # Crear cliente
        client = SearchClient(
            endpoint=endpoint,
            index_name=index_name,
            credential=AzureKeyCredential(key)
        )
        
        print("✅ Cliente de Azure AI Search creado correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_azure_storage():
    """Probar conexión con Azure Storage"""
    print("📦 Probando Azure Storage...")
    
    try:
        from azure.storage.blob import BlobServiceClient
        
        connection_string = os.getenv('STORAGE_CONNECTION_STRING')
        
        if not connection_string:
            print("❌ Falta variable STORAGE_CONNECTION_STRING")
            return False
        
        # Crear cliente
        client = BlobServiceClient.from_connection_string(connection_string)
        
        print("✅ Cliente de Azure Storage creado correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_cognitive_services():
    """Probar conexión con Cognitive Services"""
    print("🧠 Probando Cognitive Services...")
    
    try:
        from azure.cognitiveservices.vision.computervision import ComputerVisionClient
        from azure.core.credentials import AzureKeyCredential
        
        endpoint = os.getenv('COGNITIVE_SERVICES_ENDPOINT')
        key = os.getenv('COGNITIVE_SERVICES_KEY')
        
        if not all([endpoint, key]):
            print("❌ Faltan variables de entorno para Cognitive Services")
            return False
        
        # Crear cliente
        client = ComputerVisionClient(
            endpoint=endpoint,
            credentials=AzureKeyCredential(key)
        )
        
        print("✅ Cliente de Cognitive Services creado correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def main():
    """Ejecutar todas las pruebas"""
    print("🚀 VEA Connect - Test Simple")
    print("=" * 50)
    
    tests = [
        test_azure_search,
        test_azure_storage,
        test_cognitive_services
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Resultado: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("🎉 ¡Todas las conexiones funcionan correctamente!")
    else:
        print("⚠️  Algunas conexiones fallaron. Revisa la configuración.")

if __name__ == "__main__":
    main()
