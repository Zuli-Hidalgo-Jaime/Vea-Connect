# Azure Function V2 - WhatsApp Bot

## 🎯 Propósito

Esta es la **versión 2** de la Azure Function para WhatsApp, basada en la lógica del CLI local (`scripts/whatsapp_chat_cli.py`).

## 🆚 Diferencias con `funcapp-vea-prod` (V1)

| Característica | V1 (`funcapp-vea-prod`) | V2 (`funcapp-vea-v2`) |
|----------------|-------------------------|------------------------|
| **Temperature** | `0.7` (creativo) | `0.0` (determinístico) |
| **System Prompt** | Variable o hardcodeado | Prompt estricto de `whatsapp_cli_prompt.txt` |
| **Modo** | Intents + RAG | Solo RAG directo (`handler._rag_answer()`) |
| **Monkeypatch** | No | Sí (inyecta prompt en cada llamada) |
| **Deployment** | Manual vía `func azure functionapp publish` | Automático vía GitHub Actions |

## 🔑 Características clave

### 1. **Prompt estricto**
```
Eres un asistente de WhatsApp para la organización de VEA. 
Responde SOLO con base en el contexto del índice que se te proporciona. 
Sé claro, breve y respetuoso y usa lenguaje religioso amable. 
Si el contexto no contiene la respuesta, dilo explícitamente y 
sugiere contactar al equipo de Iglesia VEA.
```

### 2. **Temperature = 0.0**
- Respuestas **100% determinísticas**
- **Cero creatividad** - solo usa el contexto proporcionado
- **Evita alucinaciones** completamente

### 3. **RAG directo**
- Usa `handler._rag_answer(text)` directamente
- Sin pasar por sistema de intents
- Mismo comportamiento que el CLI local

### 4. **Monkeypatch de OpenAIService**
- Inyecta el prompt estricto en **CADA** llamada a OpenAI
- Sobrescribe cualquier prompt que intente pasar el handler
- Garantiza consistencia en todas las respuestas

## 📦 Deployment

### Via GitHub Actions (AUTOMÁTICO)
1. Hacer cambios en `functions-v2/`
2. Commit y push a `main`
3. GitHub Actions despliega automáticamente

### Manual (si es necesario)
```bash
cd functions-v2
func azure functionapp publish funcapp-vea-v2 --python
```

## 🔧 Configuración necesaria

### Secrets de GitHub
Agregar en Settings > Secrets > Actions:
- `AZURE_FUNCTIONAPP_PUBLISH_PROFILE_V2`: Publish profile de `funcapp-vea-v2`

### Variables de entorno en Azure
Copiar TODAS las variables de `funcapp-vea-prod`:
- `ACS_CONNECTION_STRING`
- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_CHAT_DEPLOYMENT`
- `AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT`
- `AZURE_OPENAI_CHAT_API_VERSION`
- `AZURE_OPENAI_EMBEDDINGS_API_VERSION`
- `AZURE_SEARCH_ENDPOINT`
- `AZURE_SEARCH_KEY`
- `AZURE_SEARCH_INDEX_NAME`
- `BOT_USE_RAG=True`
- Etc.

## 🧪 Testing

### Paso 1: Verificar sin Event Grid
```bash
# Usar curl para simular evento Event Grid
curl -X POST https://funcapp-vea-v2.azurewebsites.net/runtime/webhooks/EventGrid?functionName=whatsapp_event_grid_trigger \
  -H "aeg-event-type: Notification" \
  -H "Content-Type: application/json" \
  -d '[...]'
```

### Paso 2: Activar Event Grid
1. Crear nueva suscripción de Event Grid apuntando a `funcapp-vea-v2`
2. Enviar mensaje de WhatsApp de prueba
3. Verificar logs en Azure Portal

### Paso 3: Desactivar V1 (si V2 funciona)
1. Deshabilitar Event Grid subscription de `funcapp-vea-prod`
2. Monitorear logs de `funcapp-vea-v2`

## 📊 Monitoring

### Logs en tiempo real
```bash
# PowerShell
az functionapp log tail -g rg-vea-prod -n funcapp-vea-v2 2>&1 | Select-String -Pattern "V2|RAG|temperature" -Context 0,2
```

### Application Insights
- Query: `traces | where message contains "V2"`
- Buscar: `[V2]` en todos los logs

## ⚠️ Importante

- **NO modificar** `functions/` (V1) desde este directorio
- **NO compartir** Event Grid subscription entre V1 y V2 simultáneamente
- **Verificar** que todas las variables de entorno estén copiadas antes de activar Event Grid

## 🔄 Rollback

Si algo falla, simplemente:
1. Reactivar Event Grid subscription de `funcapp-vea-prod`
2. Deshabilitar Event Grid subscription de `funcapp-vea-v2`
3. El tráfico volverá a V1 inmediatamente

