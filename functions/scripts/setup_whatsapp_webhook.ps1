#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Script para configurar el webhook de WhatsApp con Event Grid

.DESCRIPTION
    Este script automatiza la configuración del webhook de WhatsApp,
    incluyendo la configuración de variables de entorno y la creación
    de la suscripción de Event Grid.

.PARAMETER FunctionAppName
    Nombre de la aplicación de funciones de Azure

.PARAMETER ResourceGroup
    Nombre del grupo de recursos

.PARAMETER CommunicationServiceName
    Nombre del servicio de comunicación de Azure

.PARAMETER SubscriptionId
    ID de la suscripción de Azure

.PARAMETER Environment
    Entorno de despliegue (dev, staging, prod)

.EXAMPLE
    .\setup_whatsapp_webhook.ps1 -FunctionAppName "vea-connect-functions" -ResourceGroup "vea-connect-rg" -CommunicationServiceName "acs-veu-connect-00" -SubscriptionId "9f47ecda-6fbc-479d-888a-a5966f0c9c50" -Environment "prod"
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$FunctionAppName,
    
    [Parameter(Mandatory=$true)]
    [string]$ResourceGroup,
    
    [Parameter(Mandatory=$true)]
    [string]$CommunicationServiceName,
    
    [Parameter(Mandatory=$true)]
    [string]$SubscriptionId,
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("dev", "staging", "prod")]
    [string]$Environment = "dev"
)

# Configurar colores para output
$Host.UI.RawUI.ForegroundColor = "White"

Write-Host "🚀 CONFIGURACIÓN DEL WEBHOOK DE WHATSAPP" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

# Verificar que Azure CLI esté instalado y conectado
Write-Host "🔍 Verificando Azure CLI..." -ForegroundColor Yellow
try {
    $account = az account show --query "user.name" -o tsv 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ No estás conectado a Azure. Ejecuta 'az login' primero." -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Conectado como: $account" -ForegroundColor Green
} catch {
    Write-Host "❌ Error verificando Azure CLI: $_" -ForegroundColor Red
    exit 1
}

# Verificar que la Function App existe
Write-Host "🔍 Verificando Function App..." -ForegroundColor Yellow
try {
    $functionApp = az functionapp show --name $FunctionAppName --resource-group $ResourceGroup --query "name" -o tsv 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Function App '$FunctionAppName' no encontrada en el grupo de recursos '$ResourceGroup'" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Function App encontrada: $functionApp" -ForegroundColor Green
} catch {
    Write-Host "❌ Error verificando Function App: $_" -ForegroundColor Red
    exit 1
}

# Verificar que el Communication Service existe
Write-Host "🔍 Verificando Communication Service..." -ForegroundColor Yellow
try {
    $commService = az communication show --name $CommunicationServiceName --resource-group $ResourceGroup --query "name" -o tsv 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Communication Service '$CommunicationServiceName' no encontrado en el grupo de recursos '$ResourceGroup'" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Communication Service encontrado: $commService" -ForegroundColor Green
} catch {
    Write-Host "❌ Error verificando Communication Service: $_" -ForegroundColor Red
    exit 1
}

# Configurar variables de entorno según el entorno
Write-Host "🔧 Configurando variables de entorno para entorno: $Environment" -ForegroundColor Yellow

$envVars = @{}

# Variables base para todos los entornos
$envVars["FUNCTIONS_WORKER_RUNTIME"] = "python"
$envVars["AZURE_OPENAI_CHAT_DEPLOYMENT"] = "gpt-35-turbo"
$envVars["AZURE_OPENAI_CHAT_API_VERSION"] = "2024-02-15-preview"
$envVars["AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT"] = "text-embedding-ada-002"
$envVars["AZURE_OPENAI_EMBEDDINGS_API_VERSION"] = "2023-05-15"
$envVars["REDIS_TTL_SECS"] = "3600"

# Configuración específica por entorno
switch ($Environment) {
    "dev" {
        $envVars["WHATSAPP_DEBUG"] = "true"
        $envVars["E2E_DEBUG"] = "true"
        $envVars["RAG_ENABLED"] = "false"
        $envVars["BOT_SYSTEM_PROMPT"] = "Eres un asistente virtual de VEA Connect en modo desarrollo. Responde de manera amigable y profesional en español. MODO DEBUG ACTIVO."
    }
    "staging" {
        $envVars["WHATSAPP_DEBUG"] = "false"
        $envVars["E2E_DEBUG"] = "true"
        $envVars["RAG_ENABLED"] = "true"
        $envVars["BOT_SYSTEM_PROMPT"] = "Eres un asistente virtual de VEA Connect en modo staging. Responde de manera amigable y profesional en español."
    }
    "prod" {
        $envVars["WHATSAPP_DEBUG"] = "false"
        $envVars["E2E_DEBUG"] = "false"
        $envVars["RAG_ENABLED"] = "true"
        $envVars["BOT_SYSTEM_PROMPT"] = "Eres un asistente virtual de VEA Connect, una plataforma de gestión para organizaciones sin fines de lucro. Tu función es ayudar a los usuarios con información sobre donaciones, eventos, documentos y servicios de la organización. Responde de manera amigable y profesional en español. Mantén las respuestas concisas pero informativas. Si no tienes información específica sobre algo, sugiere contactar al equipo de VEA Connect."
    }
}

# Solicitar variables sensibles al usuario
Write-Host "📝 Configuración de variables sensibles:" -ForegroundColor Yellow
Write-Host ""

