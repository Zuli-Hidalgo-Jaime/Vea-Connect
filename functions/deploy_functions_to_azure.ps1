# ===========================================
# DEPLOY AZURE FUNCTIONS TO AZURE
# ===========================================
# Script para paquetizar y desplegar funciones a Azure

param(
    [string]$ResourceGroup = "rg-vea-connect-dev",
    [string]$FunctionAppName = "vea-functions-apis-eme0byhtbbgqgwhd",
    [string]$Location = "Central US"
)

Write-Host "Iniciando deployment de Azure Functions..." -ForegroundColor Green
Write-Host "Resource Group: $ResourceGroup" -ForegroundColor Yellow
Write-Host "Function App: $FunctionAppName" -ForegroundColor Yellow
Write-Host "Location: $Location" -ForegroundColor Yellow

# Verificar que estamos en el directorio correcto
if (-not (Test-Path "host.json")) {
    Write-Host "Error: No se encontró host.json. Ejecuta este script desde el directorio functions/" -ForegroundColor Red
    exit 1
}

# Limpiar archivos anteriores
Write-Host "Limpiando archivos anteriores..." -ForegroundColor Blue
if (Test-Path "functions-deploy.zip") {
    Remove-Item "functions-deploy.zip" -Force
    Write-Host "Archivo functions-deploy.zip eliminado" -ForegroundColor Green
}

# Crear archivo .funcignore si no existe
if (-not (Test-Path ".funcignore")) {
    Write-Host "Creando .funcignore..." -ForegroundColor Blue
    @"
.git*
.venv
.vscode
local.settings.json
test_*.py
__pycache__
*.pyc
.pytest_cache
.coverage
htmlcov
.env
.azure
venv*
.egg-info
docs/
tests/
scripts/
*.log
"@ | Out-File -FilePath ".funcignore" -Encoding UTF8
}

# Verificar que Azure CLI está instalado
Write-Host "Verificando Azure CLI..." -ForegroundColor Blue
try {
    $azVersion = az version --output json | ConvertFrom-Json
    Write-Host "✅ Azure CLI encontrado: $($azVersion.'azure-cli')" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: Azure CLI no está instalado o no está en PATH" -ForegroundColor Red
    exit 1
}

# Verificar login en Azure
Write-Host "🔐 Verificando login en Azure..." -ForegroundColor Blue
try {
    $account = az account show --output json | ConvertFrom-Json
    Write-Host "✅ Logged in como: $($account.user.name)" -ForegroundColor Green
    Write-Host "   Subscription: $($account.name)" -ForegroundColor Yellow
} catch {
    Write-Host "❌ Error: No estás logueado en Azure. Ejecuta 'az login'" -ForegroundColor Red
    exit 1
}

# Verificar que el Function App existe
Write-Host "🔍 Verificando Function App..." -ForegroundColor Blue
try {
    $functionApp = az functionapp show --name $FunctionAppName --resource-group $ResourceGroup --output json | ConvertFrom-Json
    Write-Host "✅ Function App encontrado: $($functionApp.name)" -ForegroundColor Green
    Write-Host "   Estado: $($functionApp.state)" -ForegroundColor Yellow
} catch {
    Write-Host "❌ Error: Function App '$FunctionAppName' no encontrado en Resource Group '$ResourceGroup'" -ForegroundColor Red
    Write-Host "   Verifica el nombre y resource group" -ForegroundColor Yellow
    exit 1
}

