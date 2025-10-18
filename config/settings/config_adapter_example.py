"""
Ejemplo de Uso del Adaptador de Configuración - VEA Connect

Este archivo demuestra cómo usar el adaptador de configuración unificado
en nuevos módulos sin afectar el código existente.

IMPORTANTE: Este es solo un ejemplo. No usar en producción.
"""

import logging
from config.settings.config_adapter import (
    # Storage
    get_storage_account_name,
    get_storage_account_key,
    get_storage_container,
    get_storage_connection_string,
    
    # Search
    get_search_service,
    get_search_key,
    get_search_index,
    
    # OpenAI
    get_openai_endpoint,
    get_openai_api_key,
    get_openai_chat_deployment,
    
    # Vision
    get_vision_endpoint,
    get_vision_key,
    
    # ACS
    get_acs_connection_string,
    get_acs_whatsapp_api_key,
    
    # Database
    get_database_url,
    get_postgresql_name,
    
    # Functions
    get_function_app_url,
    get_function_app_key,
    
    # Utilities
    get_config_status,
    validate_required_configs,
    is_config_adapter_enabled
)

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def example_storage_configuration():
    """Ejemplo de configuración de Azure Storage"""
    logger.info("=== Configuración de Azure Storage ===")
    
    # Obtener configuración usando el adaptador
    account_name = get_storage_account_name()
    account_key = get_storage_account_key()
    container = get_storage_container()
    connection_string = get_storage_connection_string()
    
    # Mostrar estado (sin exponer valores sensibles)
    logger.info(f"Storage Account Name: {'SET' if account_name else 'NOT SET'}")
    logger.info(f"Storage Account Key: {'SET' if account_key else 'NOT SET'}")
    logger.info(f"Storage Container: {'SET' if container else 'NOT SET'}")
    logger.info(f"Connection String: {'SET' if connection_string else 'NOT SET'}")
    
    return {
        'account_name': account_name,
        'account_key': account_key,
        'container': container,
        'connection_string': connection_string
    }


def example_search_configuration():
    """Ejemplo de configuración de Azure AI Search"""
    logger.info("=== Configuración de Azure AI Search ===")
    
    service = get_search_service()
    key = get_search_key()
    index = get_search_index()
    
    logger.info(f"Search Service: {'SET' if service else 'NOT SET'}")
    logger.info(f"Search Key: {'SET' if key else 'NOT SET'}")
    logger.info(f"Search Index: {'SET' if index else 'NOT SET'}")
    
    return {
        'service': service,
        'key': key,
        'index': index
    }


def example_openai_configuration():
    """Ejemplo de configuración de Azure OpenAI"""
    logger.info("=== Configuración de Azure OpenAI ===")
    
    endpoint = get_openai_endpoint()
    api_key = get_openai_api_key()
    chat_deployment = get_openai_chat_deployment()
    
    logger.info(f"OpenAI Endpoint: {'SET' if endpoint else 'NOT SET'}")
    logger.info(f"OpenAI API Key: {'SET' if api_key else 'NOT SET'}")
    logger.info(f"Chat Deployment: {'SET' if chat_deployment else 'NOT SET'}")
    
    return {
        'endpoint': endpoint,
        'api_key': api_key,
        'chat_deployment': chat_deployment
    }


def example_vision_configuration():
    """Ejemplo de configuración de Azure Computer Vision"""
    logger.info("=== Configuración de Azure Computer Vision ===")
    
    endpoint = get_vision_endpoint()
    key = get_vision_key()
    
    logger.info(f"Vision Endpoint: {'SET' if endpoint else 'NOT SET'}")
    logger.info(f"Vision Key: {'SET' if key else 'NOT SET'}")
    
    return {
        'endpoint': endpoint,
        'key': key
    }


