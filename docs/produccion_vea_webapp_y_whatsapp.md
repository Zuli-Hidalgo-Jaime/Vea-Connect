# VEA Connect WebApp - Documentación de Producción y WhatsApp Bot

## 1. Resumen Ejecutivo

VEA Connect es una aplicación web Django desplegada en Azure App Service que gestiona documentos, donaciones, eventos y directorio de contactos para una organización. Integra Azure AI Search para búsqueda semántica y vectorial, Azure OpenAI para generar embeddings y respuestas conversacionales, y Azure Blob Storage para almacenamiento de archivos. El sistema incluye un bot de WhatsApp integrado mediante Azure Communication Services (ACS) que responde consultas de usuarios usando Retrieval-Augmented Generation (RAG) sobre el contenido indexado. Todo el flujo end-to-end opera en producción con PostgreSQL como base de datos y Redis opcional para caché de conversaciones.

---

## 2. Arquitectura (Visión General)

```
┌────────────────────────────────────────────────────────────────────────┐
│                     Azure App Service (Django)                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  Web App (HTTPS)                                                 │  │
│  │  - Documentos, Donaciones, Eventos, Directorio (CRUD)           │  │
│  │  - URLs: /, /documents/, /donations/, /events/, /directory/     │  │
│  │  - Autenticación: Django Auth + JWT                             │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  WhatsApp Bot API                                                │  │
│  │  - Webhook: /api/v1/whatsapp/webhook/                           │  │
│  │  - Handler: apps/whatsapp_bot/handlers.py                       │  │
│  │  - Intents: contact, donations, events, general                 │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                           ↓↑                        ↓↑                  │
└────────────────────────────────────────────────────────────────────────┘
                             ↓↑                        ↓↑
┌─────────────────────┐  ┌──────────────────────┐  ┌─────────────────────┐
│ Azure Communication │  │ Azure OpenAI         │  │ Azure AI Search     │
│ Services (ACS)      │  │ - Embeddings         │  │ - Vector Search     │
│ - WhatsApp Channel  │  │   (text-embedding-   │  │ - Semantic Search   │
│ - Send/Receive      │  │    ada-002)          │  │ - Index: vea-       │
│   Messages          │  │ - Chat (gpt-35-turbo)│  │   connect-index     │
└─────────────────────┘  └──────────────────────┘  └─────────────────────┘
         ↓↑                        ↓↑                        ↓↑
┌─────────────────────┐  ┌──────────────────────┐  ┌─────────────────────┐
│ Azure Blob Storage  │  │ PostgreSQL           │  │ Redis Cache         │
│ - vea-connect-files │  │ - Datos relacionales │  │ - Contexto de       │
│ - documents/*.jpg   │  │ - Usuarios, docs     │  │   conversación      │
│ - *.txt (embeddings)│  │   eventos, donations │  │ - Cache de embedds  │
└─────────────────────┘  └──────────────────────┘  └─────────────────────┘
```

### Tabla de Servicios

| Servicio                      | Rol / Responsabilidad                                                                 |
|-------------------------------|---------------------------------------------------------------------------------------|
| **Azure App Service**         | Hosting de Django webapp; entrypoint HTTPS; manejo de requests/webhooks              |
| **Azure Communication Services (ACS)** | Proveedor de WhatsApp; envío/recepción de mensajes; templates estructurados          |
| **Azure OpenAI**              | Generación de embeddings (text-embedding-ada-002); chat completion (gpt-35-turbo)    |
| **Azure AI Search**           | Índice vectorial y semántico; almacenamiento y búsqueda de documentos/eventos        |
| **Azure Blob Storage**        | Almacenamiento de archivos (.jpg, .txt); contenedor `vea-connect-files`              |
| **PostgreSQL**                | Base de datos relacional; usuarios, documentos, donaciones, eventos, directorio      |
| **Redis** (opcional)          | Caché de contexto de conversaciones WhatsApp; caché de embeddings (TTL configurables)|

---

## 3. Despliegue en Producción (Azure App Service)

### CI/CD

**Estado:** No se encontraron archivos de GitHub Actions (`.github/workflows/*.yml`) ni Azure Pipelines (`azure-pipelines*.yml`) en el repositorio. El despliegue se realiza manualmente o mediante comandos directos de Azure CLI.

### Proceso de Build y Release

**Método detectado:** Django + Gunicorn + WhiteNoise (no Docker).

- **Runtime:** Python 3.10+ (especificado en `runtime.txt` - no encontrado en esta inspección, inferido de `requirements.txt`).
- **Servidor WSGI:** `gunicorn==21.2.0` (ver `requirements.txt`).
- **Archivos estáticos:** `whitenoise==6.6.0` (middleware en `config.wsgi.py`).
- **Entrypoint WSGI:** `config/wsgi.py` → `application = get_wsgi_application()`.
- **Entrypoint ASGI:** `config/asgi.py` (para futuros canales o WebSockets).

**Comando de inicio inferido** (Azure App Service):
```bash
gunicorn --bind=0.0.0.0 --timeout 600 config.wsgi:application
```

**Build flags detectados** (en `config/settings/azure_production.py`):
- `BUILD_FLAGS=UseExpressBuild`
- `SCM_DO_BUILD_DURING_DEPLOYMENT=true`

### Variables de Entorno Requeridas

Ver sección 7 (tabla completa). Principales:

