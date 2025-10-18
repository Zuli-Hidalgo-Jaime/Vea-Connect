#!/usr/bin/env python3
"""
Script simple para verificar la estructura de Azure Functions v4 sin ejecutar dependencias externas.
"""

import os
import sys

def check_function_structure():
    """Verifica que la estructura de las funciones esté correcta."""
    print("🔍 Verificando estructura de Azure Functions v4...")
    
    # Verificar archivos principales
    required_files = [
        "function_app.py",
        "host.json",
        "requirements.txt",
        "embedding_api_function_traditional.py",
        "whatsapp_event_grid_trigger/__init__.py"
    ]
    
    print("\n📁 Archivos requeridos:")
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} - NO ENCONTRADO")
    
    # Verificar que no exista function.json (debe ser v4)
    v3_files = [
        "whatsapp_event_grid_trigger/function.json"
    ]
    
    print("\n🚫 Archivos v3 (no deben existir):")
    for file_path in v3_files:
        if os.path.exists(file_path):
            print(f"  ❌ {file_path} - DEBE ELIMINARSE (es v3)")
        else:
            print(f"  ✅ {file_path} - NO EXISTE (correcto para v4)")
    
    # Verificar contenido de function_app.py
    print("\n📝 Verificando function_app.py:")
    try:
        with open("function_app.py", "r", encoding="utf-8") as f:
            content = f.read()
            
        checks = [
            ("app = func.FunctionApp()", "Creación de la app"),
            ("@app.function_name", "Decorador function_name"),
            ("@app.route", "Decorador route"),
            ("@app.event_grid_trigger", "Decorador event_grid_trigger"),
            ("import embedding_api_function_traditional", "Importación de embeddings"),
            ("import whatsapp_event_grid_trigger", "Importación de WhatsApp")
        ]
        
        for check, description in checks:
            if check in content:
                print(f"  ✅ {description}")
            else:
                print(f"  ❌ {description} - NO ENCONTRADO")
                
    except Exception as e:
        print(f"  ❌ Error leyendo function_app.py: {e}")
    
    # Verificar contenido de whatsapp_event_grid_trigger/__init__.py
    print("\n📝 Verificando whatsapp_event_grid_trigger/__init__.py:")
    try:
        with open("whatsapp_event_grid_trigger/__init__.py", "r", encoding="utf-8") as f:
            content = f.read()
            
        checks = [
            ("@app.function_name", "Decorador function_name"),
            ("@app.event_grid_trigger", "Decorador event_grid_trigger"),
            ("from function_app import app", "Importación de app")
        ]
        
        for check, description in checks:
            if check in content:
                print(f"  ✅ {description}")
            else:
                print(f"  ❌ {description} - NO ENCONTRADO")
                
    except Exception as e:
        print(f"  ❌ Error leyendo __init__.py: {e}")
    
    print("\n🎯 Verificación de estructura completada")

if __name__ == "__main__":
    check_function_structure()
    print("\n📋 Resumen:")
    print("✅ Si todos los archivos están presentes y no hay archivos v3, la estructura es correcta")
    print("📝 Para desplegar: func azure functionapp publish vea-functions-apis")
    print("🔧 Para probar localmente: func start")
