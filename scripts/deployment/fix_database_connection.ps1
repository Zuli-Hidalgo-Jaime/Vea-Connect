# Script para diagnosticar y corregir problemas de conexión a la base de datos PostgreSQL en Azure
param(
    [string]$ResourceGroup = "vea-connect-rg",
    [string]$WebAppName = "vea-connect-g5dje9eba9bscnb6",
    [string]$DatabasePassword = ""
)

Write-Host "🔍 DIAGNÓSTICO DE CONEXIÓN A BASE DE DATOS POSTGRESQL" -ForegroundColor Cyan
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

# Función para obtener variables de entorno de Azure App Service
function Get-AzureAppSettings {
    param([string]$AppName, [string]$ResourceGroup)
    
    Write-Host "📋 Obteniendo configuración de Azure App Service..." -ForegroundColor Yellow
    
    try {
        $settings = az webapp config appsettings list --name $AppName --resource-group $ResourceGroup --output json | ConvertFrom-Json
        
        $dbSettings = @{}
        foreach ($setting in $settings) {
            if ($setting.name -like "*POSTGRESQL*" -or $setting.name -eq "DATABASE_URL") {
                $dbSettings[$setting.name] = $setting.value
            }
        }
        
        return $dbSettings
    } catch {
        Write-Host "❌ Error al obtener configuración de Azure App Service: $_" -ForegroundColor Red
        return $null
    }
}

# Función para actualizar variables de entorno
function Update-AzureAppSettings {
    param([string]$AppName, [string]$ResourceGroup, [hashtable]$Settings)
    
    Write-Host "🔄 Actualizando configuración de Azure App Service..." -ForegroundColor Yellow
    
    $settingsList = @()
    foreach ($key in $Settings.Keys) {
        $settingsList += "$key=$($Settings[$key])"
    }
    
    try {
        az webapp config appsettings set --name $AppName --resource-group $ResourceGroup --settings $settingsList --output none
        Write-Host "✅ Configuración actualizada exitosamente" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "❌ Error al actualizar configuración: $_" -ForegroundColor Red
        return $false
    }
}

# Función para generar DATABASE_URL correcta
function Generate-DatabaseUrl {
    param([hashtable]$Settings)
    
    $host = $Settings["AZURE_POSTGRESQL_HOST"]
    $name = $Settings["AZURE_POSTGRESQL_NAME"]
    $username = $Settings["AZURE_POSTGRESQL_USERNAME"]
    $password = $Settings["AZURE_POSTGRESQL_PASSWORD"]
    
    if (-not $host -or -not $name -or -not $username -or -not $password) {
        Write-Host "❌ Faltan variables de entorno para generar DATABASE_URL" -ForegroundColor Red
        return $null
    }
    
    # Asegurar que el usuario tenga el sufijo correcto
    if ($username -notlike "*@micrositio-vea-connect-server") {
        $username = "$username@micrositio-vea-connect-server"
        Write-Host "⚠️  Agregando sufijo al usuario: $username" -ForegroundColor Yellow
    }
    
    # Codificar la contraseña para caracteres especiales
    $encodedPassword = [System.Web.HttpUtility]::UrlEncode($password)
    
    # Generar URL
    $databaseUrl = "postgresql://$username`:$encodedPassword@$host`:5432/$name`?sslmode=require"
    
    return $databaseUrl
}

# Función para probar conexión a PostgreSQL
function Test-PostgreSQLConnection {
    param([hashtable]$Settings)
    
    Write-Host "🔌 Probando conexión a PostgreSQL..." -ForegroundColor Yellow
    
    $host = $Settings["AZURE_POSTGRESQL_HOST"]
    $name = $Settings["AZURE_POSTGRESQL_NAME"]
    $username = $Settings["AZURE_POSTGRESQL_USERNAME"]
    $password = $Settings["AZURE_POSTGRESQL_PASSWORD"]
    
    if (-not $host -or -not $name -or -not $username -or -not $password) {
        Write-Host "❌ Faltan variables de entorno para probar conexión" -ForegroundColor Red
        return $false
    }
    
    # Crear script temporal para probar conexión
    $testScript = @"
import psycopg2
import sys

try:
    conn = psycopg2.connect(
        host='$host',
        port=5432,
        dbname='$name',
        user='$username',
        password='$password',
        sslmode='require'
    )
    cursor = conn.cursor()
    cursor.execute('SELECT version();')
    version = cursor.fetchone()
    print(f"SUCCESS: {version[0]}")
    cursor.close()
    conn.close()
    sys.exit(0)
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
"@
    
    $testScript | Out-File -FilePath "temp_db_test.py" -Encoding UTF8
    
    try {
        $result = python temp_db_test.py 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Conexión exitosa: $result" -ForegroundColor Green
            return $true
        } else {
            Write-Host "❌ Error de conexión: $result" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "❌ Error al ejecutar prueba de conexión: $_" -ForegroundColor Red
        return $false
    } finally {
        if (Test-Path "temp_db_test.py") {
            Remove-Item "temp_db_test.py"
        }
    }
}

