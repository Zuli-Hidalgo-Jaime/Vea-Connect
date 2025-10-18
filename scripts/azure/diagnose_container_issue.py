#!/usr/bin/env python3
"""
Script de diagnóstico para problemas de contenedores en Azure App Service
"""

import os
import sys
import subprocess
import json
from datetime import datetime

def run_command(command, capture_output=True):
    """Ejecuta un comando y retorna el resultado"""
    try:
        result = subprocess.run(command, shell=True, capture_output=capture_output, text=True)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)

def check_azure_cli():
    """Verifica si Azure CLI está instalado y configurado"""
    print("=== VERIFICACIÓN DE AZURE CLI ===")
    code, stdout, stderr = run_command("az --version")
    if code == 0:
        print("✓ Azure CLI está instalado")
        return True
    else:
        print("✗ Azure CLI no está instalado o no es accesible")
        print(f"Error: {stderr}")
        return False

def check_webapp_config(webapp_name, resource_group):
    """Verifica la configuración actual del Web App"""
    print(f"\n=== CONFIGURACIÓN DEL WEB APP: {webapp_name} ===")
    
    # Obtener configuración general
    code, stdout, stderr = run_command(f"az webapp config show --name {webapp_name} --resource-group {resource_group}")
    if code == 0:
        config = json.loads(stdout)
        print(f"✓ Configuración obtenida")
        print(f"  - Linux FX Version: {config.get('linuxFxVersion', 'NO CONFIGURADO')}")
        print(f"  - Startup File: {config.get('appCommandLine', 'NO CONFIGURADO')}")
    else:
        print(f"✗ Error al obtener configuración: {stderr}")
        return False
    
    # Obtener configuración de contenedor
    code, stdout, stderr = run_command(f"az webapp config container show --name {webapp_name} --resource-group {resource_group}")
    if code == 0:
        container_config = json.loads(stdout)
        print(f"✓ Configuración de contenedor obtenida")
        print(f"  - Docker Image: {container_config.get('dockerImageName', 'NO CONFIGURADO')}")
        print(f"  - Registry URL: {container_config.get('registryUrl', 'NO CONFIGURADO')}")
    else:
        print(f"✗ Error al obtener configuración de contenedor: {stderr}")
    
    return True

def check_app_settings(webapp_name, resource_group):
    """Verifica las variables de entorno configuradas"""
    print(f"\n=== VARIABLES DE ENTORNO ===")
    
    code, stdout, stderr = run_command(f"az webapp config appsettings list --name {webapp_name} --resource-group {resource_group}")
    if code == 0:
        settings = json.loads(stdout)
        print(f"✓ Variables de entorno obtenidas ({len(settings)} configuradas)")
        
        # Variables críticas para PostgreSQL
        critical_vars = [
            'AZURE_POSTGRESQL_NAME',
            'AZURE_POSTGRESQL_USERNAME', 
            'AZURE_POSTGRESQL_PASSWORD',
            'AZURE_POSTGRESQL_HOST',
            'DATABASE_URL',
            'DJANGO_SETTINGS_MODULE',
            'WEBSITES_PORT',
            'ALLOWED_HOSTS'
        ]
        
        settings_dict = {s['name']: s['value'] for s in settings}
        
        for var in critical_vars:
            if var in settings_dict:
                value = settings_dict[var]
                if 'PASSWORD' in var:
                    value = '***HIDDEN***' if value else 'NO CONFIGURADA'
                print(f"  ✓ {var}: {value}")
            else:
                print(f"  ✗ {var}: NO CONFIGURADA")
    else:
        print(f"✗ Error al obtener variables de entorno: {stderr}")
        return False
    
    return True

def check_webapp_logs(webapp_name, resource_group):
    """Obtiene los logs recientes del Web App"""
    print(f"\n=== LOGS RECIENTES ===")
    
    code, stdout, stderr = run_command(f"az webapp log tail --name {webapp_name} --resource-group {resource_group} --timeout 10")
    if code == 0:
        print("✓ Logs obtenidos (últimos 10 segundos)")
        if stdout.strip():
            print("Últimas líneas de log:")
            lines = stdout.strip().split('\n')[-10:]
            for line in lines:
                print(f"  {line}")
        else:
            print("  No hay logs recientes")
    else:
        print(f"✗ Error al obtener logs: {stderr}")

def main():
    """Función principal"""
    print("🔍 DIAGNÓSTICO DE PROBLEMAS DE CONTENEDORES EN AZURE APP SERVICE")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Configuración
    webapp_name = os.getenv('WEBAPP_NAME', 'vea-connect')
    resource_group = os.getenv('RESOURCE_GROUP', 'rg-vea-connect-dev')
    
    print(f"Web App: {webapp_name}")
    print(f"Resource Group: {resource_group}")
    
    # Verificaciones
    if not check_azure_cli():
        print("\n❌ Azure CLI no está disponible. Instala Azure CLI y ejecuta 'az login'")
        sys.exit(1)
    
    check_webapp_config(webapp_name, resource_group)
    check_app_settings(webapp_name, resource_group)
    check_webapp_logs(webapp_name, resource_group)
    
    print(f"\n✅ Diagnóstico completado")
    print("\n📋 PRÓXIMOS PASOS:")
    print("1. Si el Linux FX Version no es 'DOCKER', ejecuta el workflow de GitHub")
    print("2. Si faltan variables de PostgreSQL, configúralas en Azure Portal")
    print("3. Si hay errores en los logs, revisa la configuración del contenedor")

if __name__ == "__main__":
    main()
