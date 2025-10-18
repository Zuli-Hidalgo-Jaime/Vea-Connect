#!/usr/bin/env python3
"""
Script para diagnosticar y corregir problemas de conexión a la base de datos PostgreSQL en Azure
"""

import os
import sys
import psycopg2
from psycopg2 import OperationalError
import urllib.parse
from pathlib import Path

def print_header(title):
    """Imprimir un encabezado formateado."""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print(f"{'='*60}")

def print_section(title):
    """Imprimir una sección formateada."""
    print(f"\n📋 {title}")
    print(f"{'-'*40}")

def check_environment_variables():
    """Verificar las variables de entorno de la base de datos."""
    print_section("VERIFICACIÓN DE VARIABLES DE ENTORNO")
    
    # Variables requeridas
    variables = {
        'AZURE_POSTGRESQL_HOST': os.environ.get('AZURE_POSTGRESQL_HOST'),
        'AZURE_POSTGRESQL_NAME': os.environ.get('AZURE_POSTGRESQL_NAME'),
        'AZURE_POSTGRESQL_USERNAME': os.environ.get('AZURE_POSTGRESQL_USERNAME'),
        'AZURE_POSTGRESQL_PASSWORD': os.environ.get('AZURE_POSTGRESQL_PASSWORD'),
        'DATABASE_URL': os.environ.get('DATABASE_URL'),
    }
    
    all_present = True
    for var_name, var_value in variables.items():
        if var_value:
            if 'PASSWORD' in var_name:
                print(f"✅ {var_name}: {'*' * len(var_value)}")
            else:
                print(f"✅ {var_name}: {var_value}")
        else:
            print(f"❌ {var_name}: NO CONFIGURADA")
            all_present = False
    
    return all_present, variables

def analyze_database_url(database_url):
    """Analizar la URL de la base de datos para detectar problemas."""
    print_section("ANÁLISIS DE DATABASE_URL")
    
    if not database_url:
        print("❌ DATABASE_URL no está configurada")
        return False
    
    try:
        # Parsear la URL
        parsed = urllib.parse.urlparse(database_url)
        
        print(f"Protocolo: {parsed.scheme}")
        print(f"Usuario: {parsed.username}")
        print(f"Host: {parsed.hostname}")
        print(f"Puerto: {parsed.port}")
        print(f"Base de datos: {parsed.path[1:] if parsed.path else 'None'}")
        print(f"Parámetros: {parsed.query}")
        
        # Verificar problemas comunes
        issues = []
        
        if not parsed.username:
            issues.append("❌ Usuario no especificado en la URL")
        
        if not parsed.hostname:
            issues.append("❌ Host no especificado en la URL")
        
        if not parsed.path or parsed.path == '/':
            issues.append("❌ Nombre de base de datos no especificado")
        
        if '@micrositio-vea-connect-server' not in parsed.username:
            issues.append("⚠️  El nombre de usuario no incluye el sufijo del servidor")
        
        if 'sslmode=require' not in parsed.query:
            issues.append("⚠️  SSL no está configurado como requerido")
        
        if issues:
            print("\nProblemas detectados:")
            for issue in issues:
                print(f"  {issue}")
            return False
        else:
            print("\n✅ La URL de la base de datos parece estar bien formada")
            return True
            
    except Exception as e:
        print(f"❌ Error al analizar DATABASE_URL: {e}")
        return False

