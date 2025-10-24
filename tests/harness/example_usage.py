"""
Ejemplo de uso del harness de testing.

Este script demuestra cómo usar los mocks para testing aislado
sin dependencias de Django.
"""

import json
import time
from typing import Dict, List, Any

# Importar todos los mocks
from .mock_openai import (
    create_mock_openai_client,
    create_mock_embedding,
    create_mock_chat_response
)
from .mock_search import create_mock_search_client
from .mock_storage import create_mock_blob_service_client
from .mock_redis import create_mock_redis_client


def demonstrate_search_workflow():
    """Demostrar flujo completo de búsqueda."""
    print("🔍 === DEMOSTRACIÓN DE BÚSQUEDA ===")
    
    # 1. Crear cliente de búsqueda
    search_client = create_mock_search_client()
    
    # 2. Realizar búsqueda
    query = "inteligencia artificial"
    print(f"Buscando: '{query}'")
    
    response = search_client.search(
        search_text=query,
        top=5,
        search_type="hybrid"
    )
    
    print(f"Resultados encontrados: {len(response.results)}")
    print(f"Tiempo de búsqueda: {response.search_time_ms}ms")
    
    # 3. Mostrar resultados
    for i, result in enumerate(response.results, 1):
        doc = result.document
        print(f"\n{i}. {doc.metadata.get('filename', 'Sin nombre')}")
        print(f"   Score: {result.score:.3f}")
        print(f"   Tipo: {doc.metadata.get('document_type', 'N/A')}")
        print(f"   Contenido: {doc.content[:100]}...")
    
    # 4. Probar sugerencias
    suggestions = search_client.suggest("django")
    print(f"\nSugerencias para 'django': {len(suggestions)}")
    for suggestion in suggestions[:3]:
        print(f"  - {suggestion['text']}")


def demonstrate_openai_workflow():
    """Demostrar flujo completo de OpenAI."""
    print("\n🤖 === DEMOSTRACIÓN DE OPENAI ===")
    
    # 1. Crear cliente de OpenAI
    openai_client = create_mock_openai_client()
    
    # 2. Probar embeddings
    texts = ["Hola mundo", "Machine learning", "Django framework"]
    print(f"Generando embeddings para: {texts}")
    
    embedding_response = openai_client.embeddings().create(
        input=texts,
        model="text-embedding-ada-002"
    )
    
    print(f"Embeddings generados: {len(embedding_response.data)}")
    print(f"Dimensiones: {len(embedding_response.data[0].embedding)}")
    print(f"Tokens usados: {embedding_response.usage['total_tokens']}")
    
    # 3. Probar chat completions
    messages = [
        {"role": "user", "content": "¿Qué es la inteligencia artificial?"}
    ]
    
    print(f"\nGenerando respuesta para: {messages[0]['content']}")
    
    chat_response = openai_client.chat().completions().create(
        messages=messages,
        model="gpt-4"
    )
    
    print(f"Respuesta: {chat_response.choices[0].message.content}")
    print(f"Modelo usado: {chat_response.model}")
    print(f"Tokens totales: {chat_response.usage['total_tokens']}")


def demonstrate_storage_workflow():
    """Demostrar flujo completo de Storage."""
    print("\n📁 === DEMOSTRACIÓN DE STORAGE ===")
    
    # 1. Crear cliente de storage
    storage_client = create_mock_blob_service_client()
    
    # 2. Listar contenedores
    containers = storage_client.list_containers()
    print(f"Contenedores disponibles: {[c['name'] for c in containers]}")
    
    # 3. Obtener cliente de contenedor
    container_client = storage_client.get_container_client("vea-documents")
    
    # 4. Listar blobs
    blobs = container_client.list_blobs()
    print(f"Blobs en contenedor: {len(blobs)}")
    
    for blob in blobs[:3]:
        print(f"  - {blob['name']} ({blob['size']} bytes)")
    
    # 5. Subir nuevo blob
    test_content = "Este es un archivo de prueba para el harness de testing."
    result = container_client.upload_blob(
        "test/harness_example.txt",
        test_content,
        content_type="text/plain",
        metadata={"test": "true", "created_by": "harness"}
    )
    
    print(f"\nBlob subido: {result}")
    
    # 6. Obtener blob específico
    blob_client = storage_client.get_blob_client("vea-documents", "documents/ai_guide.pdf")
    properties = blob_client.get_blob_properties()
    
    if properties:
        print(f"\nPropiedades del blob:")
        print(f"  Tamaño: {properties.size} bytes")
        print(f"  Tipo: {properties.content_type}")
        print(f"  Modificado: {properties.last_modified}")
    
    # 7. Generar SAS token
    sas_token = blob_client.generate_sas(permission="r")
    print(f"\nSAS Token generado: {sas_token[:50]}...")


