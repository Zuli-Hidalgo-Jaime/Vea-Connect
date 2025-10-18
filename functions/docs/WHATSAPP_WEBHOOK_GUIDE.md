# Guía del Webhook de WhatsApp con Event Grid

## Descripción General

Este sistema implementa un webhook completo para WhatsApp usando Azure Event Grid que procesa mensajes entrantes y genera respuestas automáticas usando Azure OpenAI. El sistema está diseñado para ser robusto, escalable y fácil de configurar.

## Arquitectura

```
WhatsApp → ACS Advanced Messaging → Event Grid → Azure Function → AI Response → WhatsApp
```

### Componentes Principales

1. **Event Grid Trigger**: Procesa eventos de WhatsApp entrantes
2. **Redis Cache**: Almacena historial de conversaciones
3. **Azure OpenAI**: Genera respuestas inteligentes
4. **Azure AI Search**: Proporciona contexto RAG (opcional)
5. **WhatsApp Sender**: Envía respuestas de vuelta

## Configuración

### Variables de Entorno Requeridas

```bash
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-35-turbo
AZURE_OPENAI_CHAT_API_VERSION=2024-02-15-preview

# WhatsApp/ACS
ACS_WHATSAPP_ENDPOINT=https://your-acs.communication.azure.com/
ACS_WHATSAPP_API_KEY=your-acs-key
ACS_PHONE_NUMBER=+1234567890
WHATSAPP_CHANNEL_ID_GUID=your-channel-id

# Azure AI Search (opcional para RAG)
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_API_KEY=your-search-key
AZURE_SEARCH_INDEX_NAME=your-index-name

# Redis (opcional)
REDIS_TTL_SECS=3600
```

### Variables de Entorno Opcionales

```bash
# Banderas de debug
WHATSAPP_DEBUG=false
E2E_DEBUG=false
RAG_ENABLED=false

# Prompt del bot
BOT_SYSTEM_PROMPT="Eres un asistente virtual de VEA Connect..."
```

## Funcionalidades

### 1. Soporte para SubscriptionValidation

El webhook maneja automáticamente la validación de suscripciones de Event Grid:

```json
{
  "eventType": "Microsoft.EventGrid.SubscriptionValidationEvent",
  "data": {
    "validationCode": "abc123"
  }
}
```

### 2. Parseo Robusto de Payloads

Soporta múltiples esquemas de ACS Advanced Messaging:

#### Schema 1: message.content
```json
{
  "message": {
    "content": {
      "text": "Hola"
    },
    "from": {
      "phoneNumber": "+1234567890"
    }
  }
}
```

#### Schema 2: content.text.body
```json
{
  "content": {
    "text": {
      "body": "Hola"
    }
  },
  "from": "+1234567890"
}
```

#### Schema 3: Legacy
```json
{
  "messageBody": "Hola",
  "from": "+1234567890"
}
```

#### Schema 4: Button Text
```json
{
  "button": {
    "text": "Información"
  },
  "from": "+1234567890"
}
```

#### Schema 5: Interactive List Reply
```json
{
  "interactive": {
    "listReply": {
      "title": "Eventos"
    }
  },
  "from": "+1234567890"
}
```

### 3. Normalización de Teléfonos

Convierte automáticamente números de teléfono a formato E.164:

- `1234567890` → `+11234567890`
- `whatsapp:+1234567890` → `+1234567890`
- `(123) 456-7890` → `+11234567890`

### 4. Gestión de Conversaciones

- **Redis Cache**: Almacena historial de conversaciones por número de teléfono
- **TTL Configurable**: 30 minutos por defecto para conversaciones
- **Límite de Contexto**: Mantiene solo los últimos 10 mensajes

### 5. Generación de Respuestas con AI

#### Sin RAG
```python
messages = [
    {"role": "system", "content": BOT_SYSTEM_PROMPT},
    {"role": "user", "content": "Historial de conversación..."},
    {"role": "assistant", "content": "Respuestas anteriores..."},
    {"role": "user", "content": "Mensaje actual"}
]
```

