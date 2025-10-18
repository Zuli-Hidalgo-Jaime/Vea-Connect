"""
Capa de Cache Redis Optimizada - VEA Connect

Este módulo proporciona una capa de abstracción optimizada para cache Redis
con graceful degradation, namespacing y TTLs específicos por tipo de dato.

Namespacing: vea:emb:*, vea:ans:*, vea:sas:*
TTL por defecto: emb=3600, ans=1800, sas=300
Graceful degradation: si no hay Redis/timeout → None sin excepción

Feature flag: CACHE_LAYER_ENABLED (por defecto False)
"""

import json
import hashlib
import logging
import time
from typing import Optional, Any, Dict, Union
from urllib.parse import urlparse
from django.conf import settings

# Configurar logger
logger = logging.getLogger(__name__)

# Feature flag global
CACHE_LAYER_ENABLED = getattr(settings, 'CACHE_LAYER_ENABLED', False)

# TTLs por defecto (en segundos)
DEFAULT_TTLS = {
    'emb': 3600,  # 1 hora para embeddings
    'ans': 1800,  # 30 minutos para respuestas de AI Search
    'sas': 300,   # 5 minutos para SAS tokens
}

# Namespaces
NAMESPACES = {
    'emb': 'vea:emb',
    'ans': 'vea:ans', 
    'sas': 'vea:sas',
}

# Redis client global
_redis_client = None


def _get_redis_client():
    """
    Obtiene el cliente Redis con graceful degradation
    
    Returns:
        Redis client o None si no está disponible
    """
    global _redis_client
    
    if _redis_client is not None:
        return _redis_client
    
    if not CACHE_LAYER_ENABLED:
        logger.debug("Cache layer disabled by feature flag")
        return None
    
    try:
        import redis
        
        # Obtener URL de Redis desde configuración
        redis_url = getattr(settings, 'REDIS_URL', None)
        if not redis_url:
            redis_url = getattr(settings, 'AZURE_REDIS_URL', None)
        if not redis_url:
            redis_url = getattr(settings, 'AZURE_REDIS_CONNECTIONSTRING', None)
        
        if not redis_url:
            logger.warning("Redis URL not configured, cache layer disabled")
            return None
        
        # Parsear URL para configuración SSL
        parsed_url = urlparse(redis_url)
        
        # Configurar SSL si es necesario
        ssl_config = {}
        if parsed_url.scheme == 'rediss':
            ssl_config = {
                'ssl': True,
                'ssl_cert_reqs': None,
                'ssl_ca_certs': None
            }
        
        # Crear cliente Redis con configuración optimizada
        _redis_client = redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30,
            **ssl_config
        )
        
        # Probar conexión
        _redis_client.ping()
        logger.info("Redis cache layer initialized successfully")
        
        return _redis_client
        
    except Exception as e:
        logger.warning(f"Redis connection failed, cache layer disabled: {e}")
        _redis_client = None
        return None


def _generate_key(namespace: str, identifier: str) -> str:
    """
    Genera una clave con namespace
    
    Args:
        namespace: Namespace (emb, ans, sas)
        identifier: Identificador único
    
    Returns:
        Clave formateada con namespace
    """
    if namespace not in NAMESPACES:
        raise ValueError(f"Invalid namespace: {namespace}")
    
    # Generar hash del identificador si es muy largo
    if len(identifier) > 50:
        identifier = hashlib.sha256(identifier.encode('utf-8')).hexdigest()[:16]
    
    return f"{NAMESPACES[namespace]}:{identifier}"


def _safe_redis_operation(operation, *args, **kwargs):
    """
    Ejecuta una operación Redis con graceful degradation
    
    Args:
        operation: Función de operación Redis
        *args: Argumentos de la operación
        **kwargs: Argumentos nombrados de la operación
    
    Returns:
        Resultado de la operación o None si falla
    """
    if not CACHE_LAYER_ENABLED:
        return None
    
    client = _get_redis_client()
    if not client:
        return None
    
    try:
        return operation(*args, **kwargs)
    except Exception as e:
        logger.warning(f"Redis operation failed: {e}")
        return None


# =============================================================================
# FUNCIONES DE CACHE PARA EMBEDDINGS
# =============================================================================

