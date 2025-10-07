"""
VEA Connect - Test de Integración OCR
Verificar si el chatbot está usando la información extraída por OCR
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Agregar el directorio backend al path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

load_dotenv()

async def test_ocr_integration():
    """Test específico para verificar integración OCR"""
    print("🔍 VEA Connect - Test de Integración OCR")
    print("=" * 60)
    
    try:
        from chatbot.vea_chatbot import VEAChatbot
        
        chatbot = VEAChatbot()
        print("✅ Chatbot creado exitosamente")
        
        # Preguntas específicas que deberían activar el OCR
        ocr_questions = [
            # Preguntas que deberían encontrar información de las imágenes JPG
            "¿Qué dice el banner de casa de amistad?",
            "¿Qué información hay sobre donaciones?",
            "¿Qué productos necesitan para la campaña?",
            "¿Hay información sobre la reunión de varones?",
            "¿Qué tipos de donativos aceptan?",
            "¿Qué dice sobre la recolección de alimentos?",
            "¿Hay información sobre jabón y productos de limpieza?",
            "¿Qué dice sobre arroz y frijoles?",
            "¿Hay información sobre papel higiénico?",
            "¿Qué productos de limpieza necesitan?"
        ]
        
        print(f"\n🧪 Probando {len(ocr_questions)} preguntas que deberían activar OCR...")
        print("=" * 60)
        
        for i, question in enumerate(ocr_questions, 1):
            print(f"\n{i:2d}. 👤 Usuario: {question}")
            print("-" * 50)
            
            try:
                response = await chatbot.chat(question)
                
                if response["success"]:
                    print(f"🤖 Bot: {response['response']}")
                    
                    # Verificar si la respuesta contiene información específica del OCR
                    ocr_keywords = [
                        "arroz", "frijoles", "jabón", "papel higiénico", 
                        "campaña", "recolección", "alimentos", "limpieza",
                        "donaciones", "banner", "casa de amistad", "varones"
                    ]
                    
                    found_keywords = [kw for kw in ocr_keywords if kw.lower() in response['response'].lower()]
                    if found_keywords:
                        print(f"✅ Encontró información OCR: {found_keywords}")
                    else:
                        print("⚠️ No encontró información específica del OCR")
                        
                else:
                    print(f"❌ Error: {response['error']}")
                    
            except Exception as e:
                print(f"❌ Error: {str(e)}")
            
            await asyncio.sleep(0.5)
        
        print("\n" + "=" * 60)
        print("🎉 Test de integración OCR completado!")
        
        # Test directo del SearchAgent
        print("\n🔍 Test directo del SearchAgent...")
        from chatbot.search_agent import SearchAgent
        search_agent = SearchAgent()
        
        test_queries = [
            "donaciones",
            "campaña",
            "alimentos",
            "jabón",
            "arroz"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Búsqueda directa: '{query}'")
            result = search_agent.search_documents(query)
            print(f"Resultado: {result[:200]}...")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_ocr_integration())
