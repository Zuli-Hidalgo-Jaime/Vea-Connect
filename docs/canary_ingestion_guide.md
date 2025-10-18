# Guía de Canary - Ingesta y Búsqueda Híbrida

## Resumen

Esta guía describe cómo usar los scripts de canary para probar la ingesta con visión/OCR y búsqueda híbrida sin afectar el pipeline de producción.

## Características

### ✅ No Invasivo
- No modifica el pipeline actual
- No indexa documentos reales
- No afecta servicios de producción

### ✅ Modo Canary
- Feature flag controlado (`CANARY_INGEST_ENABLED`)
- Salida a stdout para inspección
- Graceful degradation si faltan servicios

### ✅ Testing Completo
- Procesamiento de PDF + imágenes
- Extracción de texto con visión/OCR
- Generación de embeddings
- Construcción de payloads de búsqueda
- Búsqueda híbrida (BM25 + vector)

## Configuración

### 1. Feature Flag

Agregar a variables de entorno:
```bash
# Habilitar canary de ingesta
CANARY_INGEST_ENABLED=True
```

### 2. Variables Requeridas

Para funcionalidad completa, configurar:

```bash
# Azure AI Search
AZURE_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
AZURE_SEARCH_API_KEY=your-search-api-key
AZURE_SEARCH_INDEX_NAME=your-index-name

# Azure OpenAI (para embeddings)
AZURE_OPENAI_ENDPOINT=https://your-openai-resource.openai.azure.com
AZURE_OPENAI_API_KEY=your-openai-api-key

# Azure Vision (para OCR)
VISION_ENDPOINT=https://your-vision-resource.cognitiveservices.azure.com
VISION_KEY=your-vision-api-key
```

## Uso de los Canaries

### 1. Canary de Ingesta

#### Comando Django
```bash
# Procesar carpeta de prueba
python manage.py ingest_canary --path /path/to/test/folder

# Con opciones personalizadas
python manage.py ingest_canary \
    --path /path/to/test/folder \
    --chunk-size 1500 \
    --overlap 300 \
    --output-format json \
    --verbose
```

#### Parámetros Disponibles

| Parámetro | Descripción | Default |
|-----------|-------------|---------|
| `--path` | Ruta a carpeta de prueba | Requerido |
| `--chunk-size` | Tamaño de chunks de texto | 1000 |
| `--overlap` | Solapamiento entre chunks | 200 |
| `--output-format` | Formato de salida (json/text/summary) | summary |
| `--verbose` | Salida detallada | False |

#### Formatos de Salida

**Summary (default):**
```
============================================================
CANARY INGESTION SUMMARY
============================================================
Total Files: 3
Successful: 3
Failed: 0
Total Chunks: 15
Total Embeddings: 15
Total Payloads: 15
Total Processing Time: 12.45s
Average Time per File: 4.15s
```

**JSON:**
```json
[
  {
    "file_path": "/path/to/document.pdf",
    "file_name": "document.pdf",
    "status": "success",
    "processing_time": 4.15,
    "sha256": "abc123...",
    "chunks": [...],
    "embeddings": [...],
    "payloads": [...]
  }
]
```

### 2. Canary de Búsqueda Híbrida

#### Script Python
```bash
# Ejecutar demostración completa
python scripts/search/hybrid_canary.py
```

#### Salida de Ejemplo
```
🚀 Hybrid Search Canary - VEA Connect
============================================================

🔧 Service Status:
========================================
Azure AI Search: ✅ Available
Azure OpenAI: ✅ Available
Azure Vision: ✅ Available

🧪 Search Scenarios Demonstration:
============================================================

📝 Scenario: Donaciones Ministeriales
Query: 'donaciones ministerios gobierno'
Filters: {'source_type': 'canary_test'}

🔍 Executing Hybrid Search for: 'donaciones ministerios gobierno'
============================================================
📋 Hybrid Query Structure:
{
  "query_type": "hybrid",
  "search_text": "donaciones ministerios gobierno",
  "weights": {
    "bm25": 0.3,
    "vector": 0.7
  },
  "rerank": true
}

Results (3 found):
  1. Documento de Donaciones Ministeriales (Score: 0.891)
     Este documento describe los procesos de donaciones...
```

## Casos de Uso

### 1. Testing de Pipeline de Ingesta

```bash
# Crear carpeta de prueba
mkdir test_documents
cp sample_documents/* test_documents/

# Probar ingesta
python manage.py ingest_canary --path test_documents --verbose

# Verificar resultados
python manage.py ingest_canary --path test_documents --output-format json > results.json
```

### 2. Validación de Configuración

