"""
VEA Connect - Chat Interactivo
Script para interactuar con el chatbot en tiempo real
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Agregar el directorio backend al path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

load_dotenv()

async def main():
    """Función principal del chat interactivo"""
    print("=" * 60)
    print("       VEA Connect - Chat Interactivo")
    print("=" * 60)
    print("\nCargando chatbot...")
    
    try:
        from chatbot.vea_chatbot import VEAChatbot  # type: ignore
        chatbot = VEAChatbot()
        print("✓ Chatbot cargado exitosamente\n")
    except Exception as e:
        print(f"✗ Error al cargar el chatbot: {str(e)}")
        return
    
    print("Comandos disponibles:")
    print("  - Escribe tu pregunta y presiona Enter")
    print("  - 'salir' o 'exit' para terminar")
    print("  - 'limpiar' para limpiar el historial de conversación")
    print("\n" + "=" * 60 + "\n")
    
    conversation_id = "interactive_session"
    
    while True:
        try:
            # Obtener entrada del usuario
            user_input = input("Tú: ").strip()
            
            # Verificar comandos especiales
            if user_input.lower() in ['salir', 'exit', 'quit']:
                print("\n¡Que Dios te bendiga, Hermano(a)! Hasta pronto.")
                break
            
            if user_input.lower() in ['limpiar', 'clear', 'reset']:
                chatbot.clear_history()
                print("\n✓ Historial limpiado\n")
                continue
            
            if not user_input:
                continue
            
            # Obtener respuesta del chatbot
            print("\nBot: ", end="", flush=True)
            response = await chatbot.chat(user_input, conversation_id)
            
            if response["success"]:
                print(response["response"])
            else:
                print(f"Error: {response.get('error', 'Error desconocido')}")
            
            print()  # Línea en blanco para separación
            
        except KeyboardInterrupt:
            print("\n\n¡Que Dios te bendiga, Hermano(a)! Hasta pronto.")
            break
        except Exception as e:
            print(f"\nError: {str(e)}\n")

if __name__ == "__main__":
    asyncio.run(main())
