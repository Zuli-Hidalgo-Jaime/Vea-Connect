#!/usr/bin/env python3
"""
Script para corregir archivos function.json en Azure Functions v3
"""
import os
import json
import shutil
from pathlib import Path

def fix_function_json():
    """Corregir archivos function.json para Azure Functions v3."""
    print("🔧 CORRECCIÓN DE ARCHIVOS FUNCTION.JSON")
    print("=" * 50)
    
    functions_dir = Path(__file__).parent
    function_dirs = []
    
    # Encontrar todas las carpetas de funciones
    for function_json_path in functions_dir.glob("*/function.json"):
        function_dir = function_json_path.parent
        function_dirs.append(function_dir)
    
    print(f"Encontradas {len(function_dirs)} carpetas de funciones:")
    
    for function_dir in sorted(function_dirs):
        function_name = function_dir.name
        function_json_path = function_dir / "function.json"
        init_py_path = function_dir / "__init__.py"
        
        print(f"\n--- {function_name} ---")
        
        if not function_json_path.exists():
            print(f"  ❌ function.json no encontrado")
            continue
            
        if not init_py_path.exists():
            print(f"  ❌ __init__.py no encontrado")
            continue
        
        try:
            # Leer el archivo function.json actual
            with open(function_json_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Verificar si tiene scriptFile
            if 'scriptFile' not in config:
                print(f"  ⚠️  Agregando scriptFile: __init__.py")
                config['scriptFile'] = "__init__.py"
            
            # Verificar bindings
            if 'bindings' not in config or not config['bindings']:
                print(f"  ❌ No hay bindings configurados")
                continue
            
            # Corregir binding específico según el tipo de función
            main_binding = config['bindings'][0]
            binding_type = main_binding.get('type', '')
            
            if binding_type == 'httpTrigger':
                # Corregir HTTP trigger
                if 'name' not in main_binding:
                    main_binding['name'] = 'req'
                if 'direction' not in main_binding:
                    main_binding['direction'] = 'in'
                if 'authLevel' not in main_binding:
                    main_binding['authLevel'] = 'anonymous'
                if 'methods' not in main_binding:
                    main_binding['methods'] = ['get', 'post']
                
                # Agregar binding de salida si no existe
                if len(config['bindings']) == 1:
                    config['bindings'].append({
                        "type": "http",
                        "direction": "out",
                        "name": "$return"
                    })
                    print(f"  ✅ Agregado binding de salida HTTP")
                
            elif binding_type == 'eventGridTrigger':
                # Corregir Event Grid trigger
                if 'name' not in main_binding:
                    main_binding['name'] = 'event'
                if 'direction' not in main_binding:
                    main_binding['direction'] = 'in'
                print(f"  ✅ Event Grid trigger configurado correctamente")
            
            # Guardar el archivo corregido
            with open(function_json_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            print(f"  ✅ function.json corregido y guardado")
            print(f"  📋 scriptFile: {config.get('scriptFile', 'No especificado')}")
            print(f"  📋 bindings: {len(config['bindings'])} binding(s)")
            
        except json.JSONDecodeError as e:
            print(f"  ❌ Error de JSON en function.json: {e}")
        except Exception as e:
            print(f"  ❌ Error corrigiendo function.json: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Corrección completada")
    print("\n📋 PRÓXIMOS PASOS:")
    print("1. Eliminar function_app.py con decoradores")
    print("2. Usar function_app_v3.py (sin decoradores)")
    print("3. Verificar que cada función tenga su __init__.py")
    print("4. Desplegar nuevamente")

if __name__ == "__main__":
    fix_function_json()
