"""
Pruebas para funciones de WhatsApp de Azure Functions.
"""

import requests
import json
import time
from typing import Dict, Any

# Configuración
BASE_URL = "http://localhost:7074/api"
TIMEOUT = 15

def test_whatsapp_event_grid() -> Dict[str, bool]:
    """
    Probar función de Event Grid para WhatsApp.
    
    Returns:
        Dict[str, bool]: Resultados de las pruebas
    """
    print("=== Probando Event Grid de WhatsApp ===")
    
    # Datos de prueba para Event Grid
    test_event = {
        "id": "test-event-id",
        "eventType": "Microsoft.Communication.RecordingFileStatusUpdated",
        "eventTime": "2024-01-01T12:00:00Z",
        "data": {
            "recordingStatus": "available",
            "recordingUri": "https://example.com/recording.wav",
            "recordingChunks": [
                {
                    "documentId": "test-doc-id",
                    "index": 0,
                    "endReason": "StopRecording"
                }
            ]
        },
        "subject": "recording/test-recording-id",
        "topic": "/subscriptions/test-sub/resourceGroups/test-rg/providers/Microsoft.Communication/communicationServices/test-acs"
    }
    
    try:
        # Probar endpoint de Event Grid
        url = f"{BASE_URL}/runtime/webhooks/eventgrid?functionName=whatsapp_event_grid_trigger"
        print(f"Probando {url}...")
        print(f"Datos de prueba: {json.dumps(test_event, indent=2, ensure_ascii=False)}")
        
        response = requests.post(
            url, 
            json=test_event,
            headers={
                "Content-Type": "application/json",
                "aeg-event-type": "Notification"
            },
            timeout=TIMEOUT
        )
        
        if response.status_code in [200, 202]:
            print(f"✅ Event Grid - OK (Status: {response.status_code})")
            try:
                data = response.json()
                print(f"  Respuesta: {json.dumps(data, indent=2, ensure_ascii=False)}")
            except:
                print(f"  Respuesta: {response.text}")
            return {"event_grid": True}
        else:
            print(f"❌ Event Grid - Error (Status: {response.status_code})")
            print(f"  Respuesta: {response.text}")
            return {"event_grid": False}
            
    except Exception as e:
        print(f"❌ Event Grid - Error: {e}")
        return {"event_grid": False}

def test_whatsapp_health() -> Dict[str, bool]:
    """
    Probar health check específico de WhatsApp.
    
    Returns:
        Dict[str, bool]: Resultados de las pruebas
    """
    print("=== Probando Health Check de WhatsApp ===")
    
    try:
        url = f"{BASE_URL}/whatsapp/health"
        print(f"Probando {url}...")
        
        response = requests.get(url, timeout=TIMEOUT)
        
        if response.status_code == 200:
            print(f"✅ /whatsapp/health - OK (Status: {response.status_code})")
            try:
                data = response.json()
                print(f"  Respuesta: {json.dumps(data, indent=2, ensure_ascii=False)}")
            except:
                print(f"  Respuesta: {response.text}")
            return {"whatsapp_health": True}
        else:
            print(f"❌ /whatsapp/health - Error (Status: {response.status_code})")
            print(f"  Respuesta: {response.text}")
            return {"whatsapp_health": False}
            
    except Exception as e:
        print(f"❌ /whatsapp/health - Error: {e}")
        return {"whatsapp_health": False}

def test_whatsapp_function_status() -> Dict[str, bool]:
    """
    Probar el estado de la función de WhatsApp a través del health check general.
    
    Returns:
        Dict[str, bool]: Resultados de las pruebas
    """
    print("=== Probando Estado de Función WhatsApp ===")
    
    try:
        url = f"{BASE_URL}/health"
        print(f"Probando {url}...")
        
        response = requests.get(url, timeout=TIMEOUT)
        
        if response.status_code == 200:
            try:
                data = response.json()
                functions = data.get('functions', [])
                
                if 'whatsapp_event_grid_trigger' in functions:
                    print(f"✅ Función WhatsApp encontrada en health check")
                    print(f"  Funciones disponibles: {functions}")
                    return {"function_status": True}
                else:
                    print(f"❌ Función WhatsApp no encontrada en health check")
                    print(f"  Funciones disponibles: {functions}")
                    return {"function_status": False}
            except:
                print(f"❌ No se pudo parsear respuesta JSON")
                return {"function_status": False}
        else:
            print(f"❌ Health check - Error (Status: {response.status_code})")
            return {"function_status": False}
            
    except Exception as e:
        print(f"❌ Health check - Error: {e}")
        return {"function_status": False}

def run_whatsapp_tests() -> Dict[str, bool]:
    """
    Ejecuta todas las pruebas de WhatsApp.
    
    Returns:
        Dict[str, bool]: Resultados consolidados
    """
    print("🚀 Iniciando pruebas de WhatsApp...")
    print(f"URL base: {BASE_URL}")
    print(f"Timeout: {TIMEOUT} segundos")
    print()
    
    # Ejecutar pruebas
    results = {}
    
    # Verificar estado de función primero
    status_result = test_whatsapp_function_status()
    results.update(status_result)
    
    # Health check específico
    health_result = test_whatsapp_health()
    results.update(health_result)
    
    # Event Grid (solo si la función está disponible)
    if status_result.get("function_status", False):
        event_result = test_whatsapp_event_grid()
        results.update(event_result)
    else:
        print("⚠️  Saltando prueba de Event Grid debido a función no disponible")
        results.update({"event_grid": False})
    
    # Mostrar resumen
    print("=== Resumen de Pruebas de WhatsApp ===")
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    print(f"✅ Pruebas exitosas: {passed}/{total}")
    print(f"❌ Pruebas fallidas: {total - passed}/{total}")
    
    for test_name, result in results.items():
        status = "✅" if result else "❌"
        print(f"  {status} {test_name}")
    
    return results

if __name__ == "__main__":
    run_whatsapp_tests()
