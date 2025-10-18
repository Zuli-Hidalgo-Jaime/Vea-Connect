#!/usr/bin/env python3
"""
Script para diagnosticar la configuración de la base de datos en el contenedor.
"""

import os
import sys

def test_database_config():
    """Prueba la configuración de la base de datos."""
    
    print("=== DIAGNOSTICO DE CONFIGURACION DE BASE DE DATOS ===")
    print()
    
    # Verificar variables individuales
    print("1. Variables individuales de PostgreSQL:")
    print("-" * 50)
    
    db_vars = {
        'AZURE_POSTGRESQL_NAME': os.environ.get('AZURE_POSTGRESQL_NAME'),
        'AZURE_POSTGRESQL_USERNAME': os.environ.get('AZURE_POSTGRESQL_USERNAME'),
        'AZURE_POSTGRESQL_PASSWORD': os.environ.get('AZURE_POSTGRESQL_PASSWORD'),
        'AZURE_POSTGRESQL_HOST': os.environ.get('AZURE_POSTGRESQL_HOST'),
        'DB_PORT': os.environ.get('DB_PORT', '5432')
    }
    
    all_individual_vars = True
    for var, value in db_vars.items():
        if value:
            if 'PASSWORD' in var:
                display_value = '*' * min(len(value), 8) + '...'
            else:
                display_value = value
            print(f"✓ {var}: {display_value}")
        else:
            print(f"✗ {var}: NO CONFIGURADA")
            all_individual_vars = False
    
    print()
    
    # Verificar DATABASE_URL
    print("2. Variable DATABASE_URL:")
    print("-" * 50)
    
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        print(f"✓ DATABASE_URL: {database_url[:50]}...")
        
        # Verificar formato
        if database_url.startswith('postgresql://'):
            print("✓ Formato correcto (postgresql://)")
        else:
            print("⚠ Formato inesperado")
    else:
        print("✗ DATABASE_URL: NO CONFIGURADA")
    
    print()
    
    # Verificar configuración de Django
    print("3. Configuración de Django:")
    print("-" * 50)
    
    try:
        # Importar configuración de Django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
        
        import django
        django.setup()
        
        from django.conf import settings
        
        # Verificar configuración de base de datos
        db_config = settings.DATABASES.get('default', {})
        
        if db_config:
            print("✓ Configuración de DATABASES encontrada:")
            print(f"  - ENGINE: {db_config.get('ENGINE', 'NO CONFIGURADO')}")
            print(f"  - NAME: {db_config.get('NAME', 'NO CONFIGURADO')}")
            print(f"  - USER: {db_config.get('USER', 'NO CONFIGURADO')}")
            print(f"  - HOST: {db_config.get('HOST', 'NO CONFIGURADO')}")
            print(f"  - PORT: {db_config.get('PORT', 'NO CONFIGURADO')}")
            print(f"  - SSL: {db_config.get('OPTIONS', {}).get('sslmode', 'NO CONFIGURADO')}")
        else:
            print("✗ No se encontró configuración de DATABASES")
            
    except Exception as e:
        print(f"✗ Error al cargar configuración de Django: {e}")
    
    print()
    
    # Resumen
    print("4. Resumen:")
    print("-" * 50)
    
    if all_individual_vars and database_url:
        print("✅ Todas las variables están configuradas correctamente")
        print("✅ DATABASE_URL está presente")
        print("✅ La aplicación debería poder conectarse a la base de datos")
        return True
    else:
        print("❌ Hay problemas con la configuración:")
        if not all_individual_vars:
            print("  - Faltan variables individuales de PostgreSQL")
        if not database_url:
            print("  - Falta DATABASE_URL")
        return False

def main():
    """Función principal."""
    success = test_database_config()
    
    if success:
        print("\n🎉 La configuración de la base de datos está correcta.")
        return 0
    else:
        print("\n❌ Hay problemas con la configuración de la base de datos.")
        print("Por favor, revisa las variables de entorno.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
