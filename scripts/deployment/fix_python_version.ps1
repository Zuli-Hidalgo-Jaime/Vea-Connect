# Script para cambiar la versión de Python de la Web App a 3.10
# Ejecutar desde PowerShell con: .\fix_python_version.ps1

param(
    [string]$ResourceGroup = "rg-vea-connect-dev",
    [string]$WebAppName = "vea-connect"
)

Write-Host "=== CAMBIANDO VERSIÓN DE PYTHON A 3.10 ===" -ForegroundColor Green
Write-Host "Resource Group: $ResourceGroup" -ForegroundColor Yellow
Write-Host "Web App: $WebAppName" -ForegroundColor Yellow

# Verificar la configuración actual
Write-Host "`nVerificando configuración actual..." -ForegroundColor Cyan
$currentConfig = az webapp show `
    --resource-group $ResourceGroup `
    --name $WebAppName `
    --query "siteConfig.linuxFxVersion" `
    --output tsv

Write-Host "Configuración actual: $currentConfig" -ForegroundColor Yellow

# Cambiar a Python 3.10
Write-Host "`nCambiando a Python 3.10..." -ForegroundColor Cyan
az webapp config set `
    --resource-group $ResourceGroup `
    --name $WebAppName `
    --linux-fx-version "PYTHON|3.10"

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Configuración actualizada exitosamente" -ForegroundColor Green
} else {
    Write-Host "✗ Error al actualizar la configuración" -ForegroundColor Red
    exit 1
}

# Verificar la nueva configuración
Write-Host "`nVerificando nueva configuración..." -ForegroundColor Cyan
$newConfig = az webapp show `
    --resource-group $ResourceGroup `
    --name $WebAppName `
    --query "siteConfig.linuxFxVersion" `
    --output tsv

Write-Host "Nueva configuración: $newConfig" -ForegroundColor Green

# Reiniciar la Web App
Write-Host "`nReiniciando Web App..." -ForegroundColor Cyan
az webapp restart `
    --resource-group $ResourceGroup `
    --name $WebAppName

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Web App reiniciada exitosamente" -ForegroundColor Green
} else {
    Write-Host "✗ Error al reiniciar la Web App" -ForegroundColor Red
    exit 1
}

Write-Host "`n=== CONFIGURACIÓN COMPLETADA ===" -ForegroundColor Green
Write-Host "La Web App ahora usa Python 3.10" -ForegroundColor Green
Write-Host "Puedes proceder con el despliegue" -ForegroundColor Green 