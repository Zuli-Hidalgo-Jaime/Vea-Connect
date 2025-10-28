# Script para copiar App Settings de funcapp-vea-prod a funcapp-vea-v2
# USO: .\scripts\copy_funcapp_settings_to_v2.ps1

$RG = "rg-vea-prod"
$SOURCE_APP = "funcapp-vea-prod"
$TARGET_APP = "funcapp-vea-v2"

Write-Host "Copiando variables de entorno de $SOURCE_APP -> $TARGET_APP" -ForegroundColor Cyan
Write-Host ""

# Obtener settings de la Function original
Write-Host "Obteniendo settings de $SOURCE_APP..." -ForegroundColor Yellow
$sourceSettings = az functionapp config appsettings list `
    -g $RG `
    -n $SOURCE_APP `
    -o json | ConvertFrom-Json | Where-Object { 
        $_.name -notlike 'WEBSITE_*' -and 
        $_.name -notlike 'FUNCTIONS_*' -and
        $_.name -notlike 'APPINSIGHTS_*' -and
        $_.name -notlike 'APPLICATIONINSIGHTS_*'
    }

if (-not $sourceSettings) {
    Write-Host "ERROR: No se pudieron obtener settings de $SOURCE_APP" -ForegroundColor Red
    exit 1
}

Write-Host "Encontrados $($sourceSettings.Count) settings" -ForegroundColor Green
Write-Host ""

# Mostrar settings que se copiarán (sin valores sensibles)
Write-Host "Settings a copiar:" -ForegroundColor Cyan
foreach ($setting in $sourceSettings) {
    $name = $setting.name
    $valuePreview = if ($setting.value.Length -gt 20) { 
        $setting.value.Substring(0, 20) + "..." 
    } else { 
        $setting.value 
    }
    
    # Ocultar valores sensibles
    if ($name -match "KEY|SECRET|PASSWORD|CONNECTION") {
        $valuePreview = "***HIDDEN***"
    }
    
    Write-Host "  - $name = $valuePreview" -ForegroundColor Gray
}

Write-Host ""
$confirm = Read-Host "Copiar estos settings a $TARGET_APP? (SI/no)"

if ($confirm -ne "SI") {
    Write-Host "Operacion cancelada" -ForegroundColor Red
    exit 0
}

Write-Host ""
Write-Host "Copiando settings a $TARGET_APP..." -ForegroundColor Yellow

# Copiar cada setting individualmente
$successCount = 0
$errorCount = 0

foreach ($setting in $sourceSettings) {
    try {
        az functionapp config appsettings set `
            -g $RG `
            -n $TARGET_APP `
            --settings "$($setting.name)=$($setting.value)" `
            --output none
        
        Write-Host "  OK: $($setting.name)" -ForegroundColor Green
        $successCount++
    }
    catch {
        Write-Host "  ERROR: $($setting.name): $($_.Exception.Message)" -ForegroundColor Red
        $errorCount++
    }
}

Write-Host ""
Write-Host "Resumen:" -ForegroundColor Cyan
Write-Host "  Copiados: $successCount" -ForegroundColor Green
Write-Host "  Errores: $errorCount" -ForegroundColor $(if ($errorCount -gt 0) { "Red" } else { "Gray" })
Write-Host ""

if ($errorCount -eq 0) {
    Write-Host "Todos los settings copiados exitosamente!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Proximos pasos:" -ForegroundColor Cyan
    Write-Host "  1. Verificar settings en Azure Portal"
    Write-Host "  2. Hacer push del código de functions-v2/"
    Write-Host "  3. GitHub Actions desplegará automáticamente"
    Write-Host "  4. Probar la Function sin Event Grid primero"
    Write-Host "  5. Crear Event Grid subscription para funcapp-vea-v2"
} else {
    Write-Host "ATENCION: Algunos settings NO se copiaron. Revisar errores arriba." -ForegroundColor Yellow
}

