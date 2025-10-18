"""
Ejemplo de Uso de la Capa de Cache Redis - VEA Connect

Este archivo demuestra cómo usar la capa de cache Redis optimizada
en nuevos módulos sin afectar el código existente.

IMPORTANTE: Este es solo un ejemplo. No usar en producción.
"""

import logging
import time
from utils.cache_layer import (
    # Funciones de cache
    get_emb, set_emb,
    get_ans, set_ans,
    get_sas, set_sas,
    
    # Utilidades
    get_cache_stats,
    clear_cache,
    is_cache_enabled,
    get_cache_health,
    set_ttl_defaults,
    get_ttl_defaults
)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_embeddings_cache():
    """Ejemplo de cache de embeddings"""
    logger.info("=== Cache de Embeddings ===")
    
    # Texto de ejemplo
    text = "Este es un texto de ejemplo para generar embeddings"
    
    # Intentar obtener desde cache
    cached_embedding = get_emb(text)
    if cached_embedding:
        logger.info(f"✅ Embedding encontrado en cache: {len(cached_embedding)} dimensiones")
        return cached_embedding
    
    # Simular generación de embedding (en producción esto vendría de OpenAI)
    logger.info("🔄 Generando embedding...")
    time.sleep(1)  # Simular procesamiento
    
    # Embedding simulado (1536 dimensiones como OpenAI)
    embedding = [0.1] * 1536
    
    # Guardar en cache
    success = set_emb(text, embedding)
    if success:
        logger.info("✅ Embedding guardado en cache")
    else:
        logger.warning("⚠️ No se pudo guardar embedding en cache")
    
    return embedding


def example_ai_search_cache():
    """Ejemplo de cache de AI Search"""
    logger.info("=== Cache de AI Search ===")
    
    # Query de ejemplo
    query = "documentos sobre donaciones ministeriales"
    
    # Intentar obtener desde cache
    cached_response = get_ans(query)
    if cached_response:
        logger.info(f"✅ Respuesta encontrada en cache: {len(cached_response.get('results', []))} resultados")
        return cached_response
    
    # Simular búsqueda en AI Search
    logger.info("🔄 Realizando búsqueda en AI Search...")
    time.sleep(2)  # Simular procesamiento
    
    # Respuesta simulada
    response = {
        'query': query,
        'results': [
            {'id': 1, 'title': 'Documento 1', 'score': 0.95},
            {'id': 2, 'title': 'Documento 2', 'score': 0.87},
            {'id': 3, 'title': 'Documento 3', 'score': 0.82}
        ],
        'total_count': 3,
        'search_time_ms': 150
    }
    
    # Guardar en cache
    success = set_ans(query, response)
    if success:
        logger.info("✅ Respuesta guardada en cache")
    else:
        logger.warning("⚠️ No se pudo guardar respuesta en cache")
    
    return response


def example_sas_token_cache():
    """Ejemplo de cache de SAS tokens"""
    logger.info("=== Cache de SAS Tokens ===")
    
    container = "documents"
    blob_name = "documento_ejemplo.pdf"
    
    # Intentar obtener desde cache
    cached_token = get_sas(container, blob_name)
    if cached_token:
        logger.info("✅ SAS token encontrado en cache")
        return cached_token
    
    # Simular generación de SAS token
    logger.info("🔄 Generando SAS token...")
    time.sleep(0.5)  # Simular procesamiento
    
    # Token simulado
    sas_token = "https://storage.blob.core.windows.net/documents/documento_ejemplo.pdf?sv=2020-08-04&st=2024-01-01T00:00:00Z&se=2024-12-31T23:59:59Z&sr=b&sp=r&sig=example"
    
    # Guardar en cache
    success = set_sas(container, blob_name, sas_token)
    if success:
        logger.info("✅ SAS token guardado en cache")
    else:
        logger.warning("⚠️ No se pudo guardar SAS token en cache")
    
    return sas_token


