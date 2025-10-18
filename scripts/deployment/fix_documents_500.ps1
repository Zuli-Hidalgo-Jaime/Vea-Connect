# Script para diagnosticar y corregir el error 500 específico en el módulo de documentos
param(
    [string]$ResourceGroup = "vea-connect-rg",
    [string]$WebAppName = "vea-connect-g5dje9eba9bscnb6"
)

Write-Host "🔍 DIAGNÓSTICO ESPECÍFICO DEL ERROR 500 EN DOCUMENTOS" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

# Verificar si Azure CLI está instalado
try {
    $azVersion = az version --output json | ConvertFrom-Json
    Write-Host "✅ Azure CLI detectado: $($azVersion.'azure-cli')" -ForegroundColor Green
} catch {
    Write-Host "❌ Azure CLI no está instalado. Por favor, instálalo desde: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli" -ForegroundColor Red
    exit 1
}

# Verificar si el usuario está logueado
try {
    $account = az account show --output json | ConvertFrom-Json
    Write-Host "✅ Conectado como: $($account.user.name)" -ForegroundColor Green
} catch {
    Write-Host "❌ No estás logueado en Azure CLI. Ejecuta: az login" -ForegroundColor Red
    exit 1
}

# Función para ejecutar comando en Azure App Service
function Invoke-AzureAppServiceCommand {
    param([string]$AppName, [string]$ResourceGroup, [string]$Command)
    
    try {
        $result = az webapp ssh --name $AppName --resource-group $ResourceGroup --command $Command --output json | ConvertFrom-Json
        return $result
    } catch {
        Write-Host "❌ Error ejecutando comando en Azure App Service: $_" -ForegroundColor Red
        return $null
    }
}

# Función para obtener logs de la aplicación
function Get-AzureAppServiceLogs {
    param([string]$AppName, [string]$ResourceGroup)
    
    Write-Host "📋 Obteniendo logs de la aplicación..." -ForegroundColor Yellow
    
    try {
        $logs = az webapp log tail --name $AppName --resource-group $ResourceGroup --provider docker --output json | ConvertFrom-Json
        return $logs
    } catch {
        Write-Host "❌ Error obteniendo logs: $_" -ForegroundColor Red
        return $null
    }
}

# Función para ejecutar diagnóstico de documentos
function Invoke-DocumentsDiagnostic {
    param([string]$AppName, [string]$ResourceGroup)
    
    Write-Host "🔍 Ejecutando diagnóstico específico de documentos..." -ForegroundColor Yellow
    
    $command = "cd /home/site/wwwroot && python scripts/diagnostics/diagnose_documents_error.py"
    
    try {
        $result = az webapp ssh --name $AppName --resource-group $ResourceGroup --command $command
        return $result
    } catch {
        Write-Host "❌ Error ejecutando diagnóstico: $_" -ForegroundColor Red
        return $null
    }
}

# Función para aplicar migraciones
function Invoke-ApplyMigrations {
    param([string]$AppName, [string]$ResourceGroup)
    
    Write-Host "🔄 Aplicando migraciones..." -ForegroundColor Yellow
    
    $command = "cd /home/site/wwwroot && python manage.py migrate --settings=config.settings.production"
    
    try {
        $result = az webapp ssh --name $AppName --resource-group $ResourceGroup --command $command
        Write-Host "✅ Migraciones aplicadas exitosamente" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "❌ Error aplicando migraciones: $_" -ForegroundColor Red
        return $false
    }
}

# Función para verificar archivos de template
function Test-TemplateFiles {
    param([string]$AppName, [string]$ResourceGroup)
    
    Write-Host "📁 Verificando archivos de template..." -ForegroundColor Yellow
    
    $commands = @(
        "cd /home/site/wwwroot && find . -name 'documents.html'",
        "cd /home/site/wwwroot && find . -name 'documents' -type d",
        "cd /home/site/wwwroot && ls -la templates/",
        "cd /home/site/wwwroot && ls -la templates/documents/ 2>/dev/null || echo 'No existe templates/documents/'"
    )
    
    foreach ($cmd in $commands) {
        try {
            $result = az webapp ssh --name $AppName --resource-group $ResourceGroup --command $cmd
            Write-Host "   $result" -ForegroundColor Gray
        } catch {
            Write-Host "   ❌ Error: $_" -ForegroundColor Red
        }
    }
}