#### Con RAG Habilitado
```python
messages = [
    {"role": "system", "content": BOT_SYSTEM_PROMPT},
    {"role": "user", "content": "Contexto relevante:\n{rag_context}\n\nBasándote en este contexto, responde a:"},
    {"role": "user", "content": "Mensaje actual"}
]
```

### 6. Modo Debug

#### WHATSAPP_DEBUG=true
- No envía mensajes reales
- Registra en logs lo que se enviaría
- Útil para desarrollo y pruebas

#### E2E_DEBUG=true
- Registra payloads completos (truncados a 2KB)
- Información detallada de procesamiento
- Métricas de latencia

## Logging

### Información Registrada

```python
# Evento recibido
logger.info(f"Event received - Type: {event.event_type}, Subject: {event.subject}, ID: {event.id}")
logger.info(f"Payload size: {payload_size} bytes")

# Procesamiento de mensaje
logger.info(f"Processing message from {normalized_phone} (schema: {schema_used}): {text}")

# Respuesta AI
logger.info(f"AI response generated in {latency_ms}ms")

# Envío WhatsApp
logger.info(f"WhatsApp message sent successfully to {phone_number}")

# Tiempo total
logger.info(f"Total processing time: {processing_time_ms}ms")
```

### Ejemplo de Logs

```
2024-01-15 10:30:15 INFO Event received - Type: Microsoft.Communication.AdvancedMessageReceived, Subject: message-subject, ID: msg-123
2024-01-15 10:30:15 INFO Payload size: 1024 bytes
2024-01-15 10:30:15 INFO Processing message from +1234567890 (schema: message.content): Hola, necesito información
2024-01-15 10:30:16 INFO AI response generated in 850ms
2024-01-15 10:30:16 INFO WhatsApp message sent successfully to +1234567890
2024-01-15 10:30:16 INFO Total processing time: 1200ms
```

## Manejo de Errores

### Errores de Configuración
- Variables de entorno faltantes
- Configuración inválida de servicios
- Credenciales incorrectas

### Errores de Procesamiento
- Payloads malformados
- Fallos en servicios externos
- Timeouts de API

### Estrategias de Recuperación
- Fallbacks a respuestas predefinidas
- Reintentos automáticos
- Logging detallado para debugging

## Pruebas

### Script de Prueba

```bash
cd functions
python test_whatsapp_webhook.py
```

### Verificaciones

1. **Variables de Entorno**: Confirma que todas las variables requeridas estén configuradas
2. **Servicios**: Verifica que los servicios se puedan importar correctamente
3. **Esquemas**: Prueba todos los esquemas de payload soportados
4. **Validación**: Confirma el manejo de eventos de validación

### Ejemplo de Salida

```
🚀 INICIANDO PRUEBAS DEL WEBHOOK WHATSAPP
============================================================

🔧 VERIFICACIÓN DE VARIABLES DE ENTORNO
========================================
Variables requeridas:
  ✅ AZURE_OPENAI_ENDPOINT: Configurada
  ✅ AZURE_OPENAI_API_KEY: Configurada
  ✅ AZURE_OPENAI_CHAT_DEPLOYMENT: Configurada
  ✅ ACS_WHATSAPP_ENDPOINT: Configurada
  ✅ ACS_WHATSAPP_API_KEY: Configurada
  ✅ ACS_PHONE_NUMBER: Configurada
  ✅ WHATSAPP_CHANNEL_ID_GUID: Configurada

Variables opcionales:
  ✅ WHATSAPP_DEBUG: false
  ✅ E2E_DEBUG: false
  ✅ RAG_ENABLED: false
  ✅ BOT_SYSTEM_PROMPT: Configurada

📦 VERIFICACIÓN DE SERVICIOS
==============================
✅ services.whatsapp_sender.WhatsAppSenderService - OK
✅ services.redis_cache.WhatsAppCacheService - OK
✅ services.search_index_service.SearchIndexService - OK

🧪 PRUEBA DEL WEBHOOK DE WHATSAPP
==================================================

1. Probando validación de suscripción...
✅ Validación de suscripción procesada correctamente

2. Probando esquema: message.content
✅ Esquema message.content procesado correctamente

3. Probando esquema: content.text.body
✅ Esquema content.text.body procesado correctamente

4. Probando esquema: legacy
✅ Esquema legacy procesado correctamente

5. Probando esquema: button.text
✅ Esquema button.text procesado correctamente

6. Probando esquema: interactive.listReply
✅ Esquema interactive.listReply procesado correctamente

🎉 Pruebas completadas

📋 RESUMEN
====================
Las pruebas han sido completadas. Revisa los resultados anteriores.
```

