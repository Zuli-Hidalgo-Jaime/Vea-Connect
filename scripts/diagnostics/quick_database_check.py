#!/usr/bin/env python3
"""
Diagnóstico rápido de conexión a la base de datos PostgreSQL
"""

import os
import sys
import psycopg2
from psycopg2 import OperationalError
import urllib.parse

def print_header(title):
    """Imprimir un encabezado formateado."""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print(f"{'='*60}")

def check_azure_variables():
    """Verificar variables de entorno de Azure."""
    print("📋 VERIFICACIÓN DE VARIABLES DE ENTORNO")
    print("-" * 40)
    
    variables = {
        'AZURE_POSTGRESQL_HOST': os.environ.get('AZURE_POSTGRESQL_HOST'),
        'AZURE_POSTGRESQL_NAME': os.environ.get('AZURE_POSTGRESQL_NAME'),
        'AZURE_POSTGRESQL_USERNAME': os.environ.get('AZURE_POSTGRESQL_USERNAME'),
        'AZURE_POSTGRESQL_PASSWORD': os.environ.get('AZURE_POSTGRESQL_PASSWORD'),
        'DATABASE_URL': os.environ.get('DATABASE_URL'),
    }
    
    missing_vars = []
    for var_name, var_value in variables.items():
        if var_value:
            if 'PASSWORD' in var_name:
                print(f"✅ {var_name}: {'*' * len(var_value)}")
            else:
                print(f"✅ {var_name}: {var_value}")
        else:
            print(f"❌ {var_name}: NO CONFIGURADA")
            missing_vars.append(var_name)
    
    return len(missing_vars) == 0, variables

def analyze_database_url(database_url):
    """Analizar la URL de la base de datos."""
    print("\n🔍 ANÁLISIS DE DATABASE_URL")
    print("-" * 40)
    
    if not database_url:
        print("❌ DATABASE_URL no está configurada")
        return False
    
    try:
        parsed = urllib.parse.urlparse(database_url)
        
        print(f"Protocolo: {parsed.scheme}")
        print(f"Usuario: {parsed.username}")
        print(f"Host: {parsed.hostname}")
        print(f"Puerto: {parsed.port}")
        print(f"Base de datos: {parsed.path[1:] if parsed.path else 'None'}")
        print(f"Parámetros: {parsed.query}")
        
        issues = []
        
        if not parsed.username:
            issues.append("❌ Usuario no especificado")
        
        if not parsed.hostname:
            issues.append("❌ Host no especificado")
        
        if not parsed.path or parsed.path == '/':
            issues.append("❌ Nombre de base de datos no especificado")
        
        if '@micrositio-vea-connect-server' not in parsed.username:
            issues.append("⚠️  Usuario sin sufijo del servidor")
        
        if 'sslmode=require' not in parsed.query:
            issues.append("⚠️  SSL no configurado como requerido")
        
        if issues:
            print("\nProblemas detectados:")
            for issue in issues:
                print(f"  {issue}")
            return False
        else:
            print("\n✅ URL bien formada")
            return True
            
    except Exception as e:
        print(f"❌ Error al analizar URL: {e}")
        return False

def test_connection(variables):
    """Probar conexión directa a PostgreSQL."""
    print("\n🔌 PRUEBA DE CONEXIÓN")
    print("-" * 40)
    
    db_host = variables['AZURE_POSTGRESQL_HOST']
    db_name = variables['AZURE_POSTGRESQL_NAME']
    db_user = variables['AZURE_POSTGRESQL_USERNAME']
    db_password = variables['AZURE_POSTGRESQL_PASSWORD']
    
    if not all([db_host, db_name, db_user, db_password]):
        print("❌ Faltan variables para la conexión")
        return False
    
    print(f"Host: {db_host}")
    print(f"Base de datos: {db_name}")
    print(f"Usuario: {db_user}")
    print(f"Contraseña: {'*' * len(db_password)}")
    
    try:
        connection_string = f"host={db_host} port=5432 dbname={db_name} user={db_user} password={db_password} sslmode=require"
        
        print("\n🔌 Conectando...")
        conn = psycopg2.connect(connection_string)
        
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        
        print("✅ Conexión exitosa!")
        print(f"Versión: {version[0]}")
        
        cursor.execute("SELECT current_database();")
        current_db = cursor.fetchone()
        print(f"Base de datos actual: {current_db[0]}")
        
        cursor.close()
        conn.close()
        return True
        
    except OperationalError as e:
        print(f"❌ Error de conexión: {e}")
        
        error_msg = str(e).lower()
        
        if "password authentication failed" in error_msg:
            print("\n💡 DIAGNÓSTICO: Error de autenticación")
            print("   Posibles causas:")
            print("   1. Contraseña incorrecta")
            print("   2. Usuario sin sufijo '@micrositio-vea-connect-server'")
            print("   3. Usuario sin permisos")
            print("   4. Caracteres especiales en contraseña")
            
        elif "connection refused" in error_msg:
            print("\n💡 DIAGNÓSTICO: Conexión rechazada")
            print("   Posibles causas:")
            print("   1. Servidor no ejecutándose")
            print("   2. Host/puerto incorrectos")
            print("   3. Firewall bloqueando")
            
        elif "ssl" in error_msg:
            print("\n💡 DIAGNÓSTICO: Error de SSL")
            print("   Azure PostgreSQL requiere SSL")
            
        return False
        
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def generate_fix_suggestions(variables):
    """Generar sugerencias de corrección."""
    print("\n🔧 SUGERENCIAS DE CORRECCIÓN")
    print("-" * 40)
    
    db_host = variables['AZURE_POSTGRESQL_HOST']
    db_name = variables['AZURE_POSTGRESQL_NAME']
    db_user = variables['AZURE_POSTGRESQL_USERNAME']
    db_password = variables['AZURE_POSTGRESQL_PASSWORD']
    
    if all([db_host, db_name, db_user, db_password]):
        # Asegurar sufijo correcto
        if '@micrositio-vea-connect-server' not in db_user:
            db_user = f"{db_user}@micrositio-vea-connect-server"
        
        # Codificar contraseña
        encoded_password = urllib.parse.quote_plus(db_password)
        
        # Generar URL correcta
        database_url = f"postgresql://{db_user}:{encoded_password}@{db_host}:5432/{db_name}?sslmode=require"
        
        print("📝 DATABASE_URL corregida:")
        print(f"   {database_url}")
        
        print("\n📋 Variables para Azure App Service:")
        print(f"   AZURE_POSTGRESQL_HOST={db_host}")
        print(f"   AZURE_POSTGRESQL_NAME={db_name}")
        print(f"   AZURE_POSTGRESQL_USERNAME={db_user}")
        print(f"   AZURE_POSTGRESQL_PASSWORD={db_password}")
        print(f"   DATABASE_URL={database_url}")
    else:
        print("❌ No se pueden generar sugerencias sin todas las variables")

def main():
    """Función principal."""
    print_header("DIAGNÓSTICO RÁPIDO DE BASE DE DATOS")
    
    # Verificar variables
    env_ok, variables = check_azure_variables()
    
    if not env_ok:
        print("\n❌ Faltan variables críticas")
        print("💡 Ejecuta el script desde Azure App Service o configura las variables localmente")
        return 1
    
    # Analizar DATABASE_URL
    url_ok = analyze_database_url(variables['DATABASE_URL'])
    
    # Probar conexión
    connection_ok = test_connection(variables)
    
    # Generar sugerencias si hay problemas
    if not connection_ok:
        generate_fix_suggestions(variables)
        return 1
    
    print("\n✅ Diagnóstico completado. La conexión está funcionando correctamente.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
