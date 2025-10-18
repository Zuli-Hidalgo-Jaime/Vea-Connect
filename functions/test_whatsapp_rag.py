#!/usr/bin/env python3
"""
Script de prueba para verificar la funcionalidad de WhatsApp con RAG y OpenAI
"""

import os
import json
import logging
import sys
from datetime import datetime, timezone

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_rag_context():
    """Prueba la función de búsqueda vectorial"""
    logger.info("=== Probando búsqueda vectorial ===")
    
    try:
        import requests
        
        # URL de la función de búsqueda
        function_url = os.getenv('SEARCH_SIMILAR_FUNCTION_URL', 'http://localhost:7071/api/search_similar')
        
        # Query de prueba
        test_query = "contacto de Daya"
        
        logger.info(f"Query de prueba: {test_query}")
        logger.info(f"URL de función: {function_url}")
        
        # Preparar datos de búsqueda
        search_data = {
            "query": test_query,
            "top": 3
        }
        
        # Realizar búsqueda
        response = requests.post(
            function_url,
            json=search_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            search_results = response.json()
            logger.info(f"✅ Búsqueda exitosa: {len(search_results)} resultados")
            
            for i, result in enumerate(search_results, 1):
                if isinstance(result, dict):
                    content = result.get('content', '')
                    text = result.get('text', '')
                    title = result.get('title', '')
                    score = result.get('score', 0)
                    
                    relevant_text = content or text or title
                    logger.info(f"  Resultado {i}: Score={score:.3f}, Texto={relevant_text[:100]}...")
            
            return True
        else:
            logger.error(f"❌ Error en búsqueda: Status {response.status_code}")
            logger.error(f"Respuesta: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error probando búsqueda vectorial: {e}")
        return False

def test_openai_response():
    """Prueba la generación de respuestas con OpenAI"""
    logger.info("=== Probando generación de respuestas con OpenAI ===")
    
    try:
        # Verificar configuración de OpenAI
        openai_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        openai_key = os.getenv('AZURE_OPENAI_API_KEY')
        openai_deployment = os.getenv('AZURE_OPENAI_CHAT_DEPLOYMENT')
        
        logger.info(f"OpenAI Endpoint: {'✅ Configurado' if openai_endpoint else '❌ No configurado'}")
        logger.info(f"OpenAI Key: {'✅ Configurado' if openai_key else '❌ No configurado'}")
        logger.info(f"OpenAI Deployment: {'✅ Configurado' if openai_deployment else '❌ No configurado'}")
        
        if not all([openai_endpoint, openai_key, openai_deployment]):
            logger.warning("⚠️ OpenAI no está completamente configurado")
            return False
        
        # Importar OpenAI
        try:
            from openai import AzureOpenAI
        except ImportError:
            logger.error("❌ Biblioteca OpenAI no disponible")
            return False
        
        # Inicializar cliente
        client = AzureOpenAI(
            azure_endpoint=openai_endpoint,  # type: ignore
            api_key=openai_key,  # type: ignore
            api_version=os.getenv('AZURE_OPENAI_CHAT_API_VERSION', '2024-02-15-preview')
        )
        
        # Mensaje de prueba
        test_message = "Puedes darme el contacto de Daya"
        
        # Prompt del sistema
        system_prompt = """
Eres un asistente virtual de VEA Connect, una plataforma de gestión para organizaciones sin fines de lucro.
Tu función es ayudar a los usuarios con información sobre donaciones, eventos, documentos y servicios de la organización.
Responde de manera amigable y profesional en español. Mantén las respuestas concisas pero informativas.
Si no tienes información específica sobre algo, sugiere contactar al equipo de VEA Connect.
"""
        
        # Generar respuesta
        response = client.chat.completions.create(
            model=openai_deployment,  # type: ignore
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": test_message}
            ],
            max_tokens=200,
            temperature=0.7
        )
        
        if response.choices and response.choices[0].message and response.choices[0].message.content:
            ai_response = response.choices[0].message.content.strip()
            logger.info(f"✅ Respuesta generada exitosamente:")
            logger.info(f"  Usuario: {test_message}")
            logger.info(f"  Bot: {ai_response}")
            return True
        else:
            logger.error("❌ No se pudo generar respuesta")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error probando OpenAI: {e}")
        return False

def test_whatsapp_integration():
    """Prueba la integración completa de WhatsApp"""
    logger.info("=== Probando integración completa de WhatsApp ===")
    
    try:
        # Simular evento de WhatsApp
        test_event_data = {
            "content": "Puedes darme el contacto de Daya",
            "channelType": "whatsapp",
            "messageId": "test-message-id",
            "messageType": "text",
            "from": "5215519387611",
            "to": "test-recipient",
            "receivedTimestamp": datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"Evento de prueba: {json.dumps(test_event_data, indent=2)}")
        
        # Importar funciones de WhatsApp
        sys.path.append(os.path.dirname(__file__))
        from whatsapp_event_grid_trigger import _extract_message_data_tolerant, _get_rag_context, _generate_ai_response
        
        # Probar extracción de datos
        normalized = _extract_message_data_tolerant(test_event_data)
        if normalized:
            logger.info(f"✅ Extracción de datos exitosa: {normalized}")
            
            # Probar búsqueda RAG
            rag_context = _get_rag_context(normalized['text'])
            if rag_context:
                logger.info(f"✅ Contexto RAG encontrado: {len(rag_context)} caracteres")
            else:
                logger.info("⚠️ No se encontró contexto RAG")
            
            # Probar generación de respuesta
            ai_response = _generate_ai_response(normalized['text'], [], rag_context)
            logger.info(f"✅ Respuesta AI generada: {ai_response[:100]}...")
            
            return True
        else:
            logger.error("❌ Error en extracción de datos")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error en integración de WhatsApp: {e}")
        return False

def main():
    """Función principal de pruebas"""
    logger.info("🚀 Iniciando pruebas de WhatsApp con RAG y OpenAI")
    
    # Verificar variables de entorno
    logger.info("=== Verificando configuración ===")
    required_vars = [
        'AZURE_OPENAI_ENDPOINT',
        'AZURE_OPENAI_API_KEY', 
        'AZURE_OPENAI_CHAT_DEPLOYMENT',
        'SEARCH_SIMILAR_FUNCTION_URL'
    ]
    
    for var in required_vars:
        value = os.getenv(var)
        status = "✅ Configurado" if value else "❌ No configurado"
        logger.info(f"{var}: {status}")
    
    # Ejecutar pruebas
    tests = [
        ("Búsqueda Vectorial", test_rag_context),
        ("Generación OpenAI", test_openai_response),
        ("Integración WhatsApp", test_whatsapp_integration)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"Error en prueba {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumen de resultados
    logger.info(f"\n{'='*50}")
    logger.info("📊 RESUMEN DE PRUEBAS")
    logger.info("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\nResultado final: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        logger.info("🎉 ¡Todas las pruebas pasaron! El sistema está funcionando correctamente.")
    else:
        logger.warning("⚠️ Algunas pruebas fallaron. Revisa la configuración.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
