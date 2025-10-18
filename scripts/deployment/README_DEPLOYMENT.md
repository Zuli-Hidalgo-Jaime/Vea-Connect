# Despliegue Directo desde Local a Azure

Este directorio contiene scripts para desplegar directamente desde tu entorno local a Azure sin necesidad de GitHub Actions.

## Prerrequisitos

1. **Azure CLI instalado y autenticado**
   ```powershell
   # Instalar Azure CLI (si no lo tienes)
   winget install Microsoft.AzureCLI
   
   # Autenticarse
   az login
   ```

2. **Python 3.11 instalado**
   ```powershell
   python --version
   ```

3. **Dependencias del proyecto instaladas**
   ```powershell
   pip install -r requirements.txt
   ```

4. **Variables de entorno configuradas**
   - Todas las variables de Azure necesarias
   - Secrets de la aplicacion

## Scripts Disponibles

### 1. `setup_deployment_env.ps1`
Configura las variables de entorno necesarias para el despliegue.

```powershell
.\scripts\deployment\setup_deployment_env.ps1
```

Este script:
- Crea un archivo `.env.deployment` con todas las variables necesarias
- Te muestra los valores de tu suscripcion actual
- Te da instrucciones para crear un Service Principal

### 2. `validate_deployment.ps1`
Valida que todo este configurado correctamente antes del despliegue.

```powershell
.\scripts\deployment\validate_deployment.ps1
```

Este script verifica:
- Azure CLI y autenticacion
- Archivos del proyecto
- Resource Group y Web App
- Variables de entorno
- Python y dependencias
- Conectividad con Azure

### 3. `deploy_local_to_azure.ps1`
Script principal de despliegue.

```powershell
.\scripts\deployment\deploy_local_to_azure.ps1
```

Este script:
- Verifica todas las configuraciones
- Ejecuta tests locales
- Recolecta archivos estaticos
- Crea un paquete ZIP
- Despliega a Azure
- Verifica el estado del despliegue

## Proceso de Despliegue

### Paso 1: Configurar Variables de Entorno

```powershell
# Generar plantilla de variables
.\scripts\deployment\setup_deployment_env.ps1

# Editar el archivo generado
notepad .env.deployment

# Copiar a .env
Copy-Item .env.deployment .env
```

### Paso 2: Configurar Service Principal (si no lo tienes)

```powershell
# Obtener tu Subscription ID
az account show --query id --output tsv

# Crear Service Principal
az ad sp create-for-rbac --name "vea-deployment-sp" --role contributor --scopes /subscriptions/TU_SUBSCRIPTION_ID
```

### Paso 3: Validar Configuracion

```powershell
.\scripts\deployment\validate_deployment.ps1
```

### Paso 4: Desplegar

```powershell
.\scripts\deployment\deploy_local_to_azure.ps1
```

## Variables de Entorno Requeridas

### Azure Communication Services
- `ACS_CONNECTION_STRING`
- `ACS_EVENT_GRID_TOPIC_ENDPOINT`
- `ACS_EVENT_GRID_TOPIC_KEY`
- `ACS_PHONE_NUMBER`
- `ACS_WHATSAPP_API_KEY`
- `ACS_WHATSAPP_ENDPOINT`

### Azure OpenAI
- `AZURE_OPENAI_CHAT_API_VERSION`
- `AZURE_OPENAI_CHAT_DEPLOYMENT`
- `AZURE_OPENAI_EMBEDDINGS_API_VERSION`
- `AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT`
- `AZURE_OPENAI_ENDPOINT`

### Azure PostgreSQL
- `AZURE_POSTGRESQL_HOST`
- `AZURE_POSTGRESQL_NAME`
- `AZURE_POSTGRESQL_PASSWORD`
- `AZURE_POSTGRESQL_USERNAME`

### Azure Search
- `AZURE_SEARCH_ENDPOINT`
- `AZURE_SEARCH_INDEX_NAME`
- `AZURE_SEARCH_KEY`

### Azure Blob Storage
- `BLOB_ACCOUNT_KEY`
- `BLOB_ACCOUNT_NAME`
- `BLOB_CONTAINER_NAME`

### Otros
- `DATABASE_URL`
- `OPENAI_API_KEY`
- `QUEUE_NAME`
- `VISION_ENDPOINT`
- `VISION_KEY`

### Service Principal (para despliegue)
- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`
- `AZURE_CLIENT_SECRET`

## Configuracion por Defecto

- **Resource Group**: `rg-vea-connect-dev`
- **Web App**: `veaconnect-webapp-prod`
- **Environment**: `production`

Puedes cambiar estos valores pasando parametros al script:

```powershell
.\scripts\deployment\deploy_local_to_azure.ps1 -ResourceGroupName "mi-rg" -AppName "mi-app" -Environment "staging"
```

## Solucion de Problemas

### Error: Azure CLI no autenticado
```powershell
az login
```

### Error: Resource Group no existe
Verifica que el Resource Group existe en tu suscripcion:
```powershell
az group list --output table
```

### Error: Web App no existe
Verifica que la Web App existe en el Resource Group:
```powershell
az webapp list --resource-group rg-vea-connect-dev --output table
```

### Error: Variables de entorno faltantes
Ejecuta el script de validacion para ver que variables faltan:
```powershell
.\scripts\deployment\validate_deployment.ps1
```

### Error: Tests fallan
Ejecuta los tests manualmente para ver los errores:
```powershell
python -m pytest --cov=apps --cov-report=term-missing
```

## Notas Importantes

1. **Seguridad**: Nunca commits el archivo `.env` con secrets reales
2. **Backup**: Siempre haz backup de tu base de datos antes de desplegar
3. **Testing**: Ejecuta tests completos antes de desplegar a produccion
4. **Rollback**: Ten un plan de rollback en caso de problemas

## Logs y Debugging

Los scripts generan logs detallados. Si hay problemas:

1. Revisa los mensajes de error en la consola
2. Verifica los logs de la Web App en Azure Portal
3. Usa el script de validacion para diagnosticar problemas

## Contacto

Si tienes problemas con el despliegue, revisa:
1. Los logs de error
2. La documentacion de Azure
3. Los archivos de configuracion del proyecto 