# Arquitectura Completa y Despliegue - VEA Connect

## **Arquitectura del Sistema**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web App       │    │  Azure Functions │    │  Event Grid     │
│   (Django)      │    │  (Embeddings)    │    │  (WhatsApp)     │
│                 │    │                  │    │                 │
│ - Frontend      │    │ - API Embeddings │    │ - Webhooks      │
│ - Document Mgmt │    │ - Semantic Search│    │ - Message Proc  │
│ - User Interface│    │ - CRUD Operations│    │ - Delivery Rep  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │ Azure Blob      │
                    │ Storage         │
                    │                 │
                    │ - documents/    │
                    │ - converted/    │
                    └─────────────────┘
```

## **Componentes Identificados**

### **1. Web App (Django) - Ya creada**
- **Nombre**: `veaconnect-webapp-prod`
- **Runtime**: Python 3.10
- **Estado**: Running (sin despliegue)

### **2. Azure Functions - Necesita despliegue**
- **Función**: `embedding_api_function.py`
- **Propósito**: API para embeddings y búsqueda semántica
- **Endpoints**:
  - `POST /api/embeddings/create`
  - `GET /api/embeddings/get`
  - `PUT /api/embeddings/update`
  - `DELETE /api/embeddings/delete`
  - `POST /api/embeddings/search`

### **3. Event Grid - Configurado**
- **Handler**: `apps/whatsapp_bot/event_grid_handler.py`
- **Propósito**: Procesar eventos de WhatsApp
- **Eventos**: MessageReceived, DeliveryReport

### **4. Azure Blob Storage - Ya existe**
- **Contenedores**: `documents`, `converted`

## **Plan de Despliegue Completo**

### **Fase 1: Desplegar Web App (Django)**

#### **1.1 Preparar código para Web App**
```bash
# Crear ZIP del proyecto Django (excluyendo functions/)
# El ZIP debe contener:
# - apps/
# - config/
# - utilities/
# - manage.py
# - requirements.txt
# - runtime.txt
# - startup.sh
# - .deployment
```

#### **1.2 Variables de entorno para Web App**
```
AZURE_STORAGE_CONNECTION_STRING = DefaultEndpointsProtocol=https;AccountName=TU_STORAGE;AccountKey=TU_KEY;EndpointSuffix=core.windows.net
BLOB_ACCOUNT_NAME = TU_STORAGE_NAME
BLOB_ACCOUNT_KEY = TU_KEY
BLOB_CONTAINER_NAME = documents
DEBUG = False
SECRET_KEY = django-insecure-prod-key-aqui
ALLOWED_HOSTS = veaconnect-webapp-prod-c7aaezbce3ftacdp.centralus-01.azurewebsites.net
AZURE_FUNCTIONS_URL = https://veaconnect-functions.azurewebsites.net/api
```

#### **1.3 Desplegar Web App con Azure CLI**
```bash
# Crear ZIP
powershell Compress-Archive -Path "apps,config,utilities,manage.py,requirements.txt,runtime.txt,startup.sh,.deployment" -DestinationPath "webapp.zip"

# Desplegar
az webapp deployment source config-zip --resource-group rg-vea-connect-dev --name veaconnect-webapp-prod --src webapp.zip
```

### **Fase 2: Crear y Desplegar Azure Functions**

#### **2.1 Crear Function App**
```bash
# Crear Function App
az functionapp create \
  --resource-group rg-vea-connect-dev \
  --consumption-plan-location "Central US" \
  --runtime python \
  --runtime-version 3.10 \
  --functions-version 4 \
  --name veaconnect-functions \
  --storage-account TU_STORAGE_NAME \
  --os-type linux
```

#### **2.2 Variables de entorno para Functions**
```bash
az functionapp config appsettings set \
  --resource-group rg-vea-connect-dev \
  --name veaconnect-functions \
  --settings \
    AZURE_OPENAI_ENDPOINT="https://tu-openai-resource.openai.azure.com/" \
    AZURE_OPENAI_CHAT_DEPLOYMENT="gpt-35-turbo" \
    AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT="text-embedding-ada-002" \
    AZURE_OPENAI_CHAT_API_VERSION="2025-01-01-preview" \
    AZURE_OPENAI_EMBEDDINGS_API_VERSION="2023-05-15" \
    OPENAI_API_KEY="tu-openai-key" \
    AZURE_REDIS_CONNECTIONSTRING="tu-redis-connection-string"
