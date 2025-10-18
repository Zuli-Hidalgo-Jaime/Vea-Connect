# Script de PowerShell para probar Azure Functions
# Ejecutar desde el directorio functions/

param(
    [string]$BaseUrl = "http://localhost:7074/api",
    [int]$Timeout = 15
)

Write-Host "🚀 Iniciando pruebas de Azure Functions..." -ForegroundColor Green
Write-Host "URL base: $BaseUrl" -ForegroundColor Cyan
Write-Host "Timeout: $Timeout segundos" -ForegroundColor Cyan
Write-Host ""

# Función para hacer requests HTTP
function Invoke-FunctionTest {
    param(
        [string]$Url,
        [string]$Method = "GET",
        [object]$Body = $null,
        [string]$Description = ""
    )
    
    try {
        $headers = @{
            "Content-Type" = "application/json"
        }
        
        $params = @{
            Uri = $Url
            Method = $Method
            Headers = $headers
            TimeoutSec = $Timeout
        }
        
        if ($Body) {
            $params.Body = $Body | ConvertTo-Json -Depth 10
        }
        
        Write-Host "Probando $Description..." -ForegroundColor Yellow
        Write-Host "URL: $Url" -ForegroundColor Gray
        
        $response = Invoke-RestMethod @params -ErrorAction Stop
        
        Write-Host "✓ $Description - OK" -ForegroundColor Green
        Write-Host "Respuesta: $($response | ConvertTo-Json -Depth 5)" -ForegroundColor White
        return $true
        
    } catch {
        Write-Host "✗ $Description - Error: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.Exception.Response) {
            Write-Host "Status: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
        }
        return $false
    }
    Write-Host ""
}

# Resultados de las pruebas
$results = @{
    Health = @{}
    Embeddings = @{}
    WhatsApp = @{}
}

# 1. Probar Health Checks
Write-Host "=== Probando Health Checks ===" -ForegroundColor Magenta

$healthEndpoints = @(
    @{Url = "$BaseUrl/health"; Description = "Health Check Principal"},
    @{Url = "$BaseUrl/embeddings/health"; Description = "Health Check Embeddings"},
    @{Url = "$BaseUrl/whatsapp/health"; Description = "Health Check WhatsApp"}
)

foreach ($endpoint in $healthEndpoints) {
    $success = Invoke-FunctionTest -Url $endpoint.Url -Description $endpoint.Description
    $results.Health[$endpoint.Description] = $success
}

# 2. Probar Funciones de Embeddings
Write-Host "=== Probando Funciones de Embeddings ===" -ForegroundColor Magenta

# Stats
$success = Invoke-FunctionTest -Url "$BaseUrl/embeddings/stats" -Description "Embeddings Stats"
$results.Embeddings["Stats"] = $success

# Create
$createBody = @{
    text = "Este es un texto de prueba para verificar que las funciones de embeddings funcionan correctamente."
    metadata = @{
        source = "test"
        category = "technology"
        language = "es"
        timestamp = [DateTimeOffset]::Now.ToUnixTimeSeconds()
        test_id = "test_001"
    }
}
$success = Invoke-FunctionTest -Url "$BaseUrl/embeddings/create" -Method "POST" -Body $createBody -Description "Create Embedding"
$results.Embeddings["Create"] = $success

# Search
$searchBody = @{
    query = "tecnología desarrollo software"
    top_k = 3
}
$success = Invoke-FunctionTest -Url "$BaseUrl/embeddings/search" -Method "POST" -Body $searchBody -Description "Search Embeddings"
$results.Embeddings["Search"] = $success

# 3. Probar Funciones de WhatsApp
Write-Host "=== Probando Funciones de WhatsApp ===" -ForegroundColor Magenta

# Stats
$success = Invoke-FunctionTest -Url "$BaseUrl/whatsapp/stats" -Description "WhatsApp Stats"
$results.WhatsApp["Stats"] = $success

# Test
$testBody = @{
    message = "Mensaje de prueba desde las funciones de Azure"
    phone_number = "+15558100642"
    test_mode = $true
}
$success = Invoke-FunctionTest -Url "$BaseUrl/whatsapp/test" -Method "POST" -Body $testBody -Description "WhatsApp Test"
$results.WhatsApp["Test"] = $success

# Event Grid (simulación)
$eventGridBody = @{
    topic = "/subscriptions/test/resourceGroups/test/providers/Microsoft.Communication/CommunicationServices/test"
    subject = "/phonenumbers/+15558100642"
    eventType = "Microsoft.Communication.SMSReceived"
    eventTime = "2024-01-01T00:00:00.0000000Z"
    id = "test-event-id"
    data = @{
        messageId = "test-message-id"
        from = "+1234567890"
        to = "+15558100642"
        message = "Mensaje de prueba desde Event Grid"
        receivedTimestamp = "2024-01-01T00:00:00.0000000Z"
    }
    dataVersion = "2.0"
}
$success = Invoke-FunctionTest -Url "$BaseUrl/whatsapp/event-grid" -Method "POST" -Body $eventGridBody -Description "WhatsApp Event Grid"
$results.WhatsApp["EventGrid"] = $success

# Resumen de resultados
Write-Host "=== Resumen de Pruebas ===" -ForegroundColor Magenta

$totalTests = 0
$passedTests = 0

Write-Host "`nHealth Checks:" -ForegroundColor Cyan
foreach ($test in $results.Health.GetEnumerator()) {
    $totalTests++
    if ($test.Value) { $passedTests++ }
    $status = if ($test.Value) { "✓" } else { "✗" }
    Write-Host "  $status $($test.Key)" -ForegroundColor $(if ($test.Value) { "Green" } else { "Red" })
}

Write-Host "`nEmbeddings:" -ForegroundColor Cyan
foreach ($test in $results.Embeddings.GetEnumerator()) {
    $totalTests++
    if ($test.Value) { $passedTests++ }
    $status = if ($test.Value) { "✓" } else { "✗" }
    Write-Host "  $status $($test.Key)" -ForegroundColor $(if ($test.Value) { "Green" } else { "Red" })
}

Write-Host "`nWhatsApp:" -ForegroundColor Cyan
foreach ($test in $results.WhatsApp.GetEnumerator()) {
    $totalTests++
    if ($test.Value) { $passedTests++ }
    $status = if ($test.Value) { "✓" } else { "✗" }
    Write-Host "  $status $($test.Key)" -ForegroundColor $(if ($test.Value) { "Green" } else { "Red" })
}

Write-Host "`nEstadísticas:" -ForegroundColor Yellow
Write-Host "Total de pruebas: $totalTests" -ForegroundColor White
Write-Host "Pruebas exitosas: $passedTests" -ForegroundColor Green
Write-Host "Pruebas fallidas: $($totalTests - $passedTests)" -ForegroundColor Red
Write-Host "Tasa de éxito: $([math]::Round(($passedTests / $totalTests) * 100, 1))%" -ForegroundColor White

if ($passedTests -eq $totalTests) {
    Write-Host "`n🎉 ¡Todas las pruebas fueron exitosas!" -ForegroundColor Green
    Write-Host "✅ Las funciones están funcionando correctamente." -ForegroundColor Green
    exit 0
} else {
    Write-Host "`n⚠️  $($totalTests - $passedTests) prueba(s) fallaron." -ForegroundColor Yellow
    Write-Host "🔧 Revisa la configuración y los logs para más detalles." -ForegroundColor Yellow
    exit 1
} 