# Solution to Error: ModuleNotFoundError: No module named 'config'

## Critical Error

```
ModuleNotFoundError: No module named 'config'
```

Este error ocurre cuando se intenta ejecutar:
```bash
gunicorn config.wsgi:application
```

## Problem Diagnosis

The error indicates that the `config` module is not found or not in the PYTHONPATH when running in Azure App Service.

### Possible Causes

1. **The `config/` folder is not present in `/home/site/wwwroot`**
2. **The real folder name is not `config`** (e.g., `core/`, `apps/`, `project/`)
3. **Capitalization problem** (`Config/` instead of `config/`)
4. **Missing `__init__.py` in `config/`**
5. **PYTHONPATH not configured correctly**
6. **Problems with file deployment to Azure**

## Implemented Solutions

### 1. Improved Startup Script

An improved `startup.sh` has been created with exhaustive validations:

```bash
#!/bin/bash

# Navegar al directorio raíz de la app
cd /home/site/wwwroot

echo "=== DIAGNÓSTICO INICIAL ==="
echo "Directorio actual: $(pwd)"
echo "Contenido del directorio:"
ls -la

echo ""
echo "=== VERIFICACIÓN DE ESTRUCTURA ==="
echo "Verificando archivos críticos..."

# Check essential files
if [ -f "manage.py" ]; then
    echo "[OK] manage.py found"
else
    echo "[ERROR] manage.py NOT found"
    exit 1
fi

if [ -d "config" ]; then
    echo "[OK] config/ directory found"
    echo "Contents of config/:"
    ls -la config/
else
    echo "[ERROR] config/ directory NOT found"
    exit 1
fi

# ... more validations ...

echo "Checking config module importability..."
python3 -c "import config; print('[OK] config module imported correctly')"

echo "Checking config.wsgi importability..."
python3 -c "import config.wsgi; print('[OK] config.wsgi imported correctly')"

# ... rest of script ...
```

### 2. Diagnostic Scripts

#### Local Diagnostic Script
```bash
python scripts/diagnostics/check_project_structure.py
```

#### Azure Diagnostic Script
```bash
python scripts/azure/check_azure_deployment.py
```

### 3. Structure Verification

The correct structure should be:

```
/home/site/wwwroot/
├── config/
│   ├── __init__.py          # CRITICAL - Must exist
│   ├── wsgi.py              # CRITICAL - WSGI file
│   └── settings/
│       ├── __init__.py      # CRITICAL - Must exist
│       └── production.py    # CRITICAL - Production settings
├── manage.py                # CRITICAL - Django management file
├── requirements.txt         # CRITICAL - Dependencies
└── startup.sh              # CRITICAL - Startup script
```

## Steps to Solve

### Step 1: Verify Structure in Azure

1. **Access Azure App Service logs**
2. **Run the improved diagnostic script**
3. **Verify that all critical files are present**

### Step 2: Fix startup.sh

If the `config/` directory doesn't exist or has another name:

```bash
# If your WSGI file is in apps/wsgi.py:
gunicorn apps.wsgi:application

# If your WSGI file is in myproject/wsgi.py:
gunicorn myproject.wsgi:application
```

### Step 3: Verify __init__.py

Make sure these files exist (even if empty):

```bash
# Create if they don't exist
touch config/__init__.py
touch config/settings/__init__.py
```

### Step 4: Configure PYTHONPATH

In the `startup.sh`:

```bash
export PYTHONPATH=/home/site/wwwroot
export DJANGO_SETTINGS_MODULE=config.settings.production
```

## Verification Commands

### Verify Structure
```bash
# In Azure App Service
cd /home/site/wwwroot
ls -la
ls -la config/
```

### Verify Imports
```bash
# Test config module import
python3 -c "import config; print('Config imported correctly')"

# Test WSGI application import
python3 -c "import config.wsgi; print('WSGI imported correctly')"
```

### Verify Django
```bash
# Verify Django configuration
python3 manage.py check --settings=config.settings.production

# Verify migrations
python3 manage.py showmigrations --settings=config.settings.production
```

## Verification Checklist

- [ ] The `config/` directory exists in `/home/site/wwwroot`
- [ ] The `config/__init__.py` file exists (even if empty)
- [ ] The `config/wsgi.py` file exists and is valid
- [ ] The `config/settings/__init__.py` file exists
- [ ] The `config/settings/production.py` file exists
- [ ] The `manage.py` file exists in the root
- [ ] The `requirements.txt` file exists
- [ ] PYTHONPATH is configured correctly
- [ ] DJANGO_SETTINGS_MODULE is configured
- [ ] Gunicorn is installed
- [ ] Django is installed

## Emergency Solutions

### If the problem persists:

1. **Use the alternative startup script**:
   ```bash
   # Copy startup_improved.sh as startup.sh
   cp startup_improved.sh startup.sh
   ```

2. **Verify file deployment**:
   - Make sure all files are uploaded correctly
   - Verify there are no permission problems

3. **Review complete logs**:
   - Azure App Service logs
   - Application logs
   - Startup logs

## Debugging Commands

```bash
# Run complete diagnostic
python3 scripts/azure/check_azure_deployment.py

# Verify project structure
python3 scripts/diagnostics/check_project_structure.py

# Test gunicorn manually
gunicorn config.wsgi:application --bind=0.0.0.0:8000 --timeout 600 --workers 1
```

## Expected Result

After applying the solutions, you should see:

```
[OK] config module imported correctly
[OK] config.wsgi module imported correctly
[OK] Django configured correctly
[OK] Gunicorn available
=== APPLICATION STARTUP ===
[INFO] Starting gunicorn 21.2.0
[INFO] Listening at: http://0.0.0.0:8000
```

## Related Files

- `startup.sh` - Main startup script
- `startup_improved.sh` - Alternative startup script with validations
- `scripts/diagnostics/check_project_structure.py` - Local diagnostic
- `scripts/azure/check_azure_deployment.py` - Azure diagnostic
- `config/wsgi.py` - WSGI file
- `config/settings/production.py` - Production configuration 