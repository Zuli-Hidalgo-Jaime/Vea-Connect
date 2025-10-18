# Script de despliegue simple para Azure App Service
param(
    [string]$ResourceGroupName = "rg-vea-connect-dev",
    [string]$AppServiceName = "veaconnect-webapp-prod"
)

Write-Host "Iniciando despliegue en Azure App Service..." -ForegroundColor Green
Write-Host "Grupo de recursos: $ResourceGroupName" -ForegroundColor Cyan
Write-Host "App Service: $AppServiceName" -ForegroundColor Cyan

# Verificar que estamos en el directorio correcto
if (-not (Test-Path "manage.py")) {
    Write-Error "No se encontro manage.py. Ejecuta este script desde la raiz del proyecto."
    exit 1
}

# Verificar que startup.sh existe
if (Test-Path "startup.sh") {
    Write-Host "startup.sh encontrado" -ForegroundColor Green
} else {
    Write-Error "startup.sh no encontrado"
    exit 1
}

# Verificar conexion con Azure
Write-Host "Verificando conexion con Azure..." -ForegroundColor Yellow
try {
    $account = az account show --query "name" -o tsv 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Conectado a Azure: $account" -ForegroundColor Green
    } else {
        Write-Error "No se pudo conectar a Azure. Ejecuta 'az login' primero."
        exit 1
    }
} catch {
    Write-Error "Error de conexion con Azure: $_"
    exit 1
}

# Verificar que el App Service existe
Write-Host "Verificando App Service..." -ForegroundColor Yellow
try {
    $state = az webapp show --resource-group $ResourceGroupName --name $AppServiceName --query "state" -o tsv 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "App Service encontrado - Estado: $state" -ForegroundColor Green
    } else {
        Write-Error "App Service no encontrado o error de acceso"
        exit 1
    }
} catch {
    Write-Error "Error verificando App Service: $_"
    exit 1
}

# Configurar variables de entorno basicas
Write-Host "Configurando variables de entorno basicas..." -ForegroundColor Yellow

$basicSettings = @(
    "SCM_DO_BUILD_DURING_DEPLOYMENT=true",
    "WEBSITES_ENABLE_APP_SERVICE_STORAGE=true",
    "PYTHON_VERSION=3.9",
    "DJANGO_SETTINGS_MODULE=config.settings.production"
)

foreach ($setting in $basicSettings) {
    try {
        az webapp config appsettings set --resource-group $ResourceGroupName --name $AppServiceName --settings $setting 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  Configurado: $setting" -ForegroundColor Green
        } else {
            Write-Host "  Advertencia: $setting (puede que ya este configurado)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  Error configurando $setting" -ForegroundColor Yellow
    }
}

# Configurar startup command
Write-Host "Configurando comando de inicio..." -ForegroundColor Yellow
try {
    az webapp config set --resource-group $ResourceGroupName --name $AppServiceName --startup-file "startup.sh" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Comando de inicio configurado" -ForegroundColor Green
    } else {
        Write-Host "Advertencia: Error configurando comando de inicio (puede que ya este configurado)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "Error configurando comando de inicio" -ForegroundColor Yellow
}

# Crear archivo ZIP para despliegue
Write-Host "Creando archivo ZIP para despliegue..." -ForegroundColor Yellow
try {
    # Usar git archive si esta disponible, sino usar PowerShell
    if (Get-Command git -ErrorAction SilentlyContinue) {
        git archive -o deploy.zip HEAD
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Archivo ZIP creado con git archive" -ForegroundColor Green
        } else {
            Write-Host "Error con git archive, usando metodo alternativo" -ForegroundColor Yellow
            # Metodo alternativo con PowerShell
            Compress-Archive -Path * -DestinationPath deploy.zip -Force
        }
    } else {
        Write-Host "Git no disponible, usando PowerShell" -ForegroundColor Yellow
        Compress-Archive -Path * -DestinationPath deploy.zip -Force
    }
    
    if (Test-Path "deploy.zip") {
        Write-Host "Archivo deploy.zip creado" -ForegroundColor Green
    } else {
        Write-Error "No se pudo crear el archivo ZIP"
        exit 1
    }
} catch {
    Write-Error "Error creando archivo ZIP: $_"
    exit 1
}

# Desplegar codigo
Write-Host "Desplegando codigo..." -ForegroundColor Yellow
try {
    az webapp deployment source config-zip --resource-group $ResourceGroupName --name $AppServiceName --src deploy.zip 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Despliegue completado exitosamente!" -ForegroundColor Green
    } else {
        Write-Error "Error en el despliegue"
        exit 1
    }
} catch {
    Write-Error "Error durante el despliegue: $_"
    exit 1
}

# Limpiar archivo ZIP
if (Test-Path "deploy.zip") {
    Remove-Item "deploy.zip" -Force
    Write-Host "Archivo ZIP temporal eliminado" -ForegroundColor Green
}

Write-Host "Despliegue completado!" -ForegroundColor Green
Write-Host "URL de la aplicacion: https://$AppServiceName.azurewebsites.net" -ForegroundColor Cyan
Write-Host "Para ver los logs: az webapp log tail --resource-group $ResourceGroupName --name $AppServiceName" -ForegroundColor Yellow 