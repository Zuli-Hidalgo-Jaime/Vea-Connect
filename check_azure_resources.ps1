# Script para verificar recursos de Azure
# Este script verifica la conexion a Azure y lista los recursos disponibles

Write-Host "=== VERIFICACION DE RECURSOS AZURE ===" -ForegroundColor Cyan

# Verificar si Azure CLI esta instalado
Write-Host "1. Verificando Azure CLI..." -ForegroundColor Yellow
try {
    $azVersion = az --version 2>$null
    if ($azVersion) {
        Write-Host "OK: Azure CLI esta instalado" -ForegroundColor Green
    } else {
        Write-Host "ERROR: Azure CLI no esta instalado" -ForegroundColor Red
        Write-Host "Instalando Azure CLI..." -ForegroundColor Yellow
        
        # Intentar instalar Azure CLI
        try {
            winget install Microsoft.AzureCLI
            Write-Host "OK: Azure CLI instalado. Reinicia la terminal y ejecuta este script nuevamente." -ForegroundColor Green
        } catch {
            Write-Host "ERROR: No se pudo instalar Azure CLI automaticamente" -ForegroundColor Red
            Write-Host "Instala manualmente desde: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli" -ForegroundColor Yellow
        }
        exit 1
    }
} catch {
    Write-Host "ERROR: Azure CLI no esta disponible" -ForegroundColor Red
    exit 1
}

# Verificar si el usuario esta logueado
Write-Host "2. Verificando autenticacion..." -ForegroundColor Yellow
try {
    $account = az account show 2>$null
    if ($account) {
        Write-Host "OK: Usuario autenticado en Azure" -ForegroundColor Green
        $accountObj = $account | ConvertFrom-Json
        Write-Host "   - Subscription: $($accountObj.name)" -ForegroundColor White
        Write-Host "   - Tenant: $($accountObj.tenantId)" -ForegroundColor White
    } else {
        Write-Host "ERROR: Usuario no autenticado" -ForegroundColor Red
        Write-Host "Ejecutando login..." -ForegroundColor Yellow
        az login
    }
} catch {
    Write-Host "ERROR: No se pudo verificar la autenticacion" -ForegroundColor Red
    exit 1
}

# Listar grupos de recursos
Write-Host "3. Listando grupos de recursos..." -ForegroundColor Yellow
try {
    $resourceGroups = az group list --output table 2>$null
    if ($resourceGroups) {
        Write-Host "Grupos de recursos disponibles:" -ForegroundColor Green
        Write-Host $resourceGroups -ForegroundColor White
    } else {
        Write-Host "No se encontraron grupos de recursos" -ForegroundColor Yellow
    }
} catch {
    Write-Host "ERROR: No se pudieron listar los grupos de recursos" -ForegroundColor Red
}

# Buscar la Web App especifica
Write-Host "4. Verificando Web App..." -ForegroundColor Yellow
try {
    $webApp = az webapp show --name veaconnect-webapp-prod --resource-group rg-vea-connect-dev 2>$null
    if ($webApp) {
        Write-Host "OK: Web App encontrada" -ForegroundColor Green
        $webAppObj = $webApp | ConvertFrom-Json
        Write-Host "   - Nombre: $($webAppObj.name)" -ForegroundColor White
        Write-Host "   - Estado: $($webAppObj.state)" -ForegroundColor White
        Write-Host "   - URL: $($webAppObj.defaultHostName)" -ForegroundColor White
        Write-Host "   - Plan: $($webAppObj.serverFarmId)" -ForegroundColor White
    } else {
        Write-Host "ERROR: Web App no encontrada" -ForegroundColor Red
        Write-Host "Verificando si existe con otro nombre..." -ForegroundColor Yellow
        
        # Listar todas las Web Apps
        $webApps = az webapp list --output table 2>$null
        if ($webApps) {
            Write-Host "Web Apps disponibles:" -ForegroundColor Green
            Write-Host $webApps -ForegroundColor White
        }
    }
} catch {
    Write-Host "ERROR: No se pudo verificar la Web App" -ForegroundColor Red
}

# Verificar configuracion de la Web App
Write-Host "5. Verificando configuracion de la Web App..." -ForegroundColor Yellow
try {
    $config = az webapp config show --name veaconnect-webapp-prod --resource-group rg-vea-connect-dev 2>$null
    if ($config) {
        Write-Host "OK: Configuracion obtenida" -ForegroundColor Green
        $configObj = $config | ConvertFrom-Json
        
        Write-Host "Configuracion actual:" -ForegroundColor Cyan
        Write-Host "   - Python version: $($configObj.pythonVersion)" -ForegroundColor White
        Write-Host "   - Puerto: $($configObj.appSettings | Where-Object {$_.name -eq 'WEBSITES_PORT'} | Select-Object -ExpandProperty value)" -ForegroundColor White
        Write-Host "   - Startup command: $($configObj.appCommandLine)" -ForegroundColor White
    }
} catch {
    Write-Host "ERROR: No se pudo obtener la configuracion" -ForegroundColor Red
}

# Verificar variables de entorno
Write-Host "6. Verificando variables de entorno..." -ForegroundColor Yellow
try {
    $appSettings = az webapp config appsettings list --name veaconnect-webapp-prod --resource-group rg-vea-connect-dev 2>$null
    if ($appSettings) {
        Write-Host "OK: Variables de entorno obtenidas" -ForegroundColor Green
        $settingsObj = $appSettings | ConvertFrom-Json
        
        Write-Host "Variables de entorno configuradas:" -ForegroundColor Cyan
        foreach ($setting in $settingsObj) {
            Write-Host "   - $($setting.name): $($setting.value)" -ForegroundColor White
        }
    }
} catch {
    Write-Host "ERROR: No se pudieron obtener las variables de entorno" -ForegroundColor Red
}

Write-Host "Verificacion completada!" -ForegroundColor Green 