"""
VEA Connect - Más Preguntas al Chatbot
Prueba el chatbot con preguntas más específicas y variadas
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Agregar el directorio backend al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

load_dotenv()

async def test_more_questions():
    """Test con más preguntas específicas"""
    print("🤖 VEA Connect - Más Preguntas al Chatbot")
    print("=" * 60)
    
    try:
        from chatbot.vea_chatbot import VEAChatbot
        
        chatbot = VEAChatbot()
        print("✅ Chatbot creado exitosamente")
        
        # Preguntas más específicas y variadas
        questions = [
            # Preguntas sobre donaciones específicas
            "¿Qué tipo de donaciones aceptan?",
            "¿Puedo donar alimentos?",
            "¿Hay campaña de recolección actualmente?",
            "¿Qué productos de limpieza necesitan?",
            
            # Preguntas sobre eventos específicos
            "¿Cuándo es la próxima reunión de varones?",
            "¿Hay eventos para niños?",
            "¿Qué actividades hay los domingos?",
            "¿Hay retiros espirituales?",
            
            # Preguntas sobre servicios
            "¿Ofrecen consejería pastoral?",
            "¿Hay grupos de oración?",
            "¿Qué ministerios tienen?",
            "¿Hay clases de Biblia?",
            
            # Preguntas sobre medicamentos
            "¿Tienen paracetamol?",
            "¿Qué medicamentos para la presión?",
            "¿Hay medicinas para niños?",
            "¿Tienen vitaminas?",
            
            # Preguntas generales
            "¿Cuál es la misión de la iglesia?",
            "¿Cómo puedo ser miembro?",
            "¿Hay programas de ayuda social?",
            "¿Qué horarios tienen?",
            "¿Dónde está ubicada la iglesia?",
            "¿Cómo puedo ayudar como voluntario?"
        ]
        
        print(f"\n🧪 Probando {len(questions)} preguntas específicas...")
        print("=" * 60)
        
        for i, question in enumerate(questions, 1):
            print(f"\n{i:2d}. 👤 Usuario: {question}")
            print("-" * 50)
            
            try:
                response = await chatbot.chat(question)
                
                if response["success"]:
                    print(f"🤖 Bot: {response['response']}")
                else:
                    print(f"❌ Error: {response['error']}")
                    
            except Exception as e:
                print(f"❌ Error: {str(e)}")
            
            # Pausa entre preguntas
            await asyncio.sleep(0.3)
        
        print("\n" + "=" * 60)
        print("🎉 Test de preguntas específicas completado!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_more_questions())