def get_emb(text: str) -> Optional[list]:
    """
    Obtiene embedding desde cache
    
    Args:
        text: Texto para buscar en cache
    
    Returns:
        Lista de embeddings o None si no está en cache
    """
    key = _generate_key('emb', text)
    result = _safe_redis_operation(_get_redis_client().get, key)
    
    if result:
        try:
            return json.loads(result)
        except (json.JSONDecodeError, TypeError):
            logger.warning(f"Invalid JSON in cache for key: {key}")
            return None
    
    return None


def set_emb(text: str, embedding: list, ttl: Optional[int] = None) -> bool:
    """
    Guarda embedding en cache
    
    Args:
        text: Texto como clave
        embedding: Lista de embeddings a guardar
        ttl: TTL en segundos (opcional, usa default si no se especifica)
    
    Returns:
        True si se guardó exitosamente, False en caso contrario
    """
    if not embedding:
        return False
    
    key = _generate_key('emb', text)
    ttl = ttl or DEFAULT_TTLS['emb']
    
    try:
        value = json.dumps(embedding)
        return _safe_redis_operation(_get_redis_client().setex, key, ttl, value) or False
    except (TypeError, ValueError) as e:
        logger.warning(f"Failed to serialize embedding for cache: {e}")
        return False


# =============================================================================
# FUNCIONES DE CACHE PARA AI SEARCH
# =============================================================================

