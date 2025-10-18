# Script para limpiar y verificar el entorno de Azure Functions

Write-Host "🧹 Limpiando entorno de Azure Functions..." -ForegroundColor Green

# Eliminar archivos ZIP
Write-Host "🗑️  Eliminando archivos ZIP..." -ForegroundColor Yellow
if (Test-Path "*.zip") {
    Remove-Item "*.zip" -Force
    Write-Host "✅ Archivos ZIP eliminados" -ForegroundColor Green
}

# Limpiar directorios de caché
Write-Host "🗑️  Limpiando caché..." -ForegroundColor Yellow
$cacheDirs = @("__pycache__", ".python_packages", "venv310", ".venv", ".venv_clean")
foreach ($dir in $cacheDirs) {
    if (Test-Path $dir) {
        Remove-Item $dir -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "✅ $dir eliminado" -ForegroundColor Green
    }
}

# Verificar estructura de funciones
Write-Host "🔍 Verificando estructura de funciones..." -ForegroundColor Yellow

$requiredFunctions = @(
    "whatsapp_event_grid_trigger",
    "health", 
    "create_embedding",
    "search_similar",
    "get_stats",
    "embeddings_health_check"
)

$missingFunctions = @()
foreach ($func in $requiredFunctions) {
    if (Test-Path $func) {
        Write-Host "✅ $func" -ForegroundColor Green
        
        # Verificar que tiene function.json
        if (Test-Path "$func/function.json") {
            Write-Host "   📄 function.json encontrado" -ForegroundColor Gray
        } else {
            Write-Warning "   ⚠️  function.json faltante en $func"
        }
        
        # Verificar que tiene __init__.py
        if (Test-Path "$func/__init__.py") {
            Write-Host "   🐍 __init__.py encontrado" -ForegroundColor Gray
        } else {
            Write-Warning "   ⚠️  __init__.py faltante en $func"
        }
    } else {
        Write-Warning "❌ $func no encontrada"
        $missingFunctions += $func
    }
}

# Verificar archivos de configuración
Write-Host "📋 Verificando archivos de configuración..." -ForegroundColor Yellow

$configFiles = @("host.json", "requirements.txt", "local.settings.json")
foreach ($file in $configFiles) {
    if (Test-Path $file) {
        Write-Host "✅ $file" -ForegroundColor Green
    } else {
        Write-Warning "❌ $file faltante"
    }
}

# Verificar dependencias en requirements.txt
if (Test-Path "requirements.txt") {
    Write-Host "📦 Verificando dependencias críticas..." -ForegroundColor Yellow
    
    $criticalDeps = @("azure-core", "azure-functions", "azure-communication-sms")
    $content = Get-Content "requirements.txt" -Raw
    
    foreach ($dep in $criticalDeps) {
        if ($content -match $dep) {
            Write-Host "✅ $dep encontrado" -ForegroundColor Green
        } else {
            Write-Warning "❌ $dep faltante en requirements.txt"
        }
    }
}

# Verificar servicios
Write-Host "🔧 Verificando servicios..." -ForegroundColor Yellow
if (Test-Path "services") {
    Write-Host "✅ Directorio services encontrado" -ForegroundColor Green
    
    $services = @("llm.py", "whatsapp_sender.py", "search_index_service.py")
    foreach ($service in $services) {
        if (Test-Path "services/$service") {
            Write-Host "   ✅ $service" -ForegroundColor Gray
        } else {
            Write-Warning "   ⚠️  $service faltante"
        }
    }
} else {
    Write-Warning "❌ Directorio services no encontrado"
}

# Resumen
Write-Host "`n📊 RESUMEN:" -ForegroundColor Cyan
Write-Host "✅ Limpieza completada" -ForegroundColor Green

if ($missingFunctions.Count -gt 0) {
    Write-Warning "⚠️  Funciones faltantes: $($missingFunctions -join ', ')"
} else {
    Write-Host "✅ Todas las funciones están presentes" -ForegroundColor Green
}

Write-Host "`n🚀 Próximos pasos:" -ForegroundColor Cyan
Write-Host "1. Ejecutar: .\deploy_functions_no_zip.ps1" -ForegroundColor Yellow
Write-Host "2. Verificar logs: az webapp log tail --name vea-functions-apis --resource-group vea-connect-rg" -ForegroundColor Yellow
Write-Host "3. Probar funciones individualmente" -ForegroundColor Yellow
