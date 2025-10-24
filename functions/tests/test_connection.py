#!/usr/bin/env python3
"""
Script simple para diagnosticar problemas de conectividad con Azure Functions.
"""

import requests
import socket
import sys

def test_port_connection(host, port):
    """Probar si el puerto está abierto."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        print(f"Error probando puerto: {e}")
        return False

def test_http_connection(url):
    """Probar conexión HTTP."""
    try:
        response = requests.get(url, timeout=5)
        return response.status_code, response.text
    except requests.exceptions.ConnectionError:
        return None, "Error de conexión"
    except requests.exceptions.Timeout:
        return None, "Timeout"
    except Exception as e:
        return None, str(e)

def main():
    """Función principal."""
    print("🔍 Diagnóstico de Conectividad - Azure Functions")
    print("=" * 50)
    
    host = "localhost"
    port = 7074
    base_url = f"http://{host}:{port}/api"
    
    # 1. Probar puerto
    print(f"\n1. Probando puerto {port}...")
    if test_port_connection(host, port):
        print(f"✅ Puerto {port} está abierto")
    else:
        print(f"❌ Puerto {port} está cerrado o bloqueado")
        print("   Asegúrate de que las funciones estén ejecutándose:")
        print("   cd functions && func start --port 7074")
        return
    
    # 2. Probar endpoints básicos
    endpoints = [
        "/health",
        "/embeddings/health",
        "/embeddings/stats"
    ]
    
    print(f"\n2. Probando endpoints HTTP...")
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        print(f"\nProbando: {url}")
        
        status, response = test_http_connection(url)
        
        if status:
            print(f"✅ Status: {status}")
            print(f"   Respuesta: {response[:200]}...")
        else:
            print(f"❌ Error: {response}")
    
    # 3. Recomendaciones
    print(f"\n3. Recomendaciones:")
    print("   - Si el puerto está cerrado: Ejecuta 'func start --port 7074'")
    print("   - Si hay errores de conexión: Verifica el firewall")
    print("   - Si las funciones no responden: Revisa los logs de func")

if __name__ == "__main__":
    main() 