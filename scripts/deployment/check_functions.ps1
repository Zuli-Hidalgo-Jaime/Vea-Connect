# Script para verificar el estado de las Azure Functions
# Verifica si las funciones estan desplegadas y funcionando

param(
    [string]$ResourceGroupName = "rg-vea-connect-dev"
)

Write-Host "Verificando estado de las Azure Functions..."

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

# Listar todas las Function Apps en el Resource Group
Write-Host "Buscando Function Apps en el Resource Group..."
try {
    $functionApps = az functionapp list --resource-group $ResourceGroupName --output json | ConvertFrom-Json
    Write-Host "Function Apps encontradas: $($functionApps.Count)"
    
    foreach ($app in $functionApps) {
        Write-Host ""
        Write-Host "=== Function App: $($app.name) ==="
        Write-Host "Estado: $($app.state)"
        Write-Host "Runtime: $($app.kind)"
        Write-Host "URL: $($app.defaultHostName)"
        
        # Verificar funciones en esta Function App
        try {
            $functions = az functionapp function list --name $app.name --resource-group $ResourceGroupName --output json | ConvertFrom-Json
            Write-Host "Funciones encontradas: $($functions.Count)"
            
            foreach ($function in $functions) {
                Write-Host "  - $($function.name) (Estado: $($function.config.bindings[0].type))"
            }
        } catch {
            Write-Host "  Error obteniendo funciones: $_"
        }
    }
} catch {
    Write-Host "Error listando Function Apps: $_"
}

# Verificar funciones especificas que deberian existir
Write-Host ""
Write-Host "=== Verificando funciones especificas ==="

$expectedFunctions = @(
    "embedding_api_function"
)

foreach ($functionName in $expectedFunctions) {
    Write-Host "Buscando funcion: $functionName"
    try {
        # Buscar en todas las Function Apps
        $found = $false
        foreach ($app in $functionApps) {
            try {
                $functions = az functionapp function list --name $app.name --resource-group $ResourceGroupName --output json | ConvertFrom-Json
                $function = $functions | Where-Object { $_.name -eq $functionName }
                if ($function) {
                    Write-Host "  ✓ Encontrada en: $($app.name)"
                    $found = $true
                    break
                }
            } catch {
                # Continuar con la siguiente Function App
            }
        }
        
        if (-not $found) {
            Write-Host "  ✗ No encontrada"
        }
    } catch {
        Write-Host "  Error verificando funcion: $_"
    }
}

# Verificar logs de las funciones
Write-Host ""
Write-Host "=== Verificando logs de funciones ==="
Write-Host "Para ver logs en tiempo real, ejecuta:"
Write-Host "az webapp log tail --name <function-app-name> --resource-group $ResourceGroupName"

Write-Host ""
Write-Host "=== Verificacion completada ===" 