# ✅ Resumen: Azure Function V2 para WhatsApp

## 🎉 Lo que se creó

### Archivos NUEVOS (sin modificar nada existente):

```
functions-v2/
├── whatsapp_event_grid_trigger/
│   ├── __init__.py                    ← Lógica del CLI con RAG directo
│   └── function.json                  ← Config de Event Grid trigger
├── host.json                          ← Config de Azure Functions
├── requirements.txt                   ← Dependencias Python
├── .funcignore                        ← Archivos a excluir del deploy
├── README.md                          ← Documentación técnica
└── RESUMEN.md                         ← Este archivo

.github/workflows/
└── deploy-funcapp-v2.yml              ← GitHub Actions para auto-deploy

scripts/
└── copy_funcapp_settings_to_v2.ps1    ← Script para copiar variables

docs/deployment/
└── FUNCAPP_V2_DEPLOYMENT.md           ← Guía paso a paso completa
```

---

## 🔑 Características principales de V2

### 1. **Basado en `whatsapp_chat_cli.py`**
   - ✅ Misma lógica que funciona localmente
   - ✅ Usa `handler._rag_answer()` directo
   - ✅ Sin sistema de intents

### 2. **Temperature = 0.0**
   - ✅ Respuestas 100% determinísticas
   - ✅ Cero creatividad
   - ✅ NO inventa información

### 3. **System Prompt estricto**
   ```
   Eres un asistente de WhatsApp para la organización de VEA. 
   Responde SOLO con base en el contexto del índice que se te proporciona. 
   Sé claro, breve y respetuoso y usa lenguaje religioso amable. 
   Si el contexto no contiene la respuesta, dilo explícitamente y 
   sugiere contactar al equipo de Iglesia VEA.
   ```

### 4. **Monkeypatch de OpenAIService**
   - ✅ Inyecta el prompt en CADA llamada
   - ✅ Fuerza `temperature=0.0` siempre
   - ✅ Garantiza consistencia

### 5. **Deploy automático via GitHub Actions**
   - ✅ Push a `main` → deploy automático
   - ✅ No más `func azure functionapp publish` manual

---

## 📋 Próximos pasos

### ✅ Paso 1: Copiar variables de entorno
```powershell
.\scripts\copy_funcapp_settings_to_v2.ps1
```

### ✅ Paso 2: Configurar GitHub Secret
1. Descargar **Publish Profile** de `funcapp-vea-v2`
2. Agregarlo como secret: `AZURE_FUNCTIONAPP_PUBLISH_PROFILE_V2`

### ✅ Paso 3: Hacer push del código
```bash
git add functions-v2/ .github/workflows/ scripts/ docs/
git commit -m "feat: add funcapp-v2 with CLI logic"
git push origin main
```

### ✅ Paso 4: Verificar deployment
- Ver GitHub Actions → "Deploy Azure Function V2"
- Esperar a que termine con ✅

### ✅ Paso 5: Probar SIN Event Grid
```powershell
az functionapp log tail -g rg-vea-prod -n funcapp-vea-v2
```
Buscar líneas con `[V2]`

### ✅ Paso 6: Crear Event Grid Subscription
- Seguir guía en `docs/deployment/FUNCAPP_V2_DEPLOYMENT.md`
- Crear subscription apuntando a `funcapp-vea-v2`

### ✅ Paso 7: Enviar mensaje de prueba
- Probar con WhatsApp real
- Verificar que responda correctamente
- **Confirmar que NO inventa**

### ✅ Paso 8: Desactivar V1 (si V2 funciona)
```bash
# Eliminar subscription antigua
az eventgrid event-subscription delete \
  --name <NOMBRE_SUBSCRIPTION_V1> \
  --source-resource-id "/subscriptions/.../acs-vea-prod"
```

---

## ⚠️ IMPORTANTE: Evitar duplicación de mensajes

### ❌ MAL (Usuario recibe 2 respuestas):
- Event Grid → `funcapp-vea-prod` ✅ (activa)
- Event Grid → `funcapp-vea-v2` ✅ (activa)

