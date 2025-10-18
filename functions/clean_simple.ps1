# Script simplificado para limpiar Azure Functions

Write-Host "Limpiando entorno de Azure Functions..." -ForegroundColor Green

# Eliminar archivos ZIP
Write-Host "Eliminando archivos ZIP..." -ForegroundColor Yellow
if (Test-Path "*.zip") {
    Remove-Item "*.zip" -Force
    Write-Host "Archivos ZIP eliminados" -ForegroundColor Green
}

# Limpiar directorios de cache
Write-Host "Limpiando cache..." -ForegroundColor Yellow
$cacheDirs = @("__pycache__", ".python_packages", "venv310", ".venv", ".venv_clean")
foreach ($dir in $cacheDirs) {
    if (Test-Path $dir) {
        Remove-Item $dir -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "$dir eliminado" -ForegroundColor Green
    }
}

# Verificar funciones
Write-Host "Verificando funciones..." -ForegroundColor Yellow
$functions = @("whatsapp_event_grid_trigger", "health", "create_embedding", "search_similar", "get_stats", "embeddings_health_check")

foreach ($func in $functions) {
    if (Test-Path $func) {
        Write-Host "OK: $func" -ForegroundColor Green
    } else {
        Write-Warning "FALTANTE: $func"
    }
}

# Verificar archivos de configuracion
Write-Host "Verificando archivos de configuracion..." -ForegroundColor Yellow
$configFiles = @("host.json", "requirements.txt", "local.settings.json")
foreach ($file in $configFiles) {
    if (Test-Path $file) {
        Write-Host "OK: $file" -ForegroundColor Green
    } else {
        Write-Warning "FALTANTE: $file"
    }
}

Write-Host "Limpieza completada!" -ForegroundColor Green
Write-Host "Proximo paso: .\deploy_functions_no_zip.ps1" -ForegroundColor Cyan
