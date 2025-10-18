# Azure Functions - VEA Connect

## Tabla de Rutas

| Función | Método | Ruta | Descripción | Autenticación |
|---------|--------|------|-------------|---------------|
| get_stats | GET | `/api/stats` | Obtiene estadísticas del sistema | Function Key |
| search_similar | POST | `/api/search` | Búsqueda vectorial | Function Key |
| whatsapp_acs_event_grid_trigger | Event Grid | N/A | Procesa mensajes de WhatsApp | Event Grid |

## Ejemplos de Uso

### GET /api/stats

**cURL:**
```bash
curl -X GET "https://vea-functions-apis.azurewebsites.net/api/stats?code=YOUR_FUNCTION_KEY" \
  -H "Content-Type: application/json"
```

**Respuesta:**
```json
{
  "total_documents": 1250,
  "index_name": "vea-connect-index",
  "search_endpoint": "https://ai-search-veaconnect-prod.search.windows.net",
  "status": "healthy"
}
```

### POST /api/search

**cURL:**
```bash
curl -X POST "https://vea-functions-apis.azurewebsites.net/api/search?code=YOUR_FUNCTION_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "documentos sobre eventos",
    "top": 5
  }'
```

**Respuesta:**
```json
[
  {
    "id": "doc-001",
    "title": "Evento Anual 2024",
    "content": "Documento sobre el evento anual...",
    "score": 0.95
  },
  {
    "id": "doc-002", 
    "title": "Guía de Eventos",
    "content": "Guía completa para organizar eventos...",
    "score": 0.87
  }
]
```

## Event Grid - WhatsApp ACS

### Configuración Event Grid

1. **System Topic:** `Microsoft.Communication.ChatMessageReceived`
2. **Recurso:** Azure Communication Services
3. **Subscription:** 
   - Endpoint: Function `whatsapp_acs_event_grid_trigger`
   - Filtro: `subjectBeginsWith: "/whatsapp/"`

### Payload de Evento

```json
{
  "eventType": "Microsoft.Communication.ChatMessageReceived",
  "eventTime": "2024-01-01T12:00:00Z",
  "data": {
    "messageBody": "Hola, necesito información",
    "from": "whatsapp:+525512345678",
    "to": "whatsapp:+15558100642"
  },
  "subject": "/whatsapp/message",
  "topic": "/subscriptions/.../resourceGroups/.../providers/Microsoft.Communication/communicationServices/acs-veu-connect-00"
}
```

## Variables de Entorno Requeridas

### Para get_stats y search_similar:
- `AZURE_SEARCH_ENDPOINT`
- `AZURE_SEARCH_INDEX_NAME`
- `AZURE_SEARCH_KEY`

### Para whatsapp_acs_event_grid_trigger:
- `ACS_CONNECTION_STRING`
- `ACS_PHONE_NUMBER`
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_EMBEDDINGS_API_VERSION`

## Manejo de Errores

### Error 400 - Bad Request
```json
{
  "error": "El parámetro 'query' es requerido"
}
```

### Error 500 - Internal Server Error
```json
{
  "error": "Variables de entorno faltantes: ['AZURE_SEARCH_ENDPOINT']"
}
```

## Logs y Monitoreo

- **Application Insights:** Habilitado con `APPLICATIONINSIGHTS_CONNECTION_STRING`
- **Live Metrics:** Disponible en Azure Portal
- **Logs:** Disponibles en Azure Portal > Function App > Logs

### Query KQL para Dashboard:
```kusto
traces
| where customDimensions.stage == "indexing"
| summarize count() by name
```

## Despliegue

### Local
```bash
func start
```

### Azure
```bash
func azure functionapp publish vea-functions-apis
```

### GitHub Actions
```yaml
- name: Deploy to Azure Functions
  run: |
    func azure functionapp publish vea-functions-apis --no-build
```

## Tests

### Ejecutar Tests
```bash
pytest tests/ -v --cov=. --cov-report=html
```

### Cobertura Mínima
- Cobertura global: ≥ 90%
- Tests unitarios: 100%
- Tests de integración: Incluidos

## Troubleshooting

### Problema: Variables de entorno faltantes
**Solución:** Verificar configuración en Azure Portal > Function App > Configuration

### Problema: Event Grid no dispara función
**Solución:** Verificar subscription y filtros en Event Grid

### Problema: WhatsApp no responde
**Solución:** Verificar ACS connection string y phone number
