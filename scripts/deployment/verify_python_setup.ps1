# Script para verificar la configuración de Python 3.10 en la Web App
# Ejecutar desde PowerShell con: .\verify_python_setup.ps1

param(
    [string]$ResourceGroup = "rg-vea-connect-dev",
    [string]$WebAppName = "vea-connect"
)

Write-Host "=== VERIFICANDO CONFIGURACIÓN DE PYTHON 3.10 ===" -ForegroundColor Green
Write-Host "Resource Group: $ResourceGroup" -ForegroundColor Yellow
Write-Host "Web App: $WebAppName" -ForegroundColor Yellow

# Verificar la configuración actual
Write-Host "`n1. Verificando configuración de la Web App..." -ForegroundColor Cyan
$currentConfig = az webapp show `
    --resource-group $ResourceGroup `
    --name $WebAppName `
    --query "siteConfig.linuxFxVersion" `
    --output tsv

Write-Host "Configuración actual: $currentConfig" -ForegroundColor Yellow

if ($currentConfig -eq "PYTHON|3.10") {
    Write-Host "✓ Web App configurada correctamente con Python 3.10" -ForegroundColor Green
} else {
    Write-Host "✗ Web App NO está configurada con Python 3.10" -ForegroundColor Red
    Write-Host "Ejecuta: .\fix_python_version.ps1" -ForegroundColor Yellow
    exit 1
}

# Verificar el estado de la Web App
Write-Host "`n2. Verificando estado de la Web App..." -ForegroundColor Cyan
$webAppState = az webapp show `
    --resource-group $ResourceGroup `
    --name $WebAppName `
    --query "state" `
    --output tsv

Write-Host "Estado de la Web App: $webAppState" -ForegroundColor Yellow

if ($webAppState -eq "Running") {
    Write-Host "✓ Web App está ejecutándose" -ForegroundColor Green
} else {
    Write-Host "⚠ Web App no está ejecutándose. Estado: $webAppState" -ForegroundColor Yellow
}

# Verificar logs recientes
Write-Host "`n3. Verificando logs recientes..." -ForegroundColor Cyan
Write-Host "Obteniendo logs de la última hora..." -ForegroundColor Yellow

$logs = az webapp log tail `
    --resource-group $ResourceGroup `
    --name $WebAppName `
    --output tsv 2>$null

if ($logs) {
    Write-Host "✓ Logs disponibles" -ForegroundColor Green
    Write-Host "Últimas líneas de log:" -ForegroundColor Cyan
    $logs | Select-Object -Last 10 | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
} else {
    Write-Host "⚠ No se pudieron obtener logs recientes" -ForegroundColor Yellow
}

# Verificar configuración de variables de entorno
Write-Host "`n4. Verificando variables de entorno críticas..." -ForegroundColor Cyan
$appSettings = az webapp config appsettings list `
    --resource-group $ResourceGroup `
    --name $WebAppName `
    --output table

Write-Host "Variables de entorno configuradas:" -ForegroundColor Yellow
$appSettings | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }

# Verificar que runtime.txt existe y es correcto
Write-Host "`n5. Verificando archivo runtime.txt..." -ForegroundColor Cyan
if (Test-Path "runtime.txt") {
    $runtimeContent = Get-Content "runtime.txt" -Raw
    Write-Host "Contenido de runtime.txt:" -ForegroundColor Yellow
    Write-Host $runtimeContent -ForegroundColor Gray
    
    if ($runtimeContent -match "python-3\.10") {
        Write-Host "✓ runtime.txt especifica Python 3.10 correctamente" -ForegroundColor Green
    } else {
        Write-Host "✗ runtime.txt NO especifica Python 3.10" -ForegroundColor Red
    }
} else {
    Write-Host "✗ Archivo runtime.txt no encontrado" -ForegroundColor Red
}

Write-Host "`n=== VERIFICACIÓN COMPLETADA ===" -ForegroundColor Green
Write-Host "Si todos los checks pasaron, puedes proceder con el despliegue" -ForegroundColor Green 