# Función para verificar configuración de archivos
function Test-FileConfiguration {
    param([string]$AppName, [string]$ResourceGroup)
    
    Write-Host "📁 Verificando configuración de archivos..." -ForegroundColor Yellow
    
    $commands = @(
        "cd /home/site/wwwroot && ls -la media/ 2>/dev/null || echo 'No existe media/'",
        "cd /home/site/wwwroot && python -c \"import os; print('MEDIA_ROOT:', os.environ.get('MEDIA_ROOT', 'No configurado'))\"",
        "cd /home/site/wwwroot && python -c \"from django.conf import settings; print('DEFAULT_FILE_STORAGE:', getattr(settings, 'DEFAULT_FILE_STORAGE', 'No configurado'))\""
    )
    
    foreach ($cmd in $commands) {
        try {
            $result = az webapp ssh --name $AppName --resource-group $ResourceGroup --command $cmd
            Write-Host "   $result" -ForegroundColor Gray
        } catch {
            Write-Host "   ❌ Error: $_" -ForegroundColor Red
        }
    }
}

# Función para reiniciar la aplicación
function Restart-AzureAppService {
    param([string]$AppName, [string]$ResourceGroup)
    
    Write-Host "🔄 Reiniciando aplicación..." -ForegroundColor Yellow
    
    try {
        az webapp restart --name $AppName --resource-group $ResourceGroup
        Write-Host "✅ Aplicación reiniciada exitosamente" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "❌ Error reiniciando aplicación: $_" -ForegroundColor Red
        return $false
    }
}

# Función para verificar variables de entorno específicas
function Get-DocumentsEnvironmentVariables {
    param([string]$AppName, [string]$ResourceGroup)
    
    Write-Host "📋 Verificando variables de entorno específicas..." -ForegroundColor Yellow
    
    try {
        $settings = az webapp config appsettings list --name $AppName --resource-group $ResourceGroup --output json | ConvertFrom-Json
        
        $documentsVars = @{}
        foreach ($setting in $settings) {
            if ($setting.name -like "*BLOB*" -or $setting.name -like "*AZURE*" -or $setting.name -like "*MEDIA*" -or $setting.name -like "*STORAGE*") {
                $documentsVars[$setting.name] = $setting.value
            }
        }
        
        Write-Host "🔧 Variables relacionadas con documentos:" -ForegroundColor Cyan
        foreach ($key in $documentsVars.Keys) {
            if ($key -like "*KEY*" -or $key -like "*PASSWORD*") {
                Write-Host "  $key`: ********" -ForegroundColor Gray
            } else {
                Write-Host "  $key`: $($documentsVars[$key])" -ForegroundColor Gray
            }
        }
        
        return $documentsVars
    } catch {
        Write-Host "❌ Error obteniendo variables de entorno: $_" -ForegroundColor Red
        return $null
    }
}

