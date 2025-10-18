# Script para desplegar las funciones faltantes de Azure
# Ejecutar desde el directorio functions/

Write-Host "=== DESPLEGANDO FUNCIONES FALTANTES ===" -ForegroundColor Green

# Verificar que estamos en el directorio correcto
if (-not (Test-Path "local.settings.json")) {
    Write-Host "❌ Error: No se encontró local.settings.json. Ejecuta desde el directorio functions/" -ForegroundColor Red
    exit 1
}

# Cargar configuración
$localSettings = Get-Content "local.settings.json" | ConvertFrom-Json
$functionAppUrl = $localSettings.Values.FUNCTION_APP_URL

Write-Host "Function App URL: $functionAppUrl" -ForegroundColor Yellow

# Verificar que las funciones existan localmente
$requiredFunctions = @(
    "whatsapp_event_grid_trigger",
    "create_embedding", 
    "search_similar",
    "get_stats",
    "embeddings_health_check",
    "test_sdk_function"
)

Write-Host "`nVerificando funciones locales..." -ForegroundColor Cyan

foreach ($func in $requiredFunctions) {
    if (Test-Path $func) {
        Write-Host "✅ $func existe localmente" -ForegroundColor Green
    } else {
        Write-Host "❌ $func NO existe localmente" -ForegroundColor Red
    }
}

# Verificar si Azure Functions Core Tools está instalado
try {
    $funcVersion = func --version
    Write-Host "`n✅ Azure Functions Core Tools instalado: $funcVersion" -ForegroundColor Green
} catch {
    Write-Host "`n❌ Azure Functions Core Tools NO está instalado" -ForegroundColor Red
    Write-Host "Instala con: npm install -g azure-functions-core-tools@4 --unsafe-perm true" -ForegroundColor Yellow
    exit 1
}

# Verificar login de Azure
try {
    $account = az account show 2>$null
    if ($account) {
        Write-Host "`n✅ Logged in to Azure" -ForegroundColor Green
    } else {
        Write-Host "`n⚠️ No logged in to Azure. Ejecutando az login..." -ForegroundColor Yellow
        az login
    }
} catch {
    Write-Host "`n❌ Azure CLI no está instalado o no funciona" -ForegroundColor Red
    Write-Host "Instala Azure CLI desde: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli" -ForegroundColor Yellow
    exit 1
}

# Desplegar funciones
Write-Host "`n=== DESPLEGANDO FUNCIONES ===" -ForegroundColor Green

try {
    Write-Host "Desplegando todas las funciones..." -ForegroundColor Cyan
    func azure functionapp publish "vea-functions-apis" --python
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n✅ Despliegue completado exitosamente!" -ForegroundColor Green
    } else {
        Write-Host "`n❌ Error en el despliegue" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "`n❌ Error durante el despliegue: $_" -ForegroundColor Red
    exit 1
}

# Verificar despliegue
Write-Host "`n=== VERIFICANDO DESPLIEGUE ===" -ForegroundColor Green

Start-Sleep -Seconds 10  # Esperar a que el despliegue se complete

foreach ($func in $requiredFunctions) {
    try {
        $url = "$functionAppUrl/api/$func"
        $response = Invoke-WebRequest -Uri $url -Method GET -TimeoutSec 10 -ErrorAction Stop
        
        if ($response.StatusCode -eq 200 -or $response.StatusCode -eq 405) {
            Write-Host "✅ $func está funcionando (Status: $($response.StatusCode))" -ForegroundColor Green
        } else {
            Write-Host "⚠️ $func responde con status inesperado: $($response.StatusCode)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "❌ $func NO está funcionando: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`n=== DESPLIEGUE COMPLETADO ===" -ForegroundColor Green
Write-Host "Ahora verifica los logs en el portal de Azure:" -ForegroundColor Yellow
Write-Host "1. Ve a tu Function App en Azure Portal" -ForegroundColor White
Write-Host "2. Ve a 'Functions' y verifica que todas estén listadas" -ForegroundColor White
Write-Host "3. Ve a 'Monitor' en cada función para ver los logs" -ForegroundColor White
Write-Host "4. Ve a Application Insights para logs detallados" -ForegroundColor White
