#!/usr/bin/env python3
"""
Script de diagnóstico para verificar problemas de producción identificados:
1. Error de ALLOWED_HOSTS
2. FileSystemStorage en producción
3. Configuración de Azure Storage
"""

import os
import sys
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_allowed_hosts():
    """Verificar configuración de ALLOWED_HOSTS."""
    print_section("VERIFICACIÓN DE ALLOWED_HOSTS")
    
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.azure_production')
        import django
        django.setup()
        
        from django.conf import settings
        
        print(f"📋 ALLOWED_HOSTS configurado:")
        for host in settings.ALLOWED_HOSTS:
            print(f"   ✅ {host}")
        
        # Verificar hosts problemáticos
        problematic_hosts = ['169.254.130.2', '169.254.0.0/16', '*.azurewebsites.net']
        missing_hosts = []
        
        for host in problematic_hosts:
            if host not in settings.ALLOWED_HOSTS:
                missing_hosts.append(host)
        
        if missing_hosts:
            print(f"\n❌ Hosts faltantes que pueden causar errores:")
            for host in missing_hosts:
                print(f"   ❌ {host}")
            return False
        else:
            print(f"\n✅ Todos los hosts necesarios están configurados")
            return True
            
    except Exception as e:
        print(f"❌ Error al verificar ALLOWED_HOSTS: {e}")
        return False

def check_file_storage():
    """Verificar configuración de almacenamiento de archivos."""
    print_section("VERIFICACIÓN DE ALMACENAMIENTO DE ARCHIVOS")
    
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.azure_production')
        import django
        django.setup()
        
        from django.conf import settings
        
        print(f"📁 DEFAULT_FILE_STORAGE: {getattr(settings, 'DEFAULT_FILE_STORAGE', 'No configurado')}")
        
        # Verificar variables de Azure Storage
        azure_vars = {
            'AZURE_STORAGE_CONNECTION_STRING': os.environ.get('AZURE_STORAGE_CONNECTION_STRING'),
            'AZURE_STORAGE_ACCOUNT_NAME': os.environ.get('AZURE_STORAGE_ACCOUNT_NAME'),
            'AZURE_STORAGE_ACCOUNT_KEY': os.environ.get('AZURE_STORAGE_ACCOUNT_KEY'),
            'AZURE_STORAGE_CONTAINER_NAME': os.environ.get('AZURE_STORAGE_CONTAINER_NAME'),
            'BLOB_ACCOUNT_NAME': os.environ.get('BLOB_ACCOUNT_NAME'),
            'BLOB_ACCOUNT_KEY': os.environ.get('BLOB_ACCOUNT_KEY'),
            'BLOB_CONTAINER_NAME': os.environ.get('BLOB_CONTAINER_NAME'),
        }
        
        print(f"\n🔧 Variables de Azure Storage:")
        configured_vars = 0
        for var_name, var_value in azure_vars.items():
            if var_value:
                if 'KEY' in var_name:
                    print(f"   ✅ {var_name}: {'*' * len(var_value)}")
                else:
                    print(f"   ✅ {var_name}: {var_value}")
                configured_vars += 1
            else:
                print(f"   ❌ {var_name}: NO CONFIGURADA")
        
        # Verificar si está usando FileSystemStorage en producción
        if 'FileSystemStorage' in getattr(settings, 'DEFAULT_FILE_STORAGE', ''):
            if configured_vars >= 3:  # Al menos 3 variables configuradas
                print(f"\n⚠️ ADVERTENCIA: Usando FileSystemStorage en producción aunque Azure Storage está configurado")
                return False
            else:
                print(f"\n✅ Usando FileSystemStorage (Azure Storage no configurado completamente)")
                return True
        else:
            print(f"\n✅ Usando Azure Storage para archivos multimedia")
            return True
            
    except Exception as e:
        print(f"❌ Error al verificar almacenamiento: {e}")
        return False

def check_azure_storage_service():
    """Verificar que el servicio de Azure Storage funciona correctamente."""
    print_section("VERIFICACIÓN DEL SERVICIO DE AZURE STORAGE")
    
    try:
        from services.storage_service import AzureStorageService
        
        # Inicializar el servicio
        storage_service = AzureStorageService()
        
        if not storage_service.client:
            print("❌ Cliente de Azure Storage no inicializado")
            return False
        
        print("✅ Cliente de Azure Storage inicializado correctamente")
        
        # Verificar configuración
        config_status = storage_service.get_configuration_status()
        print(f"\n📋 Estado de configuración:")
        for key, value in config_status.items():
            status = "✅" if value else "❌"
            print(f"   {status} {key}: {value}")
        
        return config_status['client_initialized']
        
    except Exception as e:
        print(f"❌ Error al verificar servicio de Azure Storage: {e}")
        return False

def check_content_settings_fix():
    """Verificar que la corrección de ContentSettings está aplicada."""
    print_section("VERIFICACIÓN DE CORRECCIÓN DE CONTENTSETTINGS")
    
    try:
        from services.storage_service import AzureStorageService
        import inspect
        
        # Obtener el código fuente de los métodos
        upload_file_source = inspect.getsource(AzureStorageService.upload_file)
        upload_data_source = inspect.getsource(AzureStorageService.upload_data)
        
        # Verificar que el código problemático NO está presente
        problematic_patterns = [
            "content_settings=content_settings",
            "ContentSettings(",
            "from azure.storage.blob import ContentSettings"
        ]
        
        # Verificar que el código corregido SÍ está presente
        fixed_patterns = [
            "content_disposition=",
            "blob_client.set_http_headers("
        ]
        
        # Verificar que el código problemático NO está presente
        for pattern in problematic_patterns:
            if pattern in upload_file_source or pattern in upload_data_source:
                print(f"❌ Código problemático encontrado: {pattern}")
                return False
        
        # Verificar que el código corregido SÍ está presente
        for pattern in fixed_patterns:
            if pattern in upload_file_source and pattern in upload_data_source:
                print(f"✅ Código corregido encontrado: {pattern}")
            else:
                print(f"❌ Código corregido no encontrado: {pattern}")
                return False
        
        print("✅ Corrección de ContentSettings aplicada correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error al verificar corrección de ContentSettings: {e}")
        return False

def print_section(title):
    """Imprimir una sección con formato."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def main():
    """Función principal de diagnóstico."""
    print("🚀 Iniciando diagnóstico de problemas de producción")
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Lista de verificaciones
    checks = [
        ("ALLOWED_HOSTS", check_allowed_hosts),
        ("Almacenamiento de archivos", check_file_storage),
        ("Servicio de Azure Storage", check_azure_storage_service),
        ("Corrección de ContentSettings", check_content_settings_fix),
    ]
    
    results = []
    
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ Error en verificación {check_name}: {e}")
            results.append((check_name, False))
    
    # Resumen final
    print_section("RESUMEN DE DIAGNÓSTICO")
    
    passed = 0
    failed = 0
    
    for check_name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"{status} {check_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\n📊 Resultados: {passed} pasaron, {failed} fallaron")
    
    if failed == 0:
        print("\n🎉 Todas las verificaciones pasaron exitosamente")
        return True
    else:
        print(f"\n⚠️ {failed} problema(s) encontrado(s) que requieren atención")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
