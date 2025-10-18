# Script para forzar el despliegue a Azure App Service
# Este script resuelve problemas de conflicto Git (error 409)

param(
    [string]$ResourceGroupName = "rg-vea-connect-dev",
    [string]$AppServiceName = "veaconnect-webapp-prod",
    [string]$SourcePath = "."
)

Write-Host "=== FORZANDO DESPLIEGUE A AZURE APP SERVICE ===" -ForegroundColor Green

# Verificar que Azure CLI esté instalado
if (!(Get-Command az -ErrorAction SilentlyContinue)) {
    Write-Error "Azure CLI no está instalado. Por favor instálalo desde https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
}

# Verificar login
Write-Host "Verificando login de Azure..." -ForegroundColor Yellow
$account = az account show 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "No hay sesión activa. Iniciando login..." -ForegroundColor Yellow
    az login
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Error al hacer login en Azure"
        exit 1
    }
}

# Verificar que el App Service existe
Write-Host "Verificando App Service..." -ForegroundColor Yellow
$appService = az webapp show --name $AppServiceName --resource-group $ResourceGroupName 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Error "App Service '$AppServiceName' no encontrado en el grupo de recursos '$ResourceGroupName'"
    exit 1
}

# Crear un ZIP temporal del código
Write-Host "Creando paquete de despliegue..." -ForegroundColor Yellow
$tempZip = "deployment-$(Get-Date -Format 'yyyyMMdd-HHmmss').zip"

# Excluir archivos innecesarios
$excludePatterns = @(
    "*.git*",
    "*.pyc",
    "__pycache__",
    "venv",
    "node_modules",
    ".vscode",
    "*.log",
    "*.tmp"
)

$excludeArgs = $excludePatterns | ForEach-Object { "--exclude", $_ }

# Crear el ZIP
Compress-Archive -Path "$SourcePath\*" -DestinationPath $tempZip -Force

if (!(Test-Path $tempZip)) {
    Write-Error "Error al crear el archivo ZIP de despliegue"
    exit 1
}

Write-Host "Paquete creado: $tempZip" -ForegroundColor Green

# Desplegar usando Azure CLI (comando actualizado)
Write-Host "Desplegando a Azure App Service..." -ForegroundColor Yellow
az webapp deploy `
    --resource-group $ResourceGroupName `
    --name $AppServiceName `
    --src-path $tempZip `
    --type zip

if ($LASTEXITCODE -eq 0) {
    Write-Host "Despliegue completado exitosamente!" -ForegroundColor Green
    Write-Host "URL: https://$AppServiceName.azurewebsites.net" -ForegroundColor Cyan
} else {
    Write-Error "Error en el despliegue"
}

# Limpiar archivo temporal
if (Test-Path $tempZip) {
    Remove-Item $tempZip -Force
    Write-Host "Archivo temporal eliminado: $tempZip" -ForegroundColor Gray
}

Write-Host "=== DESPLIEGUE COMPLETADO ===" -ForegroundColor Green 