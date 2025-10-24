# Preflight de producción (idempotente, conservador)
# - Descubre estado actual (imagen y app settings) y los guarda en .backup/
# - Verifica puerto/runtimes mínimos y variables críticas usadas por el código
# - No cambia lógica de la app. Solo fija WEBSITES_PORT=8000 si falta

Param(
  [string]$ResourceGroup = "rg-vea-prod",
  [string]$AppName       = "vea-webapp-prod",
  [string]$SearchService = "",                   # p.ej. vea-search-prod (opcional)
  [string]$SearchIndex   = "vea-connect-index"   # índice esperado
)

Write-Host "=== Preflight: $AppName ==="

# Preparar carpeta de backup
New-Item -ItemType Directory -Force -Path ".backup" | Out-Null

function Invoke-AzJson {
  Param([string]$Cmd)
  try {
    $out = Invoke-Expression $Cmd
    if ($LASTEXITCODE -ne 0) { throw "Command failed: $Cmd" }
    return ($out | ConvertFrom-Json)
  } catch {
    Write-Warning $_
    return $null
  }
}

function Get-AppSettings {
  $json = az webapp config appsettings list -g $ResourceGroup -n $AppName 2>$null
  if (-not $json) { Write-Warning "No se pudieron leer App Settings (¿az login? permisos?)"; return @() }
  $arr = $json | ConvertFrom-Json
  return $arr
}

function Get-AppSetting {
  param([string]$name)
  $v = $global:AppSettings | Where-Object { $_.name -eq $name } | Select-Object -First 1
  return ($v.value)
}

# 1) Imagen actual del contenedor
try {
  $imageName = az webapp config container show -g $ResourceGroup -n $AppName --query "imageName" -o tsv 2>$null
  if (-not [string]::IsNullOrEmpty($imageName)) {
    Set-Content -Path ".backup/current_image.txt" -Value $imageName -Encoding ASCII
    Write-Host "Imagen actual: $imageName (guardada en .backup/current_image.txt)"
  } else {
    Write-Warning "No se pudo obtener imageName (¿App Service en modo código?)"
  }
} catch {
  Write-Warning "No se pudo leer contenedor actual: $_"
}

# 2) App settings actuales (backup)
try {
  az webapp config appsettings list -g $ResourceGroup -n $AppName -o json > ".backup/appsettings.json"
  Write-Host "App settings guardados en .backup/appsettings.json"
} catch {
  Write-Warning "No se pudieron exportar App Settings: $_"
}

# 3) Cargar App Settings en memoria
$global:AppSettings = Get-AppSettings

# 4) Asegurar WEBSITES_PORT (solo si falta)
$wsPort = Get-AppSetting 'WEBSITES_PORT'
if (-not $wsPort) {
  Write-Host "Fijando WEBSITES_PORT=8000 (no existía)"
  az webapp config appsettings set -g $ResourceGroup -n $AppName --settings WEBSITES_PORT="8000" | Out-Null
  $global:AppSettings = Get-AppSettings
} else {
  Write-Host "WEBSITES_PORT presente: $wsPort"
}

function Show-Check {
  param([string]$name,[bool]$ok,[string]$note="")
  $state = if ($ok) { "OK" } else { "FAIL" }
  if ($note) { Write-Host ("{0,-36} {1,-5} {2}" -f $name,$state,$note) } else { Write-Host ("{0,-36} {1}" -f $name,$state) }
}

Write-Host "-- Variables críticas (solo ACS, Search, Storage, Django) --"

# ACS (proveedor activo)
$acsEndpoint = Get-AppSetting 'ACS_WHATSAPP_ENDPOINT'
$acsApiKey   = Get-AppSetting 'ACS_WHATSAPP_API_KEY'
$acsPhone    = Get-AppSetting 'ACS_PHONE_NUMBER'
$acsChan     = Get-AppSetting 'WHATSAPP_CHANNEL_ID_GUID'