```bash
# Verificar servicios disponibles
python scripts/search/hybrid_canary.py

# Si faltan servicios, configurar variables de entorno
export AZURE_SEARCH_ENDPOINT="..."
export AZURE_SEARCH_API_KEY="..."
# ... etc
```

### 3. Testing de Búsqueda Híbrida

```bash
# Probar diferentes escenarios de búsqueda
python scripts/search/hybrid_canary.py

# Los resultados muestran:
# - Estructura de queries híbridas
# - Puntuaciones BM25 vs Vector
# - Combinación de resultados
# - Reranking
```

## Estructura de Datos

### Payloads de Búsqueda

Los canaries generan payloads listos para indexación:

```json
{
  "id": "sha256_0",
  "document_id": "sha256",
  "text": "Texto extraído del chunk...",
  "title": "nombre_archivo.pdf",
  "content": "Texto extraído del chunk...",
  "embedding": [0.1, 0.2, ...],
  "metadata": "{\"filename\": \"...\", \"sha256\": \"...\", \"chunk_index\": 0}",
  "source_type": "canary_test",
  "filename": "nombre_archivo.pdf"
}
```

### Queries Híbridas

```json
{
  "query_type": "hybrid",
  "search_text": "query text",
  "query_embedding": [0.1, 0.2, ...],
  "bm25_query": {
    "type": "full",
    "search": "query text",
    "searchFields": ["title", "content"]
  },
  "vector_query": {
    "type": "vector",
    "vector": [0.1, 0.2, ...],
    "fields": ["embedding"]
  },
  "weights": {
    "bm25": 0.3,
    "vector": 0.7
  }
}
```

## Troubleshooting

### Problemas Comunes

#### 1. Canary Deshabilitado
```
Canary ingestion is disabled. Set CANARY_INGEST_ENABLED=True to enable.
```
**Solución:** Configurar `CANARY_INGEST_ENABLED=True`

#### 2. Servicios No Disponibles
```
⚠️ Azure Vision service not available (import failed)
```
**Solución:** Verificar variables de entorno y dependencias

#### 3. No Se Encontraron Archivos
```
No supported files found in: /path/to/folder
```
**Solución:** Verificar que la carpeta contenga archivos soportados (.pdf, .jpg, .png, etc.)

#### 4. Error de Procesamiento
```
❌ Error processing document.pdf: [Error details]
```
**Solución:** Verificar permisos de archivo y configuración de servicios

### Logs y Debugging

#### Habilitar Logs Detallados
```bash
# Para ingesta
python manage.py ingest_canary --path /test/folder --verbose

# Para búsqueda
export PYTHONPATH=.
python scripts/search/hybrid_canary.py
```

#### Verificar Configuración
```bash
# Verificar variables de entorno
env | grep AZURE
env | grep VISION
env | grep CANARY
```

## Integración con Pipeline de Producción

### Migración Gradual

1. **Fase 1: Testing con Canary**
   ```bash
   # Probar con datos de prueba
   python manage.py ingest_canary --path test_data/
   ```

2. **Fase 2: Validación de Resultados**
   ```bash
   # Verificar calidad de extracción
   python manage.py ingest_canary --path test_data/ --output-format json > validation.json
   ```

3. **Fase 3: Testing de Búsqueda**
   ```bash
   # Probar búsqueda híbrida
   python scripts/search/hybrid_canary.py
   ```

4. **Fase 4: Activación en Producción**
   ```bash
   # Habilitar en entorno de producción
   export CANARY_INGEST_ENABLED=True
   ```

### Rollback

Para deshabilitar canaries:
```bash
# Deshabilitar feature flag
export CANARY_INGEST_ENABLED=False

# O eliminar variable
unset CANARY_INGEST_ENABLED
```

## Métricas y Monitoreo

### Métricas de Ingesta

- **Tiempo de procesamiento** por archivo
- **Tasa de éxito** de extracción
- **Número de chunks** generados
- **Calidad de embeddings** (dimensiones)

### Métricas de Búsqueda

- **Puntuaciones híbridas** (BM25 + Vector)
- **Tiempo de respuesta** de queries
- **Relevancia** de resultados
- **Cobertura** de servicios

## Próximos Pasos

1. **Configurar entorno de prueba** con datos reales
2. **Validar calidad** de extracción de texto
3. **Optimizar parámetros** de chunking
4. **Ajustar pesos** de búsqueda híbrida
5. **Integrar** con pipeline de producción

## Soporte

Para problemas o preguntas:
- Revisar logs detallados con `--verbose`
- Verificar configuración de servicios
- Consultar documentación de Azure AI Search
- Revisar ejemplos en `scripts/search/hybrid_canary.py`

