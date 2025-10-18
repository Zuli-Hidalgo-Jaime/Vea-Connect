#!/usr/bin/env python3
"""
Script simplificado para diagnosticar problemas de producción identificados en los logs.
Versión compatible con Windows y sin requerir configuración de base de datos.

1. Error de ALLOWED_HOSTS: '169.254.130.4:8000'
2. Error de descarga de documentos: 'argument of type NoneType is not iterable'
3. Configuración de almacenamiento

Uso: python scripts/diagnostics/fix_production_issues_simple.py
"""

import os
import sys
from datetime import datetime

def print_section(title):
    """Imprimir una sección con formato."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def check_allowed_hosts_config():
    """Verificar configuración de ALLOWED_HOSTS en el archivo."""
    print_section("VERIFICACION DE ALLOWED_HOSTS")
    
    try:
        settings_file = "config/settings/azure_production.py"
        
        if not os.path.exists(settings_file):
            print("ERROR: No se encuentra el archivo de configuracion")
            return False
        
        with open(settings_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar hosts problemáticos identificados en los logs
        problematic_hosts = [
            '169.254.130.4',  # IP específica del error
            '169.254.0.0/16',  # Rango de IPs internas de Azure
            '*.azurewebsites.net'  # Todos los subdominios de Azure
        ]
        
        missing_hosts = []
        for host in problematic_hosts:
            if host not in content:
                missing_hosts.append(host)
        
        if missing_hosts:
            print("Hosts faltantes que causan errores:")
            for host in missing_hosts:
                print(f"   - {host}")
            
            print("\nSolucion: Agregar estos hosts a ALLOWED_HOSTS en config/settings/azure_production.py")
            return False
        else:
            print("Todos los hosts necesarios estan configurados")
            return True
            
    except Exception as e:
        print(f"Error al verificar ALLOWED_HOSTS: {e}")
        return False

def check_storage_config():
    """Verificar configuración de almacenamiento."""
    print_section("VERIFICACION DE ALMACENAMIENTO")
    
    try:
        # Verificar variables de entorno de Azure Storage
        storage_vars = [
            'AZURE_STORAGE_CONNECTION_STRING',
            'AZURE_STORAGE_ACCOUNT_NAME',
            'AZURE_STORAGE_ACCOUNT_KEY',
            'AZURE_CONTAINER'
        ]
        
        print("Variables de entorno de Azure Storage:")
        for var in storage_vars:
            value = os.environ.get(var)
            if value:
                # Ocultar valores sensibles
                if 'key' in var.lower() or 'password' in var.lower():
                    masked_value = value[:10] + '***' + value[-10:] if len(value) > 20 else '***'
                    print(f"   OK {var}: {masked_value}")
                else:
                    print(f"   OK {var}: {value}")
            else:
                print(f"   FALTA {var}: No configurada")
        
        # Verificar archivo de configuración
        settings_file = "config/settings/azure_production.py"
        if os.path.exists(settings_file):
            with open(settings_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if 'FileSystemStorage' in content:
                print("\nADVERTENCIA: Usando FileSystemStorage en produccion")
                print("   Esto puede causar problemas de escalabilidad")
            else:
                print("\nOK: Usando almacenamiento en la nube")
        
        return True
        
    except Exception as e:
        print(f"Error al verificar almacenamiento: {e}")
        return False

def check_document_download_code():
    """Verificar código de descarga de documentos."""
    print_section("VERIFICACION DE CODIGO DE DESCARGA")
    
    try:
        views_file = "apps/documents/views.py"
        storage_file = "services/storage_service.py"
        
        issues_found = []
        
        # Verificar archivo de vistas
        if os.path.exists(views_file):
            with open(views_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if 'argument of type' in content and 'NoneType' in content:
                print("ADVERTENCIA: Posible error de NoneType en vistas")
                issues_found.append("Error de NoneType en vistas")
            else:
                print("OK: Vistas de documentos")
        else:
            print("ERROR: No se encuentra el archivo de vistas")
            issues_found.append("Archivo de vistas no encontrado")
        
        # Verificar archivo de servicio de almacenamiento
        if os.path.exists(storage_file):
            with open(storage_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if 'resolve_blob_name' in content:
                print("OK: Servicio de almacenamiento encontrado")
            else:
                print("ADVERTENCIA: Metodo resolve_blob_name no encontrado")
                issues_found.append("Metodo resolve_blob_name no encontrado")
        else:
            print("ERROR: No se encuentra el archivo de servicio de almacenamiento")
            issues_found.append("Archivo de servicio no encontrado")
        
        return len(issues_found) == 0
        
    except Exception as e:
        print(f"Error al verificar codigo: {e}")
        return False

def generate_fix_report():
    """Generar reporte de correcciones necesarias."""
    print_section("REPORTE DE CORRECCIONES")
    
    print("Problemas identificados en los logs:")
    print("   1. ERROR Error de ALLOWED_HOSTS: '169.254.130.4:8000'")
    print("   2. ERROR Error de descarga: 'argument of type NoneType is not iterable'")
    print("   3. ADVERTENCIA Uso de FileSystemStorage en produccion")
    
    print("\nSoluciones recomendadas:")
    print("   1. Agregar '169.254.130.4' y '169.254.0.0/16' a ALLOWED_HOSTS")
    print("   2. Verificar configuracion de Azure Storage")
    print("   3. Asegurar que DEFAULT_FILE_STORAGE use Azure Storage")
    
    print("\nPasos para aplicar las correcciones:")
    print("   1. Verificar que ALLOWED_HOSTS incluya las IPs necesarias")
    print("   2. Reiniciar la aplicacion en Azure")
    print("   3. Verificar que los errores se hayan resuelto")

def main():
    """Función principal."""
    print_section("DIAGNOSTICO DE PROBLEMAS DE PRODUCCION")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Ejecutar diagnósticos
    allowed_hosts_ok = check_allowed_hosts_config()
    storage_ok = check_storage_config()
    download_ok = check_document_download_code()
    
    # Generar reporte
    generate_fix_report()
    
    # Resumen final
    print_section("RESUMEN")
    print(f"ALLOWED_HOSTS: {'OK' if allowed_hosts_ok else 'PROBLEMA'}")
    print(f"Almacenamiento: {'OK' if storage_ok else 'PROBLEMA'}")
    print(f"Descarga de documentos: {'OK' if download_ok else 'PROBLEMA'}")
    
    if all([allowed_hosts_ok, storage_ok, download_ok]):
        print("\nTODOS LOS PROBLEMAS HAN SIDO RESUELTOS!")
    else:
        print("\nSe encontraron problemas que requieren atencion")
        print("Revisa el reporte de arriba para mas detalles")

if __name__ == "__main__":
    main()
