#!/usr/bin/env python3
"""
Script de prueba para verificar el funcionamiento del cache Redis.
"""

import os
import sys
import django
from pathlib import Path

# Agregar el directorio del proyecto al path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

from utils.redis_cache import get_emb, set_emb, get_ans, set_ans, get_cache_stats, clear_cache
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_redis_cache():
    """Probar funcionalidades del cache Redis"""
    print("=== PRUEBA DE CACHE REDIS ===")
    
    # 1. Probar estadísticas del cache
    print("\n1. Estadísticas del cache:")
    stats = get_cache_stats()
    print(f"   {stats}")
    
    # 2. Probar cache de embeddings
    print("\n2. Prueba de cache de embeddings:")
    test_text = "Este es un texto de prueba para embeddings"
    
    # Intentar obtener embedding del cache (debería ser None)
    cached_emb = get_emb(test_text)
    print(f"   Embedding en cache: {cached_emb is not None}")
    
    # Simular embedding (vector de prueba)
    test_embedding = [0.1, 0.2, 0.3, 0.4, 0.5] * 100  # Vector de 500 dimensiones
    
    # Guardar embedding en cache
    set_emb(test_text, test_embedding, ttl=3600)  # 1 hora
    print(f"   Embedding guardado en cache")
    
    # Obtener embedding del cache (debería existir ahora)
    cached_emb = get_emb(test_text)
    print(f"   Embedding recuperado del cache: {cached_emb is not None}")
    if cached_emb:
        print(f"   Longitud del vector: {len(cached_emb)}")
    
    # 3. Probar cache de respuestas de AI Search
    print("\n3. Prueba de cache de respuestas AI Search:")
    test_query = "¿Cómo puedo hacer una donación?"
    
    # Intentar obtener respuesta del cache (debería ser None)
    cached_ans = get_ans(test_query)
    print(f"   Respuesta en cache: {cached_ans is not None}")
    
    # Simular respuesta de AI Search
    test_response = {
        "response": "Para hacer una donación, puedes contactarnos al +525512345678 o visitar nuestra oficina.",
        "similar_docs": 2,
        "context_info": "Información sobre donaciones",
        "timestamp": "2025-01-08T12:00:00Z"
    }
    
    # Guardar respuesta en cache
    set_ans(test_query, test_response, ttl=3600)  # 1 hora
    print(f"   Respuesta guardada en cache")
    
    # Obtener respuesta del cache (debería existir ahora)
    cached_ans = get_ans(test_query)
    print(f"   Respuesta recuperada del cache: {cached_ans is not None}")
    if cached_ans:
        print(f"   Respuesta: {cached_ans.get('response', 'N/A')[:50]}...")
    
    # 4. Verificar estadísticas actualizadas
    print("\n4. Estadísticas actualizadas del cache:")
    stats = get_cache_stats()
    print(f"   {stats}")
    
    # 5. Probar limpieza del cache
    print("\n5. Prueba de limpieza del cache:")
    clear_cache("emb:*")
    print(f"   Cache de embeddings limpiado")
    
    # Verificar que se limpió
    cached_emb = get_emb(test_text)
    print(f"   Embedding después de limpiar: {cached_emb is not None}")
    
    # Estadísticas finales
    print("\n6. Estadísticas finales:")
    stats = get_cache_stats()
    print(f"   {stats}")
    
    print("\n=== PRUEBA COMPLETADA ===")

if __name__ == "__main__":
    test_redis_cache()
