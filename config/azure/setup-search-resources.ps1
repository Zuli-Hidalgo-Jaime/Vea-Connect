# VEA Connect - Configuración de Azure AI Search
# Este script configura el índice, skillset, datasource e indexer

param(
    [Parameter(Mandatory=$true)]
    [string]$SearchServiceName,
    
    [Parameter(Mandatory=$true)]
    [string]$SearchServiceKey,
    
    [Parameter(Mandatory=$true)]
    [string]$StorageConnectionString,
    
    [Parameter(Mandatory=$true)]
    [string]$CognitiveServicesKey
)

$SearchEndpoint = "https://$SearchServiceName.search.windows.net"

Write-Host "VEA Connect - Configurando Azure AI Search..." -ForegroundColor Green

# Función para hacer peticiones a Azure AI Search
function Invoke-SearchAPI {
    param(
        [string]$Method,
        [string]$Uri,
        [string]$Body = $null
    )
    
    $Headers = @{
        "api-key" = $SearchServiceKey
        "Content-Type" = "application/json"
    }
    
    try {
        if ($Body) {
            $Response = Invoke-RestMethod -Uri $Uri -Method $Method -Headers $Headers -Body $Body
        } else {
            $Response = Invoke-RestMethod -Uri $Uri -Method $Method -Headers $Headers
        }
        return $Response
    }
    catch {
        Write-Error "Error en petición a $Uri`: $($_.Exception.Message)"
        return $null
    }
}

# 1. Crear Data Source
Write-Host "Creando Data Source..." -ForegroundColor Yellow
$DataSourceUri = "$SearchEndpoint/datasources/vea-connect-datasource?api-version=2023-11-01"

$DataSourceBody = @{
    name = "vea-connect-datasource"
    description = "Fuente de datos de Azure Blob Storage para VEA Connect"
    type = "azureblob"
    credentials = @{
        connectionString = $StorageConnectionString
    }
    container = @{
        name = "admin-documentos"
    }
} | ConvertTo-Json -Depth 10

$DataSourceResult = Invoke-SearchAPI -Method "PUT" -Uri $DataSourceUri -Body $DataSourceBody
if ($DataSourceResult) {
    Write-Host "Data Source creado exitosamente" -ForegroundColor Green
} else {
    Write-Host "Error al crear Data Source" -ForegroundColor Red
    exit 1
}

# 2. Crear Skillset
Write-Host "Creando Skillset..." -ForegroundColor Yellow
$SkillsetUri = "$SearchEndpoint/skillsets/vea-connect-skillset?api-version=2023-11-01"

# Leer el archivo JSON del skillset
$SkillsetJson = Get-Content "vea-connect-skillset.json" -Raw
$SkillsetObject = $SkillsetJson | ConvertFrom-Json
$SkillsetObject.cognitiveServices.key = $CognitiveServicesKey
$SkillsetBody = $SkillsetObject | ConvertTo-Json -Depth 10

$SkillsetResult = Invoke-SearchAPI -Method "PUT" -Uri $SkillsetUri -Body $SkillsetBody
if ($SkillsetResult) {
    Write-Host "Skillset creado exitosamente" -ForegroundColor Green
} else {
    Write-Host "Error al crear Skillset" -ForegroundColor Red
    exit 1
}

# 3. Crear Index
Write-Host "Creando Index..." -ForegroundColor Yellow
$IndexUri = "$SearchEndpoint/indexes/vea-connect-index?api-version=2023-11-01"

# Leer el archivo JSON del índice
$IndexJson = Get-Content "vea-connect-index.json" -Raw
$IndexBody = $IndexJson

$IndexResult = Invoke-SearchAPI -Method "PUT" -Uri $IndexUri -Body $IndexBody
if ($IndexResult) {
    Write-Host "Index creado exitosamente" -ForegroundColor Green
} else {
    Write-Host "Error al crear Index" -ForegroundColor Red
    exit 1
}

# 4. Crear Indexer
Write-Host "Creando Indexer..." -ForegroundColor Yellow
$IndexerUri = "$SearchEndpoint/indexers/vea-connect-indexer?api-version=2023-11-01"

# Leer el archivo JSON del indexer
$IndexerJson = Get-Content "vea-connect-indexer.json" -Raw
$IndexerBody = $IndexerJson

$IndexerResult = Invoke-SearchAPI -Method "PUT" -Uri $IndexerUri -Body $IndexerBody
if ($IndexerResult) {
    Write-Host "Indexer creado exitosamente" -ForegroundColor Green
} else {
    Write-Host "Error al crear Indexer" -ForegroundColor Red
    exit 1
}

# 5. Ejecutar Indexer
Write-Host "Ejecutando Indexer..." -ForegroundColor Yellow
$RunIndexerUri = "$SearchEndpoint/indexers/vea-connect-indexer/run?api-version=2023-11-01"

$RunResult = Invoke-SearchAPI -Method "POST" -Uri $RunIndexerUri
if ($RunResult) {
    Write-Host "Indexer ejecutado exitosamente" -ForegroundColor Green
} else {
    Write-Host "Error al ejecutar Indexer" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Configuración de Azure AI Search completada!" -ForegroundColor Green
Write-Host "Puedes verificar el estado del indexer en el portal de Azure" -ForegroundColor Cyan
Write-Host "Endpoint de búsqueda: $SearchEndpoint" -ForegroundColor Cyan
Write-Host "Índice: vea-connect-index" -ForegroundColor Cyan