$envVars["AZURE_OPENAI_ENDPOINT"] = Read-Host "Azure OpenAI Endpoint (ej: https://openai-veaconnect.openai.azure.com/)"
$envVars["AZURE_OPENAI_API_KEY"] = Read-Host "Azure OpenAI API Key" -AsSecureString | ConvertFrom-SecureString -AsPlainText
$envVars["ACS_WHATSAPP_ENDPOINT"] = Read-Host "ACS WhatsApp Endpoint (ej: https://acs-veu-connect-00.unitedstates.communication.azure.com/)"
$envVars["ACS_WHATSAPP_API_KEY"] = Read-Host "ACS WhatsApp API Key" -AsSecureString | ConvertFrom-SecureString -AsPlainText
$envVars["ACS_PHONE_NUMBER"] = Read-Host "ACS Phone Number (ej: +5215574908943)"
$envVars["WHATSAPP_CHANNEL_ID_GUID"] = Read-Host "WhatsApp Channel ID GUID"

# Variables opcionales
Write-Host ""
Write-Host "📝 Variables opcionales (presiona Enter para usar valores por defecto):" -ForegroundColor Yellow

$searchEndpoint = Read-Host "Azure Search Endpoint (opcional)"
if ($searchEndpoint) {
    $envVars["AZURE_SEARCH_ENDPOINT"] = $searchEndpoint
    $envVars["AZURE_SEARCH_API_KEY"] = Read-Host "Azure Search API Key" -AsSecureString | ConvertFrom-SecureString -AsPlainText
    $envVars["AZURE_SEARCH_INDEX_NAME"] = Read-Host "Azure Search Index Name"
}

# Aplicar configuración
Write-Host ""
Write-Host "🔧 Aplicando configuración a la Function App..." -ForegroundColor Yellow

try {
    # Construir comando de configuración
    $settingsArgs = @()
    foreach ($key in $envVars.Keys) {
        $value = $envVars[$key]
        $settingsArgs += "$key=`"$value`""
    }
    
    $settingsString = $settingsArgs -join " "
    $command = "az functionapp config appsettings set --name $FunctionAppName --resource-group $ResourceGroup --settings $settingsString"
    
    Write-Host "Ejecutando: $command" -ForegroundColor Gray
    
    # Ejecutar comando
    Invoke-Expression $command
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Variables de entorno configuradas correctamente" -ForegroundColor Green
    } else {
        Write-Host "❌ Error configurando variables de entorno" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Error aplicando configuración: $_" -ForegroundColor Red
    exit 1
}

# Crear suscripción de Event Grid
Write-Host ""
Write-Host "🔗 Creando suscripción de Event Grid..." -ForegroundColor Yellow

try {
    $sourceResourceId = "/subscriptions/$SubscriptionId/resourceGroups/$ResourceGroup/providers/Microsoft.Communication/communicationServices/$CommunicationServiceName"
    $endpointResourceId = "/subscriptions/$SubscriptionId/resourceGroups/$ResourceGroup/providers/Microsoft.Web/sites/$FunctionAppName/functions/whatsapp_event_grid_trigger"
    
    $eventGridCommand = "az eventgrid event-subscription create --source-resource-id `"$sourceResourceId`" --name `"whatsapp-webhook-$Environment`" --endpoint-type `"azurefunction`" --endpoint `"$endpointResourceId`" --included-event-types `"Microsoft.Communication.AdvancedMessageReceived`""
    
    Write-Host "Ejecutando: $eventGridCommand" -ForegroundColor Gray
    
    Invoke-Expression $eventGridCommand
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Suscripción de Event Grid creada correctamente" -ForegroundColor Green
    } else {
        Write-Host "❌ Error creando suscripción de Event Grid" -ForegroundColor Red
        Write-Host "Puede que ya exista una suscripción con el mismo nombre" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Error creando suscripción de Event Grid: $_" -ForegroundColor Red
}

# Verificar configuración
Write-Host ""
Write-Host "🔍 Verificando configuración..." -ForegroundColor Yellow

try {
    $currentSettings = az functionapp config appsettings list --name $FunctionAppName --resource-group $ResourceGroup --query "[?name=='AZURE_OPENAI_ENDPOINT'].value" -o tsv 2>$null
    
    if ($currentSettings) {
        Write-Host "✅ Configuración verificada correctamente" -ForegroundColor Green
    } else {
        Write-Host "⚠️ No se pudo verificar la configuración" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️ Error verificando configuración: $_" -ForegroundColor Yellow
}

# Mostrar resumen
Write-Host ""
Write-Host "📋 RESUMEN DE CONFIGURACIÓN" -ForegroundColor Cyan
Write-Host "============================" -ForegroundColor Cyan
Write-Host "Function App: $FunctionAppName" -ForegroundColor White
Write-Host "Grupo de Recursos: $ResourceGroup" -ForegroundColor White
Write-Host "Communication Service: $CommunicationServiceName" -ForegroundColor White
Write-Host "Entorno: $Environment" -ForegroundColor White
Write-Host "Suscripción Event Grid: whatsapp-webhook-$Environment" -ForegroundColor White
Write-Host ""

Write-Host "🎉 Configuración completada exitosamente!" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Próximos pasos:" -ForegroundColor Yellow
Write-Host "1. Desplegar la función: func azure functionapp publish $FunctionAppName" -ForegroundColor White
Write-Host "2. Probar el webhook: python test_whatsapp_webhook.py" -ForegroundColor White
Write-Host "3. Verificar logs: az webapp log tail --name $FunctionAppName --resource-group $ResourceGroup" -ForegroundColor White
Write-Host ""

Write-Host "📚 Documentación: functions/docs/WHATSAPP_WEBHOOK_GUIDE.md" -ForegroundColor Cyan
