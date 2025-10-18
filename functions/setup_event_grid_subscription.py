#!/usr/bin/env python3
"""
Script para configurar la suscripción de Event Grid para WhatsApp.
"""

import os
import json
import logging
from typing import Dict, Any

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_event_grid_subscription():
    """Configurar la suscripción de Event Grid para WhatsApp."""
    logger.info("=== CONFIGURANDO EVENT GRID SUBSCRIPTION ===")
    
    # Cargar variables de entorno
    try:
        with open('local.settings.json', 'r') as f:
            local_settings = json.load(f)
            for key, value in local_settings.get('Values', {}).items():
                os.environ[key] = value
        logger.info("Variables de entorno cargadas")
    except Exception as e:
        logger.warning(f"No se pudo cargar local.settings.json: {e}")
    
    # Obtener configuración
    function_app_url = os.getenv('FUNCTION_APP_URL')
    acs_endpoint = os.getenv('ACS_EVENT_GRID_TOPIC_ENDPOINT')
    acs_key = os.getenv('ACS_EVENT_GRID_TOPIC_KEY')
    
    if not all([function_app_url, acs_endpoint, acs_key]):
        logger.error("Faltan variables de configuración para Event Grid")
        return False
    
    logger.info(f"Function App URL: {function_app_url}")
    logger.info(f"ACS Endpoint: {acs_endpoint}")
    
    # URL del webhook de Event Grid
    webhook_url = f"{function_app_url}/runtime/webhooks/eventgrid"
    logger.info(f"Webhook URL: {webhook_url}")
    
    # Instrucciones para configurar Event Grid
    logger.info("\n=== INSTRUCCIONES PARA CONFIGURAR EVENT GRID ===")
    
    instructions = [
        "1. Ve al portal de Azure: https://portal.azure.com",
        "2. Busca tu Azure Communication Service",
        "3. Ve a 'Event Grid' en el menú lateral",
        "4. Haz clic en '+ Event Subscription'",
        "5. Configura la suscripción:",
        "   - Name: whatsapp-events",
        "   - Event Schema: Event Grid Schema",
        "   - System Topic Name: (dejar por defecto)",
        "   - Event Types: Microsoft.Communication.AdvancedMessageReceived",
        "   - Endpoint Type: Web Hook",
        "   - Endpoint: " + webhook_url,
        "6. Haz clic en 'Create'",
        "",
        "ALTERNATIVA: Usar Azure CLI",
        "Ejecuta este comando:",
        f"az eventgrid system-topic event-subscription create --name whatsapp-events --resource-group rg-vea-connect-dev --system-topic-name acs-veaconnect-01 --endpoint {webhook_url} --included-event-types Microsoft.Communication.AdvancedMessageReceived"
    ]
    
    for instruction in instructions:
        logger.info(instruction)
    
    return True

def verify_webhook_endpoint():
    """Verificar que el webhook endpoint esté accesible."""
    logger.info("\n=== VERIFICANDO WEBHOOK ENDPOINT ===")
    
    function_app_url = os.getenv('FUNCTION_APP_URL')
    if not function_app_url:
        logger.error("FUNCTION_APP_URL no está configurada")
        return False
    
    webhook_url = f"{function_app_url}/runtime/webhooks/eventgrid"
    
    try:
        import requests
        
        # Probar el endpoint del webhook
        response = requests.get(webhook_url, timeout=10)
        
        if response.status_code == 200:
            logger.info("✅ Webhook endpoint está accesible")
            return True
        elif response.status_code == 401:
            logger.warning("⚠️ Webhook endpoint requiere autenticación (esto es normal)")
            return True
        else:
            logger.error(f"❌ Webhook endpoint no está accesible: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error verificando webhook: {e}")
        return False