def demonstrate_redis_workflow():
    """Demostrar flujo completo de Redis."""
    print("\n🔴 === DEMOSTRACIÓN DE REDIS ===")
    
    # 1. Crear cliente de Redis
    redis_client = create_mock_redis_client()
    
    # 2. Probar operaciones básicas
    print("Probando operaciones básicas...")
    
    # Set/Get
    redis_client.set("test:key", "test_value", ex=60)
    value = redis_client.get("test:key")
    print(f"Valor obtenido: {value}")
    
    # Exists
    exists = redis_client.exists("test:key", "nonexistent:key")
    print(f"Claves existentes: {exists}")
    
    # TTL
    ttl = redis_client.ttl("test:key")
    print(f"TTL restante: {ttl}s")
    
    # 3. Probar cache específico del proyecto
    print("\nProbando cache específico del proyecto...")
    
    # Cache de embeddings
    embedding = [0.1, 0.2, 0.3, 0.4, 0.5] * 300  # 1500 dimensiones
    success = redis_client.set_emb("texto de prueba", embedding)
    print(f"Embedding cacheado: {success}")
    
    cached_embedding = redis_client.get_emb("texto de prueba")
    print(f"Embedding recuperado: {len(cached_embedding) if cached_embedding else 0} dimensiones")
    
    # Cache de respuestas de búsqueda
    search_response = {
        "results": [
            {"id": "1", "content": "Resultado 1", "score": 0.95},
            {"id": "2", "content": "Resultado 2", "score": 0.87}
        ],
        "total_count": 2,
        "search_time_ms": 150
    }
    
    success = redis_client.set_ans("query de prueba", search_response)
    print(f"Respuesta cacheada: {success}")
    
    cached_response = redis_client.get_ans("query de prueba")
    print(f"Respuesta recuperada: {len(cached_response['results']) if cached_response else 0} resultados")
    
    # Cache de SAS tokens
    sas_token = "sv=2020-08-04&ss=bfqt&srt=sco&sp=r&se=2024-12-31T23:59:59Z&st=2024-01-01T00:00:00Z&spr=https&sig=test"
    success = redis_client.set_sas("documents/test.pdf", sas_token)
    print(f"SAS token cacheado: {success}")
    
    cached_sas = redis_client.get_sas("documents/test.pdf")
    print(f"SAS token recuperado: {'Sí' if cached_sas else 'No'}")
    
    # 4. Estadísticas del cache
    stats = redis_client.get_cache_stats()
    print(f"\nEstadísticas del cache:")
    print(f"  Total de claves: {stats['total_keys']}")
    print(f"  Uso de memoria: {stats['memory_usage']} bytes")
    print(f"  Namespaces: {list(stats['namespaces'].keys())}")