- **Django:** `SECRET_KEY`, `DJANGO_SETTINGS_MODULE=config.settings.azure_production`, `ALLOWED_HOSTS`, `WEBSITE_HOSTNAME`
- **Database:** `AZURE_POSTGRESQL_NAME`, `AZURE_POSTGRESQL_USERNAME`, `AZURE_POSTGRESQL_PASSWORD`, `AZURE_POSTGRESQL_HOST`, `DB_PORT` (default 5432)
- **Azure AI Search:** `AZURE_SEARCH_ENDPOINT`, `AZURE_SEARCH_API_KEY`, `AZURE_SEARCH_INDEX_NAME`
- **Azure OpenAI:** `AZURE_OPENAI_ENDPOINT`, `OPENAI_API_KEY`, `AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT`, `AZURE_OPENAI_CHAT_DEPLOYMENT`, `AZURE_OPENAI_EMBEDDINGS_API_VERSION`, `AZURE_OPENAI_CHAT_API_VERSION`
- **Azure Blob Storage:** `AZURE_STORAGE_ACCOUNT_NAME`, `AZURE_STORAGE_ACCOUNT_KEY`, `AZURE_CONTAINER` (o variables `BLOB_*` como fallback)
- **Azure Communication Services:** `ACS_WHATSAPP_ENDPOINT`, `ACS_WHATSAPP_API_KEY`, `ACS_PHONE_NUMBER`, `WHATSAPP_CHANNEL_ID_GUID`
- **Redis (opcional):** `AZURE_REDIS_URL`, `REDIS_TTL_SECS`

### Health & Readiness

**Endpoints detectados:**

- **General health check:** `GET /health/` → retorna `HttpResponse("OK")` (ruta: `config/urls.py:57`).
- **WhatsApp Bot health:** `GET /api/v1/whatsapp/health/` → verifica DB, cache y configuración ACS (ruta: `apps/whatsapp_bot/views.py:health_check`, líneas 413-461).
- **Cache stats (admin only):** `GET /ops/cache/stats/` → estadísticas de caché (ruta: `config/urls.py:60`).

**Logs en producción:**

- **App Service Logs:** Azure Portal > App Service > "Log stream" o "Diagnose and solve problems".
- **Django Logging:** Configurado en `config/settings/azure_production.py:177-224`.
  - **Handler:** `console` (StreamHandler) + `file` (FileHandler → `logs/django.log`).
  - **Loggers específicos:** `django`, `apps.whatsapp_bot`, `utils.redis_cache`.
  - **Nivel:** INFO en producción.
- **Application Insights:** Si `APPLICATIONINSIGHTS_CONNECTION_STRING` está configurado, los logs se envían a Azure Monitor.

---

## 4. Webapp: Request → Respuesta

### Entrada HTTP

**HTTPS → Azure App Service → Django → `config/urls.py`**

Principales rutas (extracto de `config/urls.py`):

| Ruta                          | Vista/Include                          | Descripción                              |
|-------------------------------|----------------------------------------|------------------------------------------|
| `/`                           | `apps.core.urls`                       | Home, login, logout                      |
| `/admin/`                     | `django.contrib.admin`                 | Panel de administración                  |
| `/dashboard/`                 | `apps.dashboard.urls`                  | Dashboard de usuario                     |
| `/documents/`                 | `apps.documents.urls`                  | CRUD de documentos                       |
| `/donations/`                 | `apps.donations.urls`                  | CRUD de donaciones                       |
| `/events/`                    | `apps.events.urls`                     | CRUD de eventos                          |
| `/directory/`                 | `apps.directory.urls`                  | CRUD de directorio de contactos          |
| `/api/v1/whatsapp/webhook/`   | `apps.whatsapp_bot.views.webhook_handler` | Webhook de WhatsApp (POST)             |
| `/health/`                    | Lambda `HttpResponse("OK")`            | Health check                             |

### Almacenamiento de Archivos y OCR

**Módulo:** `apps/documents/views.py`

**Flujo de creación de documento (upload_document, líneas 31-192):**

1. **Upload inicial:** Usuario sube archivo vía `DocumentForm` (POST a `/documents/create/`).
2. **Guardar en storage:** El archivo se guarda en Azure Blob Storage o local según configuración (`config.azure_storage.AzureMediaStorage` si configurado, `FileSystemStorage` si no).
3. **Normalización de imagen:** Si es imagen, se abre con PIL, se convierte a RGB y se guarda como JPEG (`documents/{document.id}.jpg`).
4. **OCR con Azure Computer Vision:**
   - Se llama a `tasks.document_pipeline.convert_document_to_text(content_file)`.
   - Este método invoca Azure Computer Vision (endpoint: `VISION_ENDPOINT`, key: `VISION_KEY`) para extraer texto de la imagen.
   - Resultado: `ocr_text` (string).
5. **Construcción de embedding_text:**
   ```python
   embedding_text = "\n".join([title, description, ocr_text]).strip()
   ```
6. **Guardar .txt en Blob:**
   ```python
   txt_blob_name = f"{document.id}.txt"
   _upload_blob_overwrite('vea-connect-files', txt_blob_name, embedding_text.encode('utf-8'), 'text/plain; charset=utf-8')
   ```
7. **Generar embedding y upsert en Azure AI Search:** (ver siguiente sección).

**Rutas de archivos clave:**
- `apps/documents/views.py:upload_document` (líneas 31-192)
- `apps/documents/views.py:edit_document` (líneas 405-783) — flujo similar para edición
- `tasks/document_pipeline.py:convert_document_to_text` — OCR wrapper
- `services/storage_service.py:azure_storage` — cliente de Azure Blob Storage

### Indexación a Azure AI Search

