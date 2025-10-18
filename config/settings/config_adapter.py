"""
Adaptador de Configuración Unificado - VEA Connect

Este módulo proporciona una capa de abstracción unificada para acceder a la configuración
de servicios de Azure y otros recursos, con precedencia clara y logging seguro.

Precedencia: os.environ → settings.<AZURE_*> → settings.<BLOB_*> → default None

Feature flag: CONFIG_ADAPTER_ENABLED (por defecto False)
"""

import os
import logging
from typing import Optional, Union
from django.conf import settings

# Configurar logger para el adaptador
logger = logging.getLogger(__name__)

# Feature flag global
CONFIG_ADAPTER_ENABLED = getattr(settings, 'CONFIG_ADAPTER_ENABLED', False)


def _get_config_with_precedence(
    env_var: str,
    azure_setting: str,
    legacy_setting: Optional[str] = None,
    default: Optional[str] = None
) -> Optional[str]:
    """
    Obtiene configuración con precedencia: ENV > AZURE_SETTING > LEGACY_SETTING > DEFAULT
    
    Args:
        env_var: Variable de entorno
        azure_setting: Variable de settings AZURE_*
        legacy_setting: Variable de settings BLOB_* (opcional)
        default: Valor por defecto (opcional)
    
    Returns:
        Valor de configuración o None
    """
    # 1. Variable de entorno (máxima prioridad)
    env_value = os.environ.get(env_var)
    if env_value:
        logger.debug(f"Configuración obtenida desde ENV: {env_var}")
        return env_value
    
    # 2. Variable de settings AZURE_*
    azure_value = getattr(settings, azure_setting, None)
    if azure_value:
        logger.debug(f"Configuración obtenida desde SETTINGS: {azure_setting}")
        return azure_value
    
    # 3. Variable de settings BLOB_* (legacy)
    if legacy_setting:
        legacy_value = getattr(settings, legacy_setting, None)
        if legacy_value:
            logger.debug(f"Configuración obtenida desde LEGACY: {legacy_setting}")
            return legacy_value
    
    # 4. Valor por defecto
    if default is not None:
        logger.debug(f"Configuración obtenida desde DEFAULT: {default}")
        return default
    
    logger.debug(f"Configuración no encontrada para: {env_var}")
    return None


# =============================================================================
# FUNCIONES DE CONFIGURACIÓN DE STORAGE
# =============================================================================

def get_storage_account_name() -> Optional[str]:
    """Obtiene el nombre de la cuenta de Azure Storage"""
    return _get_config_with_precedence(
        env_var='AZURE_STORAGE_ACCOUNT_NAME',
        azure_setting='AZURE_STORAGE_ACCOUNT_NAME',
        legacy_setting='BLOB_ACCOUNT_NAME'
    )


def get_storage_account_key() -> Optional[str]:
    """Obtiene la clave de la cuenta de Azure Storage"""
    return _get_config_with_precedence(
        env_var='AZURE_STORAGE_ACCOUNT_KEY',
        azure_setting='AZURE_STORAGE_ACCOUNT_KEY',
        legacy_setting='BLOB_ACCOUNT_KEY'
    )


def get_storage_container() -> Optional[str]:
    """Obtiene el nombre del contenedor de Azure Storage"""
    return _get_config_with_precedence(
        env_var='AZURE_CONTAINER',
        azure_setting='AZURE_CONTAINER',
        legacy_setting='BLOB_CONTAINER_NAME',
        default='documents'
    )


def get_storage_connection_string() -> Optional[str]:
    """Obtiene la connection string de Azure Storage"""
    return _get_config_with_precedence(
        env_var='AZURE_STORAGE_CONNECTION_STRING',
        azure_setting='AZURE_STORAGE_CONNECTION_STRING'
    )


# =============================================================================
# FUNCIONES DE CONFIGURACIÓN DE SEARCH
# =============================================================================

def get_search_service() -> Optional[str]:
    """Obtiene el endpoint del servicio de Azure AI Search"""
    return _get_config_with_precedence(
        env_var='AZURE_SEARCH_ENDPOINT',
        azure_setting='AZURE_SEARCH_ENDPOINT'
    )


def get_search_key() -> Optional[str]:
    """Obtiene la clave de API de Azure AI Search"""
    return _get_config_with_precedence(
        env_var='AZURE_SEARCH_API_KEY',
        azure_setting='AZURE_SEARCH_API_KEY'
    )


def get_search_index() -> Optional[str]:
    """Obtiene el nombre del índice de Azure AI Search"""
    return _get_config_with_precedence(
        env_var='AZURE_SEARCH_INDEX_NAME',
        azure_setting='AZURE_SEARCH_INDEX_NAME',
        default='vea-connect-index'
    )


# =============================================================================
# FUNCIONES DE CONFIGURACIÓN DE OPENAI
# =============================================================================

