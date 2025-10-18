#!/usr/bin/env python3
"""
Script para limpiar archivos function.json que causan conflictos en Azure Functions v4
"""
import os
import shutil
from pathlib import Path

def cleanup_function_json():
    """Eliminar archivos function.json que causan conflictos en v4."""
    print("🧹 LIMPIEZA DE ARCHIVOS FUNCTION.JSON")
    print("=" * 50)
    
    functions_dir = Path(__file__).parent
    function_dirs = []
    
    # Encontrar todas las carpetas de funciones
    for function_json_path in functions_dir.glob("*/function.json"):
        function_dir = function_json_path.parent
        function_dirs.append(function_dir)
    
    print(f"Encontradas {len(function_dirs)} carpetas con function.json:")
    
    for function_dir in sorted(function_dirs):
        function_name = function_dir.name
        function_json_path = function_dir / "function.json"
        
        print(f"\n--- {function_name} ---")
        
        if function_json_path.exists():
            try:
                # Crear backup antes de eliminar
                backup_path = function_json_path.with_suffix('.json.backup')
                shutil.copy2(function_json_path, backup_path)
                print(f"  📋 Backup creado: {backup_path.name}")
                
                # Eliminar function.json
                os.remove(function_json_path)
                print(f"  ✅ function.json eliminado")
                
            except Exception as e:
                print(f"  ❌ Error eliminando function.json: {e}")
        else:
            print(f"  ⚠️  function.json no encontrado")
    
    print("\n" + "=" * 50)
    print("✅ Limpieza completada")
    print("\n📋 IMPORTANTE:")
    print("- Los archivos function.json han sido eliminados")
    print("- Se crearon backups con extensión .backup")
    print("- Ahora usa function_app.py con decoradores v4")
    print("- Las funciones se detectarán correctamente")

if __name__ == "__main__":
    cleanup_function_json()
