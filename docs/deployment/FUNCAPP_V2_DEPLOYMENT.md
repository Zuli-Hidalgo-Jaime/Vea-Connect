# Guía de Deployment: Azure Function V2 (funcapp-vea-v2)

## 🎯 Objetivo

Desplegar `funcapp-vea-v2` con la lógica del CLI local (`whatsapp_chat_cli.py`) que responde correctamente, usando el mismo número de WhatsApp que `funcapp-vea-prod`.

---

## 📋 Pre-requisitos

- ✅ `funcapp-vea-v2` ya creada en Azure
- ✅ `acs-vea-prod` existente (mismo número de WhatsApp)
- ✅ Código en `functions-v2/` creado
- ✅ GitHub Actions workflow en `.github/workflows/deploy-funcapp-v2.yml`

---

## 🚀 Paso 1: Copiar variables de entorno

### Opción A: Usando script PowerShell

```powershell
cd C:\vea
.\scripts\copy_funcapp_settings_to_v2.ps1
```

Cuando te pregunte, escribe `SI` para confirmar.

### Opción B: Manual via Azure CLI

```bash
# Listar settings de V1
az functionapp config appsettings list \
  -g rg-vea-prod \
  -n funcapp-vea-prod \
  -o table

# Copiar manualmente a V2
az functionapp config appsettings set \
  -g rg-vea-prod \
  -n funcapp-vea-v2 \
  --settings \
    ACS_CONNECTION_STRING="<valor>" \
    AZURE_OPENAI_API_KEY="<valor>" \
    AZURE_OPENAI_ENDPOINT="<valor>" \
    # ... etc
```

### Settings críticos a verificar:

- `ACS_CONNECTION_STRING` ← **Mismo que V1** (mismo número WhatsApp)
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_CHAT_DEPLOYMENT`
- `AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT`
- `AZURE_OPENAI_CHAT_API_VERSION`
- `AZURE_OPENAI_EMBEDDINGS_API_VERSION`
- `AZURE_SEARCH_ENDPOINT`
- `AZURE_SEARCH_KEY`
- `AZURE_SEARCH_INDEX_NAME`
- `BOT_USE_RAG=True`
- `DJANGO_SETTINGS_MODULE=config.settings.azure_production`

---

## 🔐 Paso 2: Configurar GitHub Secrets

1. Ir a Azure Portal → `funcapp-vea-v2` → **Deployment Center**
2. Descargar el **Publish Profile**
3. Ir a GitHub → Repo → **Settings** → **Secrets and variables** → **Actions**
4. Crear nuevo secret:
   - Name: `AZURE_FUNCTIONAPP_PUBLISH_PROFILE_V2`
   - Value: *(pegar contenido del publish profile)*

---

## 📦 Paso 3: Deploy inicial via GitHub Actions

### 3.1 Commit y push del código

```bash
git status  # Verificar archivos nuevos
git add functions-v2/
git add .github/workflows/deploy-funcapp-v2.yml
git add scripts/copy_funcapp_settings_to_v2.ps1
git add docs/deployment/FUNCAPP_V2_DEPLOYMENT.md
git commit -m "feat: add funcapp-v2 with CLI logic (temperature=0.0, strict prompt)"
git push origin main
```

### 3.2 Monitorear deployment

1. Ir a GitHub → **Actions** tab
2. Ver workflow **"Deploy Azure Function V2"** en ejecución
3. Verificar que termine con ✅

---

## 🧪 Paso 4: Testing SIN Event Grid

**IMPORTANTE:** Primero probamos sin conectar Event Grid para evitar duplicar mensajes.

### 4.1 Verificar logs

```powershell
# Ver logs en tiempo real
az functionapp log tail -g rg-vea-prod -n funcapp-vea-v2
```

Buscar líneas con `[V2]` que indican que el código correcto está ejecutándose.

### 4.2 Test manual con Function URL (si aplica)

Si la Function tiene HTTP trigger habilitado:

```bash
curl -X POST https://funcapp-vea-v2.azurewebsites.net/api/whatsapp_event_grid_trigger \
  -H "Content-Type: application/json" \
  -d '{"test": "ping"}'
```

---

## 🔗 Paso 5: Crear Event Grid Subscription para V2

**⚠️ SOLO cuando V2 esté funcionando correctamente**

### 5.1 Obtener endpoint de la Function

```bash
# Obtener Function URL para Event Grid
az functionapp function show \
  -g rg-vea-prod \
  -n funcapp-vea-v2 \
  --function-name whatsapp_event_grid_trigger \
  --query "invokeUrlTemplate" \
  -o tsv
```

Copia el URL, será algo como:
```
https://funcapp-vea-v2.azurewebsites.net/runtime/webhooks/EventGrid?functionName=whatsapp_event_grid_trigger&code=...
```

### 5.2 Obtener el ID del recurso ACS

```bash
az communication list -g rg-vea-prod --query "[?name=='acs-vea-prod'].id" -o tsv
```

Resultado será algo como:
```
/subscriptions/d0c4224c-a7d0-4339-9858-567c67c992a2/resourceGroups/rg-vea-prod/providers/Microsoft.Communication/CommunicationServices/acs-vea-prod
```

### 5.3 Crear la suscripción

```bash
# Crear Event Grid subscription para V2
az eventgrid event-subscription create \
  --name whatsapp-messages-to-funcapp-v2 \
  --source-resource-id "/subscriptions/d0c4224c-a7d0-4339-9858-567c67c992a2/resourceGroups/rg-vea-prod/providers/Microsoft.Communication/CommunicationServices/acs-vea-prod" \
  --endpoint "<FUNCTION_URL_DE_V2>" \
  --endpoint-type azurefunction \
  --included-event-types Microsoft.Communication.AdvancedMessageReceived
