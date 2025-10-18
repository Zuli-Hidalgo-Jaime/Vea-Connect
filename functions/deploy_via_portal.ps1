# ===========================================
# PREPARE FUNCTIONS FOR AZURE PORTAL DEPLOYMENT
# ===========================================

Write-Host "Preparando archivos para deployment via Azure Portal..." -ForegroundColor Green

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
deploy_*.ps1
"@ | Out-File -FilePath ".funcignore" -Encoding UTF8
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
    Write-Host "Paquete creado: functions.zip ($([math]::Round($zipSize, 2)) MB)" -ForegroundColor Green
} elseif (Test-Path "functions-deploy.zip") {
    $zipSize = (Get-Item "functions-deploy.zip").Length / 1MB
    Write-Host "Paquete creado: functions-deploy.zip ($([math]::Round($zipSize, 2)) MB)" -ForegroundColor Green
} else {
    Write-Host "Error: No se pudo crear el paquete" -ForegroundColor Red
    exit 1
}

Write-Host "`n=== INSTRUCCIONES PARA DEPLOYMENT MANUAL ===" -ForegroundColor Cyan
Write-Host "1. Ve a Azure Portal: https://portal.azure.com" -ForegroundColor White
Write-Host "2. Busca el Function App: 'vea-functions-apis'" -ForegroundColor White
Write-Host "3. Ve a 'Deployment Center'" -ForegroundColor White
Write-Host "4. Selecciona 'Manual deployment'" -ForegroundColor White
Write-Host "5. Sube el archivo ZIP creado en este directorio" -ForegroundColor White
Write-Host "6. Espera a que se complete el deployment" -ForegroundColor White
Write-Host "`nFunciones incluidas en el paquete:" -ForegroundColor Yellow

# Listar las funciones incluidas
$functions = @(
    "whatsapp_event_grid_trigger",
    "create_embedding", 
    "search_similar",
    "get_stats",
    "health",
    "embeddings_health_check"
)

foreach ($function in $functions) {
    if (Test-Path $function) {
        Write-Host "   ✓ $function" -ForegroundColor Green
    } else {
        Write-Host "   ✗ $function (no encontrado)" -ForegroundColor Red
    }
}

Write-Host "`n=== CONFIGURACIÓN POST-DEPLOYMENT ===" -ForegroundColor Cyan
Write-Host "1. Configurar variables de entorno en Azure Portal" -ForegroundColor White
Write-Host "2. Habilitar WhatsApp en Azure Communication Services" -ForegroundColor White
Write-Host "3. Configurar webhook URL para WhatsApp" -ForegroundColor White
Write-Host "4. Probar las funciones" -ForegroundColor White

Write-Host "`n¡Listo! El paquete está preparado para deployment manual." -ForegroundColor Green
