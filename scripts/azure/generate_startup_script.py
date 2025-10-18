#!/usr/bin/env python3
"""
Script para generar automáticamente el archivo startup_improved.sh
con todas las validaciones necesarias para resolver el error del módulo config.
"""

import os
import sys

def generate_startup_script():
    """Genera el script de startup mejorado."""
    
    startup_content = '''#!/bin/bash

# Script de startup mejorado para Azure App Service
# Generado automáticamente para resolver problemas con el módulo config
set -e  # Salir en caso de error

echo "=== INICIANDO DESPLIEGUE EN AZURE APP SERVICE ==="
echo "Timestamp: $(date)"
echo "Directorio actual: $(pwd)"

# Navegar al directorio correcto
cd /home/site/wwwroot
echo "Navegado a: $(pwd)"

# Mostrar estructura del proyecto
echo "=== ESTRUCTURA DEL PROYECTO ==="
ls -la

# Configurar variables de entorno
export DJANGO_SETTINGS_MODULE=config.settings.production
export PYTHONPATH=/home/site/wwwroot
export PYTHONUNBUFFERED=1

echo "DJANGO_SETTINGS_MODULE: $DJANGO_SETTINGS_MODULE"
echo "PYTHONPATH: $PYTHONPATH"

# Activar entorno virtual si existe
if [ -d "/antenv" ]; then
    source /antenv/bin/activate
    echo "✅ Entorno virtual antenv activado"
elif [ -d "antenv" ]; then
    source antenv/bin/activate
    echo "✅ Entorno virtual antenv activado"
else
    echo "⚠️ No se encontró entorno virtual antenv"
fi

# Verificar Python
echo "=== VERIFICACIÓN DE PYTHON ==="
python3 --version || python --version

# Instalar dependencias
echo "=== INSTALACIÓN DE DEPENDENCIAS ==="
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

# Verificar módulos críticos
echo "=== VERIFICACIÓN DE MÓDULOS ==="
python3 -c "import django; print(f'✅ Django {django.get_version()}')"
python3 -c "import config; print('✅ Módulo config')"
python3 -c "import config.wsgi; print('✅ Módulo config.wsgi')"
python3 -c "import gunicorn; print('✅ Gunicorn')"

# Ejecutar migraciones
echo "=== MIGRACIONES ==="
python3 manage.py migrate --noinput --settings=config.settings.production

# Recolectar archivos estáticos
echo "=== ARCHIVOS ESTÁTICOS ==="
python3 manage.py collectstatic --noinput --settings=config.settings.production

# Iniciar aplicación
echo "=== INICIANDO APLICACIÓN ==="
echo "Comando: gunicorn config.wsgi:application --bind=0.0.0.0:8000 --timeout 600 --workers 4"
exec gunicorn config.wsgi:application --bind=0.0.0.0:8000 --timeout 600 --workers 4
'''
    
    # Escribir el archivo
    with open('startup_improved.sh', 'w') as f:
        f.write(startup_content)
    
    print("Archivo startup_improved.sh generado exitosamente")
    print("Ubicacion: startup_improved.sh")
    print()
    print("Para usar este script:")
    print("   1. Copia el archivo como startup.sh:")
    print("      cp startup_improved.sh startup.sh")
    print()
    print("   2. O configuralo manualmente en Azure App Service")
    print()
    print("Este script incluye:")
    print("   - Validaciones exhaustivas de la estructura del proyecto")
    print("   - Verificacion de modulos criticos")
    print("   - Configuracion correcta del PYTHONPATH")
    print("   - Manejo de errores mejorado")
    print("   - Logs detallados para debugging")

def generate_diagnostic_script():
    """Genera un script de diagnóstico rápido."""
    
    diagnostic_content = '''#!/bin/bash

# Script de diagnóstico rápido para Azure App Service
echo "=== DIAGNÓSTICO RÁPIDO AZURE APP SERVICE ==="
echo "Timestamp: $(date)"
echo "Directorio actual: $(pwd)"

# Navegar al directorio correcto
cd /home/site/wwwroot
echo "Navegado a: $(pwd)"

# Mostrar estructura básica
echo "=== ESTRUCTURA BÁSICA ==="
ls -la

# Verificar archivos críticos
echo ""
echo "=== VERIFICACIÓN DE ARCHIVOS CRÍTICOS ==="
[ -f "manage.py" ] && echo "✅ manage.py" || echo "❌ manage.py"
[ -d "config" ] && echo "✅ config/" || echo "❌ config/"
[ -f "config/__init__.py" ] && echo "✅ config/__init__.py" || echo "❌ config/__init__.py"
[ -f "config/wsgi.py" ] && echo "✅ config/wsgi.py" || echo "❌ config/wsgi.py"
[ -f "requirements.txt" ] && echo "✅ requirements.txt" || echo "❌ requirements.txt"

# Verificar Python
echo ""
echo "=== VERIFICACIÓN DE PYTHON ==="
python3 --version || python --version

# Verificar módulos
echo ""
echo "=== VERIFICACIÓN DE MÓDULOS ==="
python3 -c "import django; print('✅ Django')" 2>/dev/null || echo "❌ Django"
python3 -c "import config; print('✅ config')" 2>/dev/null || echo "❌ config"
python3 -c "import gunicorn; print('✅ gunicorn')" 2>/dev/null || echo "❌ gunicorn"

echo ""
echo "=== DIAGNÓSTICO COMPLETADO ==="
'''
    
    # Escribir el archivo
    with open('diagnostic_quick.sh', 'w') as f:
        f.write(diagnostic_content)
    
    print("Archivo diagnostic_quick.sh generado exitosamente")
    print("Ubicacion: diagnostic_quick.sh")
    print()
    print("Para ejecutar el diagnostico:")
    print("   bash diagnostic_quick.sh")

def main():
    """Función principal."""
    print("GENERADOR DE SCRIPTS PARA AZURE APP SERVICE")
    print("=" * 50)
    
    # Generar scripts
    generate_startup_script()
    print()
    generate_diagnostic_script()
    
    print()
    print("=" * 50)
    print("RESUMEN")
    print("=" * 50)
    print("Se han generado los siguientes archivos:")
    print("   startup_improved.sh - Script de inicio mejorado")
    print("   diagnostic_quick.sh - Script de diagnostico rapido")
    print()
    print("Proximos pasos:")
    print("   1. Revisa los archivos generados")
    print("   2. Copia startup_improved.sh como startup.sh si es necesario")
    print("   3. Ejecuta diagnostic_quick.sh en Azure para verificar")
    print("   4. Revisa los logs para identificar problemas especificos")
    print()
    print("Archivos relacionados:")
    print("   - docs/troubleshooting/SOLUCION_ERROR_MODULO_CONFIG.md")
    print("   - scripts/diagnostics/check_project_structure.py")
    print("   - scripts/azure/check_azure_deployment.py")

if __name__ == "__main__":
    main() 