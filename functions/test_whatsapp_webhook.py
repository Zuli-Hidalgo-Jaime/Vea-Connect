#!/usr/bin/env python3
"""
Script para probar el webhook de WhatsApp y verificar que los eventos lleguen a la función.
"""

import os
import json
import requests
import logging
from datetime import datetime, timezone
from typing import Dict, Any

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_test_event():
    """Crear un evento de prueba para WhatsApp."""
    logger.info("Creando evento de prueba para WhatsApp...")
    
    # Evento de prueba basado en el esquema de ACS Advanced Messaging
    test_event = {
        "id": "test-event-id-123",
        "eventType": "Microsoft.Communication.AdvancedMessageReceived",
        "subject": "/subscriptions/test/resourceGroups/test/providers/Microsoft.Communication/communicationServices/test/advancedMessages",
        "data": {
            "messageId": "test-message-id-123",
            "from": "+5215574908943",  # Número de prueba
            "to": "+5215574908943",    # Tu número de WhatsApp
            "channelType": "whatsapp",
            "messageType": "text",
            "receivedTimestamp": datetime.now(timezone.utc).isoformat(),
            "message": {
                "text": {
                    "body": "Hola, esto es una prueba del bot de VEA Connect"
                }
            }
        },
        "eventTime": datetime.now(timezone.utc).isoformat(),
        "dataVersion": "1.0"
    }
    
    return test_event

def send_test_event_to_function(event_data: Dict[str, Any]):
    """Enviar evento de prueba a la función de Event Grid."""
    logger.info("Enviando evento de prueba a la función...")
    
    function_app_url = os.getenv('FUNCTION_APP_URL')
    if not function_app_url:
        logger.error("FUNCTION_APP_URL no está configurada")
        return False
    
    # URL del webhook de Event Grid
    webhook_url = f"{function_app_url}/runtime/webhooks/eventgrid"
    
    # Headers requeridos para Event Grid
    headers = {
        'Content-Type': 'application/json',
        'aeg-event-type': 'Notification',
        'aeg-delivery-count': '0',
        'aeg-data-version': '1.0'
    }
    
    # Payload para Event Grid
    payload = [event_data]
    
    try:
        logger.info(f"Enviando evento a: {webhook_url}")
        logger.info(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            webhook_url,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        logger.info(f"Respuesta del webhook: {response.status_code}")
        logger.info(f"Headers de respuesta: {dict(response.headers)}")
        
        if response.status_code == 200:
            logger.info("✅ Evento enviado exitosamente")
            return True
        else:
            logger.error(f"❌ Error enviando evento: {response.status_code}")
            logger.error(f"Respuesta: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Excepción enviando evento: {e}")
        return False

def test_function_directly():
    """Probar la función directamente (para debugging)."""
    logger.info("Probando función directamente...")
    
    function_app_url = os.getenv('FUNCTION_APP_URL')
    if not function_app_url:
        logger.error("FUNCTION_APP_URL no está configurada")
        return False
    
    # Crear evento de prueba
    test_event = create_test_event()
    
    # Simular llamada directa a la función (esto no funcionará para Event Grid triggers)
    try:
        url = f"{function_app_url}/api/whatsapp_event_grid_trigger"
        response = requests.post(url, json=test_event, timeout=10)
        
        logger.info(f"Respuesta directa: {response.status_code}")
        if response.status_code == 405:
            logger.info("✅ Función existe pero requiere Event Grid (405 Method Not Allowed es esperado)")
            return True
        else:
            logger.warning(f"Respuesta inesperada: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"Error probando función directamente: {e}")
        return False

def check_application_insights_logs():
    """Verificar si hay logs en Application Insights."""
    logger.info("Verificando logs de Application Insights...")
    
    app_insights_key = os.getenv('APPINSIGHTS_INSTRUMENTATIONKEY')
    if not app_insights_key:
        logger.error("APPINSIGHTS_INSTRUMENTATIONKEY no está configurada")
        return
    
    logger.info(f"Application Insights Key: {app_insights_key[:20]}...")
    logger.info("⚠️ Para ver logs en tiempo real, ve al portal de Azure:")
    logger.info("1. Ve a Application Insights")
    logger.info("2. Ve a 'Logs'")
    logger.info("3. Ejecuta esta consulta:")
    logger.info("   traces | where timestamp > ago(1h) | where customDimensions contains 'whatsapp'")
    logger.info("   traces | where timestamp > ago(1h) | where message contains 'Event received'")

def main():
    """Función principal de prueba."""
    logger.info("=== PRUEBA DE WEBHOOK DE WHATSAPP ===")
    
    # Cargar variables de entorno
    try:
        with open('local.settings.json', 'r') as f:
            local_settings = json.load(f)
            for key, value in local_settings.get('Values', {}).items():
                os.environ[key] = value
        logger.info("Variables de entorno cargadas")
    except Exception as e:
        logger.warning(f"No se pudo cargar local.settings.json: {e}")
    
    # Verificar configuración
    function_app_url = os.getenv('FUNCTION_APP_URL')
    if not function_app_url:
        logger.error("FUNCTION_APP_URL no está configurada")
        return
    
    logger.info(f"Function App URL: {function_app_url}")
    
    # Probar función directamente
    test_function_directly()
    
    # Crear y enviar evento de prueba
    test_event = create_test_event()
    success = send_test_event_to_function(test_event)
    
    if success:
        logger.info("✅ Evento de prueba enviado exitosamente")
        logger.info("Ahora verifica los logs en Application Insights")
    else:
        logger.error("❌ Error enviando evento de prueba")
    
    # Mostrar instrucciones para verificar logs
    check_application_insights_logs()
    
    logger.info("\n=== PRUEBA COMPLETADA ===")
    logger.info("Si no ves logs, verifica:")
    logger.info("1. Que la función esté desplegada correctamente")
    logger.info("2. Que Event Grid esté configurado")
    logger.info("3. Que las variables de entorno estén en Azure")
    logger.info("4. Los logs de Application Insights en el portal de Azure")

if __name__ == "__main__":
    main()
