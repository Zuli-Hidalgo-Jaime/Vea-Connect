"""
VEA Connect - Test Completo del Chatbot
Prueba el chatbot completo con diferentes consultas
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Agregar el directorio backend al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

load_dotenv()

async def test_chatbot_complete():
    """Test completo del chatbot con diferentes consultas"""
    print("🤖 VEA Connect - Test Completo del Chatbot")
    print("=" * 60)
    
    try:
        from chatbot.vea_chatbot import VEAChatbot
        
        # Crear chatbot
        chatbot = VEAChatbot()
        print("✅ Chatbot creado exitosamente")
        
        # Lista de consultas de prueba
        test_queries = [
            "Hola, ¿cómo estás?",
            "¿Qué eventos hay esta semana?",
            "¿Qué medicamentos tienen disponibles?",
            "¿Cómo puedo hacer una donación?",
            "¿Qué servicios ofrecen?",
            "¿Quiénes son los líderes de la iglesia?",
            "¿Hay información sobre donaciones?",
            "¿Qué actividades hay para jóvenes?",
            "¿Cómo puedo contactar a la iglesia?",
            "¿Cuáles son los horarios de misa?"
        ]
        
        print(f"\n🧪 Probando {len(test_queries)} consultas diferentes...")
        print("=" * 60)
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{i:2d}. 👤 Usuario: {query}")
            print("-" * 50)
            
            try:
                response = await chatbot.chat(query)
                
                if response["success"]:
                    print(f"🤖 Bot: {response['response']}")
                else:
                    print(f"❌ Error: {response['error']}")
                    
            except Exception as e:
                print(f"❌ Error en consulta: {str(e)}")
            
            # Pausa pequeña entre consultas
            await asyncio.sleep(0.5)
        
        print("\n" + "=" * 60)
        print("🎉 Test completo del chatbot finalizado!")
        
        # Mostrar funciones disponibles
        print("\n📋 Funciones disponibles en el chatbot:")
        functions = chatbot.get_available_functions()
        for func in functions:
            print(f"   - {func['name']}: {func['description']}")
        
    except Exception as e:
        print(f"❌ Error general: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_chatbot_complete())

