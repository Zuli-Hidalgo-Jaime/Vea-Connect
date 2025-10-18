#!/usr/bin/env python3
"""
Script para probar la conectividad a PostgreSQL con las credenciales de Azure.
"""

import os
import sys
import psycopg2
from psycopg2 import OperationalError

def test_postgresql_connection():
    """Prueba la conexión a PostgreSQL con las variables de entorno configuradas."""
    
    # Obtener variables de entorno
    db_name = os.environ.get('AZURE_POSTGRESQL_NAME')
    db_user = os.environ.get('AZURE_POSTGRESQL_USERNAME')
    db_password = os.environ.get('AZURE_POSTGRESQL_PASSWORD')
    db_host = os.environ.get('AZURE_POSTGRESQL_HOST')
    db_port = os.environ.get('DB_PORT', '5432')
    
    print("=== PRUEBA DE CONECTIVIDAD POSTGRESQL ===")
    print(f"Host: {db_host}")
    print(f"Puerto: {db_port}")
    print(f"Base de datos: {db_name}")
    print(f"Usuario: {db_user}")
    print(f"Contraseña: {'*' * len(db_password) if db_password else 'NO CONFIGURADA'}")
    print()
    
    # Verificar que todas las variables estén configuradas
    if not all([db_name, db_user, db_password, db_host]):
        print("❌ ERROR: Variables de entorno faltantes:")
        print(f"  AZURE_POSTGRESQL_NAME: {db_name or 'NO CONFIGURADA'}")
        print(f"  AZURE_POSTGRESQL_USERNAME: {db_user or 'NO CONFIGURADA'}")
        print(f"  AZURE_POSTGRESQL_PASSWORD: {'*' * len(db_password) if db_password else 'NO CONFIGURADA'}")
        print(f"  AZURE_POSTGRESQL_HOST: {db_host or 'NO CONFIGURADA'}")
        return False
    
    # Verificar que el nombre de usuario incluya el sufijo del servidor
    if '@micrositio-vea-connect-server' not in db_user:
        print("❌ ERROR: El nombre de usuario debe incluir '@micrositio-vea-connect-server'")
        print(f"  Usuario actual: {db_user}")
        print(f"  Debería ser: {db_user}@micrositio-vea-connect-server")
        return False
    
    try:
        # Intentar conexión
        print("🔌 Intentando conectar a PostgreSQL...")
        
        connection_string = f"host={db_host} port={db_port} dbname={db_name} user={db_user} password={db_password} sslmode=require"
        
        conn = psycopg2.connect(connection_string)
        
        # Crear cursor y ejecutar consulta simple
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        
        print("✅ Conexión exitosa!")
        print(f"Versión de PostgreSQL: {version[0]}")
        
        # Verificar que la base de datos existe y es accesible
        cursor.execute("SELECT current_database();")
        current_db = cursor.fetchone()
        print(f"Base de datos actual: {current_db[0]}")
        
        # Verificar tablas de Django
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE 'django_%'
            LIMIT 5;
        """)
        django_tables = cursor.fetchall()
        
        if django_tables:
            print(f"✅ Tablas de Django encontradas: {len(django_tables)}")
            for table in django_tables:
                print(f"  - {table[0]}")
        else:
            print("⚠️  No se encontraron tablas de Django (puede ser normal si no se han ejecutado migraciones)")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 Todas las pruebas de conectividad pasaron exitosamente!")
        return True
        
    except OperationalError as e:
        print(f"❌ Error de conexión: {e}")
        
        # Proporcionar sugerencias específicas
        if "password authentication failed" in str(e):
            print("\n💡 SUGERENCIA: Error de autenticación de contraseña")
            print("   - Verifica que la contraseña sea correcta")
            print("   - Asegúrate de que el nombre de usuario incluya '@micrositio-vea-connect-server'")
            print("   - Verifica que el usuario tenga permisos en la base de datos")
        elif "connection refused" in str(e):
            print("\n💡 SUGERENCIA: Conexión rechazada")
            print("   - Verifica que el host y puerto sean correctos")
            print("   - Asegúrate de que el servidor PostgreSQL esté ejecutándose")
            print("   - Verifica las reglas de firewall")
        elif "SSL" in str(e):
            print("\n💡 SUGERENCIA: Error de SSL")
            print("   - Azure PostgreSQL requiere SSL")
            print("   - Verifica que sslmode=require esté configurado")
        
        return False
        
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def main():
    """Función principal."""
    success = test_postgresql_connection()
    
    if success:
        print("\n✅ La configuración de PostgreSQL está correcta.")
        return 0
    else:
        print("\n❌ Hay problemas con la configuración de PostgreSQL.")
        print("Por favor, revisa las variables de entorno y la conectividad.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