def example_cache_management():
    """Ejemplo de gestión del cache"""
    logger.info("=== Gestión del Cache ===")
    
    # Verificar si el cache está habilitado
    enabled = is_cache_enabled()
    logger.info(f"Cache habilitado: {enabled}")
    
    if not enabled:
        logger.warning("Cache no está habilitado. Verificar CACHE_LAYER_ENABLED=True")
        return
    
    # Obtener estado de salud
    health = get_cache_health()
    logger.info(f"Estado de salud: {health['status']}")
    
    if health['status'] == 'healthy':
        # Obtener estadísticas
        stats = get_cache_stats()
        logger.info(f"Versión Redis: {stats.get('redis_version', 'unknown')}")
        logger.info(f"Clientes conectados: {stats.get('connected_clients', 0)}")
        logger.info(f"Memoria usada: {stats.get('used_memory_human', 'unknown')}")
        
        # Mostrar claves por namespace
        keyspace = stats.get('keyspace', {})
        for namespace, count in keyspace.items():
            logger.info(f"Claves en {namespace}: {count}")
    
    # Obtener TTLs actuales
    ttls = get_ttl_defaults()
    logger.info(f"TTLs por defecto: {ttls}")


def example_ttl_customization():
    """Ejemplo de personalización de TTLs"""
    logger.info("=== Personalización de TTLs ===")
    
    # Mostrar TTLs actuales
    current_ttls = get_ttl_defaults()
    logger.info(f"TTLs actuales: {current_ttls}")
    
    # Configurar TTLs personalizados
    set_ttl_defaults(
        emb_ttl=7200,  # 2 horas para embeddings
        ans_ttl=3600,  # 1 hora para AI Search
        sas_ttl=600    # 10 minutos para SAS tokens
    )
    
    # Verificar cambios
    new_ttls = get_ttl_defaults()
    logger.info(f"TTLs actualizados: {new_ttls}")


def example_cache_operations():
    """Ejemplo de operaciones de cache"""
    logger.info("=== Operaciones de Cache ===")
    
    # Crear algunos datos de prueba
    test_embeddings = [0.1] * 1536
    test_response = {'results': [{'id': 1, 'title': 'Test'}]}
    test_token = "https://example.com/test?token=123"
    
    # Guardar datos de prueba
    set_emb("texto_prueba", test_embeddings)
    set_ans("query_prueba", test_response)
    set_sas("test_container", "test_blob", test_token)
    
    # Verificar que se guardaron
    logger.info("Datos de prueba guardados en cache")
    
    # Obtener estadísticas
    stats = get_cache_stats()
    keyspace = stats.get('keyspace', {})
    logger.info(f"Claves en cache: {keyspace}")
    
    # Limpiar cache por namespace
    logger.info("Limpiando cache de embeddings...")
    clear_cache('emb')
    
    # Verificar limpieza
    stats_after = get_cache_stats()
    keyspace_after = stats_after.get('keyspace', {})
    logger.info(f"Claves después de limpiar embeddings: {keyspace_after}")
    
    # Limpiar todo el cache
    logger.info("Limpiando todo el cache...")
    clear_cache()
    
    # Verificar limpieza total
    stats_final = get_cache_stats()
    keyspace_final = stats_final.get('keyspace', {})
    logger.info(f"Claves después de limpiar todo: {keyspace_final}")


def run_all_examples():
    """Ejecutar todos los ejemplos"""
    logger.info("🚀 Iniciando ejemplos de la Capa de Cache Redis")
    logger.info("=" * 60)
    
    # Verificar estado del cache
    example_cache_management()
    logger.info("")
    
    # Ejemplos de uso por tipo de dato
    example_embeddings_cache()
    logger.info("")
    
    example_ai_search_cache()
    logger.info("")
    
    example_sas_token_cache()
    logger.info("")
    
    # Ejemplos de gestión
    example_ttl_customization()
    logger.info("")
    
    example_cache_operations()
    logger.info("")
    
    logger.info("✅ Ejemplos completados")


if __name__ == "__main__":
    # Solo ejecutar si el cache está habilitado
    if is_cache_enabled():
        run_all_examples()
    else:
        logger.warning("La capa de cache está deshabilitada.")
        logger.info("Para habilitarla, establece CACHE_LAYER_ENABLED=True")
        logger.info("Ejecutando solo verificación de estado...")
        example_cache_management()

