"""
VEA Connect - Test Simple del Chatbot
Test básico del chatbot sin depender del índice de búsqueda
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Agregar el directorio backend al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

load_dotenv()

async def test_simple_chat():
    """Test simple del chatbot"""
    print("🤖 VEA Connect - Test Simple del Chatbot")
    print("=" * 50)
    
    try:
        from chatbot.vea_chatbot import VEAChatbot
        
        # Crear chatbot
        chatbot = VEAChatbot()
        print("✅ Chatbot creado exitosamente")
        
        # Test de mensaje simple
        print("\n📝 Probando mensaje simple...")
        response = await chatbot.chat("Hola, ¿cómo estás?")
        
        if response["success"]:
            print(f"✅ Respuesta: {response['response']}")
        else:
            print(f"❌ Error: {response['error']}")
        
        # Test de búsqueda (sin depender del índice)
        print("\n🔍 Probando búsqueda...")
        response = await chatbot.chat("¿Qué eventos hay esta semana?")
        
        if response["success"]:
            print(f"✅ Respuesta: {response['response']}")
        else:
            print(f"❌ Error: {response['error']}")
        
        print("\n🎉 Test completado!")
        
    except Exception as e:
        print(f"❌ Error general: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_simple_chat())