**Módulo:** `apps/documents/views.py` (líneas 146-169)

**Flujo:**

1. **Generar embedding:**
   ```python
   vector = generate_embeddings(embedding_text)
   # Llama a tasks.document_pipeline.generate_embeddings(text)
   #   → utilities.embedding_manager.EmbeddingManager.generate_embedding(text)
   #   → apps.embeddings.openai_service.OpenAIService.generate_embedding(text)
   #   → Azure OpenAI API (model: AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT, e.g., text-embedding-ada-002)
   ```

2. **Construir ID de documento vectorial:**
   ```python
   document_vector_id = f"doc_{document.id}"
   ```
   - **Convención:** `doc_<id>` para documentos, `event_<id>` para eventos, etc.

3. **Preparar metadata:**
   ```python
   metadata = {
       'title': title,
       'created_at': created_at_iso,  # ISO 8601 con 'Z'
       'metadata': json.dumps({
           'category': category,
           'description': description,
           'filename': f"documents/{document.id}.jpg",
           'ocr_text': ocr_text or ''
       })
   }
   if isinstance(vector, list) and vector:
       metadata['embedding'] = vector
   ```

4. **Upsert en Azure AI Search:**
   ```python
   search_index_service.upsert_document(document_vector_id, embedding_text, metadata)
   # Implementación: services.search_index_service.SearchIndexService.upsert_document(...)
   #   → azure.search.documents.SearchClient.upload_documents([document])
   ```
   - **Índice:** `vea-connect-index` (o valor de `AZURE_SEARCH_INDEX_NAME`).
   - **Campos del documento:**
     - `id`: `doc_<id>`
     - `content`: `embedding_text` (título + descripción + OCR)
     - `embedding`: vector de embeddings (List[float], 1536 dimensiones para ada-002)
     - `title`: título del documento
     - `created_at`: timestamp ISO 8601
     - `metadata`: JSON stringificado con info adicional
     - `source_type`: (inferido) "document"
     - `filename`: ruta en Blob

**Rutas de archivos clave:**
- `tasks/document_pipeline.py:generate_embeddings` — wrapper que llama a EmbeddingManager
- `utilities/embedding_manager.py:EmbeddingManager.generate_embedding` (líneas 63-90)
- `apps/embeddings/openai_service.py:OpenAIService.generate_embedding` (líneas 118-159)
- `services/search_index_service.py:SearchIndexService.upsert_document` (líneas 38-74)

### Búsqueda Semántica y Vectorial

**Módulo:** `utilities/azure_search_client.py`

**Métodos principales:**

1. **Búsqueda vectorial:** `AzureSearchClient.search_vector(query_vector, top_k, filter_query)` (líneas 181-230)
   - Parámetros: `query_vector` (List[float]), `top_k` (int, default 10), `filter_query` (opcional).
   - Usa `SearchClient.search()` con `vector_queries=[{"vector": query_vector, "k_nearest_neighbors": top_k, "fields": "embedding"}]`.
   - Retorna lista de documentos con `@search.score` (similaridad coseno).

2. **Búsqueda semántica:** `AzureSearchClient.search_semantic(query_text, top_k)` (líneas 232-280)
   - Parámetros: `query_text` (str), `top_k` (int).
   - Usa `SearchClient.search(search_text=query_text, top=top_k, query_type="semantic")`.
   - Retorna lista de documentos con score semántico.

**Normalización de resultados:**

Implementada en `utilities/embedding_manager.py:EmbeddingManager.find_similar` (líneas 92-144):

```python
for item in results:
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

# Filtro por threshold (opcional)
if threshold > 0:
    normalized = [r for r in normalized if r['score'] >= threshold]

# Ordenar descendente por score
normalized.sort(key=lambda r: r['score'], reverse=True)
return normalized[:top_k]
```

**Rutas de archivos clave:**
- `utilities/azure_search_client.py:AzureSearchClient.search_vector` (líneas 181-230)
- `utilities/azure_search_client.py:AzureSearchClient.search_semantic` (líneas 232-280)
- `utilities/embedding_manager.py:EmbeddingManager.find_similar` (líneas 92-144)

---

## 5. Bot de WhatsApp: Webhook y Flujo

### Proveedor Detectado

**Azure Communication Services (ACS)**

**Configuración detectada en `config/settings/base.py` (líneas 266-274):**

```python
ACS_CONNECTION_STRING = os.environ.get('ACS_CONNECTION_STRING', '')
ACS_EVENT_GRID_TOPIC_ENDPOINT = os.environ.get('ACS_EVENT_GRID_TOPIC_ENDPOINT', '')
ACS_EVENT_GRID_TOPIC_KEY = os.environ.get('ACS_EVENT_GRID_TOPIC_KEY', '')
ACS_PHONE_NUMBER = os.environ.get('ACS_PHONE_NUMBER', '')
ACS_WHATSAPP_API_KEY = os.environ.get('ACS_WHATSAPP_API_KEY', '')
ACS_WHATSAPP_ENDPOINT = os.environ.get('ACS_WHATSAPP_ENDPOINT', '')
WHATSAPP_ACCESS_TOKEN = os.environ.get('WHATSAPP_ACCESS_TOKEN', '')
WHATSAPP_CHANNEL_ID_GUID = os.environ.get('WHATSAPP_CHANNEL_ID_GUID', 'c3dd072b-9283-4812-8ed0-10b1d3a45da1')
```

