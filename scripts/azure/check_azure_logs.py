#!/usr/bin/env python
"""
Script para verificar logs de Azure y diagnosticar errores 500
"""
import os
import sys
import requests
import json
from datetime import datetime, timedelta
from pathlib import Path

# Agregar el directorio del proyecto al path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

def check_azure_app_service_status(app_service_url):
    """Verificar el estado del Azure App Service"""
    try:
        response = requests.get(app_service_url, timeout=10)
        print(f"📊 Estado del App Service: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ App Service está funcionando")
            return True
        else:
            print(f"⚠️  App Service responde con código: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al conectar con App Service: {e}")
        return False

def check_specific_endpoint(app_service_url, endpoint="/login/"):
    """Verificar un endpoint específico"""
    try:
        url = f"{app_service_url.rstrip('/')}{endpoint}"
        print(f"🔍 Verificando endpoint: {url}")
        
        response = requests.get(url, timeout=10)
        print(f"📊 Respuesta del endpoint: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Endpoint responde correctamente")
            return True
        elif response.status_code == 500:
            print("❌ Error 500 en el endpoint")
            print("📋 Contenido de la respuesta:")
            print(response.text[:500])  # Primeros 500 caracteres
            return False
        else:
            print(f"⚠️  Endpoint responde con código: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al verificar endpoint: {e}")
        return False

def check_azure_environment_variables():
    """Verificar variables de entorno de Azure"""
    print("🔧 Variables de entorno de Azure:")
    
    # Variables importantes para la aplicación
    important_vars = [
        'WEBSITE_HOSTNAME',
        'AZURE_POSTGRESQL_NAME',
        'AZURE_POSTGRESQL_USERNAME',
        'AZURE_POSTGRESQL_PASSWORD',
        'AZURE_POSTGRESQL_HOST',
        'SECRET_KEY',
        'DEBUG',
        'ALLOWED_HOSTS'
    ]
    
    for var in important_vars:
        value = os.environ.get(var)
        if value:
            # Ocultar valores sensibles
            if 'PASSWORD' in var or 'SECRET' in var or 'KEY' in var:
                print(f"   {var}: {'*' * len(value)}")
            else:
                print(f"   {var}: {value}")
        else:
            print(f"   {var}: ❌ No definida")

def check_database_connection_string():
    """Verificar la cadena de conexión de la base de datos"""
    print("\n🗄️  Verificación de base de datos:")
    
    # Verificar variables de PostgreSQL
    db_name = os.environ.get('AZURE_POSTGRESQL_NAME')
    db_user = os.environ.get('AZURE_POSTGRESQL_USERNAME')
    db_password = os.environ.get('AZURE_POSTGRESQL_PASSWORD')
    db_host = os.environ.get('AZURE_POSTGRESQL_HOST')
    
    if all([db_name, db_user, db_password, db_host]):
        print("✅ Todas las variables de PostgreSQL están configuradas")
        
        # Intentar conexión básica (sin usar Django)
        try:
            import psycopg2
            conn = psycopg2.connect(
                dbname=db_name,
                user=db_user,
                password=db_password,
                host=db_host,
                port=5432,
                sslmode='require'
            )
            conn.close()
            print("✅ Conexión a PostgreSQL exitosa")
            return True
        except Exception as e:
            print(f"❌ Error de conexión a PostgreSQL: {e}")
            return False
    else:
        print("❌ Faltan variables de configuración de PostgreSQL")
        return False

def generate_diagnostic_report():
    """Generar un reporte de diagnóstico"""
    print("📋 Generando reporte de diagnóstico...")
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'app_service_url': 'https://veaconnect-webapp-prod-c7aaezbce3ftacdp.centralus-01.azurewebsites.net',
        'checks': {}
    }
    
    # Verificar App Service
    app_service_url = report['app_service_url']
    report['checks']['app_service'] = check_azure_app_service_status(app_service_url)
    
    # Verificar endpoint de login
    report['checks']['login_endpoint'] = check_specific_endpoint(app_service_url, '/login/')
    
    # Verificar variables de entorno
    check_azure_environment_variables()
    
    # Verificar base de datos
    report['checks']['database'] = check_database_connection_string()
    
    return report

def suggest_solutions(report):
    """Sugerir soluciones basadas en el diagnóstico"""
    print("\n💡 Soluciones sugeridas:")
    
    if not report['checks'].get('app_service', False):
        print("1. 🔧 Verificar el estado del Azure App Service en el portal de Azure")
        print("2. 🔧 Revisar la configuración de la aplicación en Azure")
    
    if not report['checks'].get('login_endpoint', False):
        print("3. 🔧 Aplicar migraciones en producción usando el script apply_production_migrations.py")
        print("4. 🔧 Verificar logs de Azure App Service para más detalles del error 500")
        print("5. 🔧 Verificar que todos los archivos estáticos estén desplegados")
    
    if not report['checks'].get('database', False):
        print("6. 🔧 Verificar la configuración de la base de datos PostgreSQL en Azure")
        print("7. 🔧 Verificar las variables de entorno en Azure App Service")
    
    print("\n📝 Comandos recomendados:")
    print("   python scripts/diagnostics/check_production_db.py")
    print("   python scripts/deployment/apply_production_migrations.py")
    print("   python scripts/diagnostics/check_login_issue.py")

def main():
    """Función principal"""
    print("🔍 Diagnóstico de Azure App Service")
    print("=" * 50)
    
    # Generar reporte de diagnóstico
    report = generate_diagnostic_report()
    
    # Mostrar resumen
    print("\n📊 Resumen del diagnóstico:")
    for check, result in report['checks'].items():
        status = "✅" if result else "❌"
        print(f"   {status} {check}")
    
    # Sugerir soluciones
    suggest_solutions(report)
    
    print("\n🏁 Diagnóstico completado")

if __name__ == "__main__":
    main() 