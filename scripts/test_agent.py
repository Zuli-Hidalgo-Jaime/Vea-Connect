"""
VEA Connect - Script de Prueba del Agente
Script para probar el agente de búsqueda y chatbot
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Agregar el directorio backend al path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

load_dotenv()

def test_search_agent():
    """Probar el agente de búsqueda directamente"""
    print("Probando SearchAgent...")
    print("=" * 50)
    
    try:
        from chatbot.search_agent import SearchAgent
        # Crear instancia del agente
        search_agent = SearchAgent()
        print("SearchAgent creado exitosamente")
        
        # Pruebas de búsqueda
        test_queries = [
            ("eventos de esta semana", "eventos"),
            ("medicamentos disponibles", "medicamentos"),
            ("líderes de la iglesia", "lideres"),
            ("servicios y ministerios", "servicios"),
            ("donaciones y ofrendas", "donaciones")
        ]
        
        for query, category in test_queries:
            print(f"\nProbando: '{query}' (categoría: {category})")
            print("-" * 30)
            
            try:
                result = search_agent.search_documents(query, category)
                print(f"Resultado: {result[:200]}...")
            except Exception as e:
                print(f"Error: {str(e)}")
        
        print("\nPruebas de SearchAgent completadas")
        
    except Exception as e:
        print(f"Error al crear SearchAgent: {str(e)}")
        return False
    
    return True

async def test_chatbot():
    """Probar el chatbot completo"""
    print("\nProbando VEAChatbot...")
    print("=" * 50)
    
    try:
        from chatbot.vea_chatbot import VEAChatbot
        # Crear instancia del chatbot
        chatbot = VEAChatbot()
        print("VEAChatbot creado exitosamente")
        
        # Pruebas de chat
        test_messages = [
            "Hola, ¿qué eventos hay esta semana?",
            "¿Qué medicamentos tienen disponibles?",
            "¿Quiénes son los líderes de la iglesia?",
            "¿Qué servicios ofrecen?",
            "¿Cómo puedo hacer una donación?"
        ]
        
        for message in test_messages:
            print(f"\nUsuario: {message}")
            print("-" * 30)
            
            try:
                response = await chatbot.chat(message)
                if response["success"]:
                    print(f"Bot: {response['response'][:200]}...")
                else:
                    print(f"Error: {response.get('error', 'Error desconocido')}")
            except Exception as e:
                print(f"Error: {str(e)}")
        
        print("\nPruebas de VEAChatbot completadas")
        
    except Exception as e:
        print(f"Error al crear VEAChatbot: {str(e)}")
        return False
    
    return True

def test_environment():
    """Verificar variables de entorno"""
    print("Verificando variables de entorno...")
    print("=" * 50)
    
    required_vars = [
        "SEARCH_SERVICE_ENDPOINT",
        "SEARCH_SERVICE_KEY", 
        "SEARCH_INDEX_NAME",
        "OPENAI_API_KEY",
        "OPENAI_ENDPOINT"
    ]
    
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"{var}: {'*' * len(value)}")
        else:
            print(f"{var}: NO CONFIGURADA")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\nVariables faltantes: {', '.join(missing_vars)}")
        print("Configura estas variables en tu archivo .env")
        return False
    
    print("\nTodas las variables de entorno están configuradas")
    return True

async def main():
    """Función principal"""
    print("VEA Connect - Pruebas del Agente")
    print("=" * 60)
    
    # Verificar entorno
    if not test_environment():
        print("\nNo se pueden ejecutar las pruebas sin las variables de entorno")
        return
    
    # Probar SearchAgent
    search_success = test_search_agent()
    
    # Probar VEAChatbot
    chatbot_success = await test_chatbot()
    
    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN DE PRUEBAS")
    print("=" * 60)
    print(f"SearchAgent: {'EXITOSO' if search_success else 'FALLÓ'}")
    print(f"VEAChatbot: {'EXITOSO' if chatbot_success else 'FALLÓ'}")
    
    if search_success and chatbot_success:
        print("\nTodas las pruebas pasaron exitosamente!")
        print("\nPróximos pasos:")
        print("1. Configura Azure AI Search con documentos")
        print("2. Prueba la API REST del chatbot")
        print("3. Integra con WhatsApp")
    else:
        print("\nAlgunas pruebas fallaron. Revisa la configuración.")

if __name__ == "__main__":
    asyncio.run(main())
