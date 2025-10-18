# Embedding API - Ejemplos de Uso

## Descripción

La API de Embeddings expone operaciones CRUD y búsqueda semántica a través de endpoints HTTP. Todos los endpoints retornan respuestas JSON estandarizadas con campos `status`, `message`, `data` y `timestamp`.

## Endpoints Disponibles

### 1. Health Check
```bash
# Verificar estado de la API
GET /api/embeddings/health
```

### 2. Crear Embedding
```bash
# Crear un nuevo embedding
POST /api/embeddings/create
```

### 3. Obtener Embedding
```bash
# Obtener embedding por ID
GET /api/embeddings/get?id=<document_id>
```

### 4. Actualizar Embedding
```bash
# Actualizar embedding existente
PUT /api/embeddings/update
```

### 5. Eliminar Embedding
```bash
# Eliminar embedding por ID
DELETE /api/embeddings/delete?id=<document_id>
```

### 6. Búsqueda Semántica
```bash
# Buscar documentos similares
POST /api/embeddings/search
```

### 7. Estadísticas
```bash
# Obtener estadísticas del sistema
GET /api/embeddings/stats
```

## Ejemplos con HTTPie

### Configuración Base
```bash
# URL base para desarrollo local
BASE_URL="http://localhost:7071"

# URL base para Azure Functions (reemplazar con tu URL)
# BASE_URL="https://your-function-app.azurewebsites.net"
```

### 1. Health Check
```bash
http GET $BASE_URL/api/embeddings/health
```

**Respuesta esperada:**
```json
{
  "status": "success",
  "message": "Health check completed",
  "data": {
    "status": "healthy",
    "redis_connected": true,
    "timestamp": "2024-01-01T00:00:00.000000"
  },
  "timestamp": "2024-01-01T00:00:00.000000"
}
```

### 2. Crear Embedding
```bash
http POST $BASE_URL/api/embeddings/create \
  document_id="doc-001" \
  text="Artificial Intelligence is revolutionizing technology by enabling machines to perform complex tasks." \
  metadata:='{"category": "AI", "difficulty": "intermediate", "tags": ["AI", "technology"]}'
```

**Respuesta esperada:**
```json
{
  "status": "success",
  "message": "Embedding created successfully",
  "data": {
    "document_id": "doc-001",
    "created_at": "2024-01-01T00:00:00.000000"
  },
  "timestamp": "2024-01-01T00:00:00.000000"
}
```

### 3. Obtener Embedding
```bash
http GET $BASE_URL/api/embeddings/get?id=doc-001
```

**Respuesta esperada:**
```json
{
  "status": "success",
  "message": "Embedding retrieved successfully",
  "data": {
    "document_id": "doc-001",
    "text": "Artificial Intelligence is revolutionizing technology...",
    "metadata": {
      "category": "AI",
      "difficulty": "intermediate",
      "tags": ["AI", "technology"]
    },
    "created_at": "2024-01-01T00:00:00.000000",
    "updated_at": "2024-01-01T00:00:00.000000"
  },
  "timestamp": "2024-01-01T00:00:00.000000"
}
```

### 4. Actualizar Embedding
```bash
http PUT $BASE_URL/api/embeddings/update \
  document_id="doc-001" \
  text="Updated: Artificial Intelligence is transforming the world through intelligent automation and machine learning." \
  metadata:='{"category": "AI", "difficulty": "intermediate", "tags": ["AI", "technology", "ML"], "updated": true}'
```

**Respuesta esperada:**
```json
{
  "status": "success",
  "message": "Embedding updated successfully",
  "data": {
    "document_id": "doc-001",
    "updated_at": "2024-01-01T00:00:00.000000"
  },
  "timestamp": "2024-01-01T00:00:00.000000"
}
```

### 5. Búsqueda Semántica
```bash
http POST $BASE_URL/api/embeddings/search \
  query="How does artificial intelligence work?" \
  top_k:=3
```

**Respuesta esperada:**
```json
{
  "status": "success",
  "message": "Semantic search completed successfully",
  "data": {
    "query": "How does artificial intelligence work?",
    "top_k": 3,
    "results_count": 1,
    "results": [
      {
        "document_id": "doc-001",
        "text": "Updated: Artificial Intelligence is transforming...",
        "metadata": {
          "category": "AI",
          "difficulty": "intermediate",
          "tags": ["AI", "technology", "ML"],
          "updated": true
        },
        "similarity_score": 0.8234,
        "created_at": "2024-01-01T00:00:00.000000",
        "updated_at": "2024-01-01T00:00:00.000000"
      }
    ]
  },
  "timestamp": "2024-01-01T00:00:00.000000"
}
```

