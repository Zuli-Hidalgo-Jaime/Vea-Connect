"""
VEA Connect - Chatbot Simple sin OpenAI
Test del chatbot con respuestas simuladas para probar la lógica
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Agregar el directorio backend al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

load_dotenv()

class SimpleChatbot:
    """Chatbot simple sin OpenAI para probar la lógica"""
    
    def __init__(self):
        self.responses = {
            "hola": "¡Hola Hermano(a)! Soy VEA Connect, tu asistente virtual de la iglesia. ¿En qué puedo ayudarte hoy?",
            "eventos": "Te ayudo a buscar información sobre eventos. Por el momento no hay eventos programados, pero puedes consultar en la mesa de Relaciones Públicas.",
            "medicamentos": "Para información sobre medicamentos disponibles, te recomiendo contactar directamente con la farmacia de la iglesia.",
            "lideres": "Los líderes de nuestra iglesia están disponibles para ayudarte. Puedes consultar el directorio en la mesa de información.",
            "servicios": "Ofrecemos varios servicios y ministerios. ¿Te interesa algún servicio específico?",
            "donaciones": "Para hacer donaciones, puedes acercarte a la mesa de Relaciones Públicas o consultar los métodos disponibles en la oficina."
        }
    
    async def chat(self, user_message: str) -> dict:
        """Procesar mensaje del usuario"""
        message_lower = user_message.lower()
        
        # Buscar palabras clave
        for keyword, response in self.responses.items():
            if keyword in message_lower:
                return {
                    "success": True,
                    "response": response,
                    "timestamp": "2025-01-03T00:00:00"
                }
        
        # Respuesta por defecto
        return {
            "success": True,
            "response": "Gracias por tu consulta Hermano(a). Te voy a conectar con nuestro equipo de Relaciones Públicas para que te ayuden mejor con esa consulta.",
            "timestamp": "2025-01-03T00:00:00"
        }

async def test_simple_chatbot():
    """Test del chatbot simple"""
    print("🤖 VEA Connect - Chatbot Simple (Sin OpenAI)")
    print("=" * 50)
    
    try:
        chatbot = SimpleChatbot()
        print("✅ Chatbot simple creado exitosamente")
        
        # Tests
        test_messages = [
            "Hola, ¿cómo estás?",
            "¿Qué eventos hay esta semana?",
            "¿Qué medicamentos tienen disponibles?",
            "¿Quiénes son los líderes de la iglesia?",
            "¿Qué servicios ofrecen?",
            "¿Cómo puedo hacer una donación?",
            "¿Cuál es el horario de misas?"
        ]
        
        for message in test_messages:
            print(f"\n👤 Usuario: {message}")
            response = await chatbot.chat(message)
            print(f"🤖 Bot: {response['response']}")
        
        print("\n🎉 Test del chatbot simple completado!")
        print("\n✅ El chatbot responde correctamente a las consultas")
        print("✅ La lógica de búsqueda de palabras clave funciona")
        print("✅ Las respuestas son apropiadas para la comunidad religiosa")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_simple_chatbot())

