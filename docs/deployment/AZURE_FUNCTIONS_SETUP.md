# Configuración de Azure Functions - Complemento a Django App Service

## 🏗️ **Arquitectura Híbrida: Django + Azure Functions**

El proyecto utiliza **dos componentes separados**:

1. **Django Web App** (App Service) - Interfaz web, admin, CRUD operations
2. **Azure Functions** (Function App) - Event Grid Triggers para WhatsApp

## 📋 **Configuración del Django App Service**

### **1. App Settings para Django App Service**

Configura estas variables en Azure Portal → App Service → Configuration → Application settings:

```bash
# === DJANGO CONFIGURATION ===
DJANGO_SETTINGS_MODULE=config.settings.production
SECRET_KEY=<tu-django-secret-key>
DEBUG=False
ALLOWED_HOSTS=*.azurewebsites.net

# === PYTHON CONFIGURATION ===
PYTHON_VERSION=3.10
PYTHONPATH=/home/site/wwwroot
PYTHONUNBUFFERED=1

# === DATABASE CONFIGURATION ===
AZURE_POSTGRESQL_NAME=vea_database
AZURE_POSTGRESQL_USERNAME=vea_admin@vea-postgresql-server
AZURE_POSTGRESQL_PASSWORD=<tu-password>
AZURE_POSTGRESQL_HOST=vea-postgresql-server.postgres.database.azure.com
DB_PORT=5432

# === AZURE SERVICES ===
AZURE_STORAGE_CONNECTION_STRING=<tu-storage-connection-string>
AZURE_OPENAI_ENDPOINT=<tu-openai-endpoint>
AZURE_OPENAI_API_KEY=<tu-openai-api-key>

# === WHATSAPP BOT (OPCIONAL) ===
AZURE_REDIS_CONNECTIONSTRING=<tu-redis-connection-string>
```

### **2. Startup Command para Django**

En Azure Portal → App Service → Configuration → General settings:

```bash
# Para Django App Service
startup.sh
```

### **3. Runtime Stack para Django**

```bash
# Platform: Linux
# Runtime: Python 3.10
# Stack: Python
```

## 📋 **Configuración del Azure Functions**

### **1. App Settings para Function App**

Configura estas variables en Azure Portal → Function App → Configuration → Application settings:

```bash
# === RUNTIME CONFIGURATION ===
FUNCTIONS_WORKER_RUNTIME=python
FUNCTIONS_EXTENSION_VERSION=~4
WEBSITE_RUN_FROM_PACKAGE=1

# === PYTHON CONFIGURATION ===
PYTHON_VERSION=3.10
PYTHONPATH=/home/site/wwwroot

# === DATABASE CONFIGURATION ===
AZURE_POSTGRESQL_NAME=vea_database
AZURE_POSTGRESQL_USERNAME=vea_admin@vea-postgresql-server
AZURE_POSTGRESQL_PASSWORD=<tu-password>
AZURE_POSTGRESQL_HOST=vea-postgresql-server.postgres.database.azure.com

# === AZURE SERVICES ===
AZURE_STORAGE_CONNECTION_STRING=<tu-storage-connection-string>
AZURE_OPENAI_ENDPOINT=<tu-openai-endpoint>
AZURE_OPENAI_API_KEY=<tu-openai-api-key>

# === WHATSAPP BOT ===
AZURE_REDIS_CONNECTIONSTRING=<tu-redis-connection-string>
ACS_CONNECTION_STRING=<tu-acs-connection-string>
ACS_EVENT_GRID_TOPIC_ENDPOINT=<tu-event-grid-endpoint>
ACS_EVENT_GRID_TOPIC_KEY=<tu-event-grid-key>
ACS_PHONE_NUMBER=whatsapp:+1234567890
```

### **2. Startup Command para Functions**

```bash
# Para Azure Functions
func start
```

## 📁 **Estructura de Archivos Correcta**

```
/home/site/wwwroot/ (Django App Service)
├── startup.sh                           # ✅ Script de inicio para Django
├── apps/                               # ✅ Aplicaciones Django
├── config/                             # ✅ Configuración Django
├── manage.py                           # ✅ Django management
└── requirements.txt                    # ✅ Dependencias Django

/functions/ (Azure Functions)
├── host.json                           # ✅ Configuración del Function App
├── function.json                       # ✅ Configuración del trigger
├── whatsapp_event_grid_trigger_function.py  # ✅ Función principal
├── django_integration.py               # ✅ Integración con Django
└── requirements.txt                    # ✅ Dependencias de Functions
```

## 🔧 **Archivos de Configuración Clave**

### **startup.sh (Django App Service)**
```bash
#!/bin/bash
# Script actualizado para Django sin Redis general
# Incluye verificaciones de arquitectura
# Usa Python 3.10 y configuración de producción
```

### **functions/host.json (Azure Functions)**
```json
{
  "version": "2.0",
  "logging": {
    "applicationInsights": {
      "samplingSettings": {
        "isEnabled": true,
        "excludedTypes": "Request"
      }
    }
  },
  "extensionBundle": {
    "id": "Microsoft.Azure.Functions.ExtensionBundle",
    "version": "[4.*, 5.0.0)"
  },
  "functionTimeout": "00:05:00",
  "http": {
    "routePrefix": "api"
  }
}
```

### **functions/function.json (Azure Functions)**
```json
{
  "scriptFile": "whatsapp_event_grid_trigger_function.py",
  "bindings": [
    {
      "type": "eventGridTrigger",
      "name": "event",
      "direction": "in"
    }
  ]
}
```

## 🚀 **Despliegue**

### **1. Django App Service**

```bash
# Despliegue automático con GitHub Actions
# O manualmente:
az webapp deployment source config-zip \
  --resource-group <tu-resource-group> \
  --name <tu-django-app-name> \
  --src django-app.zip
```

### **2. Azure Functions**

```bash
# Desde el directorio functions/
cd functions
func azure functionapp publish <tu-function-app-name> --python
```

## 🔍 **Monitoreo y Logs**

### **Django App Service**
```bash
# Ver logs en tiempo real
az webapp log tail \
  --name <tu-django-app-name> \
  --resource-group <tu-resource-group>
```

### **Azure Functions**
```bash
# Ver logs en tiempo real
az webapp log tail \
  --name <tu-function-app-name> \
  --resource-group <tu-resource-group>
```

## 🧪 **Testing**

### **Django App Service**
```bash
# Test local Django
python manage.py runserver
```

### **Azure Functions**
```bash
# Test local Functions
cd functions
func start
```

## ✅ **Ventajas de la Arquitectura Híbrida**

1. **Django App Service** - Interfaz web completa, admin, CRUD
2. **Azure Functions** - Procesamiento de eventos escalable
3. **Separación de responsabilidades** - Web vs Event processing
4. **Escalabilidad independiente** - Cada componente escala según necesidad
5. **Mantenimiento simplificado** - Cada componente tiene su configuración

## 🔗 **Referencias**

- [Azure App Service Python](https://docs.microsoft.com/en-us/azure/app-service/configure-language-python)
- [Azure Functions Python](https://docs.microsoft.com/en-us/azure/azure-functions/functions-reference-python)
- [Event Grid Triggers](https://docs.microsoft.com/en-us/azure/azure-functions/functions-bindings-event-grid) 