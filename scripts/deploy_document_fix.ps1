# Script para desplegar las mejoras en el manejo de errores de descarga de documentos
param(
    [string]$ResourceGroup = "veaconnect-rg",
    [string]$AppServiceName = "veaconnect-webapp-prod"
)

Write-Host "🚀 Iniciando despliegue de mejoras en documentos..." -ForegroundColor Green

# Verificar que estamos en el directorio correcto
if (-not (Test-Path "manage.py")) {
    Write-Host "❌ Error: No se encontró manage.py. Ejecuta este script desde la raíz del proyecto." -ForegroundColor Red
    exit 1
}

# Verificar que los archivos modificados existen
$filesToCheck = @(
    "apps/documents/templates/documents.html",
    "apps/documents/views.py",
    "scripts/diagnose_document_download.py"
)

foreach ($file in $filesToCheck) {
    if (-not (Test-Path $file)) {
        Write-Host "❌ Error: No se encontró el archivo $file" -ForegroundColor Red
        exit 1
    }
}

Write-Host "✅ Archivos verificados correctamente" -ForegroundColor Green

# Desplegar a Azure App Service
Write-Host "📦 Desplegando a Azure App Service..." -ForegroundColor Yellow

try {
    # Usar Azure CLI para desplegar
    az webapp deployment source config-zip `
        --resource-group $ResourceGroup `
        --name $AppServiceName `
        --src . `
        --timeout 1800

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Despliegue completado exitosamente" -ForegroundColor Green
    } else {
        Write-Host "❌ Error en el despliegue" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Error durante el despliegue: $_" -ForegroundColor Red
    exit 1
}

# Esperar a que la aplicación se reinicie
Write-Host "⏳ Esperando a que la aplicación se reinicie..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Verificar el estado de la aplicación
Write-Host "🔍 Verificando estado de la aplicación..." -ForegroundColor Yellow

try {
    $appStatus = az webapp show --resource-group $ResourceGroup --name $AppServiceName --query "state" --output tsv
    Write-Host "Estado de la aplicación: $appStatus" -ForegroundColor Cyan
} catch {
    Write-Host "⚠️  No se pudo verificar el estado de la aplicación" -ForegroundColor Yellow
}

# Diagnosticar el problema de descarga
Write-Host "🔍 Diagnosticando problema de descarga..." -ForegroundColor Yellow

try {
    # Ejecutar el script de diagnóstico en Azure
    az webapp ssh --resource-group $ResourceGroup --name $AppServiceName --command "cd /home/site/wwwroot && python scripts/diagnose_document_download.py"
} catch {
    Write-Host "⚠️  No se pudo ejecutar el diagnóstico remotamente" -ForegroundColor Yellow
    Write-Host "💡 Puedes ejecutar manualmente: python scripts/diagnose_document_download.py" -ForegroundColor Cyan
}

Write-Host "🎉 Proceso de despliegue completado!" -ForegroundColor Green
Write-Host "📋 Próximos pasos:" -ForegroundColor Cyan
Write-Host "   1. Verificar que el modal de error se muestra correctamente" -ForegroundColor White
Write-Host "   2. Probar la descarga del archivo Donaciones_Daya" -ForegroundColor White
Write-Host "   3. Verificar que los mensajes de error son más amigables" -ForegroundColor White
Write-Host "   4. Ejecutar el diagnóstico si hay problemas persistentes" -ForegroundColor White