## Despliegue

### Azure Functions

1. **Configurar Variables de Entorno**:
   ```bash
   az functionapp config appsettings set --name your-function-app --resource-group your-rg --settings AZURE_OPENAI_ENDPOINT="https://your-openai.openai.azure.com/"
   ```

2. **Desplegar Función**:
   ```bash
   func azure functionapp publish your-function-app
   ```

3. **Configurar Event Grid**:
   - Crear suscripción de Event Grid
   - Apuntar al endpoint de la función
   - Configurar filtros de eventos

### Configuración de Event Grid

```bash
# Crear suscripción
az eventgrid event-subscription create \
  --source-resource-id "/subscriptions/{subscription-id}/resourceGroups/{resource-group}/providers/Microsoft.Communication/communicationServices/{communication-service}" \
  --name "whatsapp-webhook" \
  --endpoint-type "azurefunction" \
  --endpoint "/subscriptions/{subscription-id}/resourceGroups/{resource-group}/providers/Microsoft.Web/sites/{function-app}/functions/whatsapp_event_grid_trigger" \
  --included-event-types "Microsoft.Communication.AdvancedMessageReceived"
```

## Monitoreo

### Métricas Clave

- **Latencia de Respuesta**: Tiempo desde recepción hasta envío
- **Tasa de Éxito**: Porcentaje de mensajes procesados correctamente
- **Uso de RAG**: Frecuencia de uso del contexto de búsqueda
- **Errores por Esquema**: Identificar esquemas problemáticos

### Alertas Recomendadas

- Latencia > 5 segundos
- Tasa de error > 5%
- Fallos de configuración
- Timeouts de API

## Troubleshooting

### Problemas Comunes

1. **"Azure OpenAI configuration missing"**
   - Verificar variables de entorno
   - Confirmar credenciales válidas

2. **"WhatsApp configuration invalid"**
   - Revisar configuración de ACS
   - Verificar channel ID

3. **"No text content found in message"**
   - Verificar esquema de payload
   - Revisar logs de debug

4. **"Failed to send WhatsApp message"**
   - Verificar configuración de WhatsApp
   - Revisar logs de error detallados

### Debugging

1. **Habilitar Debug**:
   ```bash
   export E2E_DEBUG=true
   export WHATSAPP_DEBUG=true
   ```

2. **Revisar Logs**:
   ```bash
   az webapp log tail --name your-function-app --resource-group your-rg
   ```

3. **Probar Localmente**:
   ```bash
   func start
   ```

## Seguridad

### Consideraciones

- **Autenticación**: Usar Managed Identity cuando sea posible
- **Autorización**: Validar origen de eventos
- **Encriptación**: Usar HTTPS para todas las comunicaciones
- **Logging**: No registrar información sensible

### Mejores Prácticas

1. **Variables de Entorno**: Usar Azure Key Vault para secretos
2. **Validación**: Verificar payloads entrantes
3. **Rate Limiting**: Implementar límites de velocidad
4. **Monitoreo**: Configurar alertas de seguridad

## Contribución

### Estructura del Código

```
functions/
├── whatsapp_event_grid_trigger/
│   ├── __init__.py          # Función principal
│   └── function.json        # Configuración
├── test_whatsapp_webhook.py # Script de pruebas
└── docs/
    └── WHATSAPP_WEBHOOK_GUIDE.md
```

### Convenciones

- **Funciones**: Prefijo `_` para funciones privadas
- **Variables**: UPPER_CASE para constantes
- **Logging**: Usar logger configurado
- **Error Handling**: Try/catch con logging detallado

### Testing

- Ejecutar pruebas antes de commits
- Verificar todos los esquemas de payload
- Probar casos de error
- Validar configuración de entorno
