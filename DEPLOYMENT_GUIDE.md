# VEA Connect - Deployment Guide

## 📋 Prerrequisitos

- ✅ Repositorio configurado en GitHub
- ✅ Azure CLI instalado y configurado
- ✅ Permisos de administrador en Azure

## 🔐 Configuración de Secrets

Ve a tu repositorio → **Settings** → **Secrets and variables** → **Actions** y agrega estos secrets:

#### **Secrets de Azure (OBLIGATORIOS):**
```
AZURE_CLIENT_ID: your-azure-client-id
AZURE_TENANT_ID: your-azure-tenant-id
AZURE_SUBSCRIPTION_ID: your-azure-subscription-id
AZURE_CLIENT_SECRET: your-azure-client-secret
```

#### **Secrets de la Aplicación (ya configurados):**
- `ACS_CONNECTION_STRING`
- `ACS_EVENT_GRID_TOPIC_ENDPOINT`
- `ACS_EVENT_GRID_TOPIC_KEY`
- `ACS_PHONE_NUMBER`
- `ACS_WHATSAPP_API_KEY`
- `ACS_WHATSAPP_ENDPOINT`
- `AZURE_OPENAI_CHAT_API_VERSION`
- `AZURE_OPENAI_CHAT_DEPLOYMENT`
- `AZURE_OPENAI_EMBEDDINGS_API_VERSION`
- `AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT`
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_POSTGRESQL_HOST`
- `AZURE_POSTGRESQL_NAME`
- `AZURE_POSTGRESQL_PASSWORD`
- `AZURE_POSTGRESQL_USERNAME`
- `AZURE_SEARCH_ENDPOINT`
- `AZURE_SEARCH_INDEX_NAME`
- `AZURE_SEARCH_KEY`
- `BLOB_ACCOUNT_KEY`
- `BLOB_ACCOUNT_NAME`
- `BLOB_CONTAINER_NAME`
- `DATABASE_URL`
- `OPENAI_API_KEY`
- `QUEUE_NAME`
- `VISION_ENDPOINT`
- `VISION_KEY`
- `EVENT_GRID_VALIDATION_KEY`
- `AZURE_REDIS_CONNECTIONSTRING`

## 🚀 Cómo Desplegar

### Opción 1: Push Automático
```bash
git add .
git commit -m "Deploy completo"
git push origin main
```

### Opción 2: Manual desde GitHub
1. Ve a **Actions** en tu repositorio
2. Selecciona **"Deploy Complete Application"**
3. Haz clic en **"Run workflow"**
4. Selecciona la rama **main**
5. Haz clic en **"Run workflow"**

## 📊 Proceso de Deployment

### 1. **Tests** (5-10 minutos)
- ✅ Instala dependencias
- ✅ Ejecuta tests con cobertura
- ✅ Sube reporte de cobertura

### 2. **Deploy Web App** (10-15 minutos)
- ✅ Configura settings de Azure
- ✅ Despliega aplicación Django
- ✅ Verifica estado

### 3. **Deploy Functions** (5-10 minutos)
- ✅ Instala Azure Functions Core Tools
- ✅ Despliega Azure Functions
- ✅ Verifica estado

### 4. **Verificación Final** (2-3 minutos)
- ✅ Verifica ambos servicios
- ✅ Muestra URLs de acceso

## 🌐 URLs de Acceso

Una vez completado el deployment:

- **Web App**: https://your-webapp.azurewebsites.net
- **Functions**: https://your-functions.azurewebsites.net

## 🔍 Monitoreo

### En GitHub Actions:
1. Ve a **Actions** → **"Deploy Complete Application"**
2. Revisa los logs de cada job
3. Verifica que todos los pasos sean ✅ verdes

### En Azure Portal:
1. **Web App**: App Service → your-webapp
2. **Functions**: Function App → your-functions

## 🚨 Solución de Problemas

### Si falla la autenticación:
- Verifica que los 4 secrets de Azure estén configurados
- Asegúrate de que el Service Principal tenga permisos

### Si fallan los tests:
- Los tests están configurados para fallar solo si la cobertura es < 40%
- Revisa los logs para ver qué tests fallan

### Si falla el deployment:
- Revisa los logs del job específico
- Verifica que los recursos existan en Azure

## 📞 Soporte

Si tienes problemas:
1. Revisa los logs en GitHub Actions
2. Verifica la configuración de secrets
3. Asegúrate de que los recursos de Azure existan

---

**¡Listo! Con un solo push tendrás toda la aplicación desplegada.** 🎉 