Show-Check 'ACS_WHATSAPP_ENDPOINT' ([bool]$acsEndpoint)
Show-Check 'ACS_WHATSAPP_API_KEY'  ([bool]$acsApiKey)
Show-Check 'ACS_PHONE_NUMBER'      ([bool]$acsPhone)
Show-Check 'WHATSAPP_CHANNEL_ID_GUID' ([bool]$acsChan)

# Validación formato del número (whatsapp:+E164)
if ($acsPhone) {
  $okFmt = $false
  if ($acsPhone -like 'whatsapp:*') {
    $num = $acsPhone.Substring(9)
    if ($num -match '^\+?\d{8,15}$') { $okFmt = $true }
  }
  Show-Check 'ACS_PHONE_NUMBER format' $okFmt 'esperado: whatsapp:+<E164>'
}

# Azure Search
$searchEndpoint = (Get-AppSetting 'AZURE_SEARCH_ENDPOINT')
$searchApiKey   = (Get-AppSetting 'AZURE_SEARCH_API_KEY'); if (-not $searchApiKey) { $searchApiKey = Get-AppSetting 'AZURE_SEARCH_KEY' }
$searchIndex    = (Get-AppSetting 'AZURE_SEARCH_INDEX_NAME')
$semanticCfg    = (Get-AppSetting 'AZURE_SEARCH_SEMANTIC_CONFIG')

Show-Check 'AZURE_SEARCH_ENDPOINT'  ([bool]$searchEndpoint)
Show-Check 'AZURE_SEARCH_API_KEY'   ([bool]$searchApiKey) 'o AZURE_SEARCH_KEY'
Show-Check 'AZURE_SEARCH_INDEX_NAME'([bool]$searchIndex)
Show-Check 'AZURE_SEARCH_SEMANTIC_CONFIG' ([bool]$semanticCfg) 'esperado: vea-semantic'

# Storage (precedencia observada en código)
$hasConnStr = [bool](Get-AppSetting 'AZURE_STORAGE_CONNECTION_STRING')
$hasAccKey  = [bool]((Get-AppSetting 'AZURE_STORAGE_ACCOUNT_NAME') -and (Get-AppSetting 'AZURE_STORAGE_ACCOUNT_KEY'))
$hasBlob    = [bool]((Get-AppSetting 'BLOB_ACCOUNT_NAME') -or (Get-AppSetting 'BLOB_CONTAINER_NAME'))
Show-Check 'STORAGE: ConnectionString' $hasConnStr
Show-Check 'STORAGE: Account+Key'      $hasAccKey
Show-Check 'STORAGE: BLOB_* fallback'  $hasBlob
Write-Host "Precedencia efectiva: AZURE_STORAGE_CONNECTION_STRING > AZURE_STORAGE_ACCOUNT_* > BLOB_*"

# Django/App
Show-Check 'DJANGO_SETTINGS_MODULE' ([bool](Get-AppSetting 'DJANGO_SETTINGS_MODULE'))
Show-Check 'SECRET_KEY'             ([bool](Get-AppSetting 'SECRET_KEY'))
Show-Check 'DEBUG'                  ([bool](Get-AppSetting 'DEBUG'))
Show-Check 'ALLOWED_HOSTS'          ([bool](Get-AppSetting 'ALLOWED_HOSTS'))

# Opcional: verificar config semántica del índice en Azure Search
if ($SearchService -and $searchIndex) {
  try {
    az extension add --name search --only-show-errors | Out-Null
    $cfgs = az search index show -g $ResourceGroup --service-name $SearchService -n $SearchIndex --query "semanticSettings.configurations[].name" -o tsv 2>$null
    if ($cfgs) {
      $hasVea = ($cfgs -split "\r?\n") -contains 'vea-semantic'
      Show-Check 'Search semantic config in index' $hasVea ("configs: " + ($cfgs -join ','))
      if (-not $hasVea) { Write-Host "Fallback: el código usará búsqueda simple/vectorial si no hay semántico" }
    } else {
      Show-Check 'Search semantic config in index' $false 'no se pudo leer o vacío'
    }
  } catch {
    Write-Warning "No se pudo verificar semanticSettings (extension/search CLI): $_"
  }
}

Write-Host "=== Preflight terminado ==="


