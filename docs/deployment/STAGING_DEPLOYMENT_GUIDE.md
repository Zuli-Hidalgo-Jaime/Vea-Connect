# 🚀 Guía de Despliegue a Staging

## 📋 Resumen

Esta guía describe el proceso de despliegue a staging usando GitHub Actions con slots de Azure y feature flags para un rollout seguro y controlado.

## 🏗️ Arquitectura de Despliegue

### Workflows de GitHub Actions

1. **`staging-deploy.yml`** - Despliega a staging slot con feature flags
2. **`staging-to-prod-swap.yml`** - Swap seguro de staging a producción
3. **`azure_deploy.yml`** - Despliegue directo a producción (legacy)

### Feature Flags por Fase

| Fase | CONFIG_ADAPTER_ENABLED | CACHE_LAYER_ENABLED | CANARY_INGEST_ENABLED | Descripción |
|------|----------------------|-------------------|---------------------|-------------|
| A1 | False | False | False | Basic hardening |
| A3 | False | False | False | Log sanitization |
| A4 | False | **True** | False | **Cache layer Redis** |
| A5 | False | True | True | Canary ingestion |

## 🚀 Proceso de Despliegue

### Paso 1: Preparar la Rama

```bash
# Desde tu repo local
git checkout -b devops/staging-slot-pipeline
git add .
git commit -m "CI: staging slot + flags + smoke"
git push -u origin devops/staging-slot-pipeline
```

### Paso 2: Ejecutar Workflow de Staging

1. Ve a **GitHub → Actions**
2. Selecciona **"Deploy to STAGING (slot)"**
3. Configura los parámetros:
   - **phase**: `A4` (para cache layer Redis)
   - **dry_run**: `false`
4. Haz clic en **"Run workflow"**

### Paso 3: Verificar Smoke Test Automático

En el log del job, busca:

```
[smoke] OK p50=120ms p95=480ms
```

Si aparece `FAIL`, **NO** pases a producción.

### Paso 4: Checks Manuales en Staging

Usa tu `STAGING_BASE_URL` (ejemplos con curl):

```bash
# Health (debería dar 200 en <300ms p50)
curl -s -o /dev/null -w "HTTP:%{http_code} time:%{time_total}s\n" https://TU-STAGING/health

# Health extendidos (si existen)
curl -I https://TU-STAGING/api/v1/health
curl -I https://TU-STAGING/api/whatsapp/health

# Descarga de documentos (reemplaza {id})
curl -I https://TU-STAGING/documents/download/123

# Cache stats (solo si activaste A4)
curl -s https://TU-STAGING/ops/cache/stats
```

### Paso 5: Verificación Automatizada

Ejecuta el script de verificación:

```bash
python scripts/verify_staging_deployment.py
```

O configura la variable de entorno:

```bash
export STAGING_BASE_URL="https://vea-connect-staging.azurewebsites.net"
python scripts/verify_staging_deployment.py
```

### Paso 6: Swap a Producción

Si todo está bien → Swap a PROD:

1. Ve a **GitHub → Actions**
2. Selecciona **"Swap STAGING -> PROD"**
3. Configura:
   - **confirm_swap**: `YES`
   - **rollback_on_failure**: `true`
4. Haz clic en **"Run workflow"**

## ✅ Criterios de Aceptación

### Health Check
- ✅ HTTP 200 en `/health`
- ✅ Response time < 300ms (p50)
- ✅ Response time < 1000ms (p95)

### Documentos
- ✅ `/documents/download/{id}` responde 302 (Blob SAS) o 200 (FileResponse)

### Logs
- ✅ En logs de STAGING no hay secretos/PII

### Cache Layer (A4)
- ✅ `/ops/cache/stats` devuelve `{"enabled": true, ...}`
- ✅ Cache hit/miss logging funcionando

## 🔧 URLs de Staging

### Formato de URL
```
https://{WEBAPP_NAME}-{STAGING_SLOT}.azurewebsites.net
```

### Ejemplo
```
https://vea-connect-staging.azurewebsites.net
```

## 🚨 Rollback Strategy

### Rollback Automático
- Si el health check falla después del swap, se hace rollback automático
- El workflow **"Swap STAGING -> PROD"** incluye rollback automático

### Rollback Manual
Si necesitas hacer rollback manual:

1. Ve a **GitHub → Actions**
2. Ejecuta **"Swap STAGING -> PROD"** nuevamente
3. Esto intercambia staging y producción

### Desactivar Feature Flags
Para desactivar feature flags en producción:

```bash
# Via Azure CLI
az webapp config appsettings set \
  --name vea-connect \
  --resource-group rg-vea-connect-dev \
  --settings CACHE_LAYER_ENABLED=False
```

## 📊 Monitoreo

### Métricas a Observar

#### Durante Staging
- Hit rate del cache > 60%
- Sin errores de conexión Redis
- Response times estables

#### Durante Producción (24-48h)
- P50/P95 response times
- Cache hit rate > 70%
- Sin errores de conexión
- Métricas de Redis (memoria, conexiones)

### Endpoints de Monitoreo

```bash
# Health general
curl https://vea-connect.azurewebsites.net/health

# Cache stats (solo admin)
curl https://vea-connect.azurewebsites.net/ops/cache/stats

# Application Insights
# Ver en Azure Portal → Application Insights → Logs
```

## 🔍 Troubleshooting

### Problemas Comunes

#### Health Check Falla
```bash
# Verificar logs de staging
az webapp log tail --name vea-connect --resource-group rg-vea-connect-dev --slot staging
```

#### Cache No Funciona
```bash
# Verificar configuración Redis
az webapp config appsettings list --name vea-connect --resource-group rg-vea-connect-dev --slot staging
```

#### Swap Falla
```bash
# Verificar estado de slots
az webapp deployment slot list --name vea-connect --resource-group rg-vea-connect-dev
```

### Logs Útiles

```bash
# Logs de staging
az webapp log tail --name vea-connect --resource-group rg-vea-connect-dev --slot staging

# Logs de producción
az webapp log tail --name vea-connect --resource-group rg-vea-connect-dev
```

## 📝 Checklist de Despliegue

### Antes del Despliegue
- [ ] Rama `devops/staging-slot-pipeline` creada
- [ ] Cambios committeados y pusheados
- [ ] Tests locales pasando
- [ ] Feature flags configurados correctamente

### Durante el Despliegue
- [ ] Workflow de staging ejecutado
- [ ] Smoke test pasó (`[smoke] OK`)
- [ ] Health check manual verificado
- [ ] Cache stats endpoint verificado (A4)
- [ ] Performance metrics aceptables

### Después del Swap
- [ ] Health check de producción verificado
- [ ] Métricas de rendimiento monitoreadas
- [ ] Logs verificados (sin secretos/PII)
- [ ] Cache funcionando (A4)

## 🎯 Próximos Pasos

1. **Configurar Redis** en staging para pruebas completas
2. **Monitorear hit rate** en staging por 1-2 semanas
3. **Activar en producción** cuando hit rate > 60%
4. **Monitorear métricas** P50/P95 por 24-48 horas
5. **Optimizar TTLs** basado en patrones de uso

---

**Última actualización**: 2025-08-12
**Versión**: 1.0
**Autor**: DevOps Team
