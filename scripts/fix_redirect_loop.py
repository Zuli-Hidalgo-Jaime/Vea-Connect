#!/usr/bin/env python3
"""
Script para diagnosticar y solucionar el problema de redirección infinita
en VEA Connect Web App.

Uso:
    python scripts/fix_redirect_loop.py
"""

import os
import sys
import json
from pathlib import Path

def check_environment_variables():
    """Verificar variables de entorno críticas."""
    print("🔍 Verificando variables de entorno...")
    
    critical_vars = [
        'WEBSITE_HOSTNAME',
        'ALLOWED_HOSTS',
        'SECURE_SSL_REDIRECT',
        'CSRF_TRUSTED_ORIGINS'
    ]
    
    for var in critical_vars:
        value = os.getenv(var)
        print(f"  {var}: {value}")
    
    print()

def check_django_settings():
    """Verificar configuración de Django."""
    print("🔍 Verificando configuración de Django...")
    
    # Simular la configuración de producción
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
    
    try:
        import django
        django.setup()
        
        from django.conf import settings
        
        print(f"  ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
        print(f"  CSRF_TRUSTED_ORIGINS: {getattr(settings, 'CSRF_TRUSTED_ORIGINS', 'No configurado')}")
        print(f"  SECURE_SSL_REDIRECT: {getattr(settings, 'SECURE_SSL_REDIRECT', 'No configurado')}")
        print(f"  DEBUG: {settings.DEBUG}")
        
    except Exception as e:
        print(f"  Error al cargar configuración: {e}")
    
    print()

def check_azure_app_service():
    """Verificar configuración de Azure App Service."""
    print("🔍 Verificando configuración de Azure App Service...")
    
    # Variables específicas de Azure App Service
    azure_vars = [
        'WEBSITE_HOSTNAME',
        'WEBSITE_SITE_NAME',
        'WEBSITE_INSTANCE_ID',
        'WEBSITE_SLOT_NAME',
        'WEBSITE_OWNER_NAME',
        'WEBSITE_RESOURCE_GROUP',
        'WEBSITE_OS',
        'WEBSITE_SKU',
        'WEBSITE_RUN_FROM_PACKAGE'
    ]
    
    for var in azure_vars:
        value = os.getenv(var)
        if value:
            print(f"  {var}: {value}")
    
    print()

def generate_fix_report():
    """Generar reporte de soluciones."""
    print("📋 REPORTE DE SOLUCIONES PARA REDIRECCIÓN INFINITA")
    print("=" * 60)
    
    print("\n✅ CAMBIOS APLICADOS:")
    print("1. SECURE_SSL_REDIRECT = True → Comentado")
    print("2. ALLOWED_HOSTS actualizado con hostname actual")
    print("3. CSRF_TRUSTED_ORIGINS actualizado")
    
    print("\n🔧 PASOS ADICIONALES RECOMENDADOS:")
    print("1. Reiniciar la aplicación en Azure App Service")
    print("2. Verificar logs de aplicación en Azure Portal")
    print("3. Limpiar caché del navegador")
    print("4. Verificar configuración de Custom Domain si aplica")
    
    print("\n📝 CONFIGURACIÓN ACTUAL:")
    print("- SECURE_SSL_REDIRECT: Comentado (evita bucle)")
    print("- ALLOWED_HOSTS: Incluye *.azurewebsites.net")
    print("- CSRF_TRUSTED_ORIGINS: Incluye HTTPS para Azure")
    
    print("\n🚨 SI EL PROBLEMA PERSISTE:")
    print("1. Verificar logs en Azure Portal > App Service > Logs")
    print("2. Revisar configuración de Application Gateway/Front Door")
    print("3. Verificar reglas de redirección en web.config")
    print("4. Comprobar configuración de SSL/TLS en Azure")

def main():
    """Función principal."""
    print("🚀 DIAGNÓSTICO DE REDIRECCIÓN INFINITA")
    print("=" * 60)
    
    check_environment_variables()
    check_azure_app_service()
    
    try:
        check_django_settings()
    except Exception as e:
        print(f"⚠️ No se pudo verificar configuración de Django: {e}")
    
    generate_fix_report()
    
    print("\n💡 PRÓXIMOS PASOS:")
    print("1. Hacer commit de los cambios en config/settings/production.py")
    print("2. Desplegar la aplicación en Azure")
    print("3. Reiniciar la aplicación web")
    print("4. Probar acceso a la aplicación")

if __name__ == "__main__":
    main()
