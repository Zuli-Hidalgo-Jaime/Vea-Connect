#!/usr/bin/env python3
"""
Script de diagnóstico para verificar el estado de las funciones de Azure y el problema de logging.
"""

import os
import json
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_function_app_status():
    """Verificar el estado de la Function App en Azure."""
    logger.info("=== DIAGNÓSTICO DE FUNCIONES AZURE ===")
    
    # Obtener configuración desde variables de entorno
    function_app_url = os.getenv('FUNCTION_APP_URL')
    if not function_app_url:
        logger.error("FUNCTION_APP_URL no está configurada")
        return False
    
    logger.info(f"Function App URL: {function_app_url}")
    
    # Verificar funciones disponibles
    functions = [
        'health',
        'get_stats', 
        'create_embedding',
        'search_similar',
        'embeddings_health_check',
        'test_sdk_function'
    ]
    
    logger.info("Verificando funciones disponibles...")
    
    for func_name in functions:
        try:
            url = f"{function_app_url}/api/{func_name}"
            logger.info(f"Probando función: {func_name}")
            
            response = requests.get(url, timeout=10)
            logger.info(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    logger.info(f"  Response: {json.dumps(data, indent=2)[:200]}...")
                except:
                    logger.info(f"  Response: {response.text[:200]}...")
            else:
                logger.warning(f"  Error: {response.text[:200]}...")
                
        except Exception as e:
            logger.error(f"  Error probando {func_name}: {e}")
    
    return True

def check_whatsapp_configuration():
    """Verificar la configuración de WhatsApp."""
    logger.info("\n=== CONFIGURACIÓN DE WHATSAPP ===")
    
    # Variables críticas para WhatsApp
    whatsapp_vars = [
        'ACS_CONNECTION_STRING',
        'ACS_PHONE_NUMBER', 
        'WHATSAPP_CHANNEL_ID_GUID',
        'WHATSAPP_ACCESS_TOKEN',
        'WHATSAPP_DEBUG',
        'E2E_DEBUG'
    ]
    
    for var in whatsapp_vars:
        value = os.getenv(var)
        if value:
            if 'KEY' in var or 'TOKEN' in var or 'SECRET' in var:
                logger.info(f"{var}: {'CONFIGURADA'} - Valor: {value[:10]}...")
            else:
                logger.info(f"{var}: {'CONFIGURADA'} - Valor: {value}")
        else:
            logger.warning(f"{var}: NO CONFIGURADA")
    
    # Verificar configuración de Event Grid
    logger.info("\n--- Configuración de Event Grid ---")
    event_grid_vars = [
        'ACS_EVENT_GRID_TOPIC_ENDPOINT',
        'ACS_EVENT_GRID_TOPIC_KEY'
    ]
    
    for var in event_grid_vars:
        value = os.getenv(var)
        if value:
            if 'KEY' in var:
                logger.info(f"{var}: {'CONFIGURADA'} - Valor: {value[:10]}...")
            else:
                logger.info(f"{var}: {'CONFIGURADA'} - Valor: {value}")
        else:
            logger.warning(f"{var}: NO CONFIGURADA")

def check_application_insights():
    """Verificar la configuración de Application Insights."""
    logger.info("\n=== APPLICATION INSIGHTS ===")
    
    app_insights_vars = [
        'APPINSIGHTS_INSTRUMENTATIONKEY',
        'APPLICATIONINSIGHTS_CONNECTION_STRING'
    ]
    
    for var in app_insights_vars:
        value = os.getenv(var)
        if value:
            logger.info(f"{var}: {'CONFIGURADA'} - Valor: {value[:20]}...")
        else:
            logger.warning(f"{var}: NO CONFIGURADA")

def check_azure_search():
    """Verificar la configuración de Azure Search."""
    logger.info("\n=== AZURE SEARCH ===")
    
    search_vars = [
        'AZURE_SEARCH_ENDPOINT',
        'AZURE_SEARCH_KEY',
        'AZURE_SEARCH_INDEX_NAME'
    ]
    
    for var in search_vars:
        value = os.getenv(var)
        if value:
            if 'KEY' in var:
                logger.info(f"{var}: {'CONFIGURADA'} - Valor: {value[:10]}...")
            else:
                logger.info(f"{var}: {'CONFIGURADA'} - Valor: {value}")
        else:
            logger.warning(f"{var}: NO CONFIGURADA")

def check_openai_configuration():
    """Verificar la configuración de OpenAI."""
    logger.info("\n=== OPENAI CONFIGURACIÓN ===")
    
    openai_vars = [
        'AZURE_OPENAI_ENDPOINT',
        'AZURE_OPENAI_API_KEY',
        'AZURE_OPENAI_CHAT_DEPLOYMENT',
        'AZURE_OPENAI_CHAT_API_VERSION'
    ]
    
    for var in openai_vars:
        value = os.getenv(var)
        if value:
            if 'KEY' in var:
                logger.info(f"{var}: {'CONFIGURADA'} - Valor: {value[:10]}...")
            else:
                logger.info(f"{var}: {'CONFIGURADA'} - Valor: {value}")
        else:
            logger.warning(f"{var}: NO CONFIGURADA")

def generate_recommendations():
    """Generar recomendaciones para solucionar el problema de logging."""
    logger.info("\n=== RECOMENDACIONES ===")
    
    recommendations = [
        "1. Verificar que la función whatsapp_event_grid_trigger esté desplegada correctamente",
        "2. Revisar los logs de Application Insights en el portal de Azure",
        "3. Verificar que Event Grid esté configurado para enviar eventos a la función",
        "4. Comprobar que el webhook de WhatsApp esté configurado correctamente",
        "5. Verificar que las variables de entorno estén configuradas en Azure",
        "6. Revisar el Activity Log en el portal de Azure para ver si hay errores",
        "7. Probar la función manualmente enviando un evento de prueba",
        "8. Verificar que el SDK de Azure Communication esté instalado correctamente"
    ]
    
    for rec in recommendations:
        logger.info(rec)

def main():
    """Función principal del diagnóstico."""
    logger.info("Iniciando diagnóstico de funciones Azure...")
    
    # Cargar variables de entorno desde local.settings.json si existe
    try:
        with open('local.settings.json', 'r') as f:
            local_settings = json.load(f)
            for key, value in local_settings.get('Values', {}).items():
                os.environ[key] = value
        logger.info("Variables de entorno cargadas desde local.settings.json")
    except Exception as e:
        logger.warning(f"No se pudo cargar local.settings.json: {e}")
    
    # Ejecutar diagnósticos
    check_function_app_status()
    check_whatsapp_configuration()
    check_application_insights()
    check_azure_search()
    check_openai_configuration()
    generate_recommendations()
    
    logger.info("\n=== DIAGNÓSTICO COMPLETADO ===")
    logger.info("Revisa las recomendaciones anteriores para solucionar el problema de logging.")

if __name__ == "__main__":
    main()
