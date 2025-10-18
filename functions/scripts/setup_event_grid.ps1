# Script para configurar Event Grid Topic y suscripción para WhatsApp Events
# Ejecutar desde el directorio functions/

param(
    [string]$ResourceGroupName = "rg-vea-connect-dev",
    [string]$TopicName = "veaconnect-whatsapp-events",
    [string]$FunctionAppName = "vea-functions-apis",
    [string]$Location = "Central US"
)

Write-Host "🚀 Configurando Event Grid para WhatsApp Events..." -ForegroundColor Green

# Verificar Azure CLI
Write-Host "Verificando Azure CLI..." -ForegroundColor Yellow
try {
    $azVersion = az version --output json | ConvertFrom-Json
    Write-Host "Azure CLI version: $($azVersion.'azure-cli')" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: Azure CLI no está instalado" -ForegroundColor Red
    exit 1
}

# Verificar autenticación
Write-Host "Verificando autenticación..." -ForegroundColor Yellow
try {
    $account = az account show --output json | ConvertFrom-Json
    Write-Host "Autenticado como: $($account.user.name)" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: No estás autenticado. Ejecuta: az login" -ForegroundColor Red
    exit 1
}

# 1. Crear Event Grid Topic
Write-Host "📋 Creando Event Grid Topic: $TopicName" -ForegroundColor Yellow
try {
    $topicResult = az eventgrid topic create `
        --name $TopicName `
        --resource-group $ResourceGroupName `
        --location $Location `
        --output json | ConvertFrom-Json
    
    Write-Host "✅ Event Grid Topic creado exitosamente" -ForegroundColor Green
    Write-Host "   Nombre: $($topicResult.name)" -ForegroundColor Cyan
    Write-Host "   Endpoint: $($topicResult.endpoint)" -ForegroundColor Cyan
} catch {
    Write-Host "❌ Error creando Event Grid Topic: $_" -ForegroundColor Red
    exit 1
}

# 2. Obtener la URL del endpoint de la función
Write-Host "🔗 Obteniendo URL del endpoint de la función..." -ForegroundColor Yellow
$functionEndpoint = "https://$FunctionAppName.azurewebsites.net/runtime/webhooks/eventgrid?functionName=whatsapp_event_grid_trigger"
Write-Host "   Endpoint de función: $functionEndpoint" -ForegroundColor Cyan

# 3. Crear Event Grid Subscription
Write-Host "📋 Creando Event Grid Subscription..." -ForegroundColor Yellow
try {
    $subscriptionName = "whatsapp-events-subscription"
    
    $subscriptionResult = az eventgrid event-subscription create `
        --name $subscriptionName `
        --source-resource-id "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$ResourceGroupName/providers/Microsoft.EventGrid/topics/$TopicName" `
        --endpoint-type azurefunction `
        --endpoint $functionEndpoint `
        --included-event-types "Microsoft.Communication.AdvancedMessageReceived" "Microsoft.Communication.AdvancedMessageDeliveryReportReceived" `
        --output json | ConvertFrom-Json
    
    Write-Host "✅ Event Grid Subscription creado exitosamente" -ForegroundColor Green
    Write-Host "   Nombre: $($subscriptionResult.name)" -ForegroundColor Cyan
    Write-Host "   Endpoint: $($subscriptionResult.destination.endpointUrl)" -ForegroundColor Cyan
} catch {
    Write-Host "❌ Error creando Event Grid Subscription: $_" -ForegroundColor Red
    exit 1
}

# 4. Configurar variables de entorno en la Function App
Write-Host "🔧 Configurando variables de entorno en la Function App..." -ForegroundColor Yellow
try {
    $eventGridEndpoint = $topicResult.endpoint
    $eventGridKey = az eventgrid topic key list --name $TopicName --resource-group $ResourceGroupName --query "key1" -o tsv
    
    az webapp config appsettings set `
        --name $FunctionAppName `
        --resource-group $ResourceGroupName `
        --settings `
        EVENT_GRID_TOPIC_ENDPOINT="$eventGridEndpoint" `
        EVENT_GRID_TOPIC_KEY="$eventGridKey" `
        EVENT_GRID_VALIDATION_KEY="$eventGridKey"
    
    Write-Host "✅ Variables de entorno configuradas" -ForegroundColor Green
} catch {
    Write-Host "❌ Error configurando variables de entorno: $_" -ForegroundColor Red
}

# 5. Verificar la configuración
Write-Host "🔍 Verificando configuración..." -ForegroundColor Yellow
try {
    # Verificar que el topic existe
    $topicCheck = az eventgrid topic show --name $TopicName --resource-group $ResourceGroupName --output json | ConvertFrom-Json
    Write-Host "✅ Topic verificado: $($topicCheck.name)" -ForegroundColor Green
    
    # Verificar que la suscripción existe
    $subscriptionCheck = az eventgrid event-subscription show --name $subscriptionName --source-resource-id "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$ResourceGroupName/providers/Microsoft.EventGrid/topics/$TopicName" --output json | ConvertFrom-Json
    Write-Host "✅ Subscription verificado: $($subscriptionCheck.name)" -ForegroundColor Green
    
} catch {
    Write-Host "❌ Error verificando configuración: $_" -ForegroundColor Red
}

# 6. Mostrar información de configuración
Write-Host "📊 Configuración completada:" -ForegroundColor Green
Write-Host "   Topic: $TopicName" -ForegroundColor Cyan
Write-Host "   Endpoint: $($topicResult.endpoint)" -ForegroundColor Cyan
Write-Host "   Subscription: $subscriptionName" -ForegroundColor Cyan
Write-Host "   Function Endpoint: $functionEndpoint" -ForegroundColor Cyan

Write-Host "🎉 Configuración de Event Grid completada exitosamente!" -ForegroundColor Green
Write-Host "💡 Para probar, envía un mensaje de WhatsApp y verifica los logs de la función." -ForegroundColor Yellow 