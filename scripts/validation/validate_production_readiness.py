#!/usr/bin/env python3
"""
Script de validación para verificar que todas las variables de entorno
necesarias estén configuradas antes del despliegue a producción.
"""

import os
import sys
from typing import List, Tuple

def check_required_variables() -> List[Tuple[str, bool, str]]:
    """
    Verifica que todas las variables de entorno requeridas estén configuradas.
    
    Returns:
        Lista de tuplas (variable, está_presente, valor_o_error)
    """
    # Variables críticas (requeridas)
    required_vars = [
        'AZURE_POSTGRESQL_NAME',
        'AZURE_POSTGRESQL_USERNAME', 
        'AZURE_POSTGRESQL_PASSWORD',
        'AZURE_POSTGRESQL_HOST',
        'SECRET_KEY',
        'ACS_CONNECTION_STRING',
        'AZURE_OPENAI_ENDPOINT',
        'AZURE_OPENAI_API_KEY',
        'DATABASE_URL'
    ]
    
    # Variables opcionales (advertencia si no están)
    optional_vars = [
        'AZURE_STORAGE_CONNECTION_STRING',
        'AZURE_REDIS_CONNECTIONSTRING'
    ]
    
    results = []
    
    # Verificar variables requeridas
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            # Ocultar valores sensibles
            if 'PASSWORD' in var or 'KEY' in var or 'SECRET' in var:
                display_value = '*' * min(len(value), 8) + '...'
            else:
                display_value = value
            results.append((var, True, display_value))
        else:
            results.append((var, False, 'NO CONFIGURADA'))
    
    # Verificar variables opcionales
    for var in optional_vars:
        value = os.environ.get(var)
        if value:
            # Ocultar valores sensibles
            if 'PASSWORD' in var or 'KEY' in var or 'SECRET' in var:
                display_value = '*' * min(len(value), 8) + '...'
            else:
                display_value = value
            results.append((var, True, display_value))
        else:
            results.append((var, False, 'OPCIONAL - NO CONFIGURADA'))
    
    return results

def validate_postgresql_username(username: str) -> Tuple[bool, str]:
    """
    Valida que el nombre de usuario de PostgreSQL incluya el sufijo del servidor.
    
    Args:
        username: Nombre de usuario a validar
        
    Returns:
        Tupla (es_válido, mensaje_error)
    """
    if not username:
        return False, "Nombre de usuario vacío"
    
    if '@micrositio-vea-connect-server' not in username:
        return False, f"El nombre de usuario debe incluir '@micrositio-vea-connect-server'. Actual: {username}"
    
    return True, "OK"

def main():
    """Función principal del script de validación."""
    print("=== VALIDACIÓN DE VARIABLES DE ENTORNO PARA PRODUCCIÓN ===\n")
    
    # Verificar variables requeridas
    results = check_required_variables()
    
    all_valid = True
    print("Variables de entorno requeridas:")
    print("-" * 60)
    
    for var, is_present, value in results:
        if 'OPCIONAL' in value:
            # Variable opcional
            status = "⚠️" if not is_present else "✓"
            print(f"{status} {var}: {value}")
        else:
            # Variable requerida
            status = "✓" if is_present else "✗"
            print(f"{status} {var}: {value}")
            if not is_present:
                all_valid = False
    
    print()
    
    # Validar formato del nombre de usuario de PostgreSQL
    username = os.environ.get('AZURE_POSTGRESQL_USERNAME')
    if username:
        is_valid, message = validate_postgresql_username(username)
        print(f"Validación del nombre de usuario PostgreSQL: {message}")
        if not is_valid:
            all_valid = False
            print("  ✗ El nombre de usuario debe incluir '@micrositio-vea-connect-server'")
    else:
        print("✗ AZURE_POSTGRESQL_USERNAME no está configurada")
        all_valid = False
    
    print()
    
    # Verificar archivos críticos
    critical_files = [
        'run.sh',
        'Dockerfile',
        'requirements.txt',
        'manage.py',
        'config/settings/production.py'
    ]
    
    print("Archivos críticos:")
    print("-" * 60)
    
    for file_path in critical_files:
        if os.path.exists(file_path):
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} - NO ENCONTRADO")
            all_valid = False
    
    print()
    
    # Resultado final
    if all_valid:
        print("🎉 TODAS LAS VALIDACIONES PASARON EXITOSAMENTE")
        print("La aplicación está lista para el despliegue a producción.")
        return 0
    else:
        print("❌ SE ENCONTRARON ERRORES EN LA VALIDACIÓN")
        print("Por favor, corrija los problemas antes del despliegue.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
