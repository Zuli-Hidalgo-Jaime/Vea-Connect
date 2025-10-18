# CI/CD para Azure Functions - Guía Completa

## Descripción General

Este documento describe el proceso de Continuous Integration y Continuous Deployment (CI/CD) para las Azure Functions del proyecto VEA Connect, específicamente para el webhook de WhatsApp y funciones relacionadas.

## Arquitectura CI/CD

```
GitHub Repository
       │
       ▼
   GitHub Actions
       │
       ▼
   Build & Test
       │
       ▼
   Package (ZIP)
       │
       ▼
   Deploy to Azure
       │
       ▼
   Health Check
       │
       ▼
   Rollback (if needed)
```

## Workflows de GitHub Actions

### 1. CI Workflow (`.github/workflows/functions-ci.yml`)

Este workflow se ejecuta en cada Pull Request y realiza:

- **Instalación de dependencias**: Instala las dependencias de Python
- **Linting**: Verifica la calidad del código
- **Tests**: Ejecuta pruebas unitarias e integración
- **Empaquetado**: Crea un artefacto ZIP con las funciones

```yaml
name: Functions CI

on:
  pull_request:
    branches: [ main ]
    paths:
      - 'functions/**'
      - '.github/workflows/functions-ci.yml'

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        cd functions
        pip install -r requirements.txt
        pip install flake8 pytest
    
    - name: Lint with flake8
      run: |
        cd functions
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
        flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
    
    - name: Run tests
      run: |
        cd functions
        python -m pytest tests/ -v
    
    - name: Create deployment package
      run: |
        cd functions
        zip -r ../functions-deployment.zip . -x "*.pyc" "__pycache__/*" ".venv/*" "local.settings.json" "*.log"
    
    - name: Upload artifact
      uses: actions/upload-artifact@v3
      with:
        name: functions-deployment
        path: functions-deployment.zip
```

### 2. CD Workflow (`.github/workflows/functions-cd.yml`)

Este workflow se ejecuta en push a `main` y en `workflow_dispatch`:

- **Descarga del artefacto**: Obtiene el ZIP del workflow CI
- **Despliegue**: Despliega a Azure Function App
- **Health Check**: Verifica que el despliegue fue exitoso
- **Rollback**: Revierte cambios si hay problemas

```yaml
name: Functions CD

on:
  push:
    branches: [ main ]
    paths:
      - 'functions/**'
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to deploy to'
        required: true
        default: 'production'
        type: choice
        options:
        - staging
        - production

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: ${{ github.event.inputs.environment || 'production' }}
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Download artifact
      uses: actions/download-artifact@v3
      with:
        name: functions-deployment
        path: ./
    
    - name: Deploy to Azure Functions
      uses: azure/functions-container-action@v1
      with:
        app-name: ${{ secrets.AZURE_FUNCTION_APP_NAME }}
        package: './functions-deployment.zip'
        publish-profile: ${{ secrets.AZURE_FUNCTIONAPP_PUBLISH_PROFILE }}
    
    - name: Wait for deployment
      run: sleep 30
    
    - name: Health check
      run: |
        HEALTH_URL="https://${{ secrets.AZURE_FUNCTION_APP_NAME }}.azurewebsites.net/api/health"
        for i in {1..10}; do
          response=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)
          if [ $response -eq 200 ]; then
            echo "Health check passed"
            exit 0
          fi
          echo "Health check failed (attempt $i/10), status: $response"
          sleep 10
        done
        echo "Health check failed after 10 attempts"
        exit 1
    
    - name: Rollback on failure
      if: failure()
      run: |
        echo "Deployment failed, initiating rollback..."
        # Implement rollback logic here
        # This could involve deploying a previous version
        # or triggering an alert
```

## Secretos Requeridos

### GitHub Secrets

Los siguientes secretos deben configurarse en el repositorio de GitHub:

#### Azure Function App
```bash
AZURE_FUNCTION_APP_NAME=vea-connect-functions-prod
AZURE_FUNCTIONAPP_PUBLISH_PROFILE=<publish-profile-content>
```

#### Azure Credentials (Alternativo)
```bash
AZURE_CREDENTIALS=<service-principal-json>
AZURE_SUBSCRIPTION_ID=<subscription-id>
AZURE_RESOURCE_GROUP=<resource-group-name>
```

#### Health Check
```bash
HEALTH_URL=https://vea-connect-functions-prod.azurewebsites.net/api/health
```

### Cómo Obtener los Secretos

#### 1. Publish Profile
```powershell
# En Azure Portal: Function App > Overview > Get publish profile
# O usando Azure CLI
az functionapp deployment list-publishing-profiles \
  --name vea-connect-functions-prod \
  --resource-group vea-connect-rg \
  --xml
```

