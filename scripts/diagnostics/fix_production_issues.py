#!/usr/bin/env python3
"""
Script para diagnosticar y solucionar problemas de producción identificados en los logs:

1. Error de ALLOWED_HOSTS: '169.254.130.4:8000'
2. Error de descarga de documentos: 'argument of type NoneType is not iterable'
3. Configuración de almacenamiento

Uso: python scripts/diagnostics/fix_production_issues.py
"""

import os
import sys
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def print_section(title):
    """Imprimir una sección con formato."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def check_allowed_hosts():
    """Verificar y corregir configuración de ALLOWED_HOSTS."""
    print_section("VERIFICACIÓN DE ALLOWED_HOSTS")
    
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.azure_production')
        import django
        django.setup()
        
        from django.conf import settings
        
        print(f"📋 ALLOWED_HOSTS actual:")
        for host in settings.ALLOWED_HOSTS:
            print(f"   ✅ {host}")
        
        # Verificar hosts problemáticos identificados en los logs
        problematic_hosts = [
            '169.254.130.4',  # IP específica del error
            '169.254.0.0/16',  # Rango de IPs internas de Azure
            '*.azurewebsites.net'  # Todos los subdominios de Azure
        ]
        
        missing_hosts = []
        for host in problematic_hosts:
            if host not in settings.ALLOWED_HOSTS:
                missing_hosts.append(host)
        
        if missing_hosts:
            print(f"\n❌ Hosts faltantes que causan errores:")
            for host in missing_hosts:
                print(f"   ❌ {host}")
            
            print(f"\n🔧 Solución: Agregar estos hosts a ALLOWED_HOSTS en config/settings/azure_production.py")
            return False
        else:
            print(f"\n✅ Todos los hosts necesarios están configurados")
            return True
            
    except Exception as e:
        print(f"❌ Error al verificar ALLOWED_HOSTS: {e}")
        return False

def check_storage_configuration():
    """Verificar configuración de almacenamiento."""
    print_section("VERIFICACIÓN DE ALMACENAMIENTO")
    
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.azure_production')
        import django
        django.setup()
        
        from django.conf import settings
        
        # Verificar variables de entorno de Azure Storage
        storage_vars = [
            'AZURE_STORAGE_CONNECTION_STRING',
            'AZURE_STORAGE_ACCOUNT_NAME',
            'AZURE_STORAGE_ACCOUNT_KEY',
            'AZURE_CONTAINER'
        ]
        
        print("📋 Variables de entorno de Azure Storage:")
        for var in storage_vars:
            value = getattr(settings, var, None) or os.environ.get(var)
            if value:
                # Ocultar valores sensibles
                if 'key' in var.lower() or 'password' in var.lower():
                    masked_value = value[:10] + '***' + value[-10:] if len(value) > 20 else '***'
                    print(f"   ✅ {var}: {masked_value}")
                else:
                    print(f"   ✅ {var}: {value}")
            else:
                print(f"   ❌ {var}: No configurada")
        
        # Verificar DEFAULT_FILE_STORAGE
        default_storage = getattr(settings, 'DEFAULT_FILE_STORAGE', None)
        print(f"\n📁 DEFAULT_FILE_STORAGE: {default_storage}")
        
        if 'FileSystemStorage' in str(default_storage):
            print("⚠️  ADVERTENCIA: Usando FileSystemStorage en producción")
            print("   Esto puede causar problemas de escalabilidad")
        else:
            print("✅ Usando almacenamiento en la nube")
            
        return True
        
    except Exception as e:
        print(f"❌ Error al verificar almacenamiento: {e}")
        return False

def test_document_download():
    """Probar funcionalidad de descarga de documentos."""
    print_section("PRUEBA DE DESCARGA DE DOCUMENTOS")
    
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.azure_production')
        import django
        django.setup()
        
        from apps.documents.models import Document
        from services.storage_service import azure_storage
        
        # Buscar documentos con el patrón mencionado en los logs
        documents = Document.objects.filter(title__icontains='Donaciones_Daya')
        
        if not documents.exists():
            print("❌ No se encontraron documentos para probar")
            return False
        
        doc = documents.first()
        print(f"📄 Probando documento: {doc.title}")
        print(f"📁 Archivo: {doc.file.name if doc.file else 'Sin archivo'}")
        
        if not doc.file:
            print("❌ Documento sin archivo asociado")
            return False
        
        # Probar list_blobs
        print("\n🔍 Probando list_blobs...")
        try:
            result = azure_storage.list_blobs(name_starts_with=doc.title)
            if result.get('success'):
                blobs = result.get('blobs', [])
                print(f"✅ list_blobs exitoso: {len(blobs)} blobs encontrados")
                for blob in blobs[:3]:  # Mostrar solo los primeros 3
                    print(f"   📄 {blob['name']}")
            else:
                print(f"❌ Error en list_blobs: {result.get('error')}")
                return False
        except Exception as e:
            print(f"❌ Excepción en list_blobs: {e}")
            return False
        
        # Probar get_blob_url
        print("\n🔗 Probando get_blob_url...")
        try:
            url_result = azure_storage.get_blob_url(doc.file.name)
            if url_result.get('success'):
                print(f"✅ URL generada exitosamente")
                print(f"   📎 URL: {url_result.get('signed_url', 'N/A')[:50]}...")
            else:
                print(f"❌ Error generando URL: {url_result.get('error')}")
                return False
        except Exception as e:
            print(f"❌ Excepción en get_blob_url: {e}")
            return False
        
        print("\n✅ Pruebas de descarga completadas exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()
        return False

def fix_allowed_hosts():
    """Corregir configuración de ALLOWED_HOSTS."""
    print_section("CORRECCIÓN DE ALLOWED_HOSTS")
    
    try:
        settings_file = "config/settings/azure_production.py"
        
        # Leer el archivo actual
        with open(settings_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar si ya tiene las IPs necesarias
        if '169.254.130.4' in content:
            print("✅ ALLOWED_HOSTS ya incluye la IP problemática")
            return True
        
        # Buscar la línea de ALLOWED_HOSTS
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'ALLOWED_HOSTS = [' in line:
                # Encontrar el final del array
                j = i
                while j < len(lines) and ']' not in lines[j]:
                    j += 1
                
                # Insertar las nuevas IPs antes del cierre del array
                new_hosts = [
                    "    '169.254.130.4',  # IP específica del error",
                    "    '169.254.0.0/16',  # Rango de IPs internas de Azure",
                ]
                
                # Insertar antes del cierre del array
                for k, host in enumerate(new_hosts):
                    lines.insert(j + k, host)
                
                # Escribir el archivo actualizado
                with open(settings_file, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(lines))
                
                print("✅ ALLOWED_HOSTS actualizado con las IPs necesarias")
                return True
        
        print("❌ No se pudo encontrar la configuración de ALLOWED_HOSTS")
        return False
        
    except Exception as e:
        print(f"❌ Error al corregir ALLOWED_HOSTS: {e}")
        return False

def generate_fix_report():
    """Generar reporte de correcciones necesarias."""
    print_section("REPORTE DE CORRECCIONES")
    
    print("📋 Problemas identificados en los logs:")
    print("   1. ❌ Error de ALLOWED_HOSTS: '169.254.130.4:8000'")
    print("   2. ❌ Error de descarga: 'argument of type NoneType is not iterable'")
    print("   3. ⚠️  Uso de FileSystemStorage en producción")
    
    print("\n🔧 Soluciones recomendadas:")
    print("   1. Agregar '169.254.130.4' y '169.254.0.0/16' a ALLOWED_HOSTS")
    print("   2. Verificar configuración de Azure Storage")
    print("   3. Asegurar que DEFAULT_FILE_STORAGE use Azure Storage")
    
    print("\n📝 Pasos para aplicar las correcciones:")
    print("   1. Ejecutar: python scripts/diagnostics/fix_production_issues.py --fix")
    print("   2. Reiniciar la aplicación en Azure")
    print("   3. Verificar que los errores se hayan resuelto")

def main():
    """Función principal."""
    print_section("DIAGNÓSTICO DE PROBLEMAS DE PRODUCCIÓN")
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Verificar argumentos
    fix_mode = '--fix' in sys.argv
    
    # Ejecutar diagnósticos
    allowed_hosts_ok = check_allowed_hosts()
    storage_ok = check_storage_configuration()
    download_ok = test_document_download()
    
    # Aplicar correcciones si se solicita
    if fix_mode and not allowed_hosts_ok:
        fix_allowed_hosts()
    
    # Generar reporte
    generate_fix_report()
    
    # Resumen final
    print_section("RESUMEN")
    print(f"ALLOWED_HOSTS: {'✅ OK' if allowed_hosts_ok else '❌ PROBLEMA'}")
    print(f"Almacenamiento: {'✅ OK' if storage_ok else '❌ PROBLEMA'}")
    print(f"Descarga de documentos: {'✅ OK' if download_ok else '❌ PROBLEMA'}")
    
    if all([allowed_hosts_ok, storage_ok, download_ok]):
        print("\n🎉 Todos los problemas han sido resueltos!")
    else:
        print("\n⚠️  Se encontraron problemas que requieren atención")
        if not fix_mode:
            print("💡 Ejecuta con --fix para aplicar correcciones automáticas")

if __name__ == "__main__":
    main()