**Variables de entorno requeridas:**
- `ACS_WHATSAPP_ENDPOINT`: URL del servicio ACS (ej: `https://your-acs-resource.communication.azure.com`)
- `ACS_WHATSAPP_API_KEY`: Clave de acceso HMAC-SHA256
- `ACS_PHONE_NUMBER`: Número de teléfono del bot (formato: `whatsapp:+1234567890`)
- `WHATSAPP_CHANNEL_ID_GUID`: GUID del canal de WhatsApp registrado en ACS

**Nota:** No se detectaron variables para Twilio ni Meta Cloud API. El sistema usa exclusivamente ACS.

### Endpoint de Webhook

**Ruta:** `POST /api/v1/whatsapp/webhook/`

**Handler:** `apps/whatsapp_bot/views.py:webhook_handler` (líneas 28-100)

**Payload esperado (POST JSON):**

```json
{
  "from": "whatsapp:+1234567890",
  "to": "whatsapp:+0987654321",
  "message": {
    "text": "Hola, necesito información sobre donaciones"
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**Proceso:**

1. Valida `content-type: application/json`.
2. Extrae `from_number`, `message_text`.
3. Instancia `WhatsAppBotHandler()` e invoca `bot_handler.process_message(from_number, message_text)`.
4. Retorna respuesta JSON con `success`, `message_processed`, `response_type`, `processing_time_ms`.

### Flujo: Mensaje Entrante → Respuesta

**Handler principal:** `apps/whatsapp_bot/handlers.py:WhatsAppBotHandler`

**Diagrama de flujo (líneas 84-136):**

```
1. Recibir mensaje
   ↓
2. Detectar intención (detect_intent)
   ├─ 'contact' → handle_contact_intent
   ├─ 'donations' → handle_donation_intent
   ├─ 'events' → handle_event_intent
   ├─ 'general' → handle_general_intent
   └─ 'unknown' → generate_fallback_response
   ↓
3. Cada handler intenta template primero (_try_template_response)
   ├─ Success → enviar template vía ACS
   └─ Fail → fallback a RAG (_rag_answer)
   ↓
4. RAG Flow (_rag_answer, líneas ~300-450):
   a) Generar embedding de la consulta (embedding_manager.generate_embedding)
   b) Buscar similares en Azure AI Search (embedding_manager.find_similar)
      - top_k=3 (configurable)
      - threshold=0.0 (sin filtro por defecto)
   c) Construir contexto concatenando resultados
   d) Preparar mensajes para OpenAI:
      [
        {"role": "system", "content": "Eres un asistente de VEA..."},
        {"role": "user", "content": f"Contexto: {context}\n\nPregunta: {user_query}"}
      ]
   e) Llamar a OpenAI (OpenAIService.generate_chat_response)
      - Model: AZURE_OPENAI_CHAT_DEPLOYMENT (e.g., gpt-35-turbo)
      - Max tokens: 1000
      - Temperature: 0.7
   f) Retornar respuesta
   ↓
5. Enviar respuesta al usuario (ACSService.send_text_message)
   ↓
6. Registrar interacción en DB (WhatsAppInteraction model)
```

**Funciones clave:**

- `detect_intent(message_text)`: Clasificación simple por keywords (no ML). Retorna: `'contact'`, `'donations'`, `'events'`, `'general'`, `'unknown'`.
- `_rag_answer(user_query)`: Implementa flujo RAG completo.
- `generate_fallback_response(message_text, context)`: Respuesta genérica cuando todo falla.

**Rutas de archivos clave:**
- `apps/whatsapp_bot/handlers.py:WhatsAppBotHandler.process_message` (líneas 84-136)
- `apps/whatsapp_bot/handlers.py:WhatsAppBotHandler._rag_answer` (inferido, ~líneas 300-450)
- `apps/whatsapp_bot/services.py:ACSService.send_text_message` (líneas 111-157)
- `apps/whatsapp_bot/services.py:ACSService.send_template_message` (líneas 45-109)

### Manejo de Errores: Content Filter y Fallback

**Detección de content_filter:**

Implementado en `apps/embeddings/openai_service.py:_is_content_filter_error` (líneas 20-35):

```python
def _is_content_filter_error(err: Exception) -> bool:
    s = str(err).lower()
    return (
        "content_filter" in s
        or "responsibleaipolicyviolation" in s
        or ("content_filter_result" in s and "filtered" in s)
    )
```

**Manejo en `generate_chat_response` (líneas 177-230):**

```python
try:
    response = self.client.chat.completions.create(...)
    return response.choices[0].message.content or ""
except Exception as e:
    if _is_content_filter_error(e):
        logger.warning(f"Content filter triggered: {e}")
        return SAFE_FILTER_MESSAGE  # "No puedo responder esa formulación..."
    else:
        logger.error(f"Error in chat completion: {e}")
        raise
