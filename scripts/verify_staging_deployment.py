#!/usr/bin/env python3
"""
Script para verificar manualmente el despliegue en staging.
Ejecutar después del despliegue para verificar que todo funciona correctamente.
"""

import os
import sys
import time
import requests
import json
from pathlib import Path

def get_staging_url():
    """Obtener la URL de staging desde variables de entorno o input"""
    staging_url = os.getenv('STAGING_BASE_URL')
    if not staging_url:
        staging_url = input("Ingresa la URL de staging (ej: https://vea-connect-staging.azurewebsites.net): ").strip()
        if not staging_url:
            print("❌ URL de staging requerida")
            sys.exit(1)
    
    # Asegurar que la URL termine sin slash
    staging_url = staging_url.rstrip('/')
    return staging_url

def test_health_endpoint(staging_url):
    """Probar el endpoint de health"""
    print(f"\n🔍 Probando health endpoint: {staging_url}/health")
    
    try:
        start_time = time.time()
        response = requests.get(f"{staging_url}/health", timeout=10)
        response_time = (time.time() - start_time) * 1000
        
        print(f"  Status: {response.status_code}")
        print(f"  Response time: {response_time:.2f}ms")
        
        if response.status_code == 200:
            print("  ✅ Health check passed")
            if response_time < 300:
                print("  ✅ Response time < 300ms (p50)")
            else:
                print(f"  ⚠️ Response time {response_time:.2f}ms > 300ms")
            return True
        else:
            print(f"  ❌ Health check failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error en health check: {e}")
        return False

def test_extended_health_endpoints(staging_url):
    """Probar endpoints de health extendidos si existen"""
    print(f"\n🔍 Probando endpoints de health extendidos...")
    
    endpoints = [
        "/api/v1/health",
        "/api/whatsapp/health",
        "/health/"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.head(f"{staging_url}{endpoint}", timeout=5)
            if response.status_code in [200, 404]:  # 404 es OK si el endpoint no existe
                print(f"  {endpoint}: HTTP {response.status_code}")
            else:
                print(f"  {endpoint}: HTTP {response.status_code} ⚠️")
        except Exception as e:
            print(f"  {endpoint}: Error - {e}")

def test_document_download(staging_url):
    """Probar descarga de documentos"""
    print(f"\n🔍 Probando descarga de documentos...")
    
    # Probar con un ID de ejemplo
    test_ids = ["123", "test", "1"]
    
    for doc_id in test_ids:
        try:
            response = requests.head(f"{staging_url}/documents/download/{doc_id}", timeout=5)
            if response.status_code in [200, 302, 404]:
                print(f"  /documents/download/{doc_id}: HTTP {response.status_code}")
                if response.status_code == 302:
                    print(f"    → Redirect location: {response.headers.get('Location', 'N/A')}")
            else:
                print(f"  /documents/download/{doc_id}: HTTP {response.status_code} ⚠️")
        except Exception as e:
            print(f"  /documents/download/{doc_id}: Error - {e}")

def test_cache_stats_endpoint(staging_url):
    """Probar endpoint de estadísticas del cache (solo para A4)"""
    print(f"\n🔍 Probando endpoint de cache stats...")
    
    try:
        response = requests.get(f"{staging_url}/ops/cache/stats", timeout=10)
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"  ✅ Cache stats endpoint working")
                print(f"  Response: {json.dumps(data, indent=2)}")
                
                # Verificar si el cache está habilitado
                if data.get('enabled'):
                    print("  ✅ Cache layer enabled")
                else:
                    print(f"  ⚠️ Cache layer disabled: {data.get('reason', 'Unknown')}")
                    
            except json.JSONDecodeError:
                print(f"  ⚠️ Response no es JSON válido: {response.text[:100]}...")
        elif response.status_code == 403:
            print("  ⚠️ Endpoint requiere autenticación (esperado)")
        else:
            print(f"  ❌ Endpoint no disponible: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"  ❌ Error probando cache stats: {e}")

def test_log_sanitization():
    """Verificar que no hay secretos/PII en logs (para A3)"""
    print(f"\n🔍 Verificando saneamiento de logs...")
    
    # Esta verificación requeriría acceso a los logs de Azure
    # Por ahora, solo verificamos que el endpoint de health no expone información sensible
    print("  ℹ️ Verificación de logs requiere acceso a Azure Application Insights")
    print("  ℹ️ Revisar manualmente que no hay secretos en los logs de staging")

def test_performance_metrics(staging_url):
    """Probar métricas de rendimiento"""
    print(f"\n🔍 Probando métricas de rendimiento...")
    
    # Hacer múltiples requests para obtener métricas
    response_times = []
    
    for i in range(5):
        try:
            start_time = time.time()
            response = requests.get(f"{staging_url}/health", timeout=10)
            response_time = (time.time() - start_time) * 1000
            response_times.append(response_time)
            
            if response.status_code == 200:
                print(f"  Request {i+1}: {response_time:.2f}ms")
            else:
                print(f"  Request {i+1}: {response_time:.2f}ms (HTTP {response.status_code})")
                
        except Exception as e:
            print(f"  Request {i+1}: Error - {e}")
    
    if response_times:
        p50 = sorted(response_times)[len(response_times)//2]
        p95 = sorted(response_times)[int(len(response_times)*0.95)]
        
        print(f"\n  📊 Métricas de rendimiento:")
        print(f"    P50: {p50:.2f}ms")
        print(f"    P95: {p95:.2f}ms")
        
        if p50 < 300 and p95 < 1000:
            print(f"    ✅ Rendimiento dentro de límites aceptables")
        else:
            print(f"    ⚠️ Rendimiento fuera de límites esperados")

def main():
    """Función principal"""
    print("🚀 Verificación manual de despliegue en staging")
    print("=" * 50)
    
    # Obtener URL de staging
    staging_url = get_staging_url()
    print(f"Staging URL: {staging_url}")
    
    # Ejecutar verificaciones
    health_ok = test_health_endpoint(staging_url)
    
    if health_ok:
        test_extended_health_endpoints(staging_url)
        test_document_download(staging_url)
        test_cache_stats_endpoint(staging_url)
        test_log_sanitization()
        test_performance_metrics(staging_url)
        
        print(f"\n✅ Verificación completada")
        print(f"Si todos los checks pasaron, puedes proceder con el swap a producción")
    else:
        print(f"\n❌ Health check falló - no se puede proceder con el swap")
        print(f"Investiga los problemas en staging antes de continuar")

if __name__ == "__main__":
    main()
