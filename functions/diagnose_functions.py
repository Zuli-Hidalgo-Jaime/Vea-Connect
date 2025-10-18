#!/usr/bin/env python3
"""
Script de diagnóstico detallado para Azure Functions v4
Identifica problemas específicos que impiden que las funciones se carguen correctamente.
"""

import sys
import os
import json
import importlib
import traceback
from pathlib import Path
from typing import Dict, List, Any

def check_python_environment():
    """Verificar el entorno de Python."""
    print("=== VERIFICACIÓN DEL ENTORNO PYTHON ===")
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    print()

def check_azure_functions_package():
    """Verificar la instalación de azure-functions."""
    print("=== VERIFICACIÓN DE AZURE FUNCTIONS ===")
    try:
        import azure.functions
        print(f"✅ azure-functions version: {azure.functions.__version__}")
        
        # Verificar si es v4
        if hasattr(azure.functions, 'FunctionApp'):
            print("✅ Azure Functions v4 (Programming Model) detectado")
        else:
            print("❌ Azure Functions v3 (Legacy Model) detectado")
            
    except ImportError as e:
        print(f"❌ Error importando azure-functions: {e}")
    except Exception as e:
        print(f"❌ Error verificando azure-functions: {e}")
    print()

def check_function_structure():
    """Verificar la estructura de las funciones."""
    print("=== VERIFICACIÓN DE ESTRUCTURA DE FUNCIONES ===")
    
    functions_dir = Path(__file__).parent
    function_dirs = []
    
    # Encontrar todas las carpetas de funciones
    for function_json_path in functions_dir.glob("*/function.json"):
        function_dir = function_json_path.parent
        function_dirs.append(function_dir)
    
    print(f"Encontradas {len(function_dirs)} carpetas de funciones:")
    
    for function_dir in sorted(function_dirs):
        function_name = function_dir.name
        print(f"\n--- {function_name} ---")
        
        # Verificar archivos requeridos
        function_json_path = function_dir / "function.json"
        init_py_path = function_dir / "__init__.py"
        
        if function_json_path.exists():
            print(f"  ✅ function.json: OK")
            try:
                with open(function_json_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                print(f"  📋 scriptFile: {config.get('scriptFile', 'No especificado')}")
                print(f"  📋 bindings: {len(config.get('bindings', []))} binding(s)")
            except Exception as e:
                print(f"  ❌ Error leyendo function.json: {e}")
        else:
            print(f"  ❌ function.json: NO ENCONTRADO")
        
        if init_py_path.exists():
            print(f"  ✅ __init__.py: OK")
            # Verificar sintaxis del archivo Python
            try:
                with open(init_py_path, 'r', encoding='utf-8') as f:
                    compile(f.read(), str(init_py_path), 'exec')
                print(f"  ✅ Sintaxis Python: OK")
            except SyntaxError as e:
                print(f"  ❌ Error de sintaxis en __init__.py: {e}")
        else:
            print(f"  ❌ __init__.py: NO ENCONTRADO")
    print()

def check_function_app_py():
    """Verificar el archivo function_app.py."""
    print("=== VERIFICACIÓN DE FUNCTION_APP.PY ===")
    
    function_app_path = Path(__file__).parent / "function_app.py"
    
    if not function_app_path.exists():
        print("❌ function_app.py: NO ENCONTRADO")
        return
    
    print("✅ function_app.py: ENCONTRADO")
    
    try:
        with open(function_app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar sintaxis
        compile(content, str(function_app_path), 'exec')
        print("✅ Sintaxis Python: OK")
        
        # Verificar importaciones
        if "from ." in content:
            print("⚠️  Importaciones relativas detectadas (pueden causar problemas)")
        
        # Verificar decoradores
        if "@app.function_name" in content:
            print("✅ Decoradores de Azure Functions v4 detectados")
        else:
            print("❌ No se encontraron decoradores de Azure Functions v4")
            
    except SyntaxError as e:
        print(f"❌ Error de sintaxis en function_app.py: {e}")
    except Exception as e:
        print(f"❌ Error verificando function_app.py: {e}")
    print()

def check_imports():
    """Verificar importaciones de módulos."""
    print("=== VERIFICACIÓN DE IMPORTACIONES ===")
    
    modules_to_check = [
        'azure.functions',
        'azure.core',
        'azure.search.documents',
        'openai',
        'requests',
        'json',
        'logging'
    ]
    
    for module in modules_to_check:
        try:
            importlib.import_module(module)
            print(f"✅ {module}: OK")
        except ImportError as e:
            print(f"❌ {module}: {e}")
        except Exception as e:
            print(f"⚠️  {module}: {e}")
    print()

def check_host_json():
    """Verificar configuración de host.json."""
    print("=== VERIFICACIÓN DE HOST.JSON ===")
    
    host_json_path = Path(__file__).parent / "host.json"
    
    if not host_json_path.exists():
        print("❌ host.json: NO ENCONTRADO")
        return
    
    try:
        with open(host_json_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print("✅ host.json: ENCONTRADO")
        print(f"📋 version: {config.get('version', 'No especificado')}")
        print(f"📋 extensionBundle: {config.get('extensionBundle', 'No especificado')}")
        
        # Verificar configuración de logging
        logging_config = config.get('logging', {})
        if 'logLevel' in logging_config:
            print(f"📋 logLevel configurado para {len(logging_config['logLevel'])} funciones")
        
    except json.JSONDecodeError as e:
        print(f"❌ Error de JSON en host.json: {e}")
    except Exception as e:
        print(f"❌ Error verificando host.json: {e}")
    print()

def check_requirements_txt():
    """Verificar requirements.txt."""
    print("=== VERIFICACIÓN DE REQUIREMENTS.TXT ===")
    
    requirements_path = Path(__file__).parent / "requirements.txt"
    
    if not requirements_path.exists():
        print("❌ requirements.txt: NO ENCONTRADO")
        return
    
    try:
        with open(requirements_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print("✅ requirements.txt: ENCONTRADO")
        print(f"📋 {len(lines)} dependencias listadas")
        
        # Buscar azure-functions
        azure_functions_found = False
        for line in lines:
            line = line.strip()
            if line.startswith('azure-functions'):
                print(f"📋 {line}")
                azure_functions_found = True
                break
        
        if not azure_functions_found:
            print("❌ azure-functions no encontrado en requirements.txt")
            
    except Exception as e:
        print(f"❌ Error verificando requirements.txt: {e}")
    print()

def check_local_settings():
    """Verificar local.settings.json."""
    print("=== VERIFICACIÓN DE LOCAL.SETTINGS.JSON ===")
    
    settings_path = Path(__file__).parent / "local.settings.json"
    
    if not settings_path.exists():
        print("❌ local.settings.json: NO ENCONTRADO")
        return
    
    try:
        with open(settings_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print("✅ local.settings.json: ENCONTRADO")
        
        values = config.get('Values', {})
        runtime = values.get('FUNCTIONS_WORKER_RUNTIME', 'No especificado')
        print(f"📋 FUNCTIONS_WORKER_RUNTIME: {runtime}")
        
        if runtime != 'python':
            print("❌ FUNCTIONS_WORKER_RUNTIME no está configurado como 'python'")
        
        # Verificar variables críticas
        critical_vars = [
            'AzureWebJobsStorage',
            'AZURE_OPENAI_ENDPOINT',
            'AZURE_OPENAI_API_KEY'
        ]
        
        for var in critical_vars:
            if var in values:
                print(f"✅ {var}: Configurado")
            else:
                print(f"❌ {var}: No configurado")
                
    except json.JSONDecodeError as e:
        print(f"❌ Error de JSON en local.settings.json: {e}")
    except Exception as e:
        print(f"❌ Error verificando local.settings.json: {e}")
    print()

def main():
    """Ejecutar todas las verificaciones."""
    print("🔍 DIAGNÓSTICO DETALLADO DE AZURE FUNCTIONS")
    print("=" * 60)
    
    check_python_environment()
    check_azure_functions_package()
    check_function_structure()
    check_function_app_py()
    check_imports()
    check_host_json()
    check_requirements_txt()
    check_local_settings()
    
    print("=" * 60)
    print("✅ Diagnóstico completado")

if __name__ == "__main__":
    main()
