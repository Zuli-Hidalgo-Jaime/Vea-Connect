# WhatsApp Event Grid Webhook - Diagnóstico y Configuración

## Descripción General

Este documento proporciona información completa para diagnosticar, configurar y mantener el webhook de WhatsApp que utiliza Azure Event Grid para procesar mensajes entrantes y generar respuestas automáticas con Azure OpenAI.

## Endpoint y Configuración

### URL del Webhook
```
https://{function-app-name}.azurewebsites.net/api/whatsapp_event_grid_trigger
```

### Método HTTP
- **POST**: Para recibir eventos de Event Grid
- **GET**: Para validación manual (opcional)

### Headers Requeridos
```
Content-Type: application/json
aeg-event-type: Notification
```

## Payloads Soportados

El webhook soporta múltiples esquemas de ACS Advanced Messaging para robustez:

### 1. Esquema Legacy
```json
{
  "data": {
    "messageBody": "Hola, necesito información sobre donaciones",
    "from": "+525512345678"
  }
}
```

### 2. Esquema Estándar
```json
{
  "data": {
    "message": {
      "content": {
        "text": "Hola, necesito información sobre donaciones"
      },
      "from": {
        "phoneNumber": "+525512345678"
      }
    }
  }
}
```

### 3. Esquema Alternativo (Content)
```json
{
  "data": {
    "content": {
      "text": "Hola, necesito información sobre donaciones"
    },
    "from": "+525512345678"
  }
}
```

### 4. Esquema Directo
```json
{
  "data": {
    "text": "Hola, necesito información sobre donaciones",
    "from": "+525512345678"
  }
}
```

## Variables de Entorno Mínimas

### Requeridas para Funcionamiento Básico
```bash
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-openai-service.openai.azure.com/
AZURE_OPENAI_API_KEY=your_openai_api_key
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-35-turbo
AZURE_OPENAI_CHAT_API_VERSION=2024-02-15-preview

# ACS WhatsApp
ACS_WHATSAPP_ENDPOINT=https://your-acs-service.communication.azure.com/
ACS_WHATSAPP_API_KEY=your_acs_api_key
ACS_PHONE_NUMBER=+1234567890
WHATSAPP_CHANNEL_ID_GUID=your-channel-id

# Redis (para historial de conversaciones)
AZURE_REDIS_CONNECTIONSTRING=your_redis_connection_string
REDIS_TTL_SECS=3600
```

### Opcionales para Funcionalidades Avanzadas
```bash
# RAG (Retrieval-Augmented Generation)
AZURE_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
AZURE_SEARCH_API_KEY=your_search_api_key
AZURE_SEARCH_INDEX_NAME=vea-connect-index
RAG_ENABLED=true

# Application Insights
APPLICATIONINSIGHTS_CONNECTION_STRING=your_app_insights_connection_string

# Banderas de Debug
WHATSAPP_DEBUG=false
E2E_DEBUG=false

# Prompt del Bot
BOT_SYSTEM_PROMPT="Eres un asistente virtual de VEA Connect..."
```

## Recreación de Suscripción Event Grid

### 1. Eliminar Suscripción Existente
```powershell
# Obtener suscripciones existentes
az eventgrid event-subscription list --source-resource-id "/subscriptions/{subscription-id}/resourceGroups/{resource-group}/providers/Microsoft.Communication/communicationServices/{acs-service-name}"

# Eliminar suscripción específica
az eventgrid event-subscription delete --name "whatsapp-webhook-prod" --source-resource-id "/subscriptions/{subscription-id}/resourceGroups/{resource-group}/providers/Microsoft.Communication/communicationServices/{acs-service-name}"
```

### 2. Crear Nueva Suscripción
```powershell
# Crear nueva suscripción
az eventgrid event-subscription create \
  --source-resource-id "/subscriptions/{subscription-id}/resourceGroups/{resource-group}/providers/Microsoft.Communication/communicationServices/{acs-service-name}" \
  --name "whatsapp-webhook-prod" \
  --endpoint-type "azurefunction" \
  --endpoint "/subscriptions/{subscription-id}/resourceGroups/{resource-group}/providers/Microsoft.Web/sites/{function-app-name}/functions/whatsapp_event_grid_trigger" \
  --included-event-types "Microsoft.Communication.AdvancedMessageReceived"
```

### 3. Verificar Suscripción
```powershell
# Verificar que la suscripción se creó correctamente
az eventgrid event-subscription show \
  --name "whatsapp-webhook-prod" \
  --source-resource-id "/subscriptions/{subscription-id}/resourceGroups/{resource-group}/providers/Microsoft.Communication/communicationServices/{acs-service-name}"
```

## Diagnóstico de Problemas

### 1. Verificar Health Endpoint
```bash
curl -X GET "https://{function-app-name}.azurewebsites.net/api/health"
```