def test_event_grid_connection():
    """Probar la conexión con Event Grid."""
    logger.info("\n=== PROBANDO CONEXIÓN CON EVENT GRID ===")
    
    acs_endpoint = os.getenv('ACS_EVENT_GRID_TOPIC_ENDPOINT')
    acs_key = os.getenv('ACS_EVENT_GRID_TOPIC_KEY')
    
    if not all([acs_endpoint, acs_key]):
        logger.error("Faltan variables de Event Grid")
        return False
    
    try:
        import requests
        
        # Probar la conexión con ACS Event Grid
        test_url = f"{acs_endpoint}/api/events"
        headers = {
            'aeg-sas-key': acs_key,
            'Content-Type': 'application/json'
        }
        
        # Enviar un evento de prueba
        test_event = {
            "id": "test-event-id",
            "eventType": "Microsoft.Communication.AdvancedMessageReceived",
            "subject": "/subscriptions/test/resourceGroups/test/providers/Microsoft.Communication/communicationServices/test/advancedMessages",
            "data": {
                "messageId": "test-message-id",
                "from": "+1234567890",
                "to": "+1234567890",
                "channelType": "whatsapp",
                "messageType": "text",
                "message": {
                    "text": {
                        "body": "Test message"
                    }
                }
            },
            "eventTime": "2025-08-12T00:00:00Z",
            "dataVersion": "1.0"
        }
        
        response = requests.post(test_url, json=[test_event], headers=headers, timeout=10)
        
        if response.status_code in [200, 202]:
            logger.info("✅ Conexión con Event Grid exitosa")
            return True
        else:
            logger.warning(f"⚠️ Respuesta inesperada de Event Grid: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error probando Event Grid: {e}")
        return False

def generate_manual_setup_instructions():
    """Generar instrucciones manuales para configurar Event Grid."""
    logger.info("\n=== INSTRUCCIONES MANUALES ===")
    
    function_app_url = os.getenv('FUNCTION_APP_URL')
    webhook_url = f"{function_app_url}/runtime/webhooks/eventgrid"
    
    instructions = [
        "CONFIGURACIÓN MANUAL DE EVENT GRID:",
        "",
        "1. Ve a Azure Portal > Azure Communication Services",
        "2. Selecciona tu servicio: acs-veaconnect-01",
        "3. Ve a 'Event Grid' en el menú lateral",
        "4. Haz clic en '+ Event Subscription'",
        "5. Completa el formulario:",
        "   - Subscription: VEACONNECT@onesec.mx - MPN",
        "   - Resource Group: rg-vea-connect-dev",
        "   - System Topic Name: acs-veaconnect-01",
        "   - Event Subscription Name: whatsapp-events",
        "   - Event Schema: Event Grid Schema",
        "   - Event Types: Microsoft.Communication.AdvancedMessageReceived",
        "   - Endpoint Type: Web Hook",
        "   - Endpoint URL: " + webhook_url,
        "6. Haz clic en 'Create'",
        "",
        "VERIFICACIÓN:",
        "1. Ve a tu Function App en Azure Portal",
        "2. Ve a 'Functions' > 'whatsapp_event_grid_trigger'",
        "3. Ve a 'Monitor' para ver los logs",
        "4. Envía un mensaje de WhatsApp para probar",
        "",
        "COMANDO AZURE CLI ALTERNATIVO:",
        f"az eventgrid system-topic event-subscription create --name whatsapp-events --resource-group rg-vea-connect-dev --system-topic-name acs-veaconnect-01 --endpoint {webhook_url} --included-event-types Microsoft.Communication.AdvancedMessageReceived"
    ]
    
    for instruction in instructions:
        logger.info(instruction)

def main():
    """Función principal."""
    logger.info("Iniciando configuración de Event Grid...")
    
    # Verificar configuración
    setup_event_grid_subscription()
    
    # Verificar webhook
    verify_webhook_endpoint()
    
    # Probar conexión
    test_event_grid_connection()
    
    # Generar instrucciones
    generate_manual_setup_instructions()
    
    logger.info("\n=== CONFIGURACIÓN COMPLETADA ===")
    logger.info("Sigue las instrucciones manuales para configurar Event Grid")
    logger.info("Una vez configurado, deberías ver logs cuando envíes mensajes de WhatsApp")

if __name__ == "__main__":
    main()
