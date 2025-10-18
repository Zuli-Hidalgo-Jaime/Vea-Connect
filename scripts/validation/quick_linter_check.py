#!/usr/bin/env python3
"""
Verificación rápida de correcciones de linter.
"""

import subprocess
import sys

def run_command(command):
    """Ejecutar comando y retornar resultado."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def main():
    """Verificación principal."""
    print("🚀 Verificación rápida de correcciones de linter")
    print("=" * 50)
    
    tests = [
        ("Azure Search SDK", "python -c \"import azure.search.documents; print('OK')\""),
        ("Django Q Import", "python -c \"from django.db.models import Q; print('OK')\""),
        ("Django Setup", "python manage.py shell -c \"from django.db.models import Q; print('OK')\""),
    ]
    
    results = []
    
    for test_name, command in tests:
        print(f"\n📋 {test_name}...")
        success, stdout, stderr = run_command(command)
        
        if success:
            print(f"  ✅ {test_name}: EXITOSO")
            results.append(True)
        else:
            print(f"  ❌ {test_name}: FALLÓ")
            if stderr:
                print(f"     Error: {stderr.strip()}")
            results.append(False)
    
    # Resumen
    print("\n" + "=" * 50)
    print("📊 RESUMEN")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Pruebas exitosas: {passed}/{total}")
    
    if passed == total:
        print("🎉 ¡Todas las correcciones de linter están funcionando!")
        return 0
    else:
        print("⚠️ Algunas correcciones requieren atención")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 