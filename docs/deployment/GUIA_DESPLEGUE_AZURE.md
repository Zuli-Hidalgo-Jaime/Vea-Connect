# Guía de Despliegue - VEA Connect en Azure

## **Estado Actual**
- ✅ Web App creada: `veaconnect-webapp-prod`
- ✅ Runtime configurado: Python 3.10
- ❌ Sin despliegues realizados
- ❌ Azure Blob Storage no configurado

## **Paso 1: Crear Azure Blob Storage**

### **1.1 Crear cuenta de almacenamiento**
1. Ve a Azure Portal → "Storage accounts"
2. Click "Create"
3. Configuración:
   - **Resource group**: `rg-vea-connect-dev` (mismo que web app)
   - **Storage account name**: `veaconnectstorage` (debe ser único globalmente)
   - **Location**: Central US (mismo que web app)
   - **Performance**: Standard
   - **Redundancy**: LRS

### **1.2 Crear contenedores**
Una vez creada la cuenta:
1. Ve a "Containers" en el menú izquierdo
2. Crear contenedor: `documents`
3. Crear contenedor: `converted`

### **1.3 Obtener credenciales**
1. Ve a "Access keys" en el menú izquierdo
2. Copia:
   - **Storage account name**
   - **Key1** (connection string)

## **Paso 2: Configurar Variables de Entorno**

### **2.1 En Azure Portal**
1. Ve a tu web app `veaconnect-webapp-prod`
2. Menú izquierdo → "Settings" → "Configuration"
3. Click "New application setting" para cada variable:

```
AZURE_STORAGE_CONNECTION_STRING = DefaultEndpointsProtocol=https;AccountName=veaconnectstorage;AccountKey=TU_KEY_AQUI;EndpointSuffix=core.windows.net
BLOB_ACCOUNT_NAME = veaconnectstorage
BLOB_ACCOUNT_KEY = TU_KEY_AQUI
BLOB_CONTAINER_NAME = documents
DEBUG = False
SECRET_KEY = django-insecure-prod-key-aqui
ALLOWED_HOSTS = veaconnect-webapp-prod-c7aaezbce3ftacdp.centralus-01.azurewebsites.net
```

### **2.2 Variables opcionales (si las tienes)**
```
AZURE_OPENAI_ENDPOINT = https://tu-openai-resource.openai.azure.com/
AZURE_OPENAI_CHAT_DEPLOYMENT = gpt-35-turbo
AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT = text-embedding-ada-002
AZURE_OPENAI_CHAT_API_VERSION = 2025-01-01-preview
AZURE_OPENAI_EMBEDDINGS_API_VERSION = 2023-05-15
OPENAI_API_KEY = tu-openai-key
VISION_ENDPOINT = https://tu-vision-resource.cognitiveservices.azure.com/
VISION_KEY = tu-vision-key
AZURE_SEARCH_ENDPOINT = https://tu-search-service.search.windows.net
AZURE_SEARCH_KEY = tu-search-key
AZURE_SEARCH_INDEX_NAME = documents
```

## **Paso 3: Desplegar Código**

### **3.1 Opción A: Azure CLI (Recomendado)**
```bash
# Instalar Azure CLI si no lo tienes
# https://docs.microsoft.com/en-us/cli/azure/install-azure-cli

# Login
az login

# Configurar suscripción
az account set --subscription "9f47ecda-6fbc-479d-888a-a5966f0c9c50"

# Desplegar
az webapp deployment source config-zip --resource-group rg-vea-connect-dev --name veaconnect-webapp-prod --src ./deploy.zip
```

### **3.2 Opción B: GitHub Actions**
1. Ve a "Deployment Center" en tu web app
2. Selecciona "GitHub" como fuente
3. Conecta tu repositorio
4. Configura el workflow

### **3.3 Opción C: Visual Studio Code**
1. Instala extensión "Azure App Service"
2. Login con tu cuenta Azure
3. Click derecho en la web app → "Deploy to Web App"

## **Paso 4: Preparar Código para Despliegue**

### **4.1 Crear archivo requirements.txt**
```bash
pip freeze > requirements.txt
```

### **4.2 Crear archivo runtime.txt**
```
python-3.10
```

### **4.3 Crear archivo startup.sh**
```bash
#!/bin/bash
python manage.py migrate
python manage.py collectstatic --noinput
gunicorn --bind=0.0.0.0 --timeout 600 config.wsgi
```

### **4.4 Crear archivo .deployment**
```
[config]
command = bash startup.sh
```

## **Paso 5: Verificar Despliegue**

### **5.1 Revisar logs**
1. En Azure Portal → tu web app
2. Menú izquierdo → "Log stream"
3. Verificar que no hay errores

### **5.2 Probar aplicación**
1. Ve a: `https://veaconnect-webapp-prod-c7aaezbce3ftacdp.centralus-01.azurewebsites.net`
2. Verifica que carga correctamente
3. Prueba subir un documento

## **Paso 6: Configurar Dominio Personalizado (Opcional)**

### **6.1 En Azure Portal**
1. Ve a "Custom domains" en tu web app
2. Agrega tu dominio
3. Configura DNS según las instrucciones

## **Solución de Problemas Comunes**

### **Error: "No module named 'django'"**
- Verificar que `Django` está en `requirements.txt`

### **Error: "Database connection failed"**
- Verificar variables de entorno de base de datos

### **Error: "Storage connection failed"**
- Verificar credenciales de Azure Blob Storage

### **Error: "Static files not found"**
- Ejecutar `python manage.py collectstatic` en startup

## **Comandos Útiles**

### **Ver logs en tiempo real**
```bash
az webapp log tail --name veaconnect-webapp-prod --resource-group rg-vea-connect-dev
```

### **Reiniciar web app**
```bash
az webapp restart --name veaconnect-webapp-prod --resource-group rg-vea-connect-dev
```

### **Ver variables de entorno**
```bash
az webapp config appsettings list --name veaconnect-webapp-prod --resource-group rg-vea-connect-dev
```

## **Próximos Pasos**

1. **Crear Azure Blob Storage** (Paso 1)
2. **Configurar variables de entorno** (Paso 2)
3. **Preparar código** (Paso 4)
4. **Desplegar** (Paso 3)
5. **Verificar** (Paso 5)

¿Necesitas ayuda con algún paso específico? 