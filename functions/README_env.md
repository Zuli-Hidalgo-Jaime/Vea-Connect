# Variables de Entorno - Azure Functions

## Variables Obligatorias

Todas las variables deben estar configuradas en:
- `local.settings.json` (desarrollo local)
- App Settings (Azure Functions)
- GitHub Secrets (CI/CD)

### Azure Communication Services
```bash
ACS_CONNECTION_STRING=endpoint=https://acs-veu-connect-00.unitedstates.communication.azure.com/;accesskey=...
ACS_EVENT_GRID_TOPIC_ENDPOINT=https://acs-veu-connect-00.unitedstates.communication.azure.com/
ACS_EVENT_GRID_TOPIC_KEY=...
ACS_PHONE_NUMBER=+15558100642
ACS_WHATSAPP_API_KEY=...
ACS_WHATSAPP_ENDPOINT=https://acs-veu-connect-00.unitedstates.communication.azure.com/
```

### Azure OpenAI
```bash
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_EMBEDDINGS_API_VERSION=2023-05-15
AZURE_OPENAI_ENDPOINT=https://openai-veaconnect.openai.azure.com/
```

### Azure Search
```bash
AZURE_SEARCH_ENDPOINT=https://ai-search-veaconnect-prod.search.windows.net
AZURE_SEARCH_INDEX_NAME=vea-connect-index
AZURE_SEARCH_KEY=...
```

### Azure Storage
```bash
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=veaconnectstr;...
AzureWebJobsStorage=DefaultEndpointsProtocol=https;AccountName=veaconnectstr;...
```

### Base de Datos
```bash
DATABASE_URL=postgresql://twsugyiaxf:E72%24rhqEdm6b9oaI@micrositio-vea-connect-server.postgres.database.azure.com:5432/vea_connect_prod?sslmode=require
```

### Azure Functions
```bash
FUNCTIONS_WORKER_RUNTIME=python
FUNCTIONS_EXTENSION_VERSION=~4
```

### Cola de Procesamiento
```bash
QUEUE_NAME=doc-processing
```

### Application Insights
```bash
APPLICATIONINSIGHTS_CONNECTION_STRING=...
```

## Configuración Local

1. Copiar `local.settings.json.example` a `local.settings.json`
2. Configurar todas las variables de entorno
3. Ejecutar `func start` para desarrollo local

## Configuración Azure

1. Ir a Azure Portal > Function App
2. Configuration > Application settings
3. Agregar todas las variables de entorno
4. Guardar y reiniciar la aplicación

## Configuración GitHub Actions

1. Ir a GitHub > Settings > Secrets and variables > Actions
2. Agregar todos los secrets con los nombres exactos
3. Referenciar en workflows con `${{ secrets.VARIABLE_NAME }}`

## Validación

Las funciones confían en `utils.env_utils.get_env()` para validar automáticamente que todas las variables requeridas estén presentes. Si falta alguna, los servicios lanzan `EnvironmentError` y las funciones devuelven error 500.