```

### 5.4 Verificar que NO haya duplicación

```bash
# Listar TODAS las subscriptions de acs-vea-prod
az eventgrid event-subscription list \
  --source-resource-id "/subscriptions/d0c4224c-a7d0-4339-9858-567c67c992a2/resourceGroups/rg-vea-prod/providers/Microsoft.Communication/CommunicationServices/acs-vea-prod" \
  -o table
```

Deberías ver:
- ✅ Subscription antigua → `funcapp-vea-prod` (activa)
- ✅ Subscription nueva → `funcapp-vea-v2` (activa)

**⚠️ CUIDADO:** Si ambas están activas, el usuario recibirá **2 respuestas** (una de cada Function).

---

## 🔄 Paso 6: Migración de tráfico (V1 → V2)

### Opción A: Cambio inmediato

```bash
# 1. Deshabilitar subscription de V1
az eventgrid event-subscription update \
  --name <NOMBRE_SUBSCRIPTION_V1> \
  --source-resource-id "/subscriptions/.../acs-vea-prod" \
  --endpoint-type azurefunction \
  --advanced-filter data.eventType StringContains Microsoft.Communication.AdvancedMessageReceived \
  --deadletter-endpoint "" \
  --max-delivery-attempts 0  # Esto la deshabilita efectivamente
```

**O MEJOR:**

```bash
# Eliminar temporalmente (se puede recrear después)
az eventgrid event-subscription delete \
  --name <NOMBRE_SUBSCRIPTION_V1> \
  --source-resource-id "/subscriptions/.../acs-vea-prod"
```

### Opción B: A/B Testing

Mantener ambas activas pero con filtros por número:

```bash
# V1: Solo números que empiezan con +521
az eventgrid event-subscription update ... \
  --advanced-filter data.from StringBeginsWith +521

# V2: Solo números que empiezan con +52
az eventgrid event-subscription update ... \
  --advanced-filter data.from StringBeginsWith +52
```

---

## 📊 Paso 7: Monitoreo post-deployment

### Logs en tiempo real

```powershell
# Ver solo logs de V2
az functionapp log tail -g rg-vea-prod -n funcapp-vea-v2 2>&1 | Select-String -Pattern "V2|temperature|RAG" -Context 0,2
```

### Métricas clave a monitorear:

1. **Tasa de éxito de mensajes:** ¿Se envían correctamente?
2. **Latencia:** ¿Responde rápido?
3. **Alucinaciones:** ¿Sigue inventando o ya no?
4. **Errores:** ¿Hay excepciones en logs?

### Application Insights Query

```kusto
traces
| where timestamp > ago(1h)
| where message contains "[V2]"
| project timestamp, message, severityLevel
| order by timestamp desc
```

---

## 🔙 Rollback (si algo falla)

### Rollback inmediato

```bash
# 1. Reactivar V1
az eventgrid event-subscription create \
  --name whatsapp-messages-to-funcapp-prod \
  --source-resource-id "/subscriptions/.../acs-vea-prod" \
  --endpoint "<FUNCTION_URL_DE_V1>" \
  --endpoint-type azurefunction

# 2. Desactivar V2
az eventgrid event-subscription delete \
  --name whatsapp-messages-to-funcapp-v2 \
  --source-resource-id "/subscriptions/.../acs-vea-prod"
```

El tráfico vuelve a V1 **inmediatamente**.

---

## ✅ Checklist final

Antes de dar por terminado el deployment:

- [ ] Variables de entorno copiadas de V1 a V2
- [ ] GitHub Actions workflow ejecutado exitosamente
- [ ] Logs de V2 muestran `[V2]` y `temperature=0.0`
- [ ] Event Grid subscription creada apuntando a V2
- [ ] Mensaje de prueba enviado y respondido correctamente
- [ ] **NO hay alucinaciones** en las respuestas
- [ ] Subscription de V1 desactivada (solo si V2 funciona)
- [ ] Monitoreo activo en Application Insights

---

## 🆘 Troubleshooting

### Problema: V2 no responde mensajes

**Solución:**
1. Verificar logs: `az functionapp log tail -g rg-vea-prod -n funcapp-vea-v2`
2. Buscar errores con `[V2]` o `ERROR`
3. Verificar que `ACS_CONNECTION_STRING` esté configurado

### Problema: Usuario recibe 2 respuestas

**Causa:** Ambas subscriptions (V1 y V2) están activas.

**Solución:**
```bash
# Listar subscriptions
az eventgrid event-subscription list --source-resource-id "/subscriptions/.../acs-vea-prod" -o table

# Eliminar la que NO quieras
az eventgrid event-subscription delete --name <NOMBRE> --source-resource-id "/subscriptions/.../acs-vea-prod"
```

### Problema: V2 sigue inventando respuestas

**Causa:** El monkeypatch no se aplicó correctamente.

**Verificar:**
1. Buscar en logs: `[V2] Monkeypatch aplicado`
2. Verificar que el código tenga `temperature=0.0`
3. Revisar que el SYSTEM_PROMPT sea el correcto

---

## 📞 Contacto

Si tienes problemas:
1. Revisar logs con `az functionapp log tail`
2. Buscar `[V2]` en Application Insights
3. Hacer rollback a V1 si es crítico

