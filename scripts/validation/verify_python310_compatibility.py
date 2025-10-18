#!/usr/bin/env python3
"""
Script para verificar compatibilidad específica con Python 3.10
"""

import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Verifica que esté usando Python 3.10+"""
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 10:
        print("✅ Python version is 3.10+ (REQUERIDO)")
        return True
    else:
        print("❌ Python version is NOT 3.10+ (REQUERIDO)")
        return False

def check_incompatible_dependencies():
    """Verifica que no haya dependencias incompatibles"""
    incompatible_packages = [
        "zipfile36",  # Solo para Python 2.7 y 3.6
    ]
    
    print("\n=== VERIFICACIÓN DE DEPENDENCIAS INCOMPATIBLES ===")
    all_good = True
    
    for package in incompatible_packages:
        try:
            __import__(package)
            print(f"❌ {package} está instalado (INCOMPATIBLE con Python 3.10)")
            all_good = False
        except ImportError:
            print(f"✅ {package} NO está instalado (CORRECTO)")
    
    return all_good

def check_requirements_file():
    """Verifica que requirements.txt no tenga dependencias incompatibles"""
    req_file = Path("requirements.txt")
    if not req_file.exists():
        print("❌ requirements.txt not found")
        return False
    
    content = req_file.read_text()
    
    # Verificar que no tenga zipfile36
    if "zipfile36" in content:
        print("❌ requirements.txt contiene zipfile36 (INCOMPATIBLE)")
        return False
    
    print("✅ requirements.txt no contiene dependencias incompatibles")
    return True

def check_runtime_txt():
    """Verifica que runtime.txt especifique Python 3.10"""
    runtime_file = Path("runtime.txt")
    if not runtime_file.exists():
        print("❌ runtime.txt not found")
        return False
    
    content = runtime_file.read_text().strip()
    if "python-3.10" in content:
        print(f"✅ runtime.txt specifies Python 3.10: {content}")
        return True
    else:
        print(f"❌ runtime.txt does not specify Python 3.10: {content}")
        return False

def check_click_version():
    """Verifica que click esté en una versión compatible"""
    try:
        import click
        version = click.__version__
        print(f"Click version: {version}")
        
        # Verificar que sea una versión compatible con Python 3.10
        if version.startswith("8.1."):
            print("✅ Click version is compatible with Python 3.10")
            return True
        else:
            print("❌ Click version may not be compatible with Python 3.10")
            return False
    except ImportError:
        print("⚠️ Click not installed")
        return True

def main():
    """Función principal de verificación"""
    print("=== PYTHON 3.10 COMPATIBILITY CHECK ===")
    print("REQUERIDO: Python 3.10+ para todas las dependencias")
    print()
    
    checks = [
        check_python_version(),
        check_incompatible_dependencies(),
        check_requirements_file(),
        check_runtime_txt(),
        check_click_version()
    ]
    
    print("\n=== RESUMEN ===")
    if all(checks):
        print("✅ All checks passed - FULLY COMPATIBLE with Python 3.10")
        print("🎉 Ready for deployment!")
        return 0
    else:
        print("❌ Some checks failed - NOT compatible with Python 3.10")
        print("💡 Fix the issues above before deploying")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 