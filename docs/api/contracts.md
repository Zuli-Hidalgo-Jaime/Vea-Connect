# Contratos I/O - APIs VEA Connect

## Resumen

Este documento define los contratos de entrada/salida para las APIs principales del sistema VEA Connect, estableciendo esquemas estándar para búsqueda/RAG, respuestas del bot y descargas.

## 1. Búsqueda/RAG Input/Output

### 1.1 Input de Búsqueda

```json
{
  "query": {
    "text": "string (requerido)",
    "filters": {
      "document_type": ["pdf", "image", "document"],
      "date_range": {
        "start": "2024-01-01T00:00:00Z",
        "end": "2024-12-31T23:59:59Z"
      },
      "tags": ["string"],
      "categories": ["string"]
    },
    "search_type": "hybrid|semantic|vector|bm25",
    "top_k": 10,
    "include_metadata": true,
    "rerank": true
  },
  "context": {
    "user_id": "string",
    "session_id": "string",
    "preferences": {
      "language": "es|en",
      "max_results": 10
    }
  }
}
```

### 1.2 Output de Búsqueda

```json
{
  "results": [
    {
      "id": "string",
      "content": "string",
      "metadata": {
        "filename": "string",
        "document_type": "pdf|image|document",
        "upload_date": "2024-01-01T00:00:00Z",
        "file_size": 12345,
        "sha256": "string",
        "tags": ["string"],
        "categories": ["string"]
      },
      "score": 0.95,
      "highlights": [
        {
          "text": "string",
          "start": 0,
          "end": 10
        }
      ],
      "chunk_info": {
        "chunk_id": "string",
        "chunk_index": 0,
        "total_chunks": 5
      }
    }
  ],
  "search_metadata": {
    "total_results": 100,
    "search_time_ms": 150,
    "search_type": "hybrid",
    "query_processed": "string",
    "filters_applied": ["string"]
  },
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total_pages": 10
  }
}
```

## 2. Respuesta del Bot

### 2.1 Input del Bot

```json
{
  "message": {
    "text": "string (requerido)",
    "user_id": "string",
    "session_id": "string",
    "context": {
      "previous_messages": [
        {
          "role": "user|assistant",
          "content": "string",
          "timestamp": "2024-01-01T00:00:00Z"
        }
      ],
      "user_preferences": {
        "language": "es|en",
        "response_style": "concise|detailed",
        "include_sources": true
      }
    }
  },
  "search_context": {
    "enable_search": true,
    "search_filters": {
      "document_types": ["pdf", "image"],
      "date_range": {
        "start": "2024-01-01T00:00:00Z",
        "end": "2024-12-31T23:59:59Z"
      }
    }
  }
}
```

### 2.2 Output del Bot

```json
{
  "response": {
    "answer": "string (requerido)",
    "confidence": 0.95,
    "language": "es|en",
    "response_type": "direct|search_enhanced|clarification",
    "suggested_actions": [
      {
        "action": "search_more|download|contact",
        "label": "string",
        "parameters": {}
      }
    ]
  },
  "citations": [
    {
      "source_id": "string",
      "source_title": "string",
      "source_type": "document|webpage|database",
      "relevance_score": 0.95,
      "extract": "string",
      "page_number": 1,
      "url": "string"
    }
  ],
  "performance": {
    "used_cache": true,
    "cache_hit_type": "embedding|response|search",
    "latency_ms": 250,
    "tokens_used": {
      "input": 100,
      "output": 200,
      "total": 300
    },
    "model_used": "gpt-4|gpt-3.5-turbo"
  },
  "search_metadata": {
    "search_performed": true,
    "documents_retrieved": 5,
    "search_time_ms": 150,
    "query_used": "string"
  }
}
```

## 3. Descargas

### 3.1 Input de Descarga

```json
{
  "download_request": {
    "file_id": "string (requerido)",
    "user_id": "string",
    "download_type": "direct|stream|sas_url",
    "format": "original|pdf|txt",
    "include_metadata": true
  },
  "access_control": {
    "permissions": ["read", "download"],
    "expires_at": "2024-12-31T23:59:59Z"
  }
}
```

### 3.2 Output de Descarga

#### 3.2.1 Respuesta Directa (Stream)