```

#### **2.3 Desplegar Functions**
```bash
# Navegar al directorio functions
cd functions

# Desplegar
func azure functionapp publish veaconnect-functions
```

### **Fase 3: Configurar Event Grid**

#### **3.1 Crear Event Grid Topic**
```bash
# Crear Event Grid Topic para WhatsApp
az eventgrid topic create \
  --resource-group rg-vea-connect-dev \
  --name veaconnect-whatsapp-events \
  --location "Central US"
```

#### **3.2 Configurar Webhook**
```bash
# Crear subscription para la web app
az eventgrid event-subscription create \
  --resource-group rg-vea-connect-dev \
  --topic-name veaconnect-whatsapp-events \
  --name whatsapp-webhook \
  --endpoint https://veaconnect-webapp-prod-c7aaezbce3ftacdp.centralus-01.azurewebsites.net/api/whatsapp/event-grid/
```

### **Fase 4: Configurar Azure Communication Services**

#### **4.1 Variables adicionales para Web App**
```
ACS_CONNECTION_STRING = endpoint=https://tu-acs-resource.communication.azure.com/;accesskey=tu-key
ACS_EVENT_GRID_TOPIC_ENDPOINT = https://veaconnect-whatsapp-events.centralus-1.eventgrid.azure.net/api/events
ACS_EVENT_GRID_TOPIC_KEY = tu-event-grid-key
ACS_PHONE_NUMBER = +1234567890
ACS_WHATSAPP_API_KEY = tu-whatsapp-key
ACS_WHATSAPP_ENDPOINT = https://tu-acs-resource.communication.azure.com/
WHATSAPP_ACCESS_TOKEN = tu-access-token
WHATSAPP_CHANNEL_ID_GUID = tu-channel-id
```

## **Comandos de Despliegue Completos**

### **Script de Despliegue Automático**
```bash
#!/bin/bash

echo "🚀 Iniciando despliegue completo de VEA Connect..."

# 1. Desplegar Web App
echo "📦 Desplegando Web App..."
powershell Compress-Archive -Path "apps,config,utilities,manage.py,requirements.txt,runtime.txt,startup.sh,.deployment" -DestinationPath "webapp.zip" -Force
az webapp deployment source config-zip --resource-group rg-vea-connect-dev --name veaconnect-webapp-prod --src webapp.zip

# 2. Crear Function App (si no existe)
echo "⚡ Creando Function App..."
az functionapp create \
  --resource-group rg-vea-connect-dev \
  --consumption-plan-location "Central US" \
  --runtime python \
  --runtime-version 3.10 \
  --functions-version 4 \
  --name veaconnect-functions \
  --storage-account TU_STORAGE_NAME \
  --os-type linux

# 3. Desplegar Functions
echo "🔧 Desplegando Functions..."
cd functions
func azure functionapp publish veaconnect-functions
cd ..

# 4. Configurar Event Grid
echo "📡 Configurando Event Grid..."
az eventgrid topic create \
  --resource-group rg-vea-connect-dev \
  --name veaconnect-whatsapp-events \
  --location "Central US"

echo "✅ Despliegue completado!"
```

## **Verificación Post-Despliegue**

### **1. Verificar Web App**
```bash
# Ver logs
az webapp log tail --name veaconnect-webapp-prod --resource-group rg-vea-connect-dev

# Probar URL
curl https://veaconnect-webapp-prod-c7aaezbce3ftacdp.centralus-01.azurewebsites.net
```

### **2. Verificar Functions**
```bash
# Ver logs
az functionapp logs tail --name veaconnect-functions --resource-group rg-vea-connect-dev

# Probar endpoint
curl https://veaconnect-functions.azurewebsites.net/api/embeddings/health
```

### **3. Verificar Event Grid**
```bash
# Ver subscriptions
az eventgrid event-subscription list --topic-name veaconnect-whatsapp-events --resource-group rg-vea-connect-dev
```

## **URLs Finales**

- **Web App**: `https://veaconnect-webapp-prod-c7aaezbce3ftacdp.centralus-01.azurewebsites.net`
- **Functions API**: `https://veaconnect-functions.azurewebsites.net/api`
- **Event Grid**: `https://veaconnect-whatsapp-events.centralus-1.eventgrid.azure.net`

## **Próximos Pasos**

1. **Ejecutar script de despliegue**
2. **Configurar variables de entorno**
3. **Verificar todos los componentes**
4. **Probar funcionalidad completa**

¿Quieres que procedamos con el despliegue paso a paso? 