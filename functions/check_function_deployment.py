#!/usr/bin/env python3
"""
Script para verificar el estado del despliegue de las funciones de Azure.
"""

import os
import json
import requests
import logging
from typing import Dict, Any, List

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_function_list():
    """Verificar la lista de funciones disponibles."""
    logger.info("=== VERIFICANDO FUNCIONES DESPLEGADAS ===")
    
    function_app_url = os.getenv('FUNCTION_APP_URL')
    if not function_app_url:
        logger.error("FUNCTION_APP_URL no está configurada")
        return
    
    # Verificar funciones con diferentes rutas posibles
    function_paths = [
        # Rutas directas
        ('health', '/api/health'),
        ('get_stats', '/api/get_stats'),
        ('create_embedding', '/api/create_embedding'),
        ('search_similar', '/api/search_similar'),
        ('embeddings_health_check', '/api/embeddings_health_check'),
        ('test_sdk_function', '/api/test_sdk_function'),
        
        # Rutas alternativas
        ('health_alt', '/api/embeddings/health'),
        ('stats_alt', '/api/embeddings/stats'),
        ('create_alt', '/api/embeddings/create'),
        ('search_alt', '/api/embeddings/search'),
    ]
    
    working_functions = []
    failed_functions = []
    
    for func_name, path in function_paths:
        try:
            url = f"{function_app_url}{path}"
            logger.info(f"Probando: {func_name} en {path}")
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"  ✅ {func_name}: FUNCIONANDO (200)")
                working_functions.append(func_name)
            else:
                logger.warning(f"  ❌ {func_name}: ERROR ({response.status_code})")
                failed_functions.append(func_name)
                
        except Exception as e:
            logger.error(f"  ❌ {func_name}: EXCEPCIÓN - {e}")
            failed_functions.append(func_name)
    
    logger.info(f"\nResumen:")
    logger.info(f"Funciones funcionando: {len(working_functions)}")
    logger.info(f"Funciones fallando: {len(failed_functions)}")
    
    if working_functions:
        logger.info(f"Funciones OK: {', '.join(working_functions)}")
    if failed_functions:
        logger.info(f"Funciones con problemas: {', '.join(failed_functions)}")

def check_whatsapp_webhook():
    """Verificar si el webhook de WhatsApp está configurado."""
    logger.info("\n=== VERIFICANDO WEBHOOK DE WHATSAPP ===")
    
    # Verificar si la función de Event Grid está disponible
    function_app_url = os.getenv('FUNCTION_APP_URL')
    if not function_app_url:
        logger.error("FUNCTION_APP_URL no está configurada")
        return
    
    # La función de Event Grid no es accesible directamente via HTTP
    # pero podemos verificar si está en la lista de funciones
    try:
        # Intentar acceder a la función de Event Grid (debería fallar con 405 Method Not Allowed)
        url = f"{function_app_url}/api/whatsapp_event_grid_trigger"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 405:
            logger.info("✅ Función whatsapp_event_grid_trigger está desplegada (405 Method Not Allowed es esperado)")
        elif response.status_code == 404:
            logger.error("❌ Función whatsapp_event_grid_trigger NO está desplegada")
        else:
            logger.warning(f"⚠️ Función whatsapp_event_grid_trigger responde con código inesperado: {response.status_code}")
            
    except Exception as e:
        logger.error(f"❌ Error verificando función WhatsApp: {e}")

def check_event_grid_subscription():
    """Verificar la configuración de Event Grid."""
    logger.info("\n=== VERIFICANDO EVENT GRID ===")
    
    # Verificar variables de Event Grid
    event_grid_vars = [
        'ACS_EVENT_GRID_TOPIC_ENDPOINT',
        'ACS_EVENT_GRID_TOPIC_KEY'
    ]
    
    all_configured = True
    for var in event_grid_vars:
        value = os.getenv(var)
        if value:
            logger.info(f"✅ {var}: CONFIGURADA")
        else:
            logger.error(f"❌ {var}: NO CONFIGURADA")
            all_configured = False
    
    if all_configured:
        logger.info("✅ Todas las variables de Event Grid están configuradas")
        logger.info("⚠️ Verifica en el portal de Azure que la suscripción de Event Grid esté activa")
    else:
        logger.error("❌ Faltan variables de Event Grid")

def generate_deployment_instructions():
    """Generar instrucciones para el despliegue."""
    logger.info("\n=== INSTRUCCIONES DE DESPLIEGUE ===")
    
    instructions = [
        "1. **Verificar despliegue de funciones:**",
        "   - Ve al portal de Azure > Function App > Functions",
        "   - Confirma que todas las funciones estén listadas y habilitadas",
        "",
        "2. **Verificar Event Grid Subscription:**",
        "   - Ve a Azure Communication Services > Event Grid",
        "   - Confirma que la suscripción esté activa y apunte a tu función",
        "",
        "3. **Verificar variables de entorno en Azure:**",
        "   - Ve a Function App > Configuration",
        "   - Confirma que todas las variables de local.settings.json estén en Azure",
        "",
        "4. **Revisar logs de Application Insights:**",
        "   - Ve a Application Insights > Logs",
        "   - Busca por 'whatsapp_event_grid_trigger' para ver si hay eventos",
        "",
        "5. **Probar función manualmente:**",
        "   - Usa el script de prueba para enviar un evento de prueba",
        "",
        "6. **Verificar webhook de WhatsApp:**",
        "   - Confirma que el webhook esté configurado en WhatsApp Business API",
        "   - El endpoint debe ser: https://tu-function-app.azurewebsites.net/runtime/webhooks/eventgrid"
    ]
    
    for instruction in instructions:
        logger.info(instruction)

def main():
    """Función principal."""
    logger.info("Iniciando verificación de despliegue...")
    
    # Cargar variables de entorno
    try:
        with open('local.settings.json', 'r') as f:
            local_settings = json.load(f)
            for key, value in local_settings.get('Values', {}).items():
                os.environ[key] = value
        logger.info("Variables de entorno cargadas")
    except Exception as e:
        logger.warning(f"No se pudo cargar local.settings.json: {e}")
    
    # Ejecutar verificaciones
    check_function_list()
    check_whatsapp_webhook()
    check_event_grid_subscription()
    generate_deployment_instructions()
    
    logger.info("\n=== VERIFICACIÓN COMPLETADA ===")

if __name__ == "__main__":
    main()
