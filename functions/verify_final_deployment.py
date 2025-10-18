#!/usr/bin/env python3
"""
Verificación final antes del despliegue
"""
import json
from pathlib import Path

def verify_final_deployment():
    """Verificación final antes del despliegue."""
    print("🔍 VERIFICACIÓN FINAL ANTES DEL DESPLIEGUE")
    print("=" * 60)
    
    functions_dir = Path(__file__).parent
    
    # Verificar host.json
    host_json_path = functions_dir / "host.json"
    if host_json_path.exists():
        with open(host_json_path, 'r', encoding='utf-8') as f:
            host_config = json.load(f)
        
        version = host_config.get('version', '')
        extension_bundle = host_config.get('extensionBundle', {})
        bundle_version = extension_bundle.get('version', '')
        
        print(f"✅ host.json version: {version}")
        print(f"✅ extensionBundle version: {bundle_version}")
        
        if '3.*' in bundle_version:
            print("✅ Configuración correcta para Azure Functions v3")
        else:
            print("❌ Configuración incorrecta para Azure Functions v3")
            return False
    else:
        print("❌ host.json no encontrado")
        return False
    
    # Verificar requirements.txt
    requirements_path = functions_dir / "requirements.txt"
    if requirements_path.exists():
        with open(requirements_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'azure-functions==1.17.0' in content:
            print("✅ azure-functions==1.17.0 (correcto para v3)")
        else:
            print("❌ Versión incorrecta de azure-functions")
            return False
    else:
        print("❌ requirements.txt no encontrado")
        return False
    
    # Verificar function_app.py
    function_app_path = functions_dir / "function_app.py"
    if function_app_path.exists():
        with open(function_app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if '@app.function_name' in content:
            print("❌ function_app.py contiene decoradores (debe estar vacío para v3)")
            return False
        else:
            print("✅ function_app.py sin decoradores (correcto para v3)")
    else:
        print("❌ function_app.py no encontrado")
        return False
    
    # Verificar funciones
    function_dirs = []
    for function_json_path in functions_dir.glob("*/function.json"):
        function_dir = function_json_path.parent
        function_dirs.append(function_dir)
    
    print(f"\n✅ Encontradas {len(function_dirs)} funciones:")
    for function_dir in sorted(function_dirs):
        print(f"  - {function_dir.name}")
    
    print("\n" + "=" * 60)
    print("✅ VERIFICACIÓN COMPLETADA - LISTO PARA DESPLEGAR")
    print("\n📋 COMANDO DE DESPLIEGUE:")
    print("func azure functionapp publish vea-functions-apis-eme0byhtbbgqgwhd")
    
    return True

if __name__ == "__main__":
    verify_final_deployment()