# Paquetizar funciones
Write-Host "📦 Paquetizando funciones..." -ForegroundColor Blue
try {
    # Usar func pack para crear el paquete
    func pack --python
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Paquete creado exitosamente" -ForegroundColor Green
    } else {
        Write-Host "❌ Error al crear el paquete con func pack" -ForegroundColor Red
        Write-Host "🔄 Intentando método alternativo..." -ForegroundColor Yellow
        
        # Método alternativo: crear ZIP manualmente
        $excludeFiles = @(
            "*.git*",
            "*.venv*",
            "*.vscode*",
            "local.settings.json",
            "test_*.py",
            "__pycache__",
            "*.pyc",
            ".pytest_cache",
            ".coverage",
            "htmlcov",
            ".env",
            ".azure",
            "venv*",
            ".egg-info",
            "docs",
            "tests",
            "scripts",
            "*.log"
        )
        
        $excludeParams = $excludeFiles | ForEach-Object { "--exclude", $_ }
        
        # Crear ZIP con 7zip o PowerShell
        if (Get-Command "7z" -ErrorAction SilentlyContinue) {
            $excludeArgs = $excludeFiles | ForEach-Object { "-x!$_" }
            7z a -tzip functions-deploy.zip . $excludeArgs
        } else {
            # PowerShell nativo
            $files = Get-ChildItem -Path . -Recurse -File | Where-Object {
                $exclude = $false
                foreach ($pattern in $excludeFiles) {
                    if ($_.FullName -like $pattern -or $_.Name -like $pattern) {
                        $exclude = $true
                        break
                    }
                }
                -not $exclude
            }
            
            Compress-Archive -Path $files.FullName -DestinationPath "functions-deploy.zip" -Force
        }
        
        if (Test-Path "functions-deploy.zip") {
            Write-Host "✅ Paquete creado con método alternativo" -ForegroundColor Green
        } else {
            Write-Host "❌ Error al crear el paquete" -ForegroundColor Red
            exit 1
        }
    }
} catch {
    Write-Host "❌ Error durante la paquetización: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Verificar que el paquete se creó
if (-not (Test-Path "functions-deploy.zip")) {
    Write-Host "❌ Error: No se pudo crear el paquete functions-deploy.zip" -ForegroundColor Red
    exit 1
}

$zipSize = (Get-Item "functions-deploy.zip").Length / 1MB
Write-Host "📦 Paquete creado: functions-deploy.zip ($([math]::Round($zipSize, 2)) MB)" -ForegroundColor Green

# Desplegar a Azure
Write-Host "🚀 Desplegando a Azure..." -ForegroundColor Blue
try {
    az functionapp deployment source config-zip `
        --resource-group $ResourceGroup `
        --name $FunctionAppName `
        --src functions-deploy.zip `
        --output json | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Deployment exitoso!" -ForegroundColor Green
    } else {
        Write-Host "❌ Error en el deployment" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Error durante el deployment: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Verificar el estado del Function App
Write-Host "🔍 Verificando estado del Function App..." -ForegroundColor Blue
Start-Sleep -Seconds 10

try {
    $functionApp = az functionapp show --name $FunctionAppName --resource-group $ResourceGroup --output json | ConvertFrom-Json
    Write-Host "✅ Function App estado: $($functionApp.state)" -ForegroundColor Green
    
    # Obtener URL del Function App
    $functionAppUrl = $functionApp.defaultHostName
    Write-Host "🌐 URL del Function App: https://$functionAppUrl" -ForegroundColor Cyan
    
    # Listar funciones
    Write-Host "📋 Funciones desplegadas:" -ForegroundColor Blue
    $functions = az functionapp function list --name $FunctionAppName --resource-group $ResourceGroup --output json | ConvertFrom-Json
    foreach ($function in $functions) {
        Write-Host "   - $($function.name)" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "⚠️  No se pudo verificar el estado final" -ForegroundColor Yellow
}

# Limpiar archivo temporal
Write-Host "🧹 Limpiando archivo temporal..." -ForegroundColor Blue
if (Test-Path "functions-deploy.zip") {
    Remove-Item "functions-deploy.zip" -Force
    Write-Host "✅ Archivo temporal eliminado" -ForegroundColor Green
}

Write-Host "🎉 Deployment completado exitosamente!" -ForegroundColor Green
Write-Host "📝 Próximos pasos:" -ForegroundColor Cyan
Write-Host "   1. Verificar que las funciones estén ejecutándose" -ForegroundColor White
Write-Host "   2. Configurar webhook de WhatsApp en Azure Portal" -ForegroundColor White
Write-Host "   3. Probar el bot de WhatsApp" -ForegroundColor White
