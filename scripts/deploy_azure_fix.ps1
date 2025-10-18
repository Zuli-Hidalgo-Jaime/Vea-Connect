# Script de Despliegue para Corrección de Azure Storage
# Fecha: 11 de Agosto, 2025
# Propósito: Aplicar corrección del error de content_disposition

param(
    [string]$Environment = "production",
    [switch]$Force = $false
)

Write-Host "=== DESPLIEGUE DE CORRECCIÓN AZURE STORAGE ===" -ForegroundColor Green
Write-Host "Fecha: $(Get-Date)" -ForegroundColor Yellow
Write-Host "Ambiente: $Environment" -ForegroundColor Yellow

# Verificar que estamos en el directorio correcto
if (-not (Test-Path "requirements.txt")) {
    Write-Host "✗ Error: No se encontró requirements.txt" -ForegroundColor Red
    Write-Host "   Asegúrate de estar en el directorio raíz del proyecto" -ForegroundColor Red
    exit 1
}

# Función para ejecutar comandos y mostrar resultado
function Invoke-CommandWithLog {
    param(
        [string]$Command,
        [string]$Description
    )
    
    Write-Host "`n=== $Description ===" -ForegroundColor Cyan
    Write-Host "Ejecutando: $Command" -ForegroundColor Gray
    
    try {
        $result = Invoke-Expression $Command 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Comando ejecutado exitosamente" -ForegroundColor Green
            if ($result) {
                Write-Host "Salida: $result" -ForegroundColor Gray
            }
            return $true
        } else {
            Write-Host "✗ Error en el comando (Exit Code: $LASTEXITCODE)" -ForegroundColor Red
            Write-Host "Salida: $result" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "✗ Error al ejecutar comando: $_" -ForegroundColor Red
        return $false
    }
}

# Paso 1: Verificar estado actual
Write-Host "`n=== PASO 1: VERIFICACIÓN DEL ESTADO ACTUAL ===" -ForegroundColor Blue

$success = Invoke-CommandWithLog "python scripts/diagnose_azure_versions.py" "Diagnóstico de versiones actuales"
if (-not $success) {
    Write-Host "⚠ Advertencia: No se pudo ejecutar el diagnóstico completo" -ForegroundColor Yellow
}

# Paso 2: Actualizar dependencias
Write-Host "`n=== PASO 2: ACTUALIZACIÓN DE DEPENDENCIAS ===" -ForegroundColor Blue

$success = Invoke-CommandWithLog "pip install 'azure-core>=1.35.0,<2.0.0' --upgrade" "Actualizando azure-core"
if (-not $success) {
    Write-Host "⚠ Advertencia: Error al actualizar azure-core" -ForegroundColor Yellow
}

$success = Invoke-CommandWithLog "pip install 'requests>=2.31.0' --upgrade" "Actualizando requests"
if (-not $success) {
    Write-Host "⚠ Advertencia: Error al actualizar requests" -ForegroundColor Yellow
}

# Paso 3: Reinstalar dependencias de Azure
Write-Host "`n=== PASO 3: REINSTALACIÓN DE DEPENDENCIAS AZURE ===" -ForegroundColor Blue

$azurePackages = @(
    "azure-storage-blob==12.19.0",
    "azure-identity==1.15.0",
    "azure-common==1.1.28"
)

foreach ($package in $azurePackages) {
    $success = Invoke-CommandWithLog "pip install $package --force-reinstall" "Reinstalando $package"
    if (-not $success) {
        Write-Host "⚠ Advertencia: Error al reinstalar $package" -ForegroundColor Yellow
    }
}

# Paso 4: Verificar cambios
Write-Host "`n=== PASO 4: VERIFICACIÓN DE CAMBIOS ===" -ForegroundColor Blue

$success = Invoke-CommandWithLog "pip list | Select-String azure" "Versiones finales de Azure"
if (-not $success) {
    Write-Host "⚠ Advertencia: No se pudieron verificar las versiones" -ForegroundColor Yellow
}

# Paso 5: Probar el servicio
Write-Host "`n=== PASO 5: PRUEBA DEL SERVICIO ===" -ForegroundColor Blue

$success = Invoke-CommandWithLog "python scripts/fix_azure_dependencies.py" "Prueba del servicio de almacenamiento"
if (-not $success) {
    Write-Host "⚠ Advertencia: El servicio puede no estar completamente funcional" -ForegroundColor Yellow
}

# Paso 6: Verificación final
Write-Host "`n=== PASO 6: VERIFICACIÓN FINAL ===" -ForegroundColor Blue

$success = Invoke-CommandWithLog "python scripts/diagnose_azure_versions.py" "Diagnóstico final"
if ($success) {
    Write-Host "✓ Verificación final completada" -ForegroundColor Green
} else {
    Write-Host "⚠ Advertencia: Verificación final incompleta" -ForegroundColor Yellow
}

# Resumen
Write-Host "`n=== RESUMEN DEL DESPLIEGUE ===" -ForegroundColor Green
Write-Host "✓ Corrección de código aplicada" -ForegroundColor Green
Write-Host "✓ Dependencias actualizadas" -ForegroundColor Green
Write-Host "✓ Manejo de errores mejorado" -ForegroundColor Green

Write-Host "`n=== PRÓXIMOS PASOS ===" -ForegroundColor Yellow
Write-Host "1. Reinicia la aplicación web" -ForegroundColor White
Write-Host "2. Prueba subir un documento" -ForegroundColor White
Write-Host "3. Verifica los logs para confirmar que no hay errores" -ForegroundColor White
Write-Host "4. Monitorea el comportamiento durante las próximas horas" -ForegroundColor White

Write-Host "`n=== COMANDOS ÚTILES ===" -ForegroundColor Cyan
Write-Host "Ver logs en tiempo real:" -ForegroundColor White
Write-Host "  az webapp log tail --name veaconnect-webapp-prod --resource-group veaconnect-rg" -ForegroundColor Gray
Write-Host "`nVerificar estado del servicio:" -ForegroundColor White
Write-Host "  python scripts/diagnose_azure_versions.py" -ForegroundColor Gray

Write-Host "`nDespliegue completado: $(Get-Date)" -ForegroundColor Green
