# Script para desplegar usando FTP como alternativa al Git push
# Este método es más confiable cuando hay problemas con Git

param(
    [string]$AppServiceName = "veaconnect-webapp-prod",
    [string]$ResourceGroupName = "rg-vea-connect-dev",
    [string]$SourcePath = "."
)

Write-Host "=== DESPLIEGUE VIA FTP A AZURE APP SERVICE ===" -ForegroundColor Green

# Obtener credenciales de FTP
Write-Host "Obteniendo credenciales de FTP..." -ForegroundColor Yellow
$publishProfile = az webapp deployment list-publishing-profiles `
    --name $AppServiceName `
    --resource-group $ResourceGroupName `
    --xml 2>$null

if ($LASTEXITCODE -ne 0) {
    Write-Error "Error al obtener el perfil de publicación"
    exit 1
}

# Extraer información FTP del XML
$ftpUrl = ([regex]::Match($publishProfile, 'publishUrl="([^"]*)"')).Groups[1].Value
$ftpUsername = ([regex]::Match($publishProfile, 'userName="([^"]*)"')).Groups[1].Value
$ftpPassword = ([regex]::Match($publishProfile, 'userPWD="([^"]*)"')).Groups[1].Value

if (!$ftpUrl -or !$ftpUsername -or !$ftpPassword) {
    Write-Error "No se pudieron extraer las credenciales FTP"
    exit 1
}

Write-Host "FTP URL: $ftpUrl" -ForegroundColor Cyan
Write-Host "FTP Username: $ftpUsername" -ForegroundColor Cyan

# Crear archivo de configuración FTP
$ftpConfig = @"
open $ftpUrl
$ftpUsername
$ftpPassword
binary
prompt
"@

$ftpConfig | Out-File -FilePath "ftp_config.txt" -Encoding ASCII

# Crear ZIP del código
Write-Host "Creando paquete de despliegue..." -ForegroundColor Yellow
$tempZip = "deployment-ftp-$(Get-Date -Format 'yyyyMMdd-HHmmss').zip"

# Excluir archivos innecesarios
$excludePatterns = @(
    "*.git*",
    "*.pyc",
    "__pycache__",
    "venv",
    "node_modules",
    ".vscode",
    "*.log",
    "*.tmp",
    "ftp_config.txt"
)

# Crear el ZIP
Compress-Archive -Path "$SourcePath\*" -DestinationPath $tempZip -Force

if (!(Test-Path $tempZip)) {
    Write-Error "Error al crear el archivo ZIP de despliegue"
    exit 1
}

Write-Host "Paquete creado: $tempZip" -ForegroundColor Green

# Subir archivos via FTP
Write-Host "Subiendo archivos via FTP..." -ForegroundColor Yellow

# Crear script FTP
$ftpScript = @"
open $ftpUrl
$ftpUsername
$ftpPassword
binary
prompt
cd site/wwwroot
put $tempZip
bye
"@

$ftpScript | Out-File -FilePath "upload.ftp" -Encoding ASCII

# Ejecutar FTP
Write-Host "Ejecutando FTP..." -ForegroundColor Yellow
ftp -s:upload.ftp

if ($LASTEXITCODE -eq 0) {
    Write-Host "Despliegue completado exitosamente!" -ForegroundColor Green
    Write-Host "URL: https://$AppServiceName.azurewebsites.net" -ForegroundColor Cyan
} else {
    Write-Error "Error en el despliegue FTP"
}

# Limpiar archivos temporales
if (Test-Path $tempZip) { Remove-Item $tempZip -Force }
if (Test-Path "upload.ftp") { Remove-Item "upload.ftp" -Force }
if (Test-Path "ftp_config.txt") { Remove-Item "ftp_config.txt" -Force }

Write-Host "=== DESPLIEGUE COMPLETADO ===" -ForegroundColor Green 