def get_openai_endpoint() -> Optional[str]:
    """Obtiene el endpoint de Azure OpenAI"""
    return _get_config_with_precedence(
        env_var='AZURE_OPENAI_ENDPOINT',
        azure_setting='AZURE_OPENAI_ENDPOINT'
    )


def get_openai_api_key() -> Optional[str]:
    """Obtiene la clave de API de Azure OpenAI"""
    return _get_config_with_precedence(
        env_var='AZURE_OPENAI_API_KEY',
        azure_setting='AZURE_OPENAI_API_KEY'
    )


def get_openai_chat_deployment() -> Optional[str]:
    """Obtiene el deployment de chat de Azure OpenAI"""
    return _get_config_with_precedence(
        env_var='AZURE_OPENAI_CHAT_DEPLOYMENT',
        azure_setting='AZURE_OPENAI_CHAT_DEPLOYMENT',
        default='gpt-35-turbo'
    )


def get_openai_embeddings_deployment() -> Optional[str]:
    """Obtiene el deployment de embeddings de Azure OpenAI"""
    return _get_config_with_precedence(
        env_var='AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT',
        azure_setting='AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT',
        default='text-embedding-ada-002'
    )


def get_openai_chat_api_version() -> Optional[str]:
    """Obtiene la versión de API de chat de Azure OpenAI"""
    return _get_config_with_precedence(
        env_var='AZURE_OPENAI_CHAT_API_VERSION',
        azure_setting='AZURE_OPENAI_CHAT_API_VERSION',
        default='2025-01-01-preview'
    )


def get_openai_embeddings_api_version() -> Optional[str]:
    """Obtiene la versión de API de embeddings de Azure OpenAI"""
    return _get_config_with_precedence(
        env_var='AZURE_OPENAI_EMBEDDINGS_API_VERSION',
        azure_setting='AZURE_OPENAI_EMBEDDINGS_API_VERSION',
        default='2023-05-15'
    )


# =============================================================================
# FUNCIONES DE CONFIGURACIÓN DE VISION
# =============================================================================

def get_vision_endpoint() -> Optional[str]:
    """Obtiene el endpoint de Azure Computer Vision"""
    return _get_config_with_precedence(
        env_var='VISION_ENDPOINT',
        azure_setting='VISION_ENDPOINT'
    )


def get_vision_key() -> Optional[str]:
    """Obtiene la clave de API de Azure Computer Vision"""
    return _get_config_with_precedence(
        env_var='VISION_KEY',
        azure_setting='VISION_KEY'
    )


# =============================================================================
# FUNCIONES DE CONFIGURACIÓN DE ACS (COMMUNICATION SERVICES)
# =============================================================================

def get_acs_connection_string() -> Optional[str]:
    """Obtiene la connection string de Azure Communication Services"""
    return _get_config_with_precedence(
        env_var='ACS_CONNECTION_STRING',
        azure_setting='ACS_CONNECTION_STRING'
    )


def get_acs_whatsapp_api_key() -> Optional[str]:
    """Obtiene la clave de API de WhatsApp de ACS"""
    return _get_config_with_precedence(
        env_var='ACS_WHATSAPP_API_KEY',
        azure_setting='ACS_WHATSAPP_API_KEY'
    )


def get_acs_whatsapp_endpoint() -> Optional[str]:
    """Obtiene el endpoint de WhatsApp de ACS"""
    return _get_config_with_precedence(
        env_var='ACS_WHATSAPP_ENDPOINT',
        azure_setting='ACS_WHATSAPP_ENDPOINT'
    )


def get_acs_phone_number() -> Optional[str]:
    """Obtiene el número de teléfono de ACS"""
    return _get_config_with_precedence(
        env_var='ACS_PHONE_NUMBER',
        azure_setting='ACS_PHONE_NUMBER'
    )


def get_acs_event_grid_topic_endpoint() -> Optional[str]:
    """Obtiene el endpoint del topic de Event Grid de ACS"""
    return _get_config_with_precedence(
        env_var='ACS_EVENT_GRID_TOPIC_ENDPOINT',
        azure_setting='ACS_EVENT_GRID_TOPIC_ENDPOINT'
    )


def get_acs_event_grid_topic_key() -> Optional[str]:
    """Obtiene la clave del topic de Event Grid de ACS"""
    return _get_config_with_precedence(
        env_var='ACS_EVENT_GRID_TOPIC_KEY',
        azure_setting='ACS_EVENT_GRID_TOPIC_KEY'
    )


# =============================================================================
# FUNCIONES DE CONFIGURACIÓN DE FUNCTIONS
# =============================================================================

def get_function_app_url() -> Optional[str]:
    """Obtiene la URL de la Function App"""
    return _get_config_with_precedence(
        env_var='FUNCTION_APP_URL',
        azure_setting='FUNCTION_APP_URL'
    )