# Función para proporcionar soluciones específicas
function Show-DocumentsSolutions {
    Write-Host "`n🔧 SOLUCIONES ESPECÍFICAS PARA ERROR 500 EN DOCUMENTOS" -ForegroundColor Cyan
    Write-Host "================================================================" -ForegroundColor Cyan
    
    Write-Host "`n1. **Problema con archivos de template:**" -ForegroundColor Yellow
    Write-Host "   - Verificar que documents.html existe en templates/"
    Write-Host "   - Verificar que el directorio templates/documents/ existe"
    Write-Host "   - Asegurar que los templates están en el directorio correcto"
    
    Write-Host "`n2. **Problema con configuración de archivos:**" -ForegroundColor Yellow
    Write-Host "   - Verificar que MEDIA_ROOT está configurado correctamente"
    Write-Host "   - Verificar que DEFAULT_FILE_STORAGE está configurado"
    Write-Host "   - Asegurar que el directorio media/ existe y tiene permisos"
    
    Write-Host "`n3. **Problema con Azure Blob Storage:**" -ForegroundColor Yellow
    Write-Host "   - Verificar variables BLOB_ACCOUNT_NAME, BLOB_ACCOUNT_KEY, BLOB_CONTAINER_NAME"
    Write-Host "   - Verificar variables AZURE_ACCOUNT_NAME, AZURE_ACCOUNT_KEY, AZURE_CONTAINER"
    Write-Host "   - Asegurar que el contenedor de Azure existe y es accesible"
    
    Write-Host "`n4. **Problema con base de datos:**" -ForegroundColor Yellow
    Write-Host "   - Ejecutar migraciones: python manage.py migrate"
    Write-Host "   - Verificar que la tabla documents_document existe"
    Write-Host "   - Verificar permisos de usuario en la base de datos"
    
    Write-Host "`n5. **Problema con autenticación:**" -ForegroundColor Yellow
    Write-Host "   - Verificar que el usuario está autenticado"
    Write-Host "   - Verificar que el usuario tiene permisos para acceder a documentos"
    Write-Host "   - Verificar configuración de LOGIN_URL y LOGIN_REDIRECT_URL"
    
    Write-Host "`n6. **Para debugging adicional:**" -ForegroundColor Yellow
    Write-Host "   - Habilitar DEBUG temporalmente en Azure App Service"
    Write-Host "   - Revisar logs de Django en Azure Portal"
    Write-Host "   - Verificar logs de la aplicación en tiempo real"
}

# Ejecutar diagnóstico completo
Write-Host "`n🎯 INICIANDO DIAGNÓSTICO COMPLETO" -ForegroundColor Cyan

# 1. Verificar variables de entorno
$envVars = Get-DocumentsEnvironmentVariables -AppName $WebAppName -ResourceGroup $ResourceGroup

# 2. Verificar archivos de template
Test-TemplateFiles -AppName $WebAppName -ResourceGroup $ResourceGroup

# 3. Verificar configuración de archivos
Test-FileConfiguration -AppName $WebAppName -ResourceGroup $ResourceGroup

# 4. Ejecutar diagnóstico específico de documentos
Write-Host "`n🔍 EJECUTANDO DIAGNÓSTICO ESPECÍFICO..." -ForegroundColor Cyan
$diagnosticResult = Invoke-DocumentsDiagnostic -AppName $WebAppName -ResourceGroup $ResourceGroup

if ($diagnosticResult) {
    Write-Host "✅ Diagnóstico ejecutado exitosamente" -ForegroundColor Green
    Write-Host "📋 Resultado del diagnóstico:" -ForegroundColor Yellow
    Write-Host $diagnosticResult -ForegroundColor Gray
} else {
    Write-Host "❌ Error ejecutando diagnóstico específico" -ForegroundColor Red
}

# 5. Aplicar migraciones si es necesario
Write-Host "`n🔄 APLICANDO MIGRACIONES..." -ForegroundColor Cyan
$migrationsOk = Invoke-ApplyMigrations -AppName $WebAppName -ResourceGroup $ResourceGroup

# 6. Reiniciar aplicación
Write-Host "`n🔄 REINICIANDO APLICACIÓN..." -ForegroundColor Cyan
$restartOk = Restart-AzureAppService -AppName $WebAppName -ResourceGroup $ResourceGroup

# 7. Mostrar soluciones
Show-DocumentsSolutions

Write-Host "`n🎯 DIAGNÓSTICO COMPLETADO" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

Write-Host "`n💡 Próximos pasos:" -ForegroundColor Yellow
Write-Host "1. Revisa los resultados del diagnóstico específico" -ForegroundColor White
Write-Host "2. Aplica las soluciones recomendadas según los problemas encontrados" -ForegroundColor White
Write-Host "3. Verifica que la sección de documentos funcione correctamente" -ForegroundColor White
Write-Host "4. Si persisten los problemas, revisa los logs de Azure App Service" -ForegroundColor White
