#!/usr/bin/env python3
"""
Script para verificar que el despliegue use Python 3.10
"""

import sys
import subprocess
import os

def check_python_version():
    """Verifica que esté usando Python 3.10"""
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 10:
        print("✅ Python version is 3.10+ (REQUERIDO)")
        return True
    else:
        print("❌ Python version is NOT 3.10+ (REQUERIDO)")
        return False

def check_azure_runtime():
    """Verifica la configuración de Azure"""
    try:
        result = subprocess.run([
            'az', 'webapp', 'show', 
            '-g', 'rg-vea-connect-dev', 
            '-n', 'veaconnect-webapp-prod',
            '--query', 'siteConfig.linuxFxVersion',
            '-o', 'tsv'
        ], capture_output=True, text=True, check=True)
        
        runtime = result.stdout.strip()
        print(f"Azure runtime: {runtime}")
        
        if "PYTHON|3.10" in runtime:
            print("✅ Azure runtime is Python 3.10")
            return True
        else:
            print("❌ Azure runtime is NOT Python 3.10")
            return False
    except subprocess.CalledProcessError as e:
        print(f"❌ Error checking Azure runtime: {e}")
        return False

def check_runtime_files():
    """Verifica archivos de configuración"""
    checks = []
    
    # Check runtime.txt
    if os.path.exists('runtime.txt'):
        with open('runtime.txt', 'r') as f:
            content = f.read()
            if 'python-3.10' in content:
                print("✅ runtime.txt specifies Python 3.10")
                checks.append(True)
            else:
                print("❌ runtime.txt does not specify Python 3.10")
                checks.append(False)
    else:
        print("❌ runtime.txt not found")
        checks.append(False)
    
    # Check startup.sh
    if os.path.exists('startup.sh'):
        with open('startup.sh', 'r') as f:
            content = f.read()
            if 'python3.10' in content:
                print("✅ startup.sh references Python 3.10")
                checks.append(True)
            else:
                print("❌ startup.sh does not reference Python 3.10")
                checks.append(False)
    else:
        print("❌ startup.sh not found")
        checks.append(False)
    
    return all(checks)

def main():
    """Función principal"""
    print("=== PYTHON 3.10 DEPLOYMENT VERIFICATION ===")
    print()
    
    checks = [
        check_python_version(),
        check_azure_runtime(),
        check_runtime_files()
    ]
    
    print("\n=== RESUMEN ===")
    if all(checks):
        print("✅ All checks passed - Python 3.10 deployment ready")
        return 0
    else:
        print("❌ Some checks failed - Python 3.10 deployment not ready")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 