```

**Mensaje de fallback:** 

```python
SAFE_FILTER_MESSAGE = (
    "No puedo responder esa formulación porque activa nuestros filtros de contenido. "
    "Por favor, reformula tu pregunta con un lenguaje neutral y sin términos sensibles."
)
```

**Fallback general** (cuando RAG falla o no hay contexto):

`apps/whatsapp_bot/handlers.py:generate_fallback_response`:
- Mensaje genérico: "Lo siento, no encontré información sobre eso. ¿Puedes reformular tu pregunta?"
- Se registra en WhatsAppInteraction con `fallback_used=True`.

**Rutas de archivos clave:**
- `apps/embeddings/openai_service.py:_is_content_filter_error` (líneas 20-35)
- `apps/embeddings/openai_service.py:OpenAIService.generate_chat_response` (líneas 177-230)

---

## 6. RAG End-to-End (Detalle)

### Módulos Detectados

| Módulo                                        | Rol                                                                 |
|-----------------------------------------------|---------------------------------------------------------------------|
| `utilities/embedding_manager.py`              | Gestor central de embeddings; CRUD y búsqueda en Azure AI Search    |
| `apps/embeddings/openai_service.py`           | Cliente de Azure OpenAI; genera embeddings y chat completion        |
| `services/search_index_service.py`            | Servicio de indexación; wrapper de Azure AI Search                  |
| `utilities/azure_search_client.py`            | Cliente de bajo nivel para Azure AI Search; búsquedas vectoriales   |
| `apps/whatsapp_bot/handlers.py`               | Orquestador del flujo RAG; llamada a embedding_manager y OpenAI     |
| `tasks/document_pipeline.py`                  | Pipeline de procesamiento de documentos (OCR, embeddings, upsert)   |

### Flujo de Generación de Embedding

**Entrada:** `text` (string)

**Salida:** `embedding` (List[float], 1536 dimensiones)

**Flujo:**

1. **Cache check** (si Redis disponible):
   ```python
   cached = get_emb(text)
   if cached:
       return cached
   ```
   - `utils/cache_layer.py:get_emb(text)` → Redis key: `emb:{text}` (TTL configurable).

2. **Llamada a OpenAI:**
   ```python
   response = self.client.embeddings.create(
       input=text,
       model=AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT  # e.g., text-embedding-ada-002
   )
   embedding = response.data[0].embedding
   ```
   - `apps/embeddings/openai_service.py:OpenAIService.generate_embedding` (líneas 118-159).

3. **Cache store:**
   ```python
   set_emb(text, embedding)  # TTL default 3600s
   ```

4. **Retornar embedding.**

**Rutas de archivos clave:**
- `utilities/embedding_manager.py:EmbeddingManager.generate_embedding` (líneas 63-90)
- `apps/embeddings/openai_service.py:OpenAIService.generate_embedding` (líneas 118-159)
- `utils/cache_layer.py:get_emb` y `set_emb` (si existe; fallback a `django.core.cache`)

### Construcción del Campo `content`

**Contexto:** El campo `content` en Azure AI Search contiene todo el texto searchable del documento.

**Construcción (ejemplo de documentos):**

```python
# apps/documents/views.py:upload_document (línea 140)
embedding_text = "\n".join([
    str(title or ''),
    str(description or ''),
    str(ocr_text or '')
]).strip()
```

**¿Por qué concatenar fecha/hora/lugar/banco/CLABE?**

**Respuesta:** No se detectó concatenación explícita de estos campos en el código base. Sin embargo, en el flujo de **donaciones** y **eventos**, estos datos se almacenan en el campo `metadata` (JSON stringificado) y pueden ser extraídos durante la consulta RAG para construir respuestas contextuales.

**Ejemplo inferido (donaciones):**

```python
# apps/donations/signals.py o tasks/donation_pipeline.py (no encontrado explícitamente)
# Hipotético:
embedding_text = "\n".join([
    donation.donation_type,
    donation.description,
    f"Banco: {donation.bank_name}",
    f"CLABE: {donation.clabe_number}",
    f"Fecha: {donation.donation_date}"
])
```

**Nota:** El repositorio no contiene un pipeline explícito de indexación de donaciones/eventos. Es posible que esto se haga manualmente o mediante un script no incluido en el repo actual.

### Top-K, Threshold y Normalización

**Parámetros de búsqueda:**

- **`top_k`**: Número máximo de resultados a retornar (default: 3 en handlers, 10 en cliente base).
- **`threshold`**: Score mínimo para incluir un resultado (default: 0.0, sin filtro).

**Configuración en `apps/whatsapp_bot/handlers.py` (inferido):**

```python
# _rag_answer method
results = self.embedding_manager.find_similar(
    query=user_query,
    top_k=3,
    threshold=0.0
)
```

**Normalización (en `utilities/embedding_manager.py:find_similar`, líneas 121-141):**

```python
for item in results:
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

# Filtro opcional por threshold
if threshold > 0:
    normalized = [r for r in normalized if r['score'] >= threshold]

# Ordenar descendente por score
normalized.sort(key=lambda r: r['score'], reverse=True)
return normalized[:top_k]
```

**Rutas de archivos clave:**
- `utilities/embedding_manager.py:EmbeddingManager.find_similar` (líneas 92-144)
- `apps/whatsapp_bot/handlers.py:WhatsAppBotHandler._rag_answer` (inferido)

### Construcción del Prompt de Chat con Contexto

**Método:** `apps/embeddings/openai_service.py:OpenAIService.generate_chat_response` (líneas 177-230)

**Estructura de mensajes:**

```python
messages = [
    {
        "role": "system",
        "content": "Eres un asistente virtual de VEA Connect. Responde basándote exclusivamente en el contexto provisto."
    },
    {
        "role": "user",
        "content": f"Contexto:\n{context}\n\nPregunta: {user_query}"
    }
]

response = self.client.chat.completions.create(
    model=AZURE_OPENAI_CHAT_DEPLOYMENT,  # e.g., gpt-35-turbo
    messages=messages,
    max_tokens=1000,
    temperature=0.7
)

return response.choices[0].message.content or ""
```

**Construcción del contexto (en handler):**

```python
# Concatenar resultados de búsqueda
context_parts = []
for hit in results:
    text = hit.get('text', '')
    metadata = hit.get('metadata', {})
    context_parts.append(f"- {text}\n  Metadata: {json.dumps(metadata)}")

