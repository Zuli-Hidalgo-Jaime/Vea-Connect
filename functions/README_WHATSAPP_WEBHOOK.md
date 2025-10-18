# Webhook de WhatsApp con Event Grid

## 🚀 Descripción

Sistema completo de webhook para WhatsApp que procesa mensajes entrantes usando Azure Event Grid y genera respuestas automáticas con Azure OpenAI. El sistema incluye soporte para RAG (Retrieval-Augmented Generation) y gestión de conversaciones con Redis.

## 📋 Características

- ✅ **Soporte para SubscriptionValidation** de Event Grid
- ✅ **Parseo robusto** de múltiples esquemas de ACS Advanced Messaging
- ✅ **Normalización automática** de números de teléfono a E.164
- ✅ **Gestión de conversaciones** con Redis Cache
- ✅ **Generación de respuestas** con Azure OpenAI
- ✅ **Soporte RAG** con Azure AI Search (opcional)
- ✅ **Modos de debug** configurables
- ✅ **Logging detallado** y métricas de latencia
- ✅ **Manejo robusto de errores**

## 🏗️ Arquitectura

```
WhatsApp → ACS Advanced Messaging → Event Grid → Azure Function → AI Response → WhatsApp
                                    ↓
                              Redis Cache (conversaciones)
                                    ↓
                              Azure AI Search (RAG)
```

## ⚙️ Configuración Rápida

### 1. Configurar Variables de Entorno

```bash
# Variables requeridas
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-35-turbo
AZURE_OPENAI_CHAT_API_VERSION=2024-02-15-preview

ACS_WHATSAPP_ENDPOINT=https://your-acs.communication.azure.com/
ACS_WHATSAPP_API_KEY=your-acs-key
ACS_PHONE_NUMBER=+1234567890
WHATSAPP_CHANNEL_ID_GUID=your-channel-id

# Variables opcionales
WHATSAPP_DEBUG=false
E2E_DEBUG=false
RAG_ENABLED=false
BOT_SYSTEM_PROMPT="Eres un asistente virtual de VEA Connect..."
```

### 2. Usar Script de Configuración Automática

```powershell
# Ejecutar script de configuración
.\scripts\setup_whatsapp_webhook.ps1 `
  -FunctionAppName "vea-connect-functions" `
  -ResourceGroup "vea-connect-rg" `
  -CommunicationServiceName "acs-veu-connect-00" `
  -SubscriptionId "your-subscription-id" `
  -Environment "prod"
```

### 3. Desplegar Función

```bash
# Desplegar a Azure
func azure functionapp publish your-function-app

# O probar localmente
func start
```

## 🧪 Pruebas

### Ejecutar Script de Pruebas

```bash
cd functions
python test_whatsapp_webhook.py
```

### Verificar Configuración

El script de pruebas verifica:
- ✅ Variables de entorno configuradas
- ✅ Servicios importables
- ✅ Todos los esquemas de payload
- ✅ Validación de suscripción

## 📊 Esquemas de Payload Soportados

### 1. message.content
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

### 2. content.text.body
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

### 3. Legacy
```json
{
  "messageBody": "Hola",
  "from": "+1234567890"
}
```

### 4. Button Text
```json
{
  "button": {
    "text": "Información"
  },
  "from": "+1234567890"
}
```

### 5. Interactive List Reply
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

## 🔧 Modos de Debug

### WHATSAPP_DEBUG=true
- No envía mensajes reales
- Registra en logs lo que se enviaría
- Útil para desarrollo

### E2E_DEBUG=true
- Registra payloads completos (truncados a 2KB)
- Información detallada de procesamiento
- Métricas de latencia

## 📝 Logging

### Información Registrada

```
2024-01-15 10:30:15 INFO Event received - Type: Microsoft.Communication.AdvancedMessageReceived, Subject: message-subject, ID: msg-123
2024-01-15 10:30:15 INFO Payload size: 1024 bytes
2024-01-15 10:30:15 INFO Processing message from +1234567890 (schema: message.content): Hola, necesito información
2024-01-15 10:30:16 INFO AI response generated in 850ms
2024-01-15 10:30:16 INFO WhatsApp message sent successfully to +1234567890
2024-01-15 10:30:16 INFO Total processing time: 1200ms
```

## 🚨 Manejo de Errores

### Errores Comunes

1. **"Azure OpenAI configuration missing"**
   - Verificar variables de entorno
   - Confirmar credenciales válidas

2. **"WhatsApp configuration invalid"**
   - Revisar configuración de ACS
   - Verificar channel ID

3. **"No text content found in message"**
   - Verificar esquema de payload
   - Revisar logs de debug

### Estrategias de Recuperación

- Fallbacks a respuestas predefinidas
- Reintentos automáticos
- Logging detallado para debugging

## 📚 Documentación Completa

Para información detallada, consulta:
- [Guía Completa](docs/WHATSAPP_WEBHOOK_GUIDE.md)
- [Troubleshooting](docs/WHATSAPP_WEBHOOK_GUIDE.md#troubleshooting)
- [Configuración Avanzada](docs/WHATSAPP_WEBHOOK_GUIDE.md#configuración)

## 🔒 Seguridad

### Consideraciones

- Usar Managed Identity cuando sea posible
- Validar origen de eventos
- Usar HTTPS para todas las comunicaciones
- No registrar información sensible

### Mejores Prácticas

1. Variables de entorno en Azure Key Vault
2. Validación de payloads entrantes
3. Rate limiting
4. Monitoreo de seguridad

## 📈 Monitoreo

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

## 🤝 Contribución

### Estructura del Código

```
functions/
├── whatsapp_event_grid_trigger/
│   ├── __init__.py          # Función principal
│   └── function.json        # Configuración
├── test_whatsapp_webhook.py # Script de pruebas
├── scripts/
│   └── setup_whatsapp_webhook.ps1 # Script de configuración
└── docs/
    └── WHATSAPP_WEBHOOK_GUIDE.md
```

### Convenciones

- Funciones privadas con prefijo `_`
- Constantes en UPPER_CASE
- Logging consistente
- Error handling detallado

## 📞 Soporte

Para problemas o preguntas:

1. Revisar la [documentación completa](docs/WHATSAPP_WEBHOOK_GUIDE.md)
2. Ejecutar el [script de pruebas](test_whatsapp_webhook.py)
3. Verificar [logs de Azure](https://docs.microsoft.com/en-us/azure/azure-functions/functions-monitoring)
4. Consultar [troubleshooting](docs/WHATSAPP_WEBHOOK_GUIDE.md#troubleshooting)

---

**¡El webhook está listo para procesar mensajes de WhatsApp! 🎉**
