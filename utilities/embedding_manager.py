"""
Embedding Manager for VEA Connect WebApp.

This module provides a comprehensive embedding management system
with Azure OpenAI integration, Azure AI Search storage, and Redis caching.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from utilities.azure_search_client import get_azure_search_client
from apps.embeddings.openai_service import OpenAIService

# Import Redis cache layer
try:
    from utils.cache_layer import get_emb, set_emb, is_cache_enabled
    CACHE_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("Redis cache layer available for embeddings")
except ImportError:
    CACHE_AVAILABLE = False
    # Fallback to local cache
    def get_emb(text: str):
        """Get embedding from cache (local memory fallback)"""
        from django.core.cache import cache
        return cache.get(f"emb:{text}")

    def set_emb(text: str, embedding, ttl: Optional[int] = None) -> bool:
        """Set embedding in cache (local memory fallback)"""
        from django.core.cache import cache
        timeout = ttl if ttl is not None else 3600
        cache.set(f"emb:{text}", embedding, timeout)
        return True
    
    logger = logging.getLogger(__name__)
    logger.warning("Redis cache layer not available, using local cache fallback")

class EmbeddingServiceUnavailable(Exception):
    pass

class EmbeddingManager:
    """
    EmbeddingManager: CRUD de embeddings usando exclusivamente Azure AI Search.
    """
    def __init__(self, search_client=None, openai_service=None, index_name=None):
        self.openai_service = openai_service or OpenAIService()
        self.search_client = search_client or get_azure_search_client()
        self.index_name = index_name or getattr(self.search_client, 'index_name', None)
        # Health check inmediato
        if not self.search_client or not self.index_name:
            raise EmbeddingServiceUnavailable("Azure AI Search no está configurado correctamente.")
        try:
            self.health_check()
        except Exception as e:
            raise EmbeddingServiceUnavailable(f"No se puede conectar a Azure AI Search: {e}")

    def health_check(self):
        # Intenta listar documentos para validar conexión
        # Usar búsqueda semántica con un texto de ejemplo
        self.search_client.search_semantic(query_text="test", top_k=1)

    def generate_embedding(self, text: str) -> List[float]:
        """Genera un embedding para el texto usando el servicio existente.

        - Reutiliza OpenAIService del proyecto (sin redefinir clientes)
        - Si no hay configuración válida, el servicio ya usa un embedding dummy seguro
        - Nunca lanza excepción hacia arriba; retorna [] en caso de error
        """
        try:
            if not text or not isinstance(text, str) or not text.strip():
                logger.info("generate_embedding: texto vacío o inválido; retornando []")
                return []

            # Cache de embeddings por contenido, como en create_embedding
            cached = get_emb(text)
            if cached:
                logger.info("generate_embedding: cache HIT para texto (%s chars)", len(text))
                return cached  # type: ignore[return-value]

            embedding = self.openai_service.generate_embedding(text)
            # Guardar en cache para futuras consultas
            try:
                set_emb(text, embedding)
            except Exception:
                pass
            return embedding  # type: ignore[return-value]
        except Exception as e:
            logger.warning("generate_embedding: error generando embedding: %s", e)
            return []

    def find_similar(self, query, top_k: int = 3, threshold: float = 0.0, **kwargs) -> List[Dict[str, Any]]:
        """Realiza búsqueda vectorial de solo lectura en el índice actual.

        - Acepta `query` como str (se embeddea) o como vector (List[float])
        - Usa el cliente existente de Azure Search vía `get_azure_search_client()`
        - No escribe ni modifica el índice; solo lectura
        - Umbral opcional por parámetro (no global); si no se pasa, no filtra
        - Soporta `limit=` como alias de `top_k` para compatibilidad con llamadas existentes
        """
        try:
            # Compatibilidad con firmas distintas (handlers usan limit=...)
            if 'limit' in kwargs and isinstance(kwargs.get('limit'), int):
                top_k = int(kwargs['limit'])

            # Obtener vector a partir del query
            if isinstance(query, str):
                vector = self.generate_embedding(query)
            elif isinstance(query, list):
                vector = query
            else:
                logger.info("find_similar: tipo de query no soportado (%s)", type(query))
                return []

            if not vector:
                logger.info("find_similar: vector vacío; retornando []")
                return []

            # Búsqueda vectorial usando el cliente existente (solo lectura)
            results = self.search_client.search_vector(query_vector=vector, top_k=top_k)
            normalized: List[Dict[str, Any]] = []
            for item in results or []:
                score = float(item.get('score', item.get('@search.score', 0.0)) or 0.0)
                record = {
                    'id': item.get('id'),
                    'score': score,
                    'text': item.get('content') or item.get('text') or item.get('title') or '',
                    'metadata': item.get('metadata', {}),
                    'created_at': item.get('created_at'),
                    'source_type': item.get('source_type'),
                    'filename': item.get('filename'),
                }
                normalized.append(record)

            # Filtro opcional por threshold (no modifica ninguna config global)
            if isinstance(threshold, (int, float)) and threshold > 0:
                normalized = [r for r in normalized if float(r.get('score', 0.0)) >= float(threshold)]

            # Ordenar descendente por score para consistencia
            normalized.sort(key=lambda r: float(r.get('score', 0.0)), reverse=True)
            return normalized[: max(0, int(top_k))]
        except Exception as e:
            logger.warning("find_similar: error en búsqueda vectorial: %s", e)
            return []

    def create_embedding(self, document_id: str, content: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        if not document_id or not content:
            raise ValueError("document_id y content son requeridos")
        
        # Check cache first
        cached_embedding = get_emb(content)
        if cached_embedding:
            logger.info(f"Cache HIT: Using cached embedding for document: {document_id}")
            embedding = cached_embedding
        else:
            # Generate new embedding
            logger.info(f"Cache MISS: Generating new embedding for document: {document_id}")
            embedding = self.openai_service.generate_embedding(content)
            # Cache the embedding
            set_emb(content, embedding)
            logger.info(f"Generated and cached new embedding for document: {document_id}")
        
        doc = {
            "id": document_id,
            "content": content,
            "embedding": embedding,
            "created_at": datetime.utcnow().isoformat(),
        }
        result = self.search_client.upload_documents([doc])
        logger.info(f"Embedding creado en AI Search: {document_id}")
        return {"status": "success", "id": document_id}

    def list_embeddings(self, limit: int = 10, offset: int = 0) -> Dict[str, Any]:
        # Usar búsqueda semántica para listar embeddings, pero si falla, fallback a búsqueda simple
        try:
            results = self.search_client.search_semantic(query_text="*", top_k=limit)
        except Exception as e:
            logger.warning(f"Fallo búsqueda semántica, usando búsqueda simple: {e}")
            results = self.search_client.search_client.search("*", top=limit, query_type="simple")
        embeddings = [r for r in results]
        logger.info(f"Listados {len(embeddings)} embeddings desde AI Search")
        return {"status": "success", "data": {"embeddings": embeddings, "limit": limit, "offset": offset}}

    def delete_embedding(self, document_id: str) -> Dict[str, Any]:
        if not document_id:
            raise ValueError("document_id es requerido")
        result = self.search_client.delete_document(document_id)
        logger.info(f"Embedding eliminado de AI Search: {document_id}")
        return {"status": "success", "message": "Embedding deleted", "data": {"id": document_id}} 