#!/usr/bin/env python3
"""
Script para probar el SDK de Azure Communication Messages en Azure Functions
"""
import logging
import os
import sys

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_sdk_availability():
    """Prueba la disponibilidad del SDK en Azure Functions"""
    logger.info("=== PRUEBA DE SDK EN AZURE FUNCTIONS ===")
    
    # Verificar Python path
    logger.info(f"Python path: {sys.path}")
    logger.info(f"Python version: {sys.version}")
    
    # Verificar módulos instalados
    try:
        import pkg_resources
        installed_packages = [d.project_name for d in pkg_resources.working_set]
        azure_packages = [pkg for pkg in installed_packages if 'azure' in pkg.lower()]
        logger.info(f"Paquetes Azure instalados: {azure_packages}")
    except Exception as e:
        logger.error(f"Error verificando paquetes: {e}")
    
    # Probar importación del SDK
    logger.info("Probando importación del SDK...")
    
    try:
        import azure.communication.messages
        logger.info("✓ azure.communication.messages importado correctamente")
        
        # Verificar versión
        version = getattr(azure.communication.messages, '__version__', 'Desconocida')
        logger.info(f"Versión del SDK: {version}")
        
    except ImportError as e:
        logger.error(f"✗ Error importando azure.communication.messages: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ Error inesperado: {e}")
        return False
    
    # Probar importación de clases específicas
    try:
        from azure.communication.messages import NotificationMessagesClient
        logger.info("✓ NotificationMessagesClient importado correctamente")
    except ImportError as e:
        logger.error(f"✗ Error importando NotificationMessagesClient: {e}")
        return False
    
    try:
        from azure.communication.messages.models import TextNotificationContent
        logger.info("✓ TextNotificationContent importado correctamente")
    except ImportError as e:
        logger.error(f"✗ Error importando TextNotificationContent: {e}")
        return False
    
    # Probar creación de cliente
    try:
        # Usar connection string de prueba
        conn_string = os.getenv('ACS_CONNECTION_STRING')
        if conn_string:
            client = NotificationMessagesClient.from_connection_string(conn_string)
            logger.info("✓ Cliente creado correctamente")
        else:
            logger.warning("ACS_CONNECTION_STRING no disponible")
    except Exception as e:
        logger.error(f"✗ Error creando cliente: {e}")
        return False
    
    logger.info("=== SDK DISPONIBLE Y FUNCIONAL ===")
    return True

def test_message_sending():
    """Prueba el envío de mensajes usando el SDK"""
    logger.info("=== PRUEBA DE ENVÍO DE MENSAJES ===")
    
    try:
        from azure.communication.messages import NotificationMessagesClient
        from azure.communication.messages.models import TextNotificationContent
        
        # Obtener configuración
        conn_string = os.getenv('ACS_CONNECTION_STRING')
        channel_id = os.getenv('WHATSAPP_CHANNEL_ID_GUID')
        phone_number = os.getenv('ACS_PHONE_NUMBER')
        
        if not all([conn_string, channel_id, phone_number]):
            logger.error("Faltan variables de entorno requeridas")
            return False
        
        logger.info(f"Connection String: {'SET' if conn_string else 'NOT SET'}")
        logger.info(f"Channel ID: {channel_id}")
        logger.info(f"Phone Number: {phone_number}")
        
        # Crear cliente
        client = NotificationMessagesClient.from_connection_string(conn_string)
        
        # Crear mensaje de prueba
        text_content = TextNotificationContent(
            channel_registration_id=channel_id,
            to=["+5215519387611"],  # Número de prueba
            content="Prueba desde Azure Functions - SDK funcionando correctamente!"
        )
        
        # Enviar mensaje
        logger.info("Enviando mensaje de prueba...")
        message_responses = client.send(text_content)
        response = message_responses.receipts[0]
        
        if response is not None:
            logger.info(f"✓ Mensaje enviado exitosamente")
            logger.info(f"Message ID: {response.message_id}")
            logger.info(f"To: {response.to}")
            return True
        else:
            logger.error("✗ El mensaje falló al enviar")
            return False
            
    except Exception as e:
        logger.error(f"✗ Error en prueba de envío: {e}")
        return False

if __name__ == "__main__":
    logger.info("Iniciando pruebas de SDK en Azure Functions...")
    
    # Probar disponibilidad del SDK
    sdk_available = test_sdk_availability()
    
    if sdk_available:
        # Probar envío de mensajes
        message_sent = test_message_sending()
        
        if message_sent:
            logger.info("🎉 TODAS LAS PRUEBAS EXITOSAS - SDK FUNCIONANDO CORRECTAMENTE")
        else:
            logger.error("❌ Error en envío de mensajes")
    else:
        logger.error("❌ SDK NO DISPONIBLE")
    
    logger.info("Pruebas completadas")