# Función para solicitar contraseña de forma segura
function Get-SecurePassword {
    param([string]$Prompt = "Ingresa la contraseña de la base de datos")
    
    Write-Host $Prompt -ForegroundColor Yellow
    $securePassword = Read-Host -AsSecureString
    $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
    return [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
}

# Obtener configuración actual
Write-Host "📋 Obteniendo configuración actual..." -ForegroundColor Yellow
$currentSettings = Get-AzureAppSettings -AppName $WebAppName -ResourceGroup $ResourceGroup

if (-not $currentSettings) {
    Write-Host "❌ No se pudo obtener la configuración de Azure App Service" -ForegroundColor Red
    exit 1
}

# Mostrar configuración actual
Write-Host "`n📋 CONFIGURACIÓN ACTUAL:" -ForegroundColor Cyan
foreach ($key in $currentSettings.Keys) {
    if ($key -like "*PASSWORD*") {
        Write-Host "  $key`: ********" -ForegroundColor Gray
    } else {
        Write-Host "  $key`: $($currentSettings[$key])" -ForegroundColor Gray
    }
}

# Verificar si necesitamos la contraseña
if (-not $currentSettings["AZURE_POSTGRESQL_PASSWORD"] -or $DatabasePassword) {
    if (-not $DatabasePassword) {
        $DatabasePassword = Get-SecurePassword
    }
    $currentSettings["AZURE_POSTGRESQL_PASSWORD"] = $DatabasePassword
}

# Probar conexión actual
Write-Host "`n🔌 PROBANDO CONEXIÓN ACTUAL..." -ForegroundColor Cyan
$connectionOk = Test-PostgreSQLConnection -Settings $currentSettings

if (-not $connectionOk) {
    Write-Host "`n❌ La conexión actual falló. Intentando corregir..." -ForegroundColor Red
    
    # Generar DATABASE_URL correcta
    $correctDatabaseUrl = Generate-DatabaseUrl -Settings $currentSettings
    
    if ($correctDatabaseUrl) {
        Write-Host "`n📝 DATABASE_URL corregida:" -ForegroundColor Yellow
        Write-Host "  $correctDatabaseUrl" -ForegroundColor Gray
        
        # Actualizar configuración
        $updatedSettings = $currentSettings.Clone()
        $updatedSettings["DATABASE_URL"] = $correctDatabaseUrl
        
        $updateSuccess = Update-AzureAppSettings -AppName $WebAppName -ResourceGroup $ResourceGroup -Settings $updatedSettings
        
        if ($updateSuccess) {
            Write-Host "`n🔄 Esperando 30 segundos para que los cambios se propaguen..." -ForegroundColor Yellow
            Start-Sleep -Seconds 30
            
            # Probar conexión nuevamente
            Write-Host "`n🔌 PROBANDO CONEXIÓN CORREGIDA..." -ForegroundColor Cyan
            $connectionOk = Test-PostgreSQLConnection -Settings $updatedSettings
            
            if ($connectionOk) {
                Write-Host "`n✅ ¡Problema resuelto! La conexión a la base de datos ahora funciona correctamente." -ForegroundColor Green
            } else {
                Write-Host "`n❌ La conexión sigue fallando después de la corrección." -ForegroundColor Red
                Write-Host "💡 Posibles causas adicionales:" -ForegroundColor Yellow
                Write-Host "  1. La contraseña es incorrecta" -ForegroundColor Yellow
                Write-Host "  2. El usuario no tiene permisos en la base de datos" -ForegroundColor Yellow
                Write-Host "  3. El servidor PostgreSQL no está ejecutándose" -ForegroundColor Yellow
                Write-Host "  4. Reglas de firewall bloquean la conexión" -ForegroundColor Yellow
            }
        } else {
            Write-Host "`n❌ No se pudo actualizar la configuración de Azure App Service" -ForegroundColor Red
        }
    } else {
        Write-Host "`n❌ No se pudo generar una DATABASE_URL correcta" -ForegroundColor Red
    }
} else {
    Write-Host "`n✅ La conexión a la base de datos está funcionando correctamente." -ForegroundColor Green
}

Write-Host "`n🎯 DIAGNÓSTICO COMPLETADO" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
