# Script para resolver el error 500 en producción
param(
    [string]$AppServiceName = "veaconnect-webapp-prod-c7aaezbce3ftacdp",
    [string]$ResourceGroup = "veaconnect-webapp-prod-rg"
)

Write-Host "🔧 Resolviendo error 500 en Azure App Service" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green

# Verificar si Azure CLI está instalado
if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Azure CLI no está instalado. Por favor instálalo desde: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli" -ForegroundColor Red
    exit 1
}

# Verificar si estamos logueados en Azure
try {
    $account = az account show 2>$null | ConvertFrom-Json
    if (-not $account) {
        Write-Host "❌ No estás logueado en Azure. Ejecuta: az login" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Logueado en Azure como: $($account.user.name)" -ForegroundColor Green
} catch {
    Write-Host "❌ Error al verificar cuenta de Azure" -ForegroundColor Red
    exit 1
}

# Función para ejecutar comando en Azure App Service
function Invoke-AzureAppServiceCommand {
    param(
        [string]$Command,
        [string]$Description
    )
    
    Write-Host "🔄 $Description..." -ForegroundColor Yellow
    try {
        $result = az webapp ssh --name $AppServiceName --resource-group $ResourceGroup --command $Command 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ $Description completado" -ForegroundColor Green
            return $result
        } else {
            Write-Host "❌ Error en $Description" -ForegroundColor Red
            Write-Host $result -ForegroundColor Red
            return $null
        }
    } catch {
        Write-Host "❌ Error al ejecutar comando: $Command" -ForegroundColor Red
        return $null
    }
}

# Función para verificar el estado del App Service
function Test-AppServiceStatus {
    Write-Host "🔍 Verificando estado del App Service..." -ForegroundColor Yellow
    
    try {
        $status = az webapp show --name $AppServiceName --resource-group $ResourceGroup --query "state" -o tsv
        if ($status -eq "Running") {
            Write-Host "✅ App Service está ejecutándose" -ForegroundColor Green
            return $true
        } else {
            Write-Host "❌ App Service no está ejecutándose. Estado: $status" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "❌ Error al verificar estado del App Service" -ForegroundColor Red
        return $false
    }
}

# Verificar estado del App Service
if (-not (Test-AppServiceStatus)) {
    Write-Host "❌ No se puede continuar. El App Service no está ejecutándose." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🚀 Iniciando proceso de corrección..." -ForegroundColor Green

# 1. Verificar conexión a la base de datos
Write-Host "📊 Verificando conexión a la base de datos..." -ForegroundColor Yellow
$dbCheck = Invoke-AzureAppServiceCommand "python manage.py shell -c \"from django.db import connection; cursor = connection.cursor(); cursor.execute('SELECT 1'); print('Database connection OK')\"" "Verificación de base de datos"

# 2. Aplicar migraciones
Write-Host "🔄 Aplicando migraciones..." -ForegroundColor Yellow
$migrations = Invoke-AzureAppServiceCommand "python manage.py migrate --verbosity=2" "Aplicación de migraciones"

# 3. Recolectar archivos estáticos
Write-Host "📁 Recolectando archivos estáticos..." -ForegroundColor Yellow
$staticFiles = Invoke-AzureAppServiceCommand "python manage.py collectstatic --noinput" "Recolección de archivos estáticos"

# 4. Verificar tabla CustomUser
Write-Host "👥 Verificando tabla CustomUser..." -ForegroundColor Yellow
$userTable = Invoke-AzureAppServiceCommand "python manage.py shell -c `"from apps.core.models import CustomUser; print(f'Users in DB: {CustomUser.objects.count()}')`"" "Verificación de tabla CustomUser"

# 5. Crear superusuario si es necesario
Write-Host "👤 Verificando superusuario..." -ForegroundColor Yellow
$superuser = Invoke-AzureAppServiceCommand "python manage.py shell -c `"from apps.core.models import CustomUser; print('Superusers:', CustomUser.objects.filter(is_superuser=True).count())`"" "Verificación de superusuario"

# 6. Ejecutar script de diagnóstico completo
Write-Host "🔍 Ejecutando diagnóstico completo..." -ForegroundColor Yellow
$diagnostic = Invoke-AzureAppServiceCommand "python scripts/deployment/fix_production_500.py" "Diagnóstico completo"

Write-Host ""
Write-Host "🏁 Proceso completado" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green

# Verificar el resultado
Write-Host "🔍 Verificando que el error 500 se haya resuelto..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "https://$AppServiceName.azurewebsites.net/login/" -Method GET -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ El endpoint de login responde correctamente (código 200)" -ForegroundColor Green
    } else {
        Write-Host "⚠️  El endpoint responde con código: $($response.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Error al verificar el endpoint de login" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}

Write-Host ""
Write-Host "💡 Próximos pasos:" -ForegroundColor Cyan
Write-Host "1. Verifica manualmente el endpoint de login" -ForegroundColor White
Write-Host "2. Revisa los logs de Azure si persiste el error" -ForegroundColor White
Write-Host "3. Ejecuta el script de diagnóstico si es necesario" -ForegroundColor White

Write-Host ""
Write-Host "🔗 URL del App Service: https://$AppServiceName.azurewebsites.net/" -ForegroundColor Blue
Write-Host "🔗 URL del login: https://$AppServiceName.azurewebsites.net/login/" -ForegroundColor Blue 