# Script to rebuild and deploy Docker container
param(
    [string]$ResourceGroup = "vea-connect-rg",
    [string]$WebAppName = "vea-connect-g5dje9eba9bscnb6",
    [string]$AcrName = "veaconnectacr"
)

Write-Host "DOCKER CONTAINER REBUILD AND DEPLOY" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

# Check if Docker is running
Write-Host "Checking Docker status..." -ForegroundColor Yellow
try {
    docker version | Out-Null
    Write-Host "Docker is running" -ForegroundColor Green
} catch {
    Write-Host "Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Login to Azure Container Registry
Write-Host "Logging in to Azure Container Registry..." -ForegroundColor Yellow
try {
    az acr login --name $AcrName
    Write-Host "Login successful" -ForegroundColor Green
} catch {
    Write-Host "Failed to login to ACR" -ForegroundColor Red
    exit 1
}

# Build new Docker image
Write-Host "Building new Docker image..." -ForegroundColor Yellow
$imageTag = "$AcrName.azurecr.io/$WebAppName`:latest"
try {
    docker build -t $imageTag .
    Write-Host "Image built successfully" -ForegroundColor Green
} catch {
    Write-Host "Failed to build image" -ForegroundColor Red
    exit 1
}

# Push image to ACR
Write-Host "Pushing image to Azure Container Registry..." -ForegroundColor Yellow
try {
    docker push $imageTag
    Write-Host "Image pushed successfully" -ForegroundColor Green
} catch {
    Write-Host "Failed to push image" -ForegroundColor Red
    exit 1
}

# Restart Web App
Write-Host "Restarting Web App to use new image..." -ForegroundColor Yellow
try {
    az webapp restart --name $WebAppName --resource-group $ResourceGroup
    Write-Host "Web App restarted successfully" -ForegroundColor Green
} catch {
    Write-Host "Failed to restart Web App" -ForegroundColor Red
    exit 1
}

Write-Host "DEPLOYMENT COMPLETED SUCCESSFULLY" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Green
Write-Host "Your application should be updated in a few minutes." -ForegroundColor White
