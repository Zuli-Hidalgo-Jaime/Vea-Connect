# Solución para Error de Python 3.10 en Azure App Service

## Problema Identificado

El error que estás experimentando se debe a que tu Web App en Azure está configurada para usar Python 3.9 en lugar de Python 3.10, a pesar de tener `runtime.txt` especificando Python 3.10.12.

### Síntomas del Error

```
=== FORCING PYTHON 3.10 ===
Python 3.10 not found, using python3
Python 3.9.2
/usr/bin/python3: No module named pip
```

## Solución Paso a Paso

### Opción 1: Usar Scripts Automatizados (Recomendado)

#### 1. Ejecutar Script de Corrección

```powershell
# Desde el directorio raíz del proyecto
.\scripts\deployment\fix_python_version.ps1
```

Este script:
- Verifica la configuración actual
- Cambia la Web App a Python 3.10
- Reinicia la Web App
- Confirma los cambios

#### 2. Verificar la Configuración

```powershell
.\scripts\deployment\verify_python_setup.ps1
```

#### 3. Desplegar con Verificación

```powershell
.\scripts\deployment\deploy_with_python_check.ps1
```

### Opción 2: Configuración Manual

#### 1. Cambiar Versión de Python en Azure Portal

1. Ve a [Azure Portal](https://portal.azure.com)
2. Navega a tu Web App: `vea-connect`
3. Ve a **Configuración** > **Configuración general**
4. Configura:
   - **Stack**: Python
   - **Versión**: Python 3.10
   - **Sistema operativo**: Linux
5. Guarda y reinicia la Web App

#### 2. Usar Azure CLI

```bash
# Cambiar a Python 3.10
az webapp config set \
  --resource-group rg-vea-connect-dev \
  --name vea-connect \
  --linux-fx-version 'PYTHON|3.10'

# Verificar el cambio
az webapp show \
  -g rg-vea-connect-dev \
  -n vea-connect \
  --query siteConfig.linuxFxVersion -o tsv

# Reiniciar la Web App
az webapp restart \
  --resource-group rg-vea-connect-dev \
  --name vea-connect
```

## Cambios Realizados

### 1. startup.sh Simplificado

El archivo `startup.sh` ha sido simplificado para:
- Eliminar la lógica de "forzar" Python 3.10
- Usar la configuración estándar de Azure App Service
- Mejorar la detección de pip
- Agregar verificaciones más claras

### 2. Scripts de Automatización

Se han creado tres scripts de PowerShell:

- `fix_python_version.ps1`: Corrige la versión de Python
- `verify_python_setup.ps1`: Verifica la configuración
- `deploy_with_python_check.ps1`: Despliegue completo con verificación

## Verificación Post-Corrección

Después de aplicar la corrección, deberías ver en los logs:

```
=== PYTHON ENVIRONMENT VERIFICATION ===
Python 3.10.x
=== DEPENDENCY INSTALLATION ===
Collecting click==8.1.7
...
Successfully installed ...
```

## Troubleshooting

### Si Python 3.9 Reaparece

```powershell
# Verificar configuración actual
az webapp show \
  -g rg-vea-connect-dev \
  -n veaconnect-webapp-prod \
  --query siteConfig.linuxFxVersion -o tsv

# Si no es PYTHON|3.10, ejecutar el script de corrección
.\scripts\deployment\fix_python_version.ps1
```

### Si pip No Se Encuentra

Esto indica que sigues en la imagen Python 3.9. Ejecuta:

```powershell
.\scripts\deployment\fix_python_version.ps1
```

### Si Hay Errores de Dependencias

Revisa el `requirements.txt` para asegurar compatibilidad con Python 3.10.

## Prevención Futura

1. **Monitoreo**: Usa el script de verificación regularmente
2. **Documentación**: Mantén esta guía actualizada
3. **CI/CD**: Considera agregar verificaciones de versión en GitHub Actions

## Comandos Útiles

```powershell
# Verificar estado de la Web App
az webapp show -g rg-vea-connect-dev -n vea-connect

# Ver logs en tiempo real
az webapp log tail -g rg-vea-connect-dev -n vea-connect

# Ver variables de entorno
az webapp config appsettings list -g rg-vea-connect-dev -n vea-connect
```

## Tiempo Estimado de Solución

- **Configuración manual**: 5-10 minutos
- **Scripts automatizados**: 2-3 minutos
- **Verificación**: 1-2 minutos

**Total**: Aproximadamente 10 minutos para resolver completamente el problema. 