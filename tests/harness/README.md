# Harness de Testing - VEA Connect

## Resumen

Este harness proporciona mocks puros para testing aislado sin dependencias de Django. Permite probar contratos I/O, validar esquemas y simular flujos completos de la aplicación sin necesidad de configuración externa.

## Características

### ✅ Mocks Puros
- **Sin dependencias de Django**: Funciona independientemente del framework
- **Sin configuración externa**: No requiere servicios reales
- **Resultados consistentes**: Comportamiento predecible para testing

### ✅ Contratos I/O Validados
- **Esquemas estandarizados**: Según `docs/api/contracts.md`
- **Validación automática**: Tests que verifican cumplimiento
- **Tipos de datos correctos**: Estructuras compatibles con producción

### ✅ Escenarios de Testing
- **Flujos normales**: Operaciones exitosas
- **Manejo de errores**: Fallos de conexión, timeouts
- **Casos edge**: Datos vacíos, valores límite

## Estructura

```
tests/harness/
├── __init__.py                 # Exportaciones del paquete
├── mock_openai.py             # Mock de OpenAI (embeddings, chat)
├── mock_search.py             # Mock de Azure AI Search
├── mock_storage.py            # Mock de Azure Storage
├── mock_redis.py              # Mock de Redis Cache
├── test_contract_validation.py # Tests de validación
├── example_usage.py           # Ejemplos de uso
└── README.md                  # Esta documentación
```

## Uso Rápido

### 1. Importar Mocks

```python
from tests.harness import (
    create_mock_openai_client,
    create_mock_search_client,
    create_mock_blob_service_client,
    create_mock_redis_client
)
```

### 2. Crear Clientes

```python
# Clientes básicos
openai_client = create_mock_openai_client()
search_client = create_mock_search_client()
storage_client = create_mock_blob_service_client()
redis_client = create_mock_redis_client()
```

### 3. Usar Funcionalidad

```python
# Búsqueda
response = search_client.search("inteligencia artificial", top=5)
print(f"Resultados: {len(response.results)}")

# OpenAI
chat_response = openai_client.chat().completions().create(
    messages=[{"role": "user", "content": "Hola"}],
    model="gpt-4"
)
print(f"Respuesta: {chat_response.choices[0].message.content}")

# Cache
redis_client.set_emb("texto", [0.1, 0.2, 0.3])
cached = redis_client.get_emb("texto")
```

## Mocks Disponibles

### Mock OpenAI

**Funcionalidades:**
- Embeddings (text-embedding-ada-002)
- Chat completions (gpt-4, gpt-3.5-turbo)
- Tokens y métricas de uso

**Ejemplo:**
```python
from tests.harness import create_mock_openai_client

client = create_mock_openai_client()

# Embeddings
embedding_response = client.embeddings().create(
    input=["Hola mundo", "Test embedding"],
    model="text-embedding-ada-002"
)
print(f"Embeddings: {len(embedding_response.data)}")

# Chat
chat_response = client.chat().completions().create(
    messages=[{"role": "user", "content": "¿Cómo estás?"}],
    model="gpt-4"
)
print(f"Respuesta: {chat_response.choices[0].message.content}")
```

### Mock Azure AI Search

**Funcionalidades:**
- Búsqueda híbrida/semántica/vectorial
- Filtros y paginación
- Sugerencias
- Documentos con metadata completa

**Ejemplo:**
```python
from tests.harness import create_mock_search_client

client = create_mock_search_client()

# Búsqueda
response = client.search(
    search_text="machine learning",
    top=10,
    search_type="hybrid",
    filters={"document_type": ["pdf"]}
)

for result in response.results:
    print(f"- {result.document.metadata['filename']}: {result.score}")

# Sugerencias
suggestions = client.suggest("django")
for suggestion in suggestions:
    print(f"- {suggestion['text']}")
```

### Mock Azure Storage

**Funcionalidades:**
- Operaciones de blob (upload, download, delete)
- Contenedores y metadata
- SAS tokens
- Propiedades de archivos

**Ejemplo:**
```python
from tests.harness import create_mock_blob_service_client

client = create_mock_blob_service_client()

# Listar contenedores
containers = client.list_containers()
print(f"Contenedores: {[c['name'] for c in containers]}")

# Subir blob
container = client.get_container_client("vea-documents")
result = container.upload_blob(
    "test/file.txt",
    "contenido de prueba",
    content_type="text/plain"
)
print(f"Blob subido: {result}")

# Generar SAS token
blob_client = client.get_blob_client("vea-documents", "documents/file.pdf")
sas_token = blob_client.generate_sas(permission="r")
print(f"SAS: {sas_token[:50]}...")
```