context = "\n\n".join(context_parts)
```

**Rutas de archivos clave:**
- `apps/embeddings/openai_service.py:OpenAIService.generate_chat_response` (líneas 177-230)
- `apps/whatsapp_bot/handlers.py:WhatsAppBotHandler._rag_answer` (inferido)

---

## 7. Variables de Entorno (Tabla Completa)

| Nombre                                  | Uso                                           | Archivo que lo consume                     | ¿Obligatoria? | Ejemplo de formato                          |
|-----------------------------------------|-----------------------------------------------|--------------------------------------------|---------------|---------------------------------------------|
| `SECRET_KEY`                            | Django secret key                             | `config/settings/base.py`                  | Sí            | `django-insecure-****`                      |
| `DJANGO_SETTINGS_MODULE`                | Módulo de settings a usar                     | `manage.py`, `config/wsgi.py`              | Sí            | `config.settings.azure_production`          |
| `ALLOWED_HOSTS`                         | Hosts permitidos (separados por coma)        | `config/settings/base.py`                  | Sí            | `example.com,*.azurewebsites.net`           |
| `WEBSITE_HOSTNAME`                      | Hostname de Azure App Service                 | `config/settings/azure_production.py`      | Sí            | `veaconnect-webapp-prod-****.azurewebsites.net` |
| `AZURE_POSTGRESQL_NAME`                 | Nombre de la base de datos PostgreSQL        | `config/settings/azure_production.py`      | Sí            | `vea_connect_db`                            |
| `AZURE_POSTGRESQL_USERNAME`             | Usuario de PostgreSQL                         | `config/settings/azure_production.py`      | Sí            | `vea_admin@****`                            |
| `AZURE_POSTGRESQL_PASSWORD`             | Contraseña de PostgreSQL                      | `config/settings/azure_production.py`      | Sí            | `****`                                      |
| `AZURE_POSTGRESQL_HOST`                 | Host de PostgreSQL                            | `config/settings/azure_production.py`      | Sí            | `vea-connect-db.postgres.database.azure.com`|
| `DB_PORT`                               | Puerto de PostgreSQL                          | `config/settings/azure_production.py`      | No            | `5432` (default)                            |
| `AZURE_SEARCH_ENDPOINT`                 | Endpoint de Azure AI Search                   | `config/settings/base.py`, `utilities/azure_search_client.py` | Sí | `https://ai-search-****.search.windows.net` |
| `AZURE_SEARCH_API_KEY`                  | API key de Azure AI Search                    | `config/settings/base.py`, `utilities/azure_search_client.py` | Sí | `****`                                      |
| `AZURE_SEARCH_INDEX_NAME`               | Nombre del índice de búsqueda                 | `config/settings/base.py`                  | No            | `vea-connect-index` (default)               |
| `AZURE_OPENAI_ENDPOINT`                 | Endpoint de Azure OpenAI                      | `apps/embeddings/openai_service.py`        | Sí            | `https://openai-****.openai.azure.com/`     |
| `OPENAI_API_KEY`                        | API key de Azure OpenAI                       | `apps/embeddings/openai_service.py`        | Sí            | `****`                                      |
| `AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT`    | Nombre del deployment de embeddings           | `apps/embeddings/openai_service.py`        | Sí            | `text-embedding-ada-002`                    |
| `AZURE_OPENAI_CHAT_DEPLOYMENT`          | Nombre del deployment de chat                 | `apps/embeddings/openai_service.py`        | Sí            | `gpt-35-turbo`                              |
| `AZURE_OPENAI_EMBEDDINGS_API_VERSION`   | Versión de API para embeddings                | `apps/embeddings/openai_service.py`        | No            | `2023-05-15` (default)                      |
| `AZURE_OPENAI_CHAT_API_VERSION`         | Versión de API para chat                      | `apps/embeddings/openai_service.py`        | No            | `2025-01-01-preview` (default)              |
| `AZURE_STORAGE_ACCOUNT_NAME`            | Nombre de la cuenta de Azure Blob Storage     | `config/settings/base.py`, `config/azure_storage.py` | Sí | `veaconnectstorage`                         |
| `AZURE_STORAGE_ACCOUNT_KEY`             | Key de Azure Blob Storage                     | `config/settings/base.py`, `config/azure_storage.py` | Sí | `****`                                      |
| `AZURE_CONTAINER`                       | Nombre del contenedor de blobs               | `config/settings/base.py`                  | Sí            | `vea-connect-files`                         |
| `AZURE_STORAGE_CONNECTION_STRING`       | Connection string de Azure Storage            | `config/settings/base.py`                  | No            | `DefaultEndpointsProtocol=https;AccountName=****;AccountKey=****` |
| `BLOB_ACCOUNT_NAME`                     | Fallback: nombre de cuenta de Blob Storage    | `config/settings/base.py`, `utilities/azureblobstorage.py` | No | `veaconnectstorage` (si no hay AZURE_*)|
| `BLOB_ACCOUNT_KEY`                      | Fallback: key de Blob Storage                 | `config/settings/base.py`, `utilities/azureblobstorage.py` | No | `****`                                 |
| `BLOB_CONTAINER_NAME`                   | Fallback: contenedor de blobs                 | `config/settings/base.py`, `utilities/azureblobstorage.py` | No | `vea-connect-files`                    |
| `VISION_ENDPOINT`                       | Endpoint de Azure Computer Vision             | `config/settings/base.py`                  | Sí (para OCR)| `https://vea-vision.cognitiveservices.azure.com/` |
| `VISION_KEY`                            | Key de Azure Computer Vision                  | `config/settings/base.py`                  | Sí (para OCR)| `****`                                      |
| `ACS_WHATSAPP_ENDPOINT`                 | Endpoint de Azure Communication Services      | `apps/whatsapp_bot/services.py`            | Sí            | `https://your-acs-resource.communication.azure.com` |
| `ACS_WHATSAPP_API_KEY`                  | API key de ACS para WhatsApp                  | `apps/whatsapp_bot/services.py`            | Sí            | `****`                                      |
| `ACS_PHONE_NUMBER`                      | Número de teléfono del bot                    | `apps/whatsapp_bot/services.py`            | Sí            | `whatsapp:+1234567890`                      |
| `WHATSAPP_CHANNEL_ID_GUID`              | GUID del canal de WhatsApp en ACS             | `config/settings/base.py`                  | Sí            | `c3dd072b-9283-4812-8ed0-10b1d3a45da1`      |
| `ACS_CONNECTION_STRING`                 | Connection string de ACS                      | `config/settings/base.py`                  | No            | `endpoint=https://****;accesskey=****`      |
| `ACS_EVENT_GRID_TOPIC_ENDPOINT`         | Endpoint de Event Grid para ACS               | `config/settings/base.py`                  | No            | `https://****`                              |
| `ACS_EVENT_GRID_TOPIC_KEY`              | Key de Event Grid                             | `config/settings/base.py`                  | No            | `****`                                      |
| `AZURE_REDIS_URL`                       | URL de Redis para caché                       | `config/settings/azure_production.py`      | No            | `redis://:****@vea-redis.redis.cache.windows.net:6380/0?ssl=True` |
| `REDIS_TTL_SECS`                        | TTL de caché en Redis (segundos)              | `config/settings/azure_production.py`      | No            | `86400` (default: 24h)                      |
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | Connection string de Application Insights     | `config/settings/azure_production.py`      | No            | `InstrumentationKey=****`                   |
| `ApplicationInsightsAgent_EXTENSION_VERSION` | Versión de extensión de App Insights     | `config/settings/azure_production.py`      | No            | `~3` (default)                              |
| `QUEUE_NAME`                            | Nombre de cola de Azure (documentos)          | `config/settings/azure_production.py`      | No            | `doc-processing` (default)                  |
| `BUILD_FLAGS`                           | Flags de build de Azure                       | `config/settings/azure_production.py`      | No            | `UseExpressBuild`                           |
| `SCM_DO_BUILD_DURING_DEPLOYMENT`        | Build durante deploy                          | `config/settings/azure_production.py`      | No            | `true`                                      |
| `FUNCTION_APP_URL`                      | URL de Azure Function App (si se usa)         | `config/settings/base.py`                  | No            | `https://func-vea-connect.azurewebsites.net/api/ProcessDocument` |
| `FUNCTION_APP_KEY`                      | Key de Azure Function App                     | `config/settings/base.py`                  | No            | `****`                                      |
| `DEBUG`                                 | Modo debug de Django                          | `config/settings/base.py`                  | No            | `False` (producción), `True` (desarrollo)   |
| `AZURE_KEYVAULT_RESOURCEENDPOINT`       | Endpoint de Azure Key Vault                   | `config/settings/azure_production.py`      | No            | `https://kv-vea-connect.vault.azure.net/`   |
| `AZURE_KEYVAULT_SCOPE`                  | Scope de Key Vault                            | `config/settings/azure_production.py`      | No            | `https://vault.azure.net/.default`          |

