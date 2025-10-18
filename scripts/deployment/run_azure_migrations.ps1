# Script para ejecutar migraciones en Azure App Service remotamente
param(
    [Parameter(Mandatory=$true)]
    [string]$ResourceGroup,
    
    [Parameter(Mandatory=$true)]
    [string]$WebAppName
)

Write-Host "=== EJECUTANDO MIGRACIONES EN AZURE APP SERVICE ===" -ForegroundColor Green
Write-Host ""

# Verificar que estamos conectados a Azure
try {
    $context = Get-AzContext
    Write-Host "Conectado a Azure como: $($context.Account.Id)" -ForegroundColor Green
} catch {
    Write-Host "No estas conectado a Azure. Ejecuta 'Connect-AzAccount' primero." -ForegroundColor Red
    exit 1
}

Write-Host "Ejecutando migraciones en $WebAppName..." -ForegroundColor Yellow

try {
    # Ejecutar migraciones via SSH
    $migrationCommand = "python manage.py migrate --settings=config.settings.production --noinput"
    
    Write-Host "Comando a ejecutar: $migrationCommand" -ForegroundColor Cyan
    
    # Ejecutar el comando via SSH
    az webapp ssh --name $WebAppName --resource-group $ResourceGroup --command "$migrationCommand"
    
    Write-Host "✅ Migraciones ejecutadas exitosamente" -ForegroundColor Green
    
} catch {
    Write-Host "❌ Error al ejecutar migraciones: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=== VERIFICACIÓN ===" -ForegroundColor Cyan
Write-Host "1. Verifica que la aplicación responda: https://$WebAppName.azurewebsites.net/health/" -ForegroundColor White
Write-Host "2. Revisa los logs: az webapp log tail --name $WebAppName --resource-group $ResourceGroup" -ForegroundColor White

Write-Host ""
Write-Host "🎉 Proceso completado" -ForegroundColor Green