def test_direct_connection(variables):
    """Probar conexión directa a PostgreSQL."""
    print_section("PRUEBA DE CONEXIÓN DIRECTA")
    
    db_host = variables['AZURE_POSTGRESQL_HOST']
    db_name = variables['AZURE_POSTGRESQL_NAME']
    db_user = variables['AZURE_POSTGRESQL_USERNAME']
    db_password = variables['AZURE_POSTGRESQL_PASSWORD']
    
    if not all([db_host, db_name, db_user, db_password]):
        print("❌ Faltan variables de entorno para la conexión directa")
        return False
    
    print(f"Host: {db_host}")
    print(f"Base de datos: {db_name}")
    print(f"Usuario: {db_user}")
    print(f"Contraseña: {'*' * len(db_password)}")
    
    try:
        # Intentar conexión directa
        connection_string = f"host={db_host} port=5432 dbname={db_name} user={db_user} password={db_password} sslmode=require"
        
        print("\n🔌 Intentando conexión...")
        conn = psycopg2.connect(connection_string)
        
        # Verificar conexión
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        
        print("✅ Conexión exitosa!")
        print(f"Versión de PostgreSQL: {version[0]}")
        
        # Verificar base de datos actual
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
            print("⚠️  No se encontraron tablas de Django")
        
        cursor.close()
        conn.close()
        return True
        
    except OperationalError as e:
        print(f"❌ Error de conexión: {e}")
        
        # Proporcionar sugerencias específicas
        error_msg = str(e).lower()
        
        if "password authentication failed" in error_msg:
            print("\n💡 DIAGNÓSTICO: Error de autenticación de contraseña")
            print("   Posibles causas:")
            print("   1. La contraseña es incorrecta")
            print("   2. El nombre de usuario no incluye el sufijo del servidor")
            print("   3. El usuario no tiene permisos en la base de datos")
            print("   4. La contraseña contiene caracteres especiales que necesitan encoding")
            
            print("\n🔧 SOLUCIONES:")
            print("   1. Verificar la contraseña en Azure Portal")
            print("   2. Asegurar que el usuario incluya '@micrositio-vea-connect-server'")
            print("   3. Resetear la contraseña del usuario en Azure PostgreSQL")
            print("   4. Verificar que el usuario tenga permisos en la base de datos")
            
        elif "connection refused" in error_msg:
            print("\n💡 DIAGNÓSTICO: Conexión rechazada")
            print("   Posibles causas:")
            print("   1. El servidor PostgreSQL no está ejecutándose")
            print("   2. El host o puerto son incorrectos")
            print("   3. Reglas de firewall bloquean la conexión")
            
        elif "ssl" in error_msg:
            print("\n💡 DIAGNÓSTICO: Error de SSL")
            print("   Azure PostgreSQL requiere SSL")
            print("   Asegúrate de que sslmode=require esté configurado")
            
        return False
        
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def generate_correct_database_url(variables):
    """Generar una URL de base de datos correcta."""
    print_section("GENERACIÓN DE DATABASE_URL CORRECTA")
    
    db_host = variables['AZURE_POSTGRESQL_HOST']
    db_name = variables['AZURE_POSTGRESQL_NAME']
    db_user = variables['AZURE_POSTGRESQL_USERNAME']
    db_password = variables['AZURE_POSTGRESQL_PASSWORD']
    
    if not all([db_host, db_name, db_user, db_password]):
        print("❌ No se pueden generar URLs sin todas las variables")
        return None
    
    # Asegurar que el usuario tenga el sufijo correcto
    if '@micrositio-vea-connect-server' not in db_user:
        db_user = f"{db_user}@micrositio-vea-connect-server"
        print(f"⚠️  Agregando sufijo al usuario: {db_user}")
    
    # Codificar la contraseña para caracteres especiales
    encoded_password = urllib.parse.quote_plus(db_password)
    
    # Generar URL
    database_url = f"postgresql://{db_user}:{encoded_password}@{db_host}:5432/{db_name}?sslmode=require"
    
    print("✅ URL generada correctamente:")
    print(f"   {database_url}")
    
    return database_url

def provide_fix_instructions():
    """Proporcionar instrucciones para corregir el problema."""
    print_section("INSTRUCCIONES DE CORRECCIÓN")
    
    print("🔧 Para corregir el problema de autenticación:")
    print()
    print("1. **Verificar en Azure Portal:**")
    print("   - Ve a Azure Portal → PostgreSQL Flexible Server")
    print("   - Verifica que el servidor esté ejecutándose")
    print("   - Ve a 'Connection security' y verifica las reglas de firewall")
    print()
    print("2. **Verificar credenciales:**")
    print("   - Ve a Azure Portal → PostgreSQL Flexible Server → Settings → Connection strings")
    print("   - Copia las credenciales correctas")
    print("   - Asegúrate de que el usuario incluya '@micrositio-vea-connect-server'")
    print()
    print("3. **Actualizar variables en Azure App Service:**")
    print("   - Ve a Azure Portal → App Service → Configuration")
    print("   - Actualiza las siguientes variables:")
    print("     * AZURE_POSTGRESQL_HOST")
    print("     * AZURE_POSTGRESQL_NAME")
    print("     * AZURE_POSTGRESQL_USERNAME (con @servidor)")
    print("     * AZURE_POSTGRESQL_PASSWORD")
    print("     * DATABASE_URL")
    print()
    print("4. **Resetear contraseña si es necesario:**")
    print("   - Ve a Azure Portal → PostgreSQL Flexible Server → Settings → Reset password")
    print("   - Genera una nueva contraseña")
    print("   - Actualiza la variable AZURE_POSTGRESQL_PASSWORD")
    print()
    print("5. **Verificar permisos del usuario:**")
    print("   - Conecta a la base de datos usando Azure Data Studio o pgAdmin")
    print("   - Verifica que el usuario tenga permisos en la base de datos")

def main():
    """Función principal."""
    print_header("DIAGNÓSTICO DE CONEXIÓN A BASE DE DATOS POSTGRESQL")
    
    # Verificar variables de entorno
    env_ok, variables = check_environment_variables()
    
    if not env_ok:
        print("\n❌ Faltan variables de entorno críticas")
        provide_fix_instructions()
        return 1
    
    # Analizar DATABASE_URL
    database_url_ok = analyze_database_url(variables['DATABASE_URL'])
    
    # Probar conexión directa
    connection_ok = test_direct_connection(variables)
    
    # Generar URL correcta si es necesario
    if not database_url_ok:
        correct_url = generate_correct_database_url(variables)
        if correct_url:
            print(f"\n📝 URL corregida para usar en Azure App Service:")
            print(f"   DATABASE_URL={correct_url}")
    
    # Proporcionar instrucciones si hay problemas
    if not connection_ok:
        provide_fix_instructions()
        return 1
    
    print("\n✅ Diagnóstico completado. La conexión a la base de datos está funcionando correctamente.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
