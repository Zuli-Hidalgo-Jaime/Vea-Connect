"""
VEA Connect - Chat Simple
Script simplificado para hacer preguntas al chatbot
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Agregar el directorio backend al path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

load_dotenv()

async def chat_simple():
    """Chat simple con el chatbot VEA Connect"""
    print("🤖 VEA Connect - Chat Simple")
    print("=" * 40)
    print("Escribe 'salir' para terminar")
    print("=" * 40)
    
    try:
        from chatbot.search_agent import SearchAgent
        
        search_agent = SearchAgent()
        print("✅ SearchAgent conectado exitosamente")
        
        while True:
            try:
                # Obtener pregunta del usuario
                pregunta = input("\n👤 Tu pregunta: ").strip()
                
                # Verificar si quiere salir
                if pregunta.lower() in ['salir', 'exit', 'quit', 'bye', 'adiós']:
                    print("\n🤖 ¡Hasta luego! Que tengas un día bendecido.")
                    break
                
                # Verificar si la pregunta no está vacía
                if not pregunta:
                    print("⚠️ Por favor, escribe una pregunta.")
                    continue
                
                print(f"\n🔍 Buscando información...")
                print("-" * 30)
                
                # Buscar directamente con SearchAgent
                resultado = search_agent.search_documents(pregunta)
                
                print(f"🤖 Resultado encontrado:")
                print(f"{resultado}")
                
            except KeyboardInterrupt:
                print("\n\n🤖 ¡Hasta luego! Que tengas un día bendecido.")
                break
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                print("Intenta con otra pregunta o escribe 'salir' para terminar.")
        
        print("\n🎉 ¡Gracias por usar VEA Connect!")
        
    except Exception as e:
        print(f"❌ Error al conectar: {str(e)}")

if __name__ == "__main__":
    asyncio.run(chat_simple())

