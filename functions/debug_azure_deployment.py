#!/usr/bin/env python3
"""
Script para debuggear el despliegue en Azure
"""
import requests
import json
import os

def debug_azure_deployment():
    """Debuggear el despliegue en Azure."""
    print("🔍 DEBUG AZURE DEPLOYMENT")
    print("=" * 60)
    
    # URL del Function App
    function_app_url = "https://vea-functions-apis-eme0byhtbbgqgwhd.centralus-01.azurewebsites.net"
    
    print(f"📋 Function App URL: {function_app_url}")
    print()
    
    # 1. Verificar si el Function App responde
    print("1️⃣ Verificando si el Function App responde...")
    try:
        response = requests.get(function_app_url, timeout=10)
        print(f"   ✅ Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   📋 Respuesta: {response.text[:200]}...")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ No responde: {e}")
    
    print()
    
    # 2. Verificar endpoints específicos
    print("2️⃣ Verificando endpoints específicos...")
    endpoints = [
        "/api/health",
        "/api/stats", 
        "/api/embeddings/health",
        "/api/embeddings/create",
        "/api/search"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{function_app_url}{endpoint}", timeout=5)
            print(f"   📋 {endpoint}: {response.status_code}")
            if response.status_code == 404:
                print(f"      ❌ 404 - Función no encontrada")
            elif response.status_code == 500:
                print(f"      ❌ 500 - Error interno")
            elif response.status_code == 200:
                print(f"      ✅ 200 - Función funciona")
        except Exception as e:
            print(f"   ❌ {endpoint}: Error - {e}")
    
    print()
    
    # 3. Verificar si hay algún problema de configuración
    print("3️⃣ Verificando configuración...")
    try:
        # Intentar acceder a la página de administración
        admin_url = f"{function_app_url}/admin/functions"
        response = requests.get(admin_url, timeout=5)
        print(f"   📋 Admin functions: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Admin functions: Error - {e}")
    
    print()
    print("=" * 60)
    print("📋 DIAGNÓSTICO:")
    print("Si todos los endpoints dan 404:")
    print("  - Las funciones no están registradas")
    print("  - Problema de configuración en Azure")
    print("  - Bundle version incompatible")
    print()
    print("Si algunos endpoints funcionan:")
    print("  - Problema específico con ciertas funciones")
    print()
    print("🔧 SOLUCIONES:")
    print("1. Verificar Application Settings en Azure")
    print("2. Reiniciar el Function App")
    print("3. Verificar logs en Azure Portal")
    print("4. Cambiar bundle version")

if __name__ == "__main__":
    debug_azure_deployment()
