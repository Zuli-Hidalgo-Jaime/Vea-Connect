"""
Pruebas para funciones de embeddings de Azure Functions.
"""

import requests
import json
import time
from typing import Dict, Any

# Configuración
BASE_URL = "http://localhost:7074/api"
TIMEOUT = 15

def test_embeddings_stats() -> Dict[str, bool]:
    """
    Probar endpoint de estadísticas de embeddings.
    
    Returns:
        Dict[str, bool]: Resultados de las pruebas
    """
    print("=== Probando Estadísticas de Embeddings ===")
    
    try:
        url = f"{BASE_URL}/embeddings/stats"
        print(f"Probando {url}...")
        
        response = requests.get(url, timeout=TIMEOUT)
        
        if response.status_code == 200:
            print(f"✅ /embeddings/stats - OK (Status: {response.status_code})")
            try:
                data = response.json()
                print(f"  Respuesta: {json.dumps(data, indent=2, ensure_ascii=False)}")
            except:
                print(f"  Respuesta: {response.text}")
            return {"stats": True}
        else:
            print(f"❌ /embeddings/stats - Error (Status: {response.status_code})")
            print(f"  Respuesta: {response.text}")
            return {"stats": False}
            
    except Exception as e:
        print(f"❌ /embeddings/stats - Error: {e}")
        return {"stats": False}

def test_embeddings_create() -> Dict[str, bool]:
    """
    Probar endpoint de creación de embeddings.
    
    Returns:
        Dict[str, bool]: Resultados de las pruebas
    """
    print("=== Probando Creación de Embeddings ===")
    
    # Datos de prueba
    test_data = {
        "text": "Este es un texto de prueba para crear embeddings",
        "metadata": {
            "source": "test",
            "category": "prueba"
        }
    }
    
    try:
        url = f"{BASE_URL}/embeddings/create"
        print(f"Probando {url}...")
        print(f"Datos de prueba: {json.dumps(test_data, indent=2, ensure_ascii=False)}")
        
        response = requests.post(
            url, 
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            print(f"✅ /embeddings/create - OK (Status: {response.status_code})")
            try:
                data = response.json()
                print(f"  Respuesta: {json.dumps(data, indent=2, ensure_ascii=False)}")
            except:
                print(f"  Respuesta: {response.text}")
            return {"create": True}
        else:
            print(f"❌ /embeddings/create - Error (Status: {response.status_code})")
            print(f"  Respuesta: {response.text}")
            return {"create": False}
            
    except Exception as e:
        print(f"❌ /embeddings/create - Error: {e}")
        return {"create": False}

def test_embeddings_search() -> Dict[str, bool]:
    """
    Probar endpoint de búsqueda de embeddings.
    
    Returns:
        Dict[str, bool]: Resultados de las pruebas
    """
    print("=== Probando Búsqueda de Embeddings ===")
    
    # Datos de prueba
    test_data = {
        "query": "texto de prueba",
        "top_k": 5
    }
    
    try:
        url = f"{BASE_URL}/embeddings/search"
        print(f"Probando {url}...")
        print(f"Datos de prueba: {json.dumps(test_data, indent=2, ensure_ascii=False)}")
        
        response = requests.post(
            url, 
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            print(f"✅ /embeddings/search - OK (Status: {response.status_code})")
            try:
                data = response.json()
                print(f"  Respuesta: {json.dumps(data, indent=2, ensure_ascii=False)}")
            except:
                print(f"  Respuesta: {response.text}")
            return {"search": True}
        else:
            print(f"❌ /embeddings/search - Error (Status: {response.status_code})")
            print(f"  Respuesta: {response.text}")
            return {"search": False}
            
    except Exception as e:
        print(f"❌ /embeddings/search - Error: {e}")
        return {"search": False}

def test_embeddings_health() -> Dict[str, bool]:
    """
    Probar health check específico de embeddings.
    
    Returns:
        Dict[str, bool]: Resultados de las pruebas
    """
    print("=== Probando Health Check de Embeddings ===")
    
    try:
        url = f"{BASE_URL}/embeddings/health"
        print(f"Probando {url}...")
        
        response = requests.get(url, timeout=TIMEOUT)
        
        if response.status_code == 200:
            print(f"✅ /embeddings/health - OK (Status: {response.status_code})")
            try:
                data = response.json()
                print(f"  Respuesta: {json.dumps(data, indent=2, ensure_ascii=False)}")
            except:
                print(f"  Respuesta: {response.text}")
            return {"embeddings_health": True}
        else:
            print(f"❌ /embeddings/health - Error (Status: {response.status_code})")
            print(f"  Respuesta: {response.text}")
            return {"embeddings_health": False}
            
    except Exception as e:
        print(f"❌ /embeddings/health - Error: {e}")
        return {"embeddings_health": False}

def run_embeddings_tests() -> Dict[str, bool]:
    """
    Ejecuta todas las pruebas de embeddings.
    
    Returns:
        Dict[str, bool]: Resultados consolidados
    """
    print("🚀 Iniciando pruebas de embeddings...")
    print(f"URL base: {BASE_URL}")
    print(f"Timeout: {TIMEOUT} segundos")
    print()
    
    # Ejecutar pruebas
    results = {}
    
    # Health check primero
    health_result = test_embeddings_health()
    results.update(health_result)
    
    # Stats
    stats_result = test_embeddings_stats()
    results.update(stats_result)
    
    # Create (solo si health check pasa)
    if health_result.get("embeddings_health", False):
        create_result = test_embeddings_create()
        results.update(create_result)
        
        # Search (solo si create pasa)
        if create_result.get("create", False):
            search_result = test_embeddings_search()
            results.update(search_result)
    else:
        print("⚠️  Saltando pruebas de create/search debido a health check fallido")
        results.update({"create": False, "search": False})
    
    # Mostrar resumen
    print("=== Resumen de Pruebas de Embeddings ===")
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    print(f"✅ Pruebas exitosas: {passed}/{total}")
    print(f"❌ Pruebas fallidas: {total - passed}/{total}")
    
    for test_name, result in results.items():
        status = "✅" if result else "❌"
        print(f"  {status} {test_name}")
    
    return results

if __name__ == "__main__":
    run_embeddings_tests()