---

## 8. Operación y Observabilidad

### Logs en Producción

**Dónde ver logs:**

1. **Azure App Service:**
   - Portal: `App Service` > `Monitoring` > `Log stream`
   - CLI: `az webapp log tail --name <app-name> --resource-group <rg-name>`
   - Logs históricos: `App Service` > `Monitoring` > `App Service logs` > `File System` o `Blob`

2. **Application Insights:**
   - Si `APPLICATIONINSIGHTS_CONNECTION_STRING` está configurado, todos los logs se envían a Azure Monitor.
   - Portal: `Application Insights` > `Logs` > Query con Kusto (KQL).
   - Ejemplo: `traces | where message contains "WhatsApp" | order by timestamp desc`

3. **Django File Logs:**
   - Ubicación: `BASE_DIR/logs/django.log` (configurado en `config/settings/azure_production.py:198`).
   - Acceso: SSH o FTP al App Service.

**Niveles de log configurados:**

- **Root logger:** INFO
- **Loggers específicos:**
  - `django`: INFO
  - `apps.whatsapp_bot`: INFO
  - `utils.redis_cache`: INFO

**Formato:**

```
{levelname} {asctime} {module} {process:d} {thread:d} {message}
```

### Señales/Prints Críticos

**Nota:** La mayoría de prints de depuración han sido eliminados. Los prints restantes son:

1. **`config/settings/azure_production.py`:**
   - Línea 117: `"✅ Azure Storage configurado para archivos multimedia"` (si Azure Storage configurado)
   - Línea 121: `"⚠️ Azure Storage no configurado, usando almacenamiento local"` (fallback)
   - Línea 156: `"Redis cache configurado para conversaciones de WhatsApp"` (si Redis configurado)
   - Línea 166: `"Redis no configurado, usando LocMemCache (no persistente para conversaciones)"` (fallback)

