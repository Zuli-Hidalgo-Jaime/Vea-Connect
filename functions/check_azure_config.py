#!/usr/bin/env python3
"""
Script para verificar la configuración del Function App en Azure
"""
import requests
import json
import os

def check_azure_function_app():
    """Verificar la configuración del Function App en Azure."""
    print("🔍 VERIFICACIÓN DE CONFIGURACIÓN AZURE")
    print("=" * 60)
    
    # URL del Function App
    function_app_url = "https://vea-functions-apis-eme0byhtbbgqgwhd.centralus-01.azurewebsites.net"
    
    # Endpoints a verificar
    endpoints = [
        "/api/health",
        "/api/stats", 
        "/api/embeddings/health"
    ]
    
    print(f"📋 Function App URL: {function_app_url}")
    print()
    
    # Verificar si el Function App responde
    try:
        response = requests.get(f"{function_app_url}/api/health", timeout=10)
        print(f"✅ Health endpoint responde: {response.status_code}")
        if response.status_code == 200:
            print(f"📋 Respuesta: {response.text[:200]}...")
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ No se puede conectar al Function App: {e}")
    
    print()
    
    # Verificar otros endpoints
    for endpoint in endpoints:
        try:
            response = requests.get(f"{function_app_url}{endpoint}", timeout=5)
            print(f"📋 {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint}: Error - {e}")
    
    print()
    print("=" * 60)
    print("📋 DIAGNÓSTICO:")
    print("1. Si no responde: El Function App no está funcionando")
    print("2. Si responde 404: Las funciones no están registradas")
    print("3. Si responde 500: Error en las funciones")
    print("4. Si responde 200: Las funciones están funcionando")
    print()
    print("🔧 PRÓXIMOS PASOS:")
    print("- Verificar logs en Azure Portal")
    print("- Revisar Application Insights")
    print("- Verificar configuración del Function App")

if __name__ == "__main__":
    check_azure_function_app()
