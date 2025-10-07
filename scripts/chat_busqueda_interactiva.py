"""
VEA Connect - Búsqueda Interactiva (SearchAgent directo)
Permite hacer preguntas y obtener respuestas concisas del índice.
"""

import os
import sys
from dotenv import load_dotenv

# Agregar el directorio backend al path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

load_dotenv()

def main() -> None:
    print("=" * 60)
    print("      VEA Connect - Búsqueda Interactiva")
    print("=" * 60)
    print("\nComandos: escribir pregunta y Enter | 'salir' para terminar\n")

    try:
        from chatbot.search_agent import SearchAgent  # type: ignore
        agent = SearchAgent()
    except Exception as e:
        print(f"Error cargando SearchAgent: {e}")
        return

    while True:
        try:
            user_input = input("Tú: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["salir", "exit", "quit"]:
                print("\n¡Hasta pronto, Hermano(a)!\n")
                break

            result = agent.search_documents(user_input)
            print(f"\nBot: {result}\n")
        except KeyboardInterrupt:
            print("\n\n¡Hasta pronto, Hermano(a)!\n")
            break
        except Exception as e:
            print(f"\nError: {e}\n")

if __name__ == "__main__":
    main()