2. **`manage.py`:**
   - Línea 18: `"Cargando variables desde .env (modo local)"` (solo en desarrollo local)
   - Línea 21: `"python-dotenv no está instalado, continuando sin .env"` (warning)
   - Línea 23: `"Error cargando .env: {e}, continuando sin .env"` (error)

3. **`config/settings/development.py`:**
   - Línea 136: `"Azure Blob Storage no configurado. Usando almacenamiento local."` (fallback)

4. **`utilities/azureblobstorage.py`:**
   - Múltiples prints de error/warning cuando Azure Blob Storage falla (NO hay loggers en este archivo).

**Todos los demás mensajes usan `logger.*` en lugar de `print()`.**

### Pruebas Rápidas Post-Deploy

**5 checks concretos:**

1. **Health check general:**
   ```bash
   curl https://<WEBSITE_HOSTNAME>/health/
   # Esperado: "OK"
   ```

2. **Health check del bot de WhatsApp:**
   ```bash
   curl https://<WEBSITE_HOSTNAME>/api/v1/whatsapp/health/
   # Esperado: JSON con "status": "healthy"
   ```

3. **Subir documento (requiere autenticación):**
   - Login en `/login/` con credenciales válidas.
   - Navegar a `/documents/create/`.
   - Subir una imagen JPG con título y descripción.
   - Verificar que el documento aparece en `/documents/` y que se generó el embedding.

4. **Editar documento sin cambiar imagen:**
   - Editar el documento creado en paso 3.
   - Cambiar solo el título o descripción.
   - Guardar y verificar que el documento se actualizó sin errores.

5. **Mensaje de prueba WhatsApp:**
   - Enviar mensaje al número del bot (ej: "Hola, ¿cómo puedo donar?").
   - Verificar respuesta del bot en WhatsApp.
   - Revisar logs en `/api/v1/whatsapp/history/?phone_number=<tu-numero>` (requiere autenticación).

---

## 9. Anexos: Rutas y Referencias

### Archivos Clave y su Rol

| Ruta                                          | Rol                                                                 |
|-----------------------------------------------|---------------------------------------------------------------------|
| `config/settings/base.py`                     | Settings base de Django; define apps, middleware, templates, DB     |
| `config/settings/azure_production.py`         | Settings de producción; PostgreSQL, Azure services, logging         |
| `config/urls.py`                              | Routing principal; mapea URLs a apps                                |
| `config/wsgi.py`                              | Entrypoint WSGI para Gunicorn                                       |
| `config/asgi.py`                              | Entrypoint ASGI (para canales/WebSockets futuros)                   |
| `manage.py`                                   | CLI de Django; carga .env en desarrollo                             |
| `requirements.txt`                            | Dependencias de Python; Django, Azure SDK, OpenAI, Redis, etc.      |
| `apps/documents/views.py`                     | CRUD de documentos; upload, OCR, indexación en Azure AI Search      |
| `apps/documents/signals.py`                   | Signals de documentos (actualmente deshabilitados)                  |
| `apps/whatsapp_bot/urls.py`                   | Routing de WhatsApp Bot; webhook, health, send, history            |
| `apps/whatsapp_bot/views.py`                  | Endpoints REST del bot; webhook_handler, send_message, etc.         |
| `apps/whatsapp_bot/handlers.py`               | Lógica central del bot; process_message, detect_intent, RAG flow   |
| `apps/whatsapp_bot/services.py`               | Servicios del bot; ACSService, DataRetrievalService, TemplateService|
| `apps/embeddings/openai_service.py`           | Cliente de Azure OpenAI; generate_embedding, generate_chat_response |
| `utilities/embedding_manager.py`              | Gestor de embeddings; CRUD y búsqueda en Azure AI Search            |
| `utilities/azure_search_client.py`            | Cliente de bajo nivel de Azure AI Search; search_vector, search_semantic|
| `services/search_index_service.py`            | Servicio de indexación; upsert_document, delete_document, search    |
| `services/storage_service.py`                 | Cliente de Azure Blob Storage; upload, download, list               |
| `tasks/document_pipeline.py`                  | Pipeline de procesamiento de documentos; OCR, embeddings, upsert    |
| `config/azure_storage.py`                     | Storage backend personalizado para Django con Azure Blob            |

### CI/CD (no encontrado)

**Estado:** No se encontraron archivos YAML de GitHub Actions ni Azure Pipelines en el repositorio. El despliegue se realiza manualmente mediante:

1. **Azure CLI:**
   ```bash
   az webapp up --name <app-name> --resource-group <rg-name> --runtime "PYTHON:3.10"
   ```

2. **Deployment Center en Azure Portal:**
   - Configurar desde GitHub o Azure Repos.
   - Build automático con Oryx/Kudu.

3. **FTP/FTPS:**
   - Subir archivos directamente al App Service.

**Recomendación:** Implementar GitHub Actions o Azure Pipelines para CI/CD automatizado. Ejemplo de workflow básico:

```yaml
name: Deploy to Azure App Service

on:
  push:
    branches: [main]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          python manage.py test
      - name: Deploy to Azure
        uses: azure/webapps-deploy@v2
        with:
          app-name: <app-name>
          publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE }}
```

---

## Fin del Documento

**Autor:** Documentación generada mediante análisis del repositorio VEA Connect.

**Fecha:** 17 de octubre de 2025.

**Versión:** 1.0

**Notas finales:**
- Todos los datos se basan en el código del repositorio al momento de la inspección.
- Las credenciales se han enmascarado con `****` o `<...>`.
- Para actualizar este documento, re-ejecutar el análisis del repositorio y actualizar las secciones correspondientes.

