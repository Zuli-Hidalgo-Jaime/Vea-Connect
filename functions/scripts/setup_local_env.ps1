# Script de PowerShell para configurar variables de entorno de Azure Functions
# Ejecutar desde el directorio functions/

param(
    [switch]$Interactive = $true
)

Write-Host "=== Configuración de Variables de Entorno para Azure Functions ===" -ForegroundColor Green
Write-Host ""

# Verificar si estamos en el directorio correcto
if (-not (Test-Path "local.settings.json")) {
    Write-Host "Error: No se encontró local.settings.json. Ejecuta este script desde el directorio functions/" -ForegroundColor Red
    exit 1
}

# Cargar configuración actual
$settings = Get-Content "local.settings.json" | ConvertFrom-Json

# Asegurar que Values existe
if (-not $settings.Values) {
    $settings.Values = @{}
}

# Configuración básica de Functions
$settings.Values.FUNCTIONS_WORKER_RUNTIME = "python"
$settings.Values.AzureWebJobsStorage = "UseDevelopmentStorage=true"
$settings.Values.FUNCTIONS_EXTENSION_VERSION = "~4"

if ($Interactive) {
    Write-Host "Configurando Azure OpenAI..." -ForegroundColor Yellow
    $settings.Values.AZURE_OPENAI_ENDPOINT = Read-Host "Azure OpenAI Endpoint (actual: $($settings.Values.AZURE_OPENAI_ENDPOINT))"
    $settings.Values.AZURE_OPENAI_API_KEY = Read-Host "Azure OpenAI API Key" -AsSecureString | ConvertFrom-SecureString -AsPlainText

    Write-Host "`nConfigurando Azure AI Search..." -ForegroundColor Yellow
    $searchServiceName = Read-Host "Azure Search Service Name (sin .search.windows.net) (actual: $($settings.Values.AZURE_SEARCH_SERVICE_NAME))"
    $settings.Values.AZURE_SEARCH_SERVICE_NAME = $searchServiceName
    $settings.Values.AZURE_SEARCH_API_KEY = Read-Host "Azure Search API Key" -AsSecureString | ConvertFrom-SecureString -AsPlainText
    $settings.Values.AZURE_SEARCH_INDEX_NAME = Read-Host "Azure Search Index Name (actual: $($settings.Values.AZURE_SEARCH_INDEX_NAME))"
    
    # Construir endpoint completo
    if ($searchServiceName) {
        $settings.Values.AZURE_SEARCH_ENDPOINT = "https://$searchServiceName.search.windows.net"
        $settings.Values.AZURE_SEARCH_KEY = $settings.Values.AZURE_SEARCH_API_KEY
    }

    Write-Host "`nConfigurando Azure Communication Services..." -ForegroundColor Yellow
    $settings.Values.ACS_CONNECTION_STRING = Read-Host "ACS Connection String (actual: $($settings.Values.ACS_CONNECTION_STRING))"
    $settings.Values.ACS_EVENT_GRID_TOPIC_ENDPOINT = Read-Host "ACS Event Grid Topic Endpoint (actual: $($settings.Values.ACS_EVENT_GRID_TOPIC_ENDPOINT))"
    $settings.Values.ACS_EVENT_GRID_TOPIC_KEY = Read-Host "ACS Event Grid Topic Key" -AsSecureString | ConvertFrom-SecureString -AsPlainText
    $settings.Values.ACS_PHONE_NUMBER = Read-Host "ACS Phone Number (actual: $($settings.Values.ACS_PHONE_NUMBER))"
    $settings.Values.ACS_WHATSAPP_API_KEY = Read-Host "ACS WhatsApp API Key" -AsSecureString | ConvertFrom-SecureString -AsPlainText
    $settings.Values.ACS_WHATSAPP_ENDPOINT = Read-Host "ACS WhatsApp Endpoint (actual: $($settings.Values.ACS_WHATSAPP_ENDPOINT))"

    Write-Host "`nConfigurando Base de Datos..." -ForegroundColor Yellow
    $settings.Values.DATABASE_URL = Read-Host "Database URL (actual: $($settings.Values.DATABASE_URL))"

    Write-Host "`nConfigurando Redis..." -ForegroundColor Yellow
    $settings.Values.AZURE_REDIS_CONNECTIONSTRING = Read-Host "Azure Redis Connection String (actual: $($settings.Values.AZURE_REDIS_CONNECTIONSTRING))"

    Write-Host "`nConfigurando Azure Storage..." -ForegroundColor Yellow
    $settings.Values.BLOB_ACCOUNT_NAME = Read-Host "Blob Account Name (actual: $($settings.Values.BLOB_ACCOUNT_NAME))"
    $settings.Values.BLOB_ACCOUNT_KEY = Read-Host "Blob Account Key" -AsSecureString | ConvertFrom-SecureString -AsPlainText
    $settings.Values.BLOB_CONTAINER_NAME = Read-Host "Blob Container Name (actual: $($settings.Values.BLOB_CONTAINER_NAME))"
} else {
    # Configuración no interactiva con valores por defecto
    Write-Host "Configurando con valores por defecto..." -ForegroundColor Yellow
    
    if (-not $settings.Values.AZURE_SEARCH_INDEX_NAME) {
        $settings.Values.AZURE_SEARCH_INDEX_NAME = "embeddings-index"
    }
    
    if (-not $settings.Values.BLOB_CONTAINER_NAME) {
        $settings.Values.BLOB_CONTAINER_NAME = "documents"
    }
}

# Guardar configuración
$settings | ConvertTo-Json -Depth 10 | Set-Content "local.settings.json"

Write-Host "`n=== Configuración Completada ===" -ForegroundColor Green
Write-Host "El archivo local.settings.json ha sido actualizado." -ForegroundColor White
Write-Host ""
Write-Host "Para usar las funciones localmente:" -ForegroundColor Cyan
Write-Host "1. Asegúrate de tener Azure Storage Emulator ejecutándose" -ForegroundColor White
Write-Host "2. Ejecuta: func start --port 7074" -ForegroundColor White
Write-Host ""
Write-Host "Nota: Las variables de entorno con valores vacíos no funcionarán correctamente." -ForegroundColor Yellow

# Verificar Azure Storage Emulator
Write-Host "`nVerificando Azure Storage Emulator..." -ForegroundColor Yellow
try {
    $emulatorProcess = Get-Process "AzureStorageEmulator" -ErrorAction SilentlyContinue
    if ($emulatorProcess) {
        Write-Host "✓ Azure Storage Emulator está ejecutándose" -ForegroundColor Green
    } else {
        Write-Host "✗ Azure Storage Emulator no está ejecutándose" -ForegroundColor Red
        Write-Host "Para iniciarlo, ejecuta:" -ForegroundColor Yellow
        Write-Host '"C:\Program Files (x86)\Microsoft SDKs\Azure\Storage Emulator\AzureStorageEmulator.exe" start' -ForegroundColor White
    }
} catch {
    Write-Host "No se pudo verificar Azure Storage Emulator" -ForegroundColor Yellow
} 