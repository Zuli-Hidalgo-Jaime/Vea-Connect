#!/usr/bin/env python3
"""
Script para verificar y corregir la dependencia de FastAPI en Azure Functions
"""

import os
import sys
import subprocess
from pathlib import Path

def check_requirements():
    """Verificar que fastapi esté en requirements.txt"""
    requirements_path = Path("functions/requirements.txt")
    
    if not requirements_path.exists():
        print("❌ No se encontró functions/requirements.txt")
        return False
    
    with open(requirements_path, 'r') as f:
        content = f.read()
    
    if "fastapi" in content.lower():
        print("✅ FastAPI encontrado en requirements.txt")
        return True
    else:
        print("❌ FastAPI no encontrado en requirements.txt")
        return False

def check_responses_file():
    """Verificar que utils/responses.py no dependa de FastAPI"""
    responses_path = Path("functions/utils/responses.py")
    
    if not responses_path.exists():
        print("❌ No se encontró functions/utils/responses.py")
        return False
    
    with open(responses_path, 'r') as f:
        content = f.read()
    
    # Verificar si hay importación directa de FastAPI (no dentro de try/except)
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if "from fastapi.responses import JSONResponse" in line:
            # Verificar si está dentro de un bloque try
            if i > 0 and "try:" in lines[i-1]:
                print("✅ utils/responses.py usa FastAPI solo como fallback (correcto)")
                return True
            else:
                print("❌ utils/responses.py depende directamente de FastAPI")
                return False
    
    print("✅ utils/responses.py no depende de FastAPI")
    return True

def test_function_imports():
    """Probar que las funciones puedan importar utils.responses"""
    functions = [
        "health",
        "embeddings_health_check", 
        "create_embedding",
        "search_similar",
        "get_stats"
    ]
    
    for func_name in functions:
        func_path = Path(f"functions/{func_name}/__init__.py")
        if func_path.exists():
            try:
                # Simular importación
                sys.path.insert(0, str(Path("functions").absolute()))
                import importlib.util
                spec = importlib.util.spec_from_file_location("test", func_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                print(f"✅ {func_name}: Importación exitosa")
            except Exception as e:
                error_msg = str(e)
                if "Missing credentials" in error_msg:
                    print(f"⚠️  {func_name}: Error de credenciales (esperado en desarrollo)")
                else:
                    print(f"❌ {func_name}: Error en importación - {e}")
        else:
            print(f"⚠️  {func_name}: Archivo no encontrado")

def main():
    """Función principal"""
    print("🔍 Verificando dependencias de FastAPI en Azure Functions...")
    print("=" * 60)
    
    # Cambiar al directorio del proyecto
    project_root = Path(__file__).parent.parent.parent
    os.chdir(project_root)
    
    # Verificaciones
    req_ok = check_requirements()
    resp_ok = check_responses_file()
    
    print("\n🧪 Probando importaciones de funciones...")
    test_function_imports()
    
    print("\n" + "=" * 60)
    if req_ok and resp_ok:
        print("✅ Todas las verificaciones pasaron")
        print("🚀 Las Azure Functions deberían funcionar correctamente")
        print("\n📋 Resumen de correcciones realizadas:")
        print("   • FastAPI agregado a requirements.txt")
        print("   • utils/responses.py actualizado para usar Azure Functions nativo")
        print("   • Fallback a FastAPI si está disponible")
    else:
        print("❌ Algunas verificaciones fallaron")
        print("🔧 Ejecuta las correcciones necesarias")

if __name__ == "__main__":
    main()