### 6. Obtener Estadísticas
```bash
http GET $BASE_URL/api/embeddings/stats
```

**Respuesta esperada:**
```json
{
  "status": "success",
  "message": "Statistics retrieved successfully",
  "data": {
    "total_embeddings": 1,
    "redis_connected": true,
    "azure_openai_configured": false,
    "embedding_deployment": "text-embedding-ada-002",
    "redis_ttl": 2592000
  },
  "timestamp": "2024-01-01T00:00:00.000000"
}
```

### 7. Eliminar Embedding
```bash
http DELETE $BASE_URL/api/embeddings/delete?id=doc-001
```

**Respuesta esperada:**
```json
{
  "status": "success",
  "message": "Embedding deleted successfully",
  "data": {
    "document_id": "doc-001",
    "deleted_at": "2024-01-01T00:00:00.000000"
  },
  "timestamp": "2024-01-01T00:00:00.000000"
}
```

## Ejemplos con cURL

### Crear Embedding
```bash
curl -X POST http://localhost:7071/api/embeddings/create \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "doc-001",
    "text": "Artificial Intelligence is revolutionizing technology.",
    "metadata": {"category": "AI", "difficulty": "intermediate"}
  }'
```

### Búsqueda Semántica
```bash
curl -X POST http://localhost:7071/api/embeddings/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How does AI work?",
    "top_k": 3
  }'
```

## Ejemplos con Python Requests

### Cliente Python Básico
```python
import requests
import json

BASE_URL = "http://localhost:7071"

def create_embedding(document_id, text, metadata=None):
    url = f"{BASE_URL}/api/embeddings/create"
    data = {
        "document_id": document_id,
        "text": text,
        "metadata": metadata or {}
    }
    response = requests.post(url, json=data)
    return response.json()

def search_similar(query, top_k=3):
    url = f"{BASE_URL}/api/embeddings/search"
    data = {
        "query": query,
        "top_k": top_k
    }
    response = requests.post(url, json=data)
    return response.json()

# Ejemplo de uso
result = create_embedding(
    "doc-001",
    "Machine Learning is a subset of AI.",
    {"category": "ML", "difficulty": "intermediate"}
)
print(json.dumps(result, indent=2))

search_result = search_similar("What is machine learning?")
print(json.dumps(search_result, indent=2))
```

## Casos de Error

### 1. Campos Requeridos Faltantes
```bash
http POST $BASE_URL/api/embeddings/create document_id="doc-001"
```

**Respuesta:**
```json
{
  "status": "error",
  "message": "Missing required fields: text",
  "timestamp": "2024-01-01T00:00:00.000000"
}
```

### 2. Documento No Encontrado
```bash
http GET $BASE_URL/api/embeddings/get?id=non-existent
```

**Respuesta:**
```json
{
  "status": "error",
  "message": "Embedding with ID 'non-existent' not found",
  "timestamp": "2024-01-01T00:00:00.000000"
}
```

### 3. Documento Ya Existe
```bash
# Crear el mismo documento dos veces
http POST $BASE_URL/api/embeddings/create document_id="doc-001" text="Test"
http POST $BASE_URL/api/embeddings/create document_id="doc-001" text="Test"
```

**Respuesta:**
```json
{
  "status": "error",
  "message": "Embedding with ID 'doc-001' already exists",
  "timestamp": "2024-01-01T00:00:00.000000"
}
```

## Validación con Postman

### Colección de Postman
1. **Health Check**: `GET {{base_url}}/api/embeddings/health`
2. **Create Embedding**: `POST {{base_url}}/api/embeddings/create`
3. **Get Embedding**: `GET {{base_url}}/api/embeddings/get?id={{document_id}}`
4. **Update Embedding**: `PUT {{base_url}}/api/embeddings/update`
5. **Search Similar**: `POST {{base_url}}/api/embeddings/search`
6. **Delete Embedding**: `DELETE {{base_url}}/api/embeddings/delete?id={{document_id}}`
7. **Get Stats**: `GET {{base_url}}/api/embeddings/stats`

### Variables de Entorno
```json
{
  "base_url": "http://localhost:7071",
  "document_id": "doc-001"
}
```

## CORS

La API incluye soporte completo para CORS:
- `Access-Control-Allow-Origin: *`
- `Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS`
- `Access-Control-Allow-Headers: Content-Type, Authorization`

## Seguridad

- Los vectores de embedding se eliminan de las respuestas por seguridad
- Validación de campos requeridos
- Manejo de errores estandarizado
- Logs detallados para auditoría 