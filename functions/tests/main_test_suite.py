"""
Suite principal de pruebas para Azure Functions.

Descubre sub‐módulos pytest automáticamente.
Uso: pytest -q tests/
"""

import sys
from importlib import import_module

def discover_test_modules():
    """Importa todos los módulos de prueba para que pytest los descubra."""
    test_modules = [
        "tests.health_tests",
        "tests.embeddings_tests", 
        "tests.whatsapp_tests",
    ]
    
    for module_name in test_modules:
        try:
            import_module(module_name)
            print(f"✅ Módulo de prueba cargado: {module_name}")
        except ImportError as e:
            print(f"⚠️  Módulo de prueba no encontrado: {module_name} - {e}")

if __name__ == "__main__":
    print("=== Suite de Pruebas de Azure Functions ===")
    discover_test_modules()
    print("✅ Todos los módulos de prueba cargados")
else:
    # Importar automáticamente cuando se importa el módulo
    discover_test_modules()
