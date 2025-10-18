# Configuración de Event Grid Trigger para Azure Function

Esta guía describe cómo configurar la función `whatsapp_event_grid_trigger` para responder a eventos de Azure Event Grid.

## Requisitos

- Azure Function con trigger `eventGridTrigger`
- Suscripción activa al tópico de eventos (e.g., Blob Storage, Communication Services)

## Pasos Técnicos

### 1. Definición del Trigger

En `function.json`, asegúrate de usar:

```json
{
  "scriptFile": "whatsapp_event_grid_trigger_function.py",
  "bindings": [
    {
      "type": "eventGridTrigger",
      "name": "event",
      "direction": "in"
    }
  ]
}
```

### 2. Implementación de la Función

La función debe tener la siguiente estructura:

```python
import azure.functions as func  # includes EventGridEvent
import logging

logger = logging.getLogger(__name__)

def main(event: func.EventGridEvent) -> None:
    """
    Event Grid trigger for WhatsApp events.
    """
    try:
        logger.info(f"Event Grid trigger received: {event.event_type}")
        logger.info(f"Event data: {event.get_json()}")
        
        # Process the event using Django services
        event_data = {
            'event_type': event.event_type,
            'event_time': event.event_time.isoformat(),
            'id': event.id,
            'topic': event.topic,
            'subject': event.subject,
            'data': event.get_json()
        }
        
        # Delegate to Django service for business logic
        result = django_integration.process_whatsapp_event(event_data)
        
        logger.info(f"Event processed successfully: {result}")
        
    except Exception as e:
        logger.error(f"Error processing Event Grid event: {e}")
        # Don't raise exception to prevent Event Grid retries
```

### 3. Configuración de Event Grid Subscription

#### 3.1 Crear Event Grid Topic

```bash
# Crear un Event Grid Topic
az eventgrid topic create \
  --name "whatsapp-events-topic" \
  --location "East US" \
  --resource-group "your-resource-group"
```

#### 3.2 Suscribir la Function al Topic

```bash
# Obtener la URL del endpoint de la función
FUNCTION_URL=$(az functionapp function show \
  --name "your-function-app" \
  --resource-group "your-resource-group" \
  --function-name "whatsapp_event_grid_trigger" \
  --query "invokeUrlTemplate" \
  --output tsv)

# Crear la suscripción
az eventgrid event-subscription create \
  --name "whatsapp-function-subscription" \
  --source-resource-id "/subscriptions/{subscription-id}/resourceGroups/{resource-group}/providers/Microsoft.EventGrid/topics/whatsapp-events-topic" \
  --endpoint-type "azurefunction" \
  --endpoint $FUNCTION_URL \
  --included-event-types "Microsoft.Communication.RecordingFileStatusUpdated"
```

### 4. Configuración de Communication Services

#### 4.1 Habilitar Event Grid en Communication Services

```bash
# Configurar Event Grid para Communication Services
az communication event-subscription create \
  --name "whatsapp-events" \
  --resource-group "your-resource-group" \
  --resource-name "your-communication-service" \
  --endpoint-type "azurefunction" \
  --endpoint $FUNCTION_URL \
  --included-event-types "Microsoft.Communication.RecordingFileStatusUpdated"
```

#### 4.2 Configurar Webhook para WhatsApp

En Azure Communication Services, configurar el webhook para enviar eventos a Event Grid:

```json
{
  "webhookUrl": "https://your-event-grid-topic.westus2-1.eventgrid.azure.net/api/events",
  "events": [
    "Microsoft.Communication.RecordingFileStatusUpdated",
    "Microsoft.Communication.ChatMessageReceived",
    "Microsoft.Communication.ChatMessageEdited"
  ]
}
```

### 5. Validación y Testing

#### 5.1 Test Local

```bash
# Ejecutar la función localmente
func start

# Enviar evento de prueba
curl -X POST http://localhost:7071/runtime/webhooks/eventgrid \
  -H "Content-Type: application/json" \
  -H "aeg-event-type: Notification" \
  -d '{
    "id": "test-event-id",
    "eventType": "Microsoft.Communication.RecordingFileStatusUpdated",
    "subject": "/communicationServices/your-service/recordings/test-recording",
    "eventTime": "2024-01-01T12:00:00Z",
    "data": {
      "recordingId": "test-recording-id",
      "status": "Available"
    }
  }'
```

