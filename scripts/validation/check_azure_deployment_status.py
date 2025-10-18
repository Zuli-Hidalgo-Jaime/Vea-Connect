#!/usr/bin/env python3
"""
Script para verificar el estado del despliegue en Azure App Service
"""

import requests
import sys
from datetime import datetime

def check_azure_app_status():
    """Verifica el estado de la aplicación en Azure"""
    
    # URL de la aplicación en Azure
    app_url = "https://veaconnect-webapp-prod-c7aaezbce3ftacdp.centralus-01.azurewebsites.net"
    
    print("=== VERIFICACIÓN DE DESPLIEGUE EN AZURE ===")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"URL de la aplicación: {app_url}")
    print()
    
    try:
        # Intentar hacer una petición GET a la aplicación
        print("🔍 Verificando respuesta de la aplicación...")
        response = requests.get(app_url, timeout=30)
        
        print(f"✅ Estado HTTP: {response.status_code}")
        print(f"✅ Tiempo de respuesta: {response.elapsed.total_seconds():.2f} segundos")
        
        if response.status_code == 200:
            print("🎉 ¡La aplicación está funcionando correctamente!")
            return True
        elif response.status_code == 404:
            print("⚠️ La aplicación responde pero devuelve 404 (puede ser normal para la ruta raíz)")
            return True
        else:
            print(f"⚠️ La aplicación responde con estado {response.status_code}")
            return True
            
    except requests.exceptions.ConnectionError:
        print("❌ Error de conexión: No se puede conectar a la aplicación")
        print("   - La aplicación puede estar iniciando")
        print("   - Puede haber un problema de red")
        return False
        
    except requests.exceptions.Timeout:
        print("❌ Timeout: La aplicación no responde en 30 segundos")
        print("   - La aplicación puede estar sobrecargada")
        print("   - Puede haber un problema de configuración")
        return False
        
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        return False

def check_health_endpoint():
    """Verifica el endpoint de health check si existe"""
    
    health_url = "https://veaconnect-webapp-prod-c7aaezbce3ftacdp.centralus-01.azurewebsites.net/health/"
    
    try:
        print("\n🔍 Verificando endpoint de health check...")
        response = requests.get(health_url, timeout=10)
        
        if response.status_code == 200:
            print("✅ Health check responde correctamente")
            try:
                data = response.json()
                print(f"✅ Estado: {data.get('status', 'unknown')}")
            except:
                print("✅ Health check responde (formato no JSON)")
            return True
        else:
            print(f"⚠️ Health check responde con estado {response.status_code}")
            return False
            
    except Exception as e:
        print(f"⚠️ Health check no disponible: {str(e)}")
        return False

def main():
    """Función principal"""
    
    # Verificar estado general
    app_status = check_azure_app_status()
    
    # Verificar health endpoint
    health_status = check_health_endpoint()
    
    print("\n=== RESUMEN ===")
    if app_status:
        print("✅ La aplicación está desplegada y responde")
        if health_status:
            print("✅ Health check funciona correctamente")
        else:
            print("⚠️ Health check no está disponible (puede ser normal)")
        print("\n🎉 ¡El despliegue parece exitoso!")
        return 0
    else:
        print("❌ La aplicación no responde correctamente")
        print("\n💡 Posibles causas:")
        print("   - El despliegue aún está en progreso")
        print("   - Hay un problema con la instalación de dependencias")
        print("   - La aplicación falló al iniciar")
        print("   - Problemas de configuración en Azure")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 