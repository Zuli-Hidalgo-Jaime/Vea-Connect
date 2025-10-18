# Script de despliegue Git final
# Obtiene la URL de despliegue correcta

param(
    [string]$ResourceGroupName = "rg-vea-connect-dev",
    [string]$AppName = "veaconnect-webapp-prod"
)

Write-Host "Despliegue Git final iniciado..."

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

# Verificar Git
Write-Host "Verificando Git..."
try {
    $gitVersion = git --version
    Write-Host "Git: $gitVersion"
} catch {
    Write-Host "Error: Git no esta instalado"
    exit 1
}

# Recolectar archivos estaticos
Write-Host "Recolectando archivos estaticos..."
try {
    python manage.py collectstatic --noinput
    Write-Host "Archivos estaticos recolectados"
} catch {
    Write-Host "Advertencia: Error recolectando archivos estaticos, continuando..."
}

# Verificar si estamos en un repositorio Git
Write-Host "Verificando repositorio Git..."
try {
    $gitStatus = git status --porcelain
    if ($gitStatus) {
        Write-Host "Hay cambios sin commitear. Haciendo commit..."
        git add .
        git commit -m "Deploy $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    } else {
        Write-Host "No hay cambios pendientes"
    }
} catch {
    Write-Host "Error verificando Git: $_"
    exit 1
}

# Obtener URL de despliegue usando el comando correcto
Write-Host "Obteniendo URL de despliegue..."
try {
    $deployInfo = az webapp deployment source config-local-git --resource-group $ResourceGroupName --name $AppName --output json | ConvertFrom-Json
    $deployUrl = $deployInfo.url
    Write-Host "URL de despliegue obtenida: $deployUrl"
    
    if (-not $deployUrl) {
        Write-Host "Error: URL de despliegue vacia"
        exit 1
    }
} catch {
    Write-Host "Error obteniendo URL de despliegue: $_"
    exit 1
}

# Remover remote azure si existe
Write-Host "Configurando remote de despliegue..."
try {
    $remotes = git remote -v
    $azureRemote = $remotes | Where-Object { $_ -like "*azure*" }
    
    if ($azureRemote) {
        Write-Host "Removiendo remote azure existente..."
        git remote remove azure
    }
    
    # Agregar nuevo remote
    git remote add azure $deployUrl
    Write-Host "Remote azure agregado: $deployUrl"
} catch {
    Write-Host "Error configurando remote: $_"
    exit 1
}

# Hacer push al despliegue
Write-Host "Desplegando via Git..."
try {
    # Intentar con main primero
    git push azure main
    Write-Host "Despliegue Git completado exitosamente (branch main)"
} catch {
    Write-Host "Error con branch main, intentando con master..."
    try {
        git push azure master
        Write-Host "Despliegue Git completado exitosamente (branch master)"
    } catch {
        Write-Host "Error en despliegue Git (master): $_"
        Write-Host "Intentando con current branch..."
        try {
            $currentBranch = git branch --show-current
            git push azure $currentBranch
            Write-Host "Despliegue Git completado exitosamente (branch $currentBranch)"
        } catch {
            Write-Host "Error en despliegue Git: $_"
            exit 1
        }
    }
}

# Verificar estado del despliegue
Write-Host "Verificando estado del despliegue..."
try {
    Start-Sleep -Seconds 15  # Esperar a que el despliegue se procese
    $status = az webapp show --name $AppName --resource-group $ResourceGroupName --query "state" --output tsv
    Write-Host "Estado de la Web App: $status"
    
    if ($status -eq "Running") {
        Write-Host "Despliegue exitoso. La aplicacion esta ejecutandose."
        
        # Obtener URL
        $url = az webapp show --name $AppName --resource-group $ResourceGroupName --query "defaultHostName" --output tsv
        Write-Host "URL de la aplicacion: https://$url"
    } else {
        Write-Host "Advertencia: La aplicacion no esta ejecutandose. Estado: $status"
    }
} catch {
    Write-Host "Error verificando estado: $_"
}

Write-Host "Despliegue Git final completado" 