def get_ans(query: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene respuesta de AI Search desde cache
    
    Args:
        query: Query de búsqueda
    
    Returns:
        Respuesta de AI Search o None si no está en cache
    """
    key = _generate_key('ans', query)
    result = _safe_redis_operation(_get_redis_client().get, key)
    
    if result:
        try:
            return json.loads(result)
        except (json.JSONDecodeError, TypeError):
            logger.warning(f"Invalid JSON in cache for key: {key}")
            return None
    
    return None


def set_ans(query: str, response: Dict[str, Any], ttl: Optional[int] = None) -> bool:
    """
    Guarda respuesta de AI Search en cache
    
    Args:
        query: Query de búsqueda como clave
        response: Respuesta de AI Search a guardar
        ttl: TTL en segundos (opcional, usa default si no se especifica)
    
    Returns:
        True si se guardó exitosamente, False en caso contrario
    """
    if not response:
        return False
    
    key = _generate_key('ans', query)
    ttl = ttl or DEFAULT_TTLS['ans']
    
    try:
        value = json.dumps(response)
        return _safe_redis_operation(_get_redis_client().setex, key, ttl, value) or False
    except (TypeError, ValueError) as e:
        logger.warning(f"Failed to serialize AI Search response for cache: {e}")
        return False


# =============================================================================
# FUNCIONES DE CACHE PARA SAS TOKENS
# =============================================================================

def get_sas(container: str, blob_name: str) -> Optional[str]:
    """
    Obtiene SAS token desde cache
    
    Args:
        container: Nombre del contenedor
        blob_name: Nombre del blob
    
    Returns:
        SAS token o None si no está en cache
    """
    identifier = f"{container}:{blob_name}"
    key = _generate_key('sas', identifier)
    return _safe_redis_operation(_get_redis_client().get, key)


def set_sas(container: str, blob_name: str, sas_token: str, ttl: Optional[int] = None) -> bool:
    """
    Guarda SAS token en cache
    
    Args:
        container: Nombre del contenedor
        blob_name: Nombre del blob
        sas_token: SAS token a guardar
        ttl: TTL en segundos (opcional, usa default si no se especifica)
    
    Returns:
        True si se guardó exitosamente, False en caso contrario
    """
    if not sas_token:
        return False
    
    identifier = f"{container}:{blob_name}"
    key = _generate_key('sas', identifier)
    ttl = ttl or DEFAULT_TTLS['sas']
    
    return _safe_redis_operation(_get_redis_client().setex, key, ttl, sas_token) or False


# =============================================================================
# FUNCIONES DE UTILIDAD
# =============================================================================

def get_cache_stats() -> Dict[str, Any]:
    """
    Obtiene estadísticas del cache
    
    Returns:
        Diccionario con estadísticas del cache
    """
    if not CACHE_LAYER_ENABLED:
        return {
            'enabled': False,
            'reason': 'Feature flag disabled'
        }
    
    client = _get_redis_client()
    if not client:
        return {
            'enabled': False,
            'reason': 'Redis not available'
        }
    
    try:
        # Obtener información del servidor Redis
        info = client.info()
        
        # Contar claves por namespace
        stats = {
            'enabled': True,
            'redis_version': info.get('redis_version', 'unknown'),
            'connected_clients': info.get('connected_clients', 0),
            'used_memory_human': info.get('used_memory_human', 'unknown'),
            'keyspace': {}
        }
        
        # Contar claves por namespace
        for namespace in NAMESPACES.values():
            pattern = f"{namespace}:*"
            keys = client.keys(pattern)
            stats['keyspace'][namespace] = len(keys)
        
        return stats
        
    except Exception as e:
        logger.warning(f"Failed to get cache stats: {e}")
        return {
            'enabled': True,
            'error': str(e)
        }


def clear_cache(namespace: Optional[str] = None) -> bool:
    """
    Limpia el cache
    
    Args:
        namespace: Namespace específico a limpiar (emb, ans, sas) o None para limpiar todo
    
    Returns:
        True si se limpió exitosamente, False en caso contrario
    """
    if not CACHE_LAYER_ENABLED:
        return False
    
    client = _get_redis_client()
    if not client:
        return False
    
    try:
        if namespace:
            if namespace not in NAMESPACES:
                raise ValueError(f"Invalid namespace: {namespace}")
            
            pattern = f"{NAMESPACES[namespace]}:*"
            keys = client.keys(pattern)
            if keys:
                client.delete(*keys)
                logger.info(f"Cleared {len(keys)} keys from namespace: {namespace}")
        else:
            # Limpiar todos los namespaces
            total_deleted = 0
            for ns in NAMESPACES.values():
                pattern = f"{ns}:*"
                keys = client.keys(pattern)
                if keys:
                    deleted = client.delete(*keys)
                    total_deleted += deleted
            
            logger.info(f"Cleared {total_deleted} total keys from all namespaces")
        
        return True
        
    except Exception as e:
        logger.warning(f"Failed to clear cache: {e}")
        return False


def is_cache_enabled() -> bool:
    """
    Verifica si el cache está habilitado
    
    Returns:
        True si el cache está habilitado y disponible
    """
    if not CACHE_LAYER_ENABLED:
        return False
    
    return _get_redis_client() is not None


def get_cache_health() -> Dict[str, Any]:
    """
    Obtiene el estado de salud del cache
    
    Returns:
        Diccionario con información de salud del cache
    """
    health = {
        'feature_flag_enabled': CACHE_LAYER_ENABLED,
        'redis_available': False,
        'connection_ok': False,
        'last_check': time.time()
    }
    
    if not CACHE_LAYER_ENABLED:
        health['status'] = 'disabled'
        return health
    
    client = _get_redis_client()
    if not client:
        health['status'] = 'unavailable'
        return health
    
    health['redis_available'] = True
    
    try:
        # Probar conexión
        client.ping()
        health['connection_ok'] = True
        health['status'] = 'healthy'
        
        # Obtener estadísticas básicas
        stats = get_cache_stats()
        health.update(stats)
        
    except Exception as e:
        health['status'] = 'error'
        health['error'] = str(e)
    
    return health


def set_ttl_defaults(emb_ttl: Optional[int] = None, ans_ttl: Optional[int] = None, sas_ttl: Optional[int] = None):
    """
    Configura TTLs por defecto personalizados
    
    Args:
        emb_ttl: TTL para embeddings (segundos)
        ans_ttl: TTL para respuestas de AI Search (segundos)
        sas_ttl: TTL para SAS tokens (segundos)
    """
    global DEFAULT_TTLS
    
    if emb_ttl is not None:
        DEFAULT_TTLS['emb'] = emb_ttl
    if ans_ttl is not None:
        DEFAULT_TTLS['ans'] = ans_ttl
    if sas_ttl is not None:
        DEFAULT_TTLS['sas'] = sas_ttl
    
    logger.info(f"Updated default TTLs: {DEFAULT_TTLS}")


def get_ttl_defaults() -> Dict[str, int]:
    """
    Obtiene los TTLs por defecto actuales
    
    Returns:
        Diccionario con TTLs por defecto
    """
    return DEFAULT_TTLS.copy()
