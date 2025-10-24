"""
Pruebas para endpoints de health check de Azure Functions.
"""

import requests
import json
import time
from typing import Dict, Any

# Configuración
BASE_URL = "http://localhost:7074/api"
TIMEOUT = 15

def test_health_endpoints() -> Dict[str, bool]:
    """
    Probar todos los endpoints de health check.
    
    Returns:
        Dict[str, bool]: Resultados de las pruebas
    """
    print("=== Probando Health Checks ===")
    
    health_endpoints = [
        "/health",
        "/embeddings/health", 
        "/whatsapp/health"
    ]
    
    results = {}
    
    for endpoint in health_endpoints:
        try:
            url = f"{BASE_URL}{endpoint}"
            print(f"Probando {url}...")
            
            response = requests.get(url, timeout=TIMEOUT)
            
            if response.status_code == 200:
                print(f"✅ {endpoint} - OK (Status: {response.status_code})")
                results[endpoint] = True
                
                try:
                    data = response.json()
                    print(f"  Respuesta: {json.dumps(data, indent=2, ensure_ascii=False)}")
                except:
                    print(f"  Respuesta: {response.text}")
            else:
                print(f"❌ {endpoint} - Error (Status: {response.status_code})")
                print(f"  Respuesta: {response.text}")
                results[endpoint] = False
                
        except requests.exceptions.ConnectionError:
            print(f"❌ {endpoint} - Error de conexión (¿están las funciones ejecutándose?)")
            results[endpoint] = False
        except requests.exceptions.Timeout:
            print(f"❌ {endpoint} - Timeout")
            results[endpoint] = False
        except Exception as e:
            print(f"❌ {endpoint} - Error: {e}")
            results[endpoint] = False
            
        print()
    
    return results

def test_function_health() -> Dict[str, bool]:
    """
    Prueba rápida de health check general.
    
    Returns:
        Dict[str, bool]: Resultados de las pruebas
    """
    print("=== Prueba Rápida de Health Check ===")
    
    try:
        url = f"{BASE_URL}/health"
        print(f"Probando {url}...")
        
        response = requests.get(url, timeout=TIMEOUT)
        
        if response.status_code == 200:
            print(f"✅ Health check - OK (Status: {response.status_code})")
            try:
                data = response.json()
                print(f"  Funciones disponibles: {data.get('functions', [])}")
            except:
                print(f"  Respuesta: {response.text}")
            return {"health": True}
        else:
            print(f"❌ Health check - Error (Status: {response.status_code})")
            return {"health": False}
            
    except Exception as e:
        print(f"❌ Health check - Error: {e}")
        return {"health": False}

def run_health_tests() -> Dict[str, bool]:
    """
    Ejecuta todas las pruebas de health check.
    
    Returns:
        Dict[str, bool]: Resultados consolidados
    """
    print("🚀 Iniciando pruebas de health check...")
    print(f"URL base: {BASE_URL}")
    print(f"Timeout: {TIMEOUT} segundos")
    print()
    
    # Ejecutar pruebas
    health_results = test_health_endpoints()
    quick_results = test_function_health()
    
    # Consolidar resultados
    all_results = {**health_results, **quick_results}
    
    # Mostrar resumen
    print("=== Resumen de Health Checks ===")
    passed = sum(1 for result in all_results.values() if result)
    total = len(all_results)
    
    print(f"✅ Pruebas exitosas: {passed}/{total}")
    print(f"❌ Pruebas fallidas: {total - passed}/{total}")
    
    for endpoint, result in all_results.items():
        status = "✅" if result else "❌"
        print(f"  {status} {endpoint}")
    
    return all_results

if __name__ == "__main__":
    run_health_tests()
