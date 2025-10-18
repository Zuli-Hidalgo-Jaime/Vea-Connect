#!/usr/bin/env python3
"""
Script para ejecutar tests actualizados.

Este script ejecuta todos los tests que han sido actualizados o creados
para verificar que las correcciones de linter y nuevas funcionalidades
funcionan correctamente.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description):
    """Ejecutar comando y mostrar resultado."""
    print(f"\n🔍 {description}")
    print("-" * 60)
    print(f"Comando: {command}")
    print("-" * 60)
    
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        if result.returncode == 0:
            print("✅ ÉXITO")
            if result.stdout:
                print("Salida:")
                print(result.stdout)
        else:
            print("❌ ERROR")
            if result.stderr:
                print("Error:")
                print(result.stderr)
            if result.stdout:
                print("Salida:")
                print(result.stdout)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def main():
    """Función principal."""
    print("🚀 Ejecutando Tests Actualizados")
    print("=" * 60)
    
    # Lista de tests a ejecutar
    tests = [
        # Tests de correcciones de linter
        (
            "python -m pytest tests/unit/test_linter_fixes.py -v",
            "Tests de correcciones de linter"
        ),
        
        # Tests de funcionalidad de almacenamiento de texto extraído
        (
            "python -m pytest tests/unit/test_azure_blob_storage_extracted_text.py -v",
            "Tests de almacenamiento de texto extraído"
        ),
        
        # Tests de integración del flujo completo
        (
            "python -m pytest tests/integration/test_extracted_text_workflow.py -v",
            "Tests de integración del flujo de texto extraído"
        ),
        
        # Tests existentes actualizados
        (
            "python -m pytest tests/unit/test_azure_vision_service.py::TestAzureVisionService::test_extract_text_from_pdf_success -v",
            "Test actualizado de Azure Vision Service"
        ),
        
        # Tests de Azure Search (existentes)
        (
            "python -m pytest tests/unit/test_azure_search_provider.py -v",
            "Tests de Azure Search Provider"
        ),
        
        # Tests de Embedding Manager (existentes)
        (
            "python -m pytest tests/unit/test_embedding_manager.py -v",
            "Tests de Embedding Manager"
        ),
        
        # Tests de integración generales
        (
            "python -m pytest tests/integration/test_api_integration.py -v",
            "Tests de integración de APIs"
        ),
    ]
    
    results = []
    
    for command, description in tests:
        success = run_command(command, description)
        results.append((description, success))
    
    # Resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE TESTS")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for description, success in results:
        status = "✅ PASÓ" if success else "❌ FALLÓ"
        print(f"  {description}: {status}")
    
    print(f"\n🎯 Resultado: {passed}/{total} tests pasaron")
    
    if passed == total:
        print("🎉 ¡TODOS LOS TESTS PASARON EXITOSAMENTE!")
        print("✅ El proyecto está listo para despliegue")
        return 0
    else:
        print("⚠️ Algunos tests fallaron - revisar antes del despliegue")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 