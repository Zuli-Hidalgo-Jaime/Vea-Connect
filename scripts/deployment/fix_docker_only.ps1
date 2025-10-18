# Script que SOLO configura Docker sin tocar variables
param(
    [string]$ResourceGroup = "rg-vea-connect-dev",
    [string]$WebAppName = "vea-connect",
    [string]$AcrName = "veaconnectacr"
)

Write-Host "Configurando SOLO imagen Docker personalizada..." -ForegroundColor Green

# Obtener password de ACR
$password = az acr credential show --name $AcrName --query "passwords[0].value" -o tsv

Write-Host "Configurando contenedor Docker personalizado..." -ForegroundColor Yellow

# Configurar contenedor
az webapp config container set `
    --name $WebAppName `
    --resource-group $ResourceGroup `
    --container-image-name "$AcrName.azurecr.io/$WebAppName:prod" `
    --container-registry-url "https://$AcrName.azurecr.io" `
    --container-registry-user $AcrName `
    --container-registry-password $password

Write-Host "Eliminando STARTUP_COMMAND..." -ForegroundColor Yellow

# Eliminar startup command
az webapp config set `
    --name $WebAppName `
    --resource-group $ResourceGroup `
    --startup-file ""

Write-Host "Reiniciando aplicacion..." -ForegroundColor Yellow

# Reiniciar
az webapp restart --name $WebAppName --resource-group $ResourceGroup

Write-Host "Configuracion completada! Variables NO fueron tocadas." -ForegroundColor Green