def demonstrate_integrated_workflow():
    """Demostrar flujo integrado completo."""
    print("\n🔄 === DEMOSTRACIÓN INTEGRADA ===")
    
    # Crear todos los clientes
    openai_client = create_mock_openai_client()
    search_client = create_mock_search_client()
    storage_client = create_mock_blob_service_client()
    redis_client = create_mock_redis_client()
    
    # Simular flujo completo: búsqueda + generación de respuesta + cache
    query = "¿Qué es machine learning?"
    
    print(f"Procesando consulta: '{query}'")
    
    # 1. Verificar cache de búsqueda
    cached_search = redis_client.get_ans(query)
    if cached_search:
        print("✅ Respuesta encontrada en cache")
        search_results = cached_search
    else:
        print("🔍 Realizando búsqueda...")
        search_response = search_client.search(query, top=3)
        
        # Convertir a formato cacheable
        search_results = {
            "results": [
                {
                    "id": result.document.id,
                    "content": result.document.content[:200],
                    "metadata": result.document.metadata,
                    "score": result.score
                }
                for result in search_response.results
            ],
            "total_count": search_response.total_count,
            "search_time_ms": search_response.search_time_ms
        }
        
        # Cachear resultados
        redis_client.set_ans(query, search_results)
        print("💾 Resultados cacheados")
    
    # 2. Generar respuesta con contexto
    context = " ".join([r["content"] for r in search_results["results"]])
    
    messages = [
        {"role": "system", "content": "Eres un asistente experto en tecnología."},
        {"role": "user", "content": f"Basándote en esta información: {context}\n\nPregunta: {query}"}
    ]
    
    print("🤖 Generando respuesta...")
    
    # Verificar cache de embeddings para el contexto
    context_embedding = redis_client.get_emb(context)
    if not context_embedding:
        embedding_response = openai_client.embeddings().create(input=[context])
        context_embedding = embedding_response.data[0].embedding
        redis_client.set_emb(context, context_embedding)
        print("💾 Embedding del contexto cacheado")
    
    # Generar respuesta
    chat_response = openai_client.chat().completions().create(
        messages=messages,
        model="gpt-4"
    )
    
    answer = chat_response.choices[0].message.content
    
    # 3. Construir respuesta final
    final_response = {
        "response": {
            "answer": answer,
            "confidence": 0.95,
            "language": "es",
            "response_type": "search_enhanced"
        },
        "citations": [
            {
                "source_id": result["id"],
                "source_title": result["metadata"]["filename"],
                "source_type": "document",
                "relevance_score": result["score"],
                "extract": result["content"][:100]
            }
            for result in search_results["results"]
        ],
        "performance": {
            "used_cache": cached_search is not None,
            "cache_hit_type": "search" if cached_search else "none",
            "latency_ms": search_results["search_time_ms"] + 200,  # Simulado
            "tokens_used": chat_response.usage,
            "model_used": chat_response.model
        },
        "search_metadata": {
            "search_performed": True,
            "documents_retrieved": len(search_results["results"]),
            "search_time_ms": search_results["search_time_ms"],
            "query_used": query
        }
    }
    
    print(f"\n📝 Respuesta generada:")
    print(f"  Respuesta: {answer[:100]}...")
    print(f"  Fuentes: {len(final_response['citations'])}")
    print(f"  Cache usado: {final_response['performance']['used_cache']}")
    print(f"  Latencia: {final_response['performance']['latency_ms']}ms")


def demonstrate_error_scenarios():
    """Demostrar manejo de errores y escenarios de fallo."""
    print("\n⚠️ === DEMOSTRACIÓN DE ESCENARIOS DE ERROR ===")
    
    # 1. Redis no disponible
    print("Probando Redis no disponible...")
    from .mock_redis import create_mock_redis_unavailable, create_mock_redis_with_timeouts
    redis_unavailable = create_mock_redis_unavailable()
    
    result = redis_unavailable.set("test", "value")
    print(f"  Set con Redis down: {result}")
    
    value = redis_unavailable.get("test")
    print(f"  Get con Redis down: {value}")
    
    # 2. Redis con timeouts intermitentes
    print("\nProbando Redis con timeouts...")
    redis_timeout = create_mock_redis_with_timeouts(probability=0.5)
    
    for i in range(5):
        result = redis_timeout.set(f"key_{i}", f"value_{i}")
        print(f"  Set {i}: {'✅' if result else '❌'}")
    
    # 3. Búsqueda sin resultados
    print("\nProbando búsqueda sin resultados...")
    search_client = create_mock_search_client()
    
    response = search_client.search("xyz123nonexistent", top=5)
    print(f"  Resultados para query inexistente: {len(response.results)}")
    
    # 4. Blob no encontrado
    print("\nProbando blob no encontrado...")
    storage_client = create_mock_blob_service_client()
    blob_client = storage_client.get_blob_client("vea-documents", "nonexistent.pdf")
    
    try:
        blob = blob_client.download_blob()
        print(f"  Blob descargado: {blob.name}")
    except ValueError as e:
        print(f"  Error esperado: {e}")


def main():
    """Función principal que ejecuta todas las demostraciones."""
    print("🚀 INICIANDO DEMOSTRACIÓN DEL HARNESS DE TESTING")
    print("=" * 60)
    
    try:
        # Ejecutar todas las demostraciones
        demonstrate_search_workflow()
        demonstrate_openai_workflow()
        demonstrate_storage_workflow()
        demonstrate_redis_workflow()
        demonstrate_integrated_workflow()
        demonstrate_error_scenarios()
        
        print("\n" + "=" * 60)
        print("✅ DEMOSTRACIÓN COMPLETADA EXITOSAMENTE")
        print("\nEl harness de testing está funcionando correctamente.")
        print("Puedes usar estos mocks para testing aislado sin Django.")
        
    except Exception as e:
        print(f"\n❌ Error durante la demostración: {e}")
        raise


if __name__ == "__main__":
    main()
