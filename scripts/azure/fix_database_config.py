#!/usr/bin/env python3
"""
Script para corregir la configuración de la base de datos en Azure Web App
"""

import os
import subprocess
import json

def run_azure_command(command):
    """Ejecuta un comando de Azure CLI"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            print(f"Error ejecutando comando: {command}")
            print(f"Error: {result.stderr}")
            return None
    except Exception as e:
        print(f"Excepción ejecutando comando: {e}")
        return None

def get_current_settings(app_name, resource_group):
    """Obtiene la configuración actual de la App Service"""
    command = f'az webapp config appsettings list --name {app_name} --resource-group {resource_group} --output json'
    result = run_azure_command(command)
    if result:
        return json.loads(result)
    return []

def update_database_settings(app_name, resource_group):
    """Actualiza la configuración de la base de datos"""
    
    # Configuración de SQLite para desarrollo (temporal)
    settings = [
        'DATABASE_URL=sqlite:///db.sqlite3',
        'DEBUG=True',
        'DJANGO_SETTINGS_MODULE=config.settings.development'
    ]
    
    # Aplicar configuración
    for setting in settings:
        key, value = setting.split('=', 1)
        command = f'az webapp config appsettings set --name {app_name} --resource-group {resource_group} --settings {key}="{value}"'
        print(f"Aplicando configuración: {key}")
        result = run_azure_command(command)
        if result:
            print(f"✅ {key} configurado correctamente")
        else:
            print(f"❌ Error configurando {key}")

def main():
    """Función principal"""
    print("🔧 Corrigiendo configuración de base de datos...")
    
    # Configuración
    app_name = "veaconnect-webapp-prod"
    resource_group = "rg-vea-connect-dev"
    
    print(f"📋 App Service: {app_name}")
    print(f"📋 Resource Group: {resource_group}")
    
    # Obtener configuración actual
    print("\n📊 Configuración actual:")
    current_settings = get_current_settings(app_name, resource_group)
    if current_settings:
        for setting in current_settings:
            if 'POSTGRESQL' in setting['name'] or 'DATABASE' in setting['name']:
                print(f"  {setting['name']}: {setting['value']}")
    
    # Actualizar configuración
    print("\n🔄 Actualizando configuración...")
    update_database_settings(app_name, resource_group)
    
    print("\n✅ Configuración actualizada. Reiniciando aplicación...")
    
    # Reiniciar la aplicación
    restart_command = f'az webapp restart --name {app_name} --resource-group {resource_group}'
    run_azure_command(restart_command)
    
    print("\n🎉 ¡Listo! La aplicación debería funcionar ahora.")

if __name__ == "__main__":
    main() 