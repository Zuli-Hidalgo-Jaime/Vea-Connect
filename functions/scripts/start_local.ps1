# Script para iniciar Azure Functions localmente
Write-Host "Iniciando Azure Functions localmente..." -ForegroundColor Green

# Verificar si estamos en el directorio correcto
if (-not (Test-Path "host.json")) {
    Write-Host "Error: No se encontró host.json. Asegúrate de estar en el directorio functions/" -ForegroundColor Red
    exit 1
}

# Verificar si Azure Functions Core Tools está instalado
try {
    $funcVersion = func --version
    Write-Host "Azure Functions Core Tools version: $funcVersion" -ForegroundColor Yellow
} catch {
    Write-Host "Error: Azure Functions Core Tools no está instalado o no está en el PATH" -ForegroundColor Red
    Write-Host "Instala Azure Functions Core Tools desde: https://docs.microsoft.com/en-us/azure/azure-functions/functions-run-local" -ForegroundColor Yellow
    exit 1
}

# Verificar si Python está disponible
try {
    $pythonVersion = python --version
    Write-Host "Python version: $pythonVersion" -ForegroundColor Yellow
} catch {
    Write-Host "Error: Python no está instalado o no está en el PATH" -ForegroundColor Red
    exit 1
}

# Instalar dependencias si es necesario
if (-not (Test-Path ".venv")) {
    Write-Host "Creando entorno virtual..." -ForegroundColor Yellow
    python -m venv .venv
}

# Activar entorno virtual
Write-Host "Activando entorno virtual..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

# Instalar dependencias
Write-Host "Instalando dependencias..." -ForegroundColor Yellow
pip install -r requirements.txt

# Iniciar Azure Functions
Write-Host "Iniciando Azure Functions en el puerto 7072..." -ForegroundColor Green
func start --port 7072 --verbose 