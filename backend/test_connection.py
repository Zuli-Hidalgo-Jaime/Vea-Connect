"""
VEA Connect - Script de Prueba de Conexión
Script para verificar que la configuración y conexiones funcionan correctamente
"""

import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def test_config():
    """Probar configuración"""
    print("🔧 Probando configuración...")
    
    try:
        from config import Config
        
        # Verificar variables de entorno
        required_vars = [
            "SEARCH_SERVICE_NAME",
            "SEARCH_SERVICE_KEY", 
            "SEARCH_SERVICE_ENDPOINT",
            "SEARCH_INDEX_NAME",
            "STORAGE_ACCOUNT_NAME",
            "STORAGE_CONTAINER_NAME",
            "STORAGE_CONNECTION_STRING",
            "COGNITIVE_SERVICES_KEY",
            "COGNITIVE_SERVICES_ENDPOINT"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(Config, var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"❌ Variables de entorno faltantes: {', '.join(missing_vars)}")
            print("💡 Copia env_example.txt a .env y configura las variables")
            return False
        
        print("✅ Configuración válida")
        return True
        
    except Exception as e:
        print(f"❌ Error en configuración: {str(e)}")
        return False

def test_search_client():
    """Probar cliente de Azure AI Search"""
    print("🔍 Probando cliente de Azure AI Search...")
    
    try:
        from search.azure_search_client import AzureSearchClient
        
        client = AzureSearchClient()
        
        # Health check
        if client.health_check():
            print("✅ Cliente de Azure AI Search funcionando")
            return True
        else:
            print("❌ Cliente de Azure AI Search no responde")
            return False
            
    except Exception as e:
        print(f"❌ Error en cliente de Azure AI Search: {str(e)}")
        return False

def test_search_service():
    """Probar servicio de búsqueda"""
    print("🔍 Probando servicio de búsqueda...")
    
    try:
        from search.search_service import SearchService
        
        service = SearchService()
        
        # Health check
        health = service.health_check()
        if health["status"] == "healthy":
            print("✅ Servicio de búsqueda funcionando")
            return True
        else:
            print(f"❌ Servicio de búsqueda no saludable: {health}")
            return False
            
    except Exception as e:
        print(f"❌ Error en servicio de búsqueda: {str(e)}")
        return False

def test_chatbot_service():
    """Probar servicio de chatbot"""
    print("🤖 Probando servicio de chatbot...")
    
    try:
        from chatbot.chatbot_service import ChatbotService
        
        chatbot = ChatbotService()
        
        # Health check
        health = chatbot.health_check()
        if health["status"] == "healthy":
            print("✅ Servicio de chatbot funcionando")
            return True
        else:
            print(f"❌ Servicio de chatbot no saludable: {health}")
            return False
            
    except Exception as e:
        print(f"❌ Error en servicio de chatbot: {str(e)}")
        return False

def test_api():
    """Probar API"""
    print("🌐 Probando API...")
    
    try:
        from main import app
        
        print("✅ API FastAPI creada correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error en API: {str(e)}")
        return False

def main():
    """Función principal de prueba"""
    print("🚀 VEA Connect - Prueba de Conexión")
    print("=" * 50)
    
    tests = [
        ("Configuración", test_config),
        ("Cliente de Azure AI Search", test_search_client),
        ("Servicio de Búsqueda", test_search_service),
        ("Servicio de Chatbot", test_chatbot_service),
        ("API", test_api)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}:")
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 50)
    print("📊 Resumen de Pruebas:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Resultado: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron! El sistema está listo.")
        print("\n🚀 Para ejecutar la aplicación:")
        print("   python main.py")
        print("\n🌐 La API estará disponible en: http://localhost:8000")
        print("📚 Documentación de la API: http://localhost:8000/docs")
    else:
        print("⚠️  Algunas pruebas fallaron. Revisa la configuración.")
        print("\n💡 Pasos para solucionar:")
        print("1. Copia env_example.txt a .env")
        print("2. Configura las variables de entorno con tus credenciales de Azure")
        print("3. Asegúrate de que los recursos de Azure estén creados")
        print("4. Ejecuta este script nuevamente")

if __name__ == "__main__":
    main()



