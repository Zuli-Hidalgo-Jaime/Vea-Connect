#!/usr/bin/env python3
"""
Script para validar que la reorganización del proyecto fue exitosa.
Verifica que todos los archivos estén en su lugar correcto y que el proyecto funcione.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_file_structure():
    """Verifica que la estructura de archivos sea correcta."""
    print("🔍 Verificando estructura de archivos...")
    
    expected_structure = {
        'tests/': [
            'integration/health/',
            'integration/api/',
    
            'integration/server/',
            'integration/system/',
            'integration/whatsapp/',
            'performance/',
            'fixtures/'
        ],
        'scripts/': [
            'testing/',
    
            'maintenance/templates/',
            'deployment/startup/',
            'deployment/validation/',
            'diagnostics/',
            'azure/storage/',
            'azure/fixes/',
            'azure/diagnostics/',
            'azure/validation/',
            'data/migrations/',
            'data/cleanup/',
            'setup/'
        ],
        'docs/': [
            'optimization/health-check/',
            'troubleshooting/',
            'reports/whatsapp/',
            'integrations/azure/',
            'integrations/openai/',
            'components/embeddings/',
            'maintenance/corrections/'
        ],
        'data/': [
            'results/',
            'examples/',
            'databases/'
        ],
        'tools/': [],
        'config/azure/': []
    }
    
    all_good = True
    
    for directory, subdirs in expected_structure.items():
        if not os.path.exists(directory):
            print(f"❌ Falta directorio: {directory}")
            all_good = False
        else:
            print(f"✅ Directorio existe: {directory}")
            
        for subdir in subdirs:
            full_path = os.path.join(directory, subdir)
            if not os.path.exists(full_path):
                print(f"❌ Falta subdirectorio: {full_path}")
                all_good = False
            else:
                print(f"✅ Subdirectorio existe: {full_path}")
    
    return all_good

def check_critical_files():
    """Verifica que los archivos críticos estén en su lugar."""
    print("\n🔍 Verificando archivos críticos...")
    
    critical_files = [
        'manage.py',
        'requirements.txt',
        'pytest.ini',
        'runtime.txt',
        '.python-version',
        'README.md',
        'CHANGELOG.md',
        'CONTRIBUTING.md',
        'LICENSE.md',
        '.gitignore',
        '.gitattributes',
        '.flake8',
        'codecov.yml'
    ]
    
    all_good = True
    
    for file in critical_files:
        if os.path.exists(file):
            print(f"✅ Archivo crítico existe: {file}")
        else:
            print(f"❌ Falta archivo crítico: {file}")
            all_good = False
    
    # Verificar que passwords.txt NO existe
    if os.path.exists('passwords.txt'):
        print("❌ CRÍTICO: passwords.txt aún existe")
        all_good = False
    else:
        print("✅ passwords.txt eliminado correctamente")
    
    return all_good

def check_django_functionality():
    """Verifica que Django funcione correctamente."""
    print("\n🔍 Verificando funcionalidad de Django...")
    
    try:
        # Verificar que manage.py funciona
        result = subprocess.run(
            [sys.executable, 'manage.py', 'check', '--deploy'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("✅ Django check --deploy exitoso")
            return True
        else:
            print(f"❌ Django check --deploy falló: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando Django: {e}")
        return False

def check_test_files():
    """Verifica que los archivos de prueba estén en su lugar."""
    print("\n🔍 Verificando archivos de prueba...")
    
    test_files = [
        'tests/integration/health/test_simple_health.py',
        'tests/integration/health/test_health_simple.py',
        'tests/integration/health/quick_health_test.py',
        'tests/performance/test_health_check_performance.py',

        'tests/integration/api/test_all_api_endpoints.py',
        'tests/integration/api/test_api_urls.py',
        'tests/integration/api/test_api_import.py',
        'tests/integration/whatsapp/test_whatsapp_bot.py',
        'tests/integration/system/final_test.py'
    ]
    
    all_good = True
    
    for file in test_files:
        if os.path.exists(file):
            print(f"✅ Archivo de prueba existe: {file}")
        else:
            print(f"❌ Falta archivo de prueba: {file}")
            all_good = False
    
    return all_good

def main():
    """Función principal de validación."""
    print("🚀 Iniciando validación de reorganización del proyecto...")
    
    # Cambiar al directorio del proyecto
    project_root = Path(__file__).parent.parent.parent.parent
    os.chdir(project_root)
    
    # Realizar todas las verificaciones
    structure_ok = check_file_structure()
    critical_ok = check_critical_files()
    django_ok = check_django_functionality()
    tests_ok = check_test_files()
    
    # Resumen final
    print("\n" + "="*50)
    print("📊 RESUMEN DE VALIDACIÓN")
    print("="*50)
    
    print(f"Estructura de archivos: {'✅ OK' if structure_ok else '❌ FALLA'}")
    print(f"Archivos críticos: {'✅ OK' if critical_ok else '❌ FALLA'}")
    print(f"Funcionalidad Django: {'✅ OK' if django_ok else '❌ FALLA'}")
    print(f"Archivos de prueba: {'✅ OK' if tests_ok else '❌ FALLA'}")
    
    if all([structure_ok, critical_ok, django_ok, tests_ok]):
        print("\n🎉 ¡TODAS LAS VALIDACIONES EXITOSAS!")
        print("✅ La reorganización del proyecto fue completada correctamente.")
        return True
    else:
        print("\n⚠️  ALGUNAS VALIDACIONES FALLARON")
        print("❌ La reorganización necesita correcciones.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 