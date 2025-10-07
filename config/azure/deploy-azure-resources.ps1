# VEA Connect - Script de Despliegue de Recursos de Azure
# Este script crea los recursos necesarios para VEA Connect

param(
    [Parameter(Mandatory=$true)]
    [string]$ResourceGroupName,
    
    [Parameter(Mandatory=$true)]
    [string]$Location = "East US",
    
    [Parameter(Mandatory=$true)]
    [string]$SearchServiceName,
    
    [Parameter(Mandatory=$true)]
    [string]$StorageAccountName,
    
    [Parameter(Mandatory=$true)]
    [string]$CognitiveServicesName,
    
    [Parameter(Mandatory=$true)]
    [string]$ContainerName = "admin-documentos"
)

Write-Host "VEA Connect - Desplegando recursos de Azure..." -ForegroundColor Green

# 1. Crear grupo de recursos
Write-Host "Creando grupo de recursos: $ResourceGroupName" -ForegroundColor Yellow
az group create --name $ResourceGroupName --location $Location

# 2. Crear Azure AI Search
Write-Host "Creando Azure AI Search: $SearchServiceName" -ForegroundColor Yellow
az search service create --name $SearchServiceName --resource-group $ResourceGroupName --sku standard --location $Location

# 3. Crear Azure Storage Account
Write-Host "Creando Azure Storage Account: $StorageAccountName" -ForegroundColor Yellow
az storage account create --name $StorageAccountName --resource-group $ResourceGroupName --location $Location --sku Standard_LRS

# 4. Crear contenedor de blob
Write-Host "Creando contenedor de blob: $ContainerName" -ForegroundColor Yellow
az storage container create --name $ContainerName --account-name $StorageAccountName

# 5. Crear Azure Cognitive Services
Write-Host "Creando Azure Cognitive Services: $CognitiveServicesName" -ForegroundColor Yellow
az cognitiveservices account create --name $CognitiveServicesName --resource-group $ResourceGroupName --location $Location --kind CognitiveServices --sku S0

# 6. Obtener claves y endpoints
Write-Host "Obteniendo claves y endpoints..." -ForegroundColor Yellow

# Obtener clave de Azure AI Search
$SearchKey = az search admin-key show --resource-group $ResourceGroupName --service-name $SearchServiceName --query "primaryKey" -o tsv

# Obtener cadena de conexión de Storage
$StorageConnectionString = az storage account show-connection-string --name $StorageAccountName --resource-group $ResourceGroupName --query "connectionString" -o tsv

# Obtener clave de Cognitive Services
$CognitiveKey = az cognitiveservices account keys list --name $CognitiveServicesName --resource-group $ResourceGroupName --query "key1" -o tsv

# 7. Crear archivo de configuración
Write-Host "Creando archivo de configuración..." -ForegroundColor Yellow

$ConfigContent = @"
# VEA Connect - Configuración de Azure
# Generado automáticamente el $(Get-Date)

# Azure AI Search
SEARCH_SERVICE_NAME=$SearchServiceName
SEARCH_SERVICE_ENDPOINT=https://$SearchServiceName.search.windows.net
SEARCH_SERVICE_KEY=$SearchKey
SEARCH_INDEX_NAME=vea-connect-index

# Azure Storage
STORAGE_ACCOUNT_NAME=$StorageAccountName
STORAGE_CONTAINER_NAME=$ContainerName
STORAGE_CONNECTION_STRING=$StorageConnectionString

# Azure Cognitive Services
COGNITIVE_SERVICES_KEY=$CognitiveKey
COGNITIVE_SERVICES_ENDPOINT=https://$CognitiveServicesName.cognitiveservices.azure.com/

# Aplicación
DEBUG=False
PORT=8000
FRONTEND_URL=http://localhost:3000
"@

$ConfigContent | Out-File -FilePath "..\env_example.txt" -Encoding UTF8

Write-Host "Configuración completada!" -ForegroundColor Green
Write-Host "Archivo de configuración creado: env_example.txt" -ForegroundColor Green
Write-Host ""
Write-Host "Próximos pasos:" -ForegroundColor Cyan
Write-Host "1. Copia env_example.txt a .env en la carpeta backend" -ForegroundColor White
Write-Host "2. Ejecuta el script de configuración de Azure AI Search" -ForegroundColor White
Write-Host "3. Sube documentos al contenedor de blob storage" -ForegroundColor White
Write-Host "4. Ejecuta el indexer para procesar los documentos" -ForegroundColor White




