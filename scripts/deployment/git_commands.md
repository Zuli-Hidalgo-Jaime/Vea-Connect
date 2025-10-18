# Comandos de Git para Despliegue LIMPIO con Python 3.10

## 1. Verificar estado actual
```bash
git status
```

## 2. Agregar todos los cambios
```bash
git add .
```

## 3. Crear commit
```bash
git commit -m "Fix: Configurar Python 3.10 y eliminar dependencia de run.sh

- Configurar Azure App Service para usar Python 3.10 del Dockerfile
- Eliminar comando de inicio personalizado para usar CMD del Dockerfile
- El workflow ya NO configura variables automáticamente
- Dockerfile ejecuta Gunicorn directamente sin run.sh"
```

## 4. Hacer push
```bash
git push origin main
```

## 5. DESPUÉS DEL PUSH - Configurar Python 3.10 y Dockerfile

### Opción A: Script completo (Recomendado)
```powershell
.\scripts\deployment\fix_azure_python_config.ps1 -ResourceGroup "rg-vea-connect-dev" -WebAppName "vea-connect"
```

### Opción B: Usando Azure CLI
```bash
# Configurar Python 3.10 y variables básicas
az webapp config appsettings set \
  --name vea-connect \
  --resource-group rg-vea-connect-dev \
  --settings \
  WEBSITES_PORT=8000 \
  DJANGO_SETTINGS_MODULE=config.settings.production \
  DEBUG=False \
  ALLOWED_HOSTS=vea-connect.azurewebsites.net,*.azurewebsites.net \
  WEBSITES_ENABLE_APP_SERVICE_STORAGE=true \
  PYTHON_VERSION=3.10 \
  PYTHONUNBUFFERED=1 \
  PORT=8000

# Configurar para usar Dockerfile (sin run.sh)
az webapp config set \
  --name vea-connect \
  --resource-group rg-vea-connect-dev \
  --linux-fx-version DOCKER \
  --startup-file ""

# Habilitar logs
az webapp log config \
  --name vea-connect \
  --resource-group rg-vea-connect-dev \
  --docker-container-logging filesystem

# Reiniciar aplicación
az webapp restart --name vea-connect --resource-group rg-vea-connect-dev
```

## 6. Verificar configuración
```bash
# Ver logs en tiempo real
az webapp log tail --name vea-connect --resource-group rg-vea-connect-dev

# Verificar health check
curl https://vea-connect.azurewebsites.net/health/

# Verificar configuración de Python y Docker
az webapp config show --name vea-connect --resource-group rg-vea-connect-dev --query linuxFxVersion
az webapp config appsettings list --name vea-connect --resource-group rg-vea-connect-dev --query '[?name==`PYTHON_VERSION` || name==`WEBSITES_PORT`]'
```

## 7. Si necesitas corregir variables de PostgreSQL manualmente
```powershell
# Solo si las variables están malformateadas
.\scripts\deployment\fix_azure_variables.ps1 -ResourceGroup "rg-vea-connect-dev" -WebAppName "vea-connect"
```

## Problemas Identificados y Solucionados:

### ❌ Problema 1: Python 3.10 vs 3.9
- **Causa:** Azure App Service intentaba usar Python 3.9 de la imagen estándar
- **Solución:** Configurar para usar Python 3.10 del Dockerfile personalizado

### ❌ Problema 2: Error con run.sh
- **Causa:** Azure App Service intentaba ejecutar `run.sh` que no estaba configurado correctamente
- **Solución:** Eliminar comando de inicio personalizado para usar CMD del Dockerfile

### ❌ Problema 3: Variables malformateadas
- **Causa:** Workflow de GitHub Actions malformateaba variables de PostgreSQL
- **Solución:** Eliminar toda configuración automática de variables del workflow

### ✅ Solución Implementada:
- **Python 3.10:** Configurado desde el Dockerfile
- **Dockerfile:** Ejecuta Gunicorn directamente sin run.sh
- **Workflow limpio:** Solo construye y despliega Docker
- **Variables:** Se configuran manualmente para evitar malformateo

### 🔧 Nueva Estrategia:
1. **Workflow:** Solo construye y despliega la imagen Docker
2. **Dockerfile:** Usa Python 3.10 y ejecuta Gunicorn directamente
3. **Azure App Service:** Configurado para usar Dockerfile sin interferencias
4. **Variables de PostgreSQL:** Se configuran manualmente en Azure Portal

### 📋 Variables que NO se tocan:
- `AZURE_POSTGRESQL_NAME`
- `AZURE_POSTGRESQL_USERNAME`
- `AZURE_POSTGRESQL_PASSWORD`
- `AZURE_POSTGRESQL_HOST`
- `DATABASE_URL`
- `SECRET_KEY`
- Cualquier otra variable de Azure

### 🐍 Configuración de Python:
- **Versión:** Python 3.10 (desde Dockerfile)
- **Comando:** Gunicorn directo (sin run.sh)
- **Puerto:** 8000
- **Workers:** 2
- **Timeout:** 120 segundos
