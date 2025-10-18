# Script simple para configurar Docker
param(
    [string]$ResourceGroup = "rg-vea-connect-dev",
    [string]$WebAppName = "vea-connect",
    [string]$AcrName = "veaconnectacr"
)

Write-Host "Configurando imagen Docker personalizada..." -ForegroundColor Green

# Obtener password de ACR
$password = az acr credential show --name $AcrName --query "passwords[0].value" -o tsv

# Configurar contenedor
az webapp config container set `
    --name $WebAppName `
    --resource-group $ResourceGroup `
    --docker-custom-image-name "$AcrName.azurecr.io/$WebAppName:prod" `
    --docker-registry-server-url "https://$AcrName.azurecr.io" `
    --docker-registry-server-user $AcrName `
    --docker-registry-server-password $password

# Eliminar startup command
az webapp config set `
    --name $WebAppName `
    --resource-group $ResourceGroup `
    --startup-file ""

# Configurar variables basicas
az webapp config appsettings set `
    --name $WebAppName `
    --resource-group $ResourceGroup `
    --settings WEBSITES_PORT=8000 DJANGO_SETTINGS_MODULE=config.settings.production DEBUG=False

# Reiniciar
az webapp restart --name $WebAppName --resource-group $ResourceGroup

Write-Host "Configuracion completada!" -ForegroundColor Green

