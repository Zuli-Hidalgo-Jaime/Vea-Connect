# Script para aplicar migraciones en Azure App Service
# Uso: .\apply_azure_migrations.ps1 -ResourceGroup "rg-vea-connect-dev" -AppName "vea-connect"

param(
    [Parameter(Mandatory=$true)]
    [string]$ResourceGroup,
    
    [Parameter(Mandatory=$true)]
    [string]$AppName
)

Write-Host "🚀 Iniciando aplicación de migraciones en Azure..." -ForegroundColor Green

try {
    # 1. Conectar al contenedor via SSH
    Write-Host "📡 Conectando al contenedor de Azure App Service..." -ForegroundColor Yellow
    az webapp ssh --resource-group $ResourceGroup --name $AppName --command "
        echo '🔍 Verificando estado de la base de datos...'
        python manage.py showmigrations
        
        echo '📦 Aplicando migraciones...'
        python manage.py migrate --noinput
        
        echo '📁 Recolectando archivos estáticos...'
        python manage.py collectstatic --noinput
        
        echo '✅ Migraciones aplicadas exitosamente'
        exit
    "
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Migraciones aplicadas exitosamente" -ForegroundColor Green
        
        # 2. Reiniciar la aplicación
        Write-Host "🔄 Reiniciando la aplicación..." -ForegroundColor Yellow
        az webapp restart --resource-group $ResourceGroup --name $AppName
        
        Write-Host "✅ Proceso completado exitosamente" -ForegroundColor Green
    } else {
        Write-Host "❌ Error aplicando migraciones" -ForegroundColor Red
        exit 1
    }
    
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
