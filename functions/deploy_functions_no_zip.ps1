# Script para desplegar Azure Functions sin compresión ZIP
# Esto evita problemas de dependencias faltantes

param(
    [string]$FunctionAppName = "vea-functions-apis",
    [string]$ResourceGroup = "vea-connect-rg",
    [string]$Location = "East US"
)

Write-Host "🚀 Iniciando despliegue de Azure Functions sin compresión..." -ForegroundColor Green

# Verificar que estamos en el directorio correcto
if (-not (Test-Path "host.json")) {
    Write-Error "❌ No se encontró host.json. Ejecuta este script desde el directorio functions/"
    exit 1
}

# Limpiar archivos temporales
Write-Host "🧹 Limpiando archivos temporales..." -ForegroundColor Yellow
if (Test-Path "*.zip") {
    Remove-Item "*.zip" -Force
    Write-Host "✅ Archivos ZIP eliminados" -ForegroundColor Green
}

# Verificar que las funciones están presentes
$functions = @(
    "whatsapp_event_grid_trigger",
    "health",
    "create_embedding", 
    "search_similar",
    "get_stats",
    "embeddings_health_check"
)

foreach ($func in $functions) {
    if (-not (Test-Path $func)) {
        Write-Warning "⚠️  Función $func no encontrada"
    } else {
        Write-Host "✅ Función $func encontrada" -ForegroundColor Green
    }
}

# Verificar requirements.txt
if (Test-Path "requirements.txt") {
    Write-Host "✅ requirements.txt encontrado" -ForegroundColor Green
    Write-Host "📋 Dependencias incluidas:" -ForegroundColor Cyan
    Get-Content "requirements.txt" | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }
} else {
    Write-Error "❌ requirements.txt no encontrado"
    exit 1
}

# Desplegar usando func azure functionapp publish sin compresión
Write-Host "📤 Desplegando funciones a Azure..." -ForegroundColor Yellow
Write-Host "🔧 Usando: func azure functionapp publish $FunctionAppName --build remote" -ForegroundColor Cyan

try {
    # Primero, intentar con build remote
    func azure functionapp publish $FunctionAppName --build remote
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Despliegue exitoso con build remote" -ForegroundColor Green
    } else {
        Write-Warning "⚠️  Build remote falló, intentando con build local..."
        
        # Si falla, intentar con build local
        func azure functionapp publish $FunctionAppName --build local
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Despliegue exitoso con build local" -ForegroundColor Green
        } else {
            Write-Error "❌ Despliegue falló"
            exit 1
        }
    }
} catch {
    Write-Error "❌ Error durante el despliegue: $($_.Exception.Message)"
    exit 1
}

# Verificar el estado del despliegue
Write-Host "🔍 Verificando estado del despliegue..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

try {
    $status = az functionapp show --name $FunctionAppName --resource-group $ResourceGroup --query "state" -o tsv
    Write-Host "📊 Estado de la Function App: $status" -ForegroundColor Cyan
    
    if ($status -eq "Running") {
        Write-Host "✅ Function App está ejecutándose correctamente" -ForegroundColor Green
    } else {
        Write-Warning "⚠️  Function App no está en estado Running: $status"
    }
} catch {
    Write-Warning "⚠️  No se pudo verificar el estado de la Function App"
}

# Mostrar URLs de las funciones
Write-Host "🌐 URLs de las funciones:" -ForegroundColor Cyan
$baseUrl = "https://$FunctionAppName.azurewebsites.net/api"

foreach ($func in $functions) {
    if (Test-Path $func) {
        Write-Host "   $func: $baseUrl/$func" -ForegroundColor Gray
    }
}

Write-Host "🎉 Despliegue completado!" -ForegroundColor Green
Write-Host "📝 Para ver logs: az webapp log tail --name $FunctionAppName --resource-group $ResourceGroup" -ForegroundColor Cyan
