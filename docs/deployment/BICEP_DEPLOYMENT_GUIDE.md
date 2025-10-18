# 🚀 Guía de Despliegue con Bicep

## 📋 **Resumen**

Esta guía te permite desplegar toda la infraestructura de tu proyecto VEA usando Azure Bicep, que es más eficiente y declarativo que crear recursos manualmente.

## 🎯 **Recursos que se Crean**

### **Infraestructura de Red:**
- ✅ Virtual Network con subnet
- ✅ Network Security Group (puertos 22, 6379, 8001, 80, 443)
- ✅ Public IP para VM

### **Aplicación:**
- ✅ App Service Plan (B1 - Basic)
- ✅ App Service con Python 3.10
- ✅ Variables de entorno configuradas

### **Base de Datos:**
- ✅ PostgreSQL Flexible Server
- ✅ Base de datos `vea_database`

### **Almacenamiento:**
- ✅ Storage Account con 3 containers:
  - `static` (archivos estáticos)
  - `media` (archivos multimedia)
  - `documents` (documentos)



### **Seguridad:**
- ✅ Key Vault para secretos
- ✅ Contraseñas seguras generadas automáticamente

## 🛠️ **Requisitos Previos**

### **1. Azure CLI**
```bash
# Instalar Azure CLI
# Windows: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli-windows
# macOS: brew install azure-cli
# Linux: curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Verificar instalación
az version
```

### **2. Bicep CLI**
```bash
# Instalar Bicep (viene con Azure CLI 2.20.0+)
az bicep install

# Verificar instalación
az bicep version
```

### **3. Autenticación**
```bash
# Iniciar sesión en Azure
az login

# Verificar suscripción
az account show

# Listar suscripciones (si tienes varias)
az account list --output table
```

## 🚀 **Despliegue Paso a Paso**

### **Opción 1: Script Automatizado (Recomendado)**

```powershell
# Ejecutar script PowerShell
.\scripts\deployment\deploy_bicep.ps1

# Con parámetros personalizados
.\scripts\deployment\deploy_bicep.ps1 -ResourceGroupName "mi-grupo-recursos" -Location "westeurope" -ProjectName "mi-proyecto"
```

### **Opción 2: Comandos Manuales**

```bash
# 1. Crear Resource Group
az group create --name "vea-resource-group" --location "eastus"

# 2. Desplegar template Bicep
az deployment group create \
  --resource-group "vea-resource-group" \
  --template-file "infra/main.bicep" \
  --parameters "infra/main.parameters.json"

# 3. Obtener outputs
az deployment group show \
  --resource-group "vea-resource-group" \
  --name "main" \
  --query properties.outputs
```

### **Opción 3: Portal Azure**

1. Ir a [Portal Azure](https://portal.azure.com)
2. Buscar "Deploy a custom template"
3. Seleccionar "Build your own template in the editor"
4. Copiar contenido de `infra/main.bicep`
5. Configurar parámetros
6. Revisar y crear

## 📊 **Parámetros del Template**

| Parámetro | Descripción | Valor por Defecto |
|-----------|-------------|-------------------|
| `projectName` | Nombre del proyecto | `vea` |
| `location` | Región de Azure | `eastus` |
| `vmSize` | Tamaño de la VM | `Standard_B2s` |
| `postgresAdminPassword` | Contraseña PostgreSQL | Requerido |

| `djangoSecretKey` | Django SECRET_KEY | Requerido |
| `vmAdminUsername` | Usuario VM | `azureuser` |

## 🔧 **Configuración Post-Despliegue**



### **2. Desplegar Código Django**

```bash
# Usando Azure CLI
az webapp deployment source config-local-git --name "vea-webapp-process-botconnect" --resource-group "vea-resource-group"

# O usando GitHub Actions
# Configurar secrets en tu repositorio GitHub
```

### **3. Ejecutar Migraciones**

```bash
# En App Service
az webapp ssh --name "vea-webapp-process-botconnect" --resource-group "vea-resource-group"

# Dentro del SSH
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic
```

## 📈 **Monitoreo y Logs**

### **App Service Logs:**
```bash
# Ver logs en tiempo real
az webapp log tail --name "vea-webapp-process-botconnect" --resource-group "vea-resource-group"

# Descargar logs
az webapp log download --name "vea-webapp-process-botconnect" --resource-group "vea-resource-group"
```



### **PostgreSQL Monitoring:**
```bash
# Conectar a base de datos
psql "host=[POSTGRES_SERVER].postgres.database.azure.com port=5432 dbname=vea_database user=vea_admin@[POSTGRES_SERVER]"
```

## 🔒 **Seguridad**

### **Firewall Rules:**
- ✅ SSH (puerto 22) - Acceso limitado
- ✅ HTTP/HTTPS (puertos 80/443) - App Service

### **Contraseñas Seguras:**
- ✅ Generadas automáticamente
- ✅ Almacenadas en Key Vault
- ✅ Rotación recomendada cada 90 días

### **Network Security:**
- ✅ Virtual Network aislada
- ✅ Network Security Groups
- ✅ Acceso privado a PostgreSQL

## 💰 **Costos Estimados**

| Recurso | SKU | Costo Mensual |
|---------|-----|---------------|
| App Service Plan | B1 | ~$13 |
| PostgreSQL | Standard_B1ms | ~$25 |
| Storage Account | Standard_LRS | ~$2-5 |

| Key Vault | Standard | ~$1 |
| **Total** | | **~$41-44** |

## 🚨 **Troubleshooting**

### **Error: "Template validation failed"**
```bash
# Validar template
az bicep build --file infra/main.bicep

# Verificar sintaxis
az bicep lint --file infra/main.bicep
```

### **Error: "Resource already exists"**
```bash
# Eliminar recursos existentes
az group delete --name "vea-resource-group" --yes

# O usar nombres únicos
az deployment group create --parameters projectName="vea-$(date +%s)"
```

### **Error: "Insufficient permissions"**
```bash
# Verificar permisos
az role assignment list --assignee [tu-email] --scope /subscriptions/[subscription-id]

# Solicitar permisos de administrador
```



## 📞 **Soporte**

### **Recursos Útiles:**
- [Azure Bicep Documentation](https://docs.microsoft.com/en-us/azure/azure-resource-manager/bicep/)
- [Azure CLI Documentation](https://docs.microsoft.com/en-us/cli/azure/)
- [Azure App Service Documentation](https://docs.microsoft.com/en-us/azure/app-service/)

### **Comandos de Verificación:**
```bash
# Verificar estado de recursos
az resource list --resource-group "vea-resource-group" --output table

# Verificar App Service
curl -I https://vea-webapp-process-botconnect.azurewebsites.net


```

## ✅ **Checklist de Verificación**

- [ ] Azure CLI instalado y autenticado
- [ ] Bicep CLI instalado
- [ ] Template validado sin errores
- [ ] Resource Group creado
- [ ] Todos los recursos desplegados

- [ ] App Service accesible
- [ ] Base de datos conecta
- [ ] Storage containers creados
- [ ] Variables de entorno configuradas
- [ ] Logs funcionando
- [ ] Monitoreo activo

**¡Tu infraestructura está lista para producción!** 🎉 