### Mock Redis

**Funcionalidades:**
- Operaciones básicas (set, get, delete, ttl)
- Cache específico del proyecto (emb, ans, sas)
- Simulación de fallos y timeouts
- Estadísticas del cache

**Ejemplo:**
```python
from tests.harness import create_mock_redis_client

client = create_mock_redis_client()

# Operaciones básicas
client.set("key", "value", ex=3600)
value = client.get("key")
print(f"Valor: {value}")

# Cache específico
client.set_emb("texto", [0.1] * 1536)
client.set_ans("query", {"results": [], "total": 0})
client.set_sas("blob", "sas_token_here")

# Estadísticas
stats = client.get_cache_stats()
print(f"Total keys: {stats['total_keys']}")
```

## Tests de Validación

### Ejecutar Tests

```bash
# Ejecutar todos los tests
pytest tests/harness/test_contract_validation.py -v

# Ejecutar tests específicos
pytest tests/harness/test_contract_validation.py::TestSearchContractValidation -v
```

### Tests Disponibles

1. **TestSearchContractValidation**: Valida contratos de búsqueda/RAG
2. **TestBotResponseContractValidation**: Valida contratos de respuesta del bot
3. **TestDownloadContractValidation**: Valida contratos de descarga
4. **TestErrorContractValidation**: Valida estructura de errores
5. **TestMockIntegrationValidation**: Valida integración entre mocks
6. **TestPerformanceValidation**: Valida métricas de performance

## Ejemplos de Uso

### Flujo Completo de Búsqueda

```python
from tests.harness import (
    create_mock_openai_client,
    create_mock_search_client,
    create_mock_redis_client
)

# Clientes
openai_client = create_mock_openai_client()
search_client = create_mock_search_client()
redis_client = create_mock_redis_client()

# 1. Verificar cache
query = "¿Qué es machine learning?"
cached_response = redis_client.get_ans(query)

if cached_response:
    print("✅ Respuesta en cache")
    results = cached_response
else:
    # 2. Realizar búsqueda
    search_response = search_client.search(query, top=3)
    results = {
        "results": [
            {
                "id": result.document.id,
                "content": result.document.content[:200],
                "score": result.score
            }
            for result in search_response.results
        ]
    }
    
    # 3. Cachear resultados
    redis_client.set_ans(query, results)

# 4. Generar respuesta
context = " ".join([r["content"] for r in results["results"]])
messages = [
    {"role": "user", "content": f"Contexto: {context}\n\nPregunta: {query}"}
]

chat_response = openai_client.chat().completions().create(
    messages=messages,
    model="gpt-4"
)

print(f"Respuesta: {chat_response.choices[0].message.content}")
```

### Simulación de Errores

```python
from tests.harness import create_mock_redis_unavailable, create_mock_redis_with_timeouts

# Redis no disponible
redis_down = create_mock_redis_unavailable()
result = redis_down.set("key", "value")
print(f"Set con Redis down: {result}")  # False

# Redis con timeouts
redis_timeout = create_mock_redis_with_timeouts(probability=0.3)
for i in range(5):
    result = redis_timeout.set(f"key_{i}", f"value_{i}")
    print(f"Set {i}: {'✅' if result else '❌'}")
```

## Escenarios de Testing

### 1. Testing de Contratos

```python
def test_search_contract():
    """Validar que la búsqueda cumple el contrato."""
    client = create_mock_search_client()
    response = client.search("test", top=5)
    
    # Validar estructura
    assert hasattr(response, 'results')
    assert hasattr(response, 'total_count')
    assert hasattr(response, 'search_time_ms')
    
    # Validar tipos
    assert isinstance(response.results, list)
    assert isinstance(response.total_count, int)
    assert isinstance(response.search_time_ms, int)
    
    # Validar rangos
    assert response.total_count >= 0
    assert response.search_time_ms >= 0
```

### 2. Testing de Integración

