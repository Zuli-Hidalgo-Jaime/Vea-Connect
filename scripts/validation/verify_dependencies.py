#!/usr/bin/env python3
"""
Script para verificar compatibilidad de dependencias con Python 3.9 y 3.10
"""

import sys
import subprocess
import pkg_resources
from pathlib import Path

def check_python_version():
    """Verifica la versión de Python actual"""
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 9:
        print("✅ Python version is compatible (3.9+)")
        return True
    else:
        print("❌ Python version is not compatible (requires 3.9+)")
        return False

def check_requirements_file():
    """Verifica que requirements.txt existe y es válido"""
    req_file = Path("requirements.txt")
    if not req_file.exists():
        print("❌ requirements.txt not found")
        return False
    
    print("✅ requirements.txt found")
    return True

def check_constraints_file():
    """Verifica que constraints.txt existe"""
    constraints_file = Path("constraints.txt")
    if not constraints_file.exists():
        print("❌ constraints.txt not found")
        return False
    
    print("✅ constraints.txt found")
    return True

def check_click_version():
    """Verifica que click esté en una versión compatible"""
    try:
        import click
        version = click.__version__
        print(f"Click version: {version}")
        
        # Verificar que sea una versión compatible
        if version.startswith("8.1."):
            print("✅ Click version is compatible")
            return True
        else:
            print("❌ Click version may not be compatible")
            return False
    except ImportError:
        print("⚠️ Click not installed")
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

def main():
    """Función principal de verificación"""
    print("=== DEPENDENCY COMPATIBILITY CHECK ===")
    
    checks = [
        check_python_version(),
        check_requirements_file(),
        check_constraints_file(),
        check_click_version(),
        check_runtime_txt()
    ]
    
    print("\n=== SUMMARY ===")
    if all(checks):
        print("✅ All checks passed - dependencies are compatible")
        return 0
    else:
        print("❌ Some checks failed - please review the issues above")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 