Respuesta esperada:
```json
{
  "status": "healthy",
  "message": "Azure Functions are running",
  "functions": ["health", "whatsapp_event_grid_trigger", ...],
  "health_checks": {
    "eventgrid_ready": true,
    "acs_outbound_ready": true,
    "openai_configured": true,
    "ai_search_ready": true,
    "redis_connected": true,
    "build_version": "1.0.0-2024-01-01"
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 2. Verificar Logs de Function
```bash
# En Azure Portal: Function App > whatsapp_event_grid_trigger > Logs
# O usando Azure CLI
az webapp log tail --name {function-app-name} --resource-group {resource-group}
```

### 3. Probar Webhook Manualmente
```bash
# Simular evento de validación
curl -X POST "https://{function-app-name}.azurewebsites.net/api/whatsapp_event_grid_trigger" \
  -H "Content-Type: application/json" \
  -H "aeg-event-type: Notification" \
  -d '{
    "eventType": "Microsoft.EventGrid.SubscriptionValidationEvent",
    "data": {
      "validationCode": "test-validation-code"
    }
  }'
```

### 4. Verificar Configuración de ACS
```powershell
# Verificar configuración de ACS
az communication service show \
  --name {acs-service-name} \
  --resource-group {resource-group}

# Verificar números de teléfono
az communication phone-number list \
  --resource-group {resource-group} \
  --source {acs-service-name}
```

## Monitoreo y Métricas

### Application Insights Events
- `wa.incoming`: Mensajes entrantes
- `wa.reply`: Respuestas enviadas
- `rag.search`: Búsquedas RAG
- `llm.call`: Llamadas a OpenAI
- `wa.conversation`: Operaciones de historial
- `wa.processing`: Tiempo de procesamiento

### Logs Importantes
- **Evento recibido**: `Event received - Type: {event_type}, Subject: {subject}, ID: {id}`
- **Mensaje procesado**: `Processing message from {phone} (schema: {schema}): {text}`
- **Respuesta generada**: `AI response generated in {time}ms for session {session}`
- **Mensaje enviado**: `WhatsApp message sent successfully to {phone}`

## Troubleshooting Común

### Error: "No matching schema found"
**Causa**: El payload de ACS no coincide con ningún esquema conocido.
**Solución**: 
1. Verificar logs para ver las claves disponibles
2. Actualizar el parser en `models.py` si es necesario
3. Contactar soporte de ACS si el formato cambió

### Error: "OpenAI configuration missing"
**Causa**: Variables de entorno de OpenAI no configuradas.
**Solución**:
1. Verificar `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_CHAT_DEPLOYMENT`
2. Asegurar que el deployment existe y está activo
3. Verificar permisos de API key

### Error: "ACS outbound messaging failed"
**Causa**: Problemas con la configuración de ACS WhatsApp.
**Solución**:
1. Verificar `ACS_WHATSAPP_ENDPOINT`, `ACS_WHATSAPP_API_KEY`
2. Confirmar que `ACS_PHONE_NUMBER` está verificado
3. Verificar que `WHATSAPP_CHANNEL_ID_GUID` es correcto
4. Revisar logs de ACS para errores específicos

### Error: "Redis connection failed"
**Causa**: Problemas de conectividad con Redis.
**Solución**:
1. Verificar `AZURE_REDIS_CONNECTIONSTRING`
2. Confirmar que Redis está accesible desde la Function App
3. Verificar reglas de firewall si aplica

### Error: "RAG search failed"
**Causa**: Problemas con Azure AI Search.
**Solución**:
1. Verificar configuración de `AZURE_SEARCH_ENDPOINT`, `AZURE_SEARCH_API_KEY`
2. Confirmar que el índice `AZURE_SEARCH_INDEX_NAME` existe
3. Verificar que el índice tiene el campo `content`

## Escalación

Si los problemas persisten después de seguir esta guía:

1. **Recopilar información**:
   - Logs completos de la Function App
   - Respuesta del health endpoint
   - Configuración de variables de entorno (sin valores sensibles)
   - Payload del evento que falla

2. **Contactar soporte** con:
   - Descripción detallada del problema
   - Pasos para reproducir
   - Información recopilada
   - Impacto en el negocio

## Referencias

- [Azure Event Grid Documentation](https://docs.microsoft.com/en-us/azure/event-grid/)
- [Azure Communication Services WhatsApp](https://docs.microsoft.com/en-us/azure/communication-services/quickstarts/telephony-sms/get-phone-number)
- [Azure Functions HTTP Triggers](https://docs.microsoft.com/en-us/azure/azure-functions/functions-bindings-http-webhook)
- [Azure OpenAI Service](https://docs.microsoft.com/en-us/azure/cognitive-services/openai/)
