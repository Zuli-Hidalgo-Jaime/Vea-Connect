# ===========================================
# DEPLOY AZURE FUNCTIONS TO AZURE - SIMPLE
# ===========================================

param(
    [string]$ResourceGroup = "rg-vea-connect-dev",
    [string]$FunctionAppName = "vea-functions-apis"
)

Write-Host "Iniciando deployment de Azure Functions..." -ForegroundColor Green
Write-Host "Resource Group: $ResourceGroup" -ForegroundColor Yellow
Write-Host "Function App: $FunctionAppName" -ForegroundColor Yellow

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

# Verificar que Azure CLI está instalado
Write-Host "Verificando Azure CLI..." -ForegroundColor Blue
try {
    $azVersion = az version --output json | ConvertFrom-Json
    Write-Host "Azure CLI encontrado: $($azVersion.'azure-cli')" -ForegroundColor Green
} catch {
    Write-Host "Error: Azure CLI no está instalado o no está en PATH" -ForegroundColor Red
    exit 1
}

# Verificar login en Azure
Write-Host "Verificando login en Azure..." -ForegroundColor Blue
try {
    $account = az account show --output json | ConvertFrom-Json
    Write-Host "Logged in como: $($account.user.name)" -ForegroundColor Green
    Write-Host "Subscription: $($account.name)" -ForegroundColor Yellow
} catch {
    Write-Host "Error: No estás logueado en Azure. Ejecuta 'az login'" -ForegroundColor Red
    exit 1
}

# Verificar que el Function App existe
Write-Host "Verificando Function App..." -ForegroundColor Blue
try {
    $functionApp = az functionapp show --name $FunctionAppName --resource-group $ResourceGroup --output json | ConvertFrom-Json
    Write-Host "Function App encontrado: $($functionApp.name)" -ForegroundColor Green
    Write-Host "Estado: $($functionApp.state)" -ForegroundColor Yellow
} catch {
    Write-Host "Error: Function App '$FunctionAppName' no encontrado en Resource Group '$ResourceGroup'" -ForegroundColor Red
    exit 1
}

# Paquetizar funciones usando func pack
Write-Host "Paquetizando funciones..." -ForegroundColor Blue
try {
    func pack --python
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Paquete creado exitosamente" -ForegroundColor Green
    } else {
        Write-Host "Error al crear el paquete con func pack" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "Error durante la paquetización: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Verificar que el paquete se creó
if (Test-Path "functions.zip") {
    $zipSize = (Get-Item "functions.zip").Length / 1MB
    Write-Host "Package created: functions.zip ($([math]::Round($zipSize, 2)) MB)" -ForegroundColor Green
} elseif (Test-Path "functions-deploy.zip") {
    $zipSize = (Get-Item "functions-deploy.zip").Length / 1MB
    Write-Host "Package created: functions-deploy.zip ($([math]::Round($zipSize, 2)) MB)" -ForegroundColor Green
} else {
    Write-Host "Error: Could not create package" -ForegroundColor Red
    exit 1
}

# Deploy to Azure
Write-Host "Deploying to Azure..." -ForegroundColor Blue
try {
    $zipFile = if (Test-Path "functions.zip") { "functions.zip" } else { "functions-deploy.zip" }
    az functionapp deployment source config-zip `
        --resource-group $ResourceGroup `
        --name $FunctionAppName `
        --src $zipFile `
        --output json | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Deployment successful!" -ForegroundColor Green
    } else {
        Write-Host "Deployment error" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "Error during deployment: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Check Function App status
Write-Host "Checking Function App status..." -ForegroundColor Blue
Start-Sleep -Seconds 10

try {
    $functionApp = az functionapp show --name $FunctionAppName --resource-group $ResourceGroup --output json | ConvertFrom-Json
    Write-Host "Function App status: $($functionApp.state)" -ForegroundColor Green
    
    # Get Function App URL
    $functionAppUrl = $functionApp.defaultHostName
    Write-Host "Function App URL: https://$functionAppUrl" -ForegroundColor Cyan
    
    # List functions
    Write-Host "Deployed functions:" -ForegroundColor Blue
    $functions = az functionapp function list --name $FunctionAppName --resource-group $ResourceGroup --output json | ConvertFrom-Json
    foreach ($function in $functions) {
        Write-Host "   - $($function.name)" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "Could not verify final status" -ForegroundColor Yellow
}

# Clean temporary file
Write-Host "Cleaning temporary file..." -ForegroundColor Blue
if (Test-Path "functions-deploy.zip") {
    Remove-Item "functions-deploy.zip" -Force
    Write-Host "Temporary file removed" -ForegroundColor Green
}

Write-Host "Deployment completed successfully!" -ForegroundColor Green
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "   1. Verify functions are running" -ForegroundColor White
Write-Host "   2. Configure WhatsApp webhook in Azure Portal" -ForegroundColor White
Write-Host "   3. Test WhatsApp bot" -ForegroundColor White