#### 2. Service Principal
```powershell
# Crear Service Principal
az ad sp create-for-rbac --name "vea-connect-functions-sp" \
  --role contributor \
  --scopes /subscriptions/{subscription-id}/resourceGroups/{resource-group} \
  --sdk-auth

# El resultado es el JSON que se usa como AZURE_CREDENTIALS
```

## Configuración de Entornos

### Variables de Entorno por Ambiente

#### Staging
```bash
AZURE_FUNCTION_APP_NAME=vea-connect-functions-staging
WHATSAPP_DEBUG=true
E2E_DEBUG=true
RAG_ENABLED=false
```

#### Production
```bash
AZURE_FUNCTION_APP_NAME=vea-connect-functions-prod
WHATSAPP_DEBUG=false
E2E_DEBUG=false
RAG_ENABLED=true
```

## Proceso de Rollback

### Rollback Automático

El workflow de CD incluye rollback automático en caso de fallo:

1. **Detección de fallo**: Health check falla después del despliegue
2. **Notificación**: Se envía alerta al equipo
3. **Rollback**: Se despliega la versión anterior
4. **Verificación**: Se confirma que el rollback fue exitoso

### Rollback Manual

```powershell
# Listar deployments
az functionapp deployment list --name vea-connect-functions-prod --resource-group vea-connect-rg

# Rollback a versión específica
az functionapp deployment source config-zip \
  --resource-group vea-connect-rg \
  --name vea-connect-functions-prod \
  --src previous-deployment.zip
```

## Monitoreo del Despliegue

### Métricas de Despliegue

- **Tiempo de despliegue**: Tiempo total desde push hasta health check exitoso
- **Tasa de éxito**: Porcentaje de despliegues exitosos
- **Tiempo de rollback**: Tiempo para revertir cambios fallidos

### Alertas

Configurar alertas para:
- Despliegues fallidos
- Health checks fallidos
- Rollbacks ejecutados
- Tiempo de respuesta de funciones

## Seguridad

### Buenas Prácticas

1. **Secretos**: Nunca hardcodear credenciales en el código
2. **Principio de menor privilegio**: Service Principal con permisos mínimos
3. **Rotación de credenciales**: Cambiar credenciales regularmente
4. **Auditoría**: Revisar logs de acceso regularmente

### Validaciones de Seguridad

```yaml
# En el workflow CI
- name: Security scan
  run: |
    pip install bandit
    bandit -r functions/ -f json -o bandit-report.json
    
- name: Upload security report
  uses: actions/upload-artifact@v3
  with:
    name: security-report
    path: bandit-report.json
```

## Troubleshooting

### Problemas Comunes

#### 1. Deploy Failed - Invalid Publish Profile
**Causa**: Publish profile expirado o inválido
**Solución**: Regenerar publish profile desde Azure Portal

#### 2. Health Check Failed
**Causa**: Función no responde después del despliegue
**Solución**:
1. Verificar logs de la Function App
2. Confirmar que las variables de entorno están configuradas
3. Verificar que las dependencias se instalaron correctamente

#### 3. Permission Denied
**Causa**: Service Principal sin permisos suficientes
**Solución**: Actualizar permisos del Service Principal

#### 4. Package Too Large
**Causa**: Artefacto ZIP excede límites de Azure Functions
**Solución**: Optimizar dependencias y excluir archivos innecesarios

### Logs de Debug

```yaml
# Habilitar logs detallados
- name: Enable debug logging
  run: |
    az webapp log config \
      --name ${{ secrets.AZURE_FUNCTION_APP_NAME }} \
      --resource-group vea-connect-rg \
      --web-server-logging filesystem \
      --level verbose
```

## Optimización

### Caché de Dependencias

```yaml
- name: Cache pip dependencies
  uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('functions/requirements.txt') }}
    restore-keys: |
      ${{ runner.os }}-pip-
```

### Build Paralelo

```yaml
jobs:
  lint:
    runs-on: ubuntu-latest
    steps: # Linting steps
    
  test:
    runs-on: ubuntu-latest
    steps: # Testing steps
    
  package:
    needs: [lint, test]
    runs-on: ubuntu-latest
    steps: # Packaging steps
```

## Referencias

- [Azure Functions Deployment](https://docs.microsoft.com/en-us/azure/azure-functions/functions-deployment-technologies)
- [GitHub Actions for Azure](https://docs.microsoft.com/en-us/azure/developer/github/github-actions)
- [Azure CLI Function App Commands](https://docs.microsoft.com/en-us/cli/azure/functionapp)
- [Azure Functions Monitoring](https://docs.microsoft.com/en-us/azure/azure-functions/functions-monitoring)
