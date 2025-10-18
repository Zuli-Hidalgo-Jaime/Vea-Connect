#!/usr/bin/env python3
"""
Script de verificación final para Azure Functions v3 (Legacy Model)
"""
import os
import json
from pathlib import Path

def verify_v3_setup():
    """Verificar que la configuración v3 esté correcta."""
    print("🔍 VERIFICACIÓN FINAL - AZURE FUNCTIONS V3")
    print("=" * 60)
    
    functions_dir = Path(__file__).parent
    function_dirs = []
    
    # Encontrar todas las carpetas de funciones
    for function_json_path in functions_dir.glob("*/function.json"):
        function_dir = function_json_path.parent
        function_dirs.append(function_dir)
    
    print(f"Encontradas {len(function_dirs)} funciones:")
    
    all_valid = True
    
    for function_dir in sorted(function_dirs):
        function_name = function_dir.name
        function_json_path = function_dir / "function.json"
        init_py_path = function_dir / "__init__.py"
        
        print(f"\n--- {function_name} ---")
        
        # Verificar function.json
        if function_json_path.exists():
            try:
                with open(function_json_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # Verificar scriptFile
                script_file = config.get('scriptFile', '')
                if script_file == '__init__.py':
                    print(f"  ✅ scriptFile: {script_file}")
                else:
                    print(f"  ❌ scriptFile incorrecto: {script_file}")
                    all_valid = False
                
                # Verificar bindings
                bindings = config.get('bindings', [])
                if len(bindings) >= 1:
                    main_binding = bindings[0]
                    binding_type = main_binding.get('type', '')
                    print(f"  ✅ Binding principal: {binding_type}")
                    
                    # Verificar binding de salida para HTTP
                    if binding_type == 'httpTrigger':
                        if len(bindings) >= 2 and bindings[1].get('type') == 'http':
                            print(f"  ✅ Binding de salida HTTP: OK")
                        else:
                            print(f"  ❌ Falta binding de salida HTTP")
                            all_valid = False
                else:
                    print(f"  ❌ No hay bindings configurados")
                    all_valid = False
                    
            except Exception as e:
                print(f"  ❌ Error leyendo function.json: {e}")
                all_valid = False
        else:
            print(f"  ❌ function.json no encontrado")
            all_valid = False
        
        # Verificar __init__.py
        if init_py_path.exists():
            print(f"  ✅ __init__.py: OK")
        else:
            print(f"  ❌ __init__.py no encontrado")
            all_valid = False
    
    # Verificar function_app.py
    function_app_path = functions_dir / "function_app.py"
    if function_app_path.exists():
        try:
            with open(function_app_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if "@app.function_name" in content:
                print(f"\n❌ function_app.py contiene decoradores (debe estar vacío para v3)")
                all_valid = False
            else:
                print(f"\n✅ function_app.py sin decoradores (correcto para v3)")
        except Exception as e:
            print(f"\n❌ Error verificando function_app.py: {e}")
            all_valid = False
    
    print("\n" + "=" * 60)
    if all_valid:
        print("✅ CONFIGURACIÓN V3 CORRECTA")
        print("\n📋 RESUMEN:")
        print("- Todas las funciones tienen function.json válido")
        print("- Todos los function.json tienen scriptFile: __init__.py")
        print("- Todos los function.json tienen bindings correctos")
        print("- function_app.py no tiene decoradores")
        print("- Estructura compatible con Azure Functions v3")
        print("\n🚀 LISTO PARA DESPLEGAR")
    else:
        print("❌ HAY PROBLEMAS EN LA CONFIGURACIÓN")
        print("\n📋 REVISAR:")
        print("- Archivos function.json con errores")
        print("- Archivos __init__.py faltantes")
        print("- function_app.py con decoradores")
    
    return all_valid

if __name__ == "__main__":
    verify_v3_setup()
