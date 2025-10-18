# Script para arreglar la configuración de contenedores en Azure App Service
# Ejecutar: .\fix_container_config.ps1

param(
    [string]$WebAppName = "vea-connect",
    [string]$ResourceGroup = "rg-vea-connect-dev",
    [string]$ACRName = "veaconnectacr"
)

Write-Host "🔧 ARREGLANDO CONFIGURACIÓN DE CONTENEDORES EN AZURE APP SERVICE" -ForegroundColor Green
Write-Host "Web App: $WebAppName" -ForegroundColor Yellow
Write-Host "Resource Group: $ResourceGroup" -ForegroundColor Yellow
Write-Host "ACR: $ACRName" -ForegroundColor Yellow
Write-Host ""

# Verificar si Azure CLI está disponible
try {
    $azVersion = az --version 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Azure CLI no está disponible"
    }
    Write-Host "✓ Azure CLI está disponible" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: Azure CLI no está disponible. Instala Azure CLI y ejecuta 'az login'" -ForegroundColor Red
    exit 1
}

# Paso 1: Forzar configuración para usar solo contenedores Docker
Write-Host "`n📋 PASO 1: Configurando Web App para usar solo contenedores Docker..." -ForegroundColor Cyan
az webapp config set `
    --name $WebAppName `
    --resource-group $ResourceGroup `
    --linux-fx-version DOCKER `
    --startup-file ""

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Configuración de Docker aplicada" -ForegroundColor Green
} else {
    Write-Host "❌ Error al aplicar configuración de Docker" -ForegroundColor Red
    exit 1
}

# Paso 2: Configurar imagen de contenedor
Write-Host "`n📋 PASO 2: Configurando imagen de contenedor..." -ForegroundColor Cyan

# Obtener credenciales de ACR
$acrUsername = az acr credential show --name $ACRName --query username -o tsv 2>$null
$acrPassword = az acr credential show --name $ACRName --query passwords[0].value -o tsv 2>$null

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error al obtener credenciales de ACR" -ForegroundColor Red
    exit 1
}

az webapp config container set `
    --name $WebAppName `
    --resource-group $ResourceGroup `
    --docker-custom-image-name "$ACRName.azurecr.io/$WebAppName`:prod" `
    --docker-registry-server-url "https://$ACRName.azurecr.io" `
    --docker-registry-server-user $acrUsername `
    --docker-registry-server-password $acrPassword

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Imagen de contenedor configurada" -ForegroundColor Green
} else {
    Write-Host "❌ Error al configurar imagen de contenedor" -ForegroundColor Red
    exit 1
}

# Paso 3: Configurar variables de entorno críticas
Write-Host "`n📋 PASO 3: Configurando variables de entorno..." -ForegroundColor Cyan

$appSettings = @(
    "WEBSITES_PORT=8000",
    "DJANGO_SETTINGS_MODULE=config.settings.production",
    "PYTHON_VERSION=3.10",
    "DEBUG=False",
    "ALLOWED_HOSTS=$WebAppName.azurewebsites.net,*.azurewebsites.net",
    "WEBSITES_ENABLE_APP_SERVICE_STORAGE=true"
)

# Agregar variables de entorno desde secrets (si están disponibles)
$secrets = @(
    "ACS_CONNECTION_STRING",
    "ACS_EVENT_GRID_TOPIC_ENDPOINT", 
    "ACS_EVENT_GRID_TOPIC_KEY",
    "ACS_PHONE_NUMBER",
    "ACS_WHATSAPP_API_KEY",
    "ACS_WHATSAPP_ENDPOINT",
    "AZURE_OPENAI_ENDPOINT",
    "AZURE_OPENAI_API_KEY",
    "AZURE_SEARCH_ENDPOINT",
    "AZURE_SEARCH_KEY",
    "AZURE_STORAGE_CONNECTION_STRING",
    "VISION_ENDPOINT",
    "VISION_KEY",
    "DATABASE_URL",
    "AZURE_POSTGRESQL_NAME",
    "AZURE_POSTGRESQL_USERNAME",
    "AZURE_POSTGRESQL_PASSWORD",
    "AZURE_POSTGRESQL_HOST",
    "DB_PORT",
    "SECRET_KEY",
    "AZURE_REDIS_CONNECTIONSTRING"
)

Write-Host "⚠️  NOTA: Las variables de entorno deben configurarse manualmente en Azure Portal" -ForegroundColor Yellow
Write-Host "   Variables críticas que necesitas configurar:" -ForegroundColor Yellow
foreach ($secret in $secrets) {
    Write-Host "   - $secret" -ForegroundColor White
}

# Configurar las variables básicas
$settingsString = $appSettings -join " "
az webapp config appsettings set `
    --name $WebAppName `
    --resource-group $ResourceGroup `
    --settings $settingsString

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Variables de entorno básicas configuradas" -ForegroundColor Green
} else {
    Write-Host "❌ Error al configurar variables de entorno" -ForegroundColor Red
}

# Paso 4: Reiniciar Web App
Write-Host "`n📋 PASO 4: Reiniciando Web App..." -ForegroundColor Cyan
az webapp restart --name $WebAppName --resource-group $ResourceGroup

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Web App reiniciada" -ForegroundColor Green
} else {
    Write-Host "❌ Error al reiniciar Web App" -ForegroundColor Red
}

# Paso 5: Verificar estado
Write-Host "`n📋 PASO 5: Verificando estado..." -ForegroundColor Cyan
Start-Sleep -Seconds 10

$webappUrl = "https://$WebAppName.azurewebsites.net"
Write-Host "URL del Web App: $webappUrl" -ForegroundColor Yellow

try {
    $response = Invoke-WebRequest -Uri "$webappUrl/health/" -TimeoutSec 30 -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host "✓ Web App responde correctamente" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Web App responde con código: $($response.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Web App no responde: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n✅ CONFIGURACIÓN COMPLETADA" -ForegroundColor Green
Write-Host "`n📋 PRÓXIMOS PASOS:" -ForegroundColor Cyan
Write-Host "1. Ve a Azure Portal > App Service > $WebAppName > Configuration" -ForegroundColor White
Write-Host "2. Configura las variables de entorno faltantes (especialmente las de PostgreSQL)" -ForegroundColor White
Write-Host "3. Verifica los logs en: Log stream" -ForegroundColor White
Write-Host "4. Si hay problemas, ejecuta: az webapp log tail --name $WebAppName --resource-group $ResourceGroup" -ForegroundColor White
