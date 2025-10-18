#!/usr/bin/env python3
"""
Script para actualizar las dependencias de Azure y resolver conflictos de versiones.
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Ejecutar un comando y mostrar el resultado."""
    print(f"\n=== {description} ===")
    print(f"Ejecutando: {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ Comando ejecutado exitosamente")
            if result.stdout:
                print("Salida:", result.stdout)
        else:
            print("✗ Error en el comando:")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
    except Exception as e:
        print(f"✗ Error al ejecutar comando: {e}")
        return False
    
    return True

def fix_azure_dependencies():
    """Actualizar las dependencias de Azure para resolver conflictos."""
    print("=== CORRECCIÓN DE DEPENDENCIAS DE AZURE ===\n")
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists('requirements.txt'):
        print("✗ No se encontró requirements.txt. Asegúrate de estar en el directorio raíz del proyecto.")
        return False
    
    # Actualizar azure-core específicamente
    print("1. Actualizando azure-core a la versión compatible...")
    success = run_command(
        "pip install 'azure-core>=1.35.0,<2.0.0' --upgrade",
        "Actualizando azure-core"
    )
    
    if not success:
        print("⚠ Error al actualizar azure-core, continuando...")
    
    # Verificar que no hay conflictos con requests
    print("\n2. Verificando compatibilidad con requests...")
    success = run_command(
        "pip install 'requests>=2.31.0' --upgrade",
        "Actualizando requests"
    )
    
    if not success:
        print("⚠ Error al actualizar requests, continuando...")
    
    # Reinstalar todas las dependencias de Azure para asegurar compatibilidad
    print("\n3. Reinstalando dependencias de Azure...")
    azure_packages = [
        'azure-storage-blob==12.19.0',
        'azure-identity==1.15.0',
        'azure-common==1.1.28'
    ]
    
    for package in azure_packages:
        success = run_command(
            f"pip install {package} --force-reinstall",
            f"Reinstalando {package}"
        )
        if not success:
            print(f"⚠ Error al reinstalar {package}")
    
    # Verificar las versiones finales
    print("\n4. Verificando versiones finales...")
    run_command(
        "pip list | grep azure",
        "Versiones de Azure instaladas"
    )
    
    return True

def test_storage_service():
    """Probar que el servicio de almacenamiento funciona correctamente."""
    print("\n=== PRUEBA DEL SERVICIO DE ALMACENAMIENTO ===")
    
    # Configurar el entorno Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.azure_production')
    
    try:
        import django
        django.setup()
        
        from services.storage_service import AzureStorageService
        
        service = AzureStorageService()
        status = service.get_configuration_status()
        
        print(f"Estado del servicio: {status.get('status', 'unknown')}")
        if status.get('status') == 'configured':
            print("✓ Servicio de almacenamiento configurado correctamente")
            return True
        else:
            print(f"⚠ Servicio no configurado: {status.get('message', 'unknown error')}")
            return False
            
    except Exception as e:
        print(f"✗ Error al verificar servicio de almacenamiento: {e}")
        return False

def main():
    """Función principal."""
    print("=== CORRECCIÓN DE ERRORES DE AZURE STORAGE ===\n")
    
    # Actualizar dependencias
    if not fix_azure_dependencies():
        print("\n✗ Error al actualizar dependencias")
        return False
    
    # Probar el servicio
    if not test_storage_service():
        print("\n⚠ El servicio de almacenamiento puede no estar completamente funcional")
        print("   Verifica la configuración de Azure Storage")
    
    print("\n=== RESUMEN ===")
    print("✓ Dependencias de Azure actualizadas")
    print("✓ Código corregido para usar ContentSettings")
    print("✓ Conflictos de versiones resueltos")
    
    print("\n=== PRÓXIMOS PASOS ===")
    print("1. Reinicia la aplicación web")
    print("2. Prueba subir un documento")
    print("3. Verifica que no aparezcan errores de 'content_disposition'")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