```json
{
  "download": {
    "type": "stream",
    "content": "base64_encoded_content",
    "content_type": "application/pdf|image/jpeg|text/plain",
    "filename": "document.pdf",
    "file_size": 12345,
    "checksum": {
      "sha256": "string",
      "md5": "string"
    }
  },
  "metadata": {
    "upload_date": "2024-01-01T00:00:00Z",
    "last_modified": "2024-01-01T00:00:00Z",
    "tags": ["string"],
    "categories": ["string"]
  }
}
```

#### 3.2.2 Respuesta con URL (Redirect)

```json
{
  "download": {
    "type": "redirect_url",
    "url": "https://storage.blob.core.windows.net/container/file.pdf?sv=2020-08-04&ss=bfqt&srt=sco&sp=rwdlacupitfx&se=2024-12-31T23:59:59Z&st=2024-01-01T00:00:00Z&spr=https&sig=...",
    "expires_at": "2024-12-31T23:59:59Z",
    "content_type": "application/pdf",
    "filename": "document.pdf",
    "file_size": 12345
  },
  "metadata": {
    "upload_date": "2024-01-01T00:00:00Z",
    "last_modified": "2024-01-01T00:00:00Z",
    "tags": ["string"],
    "categories": ["string"]
  }
}
```

## 4. Códigos de Error Estándar

### 4.1 Estructura de Error

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": "string",
    "timestamp": "2024-01-01T00:00:00Z",
    "request_id": "string"
  }
}
```

### 4.2 Códigos de Error Comunes

| Código | Descripción | HTTP Status |
|--------|-------------|-------------|
| `INVALID_INPUT` | Datos de entrada inválidos | 400 |
| `UNAUTHORIZED` | No autorizado | 401 |
| `FORBIDDEN` | Acceso prohibido | 403 |
| `NOT_FOUND` | Recurso no encontrado | 404 |
| `RATE_LIMITED` | Límite de tasa excedido | 429 |
| `INTERNAL_ERROR` | Error interno del servidor | 500 |
| `SERVICE_UNAVAILABLE` | Servicio no disponible | 503 |
| `SEARCH_ERROR` | Error en búsqueda | 500 |
| `EMBEDDING_ERROR` | Error en embeddings | 500 |
| `STORAGE_ERROR` | Error en almacenamiento | 500 |

## 5. Headers de Respuesta Estándar

```
Content-Type: application/json
X-Request-ID: uuid
X-Response-Time: 150ms
X-Cache-Hit: true|false
X-Total-Results: 100
X-Page-Count: 10
```

## 6. Validación de Contratos

### 6.1 Reglas de Validación

- **Campos requeridos**: Deben estar presentes y no ser null
- **Tipos de datos**: Deben coincidir con los especificados
- **Rangos**: Los valores numéricos deben estar en rangos válidos
- **Formatos**: Fechas en ISO 8601, URLs válidas
- **Tamaños**: Límites en longitud de strings y arrays

### 6.2 Ejemplos de Validación

```python
# Validación de entrada de búsqueda
def validate_search_input(data):
    required_fields = ['query', 'text']
    for field in required_fields:
        if field not in data['query']:
            raise ValueError(f"Campo requerido faltante: {field}")
    
    if len(data['query']['text']) > 1000:
        raise ValueError("Query text demasiado largo")
    
    if data['query'].get('top_k', 10) > 100:
        raise ValueError("top_k excede el límite máximo")
```

## 7. Versionado de Contratos

### 7.1 Estrategia de Versionado

- **Versión mayor**: Cambios incompatibles
- **Versión menor**: Nuevas características compatibles
- **Versión patch**: Correcciones de bugs

### 7.2 Headers de Versionado

```
API-Version: 1.0
Accept-Version: 1.0,1.1
```

## 8. Documentación de Cambios

### 8.1 Changelog

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 1.0.0 | 2024-01-01 | Versión inicial |
| 1.1.0 | 2024-02-01 | Agregado soporte para filtros avanzados |
| 1.2.0 | 2024-03-01 | Agregado métricas de performance |

### 8.2 Migración

Para migrar entre versiones:

1. Revisar changelog
2. Actualizar validaciones
3. Probar compatibilidad
4. Implementar gradualmente
