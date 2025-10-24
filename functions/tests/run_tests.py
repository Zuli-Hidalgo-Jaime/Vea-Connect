#!/usr/bin/env python3
"""
Script principal para ejecutar todas las pruebas de Azure Functions.

Este script utiliza la nueva estructura modular de pruebas para ejecutar
todas las pruebas de manera organizada y consolidada.
"""

import sys
import time
from typing import Dict, Any

# Importar módulos de prueba
from tests.health_tests import run_health_tests
from tests.embeddings_tests import run_embeddings_tests
from tests.whatsapp_tests import run_whatsapp_tests

def print_header():
    """Imprimir encabezado del script."""
    print("=" * 60)
    print("🚀 SUITE DE PRUEBAS DE AZURE FUNCTIONS")
    print("=" * 60)
    print("📋 Ejecutando pruebas con estructura modular")
    print("📅 Fecha:", time.strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)
    print()

def print_summary(all_results: Dict[str, Dict[str, bool]]):
    """Imprimir resumen final de todas las pruebas."""
    print("=" * 60)
    print("📊 RESUMEN FINAL DE PRUEBAS")
    print("=" * 60)
    
    total_passed = 0
    total_failed = 0
    total_tests = 0
    
    for test_suite, results in all_results.items():
        suite_passed = sum(1 for result in results.values() if result)
        suite_total = len(results)
        suite_failed = suite_total - suite_passed
        
        total_passed += suite_passed
        total_failed += suite_failed
        total_tests += suite_total
        
        status = "✅" if suite_failed == 0 else "⚠️" if suite_passed > 0 else "❌"
        print(f"{status} {test_suite.upper()}: {suite_passed}/{suite_total} exitosas")
    
    print("-" * 60)
    overall_status = "✅" if total_failed == 0 else "⚠️" if total_passed > 0 else "❌"
    print(f"{overall_status} TOTAL: {total_passed}/{total_tests} pruebas exitosas")
    
    if total_failed > 0:
        print(f"❌ {total_failed} pruebas fallidas")
    
    print("=" * 60)

def main():
    """Función principal del script."""
    print_header()
    
    all_results = {}
    
    try:
        # Ejecutar pruebas de health check
        print("🔍 Ejecutando pruebas de Health Check...")
        health_results = run_health_tests()
        all_results["health"] = health_results
        print()
        
        # Ejecutar pruebas de embeddings
        print("🧠 Ejecutando pruebas de Embeddings...")
        embeddings_results = run_embeddings_tests()
        all_results["embeddings"] = embeddings_results
        print()
        
        # Ejecutar pruebas de WhatsApp
        print("📱 Ejecutando pruebas de WhatsApp...")
        whatsapp_results = run_whatsapp_tests()
        all_results["whatsapp"] = whatsapp_results
        print()
        
        # Mostrar resumen final
        print_summary(all_results)
        
        # Determinar código de salida
        total_failed = sum(
            sum(1 for result in results.values() if not result)
            for results in all_results.values()
        )
        
        if total_failed == 0:
            print("🎉 ¡Todas las pruebas pasaron exitosamente!")
            sys.exit(0)
        else:
            print(f"⚠️  {total_failed} pruebas fallaron. Revisa los logs arriba.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Pruebas interrumpidas por el usuario.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
