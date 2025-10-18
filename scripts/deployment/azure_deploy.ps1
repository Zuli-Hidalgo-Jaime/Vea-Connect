# Script de despliegue para Azure App Service
param(
    [string]$ResourceGroupName = "rg-vea-connect-dev",
    [string]$AppServiceName = "veaconnect-webapp-prod",
    [string]$Location = "Central US"
)

Write-Host "🚀 Iniciando despliegue en Azure App Service..." -ForegroundColor Green

# Verificar que estamos en el directorio correcto
if (-not (Test-Path "manage.py")) {
    Write-Error "❌ No se encontró manage.py. Ejecuta este script desde la raíz del proyecto."
    exit 1
}

# Verificar que startup.sh existe y tiene permisos
if (Test-Path "startup.sh") {
    Write-Host "✅ startup.sh encontrado" -ForegroundColor Green
} else {
    Write-Error "❌ startup.sh no encontrado"
    exit 1
}

# Configurar variables de entorno en Azure App Service
Write-Host "🔧 Configurando variables de entorno..." -ForegroundColor Yellow

$envVars = @{
    "SCM_DO_BUILD_DURING_DEPLOYMENT" = "true"
    "WEBSITES_ENABLE_APP_SERVICE_STORAGE" = "true"
    "PYTHON_VERSION" = "3.10"
    "DJANGO_SETTINGS_MODULE" = "config.settings.production"
    "PYTHONPATH" = "/home/site/wwwroot"
}

foreach ($key in $envVars.Keys) {
    az webapp config appsettings set --resource-group $ResourceGroupName --name $AppServiceName --settings "$key=$($envVars[$key])"
    Write-Host "  ✅ $key configurado" -ForegroundColor Green
}

# Configurar startup command
Write-Host "🔧 Configurando comando de inicio..." -ForegroundColor Yellow
az webapp config set --resource-group $ResourceGroupName --name $AppServiceName --startup-file "startup.sh"

# Configurar Python runtime
Write-Host "🔧 Configurando runtime de Python..." -ForegroundColor Yellow
az webapp config set --resource-group $ResourceGroupName --name $AppServiceName --linux-fx-version "PYTHON|3.10"

# Desplegar código
Write-Host "📦 Desplegando código..." -ForegroundColor Yellow
az webapp deployment source config-zip --resource-group $ResourceGroupName --name $AppServiceName --src "deploy.zip"

Write-Host "✅ Despliegue completado!" -ForegroundColor Green
Write-Host "🌐 URL de la aplicación: https://$AppServiceName.azurewebsites.net" -ForegroundColor Cyan 