def get_function_app_key() -> Optional[str]:
    """Obtiene la clave de la Function App"""
    return _get_config_with_precedence(
        env_var='FUNCTION_APP_KEY',
        azure_setting='FUNCTION_APP_KEY'
    )


# =============================================================================
# FUNCIONES DE CONFIGURACIÓN DE DATABASE
# =============================================================================

def get_database_url() -> Optional[str]:
    """Obtiene la URL de la base de datos"""
    return _get_config_with_precedence(
        env_var='DATABASE_URL',
        azure_setting='DATABASE_URL'
    )


def get_postgresql_name() -> Optional[str]:
    """Obtiene el nombre de la base de datos PostgreSQL"""
    return _get_config_with_precedence(
        env_var='AZURE_POSTGRESQL_NAME',
        azure_setting='AZURE_POSTGRESQL_NAME'
    )


def get_postgresql_username() -> Optional[str]:
    """Obtiene el usuario de la base de datos PostgreSQL"""
    return _get_config_with_precedence(
        env_var='AZURE_POSTGRESQL_USERNAME',
        azure_setting='AZURE_POSTGRESQL_USERNAME'
    )


def get_postgresql_password() -> Optional[str]:
    """Obtiene la contraseña de la base de datos PostgreSQL"""
    return _get_config_with_precedence(
        env_var='AZURE_POSTGRESQL_PASSWORD',
        azure_setting='AZURE_POSTGRESQL_PASSWORD'
    )


def get_postgresql_host() -> Optional[str]:
    """Obtiene el host de la base de datos PostgreSQL"""
    return _get_config_with_precedence(
        env_var='AZURE_POSTGRESQL_HOST',
        azure_setting='AZURE_POSTGRESQL_HOST'
    )


def get_postgresql_port() -> Optional[str]:
    """Obtiene el puerto de la base de datos PostgreSQL"""
    return _get_config_with_precedence(
        env_var='DB_PORT',
        azure_setting='DB_PORT',
        default='5432'
    )


# =============================================================================
# FUNCIONES DE CONFIGURACIÓN DE APPLICATION INSIGHTS
# =============================================================================

def get_application_insights_connection_string() -> Optional[str]:
    """Obtiene la connection string de Application Insights"""
    return _get_config_with_precedence(
        env_var='APPLICATIONINSIGHTS_CONNECTION_STRING',
        azure_setting='APPLICATIONINSIGHTS_CONNECTION_STRING'
    )


# =============================================================================
# FUNCIONES DE CONFIGURACIÓN DE QUEUE
# =============================================================================

def get_queue_name() -> Optional[str]:
    """Obtiene el nombre de la cola de procesamiento"""
    return _get_config_with_precedence(
        env_var='QUEUE_NAME',
        azure_setting='QUEUE_NAME',
        default='doc-processing'
    )


# =============================================================================
# FUNCIONES DE UTILIDAD
# =============================================================================

def is_config_adapter_enabled() -> bool:
    """Verifica si el adaptador de configuración está habilitado"""
    return CONFIG_ADAPTER_ENABLED


def get_config_status() -> dict:
    """
    Obtiene el estado de todas las configuraciones principales
    
    Returns:
        Dict con el estado de cada configuración (SET/NOT SET)
    """
    configs = {
        'storage_account_name': get_storage_account_name(),
        'storage_account_key': get_storage_account_key(),
        'storage_container': get_storage_container(),
        'storage_connection_string': get_storage_connection_string(),
        'search_service': get_search_service(),
        'search_key': get_search_key(),
        'search_index': get_search_index(),
        'openai_endpoint': get_openai_endpoint(),
        'openai_api_key': get_openai_api_key(),
        'vision_endpoint': get_vision_endpoint(),
        'vision_key': get_vision_key(),
        'acs_connection_string': get_acs_connection_string(),
        'acs_whatsapp_api_key': get_acs_whatsapp_api_key(),
        'database_url': get_database_url(),
        'function_app_url': get_function_app_url(),
        'function_app_key': get_function_app_key(),
    }
    
    return {key: 'SET' if value else 'NOT SET' for key, value in configs.items()}


def validate_required_configs(required_configs: list) -> dict:
    """
    Valida que las configuraciones requeridas estén disponibles
    
    Args:
        required_configs: Lista de nombres de funciones de configuración requeridas
    
    Returns:
        Dict con el estado de validación
    """
    validation_result = {}
    
    for config_name in required_configs:
        if hasattr(globals(), config_name):
            config_func = globals()[config_name]
            value = config_func()
            validation_result[config_name] = {
                'available': bool(value),
                'status': 'SET' if value else 'NOT SET'
            }
        else:
            validation_result[config_name] = {
                'available': False,
                'status': 'FUNCTION_NOT_FOUND'
            }
    
    return validation_result