#### 5.2 Test en Azure

```bash
# Verificar logs de la función
az webapp log tail \
  --name "your-function-app" \
  --resource-group "your-resource-group"

# Verificar eventos recibidos
az eventgrid event-subscription show \
  --name "whatsapp-function-subscription" \
  --source-resource-id "/subscriptions/{subscription-id}/resourceGroups/{resource-group}/providers/Microsoft.EventGrid/topics/whatsapp-events-topic"
```

### 6. Monitoreo y Logging

#### 6.1 Application Insights

Configurar Application Insights para monitorear la función:

```json
{
  "applicationInsights": {
    "samplingSettings": {
      "isEnabled": true,
      "excludedTypes": "Request"
    }
  }
}
```

#### 6.2 Logs Estructurados

```python
# En la función, usar logs estructurados
logger.info("Event processed", extra={
    "event_id": event.id,
    "event_type": event.event_type,
    "processing_time_ms": processing_time,
    "success": True
})
```

### 7. Manejo de Errores

#### 7.1 Retry Policy

Event Grid maneja automáticamente los reintentos. Configurar en la suscripción:

```bash
az eventgrid event-subscription update \
  --name "whatsapp-function-subscription" \
  --source-resource-id "/subscriptions/{subscription-id}/resourceGroups/{resource-group}/providers/Microsoft.EventGrid/topics/whatsapp-events-topic" \
  --max-delivery-attempts 3 \
  --event-ttl 1440
```

#### 7.2 Dead Letter Queue

```bash
# Configurar Dead Letter Queue
az eventgrid event-subscription update \
  --name "whatsapp-function-subscription" \
  --source-resource-id "/subscriptions/{subscription-id}/resourceGroups/{resource-group}/providers/Microsoft.EventGrid/topics/whatsapp-events-topic" \
  --deadletter-endpoint "https://your-storage-account.blob.core.windows.net/deadletter"
```

### 8. Seguridad

#### 8.1 Autenticación

```bash
# Configurar autenticación para la función
az functionapp update \
  --name "your-function-app" \
  --resource-group "your-resource-group" \
  --https-only true

# Configurar CORS si es necesario
az functionapp cors add \
  --name "your-function-app" \
  --resource-group "your-resource-group" \
  --allowed-origins "https://your-domain.com"
```

#### 8.2 Network Security

```bash
# Configurar Private Endpoints si es necesario
az network private-endpoint create \
  --name "function-private-endpoint" \
  --resource-group "your-resource-group" \
  --vnet-name "your-vnet" \
  --subnet "functions-subnet" \
  --private-connection-resource-id "/subscriptions/{subscription-id}/resourceGroups/{resource-group}/providers/Microsoft.Web/sites/your-function-app" \
  --group-id "sites" \
  --connection-name "function-private-connection"
```

## Troubleshooting

### Problemas Comunes

1. **Eventos no llegan a la función**
   - Verificar que la suscripción esté activa
   - Verificar que la URL del endpoint sea correcta
   - Verificar logs de Event Grid

2. **Errores de autenticación**
   - Verificar que la función tenga permisos para recibir eventos
   - Verificar configuración de CORS

3. **Errores de procesamiento**
   - Verificar logs de la función en Application Insights
   - Verificar que el formato del evento sea correcto

### Comandos de Diagnóstico

```bash
# Verificar estado de la suscripción
az eventgrid event-subscription show \
  --name "whatsapp-function-subscription" \
  --source-resource-id "/subscriptions/{subscription-id}/resourceGroups/{resource-group}/providers/Microsoft.EventGrid/topics/whatsapp-events-topic"

# Verificar eventos enviados
az eventgrid event-subscription list-event-types \
  --source-resource-id "/subscriptions/{subscription-id}/resourceGroups/{resource-group}/providers/Microsoft.EventGrid/topics/whatsapp-events-topic"

# Verificar logs de la función
az webapp log download \
  --name "your-function-app" \
  --resource-group "your-resource-group"
```

## Referencias

- [Azure Event Grid Documentation](https://docs.microsoft.com/en-us/azure/event-grid/)
- [Azure Functions Event Grid Trigger](https://docs.microsoft.com/en-us/azure/azure-functions/functions-bindings-event-grid)
- [Communication Services Events](https://docs.microsoft.com/en-us/azure/communication-services/concepts/event-handling) 