def example_acs_configuration():
    """Ejemplo de configuración de Azure Communication Services"""
    logger.info("=== Configuración de Azure Communication Services ===")
    
    connection_string = get_acs_connection_string()
    whatsapp_api_key = get_acs_whatsapp_api_key()
    
    logger.info(f"ACS Connection String: {'SET' if connection_string else 'NOT SET'}")
    logger.info(f"WhatsApp API Key: {'SET' if whatsapp_api_key else 'NOT SET'}")
    
    return {
        'connection_string': connection_string,
        'whatsapp_api_key': whatsapp_api_key
    }


def example_database_configuration():
    """Ejemplo de configuración de Base de Datos"""
    logger.info("=== Configuración de Base de Datos ===")
    
    database_url = get_database_url()
    postgresql_name = get_postgresql_name()
    
    logger.info(f"Database URL: {'SET' if database_url else 'NOT SET'}")
    logger.info(f"PostgreSQL Name: {'SET' if postgresql_name else 'NOT SET'}")
    
    return {
        'database_url': database_url,
        'postgresql_name': postgresql_name
    }


def example_function_configuration():
    """Ejemplo de configuración de Azure Functions"""
    logger.info("=== Configuración de Azure Functions ===")
    
    function_url = get_function_app_url()
    function_key = get_function_app_key()
    
    logger.info(f"Function App URL: {'SET' if function_url else 'NOT SET'}")
    logger.info(f"Function App Key: {'SET' if function_key else 'NOT SET'}")
    
    return {
        'function_url': function_url,
        'function_key': function_key
    }


def example_validation():
    """Ejemplo de validación de configuraciones requeridas"""
    logger.info("=== Validación de Configuraciones ===")
    
    # Validar configuraciones requeridas para un módulo específico
    required_configs = [
        'get_storage_account_name',
        'get_storage_account_key',
        'get_storage_container'
    ]
    
    validation_result = validate_required_configs(required_configs)
    
    for config_name, result in validation_result.items():
        status = result['status']
        available = result['available']
        logger.info(f"{config_name}: {status} ({'Available' if available else 'Not Available'})")
    
    return validation_result


def example_config_status():
    """Ejemplo de obtención del estado general de configuración"""
    logger.info("=== Estado General de Configuración ===")
    
    status = get_config_status()
    
    for config_name, config_status in status.items():
        logger.info(f"{config_name}: {config_status}")
    
    return status


def example_feature_flag():
    """Ejemplo de verificación del feature flag"""
    logger.info("=== Feature Flag del Adaptador ===")
    
    enabled = is_config_adapter_enabled()
    logger.info(f"Config Adapter Enabled: {enabled}")
    
    if enabled:
        logger.info("El adaptador de configuración está habilitado")
    else:
        logger.info("El adaptador de configuración está deshabilitado (comportamiento por defecto)")
    
    return enabled


def run_all_examples():
    """Ejecutar todos los ejemplos"""
    logger.info("🚀 Iniciando ejemplos del Adaptador de Configuración")
    logger.info("=" * 60)
    
    # Verificar feature flag
    example_feature_flag()
    logger.info("")
    
    # Ejemplos de configuración por servicio
    example_storage_configuration()
    logger.info("")
    
    example_search_configuration()
    logger.info("")
    
    example_openai_configuration()
    logger.info("")
    
    example_vision_configuration()
    logger.info("")
    
    example_acs_configuration()
    logger.info("")
    
    example_database_configuration()
    logger.info("")
    
    example_function_configuration()
    logger.info("")
    
    # Ejemplos de utilidades
    example_validation()
    logger.info("")
    
    example_config_status()
    logger.info("")
    
    logger.info("✅ Ejemplos completados")


if __name__ == "__main__":
    # Solo ejecutar si el adaptador está habilitado
    if is_config_adapter_enabled():
        run_all_examples()
    else:
        logger.warning("El adaptador de configuración está deshabilitado.")
        logger.info("Para habilitarlo, establece CONFIG_ADAPTER_ENABLED=True")
        logger.info("Ejecutando solo verificación de feature flag...")
        example_feature_flag()
