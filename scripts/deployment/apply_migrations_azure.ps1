# Script para aplicar migraciones en Azure App Service
param(
    [string]$ResourceGroupName = "rg-vea-connect-prod",
    [string]$AppServiceName = "veaconnect-webapp-prod-c7aaezbce3ftacdp",
    [string]$SlotName = ""
)

Write-Host "=== APLICANDO MIGRACIONES EN AZURE APP SERVICE ===" -ForegroundColor Green

try {
    # Verificar si estamos conectados a Azure
    $context = Get-AzContext
    if (-not $context) {
        Write-Host "❌ No estás conectado a Azure. Ejecuta Connect-AzAccount primero." -ForegroundColor Red
        exit 1
    }
    
    Write-Host "✅ Conectado a Azure como: $($context.Account.Id)" -ForegroundColor Green
    
    # Construir el comando de migración
    $migrationCommand = "python manage.py migrate"
    
    # Aplicar migraciones
    Write-Host "Aplicando migraciones..." -ForegroundColor Yellow
    
    if ($SlotName) {
        # Aplicar en slot específico
        az webapp ssh --resource-group $ResourceGroupName --name $AppServiceName --slot $SlotName --command "$migrationCommand"
    } else {
        # Aplicar en producción
        az webapp ssh --resource-group $ResourceGroupName --name $AppServiceName --command "$migrationCommand"
    }
    
    Write-Host "✅ Migraciones aplicadas exitosamente" -ForegroundColor Green
    
    # Verificar estado de migraciones
    Write-Host "Verificando estado de migraciones..." -ForegroundColor Yellow
    
    $showMigrationsCommand = "python manage.py showmigrations"
    
    if ($SlotName) {
        az webapp ssh --resource-group $ResourceGroupName --name $AppServiceName --slot $SlotName --command "$showMigrationsCommand"
    } else {
        az webapp ssh --resource-group $ResourceGroupName --name $AppServiceName --command "$showMigrationsCommand"
    }
    
} catch {
    Write-Host "❌ Error aplicando migraciones: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host "=== PROCESO COMPLETADO ===" -ForegroundColor Green
