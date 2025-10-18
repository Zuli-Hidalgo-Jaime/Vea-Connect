# WhatsApp Event Grid Trigger Function

## 📋 Descripción

Esta función está configurada específicamente para recibir eventos de WhatsApp desde Azure Event Grid. Utiliza la sintaxis correcta de Azure Functions v4 con el decorador `@event_grid_trigger`.

## 🏗️ Estructura de Archivos

```
functions/
├── whatsapp_event_grid_trigger/
│   ├── __init__.py              # Función principal de Event Grid
│   └── function.json            # Configuración del trigger
├── setup_event_grid.ps1         # Script de configuración
└── setup_event_grid.py          # Script de configuración (Python)
```

## ⚙️ Configuración

### 1. Función de Event Grid

La función está ubicada en `functions/whatsapp_event_grid_trigger/` y utiliza:

- **Trigger**: `eventGridTrigger` (correcto para Event Grid)
- **Sintaxis**: Azure Functions v4 con decoradores
- **Parámetro**: `event: func.EventGridEvent`

### 2. Archivo function.json

```json
{
  "scriptFile": "__init__.py",
  "bindings": [
    {
      "type": "eventGridTrigger",
      "name": "event",
      "direction": "in"
    }
  ]
}
```

## 🚀 Configuración en Azure

### Paso 1: Crear Event Grid Topic

```powershell
# Ejecutar desde el directorio functions/
.\setup_event_grid.ps1
```

O manualmente:

```bash
az eventgrid topic create \
    --name "veaconnect-whatsapp-events" \
    --resource-group "rg-vea-connect-dev" \
    --location "Central US"
```

### Paso 2: Crear Event Grid Subscription

```bash
az eventgrid event-subscription create \
    --name "whatsapp-events-subscription" \
    --source-resource-id "/subscriptions/{subscription-id}/resourceGroups/rg-vea-connect-dev/providers/Microsoft.EventGrid/topics/veaconnect-whatsapp-events" \
    --endpoint-type azurefunction \
    --endpoint "https://vea-functions-apis.azurewebsites.net/runtime/webhooks/eventgrid?functionName=whatsapp_event_grid_trigger" \
    --included-event-types "Microsoft.Communication.AdvancedMessageReceived" "Microsoft.Communication.AdvancedMessageDeliveryReportReceived"
```

### Paso 3: Configurar Variables de Entorno

```bash
az webapp config appsettings set \
    --name "vea-functions-apis" \
    --resource-group "rg-vea-connect-dev" \
    --settings \
    EVENT_GRID_TOPIC_ENDPOINT="https://veaconnect-whatsapp-events.centralus-1.eventgrid.azure.net/api/events" \
    EVENT_GRID_TOPIC_KEY="{topic-key}" \
    EVENT_GRID_VALIDATION_KEY="{validation-key}"
```

## 📡 Tipos de Eventos Soportados

La función procesa los siguientes tipos de eventos de WhatsApp:

1. **`Microsoft.Communication.AdvancedMessageReceived`**
   - Mensajes recibidos de WhatsApp
   - Contiene texto, archivos multimedia, etc.

2. **`Microsoft.Communication.AdvancedMessageDeliveryReportReceived`**
   - Reportes de entrega de mensajes
   - Estado de envío (entregado, fallido, etc.)

## 🔧 Integración con Django

La función delega el procesamiento de eventos a los servicios de Django:

```python
# Procesar evento usando servicios de Django
result = django_integration.process_whatsapp_event(event_data)
```

### Estructura de Datos del Evento

```python
event_data = {
    'event_type': event.event_type,
    'event_time': event.event_time.isoformat(),
    'id': event.id,
    'topic': event.topic,
    'subject': event.subject,
    'data': event.get_json()
}
```

## 🧪 Pruebas

### Prueba Local

```bash
# Iniciar Azure Functions localmente
func start

# Enviar evento de prueba
curl -X POST http://localhost:7071/runtime/webhooks/eventgrid \
  -H "Content-Type: application/json" \
  -H "aeg-event-type: Notification" \
  -d '[
    {
      "id": "test-event-id",
      "eventType": "Microsoft.Communication.AdvancedMessageReceived",
      "subject": "/whatsapp/message",
      "eventTime": "2024-01-01T00:00:00Z",
      "data": {
        "from": "+1234567890",
        "to": "+0987654321",
        "message": "Hola desde WhatsApp"
      }
    }
  ]'
```

### Prueba en Producción

1. Enviar un mensaje de WhatsApp al número configurado
2. Verificar logs en Azure Portal:
   - Function App → `vea-functions-apis`
   - Función → `whatsapp_event_grid_trigger`
   - Logs de aplicación

## 🔍 Monitoreo

### Logs de la Función

```bash
# Ver logs en tiempo real
az webapp log tail --name "vea-functions-apis" --resource-group "rg-vea-connect-dev"
```

### Métricas de Event Grid

- Ir a Azure Portal → Event Grid Topics
- Seleccionar `veaconnect-whatsapp-events`
- Ver métricas de eventos publicados y entregados

## 🚨 Solución de Problemas

### Error: "Function not found"

1. Verificar que la función esté desplegada:
   ```bash
   az functionapp function list --name "vea-functions-apis" --resource-group "rg-vea-connect-dev"
   ```

2. Verificar el nombre de la función en la suscripción:
   ```bash
   az eventgrid event-subscription show --name "whatsapp-events-subscription" --source-resource-id "{topic-resource-id}"
   ```

### Error: "Authentication failed"

1. Verificar la clave del topic:
   ```bash
   az eventgrid topic key list --name "veaconnect-whatsapp-events" --resource-group "rg-vea-connect-dev"
   ```

2. Actualizar la clave en la Function App:
   ```bash
   az webapp config appsettings set --name "vea-functions-apis" --resource-group "rg-vea-connect-dev" --settings EVENT_GRID_TOPIC_KEY="{new-key}"
   ```

### Error: "No events received"

1. Verificar que ACS esté configurado para enviar eventos:
   ```bash
   az communication phonenumber show --phone-number "{phone-number}" --resource-group "rg-vea-connect-dev"
   ```

2. Verificar que el topic esté activo:
   ```bash
   az eventgrid topic show --name "veaconnect-whatsapp-events" --resource-group "rg-vea-connect-dev"
   ```

## 📚 Referencias

- [Azure Event Grid Documentation](https://docs.microsoft.com/en-us/azure/event-grid/)
- [Azure Functions Event Grid Trigger](https://docs.microsoft.com/en-us/azure/azure-functions/functions-bindings-event-grid)
- [Azure Communication Services Events](https://docs.microsoft.com/en-us/azure/communication-services/concepts/event-handling)

## ✅ Checklist de Configuración

- [ ] Event Grid Topic creado
- [ ] Event Grid Subscription configurado
- [ ] Variables de entorno configuradas
- [ ] Función desplegada correctamente
- [ ] ACS configurado para enviar eventos
- [ ] Pruebas realizadas exitosamente
- [ ] Monitoreo configurado 