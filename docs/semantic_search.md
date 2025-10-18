# Sistema de Búsqueda Semántica

## Descripción General

El sistema de búsqueda semántica implementa capacidades de búsqueda KNN (K-Nearest Neighbors) usando embeddings vectoriales almacenados en Redis. Permite encontrar documentos similares basándose en similitud semántica del contenido.

## Componentes Principales

### EmbeddingManager

La clase principal que maneja:
- Generación de embeddings usando Azure OpenAI o embeddings dummy
- Almacenamiento y recuperación de embeddings en Redis
- Búsqueda semántica KNN
- Operaciones CRUD completas

### Métodos Principales

#### `execute_query()`

```python
def execute_query(self, 
                 np_vector: List[float], 
                 return_fields: List[str] = None,
                 search_type: str = "KNN", 
                 number_of_results: int = 20) -> List[Dict[str, Any]]:
```

**Parámetros:**
- `np_vector`: Vector de consulta para búsqueda de similitud
- `return_fields`: Campos a retornar (default: ['text', 'filename'])
- `search_type`: Tipo de búsqueda (default: "KNN")
- `number_of_results`: Número de resultados (default: 20)

**Retorna:**
- Lista de documentos similares con puntuaciones de similitud

#### `create_embedding_with_filename()`

```python
def create_embedding_with_filename(self, 
                                 document_id: str, 
                                 text: str, 
                                 metadata: Dict[str, Any],
                                 filename: str = None) -> bool:
```

**Parámetros:**
- `document_id`: Identificador único del documento
- `text`: Contenido de texto a procesar
- `metadata`: Metadatos adicionales
- `filename`: Nombre del archivo (opcional)

## Implementación de Búsqueda KNN

### Algoritmo de Similitud

El sistema utiliza **similitud coseno** para calcular la similitud entre vectores:

```python
def _calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
    # Calcula similitud coseno entre dos vectores
    dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
    magnitude1 = sum(a * a for a in embedding1) ** 0.5
    magnitude2 = sum(b * b for b in embedding2) ** 0.5
    similarity = dot_product / (magnitude1 * magnitude2)
    return max(0.0, min(1.0, similarity))  # Clamp entre 0 y 1
```

### Proceso de Búsqueda

1. **Generación de Embedding**: Se genera un embedding para la consulta
2. **Recuperación de Documentos**: Se obtienen todos los embeddings almacenados
3. **Cálculo de Similitud**: Se calcula la similitud coseno con cada documento
4. **Ordenamiento**: Se ordenan por puntuación de similitud (descendente)
5. **Retorno**: Se devuelven los top-k resultados

## Uso del Sistema

### Ejemplo Básico

```python
from utilities.embedding_manager import get_embedding_manager

# Obtener manager
manager = get_embedding_manager()

# Crear embedding
success = manager.create_embedding_with_filename(
    document_id="doc-001",
    text="Este es un documento sobre inteligencia artificial",
    metadata={"category": "AI", "author": "Usuario"},
    filename="ai_document.txt"
)

# Buscar documentos similares
query_embedding = manager._generate_embedding("¿Qué es la IA?")
results = manager.execute_query(
    np_vector=query_embedding,
    return_fields=['text', 'filename'],
    number_of_results=5
)

# Procesar resultados
for result in results:
    print(f"Documento: {result['document_id']}")
    print(f"Similitud: {result['score']:.4f}")
    print(f"Archivo: {result['filename']}")
```

### Ejemplo Avanzado

```python
# Múltiples consultas
queries = [
    "machine learning algorithms",
    "web development frameworks", 
    "data science tools"
]

for query in queries:
    print(f"\nBuscando: {query}")
    query_embedding = manager._generate_embedding(query)
    results = manager.execute_query(
        np_vector=query_embedding,
        return_fields=['text', 'filename'],
        number_of_results=3
    )
    
    for result in results:
        print(f"  - {result['document_id']} (similitud: {result['score']:.4f})")
```

## Configuración

### Variables de Entorno

```bash
# Redis
AZURE_REDIS_CONNECTIONSTRING=localhost
AZURE_REDIS_CONNECTIONSTRING=6379
AZURE_REDIS_CONNECTIONSTRING=

# Azure OpenAI (opcional)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
OPENAI_API_KEY=your-azure-openai-key
AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT=text-embedding-ada-002

# Embeddings
REDIS_EMBEDDING_TTL=2592000  # 30 días
```

### Configuración de Embeddings

- **Dimensiones**: 1536 (compatible con OpenAI)
- **Métrica de Distancia**: Similitud Coseno
- **TTL**: 30 días por defecto
- **Formato**: JSON con metadatos

## Pruebas

### Script de Prueba

```bash
# Probar búsqueda semántica completa
python scripts/test_semantic_search.py
```

Este script:
1. Crea múltiples documentos de prueba
2. Ejecuta búsquedas semánticas variadas
3. Prueba diferentes escenarios
4. Limpia los documentos de prueba

### Casos de Prueba

- **Búsqueda por categoría**: Consultas específicas por tema
- **Búsqueda mixta**: Consultas que abarcan múltiples temas
- **Búsqueda sin resultados**: Consultas únicas sin coincidencias
- **Diferentes top-k**: Variar el número de resultados

## Limitaciones Actuales

### Implementación Simplificada

La implementación actual usa una búsqueda lineal en lugar de índices vectoriales optimizados:

- ✅ **Funcional**: Búsqueda KNN básica funciona
- ⚠️ **Rendimiento**: O(n) en lugar de O(log n)
- ⚠️ **Escalabilidad**: Limitada para grandes volúmenes

### Mejoras Futuras

1. **RediSearch Vector**: Implementar índices vectoriales nativos
2. **Redis Stack**: Usar Redis Stack con capacidades vectoriales
3. **Optimización**: Implementar búsqueda aproximada (ANN)
4. **Caché**: Agregar caché de consultas frecuentes

## Integración con RediSearch

### Implementación Futura

Para usar RediSearch completo:

```python
# Crear índice vectorial
schema = (
    redis.search.TextField("text"),
    redis.search.TextField("filename"),
    redis.search.VectorField(
        "embeddings", 
        "FLOAT32", 
        1536,
        "FLAT", 
        {
            "TYPE": "FLOAT32",
            "DIM": 1536,
            "DISTANCE_METRIC": "COSINE"
        }
    )
)

# Query KNN
query = f"*=>[KNN {number_of_results} @embeddings $vec_param AS score]"
results = redis_client.ft("embeddings_idx").search(
    query,
    query_params={'vec_param': vector_str},
    dialect=2
)
```

## Monitoreo y Estadísticas

### Métricas Disponibles

```python
stats = manager.get_stats()
# Retorna:
# - total_embeddings: Número total de embeddings
# - redis_connected: Estado de conexión Redis
# - azure_openai_configured: Configuración de Azure OpenAI
# - embedding_deployment: Modelo de embedding
# - redis_ttl: Tiempo de vida de embeddings
```

## Troubleshooting

### Problemas Comunes

1. **Redis no conectado**
   - Verificar variables de entorno
   - Comprobar que Redis esté ejecutándose

2. **Sin resultados de búsqueda**
   - Verificar que existan embeddings
   - Comprobar similitud de consulta

3. **Errores de embedding**
   - Verificar configuración de Azure OpenAI
   - Usar embeddings dummy para desarrollo

### Logs

El sistema registra logs detallados:
- Creación/eliminación de embeddings
- Resultados de búsqueda
- Errores de conexión
- Estadísticas de rendimiento 