```python
def test_openai_search_integration():
    """Validar integración entre OpenAI y Search."""
    openai_client = create_mock_openai_client()
    search_client = create_mock_search_client()
    
    # Búsqueda
    search_response = search_client.search("AI", top=3)
    context = " ".join([r.document.content[:100] for r in search_response.results])
    
    # Generar respuesta
    messages = [
        {"role": "user", "content": f"Contexto: {context}\n\nPregunta: ¿Qué es AI?"}
    ]
    
    chat_response = openai_client.chat().completions().create(
        messages=messages,
        model="gpt-4"
    )
    
    assert len(chat_response.choices) > 0
    assert len(chat_response.choices[0].message.content) > 0
```

### 3. Testing de Performance

```python
def test_cache_performance():
    """Validar métricas de performance del cache."""
    redis_client = create_mock_redis_client()
    
    # Llenar cache
    for i in range(100):
        redis_client.set_emb(f"text_{i}", [0.1] * 1536)
    
    # Obtener estadísticas
    stats = redis_client.get_cache_stats()
    
    assert stats["total_keys"] >= 100
    assert "vea" in stats["namespaces"]
    assert stats["memory_usage"] > 0
```

## Configuración Avanzada

### Personalizar Mocks

```python
# Mock con datos predefinidos
from tests.harness import create_mock_redis_with_data

data = {
    "vea:emb:text1": [0.1, 0.2, 0.3],
    "vea:ans:query1": {"results": [], "total": 0}
}
redis_client = create_mock_redis_with_data(data)

# Mock con timeouts
from tests.harness import create_mock_redis_with_timeouts
redis_client = create_mock_redis_with_timeouts(probability=0.5)
```

### Simular Problemas de Conexión

```python
# Simular fallo de conexión
redis_client = create_mock_redis_client()
redis_client.simulate_connection_failure(available=False)

# Simular timeout
redis_client.simulate_timeout(timeout=True)

# Establecer probabilidad de timeout
redis_client.set_timeout_probability(0.3)
```

## Ejecutar Demostración

```bash
# Ejecutar ejemplo completo
python tests/harness/example_usage.py
```

Esto ejecutará todas las demostraciones:
- 🔍 Búsqueda
- 🤖 OpenAI
- 📁 Storage
- 🔴 Redis
- 🔄 Flujo integrado
- ⚠️ Escenarios de error

## Ventajas del Harness

### ✅ Aislamiento
- **Sin dependencias externas**: No requiere servicios reales
- **Sin configuración**: Funciona inmediatamente
- **Sin efectos secundarios**: No modifica datos reales

### ✅ Consistencia
- **Resultados predecibles**: Comportamiento conocido
- **Contratos validados**: Cumple esquemas definidos
- **Tipos correctos**: Estructuras compatibles

### ✅ Flexibilidad
- **Escenarios configurables**: Diferentes configuraciones
- **Simulación de errores**: Fallos controlados
- **Testing completo**: Cobertura de casos edge

### ✅ Productividad
- **Desarrollo rápido**: No esperar servicios
- **Testing eficiente**: Ejecución inmediata
- **Debugging fácil**: Comportamiento transparente

## Integración con CI/CD

### GitHub Actions

```yaml
name: Test Harness
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: pip install pytest
      - name: Run harness tests
        run: pytest tests/harness/ -v
```

### Local Development

```bash
# Instalar dependencias
pip install pytest

# Ejecutar tests
pytest tests/harness/ -v

# Ejecutar con coverage
pytest tests/harness/ --cov=tests.harness --cov-report=html
```

## Troubleshooting

### Problemas Comunes

1. **ImportError**: Verificar que estás en el directorio correcto
2. **AttributeError**: Verificar que usas las funciones correctas
3. **TypeError**: Verificar tipos de datos en contratos

### Debugging

```python
# Habilitar logging detallado
import logging
logging.basicConfig(level=logging.DEBUG)

# Verificar comportamiento de mocks
client = create_mock_redis_client()
print(f"Redis disponible: {client.ping()}")
print(f"Estadísticas: {client.get_cache_stats()}")
```

## Contribuir

### Agregar Nuevos Mocks

1. Crear archivo `mock_service.py`
2. Implementar interfaz compatible
3. Agregar tests de validación
4. Actualizar `__init__.py`
5. Documentar en README

### Mejorar Tests

1. Identificar casos edge
2. Agregar validaciones específicas
3. Mejorar cobertura
4. Optimizar performance

## Licencia

Este harness es parte del proyecto VEA Connect y sigue las mismas políticas de licenciamiento.
