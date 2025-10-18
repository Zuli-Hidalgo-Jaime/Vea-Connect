# Script de despliegue con verificación de Python 3.10
# Ejecutar desde PowerShell con: .\deploy_with_python_check.ps1

param(
    [string]$ResourceGroup = "rg-vea-connect-dev",
    [string]$WebAppName = "vea-connect",
    [switch]$SkipPythonCheck = $false
)

Write-Host "=== DESPLIEGUE CON VERIFICACIÓN DE PYTHON 3.10 ===" -ForegroundColor Green
Write-Host "Resource Group: $ResourceGroup" -ForegroundColor Yellow
Write-Host "Web App: $WebAppName" -ForegroundColor Yellow

# Verificar que estamos en el directorio correcto
if (-not (Test-Path "manage.py")) {
    Write-Host "✗ Error: No se encontró manage.py. Ejecuta este script desde el directorio raíz del proyecto." -ForegroundColor Red
    exit 1
}

# Verificar configuración de Python si no se omite
if (-not $SkipPythonCheck) {
    Write-Host "`n1. Verificando configuración de Python..." -ForegroundColor Cyan
    
    $currentConfig = az webapp show `
        --resource-group $ResourceGroup `
        --name $WebAppName `
        --query "siteConfig.linuxFxVersion" `
        --output tsv
    
    Write-Host "Configuración actual: $currentConfig" -ForegroundColor Yellow
    
    if ($currentConfig -ne "PYTHON|3.10") {
        Write-Host "⚠ Web App no está configurada con Python 3.10" -ForegroundColor Yellow
        Write-Host "Cambiando a Python 3.10..." -ForegroundColor Cyan
        
        az webapp config set `
            --resource-group $ResourceGroup `
            --name $WebAppName `
            --linux-fx-version "PYTHON|3.10"
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Configuración actualizada a Python 3.10" -ForegroundColor Green
            
            Write-Host "Reiniciando Web App..." -ForegroundColor Cyan
            az webapp restart `
                --resource-group $ResourceGroup `
                --name $WebAppName
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✓ Web App reiniciada" -ForegroundColor Green
                Write-Host "Esperando 30 segundos para que los cambios se apliquen..." -ForegroundColor Yellow
                Start-Sleep -Seconds 30
            } else {
                Write-Host "✗ Error al reiniciar la Web App" -ForegroundColor Red
                exit 1
            }
        } else {
            Write-Host "✗ Error al actualizar la configuración" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "✓ Web App ya está configurada con Python 3.10" -ForegroundColor Green
    }
}

# Verificar que runtime.txt existe y es correcto
Write-Host "`n2. Verificando runtime.txt..." -ForegroundColor Cyan
if (Test-Path "runtime.txt") {
    $runtimeContent = Get-Content "runtime.txt" -Raw
    if ($runtimeContent -match "python-3\.10") {
        Write-Host "✓ runtime.txt especifica Python 3.10 correctamente" -ForegroundColor Green
    } else {
        Write-Host "✗ runtime.txt NO especifica Python 3.10" -ForegroundColor Red
        Write-Host "Actualizando runtime.txt..." -ForegroundColor Yellow
        Set-Content "runtime.txt" "python-3.10.12`n# REQUERIDO: Python 3.10+ para compatibilidad con todas las dependencias"
        Write-Host "✓ runtime.txt actualizado" -ForegroundColor Green
    }
} else {
    Write-Host "✗ Archivo runtime.txt no encontrado. Creándolo..." -ForegroundColor Yellow
    Set-Content "runtime.txt" "python-3.10.12`n# REQUERIDO: Python 3.10+ para compatibilidad con todas las dependencias"
    Write-Host "✓ runtime.txt creado" -ForegroundColor Green
}

# Verificar que startup.sh existe y tiene permisos de ejecución
Write-Host "`n3. Verificando startup.sh..." -ForegroundColor Cyan
if (Test-Path "startup.sh") {
    Write-Host "✓ startup.sh encontrado" -ForegroundColor Green
} else {
    Write-Host "✗ startup.sh no encontrado" -ForegroundColor Red
    exit 1
}

# Verificar requirements.txt
Write-Host "`n4. Verificando requirements.txt..." -ForegroundColor Cyan
if (Test-Path "requirements.txt") {
    Write-Host "✓ requirements.txt encontrado" -ForegroundColor Green
    $requirementsContent = Get-Content "requirements.txt"
    Write-Host "Dependencias encontradas: $($requirementsContent.Count)" -ForegroundColor Yellow
} else {
    Write-Host "✗ requirements.txt no encontrado" -ForegroundColor Red
    exit 1
}

# Realizar commit de los cambios si es necesario
Write-Host "`n5. Verificando cambios en Git..." -ForegroundColor Cyan
$gitStatus = git status --porcelain
if ($gitStatus) {
    Write-Host "Cambios detectados:" -ForegroundColor Yellow
    $gitStatus | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
    
    $commitMessage = "fix: Actualizar configuración Python 3.10 para Azure App Service"
    Write-Host "Realizando commit: $commitMessage" -ForegroundColor Cyan
    
    git add .
    git commit -m $commitMessage
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Commit realizado exitosamente" -ForegroundColor Green
    } else {
        Write-Host "✗ Error al realizar commit" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "✓ No hay cambios pendientes" -ForegroundColor Green
}

# Push a GitHub para trigger del despliegue
Write-Host "`n6. Enviando cambios a GitHub..." -ForegroundColor Cyan
git push origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Cambios enviados a GitHub" -ForegroundColor Green
    Write-Host "El despliegue automático se iniciará en GitHub Actions" -ForegroundColor Green
} else {
    Write-Host "✗ Error al enviar cambios a GitHub" -ForegroundColor Red
    exit 1
}

Write-Host "`n=== DESPLIEGUE INICIADO ===" -ForegroundColor Green
Write-Host "1. Los cambios se han enviado a GitHub" -ForegroundColor Green
Write-Host "2. GitHub Actions iniciará el despliegue automáticamente" -ForegroundColor Green
Write-Host "3. Puedes monitorear el progreso en: https://github.com/[tu-usuario]/veaconnect-webapp-prod/actions" -ForegroundColor Green
Write-Host "4. Una vez completado, verifica la aplicación en: https://$WebAppName.azurewebsites.net" -ForegroundColor Green 