# Script para encontrar manage.py y ejecutar migraciones
# Busca el archivo manage.py en la Web App y ejecuta las migraciones

param(
    [string]$ResourceGroupName = "rg-vea-connect-dev",
    [string]$AppName = "veaconnect-webapp-prod"
)

Write-Host "Buscando manage.py y ejecutando migraciones..."

# Verificar Azure CLI
Write-Host "Verificando Azure CLI..."
try {
    $azVersion = az version --output json | ConvertFrom-Json
    Write-Host "Azure CLI version: $($azVersion.'azure-cli')"
} catch {
    Write-Host "Error: Azure CLI no esta instalado"
    exit 1
}

# Verificar autenticacion
Write-Host "Verificando autenticacion..."
try {
    $account = az account show --output json | ConvertFrom-Json
    Write-Host "Autenticado como: $($account.user.name)"
} catch {
    Write-Host "Error: No estas autenticado. Ejecuta: az login"
    exit 1
}

Write-Host "Conectando a la Web App..."
Write-Host "Una vez conectado, ejecuta estos comandos:"
Write-Host ""
Write-Host "1. Buscar manage.py:"
Write-Host "   find /home -name 'manage.py' -type f"
Write-Host ""
Write-Host "2. Ir al directorio donde esta manage.py:"
Write-Host "   cd /ruta/encontrada/por/find"
Write-Host ""
Write-Host "3. Ejecutar migraciones:"
Write-Host "   python manage.py migrate"
Write-Host ""
Write-Host "4. Crear superusuario:"
Write-Host "   python manage.py createsuperuser"
Write-Host ""
Write-Host "5. Salir:"
Write-Host "   exit"
Write-Host ""

# Conectar a la Web App
try {
    az webapp ssh --resource-group $ResourceGroupName --name $AppName
} catch {
    Write-Host "Error conectando a la Web App: $_"
    Write-Host "Puedes acceder manualmente al portal de Azure:"
    Write-Host "1. Ve al portal de Azure"
    Write-Host "2. Busca tu Web App"
    Write-Host "3. Ve a 'Development Tools' > 'SSH'"
    Write-Host "4. Ejecuta los comandos mostrados arriba"
} 