### ✅ BIEN (Usuario recibe 1 respuesta):
**Opción A:**
- Event Grid → `funcapp-vea-prod` ❌ (desactivada)
- Event Grid → `funcapp-vea-v2` ✅ (activa)

**Opción B:**
- Event Grid → `funcapp-vea-prod` ✅ (activa, solo números +521xxx)
- Event Grid → `funcapp-vea-v2` ✅ (activa, solo números +522xxx)

---

## 🔙 Rollback (si falla)

Si V2 no funciona, **es FÁCIL volver a V1**:

```bash
# 1. Desactivar V2
az eventgrid event-subscription delete \
  --name whatsapp-messages-to-funcapp-v2 \
  --source-resource-id "/subscriptions/.../acs-vea-prod"

# 2. Reactivar V1 (si la eliminaste)
az eventgrid event-subscription create \
  --name whatsapp-messages-to-funcapp-prod \
  --source-resource-id "/subscriptions/.../acs-vea-prod" \
  --endpoint "<FUNCTION_URL_DE_V1>" \
  --endpoint-type azurefunction
```

---

## 📊 Cómo verificar que funciona

### 1. **Logs muestran `[V2]`**
```
[V2] Event Grid trigger ejecutado
[V2] Monkeypatch aplicado: temperature=0.0
[V2] Llamando a handler._rag_answer(...)
[V2] Respuesta RAG generada
[V2] Mensaje enviado correctamente
```

### 2. **Temperature es 0.0**
- Revisar logs de OpenAI
- Buscar `temperature=0.0` en llamadas

### 3. **NO inventa información**
- Preguntar algo que NO esté en el índice
- Debe responder: "No tengo esa información, contacta al equipo de Iglesia VEA"

### 4. **Responde rápido**
- Latencia < 5 segundos
- Sin timeouts

---

## 🆘 Si algo sale mal

1. **Ver logs:**
   ```powershell
   az functionapp log tail -g rg-vea-prod -n funcapp-vea-v2
   ```

2. **Buscar errores con `[V2]` o `ERROR`**

3. **Hacer rollback a V1:**
   - Desactivar Event Grid de V2
   - Reactivar Event Grid de V1
   - El bot vuelve a funcionar inmediatamente

4. **Debuggear V2:**
   - Revisar variables de entorno
   - Verificar que `ACS_CONNECTION_STRING` esté configurado
   - Revisar que el código se haya desplegado correctamente

---

## ✅ TODO checklist

Antes de dar por terminado:

- [ ] Variables de entorno copiadas
- [ ] GitHub Secret configurado
- [ ] Código pusheado a `main`
- [ ] GitHub Actions ejecutado exitosamente
- [ ] Logs muestran `[V2]`
- [ ] Event Grid subscription creada
- [ ] Mensaje de prueba enviado
- [ ] Respuesta correcta recibida
- [ ] **NO hay alucinaciones**
- [ ] V1 desactivada (opcional)
- [ ] Monitoreo activo

---

## 📞 Referencia rápida

### Logs en vivo:
```powershell
az functionapp log tail -g rg-vea-prod -n funcapp-vea-v2 2>&1 | Select-String -Pattern "V2" -Context 0,2
```

### Listar Event Grid subscriptions:
```bash
az eventgrid event-subscription list \
  --source-resource-id "/subscriptions/d0c4224c-a7d0-4339-9858-567c67c992a2/resourceGroups/rg-vea-prod/providers/Microsoft.Communication/CommunicationServices/acs-vea-prod" \
  -o table
```

### Ver settings de V2:
```bash
az functionapp config appsettings list -g rg-vea-prod -n funcapp-vea-v2 -o table
```

---

## 🎯 Resultado esperado

Después de completar todos los pasos:

✅ WhatsApp bot responde **EXACTAMENTE** como el CLI local  
✅ **NO inventa** información  
✅ Usa **solo** el contexto del índice  
✅ Temperature = **0.0** (determinístico)  
✅ Deploy **automático** con GitHub Actions  
✅ Mismo número de WhatsApp que V1  
✅ Fácil rollback si algo falla  




