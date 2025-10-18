# Azure Functions - Configuración y Uso

Este directorio contiene las Azure Functions para el proyecto VeaConnect, incluyendo funciones para embeddings, WhatsApp y health checks.

## Configuración Inicial

### 1. Configurar Variables de Entorno

Antes de ejecutar las funciones, necesitas configurar las variables de entorno. Puedes hacerlo de dos maneras:

#### Opción A: Usar el Script de Configuración (Recomendado)

```bash
cd functions
python setup_local_env.py
```

Este script te guiará a través de la configuración de todas las variables necesarias.

#### Opción B: Configuración Manual

Edita el archivo `local.settings.json` y configura las siguientes variables:

```json
{
  "IsEncrypted": false,
  "Values": {
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_EXTENSION_VERSION": "~4",
    "AZURE_OPENAI_ENDPOINT": "https://tu-recurso.openai.azure.com/",
    "AZURE_OPENAI_API_KEY": "tu-api-key",
    "AZURE_SEARCH_SERVICE_NAME": "tu-search-service",
    "AZURE_SEARCH_API_KEY": "tu-search-key",
    "AZURE_SEARCH_INDEX_NAME": "embeddings-index",
    "AZURE_SEARCH_ENDPOINT": "https://tu-search-service.search.windows.net",
    "AZURE_SEARCH_KEY": "tu-search-key"
  }
}
```

### 2. Variables de Entorno Requeridas

#### Para Embeddings:
- `AZURE_OPENAI_ENDPOINT`: Endpoint de Azure OpenAI
- `AZURE_OPENAI_API_KEY`: API Key de Azure OpenAI
- `AZURE_SEARCH_SERVICE_NAME`: Nombre del servicio de Azure Search (sin .search.windows.net)
- `AZURE_SEARCH_API_KEY`: API Key de Azure Search
- `AZURE_SEARCH_INDEX_NAME`: Nombre del índice (por defecto: "embeddings-index")

#### Para WhatsApp:
- `ACS_CONNECTION_STRING`: Connection string de Azure Communication Services
- `ACS_EVENT_GRID_TOPIC_ENDPOINT`: Endpoint del topic de Event Grid
- `ACS_EVENT_GRID_TOPIC_KEY`: Key del topic de Event Grid
- `ACS_PHONE_NUMBER`: Número de teléfono de ACS
- `ACS_WHATSAPP_API_KEY`: API Key de WhatsApp
- `ACS_WHATSAPP_ENDPOINT`: Endpoint de WhatsApp

## Ejecución Local

### 1. Instalar Dependencias

```bash
cd functions
pip install -r requirements.txt
```

### 2. Iniciar Azure Storage Emulator (Windows)

```bash
# Instalar Azure Storage Emulator si no lo tienes
# Descargar desde: https://go.microsoft.com/fwlink/?LinkId=717179

# Iniciar el emulador
"C:\Program Files (x86)\Microsoft SDKs\Azure\Storage Emulator\AzureStorageEmulator.exe" start
```

### 3. Ejecutar las Funciones

```bash
func start --port 7074
```

## Endpoints Disponibles

### Health Checks
- `GET /api/health` - Health check principal
- `GET /api/embeddings/health` - Health check de embeddings
- `GET /api/whatsapp/health` - Health check de WhatsApp

### Embeddings
- `POST /api/embeddings/create` - Crear un nuevo embedding
- `POST /api/embeddings/search` - Buscar embeddings similares
- `GET /api/embeddings/stats` - Obtener estadísticas de embeddings

### WhatsApp
- `POST /api/whatsapp/event-grid` - Webhook para Event Grid
- `POST /api/whatsapp/test` - Función de prueba
- `GET /api/whatsapp/stats` - Estadísticas de WhatsApp

## Solución de Problemas

### Error: "URL has an invalid label"

Este error ocurre cuando `AZURE_SEARCH_SERVICE_NAME` está vacío o mal configurado.

**Solución:**
1. Verifica que `AZURE_SEARCH_SERVICE_NAME` tenga un valor válido
2. El valor debe ser solo el nombre del servicio, sin `.search.windows.net`
3. Ejemplo: Si tu endpoint es `https://mi-servicio.search.windows.net`, usa `mi-servicio`

### Error: "AzureWebJobsStorage connection string"

Este error ocurre cuando Azure Storage Emulator no está ejecutándose.

**Solución:**
1. Inicia Azure Storage Emulator
2. O configura una cadena de conexión real de Azure Storage

### Error: "Environment variable not set"

Este error ocurre cuando las variables de entorno requeridas no están configuradas.

**Solución:**
1. Ejecuta `python setup_local_env.py` para configurar todas las variables
2. Verifica que todas las variables requeridas tengan valores válidos

## Pruebas

### Opción 1: Scripts Automatizados (Recomendado)

#### Python
```bash
# Prueba rápida (solo health checks y stats)
python quick_test.py

# Prueba completa (todas las funciones)
python test_all_functions.py
```

#### PowerShell (Windows)
```powershell
# Prueba completa con PowerShell
.\test_functions.ps1
```

### Opción 2: Pruebas Manuales

#### Health Checks

```bash
# Health check principal
curl http://localhost:7074/api/health

# Health check de embeddings
curl http://localhost:7074/api/embeddings/health

# Health check de WhatsApp
curl http://localhost:7074/api/whatsapp/health
```

#### Funciones de Embeddings

```bash
# Obtener estadísticas
curl http://localhost:7074/api/embeddings/stats

# Crear embedding
curl -X POST http://localhost:7074/api/embeddings/create \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Este es un texto de prueba para verificar que las funciones funcionan correctamente.",
    "metadata": {
      "source": "test",
      "category": "technology",
      "language": "es",
      "test_id": "test_001"
    }
  }'

# Buscar embeddings similares
curl -X POST http://localhost:7074/api/embeddings/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "tecnología desarrollo software",
    "top_k": 3
  }'
```

#### Funciones de WhatsApp

```bash
# Obtener estadísticas
curl http://localhost:7074/api/whatsapp/stats

# Función de prueba
curl -X POST http://localhost:7074/api/whatsapp/test \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Mensaje de prueba desde las funciones de Azure",
    "phone_number": "+15558100642",
    "test_mode": true
  }'

# Event Grid trigger (simulación)
curl -X POST http://localhost:7074/api/whatsapp/event-grid \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "/subscriptions/test/resourceGroups/test/providers/Microsoft.Communication/CommunicationServices/test",
    "subject": "/phonenumbers/+15558100642",
    "eventType": "Microsoft.Communication.SMSReceived",
    "eventTime": "2024-01-01T00:00:00.0000000Z",
    "id": "test-event-id",
    "data": {
      "messageId": "test-message-id",
      "from": "+1234567890",
      "to": "+15558100642",
      "message": "Mensaje de prueba desde Event Grid",
      "receivedTimestamp": "2024-01-01T00:00:00.0000000Z"
    },
    "dataVersion": "2.0"
  }'
```

## Despliegue

Para desplegar las funciones a Azure:

```bash
# Configurar Azure CLI
az login

# Desplegar
func azure functionapp publish <nombre-de-tu-function-app>
```

## Estructura de Archivos

- `embedding_api_function_traditional.py` - Funciones de embeddings
- `whatsapp_event_grid_traditional.py` - Funciones de WhatsApp
- `function_app.py` - Configuración principal de la aplicación
- `local.settings.json` - Variables de entorno locales
- `setup_local_env.py` - Script de configuración
- `requirements.txt` - Dependencias de Python
- `host.json` - Configuración del host de Functions 