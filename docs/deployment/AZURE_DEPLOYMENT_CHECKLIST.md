# Checklist de Despliegue a Azure

## 🚀 **Preparación Inicial**

### **Requisitos Previos:**
- [ ] Azure CLI instalado y autenticado
- [ ] Suscripción Azure activa
- [ ] Permisos de administrador en la suscripción
- [ ] SSH key generada (para VM)

### **Configuración Local:**
- [ ] Azure CLI login: `az login`
- [ ] Verificar suscripción: `az account show`
- [ ] Generar SSH key: `ssh-keygen -t rsa -b 4096`

## 📦 **Recursos a Crear**

### **1. Resource Group**
- [ ] Nombre: `vea-resource-group`
- [ ] Región: `eastus` o `westeurope`
- [ ] Crear con: `az group create`

### **2. App Service Plan**
- [ ] Nombre: `vea-app-service-plan`
- [ ] SKU: `B1` (Basic) o `S1` (Standard)
- [ ] OS: Linux
- [ ] Runtime: Python 3.10

### **3. App Service**
- [ ] Nombre: `vea-webapp-process-botconnect`
- [ ] Plan: `vea-app-service-plan`
- [ ] Runtime: `PYTHON|3.10`
- [ ] Startup command: `gunicorn --bind=0.0.0.0 --timeout 600 config.wsgi:application`

### **4. PostgreSQL Database**
- [ ] Servidor: `vea-postgresql-server`
- [ ] Base de datos: `vea_database`
- [ ] Usuario admin: `vea_admin`
- [ ] Contraseña: [GENERAR FUERTE]
- [ ] Versión: PostgreSQL 13
- [ ] SKU: `Standard_B1ms`

### **5. Azure Blob Storage**
- [ ] Storage Account: `veastorageaccount[timestamp]`
- [ ] SKU: `Standard_LRS`
- [ ] Containers:
  - [ ] `static`
  - [ ] `media`
  - [ ] `documents`



## ⚙️ **Configuración de Variables de Entorno**

### **App Service Configuration:**
- [ ] `AZURE_POSTGRESQL_NAME=vea_database`
- [ ] `AZURE_POSTGRESQL_USERNAME=vea_admin@vea-postgresql-server`
- [ ] `AZURE_POSTGRESQL_PASSWORD=[CONTRASEÑA]`
- [ ] `AZURE_POSTGRESQL_HOST=vea-postgresql-server.postgres.database.azure.com`
- [ ] `DB_PORT=5432`
- [ ] `AZURE_STORAGE_CONNECTION_STRING=[CONNECTION_STRING]`
- [ ] `BLOB_ACCOUNT_NAME=[STORAGE_ACCOUNT_NAME]`
- [ ] `BLOB_ACCOUNT_KEY=[STORAGE_KEY]`
- [ ] `BLOB_CONTAINER_NAME=documents`
- [ ] `AZURE_REDIS_CONNECTIONSTRING=[OPCIONAL - Solo para WhatsApp Bot]`
- [ ] `DEBUG=False`
- [ ] `SECRET_KEY=[DJANGO_SECRET_KEY]`
- [ ] `ALLOWED_HOSTS=vea-webapp-process-botconnect.azurewebsites.net,localhost,127.0.0.1`



## 🔧 **Configuración de Django**

### **Migraciones:**
- [ ] Ejecutar: `python manage.py migrate`
- [ ] Crear superusuario: `python manage.py createsuperuser`
- [ ] Colectar archivos estáticos: `python manage.py collectstatic`

### **Verificaciones:**
- [ ] App Service responde correctamente
- [ ] Base de datos conecta sin errores
- [ ] Archivos se suben a Blob Storage
- [ ] Login funciona correctamente

## 🔒 **Seguridad**

### **Firewall y Networking:**
- [ ] VM firewall configurado
- [ ] Solo puertos necesarios abiertos
- [ ] Conexiones limitadas a App Service IP

### **Contraseñas:**
- [ ] PostgreSQL password fuerte
- [ ] Django SECRET_KEY generado
- [ ] Storage account key seguro

### **SSL/TLS:**
- [ ] App Service HTTPS habilitado
- [ ] PostgreSQL SSL requerido
- [ ] Redis conexión segura (si es necesario)

## 📊 **Monitoreo**

### **Logs:**
- [ ] App Service logs habilitados
- [ ] PostgreSQL logs configurados

### **Métricas:**
- [ ] App Service métricas activas
- [ ] Database métricas configuradas
- [ ] Storage métricas habilitadas

## 🚨 **Post-Despliegue**

### **Verificaciones Finales:**
- [ ] Aplicación accesible públicamente
- [ ] Todas las funcionalidades trabajan
- [ ] Performance aceptable
- [ ] Error logs limpios

### **Backup:**
- [ ] Database backup configurado
- [ ] Storage backup habilitado

### **Documentación:**
- [ ] Credenciales guardadas de forma segura
- [ ] URLs de acceso documentadas
- [ ] Procedimientos de mantenimiento creados

## 💰 **Costos Estimados (Mensual)**

### **Recursos:**
- [ ] App Service B1: ~$13/mes
- [ ] PostgreSQL Basic: ~$25/mes
- [ ] Storage Account: ~$2-5/mes
- [ ] **Total estimado: ~$40-43/mes**

## ✅ **Comandos de Verificación**

```bash
# Verificar App Service
curl -I https://vea-webapp-process-botconnect.azurewebsites.net

# Verificar PostgreSQL
psql "host=vea-postgresql-server.postgres.database.azure.com port=5432 dbname=vea_database user=vea_admin@vea-postgresql-server"



# Verificar Storage
az storage container list --account-name [STORAGE_ACCOUNT] --account-key [STORAGE_KEY]
```

## 🎯 **URLs de Acceso**

- **App Service:** https://vea-webapp-process-botconnect.azurewebsites.net
- **PostgreSQL:** vea-postgresql-server.postgres.database.azure.com:5432
- **Storage:** https://[STORAGE_ACCOUNT].blob.core.windows.net

## 📞 **Soporte**

- **Azure Support:** Portal Azure > Help + support
- **Documentación:** docs.microsoft.com
- **Community:** Stack Overflow, GitHub Issues 